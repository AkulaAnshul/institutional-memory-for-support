"""Tool definitions and dispatch for the support agent.

The tools are intentionally thin: each one is a focused question against
Hindsight. The agent decides which to call.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .memory import (
    MM_EMERGING_ISSUES,
    HindsightMemory,
    format_citations,
)
from .models import Citation, Customer, Ticket, ToolCallTrace

log = logging.getLogger(__name__)

# Keep tool output small: every character here costs prompt tokens and the free
# Groq tier has a tight daily budget. We cap count and length aggressively.
MAX_MEMORIES = 4
MAX_CHARS = 320
MAX_REPORT_CHARS = 900


def _clip(text: str, limit: int = MAX_CHARS) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


TOOL_SPECS = [
    _schema(
        "recall_customer_history",
        "Look up this customer's account details, environment, plan and their past "
        "support tickets. Use before answering anything that depends on who the customer is.",
        {},
    ),
    _schema(
        "find_known_issues",
        "Search the company-wide memory for known issues and workarounds matching a "
        "symptom. Returns observations consolidated across all customers.",
        {
            "query": {"type": "string", "description": "The symptom to search for."},
            "product": {"type": "string", "description": "Optional product name."},
        },
        ["query"],
    ),
    _schema(
        "get_emerging_issues",
        "Read the current 'Emerging Issues' report: recurring defects across customers, "
        "how many are affected, and whether the trend is rising. Cheap, no LLM call.",
        {},
    ),
    _schema(
        "reflect_on_customer",
        "Ask Hindsight to reason over everything known about this customer and propose "
        "the best next step. Use for a nuanced or relationship-sensitive reply.",
        {"question": {"type": "string"}},
        ["question"],
    ),
]


class SupportTools:
    """Executes tool calls and records the citations they produced."""

    def __init__(self, memory: HindsightMemory, customer: Customer, ticket: Ticket) -> None:
        self.memory = memory
        self.customer = customer
        self.ticket = ticket
        self.citations: list[Citation] = []
        self.traces: list[ToolCallTrace] = []

    # ------------------------------------------------------------------
    def specs(self) -> list[dict]:
        return TOOL_SPECS

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        trace = ToolCallTrace(name=name, arguments=arguments)
        try:
            result = self._run(name, arguments)
            trace.result_preview = result[:280]
            return result
        except Exception as exc:  # feed the failure back to the model
            log.warning("tool %s failed: %s", name, exc)
            trace.error = str(exc)
            return json.dumps({"error": str(exc), "is_error": True})
        finally:
            self.traces.append(trace)

    # ------------------------------------------------------------------
    def _run(self, name: str, args: dict[str, Any]) -> str:
        if name == "recall_customer_history":
            citations = self.memory.recall_customer_setup(self.customer.id)
            self.citations.extend(citations)
            if not citations:
                return json.dumps({"found": False, "note": "No prior history on record."})
            return json.dumps(
                {
                    "found": True,
                    "customer": self.customer.model_dump(),
                    "memories": [_clip(c.text) for c in citations[:MAX_MEMORIES]],
                }
            )

        if name == "find_known_issues":
            citations = self.memory.recall_known_issues(
                args["query"],
                product=args.get("product") or self.ticket.product,
            )
            self.citations.extend(citations)
            return json.dumps(
                {
                    "found": bool(citations),
                    "issues": [
                        {"text": _clip(c.text), "evidence": len(c.source_fact_ids)}
                        for c in citations[:MAX_MEMORIES]
                    ],
                }
            )

        if name == "get_emerging_issues":
            mm = self.memory.read_mental_model(MM_EMERGING_ISSUES)
            if not mm or not mm.content:
                return json.dumps({"found": False, "note": "No emerging-issue report yet."})
            self.citations.append(Citation(kind="emerging_issue", text=mm.content))
            return json.dumps({"found": True, "report": _clip(mm.content, MAX_REPORT_CHARS)})

        if name == "reflect_on_customer":
            answer = self.memory.reflect_customer(
                self.customer.id,
                args["question"],
                context=f"Replying to ticket {self.ticket.id}: {self.ticket.subject}",
            )
            self.citations.append(Citation(kind="customer_history", text=answer))
            return json.dumps({"answer": _clip(answer, 700)})

        return json.dumps({"error": f"unknown tool {name}", "is_error": True})

    # ------------------------------------------------------------------
    def citation_block(self) -> str:
        return format_citations(self.citations)
