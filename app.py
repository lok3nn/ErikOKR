from flask import Flask, request, jsonify
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

# ✅ Load Google Credentials
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": "googleapis.com"
}

# ✅ Authenticate with Google Sheets API
try:
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    print("✅ Google Sheets API authentication successful!")
except Exception as e:
    raise ValueError(f"❌ Google Sheets API initialization failed: {e}")

# ✅ Open Google Sheet
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # First sheet

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming Grafana alerts and logs data into Google Sheets."""
    try:
        data = request.json  # Parse JSON payload
        print("📥 Received Webhook Data:", json.dumps(data, indent=4))  # Debugging

        # ✅ Extract timestamp
        timestamp = data.get("startsAt", datetime.utcnow().isoformat())  # Default to now

        # ✅ Extract metric name
        metric_name = data.get("title", "Unknown Metric")

        # ✅ Extract alert state (FIRING / RESOLVED)
        alert_state = data.get("state", "Unknown State")

        # ✅ Extract value (Ensure it's correctly parsed)
        value = "No Data"
        if "valueString" in data:
            value = data["valueString"]
        elif "evalMatches" in data and isinstance(data["evalMatches"], list):
            if len(data["evalMatches"]) > 0:
                value = str(data["evalMatches"][0].get("value", "No Data"))

        print(f"📊 Parsed Data: Timestamp: {timestamp}, Metric: {metric_name}, State: {alert_state}, Value: {value}")

        # ✅ Append data to Google Sheets
        sheet.append_row([timestamp, metric_name, alert_state, value])

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200

    except Exception as e:
        print(f"❌ Error: {str(e)}")  # Debugging
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
