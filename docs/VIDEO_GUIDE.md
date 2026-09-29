# 🎬 Video Guide — step by step (no technical background needed)

This guide takes you from zero to a finished, uploaded YouTube video, even if you have
never run a project like this before. Do every step in order. Copy-paste commands exactly
as written. Total time: about 30–45 minutes (most of it waiting/recording).

> If anything goes wrong, jump to **Troubleshooting** at the bottom. Nothing here can
> "break" your computer.

---

## Part 0 — What you need before starting

- A **laptop** (Mac or Windows) with internet.
- **Two secret keys** that I will send you separately (do **not** put them in an email
  that others can see). They look like this:
  - `GROQ_API_KEY` → starts with `gsk_`
  - `HINDSIGHT_API_KEY` → starts with `hsk_`
- A **microphone** (your laptop's built-in mic is fine).
- A quiet room.

You do **not** need a GitHub account or any paid software.

---

## Part 1 — Download the project (3 min)

1. Open your browser and go to:
   **https://github.com/AkulaAnshul/institutional-memory-for-support**
2. Click the green **`< > Code`** button (top right of the file list).
3. Click **Download ZIP**.
4. Find the downloaded file (usually in **Downloads**), right-click it → **Extract All**
   (Windows) or double-click it (Mac). You now have a folder called
   `institutional-memory-for-support`.

> Move this folder to your **Desktop** so it is easy to find.

---

## Part 2 — Install Python (one time, ~5 min)

The easiest option is **Anaconda**.

1. Go to **https://www.anaconda.com/download** and download the **Anaconda Distribution**.
2. Run the installer and click **Next / Agree / Install** with the **default** options.
3. When it finishes, you will have:
   - **Windows:** a program called **“Anaconda Prompt”** in your Start menu.
   - **Mac:** a **Terminal** app (the built-in one is fine).

That's it. You do not need to open it yet.

---

## Part 3 — Add your secret keys (3 min)

1. Open the project folder `institutional-memory-for-support`.
2. Find the file named **`.env.example`**.
   - **Windows:** if you don't see the `.example`, click **View → Show → File name
     extensions** in the folder window first.
3. **Copy** that file and **paste** it in the same folder.
4. **Rename the copy** from `env.example.txt`/`.env.example` to exactly:
   **`.env`**  (no “.example” at the end).
5. Open `.env` with **Notepad** (Windows) or **TextEdit** (Mac).
6. Replace it with exactly this, pasting **your** two keys where shown, then **Save**:

```
GROQ_API_KEY=gsk_PASTE_YOUR_GROQ_KEY_HERE
GROQ_MODEL=openai/gpt-oss-120b
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=hsk_PASTE_YOUR_HINDSIGHT_KEY_HERE
ORG_BANK_ID=org:acme
```

> ⚠️ Keep the keys secret. Never show this file on camera.

---

## Part 4 — Set it up (one command, ~3 min)

**Windows**
1. Open the project folder.
2. **Double-click** the file **`setup.bat`**.
3. A black window opens and installs things. Wait until it says **“Setup complete.”**
4. Press any key to close it.

**Mac**
1. Open **Terminal** (press `Cmd` + `Space`, type `Terminal`, press Enter).
2. In Terminal, type `cd ` (with a space), then **drag the project folder** onto the
   Terminal window and press **Enter**. (This puts you "inside" the folder.)
3. Copy-paste this line and press **Enter**:
   ```
   ./setup.sh
   ```
4. Wait until it says **“Setup complete.”**

---

## Part 5 — Start the app (~1 min)

**Windows**
- **Double-click** the file **`run.bat`**. A black window opens. **Leave it open.**

**Mac**
- In the same Terminal window, copy-paste and press **Enter**:
  ```
  ./run.sh
  ```
- Wait for a line that says **“Uvicorn running on http://127.0.0.1:8000”**. **Leave the
  Terminal open.**

Now open your browser and go to:

### 👉 http://127.0.0.1:8000

You should see a dark dashboard called **“Institutional Memory · Support Console”**.
If you see it, **you're ready to record.** 🎉

> If the page is empty or the side panel says “Not built yet”, see Troubleshooting.

---

## Part 6 — Rehearse once (5 min, recommended)

Before recording, do a full dry run of the steps below **without recording**. This makes
the real take smooth. Don't worry if the first AI reply takes 10–20 seconds — that's
normal, keep talking.

---

## Part 7 — Get ready to record (5 min)

1. **Close distractions:** quit Slack/WhatsApp, close other browser tabs, and turn on
   **Do Not Disturb** so no notifications pop up.
2. Make the browser **full screen** (press `F11` on Windows, or the green button on Mac).
3. Pick a recorder:
   - **Mac (easiest):** press `Cmd` + `Shift` + `5` → choose **Record Entire Screen** →
     set the microphone → click **Record**.
   - **Windows (easiest):** press `Windows` + `G` → click the **Record** button. Make
     sure the **mic** is enabled in the capture settings.
   - **Either (nicer):** free **OBS Studio** (https://obsproject.com). Set
     **Output Resolution 1920×1080**, **30 FPS**, and add your microphone. If OBS feels
     confusing, use the built-in options above.
4. Do a **5-second test**, stop, and play it back to check your voice is audible.

---

## Part 8 — The exact script to follow (about 3 minutes)

Do exactly this, in order. The words in **quotes** are what to say (say it naturally,
don't read robotically).

### Scene 1 — Intro (0:00 – 0:20)
- Start recording.
- You are looking at the dashboard.
- Say:
  > “Hi, I'm **[your name]**. This is an AI support assistant that actually remembers
  > every customer, and gets smarter with every ticket it handles. Let me show you.”

### Scene 2 — Show the problem (0:20 – 0:50)
- At the top right, click the toggle so it says **Amnesia**.
- In the left **Ticket queue**, click the first ticket (the subject line).
- Click the big **“Draft reply”** button.
- Wait for the reply to appear. Read the top line silently.
- Say:
  > “This is how most support AI works — it has no memory. It only sees this one message.
  > So it gives a generic answer, like ‘please clear your cache.’ It doesn't know who
  > this customer is, or that we've seen this problem many times before.”

### Scene 3 — Same ticket, with memory (0:50 – 1:40)
- Click the toggle back to **Memory**.
- With the **same ticket still selected**, click **“Draft reply”** again.
- Wait for the new reply. Point at the reply and the list below it.
- Say:
  > “Same ticket, but now memory is on. Before it writes anything, it checks two memories:
  > this customer's history, and every ticket we've ever handled. Look at the result — it
  > names their setup, it tells them this is a **known issue**, gives the exact
  > workaround, and even references their **previous ticket** from months ago. That's not
  > a longer prompt. That's memory.”

### Scene 4 — Watch it learn live (1:40 – 2:20)
- Click **“Play stream”** at the top right (it will replay a few tickets automatically
  and draft replies on its own).
- Let it run for ~4–5 tickets, then click **“Stop stream”**.
- Point at the **Learning curve** panel on the right.
- Say:
  > “Watch the learning curve. As new tickets come in, the agent keeps grounding its
  > answers in memory. And this panel — **Emerging issues** — is built from all those
  > tickets by itself, so we can see which problems are trending this week.”

### Scene 5 — The surprise: it catches a regression (2:20 – 2:50)
- In the **Regression alerts** panel, click **“Run audit”**.
- Wait a few seconds. Two red alert cards appear.
- Say:
  > “Here's my favourite part. Nobody asked it a question. On its own, it reviewed
  > everything it knows and found a bug we marked **fixed** months ago that has quietly
  > come **back**. It tells us exactly where it was fixed, where it returned, and how
  > confident it is. That's the difference between a chatbot and a system that learns.”

### Scene 6 — Wrap up (2:50 – 3:10)
- Say:
  > “So: a support agent that remembers every customer, gets smarter with every ticket,
  > and warns the team when a fix doesn't stick. Thanks for watching.”
- **Stop the recording.**

> Keep it under 5 minutes. If you fumble a sentence, just keep going — authenticity beats
> perfection.

---

## Part 9 — Upload to YouTube (~10 min)

1. Find your recording file (Desktop or Movies folder). If asked to save, keep it as
   **MP4**.
2. Go to **https://youtube.com** and sign in.
3. Click the **camera icon with a `+`** (top right) → **Upload video**.
4. Select your file. While it uploads, fill in:
   - **Title** (pick one):
     - `A support agent that remembers every customer`
     - `I gave my support agent a company-wide memory`
     - `Watch a support agent get smarter with every ticket`
   - **Description** (copy-paste this and replace nothing):
     ```
     An AI support assistant with persistent memory, built on Hindsight (agent memory
     that learns). It remembers each customer, consolidates recurring tickets into a
     company-wide brain, and proactively flags issues that were fixed but came back.

     Code: https://github.com/AkulaAnshul/institutional-memory-for-support
     Hindsight: https://hindsight.vectorize.io/
     ```
   - **Visibility:** **Public**.
5. Click **Next → Next → Publish**.
6. Copy the video link (starts with `https://youtu.be/...`) and send it to the team.

> **Do not** mention any hackathon/competition in the title or description.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `./run.sh: Permission denied` | Type `chmod +x run.sh setup.sh` in Terminal, press Enter, then `./run.sh` again. |
| Browser page is blank / “can't connect” | The black window/Terminal must stay **open**. Make sure it says “Uvicorn running”, then refresh the page. |
| The right panel says “Not built yet” | The memory needs to be filled once. Click **“Seed”** at the top right and **wait about 10 minutes**. Only do this once. |
| A reply shows `Groq daily token limit reached` | The free AI quota for today is used up. Record tomorrow, or just demo the panels that don't need it (Emerging issues, Regression audit). |
| `Hindsight` error / red status dot | Your `.env` keys are wrong or missing. Re-check Part 3. |
| Windows blocks `setup.bat` | Right-click → **Run as administrator**, or open **Anaconda Prompt** and run `setup.bat`. |
| Everything is too small on screen | In the browser press `Ctrl` + `+` (Windows) or `Cmd` + `+` (Mac) a couple of times. |

## Golden rules
1. **Never** show the `.env` file or the keys on camera.
2. **Don't click “Seed”** unless the panel is empty (it's slow).
3. If you see an error toast, just keep going or stop and re-record that scene.
4. Aim for **under 5 minutes**; shorter is better.
