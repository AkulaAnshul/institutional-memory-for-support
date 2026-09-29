"""Thin, well-typed wrapper around the Hindsight memory system.

Everything the rest of the app needs from memory goes through this module, so
the agent never talks to Hindsight directly and the behaviour is easy to fake
in tests.
"""
from __future__ import annotations

import asyncio
import contextlib
import functools
import logging
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from hindsight_client import Hindsight

from . import config as cfg
from .models import Citation, Customer, KnownIssue, Ticket

log = logging.getLogger(__name__)

# Deterministic mental-model ids so the dashboard can read them by name.
MM_EMERGING_ISSUES = "emerging-issues"
MM_KNOWN_ISSUES = "known-issues"

# A memory is only useful once it has been extracted *and* consolidated, and
# Hindsight does both in the background. These are our polling bounds.
OPERATION_TIMEOUT_S = 180.0
OPERATION_POLL_S = 1.5

# Structured schema for the proactive regression audit. Hindsight's reflect
# target language fills this in from the bank's observations and facts.
REGRESSION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "regressions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"},
                    "previously_fixed_in": {"type": "string"},
                    "currently_affected": {"type": "string"},
                    "affected_customers": {"type": "integer"},
                    "confidence": {"type": "string"},
                },
                "required": ["issue"],
            },
        }
    },
    "required": ["regressions"],
}


def _iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.isoformat()


