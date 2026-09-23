# LekhaSignal — Snowflake Revenue Reliability Control Plane

LekhaSignal is a portfolio-grade data-engineering platform for a common business problem: a finance team needs to know whether daily revenue, invoices, and cash data are accurate enough to use.

It combines CDC and batch ingestion, Snowflake-native processing, dbt marts, orchestration, data contracts, reconciliation controls, cost attribution, and a conversational incident desk. The agent layer is intentionally bounded: it investigates with read-only MCP tools and requires human approval for any recovery action.

> All source events and incidents are simulated. The public operator console is a deterministic operator-training surface and deliberately has no Snowflake credential. The Snowflake-native pipeline is separately reproducible and has been executed against an authorized trial account; see [the execution record](docs/snowflake_execution.md).

**Operator console:** run the deterministic training surface locally with the
quickstart below. The repository separately records the verified Snowflake
execution in [docs/snowflake_execution.md](docs/snowflake_execution.md).

## Demo experience

Ask the operator console naturally:

- “Why did cash reporting double-count payments today?”
- “Did an ERP source contract change?”
- “Why is revenue close stale?”
- “Why did warehouse cost spike?”

The result is a structured evidence packet: business impact, affected governed assets, data-quality evidence, agent handoffs, a safe recovery recommendation, and the approval boundary.

## Stack and design rationale

| Capability | Implementation |
|---|---|
| Warehouse and governance | Snowflake RBAC, masking policy, resource monitor, query tagging |
| Batch ingestion | GCS external stage + Snowpipe blueprint |
| CDC | PostgreSQL/Debezium/Kafka-compatible event flow + Snowflake Streams/triggered Task |
| Transformation | dbt incremental marts plus Dynamic Tables for freshness-driven read models |
| Orchestration | Airflow revenue-close DAG |
| Reliability | contracts, dbt tests, Snowflake DMFs, reconciliation controls, incident timeline |
| AI operations | restricted MCP evidence tools, deterministic specialist handoffs, human approval gate |
| Delivery | Docker, Terraform blueprint, GitHub Actions, Cloud Run-ready FastAPI demo |

Dynamic Tables are deliberately used for pure declarative marts; Streams and Tasks are used for audited, stateful CDC merge logic. See [Snowflake design guidance](https://docs.snowflake.com/en/user-guide/dynamic-tables/migrate-streams-tasks).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn lekh_signal.api:app --reload --port 8080
```

Open `http://localhost:8080`.

## Snowflake deployment assets

1. Apply `snowflake/sql/00_platform.sql` with a controlled platform-admin role. It uses an X-Small transformation warehouse, 60-second auto-suspend, and a 20-credit monthly monitor.
2. Apply `snowflake/sql/10_revenue_pipeline.sql`.
3. For an end-to-end non-production demonstration, run `snowflake/sql/20_demo_seed.sql`; it only creates synthetic finance events and a reconciliation view.
4. Configure a least-privilege GCS storage integration and replace the commented stage/pipe blueprint before connecting a real source.
5. Configure the dbt profile, then run `dbt build` inside `snowflake/dbt/`.
6. Deploy Airflow and Terraform only with real, non-committed credentials.

The demo delivery and production-hardening boundaries are documented in [docs/deployment.md](docs/deployment.md).

## MCP evidence server

```bash
pip install -e '.[mcp]'
python -m lekh_signal.mcp_server
```

The MCP surface is deliberately narrow: platform SLOs, governed asset lineage, and a non-executable recovery runbook. The Snowflake adapter enforces named read-only evidence queries; it does not accept arbitrary SQL from an agent.

## Failure lab

The incident catalog covers duplicate payments, late invoices, schema drift, out-of-order CDC, offset gaps, dbt-test failure, stale Dynamic Tables, and warehouse-cost spikes. Each scenario must demonstrate detect → assess downstream exposure → propose recovery → human approve → replay → reconcile.

## What makes it interview-ready

- A real finance domain, rather than word count or generic retail tables.
- Clear boundaries between Snowflake-native processing, dbt modeling, and Airflow orchestration.
- Evidence-backed incident response and explicit no-autonomous-write policy.
- Production assets: Terraform, CI, Docker, data contracts, and a runnable demo.
