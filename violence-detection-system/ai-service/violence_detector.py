import cv2
import numpy as np
import os
import torch
import torch.nn as nn
import pytorchvideo.models.hub as hub
import subprocess
from ultralytics import YOLO

print("Loading Official Pre-trained X3D Action Model...")
violence_model = hub.x3d_m(pretrained=True)
violence_model.eval()

# Kinetics-400 Action IDs that represent physical fights / violence
VIOLENT_ACTION_IDS = {150, 259, 314, 395, 101, 201, 343}

print("Violence model loaded successfully!\n")

yolo_model = YOLO("yolo11m.pt")

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


def enhance_low_light(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


MEAN = torch.tensor([0.45, 0.45, 0.45]).view(1, 3, 1, 1, 1)
STD = torch.tensor([0.225, 0.225, 0.225]).view(1, 3, 1, 1, 1)


def predict_chunk(frames):

    video = np.array(frames, dtype=np.float32)
    video = torch.tensor(video)
    video = video.permute(3, 0, 1, 2)
    video = video.unsqueeze(0) / 255.0
    video = (video - MEAN) / STD

    with torch.no_grad():
        output = violence_model(video)
        prob = torch.softmax(output, dim=1)
        
        top5_prob, top5_idx = prob.topk(5, dim=1)
        
        # Debug: Print the Top-1 predicted class ID and probability
        top1_id = int(top5_idx[0][0].item())
        top1_prob = float(top5_prob[0][0].item())
        print(f"DEBUG - Top-1 Predicted Class ID: {top1_id} with Prob: {round(top1_prob * 100, 2)}%")
        
        violence_prob = 0.0
        for i in range(5):
            class_id = int(top5_idx[0][i].item())
            if class_id in VIOLENT_ACTION_IDS:
                violence_prob = max(violence_prob, float(top5_prob[0][i].item()))
        
        x3d_confidence = round(violence_prob * 100, 2)

    return x3d_confidence


ALLOWED_OBJECTS = {
    "person", "knife", "gun", "backpack", "handbag",
    "suitcase", "baseball bat", "bottle", "car", "truck", "bus", "motorcycle", "bicycle", "cell phone"
}


def detect_objects(frame_bgr):
    results = yolo_model(frame_bgr, verbose=False)[0]
    objects = {}

    for box in results.boxes:
        conf = float(box.conf[0])
        if conf < 0.15:
            continue

        cls_id = int(box.cls[0])
        cls_name = yolo_model.names[cls_id]

        if cls_name not in ALLOWED_OBJECTS:
            continue

        min_conf = 0.10 if cls_name == "person" else 0.10

        if conf < min_conf:
            continue

        objects[cls_name] = objects.get(cls_name, 0) + 1

    return objects


def detect_objects_multi_frame(raw_frames, sample_count=5):
    total_frames = len(raw_frames)
    indices = [int(i * total_frames / sample_count) for i in range(sample_count)]

    best_objects = {}
    for idx in indices:
        frame = raw_frames[idx]
        objects = detect_objects(frame)
        for obj, count in objects.items():
            best_objects[obj] = max(best_objects.get(obj, 0), count)

    return best_objects


def get_person_boxes(frame_bgr):
    results = yolo_model(frame_bgr, verbose=False)[0]
    person_boxes = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = yolo_model.names[cls_id]
        conf = float(box.conf[0])

        if cls_name == "person" and conf >= 0.10:  # Lowered to 0.10 for dark/night/blurry videos
            person_boxes.append(box.xyxy[0].tolist())

    return person_boxes


def check_person_proximity(frame_bgr):

    person_boxes = get_person_boxes(frame_bgr)

    close_pairs = 0
    for i in range(len(person_boxes)):
        for j in range(i + 1, len(person_boxes)):
            x1a, y1a, x2a, y2a = person_boxes[i]
            x1b, y1b, x2b, y2b = person_boxes[j]

            dx = max(x1a, x1b) - min(x2a, x2b)
            dy = max(y1a, y1b) - min(y2a, y2b)


            if dx < -5 and dy < -5:
                close_pairs += 1

    return close_pairs > 0, len(person_boxes)


def compute_motion_intensity(frames):
    if len(frames) < 2:
        return 0.0

    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    total_motion = 0.0
    count = 0

    for i in range(1, len(frames)):
        gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None,
            0.5, 3, 15, 3, 5, 1.2, 0
        )
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        total_motion += float(np.mean(magnitude))
        count += 1
        prev_gray = gray


    return float(total_motion / count) if count else 0.0


