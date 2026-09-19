import pytest

from lekh_signal.snowflake_adapter import get_evidence_query


def test_only_named_read_only_evidence_queries_are_exposed() -> None:
    assert get_evidence_query("task_health").sql.startswith("SELECT")
    with pytest.raises(ValueError):
        get_evidence_query("DROP DATABASE LEKHASIGNAL")
