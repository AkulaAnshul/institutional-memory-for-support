"""The dataset must contain the storyline the demo depends on."""
from __future__ import annotations

from app.repository import load_customers, load_demo_stream, load_history_tickets


def test_customer_count():
    assert len(load_customers()) == 15


def test_history_contains_export_timeout_and_fix_claim():
    history = load_history_tickets()
    subjects = " ".join(t.subject for t in history).lower()
    assert "export" in subjects
    resolutions = " ".join((t.resolution or "") for t in history)
    assert "believed fixed in v2.3" in resolutions


def test_demo_stream_contains_regression():
    stream = load_demo_stream()
    regressions = [t for t in stream if t.issue_type == "regression"]
    assert regressions, "the demo stream must include the v2.4 export regression"


def test_all_tickets_reference_known_customers():
    ids = set(load_customers())
    for ticket in [*load_history_tickets(), *load_demo_stream()]:
        assert ticket.customer_id in ids
