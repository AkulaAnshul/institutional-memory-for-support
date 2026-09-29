# Run & Showcase Guide

Everything needed to go from a fresh `git clone` to a live demo, in two paths:

- **Option A — 60-second offline demo:** no accounts, no API keys. Sees the whole product.
- **Option B — Full setup:** real Hindsight memory + a Groq LLM. This is what judges should see.

---

## 0. Prerequisites

- **Git**
- **Python 3.11+** (a project-local env is created below; nothing global is touched)
- Optional: **conda** (recommended) or just `python3 -m venv`
- Optional: **Docker** (only if self-hosting Hindsight instead of using Hindsight Cloud)

---

## Option A — 60-second offline demo (no keys)

This uses an in-process memory stand-in and a deterministic agent, but it runs the
**full pipeline** (recall, drafting, consolidation, mental models, regression audit).

```bash
git clone https://github.com/AkulaAnshul/institutional-memory-for-support.git
cd institutional-memory-for-support

# environment (conda)
conda create --prefix ./.conda python=3.11 -y
./.conda/bin/pip install -r requirements.txt

# or environment (venv, if you don't use conda)
# python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt

# run the whole flow from the command line
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/seed.py
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/demo.py
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./.conda/bin/python scripts/regressions.py
```

Or run the UI offline:

```bash
USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1 ./run.sh
# open http://127.0.0.1:8000
```

---

## Option B — Full setup (Hindsight + Groq)

### Step 1 — Clone and create the environment

```bash
git clone https://github.com/AkulaAnshul/institutional-memory-for-support.git
cd institutional-memory-for-support

# conda (recommended)
conda create --prefix ./.conda python=3.11 -y
./.conda/bin/pip install -r requirements.txt

# or venv
# python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
```

### Step 2 — Get a Groq API key (free)

1. Go to <https://console.groq.com/keys>
2. Create an API key (starts with `gsk_`).

> The brief suggests `qwen/qwen3-32b`, but Groq shut that model down on 2026-07-17.
> This project uses **`openai/gpt-oss-120b`**, the documented replacement with tool calling.

### Step 3 — Get Hindsight (pick one)

**3a. Hindsight Cloud (easiest)**
1. Sign up at <https://ui.hindsight.vectorize.io/signup>
2. **After** registering, add promo code **`MEMHACK99`** in the billing section for $50 credits.
3. Create an API key (starts with `hsk_`).

**3b. Self-hosted Hindsight (Docker, no cloud account)**

```bash
export GROQ_API_KEY=gsk_your_key
docker run -it --pull always --name hindsight --restart unless-stopped \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq \
  -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

### Step 4 — Create `.env`

```bash
cp .env.example .env
```

Then edit `.env`:

**For Hindsight Cloud:**
```dotenv
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=openai/gpt-oss-120b
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=hsk_xxxxxxxxxxxxxxxxxxxx
ORG_BANK_ID=org:acme
```

**For self-hosted:**
```dotenv
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=openai/gpt-oss-120b
HINDSIGHT_BASE_URL=http://localhost:8888
HINDSIGHT_API_KEY=
ORG_BANK_ID=org:acme
```

### Step 5 — Seed the historical tickets

```bash
./.conda/bin/python scripts/seed.py
```

This ingests 69 historical tickets + a knowledge base into 15 customer banks and the
org bank, waits for Hindsight to consolidate, and builds the `Emerging Issues` and
`Known Issues` mental models. **This takes a few minutes** because Hindsight extracts
and consolidates asynchronously.

### Step 6 — Start the console

```bash
./run.sh
# open http://127.0.0.1:8000
```

---

## Showcase script (what to click and say)

1. **Start with the problem.** In the UI, keep the mode on **Amnesia**. Pick a ticket,
   click **Draft reply**. → generic "*please clear your cache*", 0 memories cited.
   > "This is what most support AI does: it only sees this one message."

2. **Switch to Memory.** Toggle **Memory**, click **Draft reply** again.
   → it names the customer's environment, the **known issue**, the **workaround**, and a
   **prior ticket**; the citations panel fills in.
   > "Same ticket. Memory on. This isn't a longer prompt — it's memory."

3. **Show the learning.** Click **Play live stream**. Tickets stream in and get drafted;
   the **Learning curve** chart rises as more replies are grounded in memory.

4. **Show the institutional brain.** Point at the **Emerging issues** panel.
   > "That report is a Hindsight mental model — reading it is a plain database read, no LLM call."

5. **Proactive audit.** Click **Run regression audit**.
   > "Nobody asked a question. The agent reflected over every ticket and found an issue
   > we marked fixed in v2.3 that's back in v2.4 — high confidence."

6. **Close with the metric.** Show `results/eval_report.md`:
   > "Same tickets: 0% of replies grounded in memory without it, 100% with it."

---

## Command-line showcase (no UI)

```bash
./.conda/bin/python scripts/demo.py          # one ticket, amnesia vs memory, side by side
./.conda/bin/python scripts/regressions.py   # proactive regression audit
SKIP_SEED=1 EVAL_LIMIT=8 ./.conda/bin/python scripts/eval.py   # before/after metrics
```

Useful flags: `SKIP_SEED=1` (data already seeded), `EVAL_LIMIT=N`, `AMNESIA_SAMPLE=N`,
`USE_FAKE_MEMORY=1`, `USE_FAKE_AGENT=1`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/api/config` shows `service_error` or drafting says "GROQ_API_KEY ..." | `.env` missing/invalid; copy from `.env.example` and fill it in. The `.env` must be in the repo root. |
| `Hindsight ERROR` / connection refused | Wrong `HINDSIGHT_BASE_URL`, or the self-hosted server isn't running (`docker ps`). For Cloud, check the `hsk_` key. |
| `Groq daily token limit reached` | Free tier is 200k tokens/day. Wait for the daily reset, use `EVAL_LIMIT`, or run offline (`USE_FAKE_MEMORY=1 USE_FAKE_AGENT=1`). |
| `seed.py` finishes but the dashboard is empty | Consolidation is asynchronous; wait a minute and refresh, or re-run `scripts/seed.py`. |
| `./run.sh: Permission denied` | `chmod +x run.sh` |
| Port 8000 in use | `PORT=8010 ./run.sh` |
| Mind the data | Data is synthetic and committed to `data/`; regenerate with `scripts/generate_data.py`. |

---

## What to look at in the code

- `app/memory.py` — the Hindsight wrapper (banks, retain/recall/reflect, mental models, regression audit).
- `app/tools.py` — the agent's memory tools.
- `app/agent.py` — the Groq tool-calling loop with rate-limit handling.
- `app/service.py` — the async-safe pipeline: recall first, retain after the turn.
- `frontend/` — the console (no build step).
- `docs/PROBLEM_AND_SOLUTION.md` — the exact problem statement and our solution.
