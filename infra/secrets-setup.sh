#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"

echo "Creating GCP secrets..."

# Create secrets (prompts for values)
for SECRET in neo4j-password pg-password anthropic-key opensanctions-key freight-key news-api-key; do
  echo "Enter value for $SECRET:"
  read -s VALUE
  echo -n "$VALUE" | gcloud secrets create "$SECRET" \
    --data-file=- \
    --project="$PROJECT_ID" 2>/dev/null || \
  echo -n "$VALUE" | gcloud secrets versions add "$SECRET" \
    --data-file=- \
    --project="$PROJECT_ID"
  echo "  -> $SECRET stored"
done

echo "Done. Grant Cloud Run service account access with:"
echo "  gcloud secrets add-iam-policy-binding SECRET --member=serviceAccount:SA --role=roles/secretmanager.secretAccessor"
