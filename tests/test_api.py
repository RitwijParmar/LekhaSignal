from fastapi.testclient import TestClient

from lekh_signal.api import app


client = TestClient(app)


def test_operator_console_returns_an_approval_gated_investigation() -> None:
    response = client.post("/api/investigate", json={"message": "Why did cash reporting double-count payments today?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["incident"]["kind"] == "duplicate_payments"
    assert payload["steps"][-1]["status"] == "approval_required"


def test_overview_exposes_reliability_metrics() -> None:
    response = client.get("/api/overview")

    assert response.status_code == 200
    assert len(response.json()["metrics"]) == 4
