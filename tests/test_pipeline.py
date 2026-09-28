"""End-to-end pipeline test: draft, then write to memory (never the same turn)."""
from __future__ import annotations

from datetime import datetime

from app.agent import SupportAgent
from app.models import Ticket
from app.service import SupportService

from .conftest import FakeGroq, text_message, tool_call_message


def make_ticket() -> Ticket:
    return Ticket(
        id="T200", customer_id="c02", created_at=datetime(2026, 4, 9), product="Acme Cloud",
        version="v2.4", module="Authentication", issue_type="bug",
        subject="SSO redirect loop after password reset", body="Users loop on login.",
    )


def build_service(script) -> SupportService:
    agent = SupportAgent(client=FakeGroq(script))
    # memory omitted -> service builds one; force the fake explicitly instead
    from app.fake_memory import FakeMemory

    return SupportService(memory=FakeMemory(), agent=agent)


def test_process_writes_memory_after_drafting():
    script = [
        tool_call_message(("recall_customer_history", {})),
        tool_call_message(("find_known_issues", {"query": "SSO redirect loop"})),
        text_message("Hi Marcus, this is a known SSO issue; here is the workaround."),
    ]
    service = build_service(script)
    ticket = make_ticket()

    result = service.process(ticket, mode="memory")

    assert result.mode == "memory"
    assert "known SSO issue" in result.draft
    assert len(result.tool_calls) == 2
    # The ticket was retained into both the customer bank and the org brain.
    assert any(row["module"] == "Authentication" for row in service.memory.customer_events["c02"])
    assert any(row["module"] == "Authentication" for row in service.memory.org_events)


def test_amnesia_mode_does_not_write_memory():
    service = build_service([text_message("Generic reply.")])
    service.process(make_ticket(), mode="amnesia")
    assert service.memory.org_events == []