WEAPON_MOTION_THRESHOLD = 1.5
UNARMED_MOTION_THRESHOLD = 2.5  # Lowered from 4.0 to catch subtle motion in the dark

X3D_MIN_CONFIDENCE = 40.0


def classify_violence_type(objects, is_violence, person_count, x3d_confidence, motion_val):
    if not is_violence:
        return "Normal", "No violence detected."

    # Identify weapons and vehicles
    weapons = {"knife", "gun", "pistol"}
    found_weapons = [w for w in weapons if w in objects]
    
    vehicles = {"car", "truck", "bus", "van", "motorcycle"}
    found_vehicles = [v for v in vehicles if v in objects]

    has_bags = any(b in objects for b in ["backpack", "handbag", "suitcase", "bag"])

    # 1. Kidnap heuristic
    if found_vehicles and person_count >= 1:
        desc = f"A kidnapping attempt involving a vehicle and {person_count} individual(s) detected."
        return "Kidnap", desc

    # 2. Robbery heuristic
    if (found_weapons or has_bags) and person_count >= 1:
        if found_weapons:
            desc = f"An armed robbery involving a {', '.join(found_weapons)} and {person_count} individual(s) detected."
        else:
            desc = f"A robbery/snatching attempt involving {person_count} individual(s) detected."
        return "Robbery", desc

    # 3. Murder heuristic (Severe armed assault)
    if found_weapons and (x3d_confidence >= 75.0 or motion_val > 4.5):
        if person_count >= 3:
            desc = f"A man assaulted/murdered by {person_count - 1} men with a {found_weapons[0]}."
        else:
            desc = f"A man attacked/murdered by an armed assailant."
        return "Murder", desc

    # 4. Group Fight
    if person_count >= 3:
        desc = f"A group fight involving {person_count} individuals detected."
        return "Group Fight", desc

    # 5. Assault
    if person_count == 2:
        desc = f"An assault/fight between 2 individuals detected."
        return "Assault", desc

    # General Fallback
    desc = "A physical altercation / violence detected."
    return "Assault", desc


def scale_confidence(motion_intensity, threshold, base=55, ceiling=97):

    if threshold <= 0:
        return base

    excess_ratio = (motion_intensity - threshold) / threshold  # 0 = just crossed, 1 = double
    excess_ratio = max(0.0, excess_ratio)

    # excess_ratio 0 -> base, excess_ratio 1.5+ -> ceiling (saturate)
    scaled = base + (ceiling - base) * min(excess_ratio / 1.5, 1.0)
    return float(round(scaled, 2))


def trim_video_and_extract_audio(video_path, start_time, timestamp):
    evidence_dir = "evidence"
    os.makedirs(evidence_dir, exist_ok=True)
    
    video_clip_name = f"clip_{timestamp}.mp4".replace(":", "-").replace(" ", "_")
    audio_clip_name = f"audio_{timestamp}.mp3".replace(":", "-").replace(" ", "_")
    
    video_clip_path = os.path.join(evidence_dir, video_clip_name)
    audio_clip_path = os.path.join(evidence_dir, audio_clip_name)
    
    ffmpeg_path = "D:\\ffmpeg-9.0-essentials_build\\ffmpeg-9.0-essentials_build\\bin\\ffmpeg.exe"
    
    # 1. Trim 5-second video clip using FFmpeg and re-encode as H264 for mobile compatibility
    video_cmd = [
        ffmpeg_path, "-y",
        "-ss", str(max(0.0, start_time)),
        "-i", video_path,
        "-t", "5",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        video_clip_path
    ]
    
    # 2. Extract 5-second audio clip as MP3
    audio_cmd = [
        ffmpeg_path, "-y",
        "-ss", str(max(0.0, start_time)),
        "-i", video_path,
        "-t", "5",
        "-vn",
        "-acodec", "libmp3lame",
        audio_clip_path
    ]
    
    try:
        subprocess.run(video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"FFmpeg trim error: {e}")
        
    return video_clip_path, audio_clip_path


