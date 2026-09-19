"""Snowflake access boundary for a real deployment.

Only named evidence queries belong here. The conversational agent never receives a
connector, credentials, or a free-form SQL tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ALLOWED_EVIDENCE_QUERIES = {
    "dynamic_table_health": "SELECT name, target_lag, data_timestamp, scheduling_state FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())",
    "task_health": "SELECT name, state, query_start_time, error_message FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())",
    "query_cost": "SELECT query_tag, warehouse_name, credits_used_cloud_services FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY WHERE query_tag LIKE 'lekhasignal:%'",
}


@dataclass(frozen=True)
class EvidenceQuery:
    name: str
    sql: str


def get_evidence_query(name: str) -> EvidenceQuery:
    """Return an audited query from a fixed allowlist; reject arbitrary SQL."""
    if name not in ALLOWED_EVIDENCE_QUERIES:
        raise ValueError(f"Unsupported evidence query: {name}")
    return EvidenceQuery(name=name, sql=ALLOWED_EVIDENCE_QUERIES[name])


def execute_named_evidence_query(connection: Any, name: str) -> list[dict]:
    """Execute a parameterless, reviewed evidence query using a caller-owned connection."""
    query = get_evidence_query(name)
    cursor = connection.cursor()
    try:
        cursor.execute(query.sql)
        columns = [column[0].lower() for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        cursor.close()
