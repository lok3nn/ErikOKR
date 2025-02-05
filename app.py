from flask import Flask, request, jsonify
import gspread
import json
import os
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ✅ Step 1: Load and fix Google Service Account credentials
raw_credentials = os.getenv("GOOGLE_CREDENTIALS")
if not raw_credentials:
    raise ValueError("❌ GOOGLE_CREDENTIALS is missing! Check Render environment variables.")

try:
    SERVICE_ACCOUNT_INFO = json.loads(raw_credentials)
    if "private_key" in SERVICE_ACCOUNT_INFO:
        SERVICE_ACCOUNT_INFO["private_key"] = SERVICE_ACCOUNT_INFO["private_key"].replace("\\n", "\n")  # Fix newlines
    print("✅ Successfully loaded and formatted credentials!")
except json.JSONDecodeError as e:
    raise ValueError(f"❌ JSON Parsing Error: {e}")

# ✅ Step 2: Authenticate with Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

# ✅ Step 3: Open Google Sheet
SPREADSHEET_ID = "1ixnyPaYJydg9T8iJzLIMDlX1EyJcdz7KBKSy7slubqI"  # Replace with actual Sheet ID
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
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
