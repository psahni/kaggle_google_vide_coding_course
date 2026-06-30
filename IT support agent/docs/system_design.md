# IT Support Laptop Agent: System Architecture & Workflow Design

This document details the system architecture, data models, and request flows of the IT Support Laptop Request agent.

---

## 1. High-Level System Architecture

The system consists of three main parts:
1. **Conversational Agent (Backend)**: Orchestrates the user experience, checks policy constraints, evaluates eligibility, and creates requests.
2. **Web Portal (Frontend)**: Next.js dashboard where Managers and Finance teams log in using Employee ID to approve, reject, and review ticket histories.
3. **Database Layer (Firestore)**: Single source of truth containing employees, policies, and tickets.

```mermaid
graph TD
    %% Define Styles
    style Employee fill:#d0e1fd,stroke:#1a73e8,stroke-width:2px;
    style Agent fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px;
    style Portal fill:#e6f4ea,stroke:#137333,stroke-width:2px;
    style DB fill:#fef7e0,stroke:#b06000,stroke-width:2px;
    style Manager fill:#fce8e6,stroke:#c5221f,stroke-width:2px;

    %% Elements
    Employee(Employee / User Chat) -->|1. Request Laptop| Agent(Conversational AI Agent)
    Agent -->|2. Query & Write| DB[(Google Cloud Firestore)]
    
    Portal(Manager & Finance Web Portal) -->|3. Query & Action| DB
    Manager(Manager / Finance User) -->|4. Approve / Reject / Comment| Portal

    subgraph Firebase / GCP
        DB
    end
```

---

## 2. Core Request Flow & Policy Engine

Below is the detailed workflow that executes when an employee requests a laptop. This covers **Pre-Flight Checks**, **Dynamic Device Allocation**, **Cooldown Verification**, and **Approval Routing**.

```mermaid
sequenceDiagram
    autonumber
    actor User as Employee
    participant Agent as Conversational Agent
    participant DB as Firestore Database
    participant Policy as Policy Engine (check_policy)
    actor Mgr as Manager / Finance

    User->>Agent: "I need a replacement laptop"
    Agent->>DB: Lookup Employee (EMP ID)
    DB-->>Agent: Return designation, experience, manager info

    Note over Agent, DB: Pre-Flight Check (check_existing_requests)
    Agent->>DB: Query tickets for Employee
    DB-->>Agent: Return active, pending, or fulfilled tickets

    alt Active/Pending Request Exists
        Agent-->>User: BLOCK: "You already have a ticket in progress."
    else Laptop Received < 365 Days Ago
        Agent->>User: Prompt for replacement justification (damaged, slow, defective, etc.)
        User-->>Agent: Provides justification (e.g. "Screen is broken")
        alt Justification matches bypass keywords (slow, RAM, broken, defective)
            Agent->>Agent: Pass pre-flight (Set status to warn_defective)
        else Justification is generic/missing
            Agent-->>User: BLOCK: "Requests within 1 year are not permitted unless defective/damaged/performance issues are stated."
        end
    end

    Note over Agent, Policy: Context Collection & Policy Evaluation
    Agent->>Agent: Auto-determine device tier (designation & experience)<br/>• Mgr or Experience >= 7 yrs -> Premium<br/>• Others -> Standard
    Agent->>Policy: check_policy(EMP ID, designation, experience, type, resolved_device)
    
    Note over Policy: Policy checks:<br/>1. Designation base tier<br/>2. Experience overrides (>=7 yrs to Premium, >=10 yrs to Auto-approve)<br/>3. Cooldown overrides (Force to manager approval if received within 1 year)
    
    Policy-->>Agent: Return resolved tier, path, and descriptive reasoning
    
    Agent->>DB: create_ticket(requester, request, path, policy_reason)
    DB-->>Agent: Ticket created (approved OR pending_manager_approval)

    alt Path is 'Auto-approve'
        Agent-->>User: "Approved! Confirmed MacBook Pro 14 (Standard). Please confirm receipt once delivered."
        User->>Agent: "I have received it."
        Agent->>DB: mark_received(ticket_id) -> Sets received_at (Starts 1-year cooldown)
    else Path requires approval
        Agent-->>User: "Ticket created. Awaiting manager approval."
        Mgr->>DB: Approves ticket on Web Portal -> Status set to 'approved'
        User->>Agent: "I have received the laptop."
        Agent->>DB: mark_received(ticket_id) -> Sets received_at (Starts 1-year cooldown)
    end
```

---

## 3. Web Portal Actions & Lifecycle States

The Web Portal enforces different permissions for **Managers** (who can only see and approve tickets for their direct reports) and **Finance** (who can view and action all tickets).

### Ticket State Transitions
```mermaid
stateDiagram-v2
    [*] --> pending_manager_approval : Ticket Created (Requires Approval)
    [*] --> approved : Ticket Created (Auto-Approved)
    
    pending_manager_approval --> approved : Manager Approves (Portal)
    pending_manager_approval --> rejected : Manager Rejects (Portal)
    
    approved --> fulfilled : Employee confirms receipt (mark_received)
    rejected --> [*]
    fulfilled --> [*] : Starts 1-Year Cooldown Clock
```

---

## 4. Firestore Data Models

### `employees` collection
```json
{
  "employee_id": "EMP-002",
  "name": "Bob Smith",
  "designation": "Senior Engineer",
  "experience": 8,
  "department": "Engineering",
  "manager": "EMP-005",
  "location": "Remote",
  "cost_center": "CC-ENG-02",
  "employment_type": "Full-time"
}
```

### `tickets` collection
```json
{
  "ticket_id": "LT-2026-61803",
  "created_at": "2026-06-30T12:47:18Z",
  "received_at": "2026-06-30T12:55:00Z",
  "requester": {
    "employee_id": "EMP-002",
    "name": "Bob Smith",
    "designation": "Senior Engineer",
    "manager": "EMP-005"
  },
  "request": {
    "type": "Replacement",
    "device_category": "Premium",
    "justification": "My laptop screen is cracked and damaged",
    "accessories": "None"
  },
  "status": "fulfilled",
  "approved_by": "EMP-005",
  "manager_override": false,
  "policy_reason": "Employee designation 'Senior Engineer' is entitled to MacBook Pro 14 (Standard tier). Device tier upgraded to Premium based on experience override (8 years >= 7). Cooldown is active. Auto-approval revoked; forced to Manager required.",
  "audit_trail": [
    {
      "timestamp": "2026-06-30T12:47:18Z",
      "actor": "employee",
      "action": "request_submitted",
      "details": "User submitted the laptop request."
    },
    {
      "timestamp": "2026-06-30T12:47:18Z",
      "actor": "agent",
      "action": "policy_check_passed",
      "details": "Policy check completed. Path: Manager required. Reason: ..."
    },
    {
      "timestamp": "2026-06-30T12:50:00Z",
      "actor": "manager",
      "action": "approved",
      "details": "Approved via Web Portal."
    },
    {
      "timestamp": "2026-06-30T12:55:00Z",
      "actor": "employee",
      "action": "laptop_received",
      "details": "Employee confirmed receipt. 1-year cooldown starts."
    }
  ]
}
```
