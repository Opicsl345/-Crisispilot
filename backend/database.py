import json
import os

DB_FILE = "reports_db.json"

def load_database():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_database(database):
    with open(DB_FILE, "w") as f:
        json.dump(database, f, indent=4)

def add_report(new_report):
    db = load_database()
    db.insert(0, new_report)
    save_database(db)
    return db

def get_all_reports():
    return load_database()

def update_report_status(report_id, status, gov_note):
    db = load_database()
    for report in db:
        if report["report_id"] == report_id:
            report["status"] = status
            report["gov_response"] = gov_note
            save_database(db)
            return True
    return False