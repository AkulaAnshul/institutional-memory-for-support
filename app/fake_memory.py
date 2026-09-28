"""An in-process stand-in for Hindsight, used only for offline UI dev and tests.

The real submission always runs against Hindsight (see ``memory.py``). This fake
implements the same surface so the app, the eval and the test-suite can run
without network access. It makes no claims of being a good memory system.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from .models import Citation, KnownIssue, Ticket
from .repository import load_kb_articles

_WORD = re.compile(r"[a-z0-9]+")


def _terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if len(w) > 3}


class FakeMemory:
    def __init__(self, *_: Any, **__: Any) -> None:
        self.customer_events: dict[str, list[dict]] = {}
        self.org_events: list[dict] = []
        self._kb = load_kb_articles()

    # ---- setup ----
    def health(self) -> dict[str, Any]:
        return {"ok": True, "base_url": "fake", "api_version": "fake-0"}

    def close(self) -> None:
        return None

    def ensure_org_bank(self) -> None:
        return None

    def ensure_customer_bank(self, customer) -> None:  # noqa: ANN001
        return None

    def ensure_mental_models(self) -> list[str]:
        return []

    def refresh_all_mental_models(self) -> list[str]:
        return []

    def trigger_consolidation(self) -> None:
        return None

    def wait_for_operation(self, operation_id: str, **_: Any) -> bool:
        return True

    def settle(self, seconds: float = 0.0) -> None:
        return None

    # ---- retain ----
    def _record(self, ticket: Ticket) -> None:
        text = self.ticket_content(ticket)
        row = {
            "text": text,
            "tags": self.ticket_tags(ticket),
            "timestamp": ticket.created_at,
            "customer_id": ticket.customer_id,
            "module": ticket.module,
            "issue_type": ticket.issue_type,
            "version": ticket.version,
        }
        self.customer_events.setdefault(ticket.customer_id, []).append(row)
        self.org_events.append(row)

    def retain_org_ticket(self, ticket: Ticket) -> str | None:
        self._record(ticket)
        return "fake-op"

    def retain_customer_ticket(self, ticket: Ticket) -> str | None:
        self._record(ticket)
        return "fake-op"

    @staticmethod
    def ticket_content(ticket: Ticket) -> str:
        from .memory import HindsightMemory

        return HindsightMemory.ticket_content(ticket)

    @staticmethod
    def ticket_tags(ticket: Ticket) -> list[str]:
        from .memory import HindsightMemory

        return HindsightMemory.ticket_tags(ticket)

    # ---- recall ----
    def recall_customer_setup(self, customer_id: str) -> list[Citation]:
        rows = self.customer_events.get(customer_id, [])
        return [
            Citation(kind="customer_history", text=r["text"], tags=r["tags"])
            for r in rows[-4:]
        ]

    def recall_known_issues(self, query: str, *, product=None, version=None, module=None) -> list[Citation]:
        q = _terms(query)
        hits = [r for r in self.org_events if q & _terms(r["text"])]
        # Prefer repeated modules -> approximate observation consolidation.
        counts: dict[str, int] = {}
        for r in hits:
            counts[r["module"]] = counts.get(r["module"], 0) + 1
        out: list[Citation] = []
        for module_name, count in sorted(counts.items(), key=lambda kv: -kv[1])[:3]:
            sample = next(r for r in hits if r["module"] == module_name)
            out.append(
                Citation(
                    kind="known_issue",
                    text=f"{module_name}: recurring issue seen across {count} tickets. "
                    f"Example: {sample['text'].splitlines()[0]}",
                    tags=sample["tags"],
                )
            )
        return out

    def reflect_customer(self, customer_id: str, query: str, *, context=None) -> str:
        rows = self.customer_events.get(customer_id, [])
        return f"Based on {len(rows)} recorded interactions, the customer's recent theme is: " + (
            rows[-1]["text"].splitlines()[-1] if rows else "no prior interactions"
        )

    # ---- mental models ----
    def read_mental_model(self, model_id: str) -> KnownIssue | None:
        counts: dict[str, int] = {}
        for r in self.org_events:
            counts[r["module"]] = counts.get(r["module"], 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
        content = "\n".join(f"- {m}: {c} tickets" for m, c in top) or "No issues recorded yet."
        return KnownIssue(
            id=model_id,
            name=model_id,
            content=content,
            last_refreshed_at=datetime.now(UTC),
            is_stale=False,
        )

    def detect_regressions(self) -> list[dict]:
        """Offline heuristic: a module with a 'believed fixed' note that later
        shows a regression is flagged, mirroring what Hindsight.reflect finds."""
        fixed_modules = {
            r["module"] for r in self.org_events if "believed fixed" in r["text"].lower()
        }
        regressions = []
        for module in fixed_modules:
            affected = [r for r in self.org_events if r["module"] == module and r["issue_type"] == "regression"]
            if affected:
                regressions.append(
                    {
                        "issue": f"{module}: previously-fixed issue reported again",
                        "previously_fixed_in": "v2.3",
                        "currently_affected": affected[-1]["version"],
                        "affected_customers": len(affected),
                        "confidence": "high",
                    }
                )
        return regressions
