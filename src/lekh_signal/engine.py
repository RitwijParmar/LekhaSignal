from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from .contracts import AgentStep, Incident, Investigation, Metric


INCIDENTS: dict[str, dict] = {
    "duplicate_payments": {
        "title": "Duplicate payment event burst in settlement feed",
        "severity": "critical",
        "impact": "$184,230 of cash receipts could be double-counted in the reconciliation mart.",
        "assets": ["RAW.PAYMENT_EVENTS", "CORE.PAYMENT_LEDGER", "MART.DAILY_CASH_POSITION"],
        "evidence": ["DMF duplicate_event_id rate: 2.8% (SLO < 0.1%)", "Kafka partition 4 replayed offsets 851220–851372", "dbt test unique_payment_event_id failed"],
        "action": "Quarantine the replayed event range, rebuild the affected incremental partition, then reconcile against settlement control totals.",
    },
    "late_invoices": {
        "title": "Invoice feed is late beyond finance freshness SLO",
        "severity": "warning",
        "impact": "$2.1M of invoices are absent from the 08:00 revenue-close dataset.",
        "assets": ["RAW.ERP_INVOICES", "DT.FCT_REVENUE_RECOGNITION", "MART.REVENUE_CLOSE"],
        "evidence": ["Freshness: 94 minutes (SLO < 30 minutes)", "Snowpipe load history shows no files since 06:26 UTC", "Upstream ERP extract completed late"],
        "action": "Hold the revenue-close exposure, load the delayed immutable batch, and refresh downstream dynamic tables.",
    },
    "schema_drift": {
        "title": "ERP source contract changed without approval",
        "severity": "critical",
        "impact": "Payment-matching transformation rejects new remittance records; downstream cash reporting is incomplete.",
        "assets": ["RAW.REMITTANCE_EVENTS", "DBT.STG_REMITTANCES", "MART.CASH_APPLICATION"],
        "evidence": ["Contract: expected remittance_reference STRING, received remittanceReferences ARRAY", "Schema registry version 18 was not approved", "Rejected-record rate: 17.4%"],
        "action": "Keep the raw payload immutable, add a backward-compatible normalization rule, and require owner approval before promotion.",
    },
    "out_of_order_cdc": {
        "title": "Out-of-order CDC updates threaten invoice state",
        "severity": "warning",
        "impact": "38 invoices may show an older balance after a late status update.",
        "assets": ["RAW.CDC_INVOICE", "CORE.INVOICE_SCD", "MART.AR_AGING"],
        "evidence": ["38 source_lsn values arrived behind the current watermark", "SCD merge selected event_ts before source_lsn", "Late-event window exceeded 15 minutes"],
        "action": "Replay the affected keys using source_lsn ordering and validate the AR-aging control total.",
    },
    "offset_gap": {
        "title": "CDC offset gap detected before warehouse load",
        "severity": "critical",
        "impact": "The pipeline cannot prove completeness for the payment ledger after offset 851219.",
        "assets": ["KAFKA.PAYMENT_CDC", "RAW.PAYMENT_EVENTS", "CONTROL.INGEST_WATERMARKS"],
        "evidence": ["Expected offset 851220; next committed offset 851374", "No matching dead-letter batch", "Completeness control is blocked"],
        "action": "Stop the consumer checkpoint, recover the missing offset range from the source log, then resume from an audited watermark.",
    },
    "dbt_test_failure": {
        "title": "dbt revenue reconciliation test failed",
        "severity": "warning",
        "impact": "Recognized revenue differs from the invoice control total by $23,410.",
        "assets": ["DBT.FCT_REVENUE", "MART.REVENUE_CLOSE", "BI.REVENUE_DASHBOARD"],
        "evidence": ["accepted_values invoice_status test passed", "revenue_to_invoice_control failed", "A refund adjustment was omitted from one incremental partition"],
        "action": "Block publication of the exposure, rerun the affected partition, and require a reconciliation pass before release.",
    },
    "stale_dynamic_table": {
        "title": "Revenue dynamic table missed freshness target",
        "severity": "warning",
        "impact": "Executive revenue dashboard is 46 minutes stale.",
        "assets": ["DT.FCT_REVENUE_RECOGNITION", "MART.REVENUE_CLOSE", "BI.EXECUTIVE_REVENUE"],
        "evidence": ["TARGET_LAG: 15 minutes; actual lag: 46 minutes", "Refresh history: warehouse queue wait", "No raw-data contract breach found"],
        "action": "Scale the transform warehouse within its budget policy, refresh the dynamic table, and review the queued workload.",
    },
    "warehouse_cost_spike": {
        "title": "Transform warehouse cost anomaly",
        "severity": "warning",
        "impact": "Projected daily transformation spend is 2.4× the approved budget.",
        "assets": ["WAREHOUSE.TRANSFORM_WH", "QUERY_HISTORY", "DT.FCT_REVENUE_RECOGNITION"],
        "evidence": ["Query tag lekhasignal:backfill consumed 38.2 credits", "Partition predicate was missing in a dbt incremental run", "Resource monitor is at 78%"],
        "action": "Cancel only the tagged non-production backfill, repair the partition predicate, and resume under the resource monitor cap.",
    },
}


