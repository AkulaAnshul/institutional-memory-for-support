# Problem Statement & Our Solution

## 1. The exact Problem Statement

**Title:** *AI Agents That Learn Using Hindsight*

> In this hackathon, you will build AI-powered applications using **Hindsight**, a memory
> system developed by Vectorize that allows AI agents to remember, recall, and improve
> over time.
>
> Instead of building AI that forgets conversations, your project should demonstrate
> **persistent memory and learning from past interactions**.

**Required technology (verbatim):**
> All teams must build their projects using **Hindsight**.

**Important rules (verbatim):**
> All teams must ALSO share their project based on challenges from the official content
> guide. […] Your project must clearly demonstrate **how Hindsight memory is used in your
> solution**.

**Judging criteria (verbatim weights):**

| Criteria | Weight | What judges look for |
|---|---|---|
| Innovation | 30% | A fresh take on a real problem; beyond obvious chatbot territory |
| Use of Hindsight Memory | 25% | Is memory central to the value proposition? Does the agent improve over time? |
| Technical Implementation | 20% | Clean, well-architected, functional; handles edge cases |
| User Experience | 15% | Intuitive; the demo tells a compelling story |
| Real-world Impact | 10% | Could it solve a real problem? Is there a path to adoption? |

> **Note on the idea list.** The PDF's "Customer Support Agent", "Sales Agent", etc. appear
> under a section titled *"Project Ideas That Look Real"* that ends with *"Browse this
> repository for more inspiration."* They are **starting points, not the Problem
> Statement**. The PS is the Hindsight-memory theme above; every team still has to invent
> the actual solution on top of it.

---

## 2. Our solution

**Project:** *Institutional Memory for Support*
**One line:** an institutional memory that turns a company's entire ticket stream into an
evolving, evidence-backed model of its product — and catches the day a "fixed" bug comes
back.

**Positioning:** *The support agent is the interface. The memory is the product.*
We start from one of the brief's suggested categories (Customer Support + User Feedback
Synthesizer), but the thing we actually built is a **reusable institutional-memory layer**
whose first interface is support. That reframing is deliberate: it is what makes the
project a fresh take rather than "another support bot".

### The real problem we target
**Institutional knowledge loss.** Every company forgets what it fixed, why, and whether it
stayed fixed. Symptoms:
- Support agents make customers repeat themselves on every ticket.
- Recurring bugs are re-discovered from scratch dozens of times.
- A bug that was "fixed" regresses silently because nothing remembers the fix.

### Why this is a fresh take (Innovation, 30%)

| The obvious chatbot | This project |
|---|---|
| Remembers one conversation | Remembers across **months, customers, and the whole company** |
| Answers only when asked | **Proactively audits** memory and raises regression alerts |
| Stores chat history | **Consolidates** recurring tickets into evidence-backed observations |
| Forgets the pattern | **Preserves the history** of an issue being reported, "fixed", and reported again |
| A bolt-on feature | A reusable **institutional-memory layer**; support is the first interface |

The headline capability is the **regression audit**: the agent reflects over everything it
knows and surfaces issues the company believed were fixed but that are being reported
again — before a human notices.

### Our approach (the loop)

```
ticket arrives
   │
   ├─ recall(customer bank)                    → who is this customer? environment, history
   ├─ recall(org bank, types=[observation])    → is this a known issue? recorded workaround?
   ├─ read mental model "Emerging Issues"      → is it trending? (database read, no LLM call)
   │
   ├─ agent drafts a grounded reply (cites memories)
   │
   └─ AFTER replying: retain to BOTH banks
            └─ background consolidation → observations update → mental models refresh
```

**Two Hindsight banks, because Hindsight isolates banks strictly:**
1. **Customer bank** (`cust:<id>`) — one per customer: environment, plan, past tickets,
   fixes that worked, communication preferences.
2. **Org bank** (`org:acme`) — shared, company-wide: every ticket, tagged by `product`,
   `version`, `module`, `issue-type`, `customer`.

**The key design rule:** *recall before the turn, retain after it.* Hindsight extracts
facts and consolidates observations **asynchronously**, so retaining and recalling in the
same turn races the extractor.

### How we use Hindsight (Use of Hindsight Memory, 25%)

| Hindsight feature | Where | Why it matters |
|---|---|---|
| `retain()` with `timestamp`, `context`, tags | `app/memory.py` | rich, un-summarised turns become factual memories |
| `recall()` (semantic + keyword + graph + temporal) | `app/tools.py` | customer history and known-issue search |
| **Observations** (evidence-backed, refined not overwritten) | org bank | recurring tickets collapse into one belief with a proof count |
| **Mental models** (read with no LLM call) | `Emerging Issues`, `Known Issues` | instant dashboard, refreshed after consolidation |
| **Conflict resolution** | demo storyline | an issue "fixed in v2.3" is reported again in v2.4 |
| **`reflect` + structured output** | regression audit | surfaces fixed-then-back issues as alerts |
| Missions, directives, disposition | `app/config.py` | what to extract, hard rules, empathy tuning |
| Tags for isolation | both banks | no cross-customer leakage (`tags_match="all"`) |
| Memory Defense | org bank | PII/secrets redacted before the shared bank |

### Stack (aligned to the brief)
- **Memory:** Hindsight (Cloud, API 0.10.1) — the mandated technology.
- **LLM:** Groq **`openai/gpt-oss-120b`** with function calling. (The brief's recommended
  `qwen/qwen3-32b` was shut down on 2026-07-17; this is its documented replacement.)
- **Backend:** Python 3.11 + FastAPI.
- **Frontend:** hand-written HTML/CSS/JS served by FastAPI — no build step.
- **Data:** 15 customers, 69 historical tickets seeded into memory, a 51-ticket live demo
  stream, and a knowledge base.

### What the demo shows
1. **Before / after.** The same regression ticket in *Amnesia* mode (generic "clear your
   cache") vs *Memory* mode (names the customer's environment, the known issue, the
   workaround, and their own prior ticket).
2. **Learning curve.** The live stream replays a quarter; the console charts the share of
   replies grounded in memory as tickets accumulate.
3. **Proactive regression audit.** With no question asked, the agent reports:
   *"Data Export Performance, believed fixed in v2.3, now affecting v2.4, high confidence."*

### Measured evidence
| Metric | Amnesia | Memory (Hindsight) |
|---|---|---|
| Replies grounded in memory | 0% | 100% |
| Avg memories cited per reply | 0.00 | 7–43 (run-dependent) |

- 8-ticket cloud run → `results/eval_report.md`
- 51-ticket offline run → `results/eval_report_offline.md`

### Mapping back to the judging criteria
- **Innovation (30%)** — an institutional-memory product whose by-product is product
  intelligence and proactive regression detection, not a chatbot.
- **Use of Hindsight (25%)** — observations, mental models, conflict resolution, isolation,
  directives, structured `reflect`.
- **Technical (20%)** — layered architecture, async-safe pipeline, rate-limit handling,
  18 passing tests.
- **UX (15%)** — a 60-second amnesia-vs-memory story plus a live learning curve and alerts.
- **Real-world impact (10%)** — fewer repeated tickets, faster resolutions, early regression
  warning; a memory layer any support/product team could adopt.

### One-liner for the judges
> *Most teams build a support bot that remembers conversations. We built the memory layer
> as the product: an institutional brain that turns thousands of tickets into an evolving
> model of product health — and catches the day a "fixed" bug silently comes back.*
