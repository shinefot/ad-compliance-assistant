# Build Guide: AD Compliance Assistant (for today)

This is your single reference. Follow the steps in order. Each step says **what to type**, **what you should see**, and **what it does**. If what you see doesn't match, stop and check the Troubleshooting table at the end (or ask Claude, pasting the exact error).

Rough timetable for today:

| Time | Steps |
|---|---|
| 13:00–13:45 | 1–4: set up the project, run the tests |
| 13:45–14:30 | 5–6: add PDFs, extract data with AI |
| 14:30–15:15 | 7–8: tune the fleet, build the search index |
| 15:15–16:15 | 9: run the assistant, understand the output |
| 16:15–17:30 | 10–11: evaluation |
| 17:30–18:30 | 12: publish to GitHub |
| 18:30–19:30 | 13: demo video and README polish |

**Terminal tip:** every command below is typed into the VS Code terminal (Terminal → New Terminal) and run with Enter. Before any command, make sure `(.venv)` shows at the start of the line. If it doesn't, activate it again:
- Windows: `.venv\Scripts\activate`
- Mac: `source .venv/bin/activate`

On Mac, if `python` doesn't work, use `python3` instead.

---

## Step 1: Put the project in place

1. Unzip `ad-compliance-assistant.zip`. You get a folder `ad-compliance-assistant`.
2. In VS Code: **File → Open Folder** → choose that folder.
3. Open a terminal and create + activate the virtual environment:

```
python -m venv .venv
.venv\Scripts\activate          (Windows)
source .venv/bin/activate       (Mac)
```

**You should see:** `(.venv)` at the start of the terminal line.

If you already made a `.venv` earlier in a different folder, that's fine; just make a new one here.

---

## Step 2: Install the libraries

```
pip install -r requirements.txt
```

**What it does:** `requirements.txt` lists every library the project needs. pip downloads and installs them into your `.venv` box. Takes 3–6 minutes.

**You should see:** lots of output, ending with `Successfully installed ...`. Yellow warnings are fine. Red `ERROR` lines are not.

---

## Step 3: Add your API key safely

```
copy .env.example .env          (Windows)
cp .env.example .env            (Mac)
```

Open `.env` in VS Code (left sidebar) and replace `your-key-here` with your real Claude API key. Save (Ctrl+S / Cmd+S).

**What it does:** the code reads your key from `.env`. The file `.gitignore` lists `.env`, so Git will never upload it to GitHub. `.env.example` (no real key) is what gets shared.

---

## Step 4: Run the unit tests

```
pytest
```

**You should see:** `14 passed`.

**What it does:** runs `tests/test_applicability.py`, small automatic checks that the applicability rules work. For example, it confirms a serial number exactly on the edge of a range counts as inside it, and that a fake citation gets caught. No AI or internet used. If you change the rules later, re-run this to make sure you didn't break anything.

Open `tests/test_applicability.py` and read two or three tests. Each one is: make a fake AD, make a fake aircraft, assert the verdict.

---

## Step 5: Add the AD PDFs

Put your downloaded PDFs here:
- FAA (Boeing 737) PDFs → `data/faa/`
- EASA (Airbus A320) PDFs → `data/easa/`
- Optional: 14 CFR Part 39 as a PDF (from ecfr.gov, "Print/PDF") → `data/regs/`

Any recent ADs work. 15 FAA + 8 EASA is plenty.

---

## Step 6: Extract structured data with AI

```
python -m src.extract
```

**What it does** (`src/extract.py`): for each PDF it reads the text page by page, sends it to Claude Haiku with the instructions in `prompts/extractor_v1.md`, and forces Claude to answer by filling in the `ADExtraction` form defined in `src/schema.py`. Results go into `data/extracted.json`. Cost: well under $1 for ~25 PDFs.

**You should see** one line per file:
```
  ok    faa/2025-12345.pdf -> AD 2025-14-07 | models: 737-600, 737-700, 737-800, ...
```

If some say `FAIL`, re-run the same command; it skips files that already worked.

**Now check the AI's work (important, 15 minutes).** Open `data/extracted.json`. Pick 5 ADs, open their PDFs, find the **Applicability** paragraph (usually "(c) Applicability"), and compare:
- Are all the aircraft models there?
- If the AD says "as identified in Boeing Alert Service Bulletin...", is `applicability_by_reference` filled in?
- Is `compliance_time` right?

