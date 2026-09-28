"""Agent loop, mode separation and Groq error-handling tests."""
from __future__ import annotations

from datetime import datetime

from app.agent import SupportAgent
from app.models import Ticket
from app.tools import SupportTools

from .conftest import ApiError, FakeGroq, text_message, tool_call_message


def ticket() -> Ticket:
    return Ticket(
        id="T100", customer_id="c01", created_at=datetime(2026, 4, 2), product="Acme Cloud",
        version="v2.4", module="Data Export", issue_type="regression",
        subject="Exports now fail with 504 Gateway Timeout", body="Large exports die instantly.",
    )


def test_memory_mode_calls_tools_then_answers(customer, memory):
    script = [
        tool_call_message(("recall_customer_history", {})),
        text_message("Hi Priya, this matches a known export issue..."),
    ]
    agent = SupportAgent(client=FakeGroq(script))
    tools = SupportTools(memory, customer, ticket())

    memory.retain_customer_ticket(ticket())
    result = agent.draft(customer, ticket(), tools)

    assert result.mode == "memory"
    assert result.draft.startswith("Hi Priya")
    assert [t.name for t in result.tool_calls] == ["recall_customer_history"]
    # tools were offered on the first model call
    assert "tools" in agent.client.completions.calls[0]


def test_amnesia_mode_offers_no_tools(customer):
    agent = SupportAgent(client=FakeGroq([text_message("Please try again.")]))
    result = agent.draft(customer, ticket(), None)

    assert result.mode == "amnesia"
    assert result.draft == "Please try again."
    assert "tools" not in agent.client.completions.calls[0]
    assert not result.used_memory


def test_400_retries_at_lower_temperature(customer, memory):
    script = [ApiError(400), text_message("Recovered after retry")]
    agent = SupportAgent(client=FakeGroq(script))
    result = agent.draft(customer, ticket(), None)

    calls = agent.client.completions.calls
    assert result.draft == "Recovered after retry"
    assert len(calls) == 2
    assert calls[1]["temperature"] < calls[0]["temperature"]


def test_tool_errors_are_fed_back_not_fatal(customer, memory):
    script = [
        tool_call_message(("does_not_exist", {})),
        text_message("I could not find that, but here is what I know."),
    ]
    agent = SupportAgent(client=FakeGroq(script))
    tools = SupportTools(memory, customer, ticket())
    result = agent.draft(customer, ticket(), tools)

    assert result.error is None
    assert result.tool_calls and result.tool_calls[0].name == "does_not_exist"
    assert "could not find" in result.draft


def test_per_minute_429_retries_and_recovers(customer):
    script = [ApiError(429, headers={"retry-after": "0"}), text_message("Recovered")]
    agent = SupportAgent(client=FakeGroq(script))
    result = agent.draft(customer, ticket(), None)

    assert result.draft == "Recovered"
    assert len(agent.client.completions.calls) == 2


def test_daily_token_limit_fails_fast(customer):
    daily = (
        "Rate limit reached for model `openai/gpt-oss-120b` on tokens per day (TPD): "
        "Limit 200000, Used 199152. Please try again in 4m14s."
    )
    script = [ApiError(429, message=daily)] * 5
    agent = SupportAgent(client=FakeGroq(script))
    result = agent.draft(customer, ticket(), None)

    assert result.error and "daily token limit" in result.error.lower()
    # No retries: a daily limit must not be slept on.
    assert len(agent.client.completions.calls) == 1

