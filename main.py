from sync import sync_all_leads

# Example FastAPI usage
from fastapi import FastAPI

app = FastAPI()

@app.get("/sync-now")
def trigger_sync():
    sync_all_leads()
    return {"message": "Manual sync complete."}
