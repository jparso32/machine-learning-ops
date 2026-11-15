#!/usr/bin/env bash
# Run from the repository root in Cloud Shell after reviewing the settings below.
# The three verified model bundle files must already be present in models/.
set -euo pipefail

PROJECT_ID=credit-risk-team2
REGION=us-central1
BUCKET_NAME=credit-risk-models-team2
REPOSITORY=credit-risk
SERVICE_NAME=credit-risk-api
SERVICE_ACCOUNT="credit-risk-api@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/api:week5"

for filename in model.joblib model_info.json feature_store.parquet; do
  test -s "models/${filename}" || { echo "Missing models/${filename}" >&2; exit 1; }
done
test -s requirements-api.txt
test -s Dockerfile

gcloud config set project "${PROJECT_ID}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com

if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" --location="${REGION}" \
    --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage buckets update "gs://${BUCKET_NAME}" --public-access-prevention

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create credit-risk-api --display-name='Credit-risk API'
fi
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" --role=roles/storage.objectViewer
gcloud storage cp models/model.joblib models/model_info.json models/feature_store.parquet \
  "gs://${BUCKET_NAME}/"

if ! gcloud artifacts repositories describe "${REPOSITORY}" --location="${REGION}" \
  >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPOSITORY}" --repository-format=docker \
    --location="${REGION}" --description='Credit-risk course API images'
fi
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker build --platform=linux/amd64 -t "${IMAGE}" .
docker push "${IMAGE}"

gcloud run deploy "${SERVICE_NAME}" --image="${IMAGE}" --region="${REGION}" \
  --service-account="${SERVICE_ACCOUNT}" --set-env-vars="MODEL_BUCKET=gs://${BUCKET_NAME}" \
  --allow-unauthenticated --min-instances=0 --max-instances=2 \
  --memory=1Gi --cpu=1 --concurrency=10 --port=8080

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" \
  --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"
curl --fail-with-body --silent --show-error "${SERVICE_URL}/health"
echo
curl --fail-with-body --silent --show-error "${SERVICE_URL}/model-info"
echo
echo 'Record the verified URL and cloud settings in docs/deployment.md.'
echo 'Then measure the LIVE URL with python run.py latency --url <verified URL>.'
echo 'Run python run.py check --stage wed and python run.py check after recording results.'
