from flask import Flask, request, jsonify
import gspread
import json
import os
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Load Google Sheets API credentials from environment variable
SERVICE_ACCOUNT_INFO = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)

# Open Google Sheet
gc = gspread.authorize(creds)
SPREADSHEET_ID = "1ixnyPaYJydg9T8iJzLIMDlX1EyJcdz7KBKSy7slubqI"  # Replace with your actual Google Sheet ID
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # First sheet

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json  # Parse JSON data from Grafana
        timestamp = request.headers.get("Date")  # Optional: Use Grafana's timestamp
        metric_name = data.get("title", "Unknown Metric")
        value = data.get("state", "No Data")

        # Append data to Google Sheets
        sheet.append_row([timestamp, metric_name, value])

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
