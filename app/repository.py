"""Load the JSONL dataset into typed models."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import config as cfg
from .models import Customer, Ticket


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


@lru_cache
def load_customers() -> dict[str, Customer]:
    rows = _read_jsonl(cfg.DATA_DIR / "customers.jsonl")
    return {row["id"]: Customer(**row) for row in rows}


def _to_ticket(row: dict) -> Ticket:
    return Ticket(**{k: v for k, v in row.items() if k in Ticket.model_fields})


def load_history_tickets() -> list[Ticket]:
    return [_to_ticket(r) for r in _read_jsonl(cfg.DATA_DIR / "seed_tickets.jsonl")]


def load_demo_stream() -> list[Ticket]:
    return [_to_ticket(r) for r in _read_jsonl(cfg.DATA_DIR / "demo_stream.jsonl")]


def load_kb_articles() -> list[dict]:
    return _read_jsonl(cfg.DATA_DIR / "kb_articles.jsonl")
