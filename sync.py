import gspread
import json
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from google.oauth2.service_account import Credentials

# ---------- Google Sheets Setup ----------
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Load Google credentials from environment variable
try:
    service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])
except KeyError:
    raise RuntimeError("❌ GOOGLE_CREDENTIALS environment variable not set.")

credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)
spreadsheet = client.open("Lead_Data")
sheet = spreadsheet.sheet1

# ---------- MongoDB Setup ----------
try:
    MONGO_URI = os.environ["MONGODB_URI"]
except KeyError:
    raise RuntimeError("❌ MONGODB_URI environment variable not set.")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["ChatbotDB"]
collection = db["lead_data"]

def find_row_by_session_id(session_id):
    records = sheet.get_all_records()
    for idx, record in enumerate(records, start=2):
        if record.get('session_id') == session_id:
            return idx
    return None

def upsert_google_sheet(doc):
    session_id = doc.get("session_id", "")
    contact_number = doc.get("contact_number", "")
    email_id = doc.get("email_id", "")
    location = doc.get("location", "")
    name = doc.get("name", "")
    service_interest = doc.get("service_interest", "")
    appointment_date = doc.get("Appointment_date", "")
    appointment_Time = doc.get("Appointment_Time", "")

    all_rows = sheet.get_all_records()
    serial_number = len(all_rows) + 1

    row_data = [
        serial_number,
        session_id,
        contact_number,
        email_id,
        location,
        name,
        service_interest,
        appointment_date,
        appointment_Time,
    ]

    row_number = find_row_by_session_id(session_id)

    if row_number:
        sheet.update(f'A{row_number}:I{row_number}', [row_data])
        print(f"✅ Updated session_id {session_id} at row {row_number}")
    else:
        sheet.append_row(row_data)
        print(f"🆕 Inserted new session_id {session_id}")

# ---------- Watch MongoDB for Real-Time Changes ----------
if __name__ == "__main__":
    print("🚀 Listening for real-time updates from MongoDB...")

    try:
        with collection.watch() as stream:
            for change in stream:
                if change["operationType"] in ("insert", "update", "replace"):
                    document_id = change["documentKey"]["_id"]
                    updated_doc = collection.find_one({"_id": document_id})
                    if updated_doc:
                        upsert_google_sheet(updated_doc)

    except PyMongoError as e:
        print(f"❌ MongoDB error: {e}")
