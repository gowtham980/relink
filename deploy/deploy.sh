#!/usr/bin/env bash
# Deploy Relink coach + web to Cloud Run (gcpdevelopment-464720 by default)
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-gcpdevelopment-464720}"
REGION="${REGION:-us-central1}"
AR_REPO="${AR_REPO:-relink}"
COACH_SERVICE="${COACH_SERVICE:-relink-coach}"
WEB_SERVICE="${WEB_SERVICE:-relink-web}"
SECRET_NAME="${SECRET_NAME:-ollama-api-key}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Project: $PROJECT  Region: $REGION"
gcloud config set project "$PROJECT"

echo "==> Enable APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  --project="$PROJECT"

echo "==> Artifact Registry"
gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" 2>/dev/null \
  || gcloud artifacts repositories create "$AR_REPO" \
       --repository-format=docker --location="$REGION" --description="Relink images"

COACH_IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/coach:latest"
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/web:latest"

echo "==> Build & push coach"
gcloud builds submit "$ROOT/services/coach" --tag "$COACH_IMAGE" --project="$PROJECT"

echo "==> Ensure secret $SECRET_NAME exists"
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT" >/dev/null 2>&1; then
  echo "Create secret first:"
  echo "  echo -n 'YOUR_KEY' | gcloud secrets create $SECRET_NAME --data-file=- --project=$PROJECT"
  exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
# Cloud Run default compute SA
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT" >/dev/null || true

echo "==> Deploy coach"
gcloud run deploy "$COACH_SERVICE" \
  --image="$COACH_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=120 \
  --set-env-vars="RELINK_LLM_PROVIDER=ollama,RELINK_LLM_FALLBACK=vertex,RELINK_ALLOW_MOCK_FALLBACK=0,OLLAMA_API_BASE=https://ollama.com/v1,RELINK_MODEL_COACH=openai/glm-5.2,RELINK_MODEL_STRUCT=openai/kimi-k2.7-code,RELINK_GEMINI_MODEL=gemini-2.0-flash,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-secrets="OLLAMA_API_KEY=${SECRET_NAME}:latest" \
  --project="$PROJECT"

COACH_URL=$(gcloud run services describe "$COACH_SERVICE" --region="$REGION" --format='value(status.url)' --project="$PROJECT")
echo "Coach URL: $COACH_URL"

echo "==> Build & push web"
gcloud builds submit "$ROOT/apps/web" --tag "$WEB_IMAGE" --project="$PROJECT"

echo "==> Deploy web"
gcloud run deploy "$WEB_SERVICE" \
  --image="$WEB_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars="COACH_URL=${COACH_URL}" \
  --project="$PROJECT"

WEB_URL=$(gcloud run services describe "$WEB_SERVICE" --region="$REGION" --format='value(status.url)' --project="$PROJECT")
echo ""
echo "========================================"
echo "Relink deployed"
echo "  Web:   $WEB_URL"
echo "  Coach: $COACH_URL"
echo "  Health: $COACH_URL/health"
echo "========================================"
