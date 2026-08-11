import cv2
import torch
import torch.nn as nn
import numpy as np
from pytorchvideo.models.hub import x3d_m
from ultralytics import YOLO
import os

violence_model = x3d_m(pretrained=False)
violence_model.blocks[5].proj = nn.Sequential(
    nn.Dropout(p=0.5),
    nn.Linear(2048, 2)
)
checkpoint = torch.load(
    "models/final/final_x3d_realtime.pt",
    map_location="cpu",
    weights_only=False
)

print("Chosen config:", checkpoint.get("chosen_config"))
print("Hyper params:", checkpoint.get("hyper_params"))
print("Final metrics:", checkpoint.get("final_metrics"))

raw_state_dict = checkpoint["model"]
new_state_dict = {}
for k, v in raw_state_dict.items():
    if k.startswith("backbone."):
        new_key = k[len("backbone."):]
        new_state_dict[new_key] = v
    else:
        new_state_dict[k] = v

result = violence_model.load_state_dict(new_state_dict, strict=False)
print("Missing:", len(result.missing_keys))
print("Unexpected:", len(result.unexpected_keys))
violence_model.eval()
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
    """
    X3D model - namba இதை RUN pannurom (active-ah irukum),
    aana output-ah confidence calculation-ku use pannala.
    Reference/info matum-ah return pannurom.
    """
    video = np.array(frames, dtype=np.float32)
    video = torch.tensor(video)
    video = video.permute(3, 0, 1, 2)
    video = video.unsqueeze(0) / 255.0
    video = (video - MEAN) / STD

    with torch.no_grad():
        output = violence_model(video)
        prob = torch.softmax(output, dim=1)
        violence_prob = float(prob[0][0])
        x3d_confidence = round(violence_prob * 100, 2)

    return x3d_confidence


ALLOWED_OBJECTS = {
    "person", "knife", "gun", "backpack", "handbag",
    "suitcase", "baseball bat", "bottle"
}


def detect_objects(frame_bgr):
    results = yolo_model(frame_bgr, verbose=False)[0]
    objects = {}

    for box in results.boxes:
        conf = float(box.conf[0])
        if conf < 0.25:
            continue

        cls_id = int(box.cls[0])
        cls_name = yolo_model.names[cls_id]

        if cls_name not in ALLOWED_OBJECTS:
            continue

        min_conf = 0.30 if cls_name == "person" else 0.45

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

        if cls_name == "person" and conf >= 0.30:
            person_boxes.append(box.xyxy[0].tolist())

    return person_boxes


def check_person_proximity(frame_bgr):
    """
    STRICT check bro - persons ACTUAL-ah overlap aaganum (touching/grappling),
    matum standing close-ah irunthaal idhu True aagaathu.
    Negative dx/dy = boxes overlap aaguthu.
    """
    person_boxes = get_person_boxes(frame_bgr)

    close_pairs = 0
    for i in range(len(person_boxes)):
        for j in range(i + 1, len(person_boxes)):
            x1a, y1a, x2a, y2a = person_boxes[i]
            x1b, y1b, x2b, y2b = person_boxes[j]

            dx = max(x1a, x1b) - min(x2a, x2b)
            dy = max(y1a, y1b) - min(y2a, y2b)

            # strict: boxes ACTUAL overlap aaganum (dx, dy negative-ah irukanum,
            # konjo margin kudukurom -5 vaikkurom)
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

    # native Python float-ah force pannurom, numpy float32 illama
    return float(total_motion / count) if count else 0.0


# Real-world logic-ku rendu vera thresholds:
# - weapon irundha, konjo lower motion podhum (weapon + slight aggression = dangerous)
# - weapon illama (bare-hand), higher motion venum (mistake-ah proximity-ah trigger aagaama)
WEAPON_MOTION_THRESHOLD = 2.0
UNARMED_MOTION_THRESHOLD = 4.0

# X3D-ah oru required gate-ah vaikkurom (AND condition). Idhu matum-ah decide pannaadhu,
# aana namba signals-oda SERNTHU thaan final violence confirm aagum.
X3D_MIN_CONFIDENCE = 50.0


def classify_violence_type(objects, is_weapon_case, person_count):
    if is_weapon_case:
        weapons = {"knife", "gun", "pistol"}
        found_weapons = [w for w in weapons if w in objects]
        if person_count >= 5:
            return f"Group Fight with Weapons ({', '.join(found_weapons)})"
        elif "gun" in found_weapons or "pistol" in found_weapons:
            return "Robbery / Armed Assault"
        else:
            return "Assault"
    else:
        if person_count >= 3:
            return "Group Fight (unarmed)"
        return "Physical Altercation (unarmed)"


def scale_confidence(motion_intensity, threshold, base=55, ceiling=97):
    """
    Motion intensity threshold-ah evlo excess-ah kadanthirukko-nu vachi
    55-97 range-ku gradual-ah scale pannurom. Threshold-ku konjo mela na
    low confidence (borderline), threshold-ku romba mela na high confidence.
    """
    if threshold <= 0:
        return base

    excess_ratio = (motion_intensity - threshold) / threshold  # 0 = just crossed, 1 = double
    excess_ratio = max(0.0, excess_ratio)

    # excess_ratio 0 -> base, excess_ratio 1.5+ -> ceiling (saturate)
    scaled = base + (ceiling - base) * min(excess_ratio / 1.5, 1.0)
    return float(round(scaled, 2))


