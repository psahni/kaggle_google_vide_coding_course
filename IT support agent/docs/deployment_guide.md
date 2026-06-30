# Google Cloud Platform (GCP) Deployment Guide

This document describes the services, tools, and step-by-step instructions required to deploy the **IT Support Laptop Agent & Web Portal** on Google Cloud Platform.

---

## 1. Technologies & Google Cloud Services Used

| Service | Purpose | Details |
|---------|---------|---------|
| **Google Cloud Run** | Serverless Container Hosting | Runs the containerized Next.js frontend and Python backend services. Scalable to zero when idle to minimize cost. |
| **Google Cloud Firestore** | Database / Storage | NoSQL document database storing employee profiles, policies config, and ticket audit trails in Native mode. |
| **Vertex AI API / Gemini API** | Conversational AI Engine | Powers the backend agent using the Vertex-integrated `gemini-3-flash-preview` or `gemini-3.1-pro-preview` model. |
| **Artifact Registry** | Container Image Management | Hosts the built Docker container images for both frontend and backend services. |
| **Cloud Secret Manager** | Secure Secrets Management | Stores database credentials, session secrets, and application API keys securely. |
| **Cloud IAM** | Security & Access Control | Restricts service account permissions following the principle of least privilege. |

---

## 2. Infrastructure Setup & IAM Permissions

### Step A: Enable GCP APIs
Execute the following gcloud command to enable all necessary APIs:
```bash
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com
```

### Step B: Create a Dedicated Service Account
Create a service account that Cloud Run will assume:
```bash
gcloud iam service-accounts create it-support-agent-sa \
    --description="Service account for IT support agent and portal" \
    --display-name="IT Support Agent SA"
```

### Step C: Assign IAM Roles
Assign roles to allow the service account to access Firestore, Vertex AI, and Secret Manager:
```bash
# Firestore Access
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:it-support-agent-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# Vertex AI Model Execution
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:it-support-agent-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## 3. Database (Firestore) Initialization

1. Open the [Google Cloud Console](https://console.cloud.google.com).
2. Navigate to **Firestore** and select **Create Database**.
3. Choose **Native Mode** (required for real-time listeners and offline SDK updates).
4. Select your preferred region (e.g., `us-east1` or `asia-east1`).
5. Populate the database by running the seed script locally (make sure your local credentials are authenticated via `gcloud auth application-default login`):
   ```bash
   uv run python app/scripts/migrate_to_firestore.py
   uv run python app/scripts/seed_eval_fulfilled_ticket.py
   ```

---

## 4. Frontend (Next.js) Deployment

### Step A: Add `Dockerfile` in `/frontend`
Create `frontend/Dockerfile` to compile and package the Next.js app:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

### Step B: Build and Deploy to Cloud Run
Build the container image using Cloud Build and deploy to Cloud Run:
```bash
# Build the image in Artifact Registry
gcloud builds submit --tag gcr.io/[PROJECT_ID]/it-support-frontend ./frontend

# Deploy to Cloud Run
gcloud run deploy it-support-frontend \
    --image gcr.io/[PROJECT_ID]/it-support-frontend \
    --platform managed \
    --region us-east1 \
    --service-account it-support-agent-sa@[PROJECT_ID].iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-env-vars=NEXT_PUBLIC_FIRESTORE_PROJECT_ID=[PROJECT_ID]
```

---

## 5. Backend (Python Agent) Deployment

### Step A: Add `Dockerfile` in `/app`
Create a `Dockerfile` in the root (pointing to the Python app module):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.agent_engine_app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step B: Build and Deploy to Cloud Run
Build the container image and deploy:
```bash
# Build the backend image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/it-support-backend .

# Deploy to Cloud Run
gcloud run deploy it-support-backend \
    --image gcr.io/[PROJECT_ID]/it-support-backend \
    --platform managed \
    --region us-east1 \
    --service-account it-support-agent-sa@[PROJECT_ID].iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=[PROJECT_ID],GOOGLE_CLOUD_LOCATION=us-east1
```

---

## 6. Security & Hardening Checklist

1. **Restrict Service Account scope**: Never grant `roles/owner` or `roles/editor` to the Cloud Run service account. Limit it to `roles/datastore.user` and `roles/aiplatform.user`.
2. **Setup Custom Domains**: Map custom domains with SSL certificate bindings using Cloud Run domain mapping or Cloud Load Balancing.
3. **Environment Secrets**: Do not store Firestore database credential files in the container image. When running on GCP, the Firestore Client initializes automatically using the service account's default credentials.