Write down any mistakes. You'll use them in Step 11.

You'll likely notice that many Boeing ADs define affected aircraft by service bulletin. Those will correctly come out as `CANNOT_DETERMINE`, which is the honest answer and a good talking point.

---

## Step 7: Make the demo fleet interesting

Open `data/fleet.json`. The three aircraft are fictional. Their serial numbers (`msn`) were made up before we knew your ADs, so adjust them so the demo shows all three verdicts:

1. In `extracted.json`, find a 737 AD that has `serial_ranges` filled in (if any).
2. Set DEMO-001's `msn` to a number **inside** that range, and DEMO-002's `msn` to one **outside** it.
3. Make sure DEMO-003's model matches the A320 variant named in your EASA ADs (e.g. `A320-214`, `A320-232`). Same for engines if the ADs name them.

If none of your ADs have serial ranges, that's fine; leave the file as is.

---

## Step 8: Build the search index

```
python -m src.index
```

**What it does** (`src/index.py`): splits every AD into ~500-word chunks, tags each chunk with its AD number and page, turns each chunk into an embedding (384 numbers representing its meaning) using a free model that runs on your laptop, and saves them in a local folder `index_store/`. The first run downloads the embedding model (~130 MB).

**You should see:** `Indexed N pages as M chunks into index_store/`

If you add PDFs later: run Step 6, then this step again.

---

## Step 9: Ask your assistant a question

```
python -m src.main DEMO-001 "Which ADs apply and what is due?"
```

**What happens** (`src/graph.py`), in order:

1. **Applicability Checker** runs the Python rules on every AD. No AI.
2. **Analyst** searches the index for text from each applicable or uncertain AD and asks Claude Sonnet to explain it, citing `[AD number p.N]` after every fact.
3. **Safety Reviewer** checks that every citation points to a page that was actually retrieved, and asks Claude to flag uncited or overconfident statements. If it finds problems, the Analyst rewrites (up to 2 times).
4. **Human gate:** if any verdict is `DOES_NOT_APPLY` or `CANNOT_DETERMINE`, the program **pauses** and shows them to you. Type your name, `y` to approve, and an optional note.
5. **Final report** is printed and saved in `reports/`.

Cost: a few cents per question.

**Then look at the audit trail.** Open `audit_log.jsonl`. Each line is one step: which model, which prompt version, which pages were used, what it produced, and your sign-off. This is the "AI governance" piece.

Try:
```
python -m src.main DEMO-003 "What inspections are required?"
python -m src.main DEMO-002 "Which ADs apply?"
```
Then try answering `n` at the sign-off and see how the report changes.

---

## Step 10: Create your evaluation set

```
python -m evals.run_evals --draft
```

This creates `evals/test_cases.json` with up to 15 aircraft/AD pairs, each with `"expected": "TODO"` and which PDF pages to read.

