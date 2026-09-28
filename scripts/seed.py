"""Seed the historical tickets into Hindsight and wait for memory to settle.

Usage:
    ./.conda/bin/python scripts/seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service import SupportService  # noqa: E402


def main() -> None:
    service = SupportService()
    print(f"memory backend: {type(service.memory).__name__} @ {service.memory.health().get('base_url')}")
    print("seeding history (retain extraction + consolidation are asynchronous)...")
    out = service.seed_history()
    print(f"seeded {out['seeded_tickets']} tickets across {out['customers']} customers")
    emerging = service.emerging_issues()
    print("\nEmerging issues mental model:")
    print(emerging.content if emerging and emerging.content else "(still building — re-run in a moment)")


if __name__ == "__main__":
    main()
