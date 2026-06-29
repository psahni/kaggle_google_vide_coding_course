import json
import os
from pathlib import Path
from google.cloud import firestore

DB_DIR = Path(__file__).parent.parent / "db"

def load_json(filename: str):
    file_path = DB_DIR / filename
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def migrate():
    print("Connecting to Firestore...")
    # Initialize Firestore client (uses Application Default Credentials)
    # This automatically picks up the GCP project from env vars if available.
    db = firestore.Client()
    
    # 1. Migrate Employees
    employees = load_json("employees.json") or []
    if employees:
        print(f"Migrating {len(employees)} employees...")
        for emp in employees:
            doc_id = emp["employee_id"]
            db.collection("employees").document(doc_id).set(emp)
            
    # 2. Migrate Policies
    policies = load_json("policies.json")
    if policies:
        print("Migrating policies config...")
        db.collection("policies").document("config").set(policies)
        
    # 3. Migrate Tickets
    tickets = load_json("tickets.json") or []
    if tickets:
        print(f"Migrating {len(tickets)} tickets...")
        for ticket in tickets:
            doc_id = ticket["ticket_id"]
            db.collection("tickets").document(doc_id).set(ticket)
            
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
