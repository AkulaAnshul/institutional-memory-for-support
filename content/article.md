# My Support Agent Noticed a Regression We'd Already Marked Fixed

Halfway through replaying a quarter of support tickets, the agent flagged something
our own tracker had missed: an export bug we closed in v2.3 was back in v2.4. It
didn't "guess" this from the ticket in front of it. It remembered closing the bug,
noticed the same symptom resurfacing, and told the customer it was a known issue —
while quietly contradicting a belief it had stored weeks earlier.

I built the agent around [Hindsight](https://hindsight.vectorize.io/), an agent-memory
system designed for agents that *learn* rather than simply store chat history. This
post is about the design decisions that made that moment possible, and the two
mistakes I made before I got them right.

## What the system does

It's a support copilot for a B2B SaaS team. It does two jobs with one memory layer:

1. **Per-customer memory** — when a ticket arrives, the agent already knows the
   account's environment, plan, and the tickets they've sent before.
2. **Institutional memory** — across *all* customers, it consolidates recurring
   symptoms into evidence-backed observations, and exposes them as a live
   "Emerging Issues" report.

The architecture is two Hindsight **banks** plus a thin agent:

```
new ticket ─► agent ──recall──► cust:<id>      (environment, history, preferences)
                 │             org:<org>       (recurring issues, workarounds)
                 ├─ draft reply
                 └─ retain ──►  both banks ──► background consolidation ──► observations
                                                                        └─► mental models
```

Hindsight isolates banks strictly, so the customer bank gives me clean
personalisation and the org bank gives me cross-customer patterns. Tickets are
written to both, with a stable `document_id` and tags for product, version, module,
issue type and customer.

## The rule nobody tells you about memory agents

My first version retained the ticket and then immediately recalled it to build the
reply. The replies looked fine in a demo and subtly wrong in practice, because
Hindsight — like most serious memory systems — extracts facts and consolidates
observations **asynchronously**. If you retain and recall in the same turn, you're
racing the extractor.

The fix is boring and changes everything: **write at the end of the turn, read at the
start of the next one.** Retaining looks like this:

```python
client.retain(
    bank_id=ORG_BANK_ID,
    content=ticket_content,                 # rich, un-summarised ticket + resolution
    context=f"support ticket in {ticket.module} for {ticket.product} v{ticket.version}",
    timestamp=ticket.created_at,            # enables temporal retrieval
    document_id=f"ticket:{ticket.id}",      # stable id = update, never duplicate
    tags=["scope:org", f"product:{ticket.product}", f"version:{ticket.version}"],
)
```

Two details matter. First, I pass the *richest* representation and let Hindsight's
LLM extract facts, entities and time — pre-summarising throws away the temporal and
causal links you'll want later. Second, `timestamp` and a stable `document_id` are
not optional if you care about "what changed since March" or idempotent re-ingest.

## Tags, not metadata, are the isolation boundary

I initially filtered memories using `metadata`. That silently does nothing: Hindsight
returns metadata with results but does **not** filter on it. The isolation primitive
is `tags`. Getting this wrong in a multi-tenant support tool is a data-leak bug, not
a performance bug.

```python
resp = client.recall(
    bank_id=ORG_BANK_ID,
    query="export times out for large datasets",
    types=["observation", "world"],   # high-level beliefs first
    tags=["scope:org", f"product:{product}"],
    tags_match="all",                 # never the default "any" for tenant data
    include_source_facts=True,        # evidence for the observation
)
```

That `tags_match="all"` is intentional. The default (`"any"`) will happily return
untagged memories — which, in a shared bank, means everyone's.

## Making memory the star: observations and mental models

The part that earns its keep is consolidation. As tickets accumulate, Hindsight
merges overlapping facts into **observations** — deduplicated, evidence-backed
beliefs with a proof count, *refined rather than overwritten* when new evidence
arrives. That's what let the agent say "this is a known issue, here's the
workaround" instead of "sorry, I'm not sure".

I also define two **mental models** — standing questions whose answers Hindsight
writes and keeps fresh in the background:

```python
client.create_mental_model(
    bank_id=ORG_BANK_ID,
    id="emerging-issues",
    name="Emerging Issues",
    source_query="What recurring defects are showing up across customers, how many "
                 "are affected, and is each trend rising or falling?",
    tags=["scope:org"],
    trigger={"refresh_after_consolidation": True, "mode": "delta"},
)
```

Reading one is a **database read** — no retrieval, no LLM call — so the dashboard is
instant and cheap. That's the difference between "an agent that remembers" and "a
system that knows things."

## The conflict is the feature

The demo dataset tells one story on purpose. In Q1, a CSV-export timeout spreads
across customers and is recorded as "believed fixed in v2.3." In Q2, after v2.4, the
same export fails again — this time as an immediate 504. Because observations keep
their history instead of silently overwriting, the agent can hold both facts:
*this was fixed, and now it's back.* A stateless bot, or a naive vector store, would
just re-learn the same bug every time with no notion that it had ever been closed.

Better still, nobody has to go looking for this. The agent can run a periodic audit — a
`reflect` over the whole bank with a structured output schema — and raise the regression
itself: *"Data Export Performance, believed fixed in v2.3, now affecting v2.4, high
confidence."* That's the line between a tool that answers when asked and a system that
watches your back.

## Results

Running the same 51-ticket stream with and without memory makes the gap obvious:

| Metric | Amnesia | Memory (Hindsight) |
|---|---|---|
| Replies grounded in memory | 0% | 100% |
| Avg memories cited per reply | 0.00 | 7.27 |

"Grounded" means the reply cites a specific observation or prior interaction — not
that it *sounds* confident. The paragraph-level quality difference is even starker
than the table: the memory replies name the customer's environment and the exact
workaround, while the amnesia replies ask them to clear their cache.

## Five things I'd tell anyone building this

1. **Separate personal and institutional memory into different banks.** They answer
   different questions and take different tags.
2. **Retain after the turn, recall before the next.** Async extraction will bite you.
3. **Use tags for isolation; metadata is not a filter.** `tags_match="all"` for
   tenant data.
4. **Never pre-summarise what you retain.** The extractor is better at finding the
   entities, times and causal links than you are at guessing them.
5. **Make the write path the hero.** Observations and mental models are where an
   agent stops being a chatbot and starts being infrastructure.

If you want to see the moving parts, the [Hindsight GitHub repo](https://github.com/vectorize-io/hindsight)
and the [documentation](https://hindsight.vectorize.io/) are the fastest way in. For
the theory behind *why* agent memory is a different problem from RAG, Vectorize's
write-up on [agent memory](https://vectorize.io/what-is-agent-memory) is worth your
time. And if you're building a support agent, start by giving it somewhere to put
what it learns — you'll be surprised how quickly it starts noticing things you
missed.
