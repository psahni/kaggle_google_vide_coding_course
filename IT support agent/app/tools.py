import json
import random
import string
from datetime import datetime, timedelta, timezone
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()

def _generate_ticket_id() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"LT-{date_str}-{suffix}"

def check_existing_requests(employee_id: str, new_request_type: str = "", replacement_reason: str = "") -> str:
    """Checks if an employee has any active, pending, or recent completed tickets.

    Must be called immediately after lookup_employee and before creating any new ticket.
    Returns a status of 'clear', 'blocked', 'warn', or 'warn_defective'.

    Args:
        employee_id: The employee ID to check.
        new_request_type: The type of new request being made (e.g., Replacement, New, Upgrade).
        replacement_reason: For Replacement requests only — the reason given by the employee
            (e.g., 'damaged', 'aging', 'lost', 'stolen', 'defective'). Only a reason of
            'defective' or 'not working' will bypass the 1-year cooldown.

    Returns:
        A JSON string with a 'status' field and additional context.
    """
    tickets_ref = db.collection("tickets")
    # Query all tickets for this employee
    query = tickets_ref.where(filter=firestore.FieldFilter("requester.employee_id", "==", employee_id))
    docs = query.stream()

    active_ticket = None
    recent_fulfilled_ticket = None
    last_rejected_ticket = None
    now = datetime.now(timezone.utc)

    for doc in docs:
        ticket = doc.to_dict()
        status = ticket.get("status", "")
        created_at_str = ticket.get("created_at", "")

        # Parse ticket creation timestamp
        try:
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            created_at = None

        # Parse received_at timestamp (when laptop was physically handed over)
        received_at_str = ticket.get("received_at")
        try:
            received_at = datetime.fromisoformat(received_at_str) if received_at_str else None
            if received_at and received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            received_at = None

        if status in ("pending_manager_approval", "approved"):
            # Active: still in the approval or dispatch pipeline
            active_ticket = ticket
        elif status == "fulfilled" and received_at:
            # Check if still within the 1-year cooldown:
            # (today - received_at) < 1 year → cooldown not yet expired → block
            time_since_received = now - received_at
            if time_since_received < timedelta(days=365):
                recent_fulfilled_ticket = ticket
        elif status == "rejected":
            # Keep track of the most recent rejection
            if last_rejected_ticket is None or (created_at and created_at > datetime.fromisoformat(
                    last_rejected_ticket.get("created_at", "2000-01-01")).replace(tzinfo=timezone.utc)):
                last_rejected_ticket = ticket

    # Priority: active > fulfilled cooldown > rejected
    if active_ticket:
        return json.dumps({
            "status": "blocked",
            "reason": "You already have an active or pending laptop request.",
            "existing_ticket_id": active_ticket["ticket_id"],
            "existing_ticket_status": active_ticket["status"],
            "message": f"Cannot create a new ticket. Existing ticket {active_ticket['ticket_id']} is currently '{active_ticket['status']}'. Please wait for it to be resolved or ask your manager to override."
        })

    if recent_fulfilled_ticket:
        # Special case: defective laptop — only bypass cooldown if employee explicitly says it's defective
        is_defective = any(word in replacement_reason.lower() for word in ["defective", "not working", "doesn't work", "dead", "faulty"])
        if new_request_type.lower() == "replacement" and is_defective:
            return json.dumps({
                "status": "warn_defective",
                "reason": "A laptop was issued to you within the last year, but a defective device replacement is allowed.",
                "existing_ticket_id": recent_fulfilled_ticket["ticket_id"],
                "message": "You received a laptop recently. Since you have reported it as defective, a replacement is permitted but requires mandatory manager approval."
            })
        return json.dumps({
            "status": "blocked",
            "reason": "You already received a laptop within the last 365 days.",
            "existing_ticket_id": recent_fulfilled_ticket["ticket_id"],
            "message": f"Cannot create a new ticket. A laptop was issued under ticket {recent_fulfilled_ticket['ticket_id']} less than a year ago. Your manager can override this policy if there is a valid reason."
        })

    if last_rejected_ticket:
        # Find rejection reason from audit trail
        audit = last_rejected_ticket.get("audit_trail", [])
        rejection_entry = next((e for e in reversed(audit) if e.get("action") == "manager_rejected"), None)
        rejection_reason = rejection_entry["details"] if rejection_entry else "No reason provided."
        return json.dumps({
            "status": "warn",
            "reason": "Your last request was rejected.",
            "existing_ticket_id": last_rejected_ticket["ticket_id"],
            "rejection_reason": rejection_reason,
            "message": f"Your previous request ({last_rejected_ticket['ticket_id']}) was rejected. Reason: {rejection_reason}. You may submit a new request with a stronger justification."
        })

    return json.dumps({"status": "clear", "message": "No conflicting tickets found. You may proceed."})

