import json
import os
import random
import string
from datetime import datetime
from pathlib import Path

DB_DIR = Path(__file__).parent / "db"

def _load_json(filename: str):
    file_path = DB_DIR / filename
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(filename: str, data):
    file_path = DB_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _generate_ticket_id() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"LT-{date_str}-{suffix}"

def lookup_employee(employee_id: str) -> str:
    """Looks up an employee record by their ID.

    Args:
        employee_id: The ID of the employee to look up (e.g., EMP-001)

    Returns:
        A JSON string representation of the employee record or an error message.
    """
    employees = _load_json("employees.json") or []
    for emp in employees:
        if emp.get("employee_id") == employee_id:
            return json.dumps(emp)
    return f"Employee with ID {employee_id} not found."

def check_policy(designation: str, experience: int, request_type: str, device: str) -> str:
    """Checks the laptop request policy to determine entitlements and approval path.

    Args:
        designation: Employee's job title/designation.
        experience: Employee's years of experience.
        request_type: The type of request (e.g., New, Upgrade, Replacement, New Hire).
        device: The device category requested (e.g., standard, premium).

    Returns:
        A JSON string containing the entitled_device, tier, and required approval_path.
    """
    policies = _load_json("policies.json") or {}
    entitlements = policies.get("designation_entitlements", {})
    request_rules = policies.get("request_type_rules", [])

    # 1. Determine base entitlement from designation
    base_entitlement = entitlements.get(designation)
    if not base_entitlement:
        return json.dumps({"error": f"No entitlement found for designation: {designation}"})

    tier = base_entitlement["tier"]
    entitled_device = base_entitlement["entitled_device"]

    # Experience overrides
    if experience >= 10:
        tier = "Premium" # 10+ years -> premium auto-approved path applies
    elif experience >= 7:
        tier = "Premium" # 7+ years -> eligible for senior tier device

    # Determine the condition to match based on the requested device/reason
    device_condition = ""
    if request_type.lower() == "new":
        device_condition = "Premium device" if "premium" in device.lower() else "Standard device"
    elif request_type.lower() == "upgrade":
        requested_tier = "Premium" if "premium" in device.lower() else "Standard"
        device_condition = f"{tier} -> {requested_tier}"
    elif request_type.lower() == "replacement":
        # For replacements, the "device" parameter should hold the reason
        if "stolen" in device.lower():
            device_condition = "Stolen"
        elif "lost" in device.lower():
            device_condition = "Lost"
        else:
            device_condition = "Damaged / Aging"
    elif request_type.lower() == "new hire":
        device_condition = "Premium" if "premium" in device.lower() else "Standard"

    approval_path = "Manager required" # default fallback
    for rule in request_rules:
        if rule["request_type"].lower() == request_type.lower():
            if rule.get("condition", "").lower() == device_condition.lower():
                approval_path = rule["approval_path"]
                break

    # Overrides apply
    if experience >= 10:
        approval_path = "Auto-approve"

    return json.dumps({
        "entitled_device": entitled_device,
        "tier": tier,
        "approval_path": approval_path
    })

def create_ticket(requester: dict, request: dict, approval_path: str) -> str:
    """Creates a new laptop request ticket.

    Args:
        requester: Dictionary containing employee details (name, employee_id, designation, department, manager).
        request: Dictionary containing request details (type, device_category, justification, required_date, location, accessories).
        approval_path: The required approval path determined by check_policy.

    Returns:
        A JSON string containing the generated ticket ID and initial status.
    """
    tickets = _load_json("tickets.json")
    if tickets is None:
        tickets = []

    ticket_id = _generate_ticket_id()

    # Determine initial status based on approval path
    status = "submitted"
    if approval_path.lower() == "auto-approve":
        status = "approved"
    elif "finance" in approval_path.lower():
        status = "pending_manager_approval" # First step is manager
    else:
        status = "pending_manager_approval"

    now_str = datetime.now().isoformat()

    new_ticket = {
        "ticket_id": ticket_id,
        "created_at": now_str,
        "requester": requester,
        "request": request,
        "status": status,
        "approved_by": None,
        "audit_trail": [
            {
                "timestamp": now_str,
                "actor": "employee",
                "action": "request_submitted",
                "details": "User submitted the laptop request."
            },
            {
                "timestamp": now_str,
                "actor": "agent",
                "action": "policy_check_passed",
                "details": f"Policy check completed. Path: {approval_path}"
            }
        ]
    }

    tickets.append(new_ticket)
    _save_json("tickets.json", tickets)

    return json.dumps({
        "ticket_id": ticket_id,
        "status": status,
        "message": "Ticket created successfully."
    })

def approve_request(ticket_id: str, approved: bool, reason: str) -> str:
    """Approves or rejects a pending ticket.

    Args:
        ticket_id: The ID of the ticket.
        approved: True if approved, False if rejected.
        reason: Reason for approval or rejection.

    Returns:
        A JSON string with the updated status.
    """
    tickets = _load_json("tickets.json") or []
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            now_str = datetime.now().isoformat()

            if approved:
                ticket["status"] = "approved"
                action = "manager_approved"
                details = f"Request approved. Reason: {reason}"
            else:
                ticket["status"] = "rejected"
                action = "manager_rejected"
                details = f"Request rejected. Reason: {reason}"

            ticket["approved_by"] = "manager"
            ticket["audit_trail"].append({
                "timestamp": now_str,
                "actor": "manager",
                "action": action,
                "details": details
            })

            # If it was an auto-approve path or just got approved, log fulfillment
            if approved:
                ticket["audit_trail"].append({
                    "timestamp": now_str,
                    "actor": "system",
                    "action": "ticket_fulfilled",
                    "details": "Ticket is ready for fulfillment."
                })
                ticket["status"] = "completed"

            _save_json("tickets.json", tickets)
            return json.dumps({"ticket_id": ticket_id, "status": ticket["status"], "message": "Ticket updated."})

    return json.dumps({"error": f"Ticket {ticket_id} not found."})

def get_status(ticket_id: str) -> str:
    """Retrieves the current status and last 3 audit entries of a ticket.

    Args:
        ticket_id: The ID of the ticket.

    Returns:
        A JSON string with status and audit trail.
    """
    tickets = _load_json("tickets.json") or []
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            audit = ticket.get("audit_trail", [])
            last_3 = audit[-3:] if len(audit) >= 3 else audit
            return json.dumps({
                "ticket_id": ticket_id,
                "status": ticket["status"],
                "recent_audit_trail": last_3
            })

    return json.dumps({"error": f"Ticket {ticket_id} not found."})
