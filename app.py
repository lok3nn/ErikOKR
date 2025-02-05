from flask import Flask, request, jsonify
import gspread
import os
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ✅ Step 1: Load Google Credentials from Environment Variables
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

# ✅ Step 2: Authenticate with Google Sheets API
try:
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    print("✅ Google Sheets API authentication successful!")
except Exception as e:
    raise ValueError(f"❌ Google Sheets API initialization failed: {e}")

# ✅ Step 3: Open Google Sheet
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")  # Load Sheet ID from environment variable
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # First sheet

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming data from Grafana and logs it to Google Sheets."""
    try:
        data = request.json  # Parse JSON payload from Grafana
        timestamp = request.headers.get("Date", "No Timestamp")
        metric_name = data.get("title", "Unknown Metric")
        value = data.get("state", "No Data")

        # ✅ Append data to Google Sheets
        sheet.append_row([timestamp, metric_name, value])

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
