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

    if audio_result["success"]:
        audio_label = audio_result["result"]

    final_violence = violence_found or (audio_label == "violence")
    evidence_path = video_path

    response = {
        "status": "SUCCESS",
        "violence": final_violence,
        "confidence": round(max_confidence, 2),
        "audio_result": audio_label,
        "overall_violence_type": overall_type,
        "objects": merged_objects,
        "evidence_path": evidence_path,
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