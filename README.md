# Institutional Memory for Support

A customer-support agent that remembers each customer **and** grows a company-wide
brain from the ticket stream. Built on [Hindsight](https://hindsight.vectorize.io/),
the agent-memory system that makes agents *learn*, not just remember.

> **The support agent is the interface. The memory is the product.**

> Without memory the agent is a stateless chatbot. With Hindsight it recognises the
> customer, spots the recurring pattern, cites the prior interaction, and tells you
> the workaround — because it has seen the issue 40 times before.

## Why this is a fresh take (not just another support bot)

The real problem we target is **institutional knowledge loss**: every company forgets what
it fixed, why, and whether it stayed fixed. The support agent is the interface; the memory
is the product.

| The obvious chatbot | This project |
|---|---|
| Remembers one conversation | Remembers across **months, customers, and the whole company** |
| Answers when asked | **Proactively audits** memory and raises regression alerts |
| Stores chat history | **Consolidates** recurring tickets into evidence-backed observations |
| Forgets the pattern | **Preserves the history** of an issue being reported, "fixed", and reported again |
| A feature you bolt on | A reusable **institutional-memory layer**; support is just the first interface |

The headline capability is the **regression audit** (see `scripts/regressions.py`): the
agent reflects over the institutional memory and surfaces issues the company believed were
fixed but that are being reported again — before a human notices.

## The idea in one picture

```
                              ┌────────────────────────────────────────────┐
                              │                Hindsight                    │
                              │                                             │
   new ticket ──► Groq agent  │  app/cust:<id>  ── per-customer memory      │
        │            │        │    (environment, history, preferences)     │
        │            │        │                                             │
        │            └──────► │  app/org:acme   ── institutional memory     │
        │       retain/recall  │    tags: product / version / module / ...  │
        │            ┌───────  │    → observations (evidence + proof count) │
        │            │        │    → mental models (Emerging / Known Issues)│
        └────────────┘        └────────────────────────────────────────────┘
                                       ▲                    │
                                       │ consolidation       │ O(1) read, no LLM
                                       │ (background)        ▼
                              ┌────────────────────────────────────────────┐
                              │  Live dashboard: Emerging Issues           │
                              └────────────────────────────────────────────┘
```

The agent runs **two banks** per tenant because Hindsight isolates banks strictly:
a **customer bank** for personalisation and a shared **org bank** for pattern
detection. Tickets are written to both after the reply is drafted — never in the
same turn as recall, because Hindsight extracts memories asynchronously.

## How Hindsight is used

| Hindsight feature | Where | Why it matters |
|---|---|---|
| `retain()` with `timestamp`, `context`, `tags` | `app/memory.py` | rich, un-summarised turns become factual memories |
| `recall()` (TEMPR: semantic + BM25 + graph + temporal) | `app/tools.py` | customer history and known-issue search |
| **Observations** (evidence-backed, refined not overwritten) | org bank | recurring tickets collapse into a belief with a proof count |
| **Mental models** (read with no LLM call) | `Emerging Issues`, `Known Issues` | instant dashboard, refreshed after consolidation |
| **Conflict resolution** | demo storyline | an issue "fixed in v2.3" is reported again in v2.4 |
| **`reflect` + structured output** | regression audit | surfaces fixed-then-back issues as alerts |
| Missions, directives, disposition | `app/config.py` | what to extract, hard rules, empathy tuning |
| Memory Defense | org bank | secrets/PII redacted before the shared bank |
| Per-bank isolation | customer banks | no cross-customer leakage |

## Quick start

**Full step-by-step instructions (including a no-key offline demo and a showcase script):
[`docs/RUN_AND_SHOWCASE.md`](docs/RUN_AND_SHOWCASE.md).**

Everything lives in this directory; the Python env is project-local and the frontend has
**no npm/build step**. The easiest path is the one-command setup script.

```bash
# 1. One-command setup (conda or venv; creates .env from the example)
./setup.sh                 # macOS/Linux
# setup.bat                # Windows (double-click)

# 2. Add your keys to .env, then seed history into Hindsight
./.conda/bin/python scripts/seed.py

# 3. Run the console
./run.sh                   # http://127.0.0.1:8000   (Windows: run.bat)
```

### Keys

- **GROQ_API_KEY** — https://console.groq.com/keys. The default model is
  `openai/gpt-oss-120b`. (The brief's `qwen/qwen3-32b` was shut down on 2026‑07‑17.)
- **Hindsight** — either Hindsight Cloud (`HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io`,
  use promo `MEMHACK99` for credits) or a self-hosted server
  (`http://localhost:8888`). See `.env.example` for the Docker one-liner.

### Offline mode (no keys)

To explore the UI and pipeline with neither service configured:

```bash
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/demo.py
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/regressions.py
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/eval.py
```

The offline path uses an in-process memory stand-in and a deterministic agent so
the whole product is still demonstrable. The production path is Hindsight + Groq.

## Demo

The dataset tells one story: a CSV-export timeout spreads through Q1 and is
"believed fixed in v2.3", then returns in v2.4 as a 504 regression — directly
contradicting the belief stored in memory. The demo replays the Q2 stream live:

1. **Seed** the Q1 history.
2. **Play the live stream** and watch replies go from generic to grounded; the
   **Learning curve** chart tracks grounded replies per ticket.
3. The **Emerging Issues** panel updates straight from Hindsight, no LLM call.
4. Click **Run regression audit** and the agent reports the fixed-then-back issue
   as an alert — the proactive capability that makes this more than a support bot.

```
./.conda/bin/python scripts/demo.py     # one ticket, both modes, side by side
./.conda/bin/python scripts/eval.py     # metrics + results/eval_report.md
SKIP_SEED=1 ./.conda/bin/python scripts/regressions.py   # proactive regression audit
```

## Evaluation

`scripts/eval.py` replays the demo stream in both modes and writes
`results/eval_report.md` (or `_offline` for the no-key path).

```bash
./.conda/bin/python scripts/eval.py                 # full run (needs Groq tokens)
SKIP_SEED=1 EVAL_LIMIT=8 ./.conda/bin/python scripts/eval.py   # sample
SKIP_SEED=1 AMNESIA_SAMPLE=3 ./.conda/bin/python scripts/eval.py  # default
```

Useful env flags:

- `SKIP_SEED=1` — don't re-ingest history (it's already in Hindsight).
- `EVAL_LIMIT=N` — evaluate the first N tickets.
- `AMNESIA_SAMPLE=N` — amnesia replies can never cite memory, so only N are
  sampled as a baseline (default 3).
- `USE_FAKE_MEMORY=1` / `USE_FAKE_AGENT=1` — run fully offline.

Offline sample output:

| Metric | Amnesia | Memory (Hindsight) |
|---|---|---|
| Replies grounded in memory | 0% | 100% |
| Avg memories cited per reply | 0.00 | 7.27 |

> **Token budget:** the Groq free tier allows 200k tokens/day on `gpt-oss-120b`.
> Tool output is capped (see `MAX_MEMORIES`/`_clip` in `app/tools.py`) to keep a
> ticket at roughly 2–3k tokens, so the full 51-ticket run fits. A *daily* limit
> is detected and fails fast rather than sleeping on it (`RateLimitExceeded`).

## Tests

```bash
./.conda/bin/python -m pytest
```

Covers the data storyline, bank isolation, the agent's tool loop, mode separation,
and Groq 400/429 retry handling.

## Layout

```
app/        config, models, memory wrapper, tools, agent, offline agent, pipeline, API
data/       synthetic customers, historical tickets, demo stream, knowledge base
frontend/   hand-written HTML/CSS/JS console (served by FastAPI)
scripts/    generate_data, seed, demo, eval, regressions
tests/      pytest suite
```

## Judging criteria

- **Innovation** — a support agent whose by-product is product intelligence, not a chatbot.
- **Use of Hindsight memory** — observations, mental models, conflict resolution, isolation.
- **Technical implementation** — layered architecture, async-safe pipeline, error handling.
- **User experience** — a 60-second amnesia-vs-memory story with a live dashboard.
- **Real-world impact** — fewer repeated tickets, earlier warning of regressions.

## Content

Articles, social posts and the demo video live under `content/`.
