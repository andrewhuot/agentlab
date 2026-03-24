#!/usr/bin/env bash
set -euo pipefail

# AutoAgent VNextCC — One-command Google Cloud deployment
# Usage: ./deploy/deploy.sh [PROJECT_ID] [REGION]

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${2:-us-central1}"
REPO="autoagent"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/autoagent-vnextcc"
TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: No project ID. Pass as argument or set via 'gcloud config set project PROJECT_ID'"
  exit 1
fi

echo "==> Deploying AutoAgent VNextCC"
echo "    Project: ${PROJECT_ID}"
echo "    Region:  ${REGION}"
echo "    Image:   ${IMAGE}:${TAG}"
echo ""

# Ensure Artifact Registry repo exists
gcloud artifacts repositories describe "$REPO" \
  --project="$PROJECT_ID" --location="$REGION" 2>/dev/null || \
gcloud artifacts repositories create "$REPO" \
  --project="$PROJECT_ID" --location="$REGION" \
  --repository-format=docker \
  --description="AutoAgent container images"

# Configure Docker auth
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Build and push
echo "==> Building container image..."
docker build -t "${IMAGE}:${TAG}" -t "${IMAGE}:latest" .
docker push "${IMAGE}:${TAG}"
docker push "${IMAGE}:latest"

# Deploy to Cloud Run
echo "==> Deploying to Cloud Run..."
gcloud run deploy autoagent-vnextcc \
  --image "${IMAGE}:${TAG}" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "AUTOAGENT_DB=/app/data/conversations.db,AUTOAGENT_CONFIGS=/app/data/configs"

echo ""
echo "==> Deployment complete!"
gcloud run services describe autoagent-vnextcc \
  --project "$PROJECT_ID" --region "$REGION" \
  --format="value(status.url)"
