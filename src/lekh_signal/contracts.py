from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["healthy", "warning", "critical"]
IncidentKind = Literal[
    "duplicate_payments",
    "late_invoices",
    "schema_drift",
    "out_of_order_cdc",
    "offset_gap",
    "dbt_test_failure",
    "stale_dynamic_table",
    "warehouse_cost_spike",
]


class Metric(BaseModel):
    name: str
    value: str
    target: str
    severity: Severity
    evidence: str


class Incident(BaseModel):
    incident_id: str
    kind: IncidentKind
    title: str
    severity: Severity
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    business_impact: str
    affected_assets: list[str]
    evidence: list[str]
    safe_action: str
    requires_approval: bool = True


class AgentStep(BaseModel):
    agent: str
    status: Literal["completed", "blocked", "approval_required"]
    finding: str
    tool: str


class Investigation(BaseModel):
    question: str
    intent: str
    incident: Incident
    steps: list[AgentStep]
    operator_summary: str
    approval_boundary: str


class OperatorRequest(BaseModel):
    message: str = Field(min_length=4, max_length=1200)
