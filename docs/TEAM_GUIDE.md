# 👋 Team Guide — start here

Everything the team needs to produce the **video**, the **LinkedIn post**, the
**article**, and the rest of the deliverables. No technical background required.

## The project in one sentence

An AI support assistant that **remembers every customer** and grows a **company-wide
brain** from the ticket stream — it consolidates recurring issues, and proactively flags
bugs that were marked “fixed” but came back.

**Repository:** https://github.com/AkulaAnshul/institutional-memory-for-support

---

## 📦 What to send to the team

1. **The GitHub link** (above) — they download it from there.
2. **The two secret keys**, privately (not in a group chat): `GROQ_API_KEY` and
   `HINDSIGHT_API_KEY`. They go into the `.env` file (see the Video Guide, Part 3).
3. **These guides:**
   - `docs/VIDEO_GUIDE.md` — record and upload the video.
   - `docs/LINKEDIN_GUIDE.md` — post on LinkedIn.
   - `content/article.md` — the article draft.
   - `content/linkedin.md` — the LinkedIn post text.
   - `content/video-script.md` — the spoken script (also inside the Video Guide).

> ⚠️ Never send or commit the `.env` file itself. Keep keys private.

---

## ✅ Deliverables checklist

| Deliverable | Who | Where | Guide |
|---|---|---|---|
| GitHub repo (public, clean) | ✅ done | link above | — |
| Explanation of Hindsight usage | ✅ done | `README.md`, `docs/PROBLEM_AND_SOLUTION.md` | — |
| Demo **video** (2–5 min, public on YouTube) | ⬜ team | YouTube | `docs/VIDEO_GUIDE.md` |
| **Article** (public, linkable) | ⬜ team | Medium / Dev.to / Hashnode / Substack | below |
| **LinkedIn post** | ⬜ each member | LinkedIn | `docs/LINKEDIN_GUIDE.md` |
| Reddit link post | ⬜ optional | r/llmdevs · r/sideproject · r/aiagents · r/aimemory | below |

---

## 📝 Publishing the article (10 min, no technical skill)

1. Open `content/article.md` in the project folder. Select all the text and **copy** it.
2. Create a free account on one of:
   - **Medium** → https://medium.com/new-story (easiest)
   - **Dev.to** → https://dev.to/new
   - **Hashnode** → https://hashnode.com
3. Click **New story / Write**, then **paste** the article.
4. Check that the **links** survived the paste. The article must contain these three
   links (they are already in the text):
   - `https://github.com/vectorize-io/hindsight`
   - `https://hindsight.vectorize.io/`
   - `https://vectorize.io/what-is-agent-memory`
5. Add a **cover image** if the platform asks (a screenshot of the console is perfect —
   the team can take one while recording the video).
6. Click **Publish** and choose **Public**.
7. Copy the public URL — you'll paste it into the LinkedIn **comment** (see the LinkedIn
   Guide).

> **Rule:** the article must **not** mention any hackathon/competition, in the title or
> the body. The current draft is already clean — don't add it.

---

## 🎬 Recording the video (summary — full steps in `docs/VIDEO_GUIDE.md`)

1. Download the project, install Anaconda, put keys in `.env`, run `setup.bat` / `./setup.sh`.
2. Start with `run.bat` / `./run.sh`, open **http://127.0.0.1:8000**.
3. Record your screen + voice following the 6 scenes in the Video Guide (about 3 minutes).
4. Upload to **YouTube as Public**, title like
   *“A support agent that remembers every customer”*.
5. Send the YouTube link to the team.

---

## 🧭 60-second demo cheat-sheet (in case someone asks)

1. Toggle **Amnesia** → pick a ticket → **Draft reply** → generic answer, 0 memories.
2. Toggle **Memory** → **Draft reply** → cites the customer, the known issue, the workaround.
3. **Play stream** → the **Learning curve** rises; **Emerging issues** updates by itself.
4. **Run audit** in “Regression alerts” → it reports a bug that was fixed and came back.
5. The payoff: **0% → 100%** of replies grounded in memory.

---

## ❓FAQ

**Does it need the internet?** Yes — the memory and the AI model are online services.

**Do I need to “Seed” anything?** Only if the right-hand “Emerging issues” panel is
empty. If it already shows content, **do not** click Seed (it takes ~10 minutes).

**Which files are the “content” deliverables?** Everything in the `content/` folder, plus
the recorded video and the published links.

**Where is the Hindsight explanation?** `README.md` (table: “How Hindsight is used”) and
`docs/PROBLEM_AND_SOLUTION.md`.
