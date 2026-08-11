from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect():

    file = request.files["file"]

    return jsonify({
        "incidentType": "Violence",
        "confidence": 95.5
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)