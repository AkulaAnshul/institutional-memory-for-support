"""Application service: wires memory + agent + dataset into one object."""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import Any

from . import config as cfg
from .agent import SupportAgent
from .fake_memory import FakeMemory
from .memory import HindsightMemory
from .models import Customer, DraftResult, KnownIssue, Ticket
from .repository import load_customers, load_demo_stream, load_history_tickets, load_kb_articles
from .tools import SupportTools

log = logging.getLogger(__name__)


def build_memory():
    """Return a Hindsight-backed memory, or an offline fake for local dev/tests."""
    if os.getenv("USE_FAKE_MEMORY") == "1":
        log.warning("USE_FAKE_MEMORY=1 -> using the offline fake memory (not Hindsight).")
        return FakeMemory()
    try:
        memory = HindsightMemory()
        memory.health()
        log.info("connected to Hindsight at %s", memory.base_url)
        return memory
    except Exception as exc:
        if os.getenv("ALLOW_FAKE_FALLBACK", "1") == "0":
            raise
        log.warning(
            "Could not reach Hindsight (%s). Falling back to the offline fake memory. "
            "Set a valid HINDSIGHT_BASE_URL/API key, or USE_FAKE_MEMORY=1 to silence this.",
            exc,
        )
        return FakeMemory()


class SupportService:
    def __init__(self, memory=None, agent: SupportAgent | None = None) -> None:
        self.memory = memory or build_memory()
        self._agent = agent
        self.customers = load_customers()
        self.history = load_history_tickets()
        self.demo = load_demo_stream()
        self.tickets: dict[str, Ticket] = {t.id: t for t in [*self.history, *self.demo]}
        self.seeded = False
        self._lock = threading.Lock()

    @property
    def agent(self):
        if self._agent is None:
            from .agent import SupportAgent
            from .offline_agent import OfflineAgent

            force_offline = os.getenv("USE_FAKE_AGENT") == "1"
            force_real = os.getenv("USE_FAKE_AGENT") == "0"
            if not force_offline and (force_real or cfg.GROQ_API_KEY):
                self._agent = SupportAgent()
            else:
                log.warning(
                    "Using the deterministic OfflineAgent. Set GROQ_API_KEY for the real "
                    "LLM-backed agent."
                )
                self._agent = OfflineAgent()
        return self._agent

    # ------------------------------------------------------------------
    def seed_history(self) -> dict[str, Any]:
        """Ingest the historical tickets, then wait for memory to settle."""
        tickets = self.history
        self.memory.ensure_org_bank()
        for customer in self.customers.values():
            self.memory.ensure_customer_bank(customer)

        for ticket in tickets:
            self.memory.retain_org_ticket(ticket)
            self.memory.retain_customer_ticket(ticket)

        # Knowledge-base articles become shared world facts.
        for article in load_kb_articles():
            self.memory.retain_org_ticket(
                Ticket(
                    id=article["id"],
                    customer_id="kb",
                    created_at=datetime(2026, 1, 1),
                    product=article.get("product", cfg.DEFAULT_PRODUCT),
                    version="all",
                    module=article["module"],
                    issue_type="how_to",
                    subject=article["title"],
                    body=article["body"],
                    status="resolved",
                    resolution=article["body"],
                )
            )

        # Retain extraction is asynchronous; wait for consolidation, then build
        # the standing reports and wait for those to finish too.
        self.memory.settle(5.0)
        op_id = self.memory.trigger_consolidation()
        if op_id:
            self.memory.wait_for_operation(op_id, timeout=300.0)
        else:
            self.memory.settle(5.0)

        ops = self.memory.ensure_mental_models()
        for op in ops:
            self.memory.wait_for_operation(op, timeout=300.0)
        self.memory.settle(2.0)
        self.seeded = True
        return {"seeded_tickets": len(tickets), "customers": len(self.customers)}

    # ------------------------------------------------------------------
    def process(self, ticket: Ticket, mode: str = "memory") -> DraftResult:
        customer = self.customers[ticket.customer_id]
        tools = SupportTools(self.memory, customer, ticket) if mode == "memory" else None
        try:
            result = self.agent.draft(customer, ticket, tools)
        except Exception as exc:  # e.g. missing GROQ_API_KEY -> return a usable error
            log.exception("could not draft for ticket %s", ticket.id)
            return DraftResult(ticket_id=ticket.id, mode=mode, draft="", error=str(exc))

        # Memory is written at the end of the turn, never before recall.
        if mode == "memory":
            self.memory.retain_customer_ticket(ticket)
            self.memory.retain_org_ticket(ticket)
            self.memory.trigger_consolidation()
        return result

    # ------------------------------------------------------------------
    def emerging_issues(self) -> KnownIssue | None:
        from .memory import MM_EMERGING_ISSUES

        return self.memory.read_mental_model(MM_EMERGING_ISSUES)

    def known_issues(self) -> KnownIssue | None:
        from .memory import MM_KNOWN_ISSUES

        return self.memory.read_mental_model(MM_KNOWN_ISSUES)

    def detect_regressions(self) -> list[dict]:
        return self.memory.detect_regressions()

    def demo_stream(self) -> list[Ticket]:
        return self.demo

    def ticket(self, ticket_id: str) -> Ticket | None:
        return self.tickets.get(ticket_id)

    def customer_for(self, customer_id: str) -> Customer:
        return self.customers[customer_id]
