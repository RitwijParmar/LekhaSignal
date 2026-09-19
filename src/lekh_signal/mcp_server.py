"""Optional MCP evidence server.

Run with `pip install -e '.[mcp]'` then `python -m lekh_signal.mcp_server`.
The tools intentionally return only simulated/read-only operational evidence. A real
Snowflake adapter must preserve the same allowlist and never accept arbitrary SQL.
"""
from __future__ import annotations

from .engine import INCIDENTS, platform_metrics, sample_timeline


def _require_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ImportError as exc:  # pragma: no cover - optional integration
        raise RuntimeError("Install MCP support first: pip install -e '.[mcp]'") from exc


def build_server():
    mcp = _require_mcp()("LekhaSignal Evidence Server")

    @mcp.tool()
    def get_platform_slos() -> list[dict]:
        """Read current freshness, reconciliation, contract, and budget SLO evidence."""
        return [metric.model_dump() for metric in platform_metrics()]

    @mcp.tool()
    def get_asset_lineage(incident_kind: str) -> dict:
        """Read the governed assets affected by one supported incident kind."""
        item = INCIDENTS.get(incident_kind)
        if not item:
            return {"error": "Unknown incident kind", "allowed": sorted(INCIDENTS)}
        return {"incident_kind": incident_kind, "assets": item["assets"], "evidence": item["evidence"]}

    @mcp.tool()
    def get_recovery_runbook(incident_kind: str) -> dict:
        """Read a proposed recovery runbook. This tool cannot execute it."""
        item = INCIDENTS.get(incident_kind)
        if not item:
            return {"error": "Unknown incident kind", "allowed": sorted(INCIDENTS)}
        return {"proposed_action": item["action"], "approval_required": True, "execution": "blocked"}

    @mcp.resource("lekhasignal://control-timeline")
    def control_timeline() -> str:
        """Recent demo control-plane events."""
        return "\n".join(f"{row['time']} — {row['event']}" for row in sample_timeline())

    return mcp


if __name__ == "__main__":  # pragma: no cover - integration entrypoint
    build_server().run()
