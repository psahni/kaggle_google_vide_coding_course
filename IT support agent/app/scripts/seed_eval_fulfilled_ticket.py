"""
Eval Seed Script: Seeds a 'fulfilled' ticket for EMP-002 (Bob Smith)
to test the scenario where an employee received a laptop recently
and now wants to request again because it's damaged.

Run this once before executing the damaged_laptop eval:
    uv run python app/scripts/seed_eval_fulfilled_ticket.py
"""
from datetime import datetime, timedelta, timezone
from google.cloud import firestore

db = firestore.Client()

def seed():
    # Simulate a ticket received 3 months ago
    three_months_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    ticket = {
        "ticket_id": "LT-EVAL-SEED-001",
        "created_at": three_months_ago,
        "received_at": three_months_ago,  # 3 months ago — within 1-year cooldown
        "status": "fulfilled",
        "approved_by": "manager",
        "manager_override": False,
        "requester": {
            "employee_id": "EMP-002",
            "name": "Bob Smith",
            "designation": "Senior Engineer",
            "department": "Engineering",
            "manager": "EMP-005"
        },
        "request": {
            "type": "New",
            "device_category": "Standard",
            "justification": "New laptop for work",
            "required_date": three_months_ago,
            "location": "San Francisco",
            "accessories": "None"
        },
        "audit_trail": [
            {
                "timestamp": three_months_ago,
                "actor": "employee",
                "action": "request_submitted",
                "details": "User submitted the laptop request."
            },
            {
                "timestamp": three_months_ago,
                "actor": "agent",
                "action": "policy_check_passed",
                "details": "Policy check completed. Path: Auto-approve"
            },
            {
                "timestamp": three_months_ago,
                "actor": "employee",
                "action": "laptop_received",
                "details": "Employee confirmed receipt of the laptop. 1-year cooldown period begins now."
            }
        ]
    }

    db.collection("tickets").document("LT-EVAL-SEED-001").set(ticket)
    print("Seeded fulfilled ticket LT-EVAL-SEED-001 for EMP-002.")
    print(f"  Received: {three_months_ago}")
    print("  Status: fulfilled")
    print("  This simulates Bob receiving a laptop 3 months ago.")

if __name__ == "__main__":
    seed()