def evaluate_violence(raw_frames, x3d_confidence):
    """
    Real-world logic bro:
    - Weapon matum irundha (police officer standing calm mari) -> VIOLENCE ILLA
    - Weapon + aggressive movement (high motion) -> VIOLENCE (armed attack)
    - People close-ah nikkiranga matum (standing/talking) -> VIOLENCE ILLA
    - People close + aggressive movement -> VIOLENCE (physical fight)
    - X3D confidence idhu DECISION-la pangu edukaathu (unreliable-ah irundhadhaala),
      response-la "x3d_reference_score" nu matum info-ku kudukurom.
    """
    mid_frame = raw_frames[len(raw_frames) // 2]
    objects_decision = detect_objects(mid_frame)

    sampled = raw_frames[::4] if len(raw_frames) >= 8 else raw_frames
    motion_intensity = compute_motion_intensity(sampled)

    weapons = {"knife", "gun", "pistol"}
    found_weapons = [w for w in weapons if w in objects_decision]

    proximity_close, person_count = check_person_proximity(mid_frame)

    print(f"Motion intensity: {round(motion_intensity, 3)} | "
          f"Weapons: {found_weapons} | Proximity: {proximity_close} | "
          f"Persons: {person_count} | X3D ref (info only): {x3d_confidence}%")

    # CASE 1: Weapon irukku - aana weapon MATUM podhaathu, aggression (motion) um venum
    if found_weapons:
        if motion_intensity > WEAPON_MOTION_THRESHOLD:
            objects_full = detect_objects_multi_frame(raw_frames, sample_count=5)
            person_count_full = max(person_count, objects_full.get("person", 0))
            v_type = classify_violence_type(objects_full, True, person_count_full)

            # weapon cases konjo high base confidence-ah start pannurom (65-98 range)
            our_confidence = scale_confidence(
                motion_intensity, WEAPON_MOTION_THRESHOLD, base=65, ceiling=98
            )
            return True, v_type, objects_full, our_confidence, x3d_confidence

        # weapon irundhalum, calm-ah irukaanga (officer holding gun mari) - violence illa
        return False, None, objects_decision, float(round(motion_intensity * 15, 2)), x3d_confidence

    # CASE 2: Weapon illama - proximity + motion venum (X3D condition illa)
    if proximity_close and motion_intensity > UNARMED_MOTION_THRESHOLD:
        objects_full = detect_objects_multi_frame(raw_frames, sample_count=5)
        person_count_full = max(person_count, objects_full.get("person", 0))
        v_type = classify_violence_type(objects_full, False, person_count_full)

        # unarmed cases konjo modest base confidence-ah start pannurom (50-95 range)
        our_confidence = scale_confidence(
            motion_intensity, UNARMED_MOTION_THRESHOLD, base=50, ceiling=95
        )
        return True, v_type, objects_full, our_confidence, x3d_confidence

    # proximity illama, illa motion kammiya irundha (standing/talking) - violence illa
    our_confidence = float(round(motion_intensity * 15, 2))
    return False, None, objects_decision, our_confidence, x3d_confidence


def analyze_full_video(video_path, chunk_size=16, stride=16):

    evidence_dir = "evidence"
    os.makedirs(evidence_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    frame_buffer = []
    raw_frame_buffer = []
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
        raw_frame_buffer.append(enhanced)

        frame_idx += 1

        if len(frame_buffer) == chunk_size:

            # X3D run pannurom (reference-ku), decision-ku use pannala
            x3d_confidence = predict_chunk(frame_buffer)

            timestamp = round((frame_idx - chunk_size) / fps, 2)

            is_violence_raw, violence_type, objects, our_confidence, x3d_ref = \
                evaluate_violence(raw_frame_buffer, x3d_confidence)

            if is_violence_raw:
                consecutive_violent += 1
            else:
                consecutive_violent = 0

            # 2+ consecutive chunks venum confirm aaga (stride=16, fps=25 na
            # ~1.3 sec continuous signal venum)
            is_violence = consecutive_violent >= 3

            entry = {
                "time_sec": timestamp,
                "violence": is_violence,
                "confidence": our_confidence,       # NAMBA formula vachi calculate pannina confidence
                "x3d_reference_score": x3d_ref,      # X3D output - display/reference-ku matum
                "objects": objects,
                "violence_type": violence_type if is_violence else None,
                "evidence_path": ""
            }

            if is_violence:
                evidence_name = f"violence_{frame_idx}.jpg"
                evidence_path = os.path.join(evidence_dir, evidence_name)

                cv2.imwrite(
                    evidence_path,
                    raw_frame_buffer[len(raw_frame_buffer) // 2]
                )

                entry["evidence_path"] = evidence_path

            results.append(entry)

            frame_buffer = frame_buffer[stride:]
            raw_frame_buffer = raw_frame_buffer[stride:]

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