def lookup_employee(employee_id: str) -> str:
    """Looks up an employee record by their ID."""
    doc = db.collection("employees").document(employee_id).get()
    if doc.exists:
        return json.dumps(doc.to_dict())
    return f"Employee with ID {employee_id} not found."

def check_policy(employee_id: str, designation: str, experience: int, request_type: str, device: str) -> str:
    """Checks the laptop request policy to determine entitlements and approval path.

    Args:
        employee_id: The ID of the employee making the request.
        designation: Employee's job title/designation.
        experience: Employee's years of experience.
        request_type: The type of request (e.g., New, Upgrade, Replacement, New Hire).
        device: The device category requested (e.g., standard, premium).

    Returns:
        A JSON string containing the entitled_device, tier, and required approval_path.
    """
    policies_doc = db.collection("policies").document("config").get()
    if not policies_doc.exists:
        return json.dumps({"error": "Policy configuration not found in database."})
    
    policies = policies_doc.to_dict()
    entitlements = policies.get("designation_entitlements", {})
    request_rules = policies.get("request_type_rules", [])

    base_entitlement = entitlements.get(designation)
    if not base_entitlement:
        return json.dumps({"error": f"No entitlement found for designation: {designation}"})

    tier = base_entitlement["tier"]
    entitled_device = base_entitlement["entitled_device"]

    # Experience overrides
    if experience >= 10:
        tier = "Premium"
    elif experience >= 7:
        tier = "Premium"

    # Determine the condition to match based on the requested device/reason
    device_condition = ""
    if request_type.lower() == "new":
        device_condition = "Premium device" if "premium" in device.lower() else "Standard device"
    elif request_type.lower() == "upgrade":
        requested_tier = "Premium" if "premium" in device.lower() else "Standard"
        device_condition = f"{tier} -> {requested_tier}"
    elif request_type.lower() == "replacement":
        if "stolen" in device.lower():
            device_condition = "Stolen"
        elif "lost" in device.lower():
            device_condition = "Lost"
        else:
            device_condition = "Damaged / Aging"
    elif request_type.lower() == "new hire":
        device_condition = "Premium" if "premium" in device.lower() else "Standard"

    approval_path = "Manager required"
    for rule in request_rules:
        if rule["request_type"].lower() == request_type.lower():
            if rule.get("condition", "").lower() == device_condition.lower():
                approval_path = rule["approval_path"]
                break

    # Overrides apply
    if experience >= 10:
        approval_path = "Auto-approve"

    # Check if employee has a completed/fulfilled ticket within the last 365 days
    has_recent_laptop = False
    tickets_ref = db.collection("tickets")
    query = tickets_ref.where(filter=firestore.FieldFilter("requester.employee_id", "==", employee_id))
    docs = query.stream()
    now = datetime.now(timezone.utc)
    for doc in docs:
        t = doc.to_dict()
        if t.get("status") == "fulfilled":
            received_at_str = t.get("received_at")
            if received_at_str:
                try:
                    received_at = datetime.fromisoformat(received_at_str)
                    if received_at.tzinfo is None:
                        received_at = received_at.replace(tzinfo=timezone.utc)
                    time_since_received = now - received_at
                    if time_since_received < timedelta(days=365):
                        has_recent_laptop = True
                        break
                except (ValueError, TypeError):
                    pass

    # Cooldown enforcement: if they received a laptop within 1 year, any auto-approval is revoked
    # and replaced with "Manager required". Other stricter paths (like Manager + Finance) remain active.
    if has_recent_laptop and approval_path.lower() == "auto-approve":
        approval_path = "Manager required"

    return json.dumps({
        "entitled_device": entitled_device,
        "tier": tier,
        "approval_path": approval_path
    })