def _on_worker(method):
    """Run a method on the client's single dedicated thread.

    The Hindsight SDK caches an asyncio event loop per thread and binds its
    aiohttp session to that loop. FastAPI executes sync endpoints on a thread
    pool, so calling the SDK from arbitrary threads corrupts the loop. Pinning
    every call to one worker keeps the SDK and its loop consistent.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        return self._executor.submit(method, self, *args, **kwargs).result()

    return wrapper


def _run_async(coro):
    """Run an async Hindsight sub-API call from synchronous code.

    The high-level operations (retain/recall/reflect) are synchronous, but the
    ``banks`` / ``operations`` / ``mental_models`` sub-APIs are async. We must
    reuse the SDK's own event loop (it caches one) instead of ``asyncio.run``,
    which would close the loop the sync methods depend on.
    """
    try:
        from hindsight_client.hindsight_client import _run_async as sdk_run_async

        return sdk_run_async(coro)
    except Exception:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class HindsightMemory:
    """Synchronous Hindsight client wrapper."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url or cfg.HINDSIGHT_BASE_URL
        self.api_key = api_key if api_key is not None else cfg.HINDSIGHT_API_KEY
        self.client = Hindsight(base_url=self.base_url, api_key=self.api_key, timeout=120.0)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hindsight")

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    @_on_worker
    def health(self) -> dict[str, Any]:
        version = self.client.get_version()
        return {
            "ok": True,
            "base_url": self.base_url,
            "api_version": getattr(version, "api_version", None),
        }

    def close(self) -> None:
        with contextlib.suppress(Exception):  # best effort
            self._executor.submit(self.client.close).result(timeout=5)
        self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Banks
    # ------------------------------------------------------------------
    @_on_worker
    def ensure_org_bank(self) -> None:
        self._safe(
            "create_bank:org",
            lambda: self.client.create_bank(
                bank_id=cfg.ORG_BANK_ID,
                name=cfg.ORG_NAME,
                mission=cfg.ORG_MISSION,
                observations_mission=cfg.ORG_OBSERVATIONS_MISSION,
                reflect_mission=cfg.ORG_REFLECT_MISSION,
                enable_observations=True,
                disposition_skepticism=3,
                disposition_literalism=4,
                disposition_empathy=2,
            ),
        )
        # Redact secrets/PII before anything reaches the shared institutional bank.
        self._safe(
            "update_bank_config",
            lambda: self.client.update_bank_config(
                cfg.ORG_BANK_ID,
                memory_defense={"mode": "redact"},
            ),
        )
        for name, content, priority in cfg.DIRECTIVES:
            self._safe(
                "create_directive",
                lambda name=name, content=content, priority=priority: self.client.create_directive(
                    cfg.ORG_BANK_ID, name=name, content=content, priority=priority
                ),
            )

    @_on_worker
    def ensure_customer_bank(self, customer: Customer) -> None:
        self._safe(
            "create_bank:customer",
            lambda: self.client.create_bank(
                bank_id=self.customer_bank_id(customer.id),
                name=f"{customer.company} ({customer.name})",
                mission=cfg.CUSTOMER_MISSION_TEMPLATE.format(name=customer.name, company=customer.company),
                enable_observations=True,
                disposition_skepticism=3,
                disposition_literalism=3,
                disposition_empathy=5,
            ),
        )
        for name, content, priority in cfg.DIRECTIVES:
            self._safe(
                "create_directive",
                lambda name=name, content=content, priority=priority: self.client.create_directive(
                    self.customer_bank_id(customer.id), name=name, content=content, priority=priority
                ),
            )

    @staticmethod
    def customer_bank_id(customer_id: str) -> str:
        return f"cust:{customer_id}"

    # ------------------------------------------------------------------
    # Retain
    # ------------------------------------------------------------------
    @staticmethod
    def ticket_content(ticket: Ticket) -> str:
        """Rich, un-summarised representation — Hindsight extracts the facts."""
        parts = [
            f"Support ticket {ticket.id}",
            f"Product: {ticket.product} {ticket.version}",
            f"Module: {ticket.module}",
            f"Issue type: {ticket.issue_type}",
            f"Subject: {ticket.subject}",
            f"Customer wrote: {ticket.body}",
        ]
        if ticket.resolution:
            parts.append(f"Resolution: {ticket.resolution}")
            parts.append("Status: resolved")
        else:
            parts.append("Status: open")
        return "\n".join(parts)

    @staticmethod
    def ticket_tags(ticket: Ticket) -> list[str]:
        return [
            f"product:{ticket.product}",
            f"version:{ticket.version}",
            f"module:{ticket.module}",
            f"issue-type:{ticket.issue_type}",
            f"customer:{ticket.customer_id}",
        ]

    @_on_worker
    def retain_org_ticket(self, ticket: Ticket) -> str | None:
        resp = self.client.retain(
            bank_id=cfg.ORG_BANK_ID,
            content=self.ticket_content(ticket),
            context=f"support ticket in {ticket.module} for {ticket.product} {ticket.version}",
            timestamp=ticket.created_at,
            document_id=f"ticket:{ticket.id}",
            tags=[cfg.TAG_SCOPE_ORG, *self.ticket_tags(ticket)],
        )
        return getattr(resp, "operation_id", None)

    @_on_worker
    def retain_customer_ticket(self, ticket: Ticket) -> str | None:
        resp = self.client.retain(
            bank_id=self.customer_bank_id(ticket.customer_id),
            content=self.ticket_content(ticket),
            context=f"interaction with this customer about {ticket.module}",
            timestamp=ticket.created_at,
            document_id=f"ticket:{ticket.id}",
            tags=self.ticket_tags(ticket),
        )
        return getattr(resp, "operation_id", None)

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------
    @_on_worker
    def recall_customer_setup(self, customer_id: str) -> list[Citation]:
        resp = self.client.recall(
            bank_id=self.customer_bank_id(customer_id),
            query="What is this customer's environment, plan, preferences and past issues?",
            budget="mid",
            max_tokens=1200,
        )
        return [
            Citation(kind="customer_history", text=r.text, score=_score(r), tags=list(r.tags or []))
            for r in resp.results
        ]

    @_on_worker
    def recall_known_issues(
        self,
        query: str,
        *,
        product: str | None = None,
        version: str | None = None,
        module: str | None = None,
    ) -> list[Citation]:
        tags = [cfg.TAG_SCOPE_ORG]
        if product:
            tags.append(f"product:{product}")
        resp = self.client.recall(
            bank_id=cfg.ORG_BANK_ID,
            query=query,
            types=["observation", "world"],
            tags=tags,
            tags_match="all",
            budget="mid",
            max_tokens=1600,
            include_source_facts=True,
        )
        out: list[Citation] = []
        for r in resp.results:
            out.append(
                Citation(
                    kind="known_issue",
                    text=r.text,
                    score=_score(r),
                    tags=list(r.tags or []),
                    source_fact_ids=list(r.source_fact_ids or []),
                )
            )
        return out

    @_on_worker
    def reflect_customer(self, customer_id: str, query: str, *, context: str | None = None) -> str:
        resp = self.client.reflect(
            bank_id=self.customer_bank_id(customer_id),
            query=query,
            context=context,
            budget="mid",
            max_tokens=1200,
        )
        return resp.text

    # ------------------------------------------------------------------
    # Proactive regression detection
    #
    # This is the "new take": instead of only answering when asked, the agent
    # reflects over the institutional memory to find issues the company
    # believed were fixed but that are being reported again.
    # ------------------------------------------------------------------
    @_on_worker
    def detect_regressions(self) -> list[dict]:
        resp = self._safe(
            "detect_regressions",
            lambda: self.client.reflect(
                bank_id=cfg.ORG_BANK_ID,
                query=(
                    "Review the institutional memory and find any product issue that was "
                    "previously believed fixed but is now being reported again by customers. "
                    "For each, give the issue name, the version it was believed fixed in, the "
                    "version(s) currently affected, an approximate number of affected "
                    "customers or tickets, and your confidence."
                ),
                context="proactive regression audit over all customer tickets",
                response_schema=REGRESSION_SCHEMA,
                budget="mid",
            ),
        )
        if not resp:
            return []
        output = getattr(resp, "structured_output", None)
        if isinstance(output, dict):
            regressions = output.get("regressions")
            if isinstance(regressions, list):
                return [r for r in regressions if isinstance(r, dict)]
        return []

    # ------------------------------------------------------------------
    # Mental models (read = pure DB read, no LLM call)
    # ------------------------------------------------------------------
    @_on_worker
    def ensure_mental_models(self) -> list[str]:
        def ensure(mm_id: str, name: str, source_query: str) -> str | None:
            resp = self._safe(
                f"create_mental_model:{mm_id}",
                lambda: self.client.create_mental_model(
                    bank_id=cfg.ORG_BANK_ID,
                    id=mm_id,
                    name=name,
                    source_query=source_query,
                    tags=[cfg.TAG_SCOPE_ORG],
                    trigger={"refresh_after_consolidation": True, "mode": "delta"},
                ),
            )
            op_id = getattr(resp, "operation_id", None)
            if not op_id:
                # Already exists (re-run) -> refresh instead of create.
                refreshed = self._safe(
                    f"refresh_mental_model:{mm_id}",
                    lambda: self.client.refresh_mental_model(cfg.ORG_BANK_ID, mm_id),
                )
                op_id = getattr(refreshed, "operation_id", None)
            return op_id

        operation_ids = []
        for mm_id, name, query in (
            (
                MM_EMERGING_ISSUES,
                "Emerging Issues",
                "What recurring product defects or regressions are showing up across "
                "customers right now, how many customers are affected, and is each "
                "trend rising or falling?",
            ),
            (
                MM_KNOWN_ISSUES,
                "Known Issues",
                "What product issues do we understand well enough to describe the "
                "symptom, the affected versions and the recommended workaround?",
            ),
        ):
            op = ensure(mm_id, name, query)
            if op:
                operation_ids.append(op)
        return operation_ids

    @_on_worker
    def read_mental_model(self, model_id: str) -> KnownIssue | None:
        try:
            mm = self.client.get_mental_model(cfg.ORG_BANK_ID, model_id, detail="content")
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("mental model %s unavailable: %s", model_id, exc)
            return None
        return KnownIssue(
            id=getattr(mm, "id", model_id),
            name=getattr(mm, "name", model_id),
            content=getattr(mm, "content", "") or "",
            last_refreshed_at=getattr(mm, "last_refreshed_at", None),
            is_stale=getattr(mm, "is_stale", None),
        )

    @_on_worker
    def refresh_all_mental_models(self) -> list[str]:
        operation_ids: list[str] = []
        for mm_id in (MM_EMERGING_ISSUES, MM_KNOWN_ISSUES):
            resp = self._safe(
                f"refresh_mental_model:{mm_id}",
                lambda mm_id=mm_id: self.client.refresh_mental_model(cfg.ORG_BANK_ID, mm_id),
            )
            op_id = getattr(resp, "operation_id", None)
            if op_id:
                operation_ids.append(op_id)
        return operation_ids

    # ------------------------------------------------------------------
    # Consolidation / async operations
    # ------------------------------------------------------------------
    @_on_worker
    def trigger_consolidation(self) -> str | None:
        resp = self._safe(
            "trigger_consolidation",
            lambda: _run_async(self.client.banks.trigger_consolidation(cfg.ORG_BANK_ID)),
        )
        return getattr(resp, "operation_id", None)

    @_on_worker
    def wait_for_operation(self, operation_id: str, *, timeout: float = OPERATION_TIMEOUT_S) -> bool:
        """Poll an async operation until it leaves a pending state."""
        if not operation_id:
            return True
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status = _run_async(
                    self.client.operations.get_operation_status(cfg.ORG_BANK_ID, operation_id)
                )
            except Exception as exc:  # pragma: no cover
                log.warning("could not poll operation %s: %s", operation_id, exc)
                return False
            state = (getattr(status, "status", "") or "").lower()
            if state in {"completed", "succeeded", "failed", "cancelled", "error"}:
                if state not in {"completed", "succeeded"}:
                    log.warning("operation %s ended as %s", operation_id, state)
                return state in {"completed", "succeeded"}
            time.sleep(OPERATION_POLL_S)
        log.warning("operation %s timed out after %.0fs", operation_id, timeout)
        return False

    def settle(self, seconds: float = 4.0) -> None:
        """Give the background worker a beat to run.

        Retain extraction and observation consolidation are asynchronous; there
        is no documented "wait until settled" call, so the seeding script uses an
        explicit settle + consolidation trigger before declaring the bank ready.
        """
        time.sleep(seconds)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    @staticmethod
    def _safe(label: str, fn) -> Any | None:
        try:
            return fn()
        except Exception as exc:  # pragma: no cover - best effort idempotent setup
            log.info("setup step %s skipped/failed: %s", label, exc)
            return None


def _score(result: Any) -> float | None:
    scores = getattr(result, "scores", None)
    if isinstance(scores, dict):
        for key in ("final", "rerank", "cross_encoder", "score"):
            if key in scores:
                try:
                    return float(scores[key])
                except (TypeError, ValueError):
                    continue
    return None


def format_citations(citations: Iterable[Citation]) -> str:
    lines = []
    for i, c in enumerate(citations, 1):
        lines.append(f"[{i}] ({c.kind}) {c.text}")
    return "\n".join(lines)
