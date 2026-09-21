from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime

app = FastAPI(title="CrisisPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "reports_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"reports": []}
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {"reports": data}
            return data
    except Exception:
        return {"reports": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ReportInput(BaseModel):
    disaster_type: str
    description: str
    latitude: float
    longitude: float

@app.get("/")
def root():
    return {"status": "CrisisPilot Backend is running."}

@app.post("/api/v1/report")
def submit_report(report: ReportInput):
    db = load_db()
    report_id = f"RPT-{int(datetime.now().timestamp())}"
    
    new_report = {
        "report_id": report_id,
        "timestamp": datetime.now().isoformat(),
        "status": "AWAITING_REVIEW",
        "gov_response": "Report logged. Awaiting official triage and dispatch.",
        "resolved_at": None,
        "user_input": report.dict()
    }
    
    db["reports"].append(new_report)
    save_db(db)
    return {"status": "success", "report_id": report_id}

@app.get("/api/v1/reports")
def get_reports():
    db = load_db()
    reports = db.get("reports", [])
    sorted_reports = sorted(reports, key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"reports": sorted_reports}

@app.post("/api/v1/report/{report_id}/update")
async def update_report_status(report_id: str, status: str = Form(...), gov_note: str = Form(...)):
    db = load_db()
    reports = db.get("reports", [])
    updated = False
    
    for r in reports:
        if r["report_id"] == report_id:
            r["status"] = status
            r["gov_response"] = gov_note
            if status == "RESOLVED":
                r["resolved_at"] = datetime.now().isoformat()
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found")
        
    save_db(db)
    return {"status": "success", "report_id": report_id, "new_status": status}

@app.post("/api/v1/drone/deploy")
async def deploy_drone(target_lat: float = Form(...), target_lon: float = Form(...)):
    # Simple simulated telemetry calculation
    base_lat, base_lon = 27.7500, 85.4000
    import math
    dist = math.sqrt((target_lat - base_lat)**2 + (target_lon - base_lon)**2) * 111 # rough km conversion
    return {
        "status": "success",
        "telemetry": {
            "distance_km": round(dist, 2),
            "estimated_flight_time_mins": round(dist * 1.5, 1)
        }
    }