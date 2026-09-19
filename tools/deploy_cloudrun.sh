#!/usr/bin/env bash
set -euo pipefail

# Public, low-cost demonstration deployment. This runtime has no Snowflake secrets
# and cannot mutate an external Snowflake account.
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project ID}"
REGION="${REGION:-us-east4}"
SERVICE="${SERVICE:-lekhasignal}"

gcloud run deploy "$SERVICE" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars LEKHASIGNAL_MODE=deterministic-demo
