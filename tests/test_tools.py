"""Tool output must stay small so the free Groq token budget survives."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from app.models import Citation, KnownIssue, Ticket
from app.tools import MAX_MEMORIES, SupportTools


class VerboseMemory:
    def recall_customer_setup(self, customer_id):
        return [Citation(kind="customer_history", text="x" * 900) for _ in range(10)]

    def recall_known_issues(self, query, **kwargs):
        return [Citation(kind="known_issue", text="y" * 900, source_fact_ids=["a", "b"]) for _ in range(10)]

    def read_mental_model(self, model_id):
        return KnownIssue(id=model_id, name=model_id, content="z" * 5000)

    def reflect_customer(self, customer_id, query, context=None):
        return "w" * 5000


@pytest.fixture
def tools(customer):
    ticket = Ticket(
        id="T1", customer_id="c01", created_at=datetime(2026, 4, 1), product="Acme Cloud",
        version="v2.4", module="Data Export", issue_type="regression",
        subject="504", body="export fails",
    )
    return SupportTools(VerboseMemory(), customer, ticket)


def test_history_tool_caps_count_and_length(tools):
    payload = json.loads(tools.dispatch("recall_customer_history", {}))
    assert len(payload["memories"]) <= MAX_MEMORIES
    assert all(len(m) <= 340 for m in payload["memories"])


def test_known_issues_tool_caps_count(tools):
    payload = json.loads(tools.dispatch("find_known_issues", {"query": "export"}))
    assert len(payload["issues"]) <= MAX_MEMORIES


def test_emerging_report_is_truncated(tools):
    payload = json.loads(tools.dispatch("get_emerging_issues", {}))
    assert len(payload["report"]) <= 900
