# Bounded agent and MCP controls

LekhaSignal uses a four-step investigation path: Signal Detector, Lineage Investigator, Impact Analyst, and Recovery Planner. The first three use read-only metadata and control results. The Recovery Planner may only produce a plan.

The MCP server must expose narrow tools such as `get_asset_lineage`, `get_dmf_results`, `get_task_history`, `get_reconciliation_controls`, and `get_runbook`. It must not expose unrestricted SQL, `ALTER`, `COPY`, `MERGE`, warehouse-resize, or publish operations.

Human approval is mandatory before a replay, quarantine, schema promotion, warehouse change, or mart publication. The UI makes this boundary visible in every investigation.
