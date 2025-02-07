from flask import Flask, request, jsonify
import gspread
import os
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

# ✅ Load Google Credentials from Environment Variables
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),  # Fix \n issues
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
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")  # Load Sheet ID from environment variable
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # First sheet

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming data from Grafana and logs it to Google Sheets."""
    try:
        data = request.json  # Parse JSON payload from Grafana

        # ✅ Debugging: Print full incoming payload
        print("🚀 Incoming Webhook Data:", data)

        # ✅ Extract the timestamp
        timestamp = data.get("startsAt", datetime.utcnow().isoformat())

        # ✅ Extract the metric name
        metric_name = data.get("title", "Unknown Metric")

        # ✅ Extract the state (FIRING / RESOLVED)
        alert_state = data.get("state", "Unknown State")

        # ✅ Extract and process multiple `evalMatches`
        values = []
        if "evalMatches" in data and isinstance(data["evalMatches"], list):
            for match in data["evalMatches"]:
                market = match.get("tags", {}).get("metric", "Unknown Market")  # Extract market name
                value = match.get("value", "No Data")  # Extract value
                values.append([timestamp, metric_name, alert_state, market, value])  # Store each row

        if not values:
            values.append([timestamp, metric_name, alert_state, "No Market", "No Data"])  # Handle empty case

        # ✅ Append all extracted rows to Google Sheets
        sheet.append_rows(values)

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
