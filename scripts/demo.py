"""Run the headline demo: the same ticket answered with and without memory.

Usage:
    ./.conda/bin/python scripts/demo.py [TICKET_ID]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service import SupportService  # noqa: E402


def show(label: str, result) -> None:
    print("=" * 78)
    print(f"{label}  ({result.elapsed_ms} ms, {len(result.citations)} memories, {len(result.tool_calls)} tool calls)")
    print("-" * 78)
    print(result.draft or f"[error] {result.error}")
    if result.citations:
        print("\nGrounded in:")
        for c in result.citations:
            print(f"  - ({c.kind}) {c.text[:140]}")


def main() -> None:
    service = SupportService()
    if not service.seeded and os.getenv("SKIP_SEED") != "1":
        service.seed_history()

    if len(sys.argv) > 1:
        ticket = service.ticket(sys.argv[1])
    else:
        ticket = next(t for t in service.demo_stream() if t.issue_type == "regression")
    assert ticket is not None, "ticket not found"

    customer = service.customer_for(ticket.customer_id)
    print(f"Ticket {ticket.id} — {ticket.subject}")
    print(f"Customer: {customer.name} ({customer.company}), {customer.environment}\n")

    show("AMNESIA (no memory)", service.process(ticket, mode="amnesia"))
    show("MEMORY (Hindsight)", service.process(ticket, mode="memory"))

    emerging = service.emerging_issues()
    print("=" * 78)
    print("EMERGING ISSUES (read from Hindsight mental model, no LLM call)")
    print("-" * 78)
    print(emerging.content if emerging and emerging.content else "(not built yet)")


if __name__ == "__main__":
    main()
