"""A publication gate that refuses an unsafe revenue-close release."""
from __future__ import annotations

import argparse
import json

from .reconcile import run as reconcile


def run(requires_control_pass: bool) -> dict[str, object]:
    control = reconcile()
    allowed = not requires_control_pass or control["status"] == "passed"
    return {
        "publication": "revenue_close",
        "status": "published" if allowed else "blocked",
        "approval_boundary": "Only a passing reconciliation control permits publication.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requires-control-pass", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.requires_control_pass), indent=2))
