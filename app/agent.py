"""The support agent: a Groq tool-calling loop with an optional memory layer.

Two modes make the value of memory obvious in the demo:
  * "memory"  -> the agent can call Hindsight tools and cite what it recalls
  * "amnesia" -> the agent sees only the current ticket, like a stateless bot
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from groq import Groq

from . import config as cfg
from .models import Customer, DraftResult, Ticket
from .tools import SupportTools

log = logging.getLogger(__name__)

MAX_ITERATIONS = 5
BASE_TEMPERATURE = 0.3


class RateLimitExceeded(RuntimeError):
    """Raised when Groq rate limits us, especially the daily token budget."""


_RETRY_AFTER_RE = re.compile(r"try again in ([0-9.]+)s", re.IGNORECASE)
_DAILY_HINTS = ("per day", "tokens per day", "tpd")


SYSTEM_COMMON = (
    "You are a senior customer support agent for a B2B SaaS product. "
    "Write a concise, kind, ready-to-send reply to the customer's ticket. "
    "Never promise refunds, credits, SLA waivers or delivery dates — escalate those. "
    "Do not invent workarounds."
)

SYSTEM_MEMORY = (
    SYSTEM_COMMON
    + " You have long-term memory tools. Call each tool AT MOST ONCE, then write the "
    "reply — do not repeat tool calls. Check the customer's history and search for known "
    "issues, then answer. Ground concrete claims in what you recall and reference prior "
    "interactions when relevant (e.g. 'the same timeout you hit in March'). If the ticket "
    "matches a known issue, say so and give the recorded workaround. Keep the reply under "
    "180 words."
)

SYSTEM_AMNESIA = (
    SYSTEM_COMMON
    + " You have no memory of this customer. Answer only from the ticket text you are given."
)


def build_user_prompt(customer: Customer, ticket: Ticket) -> str:
    status = "resolved" if ticket.status == "resolved" else "open"
    return (
        f"Customer: {customer.name} at {customer.company} ({customer.plan} plan, {customer.region})\n"
        f"Ticket {ticket.id} — {ticket.subject}\n"
        f"Product: {ticket.product} {ticket.version} | Module: {ticket.module} | "
        f"Type: {ticket.issue_type} | Status: {status}\n\n"
        f"Customer message:\n{ticket.body}\n\n"
        "Write the reply email."
    )


class SupportAgent:
    def __init__(
        self,
        *,
        client: Groq | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or cfg.GROQ_MODEL
        if client is not None:
            self.client = client
        else:
            self.client = Groq(api_key=cfg.GROQ_API_KEY, max_retries=0)

    # ------------------------------------------------------------------
    def draft(self, customer: Customer, ticket: Ticket, tools: SupportTools | None) -> DraftResult:
        started = time.perf_counter()
        mode = "memory" if tools is not None else "amnesia"
        system = SYSTEM_MEMORY if tools is not None else SYSTEM_AMNESIA
        messages: list[Any] = [
            {"role": "system", "content": system},
            {"role": "user", "content": build_user_prompt(customer, ticket)},
        ]

        try:
            draft = self._run_loop(messages, tools)
            error = None
        except Exception as exc:  # surface a usable message to the UI
            log.exception("agent failed for ticket %s", ticket.id)
            draft = ""
            error = str(exc)

        elapsed = int((time.perf_counter() - started) * 1000)
        return DraftResult(
            ticket_id=ticket.id,
            mode=mode,
            draft=draft,
            citations=tools.citations if tools else [],
            tool_calls=tools.traces if tools else [],
            used_memory=bool(tools and tools.citations),
            elapsed_ms=elapsed,
            error=error,
        )

    # ------------------------------------------------------------------
    def _run_loop(self, messages: list[Any], tools: SupportTools | None) -> str:
        specs = tools.specs() if tools else None
        for _ in range(MAX_ITERATIONS):
            response = self._chat(messages, specs)
            message = response.choices[0].message

            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls or tools is None:
                return (message.content or "").strip()

            messages.append(message)
            for call in tool_calls:
                name = call.function.name
                arguments = _safe_json(call.function.arguments)
                result = tools.dispatch(name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": name,
                        "content": result,
                    }
                )
        return "I was unable to finalise a reply automatically; escalating to a human."

    # ------------------------------------------------------------------
    def _chat(self, messages: list[Any], specs: list[dict] | None):
        temperature = BASE_TEMPERATURE
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_completion_tokens": 700,
                }
                if specs:
                    kwargs["tools"] = specs
                    kwargs["tool_choice"] = "auto"
                return self.client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - we inspect the status code
                last_exc = exc
                status = _status_code(exc)
                if status == 400 and attempt < 2:
                    # Groq rejects malformed tool calls with a 400; lower the
                    # temperature and retry rather than crashing.
                    temperature = max(0.1, temperature - 0.1)
                    continue
                if status == 429:
                    message = str(exc)
                    if any(hint in message.lower() for hint in _DAILY_HINTS):
                        # Daily budget is gone; retrying/sleeping for minutes is
                        # pointless and makes the whole run hang.
                        raise RateLimitExceeded("Groq daily token limit reached. " + _short(message)) from exc
                    if attempt < 2:
                        # Per-minute limit: back off briefly and retry.
                        time.sleep(min(_retry_after(exc, attempt), 20.0))
                        continue
                    raise RateLimitExceeded("Groq daily token limit reached. " + _short(message)) from exc
                if status and status >= 500 and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
        assert last_exc is not None
        raise last_exc


def _safe_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {}


def _status_code(exc: Exception) -> int | None:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return code
    return None


def _retry_after(exc: Exception, attempt: int) -> float:
    response = getattr(exc, "response", None)
    if response is not None:
        headers = getattr(response, "headers", {}) or {}
        raw = headers.get("retry-after") or headers.get("x-ratelimit-reset-tokens")
        if raw:
            try:
                return min(float(str(raw).rstrip("s")), 20.0)
            except ValueError:
                pass
    # Groq sometimes only states the wait in the message ("try again in 4m14.4s").
    match = _RETRY_AFTER_RE.search(str(exc))
    if match:
        return min(float(match.group(1)), 20.0)
    return 2.0 * (attempt + 1)


def _short(message: str, limit: int = 200) -> str:
    return " ".join(message.split())[:limit]

