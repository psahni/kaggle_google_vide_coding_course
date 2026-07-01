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

## 3. Database (Firestore) Configuration

1. **Database Instance**: This deployment continues to use the existing development Firestore database instance:
   * **GCP Project ID**: `ambient-agent-500404`
2. **Access Bindings**: Ensure the dedicated service account has standard user access to this project (`ambient-agent-500404`).
3. **Data Verification**: Since the database is already fully initialized and seeded with employee schemas and current ticket logs, no new migration or seed scripts are required for deployment.

---

## 4. Frontend (Next.js) Deployment

### Step A: Add `Dockerfile` in `/frontend`
Create `frontend/Dockerfile` to compile and package the Next.js app:
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
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

The backend Conversational Agent is packaged and registered directly to the **Vertex AI Agent Engine** (Reasoning Engine) platform using the ADK deployment configuration.

### Step A: Deploy to Vertex AI
Ensure you are logged into gcloud, have set the correct project context, and run the deployment target:
```bash
# Windows PowerShell (UTF-8 encoding required for output symbols)
$env:PYTHONIOENCODING="utf-8"
make deploy

# Linux/macOS
make deploy
```
This script exports the agent's dependencies into `app/app_utils/.requirements.txt`, packages the code, and calls the Vertex AI preview libraries to register the Reasoning Engine in the `us-east1` region.

Under the hood, `make deploy` executes the [deploy.py](file:///e:/Prashant/development/2026/ag2-projects/IT%20support%20agent/app/app_utils/deploy.py) script. This helper script is provided by the Google Cloud Platform Agent Starter Pack template to handle parameter wrapping, env secret injections, and Reasoning Engine client requests.

### Step B: Verify Deployed Metadata
Upon successful deployment, the unique Reasoning Engine resource ID is written to `deployment_metadata.json` in the root of the project.


---

## 6. Security & Hardening Checklist

1. **Restrict Service Account scope**: Never grant `roles/owner` or `roles/editor` to the Cloud Run service account. Limit it to `roles/datastore.user` and `roles/aiplatform.user`.
2. **Setup Custom Domains**: Map custom domains with SSL certificate bindings using Cloud Run domain mapping or Cloud Load Balancing.
3. **Environment Secrets**: Do not store Firestore database credential files in the container image. When running on GCP, the Firestore Client initializes automatically using the service account's default credentials.
