# Database Setup and Configuration

This directory contains the database structure, local schemas, and setup utilities for the IT Support Laptop Lifecycle Management system. The application operates in two modes: **Local File Database** (for local testing/evaluations) and **Google Cloud Firestore** (for production deployments).

---

## 1. Local File Database (JSON)
For local development, testing, and ADK evaluations, the database is stored as simple JSON files in this directory. 

* **[employees.json](app/db/employees.json)**: Contains employee records including names, designations, experience, department, and manager information.
* **[policies.json](app/db/policies.json)**: Stores policy parameters such as device model configurations, tier rules, experience upgrade thresholds, and cooldown durations.
* **[tickets.json](app/db/tickets.json)**: Stores ticket data, approvals, comments, and audit trails.

---

## 2. Production Database (Google Cloud Firestore)
The live cloud deployment uses Google Cloud Firestore in Native mode. The schema mirrors the JSON structure above, organized into three collections:
1. `employees`
2. `policies`
3. `tickets`

---

## 3. How to Set Up and Seed Firestore

To initialize your production database in Google Cloud:

### Step A: Authenticate with Google Cloud
Ensure you are authenticated and have configured your active project:
```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

### Step B: Create Firestore Database
Create a Firestore database in Native mode (if not already done):
```bash
gcloud alpha firestore databases create --location=us-east1
```

### Step C: Seed Employee and Policy Collections
Run the migration script to copy your local `employees.json` and `policies.json` data into Firestore collections:
```bash
uv run python app/scripts/migrate_to_firestore.py
```

### Step D: Seed Initial Test Tickets
To populate initial sample tickets (supporting 1-year cooldown validation scenarios), run the ticket seeder script:
```bash
uv run python app/scripts/seed_eval_fulfilled_ticket.py
```

---

## 4. Next.js Web Portal Connection
The Next.js frontend application connects directly to the Firestore database to serve the ticket dashboard and process approvals.

* **SDK/Driver**: Utilizes the `firebase-admin` Node.js library for secure, server-side database connectivity.
* **Initialization**: Configured in [db.ts](../../frontend/lib/db.ts) using the target GCP Project ID.
* **Environment Variables**: Reads `GOOGLE_CLOUD_PROJECT` to determine the target database. When deployed on Google Cloud Run, it automatically inherits permissions from the runtime's service account to query Firestore without local credential JSON files.

