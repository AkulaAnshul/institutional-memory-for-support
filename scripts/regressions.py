"""Proactive regression audit: issues believed fixed that are back.

Usage:
    SKIP_SEED=1 ./.conda/bin/python scripts/regressions.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service import SupportService  # noqa: E402


def main() -> None:
    service = SupportService()
    if not service.seeded and os.getenv("SKIP_SEED") != "1":
        service.seed_history()

    regressions = service.detect_regressions()
    print(f"Regression audit — {len(regressions)} found")
    print("=" * 70)
    for r in regressions:
        print(f"- {r.get('issue', 'issue')}")
        print(
            f"    fixed in {r.get('previously_fixed_in', '?')} · "
            f"back in {r.get('currently_affected', '?')} · "
            f"{r.get('affected_customers', '?')} affected · {r.get('confidence', '')}"
        )


if __name__ == "__main__":
    main()