For each case, open the PDF, read the Applicability section, compare with the aircraft in `fleet.json`, and replace `TODO` with exactly one of:
- `APPLIES`
- `DOES_NOT_APPLY`
- `CANNOT_DETERMINE` (applicability depends on a document you don't have)

Use the `note` field to record anything tricky. **Do this honestly, from the PDF, not from what the system said.** Your answers are the ground truth. This takes ~45 minutes and is the most valuable part of the project for interviews.

---

## Step 11: Score the system

```
python -m evals.run_evals
```

**You should see** a table: FALSE NEGATIVE, false positive, escalated (safe), correct. Saved to `evals/results.md`.

- **FALSE NEGATIVE** = system said "doesn't apply" but it does. The dangerous one.
- **escalated (safe)** = system said "can't determine" when it does apply. Safe, just less helpful.

**Improve and compare (optional but impressive):** if you found extraction mistakes:
1. Copy `prompts/extractor_v1.md` to `prompts/extractor_v2.md` and add a rule that fixes the mistake.
2. In `.env`, add the line `EXTRACTOR_PROMPT=extractor_v2`
3. Rename `data/extracted.json` to `data/extracted_v1.json` (keeps the old results).
4. Re-run Step 6, Step 8, Step 11. Compare the two results tables in your README.

That before/after comparison is exactly how real AI teams work.

---

## Step 12: Publish to GitHub

1. Create a free account at github.com. Click **New repository**, name it `ad-compliance-assistant`, keep it **Public**, do **not** tick "Add a README" (you already have one). Click **Create**.
2. In the terminal:

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git init
git add .
git status
```

3. **Safety check:** read the `git status` list. `.env` must **not** appear. `index_store/` and `.venv/` must not appear. If `.env` appears, stop and ask for help.
4. Then:

```
git commit -m "AD Compliance Assistant: multi-agent RAG with human sign-off"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ad-compliance-assistant.git
git push -u origin main
```

A browser window will ask you to sign in to GitHub the first time. Refresh your GitHub page; your code is there.

**Later changes:** `git add .` → `git commit -m "what changed"` → `git push`

---

## Step 13: Demo video and README

1. Record a 2-minute screen capture (Windows: Win+Alt+R with Xbox Game Bar, or Clipchamp; Mac: Cmd+Shift+5). Show: the question, the agents running, the sign-off pause, the final report, and the audit log.
2. Upload it to YouTube (unlisted) or Loom, and paste the link under **Demo** in `README.md`.
3. Paste your `evals/results.md` table under **Evaluation** in the README.
4. Commit and push again.
5. Pin the repo on your GitHub profile.

---

## How to explain it in an interview (60 seconds)

"Airworthiness Directives are mandatory safety orders, and mixed-fleet operators, like many in the Gulf, track them across the FAA and EASA. I built a multi-agent assistant with LangGraph. An LLM extracts each AD into a strict schema once; after that, applicability is decided by deterministic code, because range checks shouldn't be left to a language model. An analyst agent uses RAG with LlamaIndex to explain each AD with page citations, and a reviewer agent verifies those citations against what was actually retrieved and forces rewrites. Any 'doesn't apply' or 'can't determine' verdict pauses for an engineer's sign-off, and every step is audit-logged. I evaluated it against hand-labelled cases and track false negatives as the headline metric, because a missed AD is the failure that matters."

## What each file does (one line each)

| File | Role |
|---|---|
| `src/schema.py` | Defines the "forms" (ADRecord, Verdict, ReviewResult) the AI must fill in |
| `src/config.py` | File paths, model names, prompt versions, read from `.env` |
| `src/pdf_utils.py` | Reads PDF text page by page |
| `src/extract.py` | AI extraction: PDF → ADRecord → `extracted.json` |
| `src/applicability.py` | The rules. No AI. Decides the three verdicts |
| `src/index.py` | Builds and searches the RAG index (LlamaIndex) |
| `src/graph.py` | The LangGraph workflow: agents, retry loop, human pause |
| `src/audit.py` | Writes the audit trail |
| `src/main.py` | The command you run; handles the sign-off prompt |
| `prompts/*.md` | Instructions for each AI role, versioned |
| `evals/run_evals.py` | Creates and scores the evaluation set |
| `tests/` | Automatic checks of the rules |

## Troubleshooting

| You see | Fix |
|---|---|
| `python is not recognized` (Windows) | Python wasn't added to PATH. Re-run the Python installer → Modify → tick "Add to environment variables". Or try `py` instead of `python`. |
| `running scripts is disabled` (Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| `ModuleNotFoundError: No module named 'src'` or `'langgraph'` | You're not in the project folder, or `(.venv)` isn't active. Activate and retry. |
| `authentication_error` / `invalid x-api-key` | Key in `.env` is wrong or has spaces/quotes. It should be `ANTHROPIC_API_KEY=sk-ant-...` with nothing else on the line. |
| `credit balance is too low` | Add credit at console.anthropic.com → Billing. |
| `model not found` / `not_found_error` | Model name changed. Set `EXTRACT_MODEL=` and `REASON_MODEL=` in `.env` to current names from docs.claude.com. |
| `No text found. The PDF may be a scanned image.` | Skip that PDF; download a different AD. |
| `No documents found` at Step 8 | Run Step 6 first. |
| Embedding model download fails | Check internet; retry. On a corporate network, try home Wi-Fi. |
| Everything is `DOES_NOT_APPLY` for DEMO-003 | Your EASA ADs name a different A320 variant. Fix `model` in `fleet.json` (Step 7). |
| `git push` rejected | You ticked "Add a README" on GitHub. Run `git pull origin main --allow-unrelated-histories`, then push again. |