def create_ticket(requester: dict, request: dict, approval_path: str, manager_override: bool = False) -> str:
    """Creates a new laptop request ticket.

    Args:
        requester: Dictionary containing employee details (name, employee_id, designation, department, manager).
        request: Dictionary containing request details (type, device_category, justification, required_date, location, accessories).
        approval_path: The required approval path determined by check_policy.
        manager_override: Set to True if a manager explicitly overrode a policy block to allow this ticket.

    Returns:
        A JSON string containing the generated ticket ID and initial status.
    """
    ticket_id = _generate_ticket_id()
    
    # Check if employee has a completed/fulfilled ticket within the last 365 days for double-safety
    has_recent_laptop = False
    tickets_ref = db.collection("tickets")
    query = tickets_ref.where(filter=firestore.FieldFilter("requester.employee_id", "==", requester.get("employee_id")))
    docs = query.stream()
    now = datetime.now(timezone.utc)
    for doc in docs:
        t = doc.to_dict()
        if t.get("status") == "fulfilled":
            received_at_str = t.get("received_at")
            if received_at_str:
                try:
                    received_at = datetime.fromisoformat(received_at_str)
                    if received_at.tzinfo is None:
                        received_at = received_at.replace(tzinfo=timezone.utc)
                    time_since_received = now - received_at
                    if time_since_received < timedelta(days=365):
                        has_recent_laptop = True
                        break
                except (ValueError, TypeError):
                    pass

    status = "pending_manager_approval"
    if approval_path.lower() == "auto-approve" and not has_recent_laptop:
        # Auto-approved: laptop is being arranged. Cooldown starts only when mark_received is called.
        status = "approved"
    elif "finance" in approval_path.lower():
        status = "pending_manager_approval"
    else:
        status = "pending_manager_approval"

    now_str = datetime.now().isoformat()

    new_ticket = {
        "ticket_id": ticket_id,
        "created_at": now_str,
        "received_at": None,  # Set when employee confirms laptop received via mark_received tool
        "requester": requester,
        "request": request,
        "status": status,
        "approved_by": None,
        "manager_override": manager_override,
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

    # Log manager override in audit trail if applicable
    if manager_override:
        new_ticket["audit_trail"].append({
            "timestamp": now_str,
            "actor": "manager",
            "action": "manager_override_applied",
            "details": "Manager explicitly overrode a policy block to allow this request."
        })

    db.collection("tickets").document(ticket_id).set(new_ticket)

    return json.dumps({
        "ticket_id": ticket_id,
        "status": status,
        "message": "Ticket created successfully."
    })

def approve_request(ticket_id: str, approved: bool, reason: str) -> str:
    """Approves or rejects a pending ticket."""
    doc_ref = db.collection("tickets").document(ticket_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})
        
    ticket = doc.to_dict()
    now_str = datetime.now().isoformat()

    if approved:
        ticket["status"] = "approved"  # Laptop is being dispatched; awaiting mark_received
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

    doc_ref.set(ticket)
    return json.dumps({"ticket_id": ticket_id, "status": ticket["status"], "message": "Ticket updated."})

def mark_received(ticket_id: str) -> str:
    """Marks a laptop as physically received by the employee, starting the 1-year cooldown period.

    This must be called when the employee confirms they have received the laptop.
    The 1-year cooldown for new requests starts from this moment, not from ticket creation.

    Args:
        ticket_id: The ID of the approved ticket to mark as fulfilled.

    Returns:
        A JSON string confirming the fulfillment.
    """
    doc_ref = db.collection("tickets").document(ticket_id)
    doc = doc_ref.get()

    if not doc.exists:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})

    ticket = doc.to_dict()
    if ticket["status"] != "approved":
        return json.dumps({"error": f"Ticket {ticket_id} is not in 'approved' state. Current status: {ticket['status']}."})

    now_str = datetime.now().isoformat()
    ticket["status"] = "fulfilled"
    ticket["received_at"] = now_str  # 1-year cooldown starts from here
    ticket["audit_trail"].append({
        "timestamp": now_str,
        "actor": "employee",
        "action": "laptop_received",
        "details": "Employee confirmed receipt of the laptop. 1-year cooldown period begins now."
    })

    doc_ref.set(ticket)
    return json.dumps({
        "ticket_id": ticket_id,
        "status": "fulfilled",
        "received_at": now_str,
        "message": "Laptop marked as received. Your 1-year cooldown period has started."
    })

def get_status(ticket_id: str) -> str:
    """Retrieves the current status and last 3 audit entries of a ticket."""
    doc = db.collection("tickets").document(ticket_id).get()
    
    if not doc.exists:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})
        
    ticket = doc.to_dict()
    audit = ticket.get("audit_trail", [])
    last_3 = audit[-3:] if len(audit) >= 3 else audit
    
    return json.dumps({
        "ticket_id": ticket_id,
        "status": ticket["status"],
        "recent_audit_trail": last_3
    })
