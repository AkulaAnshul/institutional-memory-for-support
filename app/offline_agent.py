"""A deterministic, rule-based agent used only when Groq is unavailable.

It calls the *real* memory tools, so the demo, the UI and the eval still work
offline. It is deliberately simple: the point of the project is the memory, not
the prose. The Groq-backed ``SupportAgent`` is the production path.
"""
from __future__ import annotations

import time

from .models import Customer, DraftResult, Ticket
from .tools import SupportTools


class OfflineAgent:
    def draft(self, customer: Customer, ticket: Ticket, tools: SupportTools | None) -> DraftResult:
        started = time.perf_counter()
        mode = "memory" if tools is not None else "amnesia"

        if tools is None:
            draft = (
                f"Hi {customer.name.split()[0]},\n\n"
                f"Thanks for reaching out about \"{ticket.subject}\". Please try clearing your cache "
                "and retrying; if the problem persists, reply here and we will look into it.\n\n"
                "Best,\nAcme Support"
            )
        else:
            tools.dispatch("recall_customer_history", {})
            tools.dispatch("find_known_issues", {"query": f"{ticket.subject} {ticket.module}"})
            tools.dispatch("get_emerging_issues", {})

            history = [c for c in tools.citations if c.kind == "customer_history"]
            known = [c for c in tools.citations if c.kind == "known_issue"]
            emerging = [c for c in tools.citations if c.kind == "emerging_issue"]

            lines = [f"Hi {customer.name.split()[0]},", ""]
            if history:
                lines.append(
                    f"I can see from your history that we've worked together before on "
                    f"{ticket.module} — thank you for your patience."
                )
                lines.append("")
            if known:
                lines.append(
                    f"This looks like a known issue affecting {ticket.module} on {ticket.product} "
                    f"{ticket.version}. {known[0].text}"
                )
                lines.append("")
                lines.append("Recommended workaround: use a scheduled export or narrow the date range.")
            else:
                lines.append(
                    "I don't see this exact symptom recorded as a known issue yet, so I've logged "
                    "it with the product team and will follow up."
                )
            if emerging:
                lines.append("")
                lines.append("(Internal note: this area is showing up in the current emerging-issues report.)")
            lines += ["", "Best,", "Acme Support"]
            draft = "\n".join(lines)

        elapsed = int((time.perf_counter() - started) * 1000)
        return DraftResult(
            ticket_id=ticket.id,
            mode=mode,
            draft=draft,
            citations=tools.citations if tools else [],
            tool_calls=tools.traces if tools else [],
            used_memory=bool(tools and tools.citations),
            elapsed_ms=elapsed,
        )
