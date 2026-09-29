"""Configuration, bank missions and tag conventions.

Everything is read from the environment so the same code runs against
Hindsight Cloud or a self-hosted/embedded Hindsight server.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
FRONTEND_DIR = ROOT / "frontend"


def _get(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


HINDSIGHT_BASE_URL = _get("HINDSIGHT_BASE_URL", "HINDSIGHT_API_URL", default="http://localhost:8888")
HINDSIGHT_API_KEY = _get("HINDSIGHT_API_KEY")

GROQ_API_KEY = _get("GROQ_API_KEY")
# The brief recommends qwen/qwen3-32b, but Groq shut that model down on
# 2026-07-17. We default to openai/gpt-oss-20b (cheap, fast, tool calling);
# set GROQ_MODEL=openai/gpt-oss-120b for maximum reply quality.
GROQ_MODEL = _get("GROQ_MODEL", default="openai/gpt-oss-20b")

ORG_BANK_ID = _get("ORG_BANK_ID", default="org:acme")
ORG_NAME = "Acme Support"
DEFAULT_PRODUCT = "Acme Cloud"

# ---------------------------------------------------------------------------
# Tags
#
# Tags are Hindsight's isolation/filter mechanism (metadata is NOT filterable).
# We keep the tag vocabulary small and stable so observations consolidate
# across customers instead of fragmenting into per-session silos.
# ---------------------------------------------------------------------------
TAG_SCOPE_ORG = "scope:org"

# ---------------------------------------------------------------------------
# Bank missions — vague missions are the #1 cause of low-quality memories, so
# these are deliberately explicit about what to extract and what to ignore.
# ---------------------------------------------------------------------------
ORG_MISSION = (
    "You are the institutional memory for a B2B SaaS support organisation. "
    "Your job is to synthesise recurring product defects, regressions and feature "
    "requests from support tickets across all customers. Extract the product, module, "
    "affected version, the observable symptom, any workaround, and whether the issue "
    "maps to a previously believed-fixed bug. IGNORE one-off how-to questions, praise, "
    "and anything that is not evidence of a product-level pattern."
)

ORG_OBSERVATIONS_MISSION = (
    "Consolidate facts into durable, evidence-backed observations about recurring "
    "product issues. Each observation should name the product area, describe the "
    "symptom in one sentence, and preserve any history of the issue being reported, "
    "believed fixed, and then reported again. Prefer merging duplicates over creating "
    "near-identical observations."
)

ORG_REFLECT_MISSION = (
    "You are a support operations analyst. When asked about emerging issues, cite the "
    "specific recurring symptom, how many customers are affected, and whether the trend "
    "is rising. Be concise and evidence-led."
)

CUSTOMER_MISSION_TEMPLATE = (
    "You are the dedicated support memory for customer {name} ({company}). Remember "
    "their environment, plan, past tickets, the fixes that actually worked, and their "
    "communication preferences. Never invent a workaround that has not been recorded."
)

# Hard rules (guardrails) applied to both banks.
DIRECTIVES = [
    (
        "no-false-promises",
        "Never promise a refund, credit, SLA waiver, or delivery date. "
        "Escalate those requests to a human instead.",
        10,
    ),
    (
        "cite-memory",
        "When referring to a previous interaction or a known issue, cite it explicitly "
        "rather than implying you remember something you were not given.",
        8,
    ),
    (
        "no-invented-fixes",
        "Only suggest a workaround that appears in memory or in the knowledge base. "
        "If none exists, say so and offer next steps.",
        8,
    ),
]