def platform_metrics() -> list[Metric]:
    return [
        Metric(name="Revenue-close freshness", value="12 min", target="< 30 min", severity="healthy", evidence="Dynamic Table target lag: 15 min"),
        Metric(name="Reconciliation delta", value="$0", target="$0", severity="healthy", evidence="Invoice, payment, and revenue control totals agree"),
        Metric(name="Data-contract pass rate", value="99.98%", target="> 99.9%", severity="healthy", evidence="43 checks across 8 critical datasets"),
        Metric(name="Warehouse budget", value="62%", target="< 80%", severity="healthy", evidence="Query-tagged daily credit attribution"),
    ]


def _select_incident(message: str) -> str:
    text = message.lower()
    keywords = {
        "duplicate_payments": ["duplicate", "double", "payment", "cash"],
        "late_invoices": ["late", "invoice", "revenue close", "fresh"],
        "schema_drift": ["schema", "column", "contract", "remittance"],
        "out_of_order_cdc": ["order", "late event", "cdc", "invoice state"],
        "offset_gap": ["offset", "missing", "gap", "kafka"],
        "dbt_test_failure": ["dbt", "test", "reconcile", "reconciliation"],
        "stale_dynamic_table": ["stale", "dynamic", "dashboard", "lag"],
        "warehouse_cost_spike": ["cost", "credit", "warehouse", "budget"],
    }
    scores = Counter({key: sum(term in text for term in terms) for key, terms in keywords.items()})
    return scores.most_common(1)[0][0] if scores and scores.most_common(1)[0][1] else "duplicate_payments"


def investigate(message: str) -> Investigation:
    key = _select_incident(message)
    template = INCIDENTS[key]
    incident = Incident(
        incident_id=f"LS-{datetime.now(timezone.utc):%Y%m%d}-{key[:4].upper()}",
        kind=key, title=template["title"], severity=template["severity"],
        business_impact=template["impact"], affected_assets=template["assets"],
        evidence=template["evidence"], safe_action=template["action"],
    )
    steps = [
        AgentStep(agent="Signal Detector", status="completed", tool="snowflake_dmf_results", finding=f"Classified {incident.severity} reliability signal: {incident.title}."),
        AgentStep(agent="Lineage Investigator", status="completed", tool="mcp_get_asset_lineage", finding=f"Mapped {len(incident.affected_assets)} affected governed assets and their downstream exposure."),
        AgentStep(agent="Impact Analyst", status="completed", tool="mcp_reconciliation_controls", finding=incident.business_impact),
        AgentStep(agent="Recovery Planner", status="approval_required", tool="mcp_get_runbook", finding=incident.safe_action),
    ]
    return Investigation(
        question=message, intent=key.replace("_", " "), incident=incident, steps=steps,
        operator_summary=(f"I found a {incident.severity} data-reliability issue. {incident.business_impact} "
                          "I can explain the evidence and recovery path, but I will not mutate Snowflake data or resume a pipeline without an operator approval."),
        approval_boundary="Read-only investigation is automatic. Quarantine, replay, warehouse resize, and publication changes require human approval.",
    )


def sample_timeline() -> list[dict[str, str]]:
    now = datetime.now(timezone.utc)
    return [
        {"time": (now - timedelta(minutes=18)).strftime("%H:%M UTC"), "event": "Snowpipe loaded 18,442 billing records", "status": "healthy"},
        {"time": (now - timedelta(minutes=14)).strftime("%H:%M UTC"), "event": "Dynamic Table refreshed revenue mart", "status": "healthy"},
        {"time": (now - timedelta(minutes=6)).strftime("%H:%M UTC"), "event": "DMF reconciliation controls evaluated", "status": "healthy"},
        {"time": now.strftime("%H:%M UTC"), "event": "Operator console ready for an investigation", "status": "healthy"},
    ]