def evaluate_violence(raw_frames, high_res_frame, x3d_confidence, timestamp):
    # Run YOLO and get the full result to plot boxes on high_res_frame
    yolo_results = yolo_model(high_res_frame, verbose=False)[0]
    
    # Use helper with updated sensitive thresholds on high_res_frame
    objects_detected = detect_objects(high_res_frame)

    person_count = objects_detected.get("person", 0)

    is_violence = (x3d_confidence >= 40.0)
    motion = compute_motion_intensity(raw_frames)
    
    # Check for weapons, vehicles, and bags/phones
    has_weapon = any(w in objects_detected for w in ["knife", "gun"])
    has_vehicle = any(v in objects_detected for v in ["car", "truck", "bus", "motorcycle", "bicycle"])
    has_bag_or_phone = any(item in objects_detected for item in ["backpack", "handbag", "suitcase", "cell phone"])
    
    # Calculate average pixel intensity to check if it is a night/low-light scene
    avg_intensity = np.mean(high_res_frame)
    is_low_light = avg_intensity < 65.0 # Threshold for night vision
    
    if is_low_light:
        print(f"DEBUG - Low Light Scene Detected (Avg Intensity: {round(avg_intensity, 2)})")

    # 1. Force Violence if Weapons are detected (Robbery / Murder)
    if has_weapon and person_count >= 1:
        is_violence = True
        x3d_confidence = max(x3d_confidence, 85.0)
        print("FORCE VIOLENCE: Weapon detected during altercation.")
        
    # 2. Force Violence if vehicles and individuals are present with motion (Kidnap)
    elif has_vehicle and person_count >= 1 and motion > 0.05:
        is_violence = True
        x3d_confidence = max(x3d_confidence, 70.0)
        print("FORCE VIOLENCE: Vehicle and individual(s) detected with movement.")

    # 3. Fallback logic for normal/night fights and snatching robbery
    else:
        people_close, p_count = check_person_proximity(high_res_frame)
        
        # Lower motion thresholds if low light / night vision environment
        motion_threshold = 0.5 if is_low_light else 1.0
        extreme_motion_threshold = 1.0 if is_low_light else 2.5
        
        # Snatching detection: person with a bag/phone + slight motion
        is_snatching = (p_count >= 1) and has_bag_or_phone and (motion > 0.03)
        
        # Night time robbery: person moving in the dark
        is_night_robbery = is_low_light and (p_count >= 1) and (motion > 0.03)
        
        print(f"DEBUG - Proximity Check | Motion: {round(motion, 2)} | Persons: {p_count} | Close: {people_close} | Snatching/Night Check: {is_snatching or is_night_robbery}")
        
        if is_snatching or is_night_robbery:
            is_violence = True
            x3d_confidence = max(x3d_confidence, scale_confidence(motion, 0.03, 65, 88))
            print("FORCE VIOLENCE: Robbery/Snatching detected based on object context and motion.")
        elif not is_violence:
            if motion > extreme_motion_threshold or (p_count >= 2 and motion > motion_threshold) or (people_close and motion > 0.1):
                is_violence = True
                x3d_confidence = scale_confidence(motion, motion_threshold, 60, 95)
    # ---------------------------------------

    v_type, core_content = classify_violence_type(
        objects_detected, is_violence, person_count, x3d_confidence, motion
    )

    annotated_image_path = ""
    if is_violence:
        evidence_dir = "evidence"
        os.makedirs(evidence_dir, exist_ok=True)
        img_name = f"annotated_{timestamp}.jpg".replace(":", "-").replace(" ", "_")
        annotated_image_path = os.path.join(evidence_dir, img_name)
        annotated_frame = yolo_results.plot()
        cv2.imwrite(annotated_image_path, annotated_frame)

    print(f"Final Violence Confidence: {x3d_confidence}% | Violence: {is_violence} | Type: {v_type}")
    return is_violence, v_type, core_content, objects_detected, x3d_confidence, x3d_confidence, annotated_image_path


