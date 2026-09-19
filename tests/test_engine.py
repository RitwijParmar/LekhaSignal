from lekh_signal.engine import investigate, platform_metrics


def test_natural_language_investigation_is_bounded() -> None:
    result = investigate("Why did cash reporting double count payments this morning?")
    assert result.incident.kind == "duplicate_payments"
    assert result.steps[-1].status == "approval_required"
    assert result.incident.requires_approval is True


def test_platform_has_explicit_slos() -> None:
    metrics = platform_metrics()
    assert len(metrics) == 4
    assert all(metric.target for metric in metrics)
