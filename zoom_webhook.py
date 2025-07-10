from flask import Flask, request, jsonify
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
DATA_FILE = "attendance_log.csv"
Path(DATA_FILE).touch(exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return "Zoom Webhook is Live ✅", 200

@app.route("/zoom-webhook", methods=["POST"])
def zoom_webhook():
    data = request.json

    # 🛡️ Step 1: Handle URL Validation challenge
    if data.get("event") == "endpoint.url_validation":
        print("🔐 URL validation request received")
        plain_token = data["payload"]["plainToken"]
        encrypted_token = data["payload"].get("encryptedToken", "")
        return jsonify({
            "plainToken": plain_token,
            "encryptedToken": encrypted_token
        })

    # 🧾 Step 2: Handle real meeting events
    event = data.get("event")
    payload = data.get("payload", {})
    participant = payload.get("object", {}).get("participant", {})
    meeting = payload.get("object", {})

    name = participant.get("user_name", "")
    email = participant.get("email", "")
    join_time = participant.get("join_time", "")
    leave_time = participant.get("leave_time", "")
    meeting_id = meeting.get("id", "")
    topic = meeting.get("topic", "")
    timestamp = datetime.utcnow().isoformat()

    print(f"📥 Event: {event}, Participant: {name}, Meeting ID: {meeting_id}")

    df = pd.DataFrame([{
        "Event": event,
        "Name": name,
        "Email": email,
        "JoinTime": join_time,
        "LeaveTime": leave_time,
        "MeetingID": meeting_id,
        "Topic": topic,
        "ReceivedAt": timestamp
    }])
    df.to_csv(DATA_FILE, mode="a", index=False, header=not os.path.exists(DATA_FILE))

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(port=5555, debug=True)
