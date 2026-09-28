"""Tests for the offline fake memory's isolation and recall behaviour."""
from __future__ import annotations

from datetime import datetime

from app.models import Ticket


def make_ticket(tid: str, cid: str, module: str, body: str) -> Ticket:
    return Ticket(
        id=tid, customer_id=cid, created_at=datetime(2026, 2, 1), product="Acme Cloud",
        version="v2.2", module=module, issue_type="performance",
        subject="Large CSV export times out", body=body, status="resolved",
        resolution="Use a scheduled export.",
    )


def test_customer_recall_is_isolated(memory):
    memory.retain_customer_ticket(make_ticket("T1", "c01", "Data Export", "export hangs"))
    memory.retain_customer_ticket(make_ticket("T2", "c02", "Billing", "invoice wrong"))

    c01 = memory.recall_customer_setup("c01")
    assert c01 and all("invoice wrong" not in c.text for c in c01)

    c02 = memory.recall_customer_setup("c02")
    assert c02 and all("export hangs" not in c.text for c in c02)


def test_recall_known_issues_clusters_by_module(memory):
    for i in range(3):
        memory.retain_org_ticket(make_ticket(f"E{i}", "c01", "Data Export", "export timeout above 50k rows"))
    memory.retain_org_ticket(make_ticket("B1", "c02", "Billing", "duplicate seat invoice"))

    hits = memory.recall_known_issues("export timeout large rows", product="Acme Cloud")
    assert hits
    assert any("Data Export" in h.text for h in hits)


def test_detect_regressions_flags_fixed_issue_that_returned(memory):
    fixed = make_ticket("H1", "c01", "Data Export", "large export times out")
    fixed.resolution = "Workaround noted; believed fixed in v2.3."
    memory.retain_org_ticket(fixed)

    regressed = make_ticket("R1", "c02", "Data Export", "export now fails with 504")
    regressed.issue_type = "regression"
    memory.retain_org_ticket(regressed)

    regressions = memory.detect_regressions()
    assert regressions
    assert "Data Export" in regressions[0]["issue"]
