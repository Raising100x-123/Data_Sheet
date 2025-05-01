import gspread
import os
import json
from google.oauth2.service_account import Credentials
from pymongo import MongoClient
from pymongo import monitoring

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["ChatbotDB"]
collection = db["lead_data"]

# Google Sheet Setup (using environment variable)
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Load credentials from environment variable
service_account_info = json.loads(os.environ['GCP_SERVICE_ACCOUNT_JSON'])
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)

# Open Google Sheet
spreadsheet = client.open("Lead_Data")
sheet = spreadsheet.sheet1

def find_row_by_session_id(session_id):
    records = sheet.get_all_records()
    for idx, record in enumerate(records, start=2):  # start=2 because header is in row 1
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

    # Generate serial number (S.no) based on the number of rows in the sheet
    all_rows = sheet.get_all_records()
    serial_number = len(all_rows) + 1  # Auto-increment based on the current number of rows

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
        # Update existing row
        sheet.update(f'A{row_number}:I{row_number}', [row_data])
        print(f" Updated session_id {session_id} at row {row_number}")
    else:
        # Insert new row
        sheet.append_row(row_data)
        print(f" Inserted new session_id {session_id}")

# MongoDB Change Stream
print("⏳ Listening for MongoDB Changes...")

with collection.watch(full_document='updateLookup') as stream:
    for change in stream:
        if change['operationType'] in ['insert', 'update', 'replace']:
            doc = change['fullDocument']
            upsert_google_sheet(doc)
