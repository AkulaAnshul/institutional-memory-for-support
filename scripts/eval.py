"""Before/after evaluation: replay the demo stream in both modes and measure.

Writes results/eval_report.md with the comparison the judges care about.

Usage:
    ./.conda/bin/python scripts/eval.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.service import SupportService  # noqa: E402

RESULTS = ROOT / "results"
# Keep offline (fake memory / offline agent) results separate so they never
# overwrite the real cloud numbers.
SUFFIX = "_offline" if (os.getenv("USE_FAKE_MEMORY") == "1" or os.getenv("USE_FAKE_AGENT") == "1") else ""


def grounded(result) -> bool:
    return bool(result.citations) and any(c.kind in {"known_issue", "customer_history"} for c in result.citations)


def main() -> None:
    service = SupportService()
    if not service.seeded and os.getenv("SKIP_SEED") != "1":
        service.seed_history()

    limit = int(os.getenv("EVAL_LIMIT", "0") or 0)
    stream = service.demo_stream()
    if limit:
        stream = stream[:limit]

    # Amnesia replies can never cite memory, so we sample only a few to establish
    # the baseline and spend the rest of the (daily) token budget on memory mode.
    amnesia_sample = int(os.getenv("AMNESIA_SAMPLE", "3") or 0)

    rows = []
    aborted = None
    for index, ticket in enumerate(stream, 1):
        memory_result = service.process(ticket, mode="memory")
        if memory_result.error and "daily token limit" in memory_result.error.lower():
            aborted = memory_result.error
            print(f"! stopping at ticket {index}/{len(stream)}: {aborted}")
            break

        amnesia_result = service.process(ticket, mode="amnesia") if index <= amnesia_sample else None
        rows.append(
            {
                "ticket": ticket.id,
                "issue_type": ticket.issue_type,
                "memory_grounded": grounded(memory_result),
                "memory_citations": len(memory_result.citations),
                "memory_ms": memory_result.elapsed_ms,
                "memory_error": memory_result.error,
                "amnesia_grounded": grounded(amnesia_result) if amnesia_result else None,
                "amnesia_citations": len(amnesia_result.citations) if amnesia_result else None,
                "amnesia_ms": amnesia_result.elapsed_ms if amnesia_result else None,
            }
        )
        print(f"  [{index}/{len(stream)}] {ticket.id} ({ticket.issue_type}) "
              f"grounded={rows[-1]['memory_grounded']} citations={rows[-1]['memory_citations']}")

    n = len(rows)
    if n == 0:
        print("No tickets evaluated.")
        return

    amnesia_rows = [r for r in rows if r["amnesia_grounded"] is not None]
    summary = {
        "tickets": n,
        "aborted": aborted,
        "memory_grounded_rate": sum(r["memory_grounded"] for r in rows) / n,
        "amnesia_grounded_rate": (
            sum(r["amnesia_grounded"] for r in amnesia_rows) / len(amnesia_rows)
            if amnesia_rows else 0.0
        ),
        "avg_memory_citations": sum(r["memory_citations"] for r in rows) / n,
        "avg_amnesia_citations": (
            sum(r["amnesia_citations"] for r in amnesia_rows) / len(amnesia_rows)
            if amnesia_rows else 0.0
        ),
    }

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"eval{SUFFIX}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))

    report = [
        "# Evaluation — Amnesia vs Memory",
        "",
        f"Tickets replayed: **{n}**"
        + (f"  (stopped early: {aborted})" if aborted else ""),
        f"Amnesia baseline sampled on **{len(amnesia_rows)}** tickets.",
        "",
        "| Metric | Amnesia | Memory (Hindsight) |",
        "|---|---|---|",
        f"| Replies grounded in memory | {summary['amnesia_grounded_rate']:.0%} | {summary['memory_grounded_rate']:.0%} |",
        f"| Avg memories cited per reply | {summary['avg_amnesia_citations']:.2f} | {summary['avg_memory_citations']:.2f} |",
    ]
    (RESULTS / f"eval_report{SUFFIX}.md").write_text("\n".join(report) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"\nwrote {RESULTS/f'eval_report{SUFFIX}.md'} and {RESULTS/f'eval{SUFFIX}.json'}")


if __name__ == "__main__":
    main()
