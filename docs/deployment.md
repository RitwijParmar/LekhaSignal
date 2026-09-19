# Deployment guide

The public Cloud Run service is deliberately the deterministic training console only. It ships with no Snowflake credential, no source-system credential, and no write-capable agent tool.

## Cloud Run demo

Authenticate to the intended Google Cloud project, then run:

```bash
PROJECT_ID=your-project-id ./tools/deploy_cloudrun.sh
```

The service scales to zero and is limited to two instances to keep a portfolio demo inexpensive. Validate `/health`, `/api/overview`, and one `POST /api/investigate` request after deploy.

## Production hardening path

1. Store Snowflake key-pair material in Secret Manager; never in the image, Terraform state, or repository.
2. Assign a dedicated runtime service account with only the evidence-reader role path required by the API.
3. Keep agent access to the named query catalog in `snowflake_adapter.py`; do not expose arbitrary SQL execution.
4. Use a private ingress or identity-aware access for operational consoles containing real financial data.
5. Run the Snowflake DDL through reviewed change control, then attach the real stage, pipe, and dbt profile.
