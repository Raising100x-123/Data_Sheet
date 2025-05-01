import os
import json
import gspread
from google.oauth2.service_account import Credentials
from pymongo import MongoClient

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["ChatbotDB"]
collection = db["lead_data"]

# Google Sheet Setup
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

service_account_info = json.loads(os.environ['GCP_SERVICE_ACCOUNT_JSON'])
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)
spreadsheet = client.open("Lead_Data")
sheet = spreadsheet.sheet1

def find_row_by_session_id(session_id):
    records = sheet.get_all_records()
    for idx, record in enumerate(records, start=2):  # skip header
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
        print(f"✅ Inserted new session_id {session_id}")

def sync_all_leads():
    all_docs = collection.find()
    for doc in all_docs:
        upsert_google_sheet(doc)
