import json
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
    if not SERVICE_ACCOUNT_INFO["private_key"]:
        raise ValueError("❌ Missing Google credentials. Check environment variables.")

    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    print("✅ Google Sheets API authentication successful!")
except Exception as e:
    raise ValueError(f"❌ Google Sheets API initialization failed: {e}")

# ✅ Open Google Sheet
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming data from Grafana and logs it to Google Sheets."""
    try:
        data = request.json  # Parse JSON payload from Grafana
        print("\n🚀 FULL INCOMING WEBHOOK DATA 🚀")
        print(data)

        # ✅ Check if the actual data is inside `message` as a JSON string
        if "message" in data and isinstance(data["message"], str):
            try:
                extracted_data = json.loads(data["message"])  # Convert to dictionary
                print("✅ Extracted JSON from 'message' field")
                data = extracted_data  # Replace main data variable with extracted data
            except json.JSONDecodeError:
                print("⚠️ Failed to parse 'message' as JSON. Using original payload.")

        # ✅ Extract timestamp
        timestamp = data.get("startsAt", datetime.utcnow().isoformat())

        # ✅ Extract alert name
        alert_name = data.get("title", "Unknown Alert")

        # ✅ Extract alert state
        alert_state = data.get("state", "Unknown State")

        # ✅ Process multiple alerts (markets)
        values = []
        if "alerts" in data and isinstance(data["alerts"], list):
            for alert in data["alerts"]:
                market = alert.get("labels", {}).get("metric", "Unknown Market")
                value = alert.get("values", {}).get("A", "No Data")  # Extract value from 'values.A'

                print(f"📌 Extracted: {market} -> {value}")  # Debugging
                values.append([timestamp, alert_name, alert_state, market, value])  # Store each row

        if not values:
            values.append([timestamp, alert_name, alert_state, "No Market", "No Data"])  # Handle empty case

        # ✅ Debug: Print the final values before sending to Sheets
        print("✅ FINAL VALUES TO WRITE TO SHEETS:", values)

        # ✅ Append all extracted rows to Google Sheets
        sheet.append_rows(values)
        print("📄 Data successfully written to Google Sheets!")

        return jsonify({"status": "success", "message": "Data added to Google Sheets"}), 200
    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
