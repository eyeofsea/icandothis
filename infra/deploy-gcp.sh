#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE_NAME="scm-risk"
DB_INSTANCE="${SERVICE_NAME}-pg"
REDIS_INSTANCE="${SERVICE_NAME}-redis"
NEO4J_VM="${SERVICE_NAME}-neo4j"

echo "=== SCM Risk Intelligence — GCP Deployment ==="
echo "Project: $PROJECT_ID | Region: $REGION"

# 1. Enable APIs
echo "[1/7] Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project="$PROJECT_ID"

# 2. Create Artifact Registry
echo "[2/7] Creating Artifact Registry..."
gcloud artifacts repositories create scm-risk \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || true

# 3. Cloud SQL (PostgreSQL)
echo "[3/7] Creating Cloud SQL instance..."
gcloud sql instances create "$DB_INSTANCE" \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --storage-auto-increase 2>/dev/null || echo "Instance exists"

gcloud sql databases create scm_risk_db \
  --instance="$DB_INSTANCE" \
  --project="$PROJECT_ID" 2>/dev/null || true

gcloud sql users create scmrisk \
  --instance="$DB_INSTANCE" \
  --password="$(openssl rand -base64 24)" \
  --project="$PROJECT_ID" 2>/dev/null || true

# 4. Memorystore (Redis)
echo "[4/7] Creating Memorystore Redis..."
gcloud redis instances create "$REDIS_INSTANCE" \
  --size=1 \
  --region="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || echo "Instance exists"

# 5. Build and push images
echo "[5/7] Building and pushing Docker images..."
REGISTRY="$REGION-docker.pkg.dev/$PROJECT_ID/scm-risk"

docker build -t "$REGISTRY/backend:latest" ./backend
docker push "$REGISTRY/backend:latest"

docker build -t "$REGISTRY/frontend:latest" ./frontend
docker push "$REGISTRY/frontend:latest"

# 6. Deploy backend to Cloud Run
echo "[6/7] Deploying backend..."
gcloud run deploy "${SERVICE_NAME}-api" \
  --image="$REGISTRY/backend:latest" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="NEO4J_URI=bolt://${NEO4J_VM}:7687,NEO4J_USER=neo4j" \
  --set-secrets="NEO4J_PASSWORD=neo4j-password:latest,ANTHROPIC_API_KEY=anthropic-key:latest,POSTGRES_PASSWORD=pg-password:latest,OPENSANCTIONS_API_KEY=opensanctions-key:latest,FREIGHT_API_KEY=freight-key:latest,NEWS_API_KEY=news-api-key:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:$DB_INSTANCE"

BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}-api" --region="$REGION" --format="value(status.url)")

# 7. Deploy frontend to Cloud Run
echo "[7/7] Deploying frontend..."
gcloud run deploy "${SERVICE_NAME}-web" \
  --image="$REGISTRY/frontend:latest" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --port=3000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"

FRONTEND_URL=$(gcloud run services describe "${SERVICE_NAME}-web" --region="$REGION" --format="value(status.url)")

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/health"