def analyze_full_video(video_path, chunk_size=16, stride=16):  # Changed stride to 16 for 2x speedup

    evidence_dir = "evidence"
    os.makedirs(evidence_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    frame_buffer = []
    raw_frame_buffer = []
    high_res_buffer = []
    frame_idx = 0
    results = []
    consecutive_violent = 0  # loop-ku VELIYA, once matum initialize

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        enhanced = enhance_low_light(frame)
        resized = cv2.resize(enhanced, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        frame_buffer.append(rgb)
        raw_frame_buffer.append(resized)  # HUGE Speedup: Run optical flow & YOLO on 224x224 instead of HD 1080p
        high_res_buffer.append(enhanced)

        frame_idx += 1

        if len(frame_buffer) == chunk_size:


            x3d_confidence = predict_chunk(frame_buffer)

            timestamp = round((frame_idx - chunk_size) / fps, 2)
            
            mid_high_res = high_res_buffer[len(high_res_buffer) // 2]

            is_violence_raw, violence_type, core_content, objects, our_confidence, x3d_ref, annotated_img = \
                evaluate_violence(raw_frame_buffer, mid_high_res, x3d_confidence, timestamp)

            if is_violence_raw:
                consecutive_violent += 1
            else:
                consecutive_violent = 0

            # Trigger violence immediately if at least 1 chunk is detected as violent
            is_violence = consecutive_violent >= 1

            entry = {
                "time_sec": timestamp,
                "violence": is_violence,
                "confidence": our_confidence,
                "x3d_reference_score": x3d_ref,
                "objects": objects,
                "violence_type": violence_type if is_violence else None,
                "core_content": core_content if is_violence else "No violence detected.",
                "evidence_path": "",
                "annotated_image_path": annotated_img if is_violence else "",
                "video_clip_path": "",
                "audio_clip_path": ""
            }

            if is_violence:
                # Save raw evidence screenshot
                evidence_name = f"violence_{frame_idx}.jpg"
                evidence_path = os.path.join(evidence_dir, evidence_name)
                cv2.imwrite(
                    evidence_path,
                    high_res_buffer[len(high_res_buffer) // 2]
                )
                entry["evidence_path"] = evidence_path

                # Trim 5-second video clip and extract audio using FFmpeg
                clip_path, audio_path = trim_video_and_extract_audio(
                    video_path, timestamp, timestamp
                )
                entry["video_clip_path"] = clip_path
                entry["audio_clip_path"] = audio_path

            results.append(entry)

            frame_buffer = frame_buffer[stride:]
            raw_frame_buffer = raw_frame_buffer[stride:]
            high_res_buffer = high_res_buffer[stride:]

    cap.release()

    return results


if __name__ == "__main__":
    video_path = "sample_video.mp4"
    output = analyze_full_video(video_path)

    print(f"\n--- Analysis Result for {video_path} ---\n")
    for r in output:
        if r["violence"]:
            print(f"[{r['time_sec']}s] VIOLENCE DETECTED "
                  f"(our confidence: {r['confidence']}% | x3d ref: {r['x3d_reference_score']}%) "
                  f"| Type: {r['violence_type']} | Objects: {r['objects']}")
        else:
            print(f"[{r['time_sec']}s] Normal "
                  f"(our confidence: {r['confidence']}% | x3d ref: {r['x3d_reference_score']}%)")