from flask import Flask, request, jsonify
import os
import pickle

from violence_detector import analyze_full_video
from audio_detector import AudioViolenceDetector

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_PATH = "../models/violence_model.pkl"

with open(MODEL_PATH, "rb") as model_file:
    model = pickle.load(model_file)

audio_detector = AudioViolenceDetector(model)

print("Audio Violence Detector initialized successfully")


@app.route("/detect-video", methods=["POST"])
def detect_video():

    print("VIDEO API HIT")

    file = request.files["file"]
    video_path = os.path.join(UPLOAD_FOLDER, "temp_video.mp4")
    file.save(video_path)

    results = analyze_full_video(video_path)

    violence_found = any(r["violence"] for r in results)

    merged_objects = {}
    violence_events = []

    for r in results:
        if r["violence"]:
            violence_events.append({
                "time_sec": r["time_sec"],
                "confidence": r["confidence"],
                "violence_type": r["violence_type"],
                "objects": r["objects"]
            })

            for obj, count in r["objects"].items():
                merged_objects[obj] = max(merged_objects.get(obj, 0), count)

    max_confidence = max(
        [r["confidence"] for r in results if r["violence"]],
        default=0
    )

    video_violence_types = [r["violence_type"] for r in results if r["violence"] and r.get("violence_type")]
    video_core_contents = [r["core_content"] for r in results if r["violence"] and r.get("core_content")]
    
    if video_violence_types:
        overall_type = video_violence_types[-1] # take the most recent clear type
    else:
        max_persons = merged_objects.get("person", 0)
        if max_persons >= 3:
            overall_type = "Group Fight"
        elif max_persons == 2:
            overall_type = "Assault/Fight"
        elif merged_objects:
            overall_type = "Suspicious Activity"
        else:
            overall_type = "No clear violence type"

    audio_result = audio_detector.detect(video_path)

    audio_label = "Unknown"
    audio_conf = 0.0

    if audio_result.get("success"):
        audio_label = audio_result.get("result", "Unknown")
        if audio_label == "violence":
            audio_conf = 66.0

    final_violence = violence_found or (audio_label == "violence")

    if video_core_contents:
        core_content = video_core_contents[-1]
    else:
        if audio_label == "violence":
            core_content = "Scream or distress sound detected in the audio feed."
        elif final_violence:
            core_content = "A physical altercation / violence detected."
        else:
            core_content = "No violence detected."

    if final_violence:
        if max_confidence <= 0:
            max_confidence = audio_conf if audio_conf > 0 else 75.0

        if not violence_found and audio_label == "violence":
            overall_type = "Audio-Detected Violence (Scream/Distress)"

    evidence_path = video_path

    # Extract evidence file paths from the first violent chunk
    annotated_image_path = ""
    video_clip_path = ""
    audio_clip_path = ""
    for r in results:
        if r["violence"]:
            if r.get("annotated_image_path"):
                annotated_image_path = r["annotated_image_path"]
            if r.get("video_clip_path"):
                video_clip_path = r["video_clip_path"]
            if r.get("audio_clip_path"):
                audio_clip_path = r["audio_clip_path"]
            break  # Use the first violent chunk's evidence

    response = {
        "status": "SUCCESS",
        "violence": final_violence,
        "confidence": round(max_confidence, 2),
        "audio_result": audio_label,
        "overall_violence_type": overall_type,
        "core_content": core_content,
        "objects": merged_objects,
        "evidence_path": evidence_path,
        "annotated_image_path": annotated_image_path,
        "video_clip_path": video_clip_path,
        "audio_clip_path": audio_clip_path,
        "violence_events": violence_events
    }

    print("RESULT =", response)

    return jsonify(response)


@app.route("/detect-audio", methods=["POST"])
def detect_audio():
    print("AUDIO API HIT")

    file = request.files["file"]
    audio_path = os.path.join(UPLOAD_FOLDER, "temp_audio.wav")
    file.save(audio_path)

    audio_check = audio_detector.detect(audio_path)

    print("AUDIO CHECK RESULT:", audio_check)

    if not audio_check["success"]:
        return jsonify({
            "status": "FAILED",
            "error": audio_check.get("error", "Unknown error")
        }), 500

    result_label = audio_check["result"]
    is_violence = (result_label == "violence")

    response = {
        "status": "SUCCESS",
        "violence": is_violence,
        "audio_result": result_label,
        "overall_violence_type": "Audio-based Violence (scream/distress detected)" if is_violence else "Normal Audio"
    }

    print("AUDIO RESULT =", response)

    return jsonify(response)


@app.route("/detect", methods=["POST"])
def detect_image():
    from ultralytics import YOLO
    yolo_model = YOLO("yolo11m.pt")

    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, "temp.jpg")
    file.save(path)

    results = yolo_model(path)
    object_count = {}

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            obj = yolo_model.names[cls]
            object_count[obj] = object_count.get(obj, 0) + 1

    return jsonify({
        "status": "SUCCESS",
        "objects": object_count
    })


@app.route("/analyze", methods=["POST"])
def analyze_rtsp():

    data = request.json
    rtsp_url = data.get("rtspUrl")

    return jsonify({
        "violence": False,
        "confidence": 0,
        "message": "RTSP analysis endpoint ready"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)