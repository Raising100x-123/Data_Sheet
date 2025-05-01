from fastapi import FastAPI
from sync import sync_all_leads

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/sync")
def sync_data():
    sync_all_leads()
    return {"status": "Synced"}
