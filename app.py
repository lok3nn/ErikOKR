from flask import Flask, request, jsonify
import gspread
import json
import os
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Load credentials manually
raw_credentials = os.getenv("GOOGLE_CREDENTIALS")
if raw_credentials is None:
    raise ValueError("❌ GOOGLE_CREDENTIALS is missing!")

SERVICE_ACCOUNT_INFO = json.loads(raw_credentials)

# Ensure the private key is correctly formatted
SERVICE_ACCOUNT_INFO["private_key"] = SERVICE_ACCOUNT_INFO["private_key"].replace("\\n", "\n")

# Authenticate with Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)

gc = gspread.authorize(creds)

# Open Google Sheet
SPREADSHEET_ID = "1ixnyPaYJydg9T8iJzLIMDlX1EyJcdz7KBKSy7slubqI"
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        timestamp = request.headers.get("Date")
        metric_name = data.get("title", "Unknown Metric")
        value = data.get("state", "No Data")

        sheet.append_row([timestamp, metric_name, value])

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
