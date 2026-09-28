# Demo video — script (≈3 minutes)

**Format:** screen recording with voiceover over the running console
(`./run.sh` → http://127.0.0.1:8000). Record at 1080p, terminal/editor font bumped up.
Keep the narration conversational — don't read it word for word.

## 0:00–0:30 — Intro

**On screen:** the console, ticket queue on the left, Emerging Issues on the right.

> "Hi, I'm [name]. I built a support agent that remembers every customer, and grows a
> company-wide memory from the tickets it handles. The memory layer is Hindsight. Let
> me show you why memory is the whole point."

## 0:30–1:00 — The problem (no memory)

**On screen:** toggle **Amnesia**, open a regression ticket, click **Draft reply**.

> "This is the same agent with memory switched off — what most support bots do. It
> only sees the ticket text. So it tells the customer to clear their cache. It doesn't
> know who they are, and it doesn't know this bug has hit forty other accounts."

**Show:** the reply is generic; the citations panel reads 0.

## 1:00–2:30 — The demo (memory on)

**Step 1 — recall.** Toggle **Memory**, re-draft the ticket.

> "Same ticket, memory on. Before it writes anything, the agent calls Hindsight:
> this customer's environment, their past tickets, and whether this symptom is a known
> issue. Watch the citations fill in. It recognises the account and the pattern."

**Step 2 — the payoff.** Scroll the draft.

> "Now it says: this is a known export issue on v2.4, here's the workaround, and we've
> seen it before on your account. That's not a longer prompt. It's memory."

**Step 3 — the conflict.** Point at the Emerging Issues panel.

> "Here's my favourite part. In Q1 this export bug was marked fixed. When v2.4 shipped
> it came back as a 504. Because observations keep their history instead of overwriting,
> the agent holds both facts — fixed, and now regressed."

**Step 4 — live.** Click **Play live stream**.

> "I'll replay the quarter. Tickets stream in, the agent drafts each one, and the
> Emerging Issues report updates — that report is a Hindsight mental model, so reading
> it is a plain database read, no LLM call."

**Step 5 — proactive.** Click **Run regression audit**.

> "And here's the part that isn't a support bot: on its own, the agent reflects over
> everything it knows and raises the regression — 'Data Export, fixed in v2.3, back in
> v2.4, high confidence.' Nobody asked it that question."

## 2:30–3:00 — Takeaway

**On screen:** the eval table (`results/eval_report.md`).

> "Same fifty-one tickets, both modes. Zero percent of replies grounded in memory
> without it, a hundred percent with it. What surprised me most: I had to retain
> *after* replying, never before, because Hindsight extracts memories asynchronously.
> Respect the write path, and the agent starts noticing things you missed."

## Five video title options

1. I gave my support agent a company-wide memory
2. My agent caught a regression we'd marked fixed
3. Adding long-term memory to a support agent with Hindsight
4. Watch a support agent get smarter with every ticket
5. From "clear your cache" to "known issue" — memory in action
