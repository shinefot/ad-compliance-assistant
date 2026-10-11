# AD Compliance Assistant

A multi-agent AI assistant that helps aircraft fleet engineers work out which **Airworthiness Directives (ADs)** apply to each aircraft, explains what each one requires with page-level citations, and never finalizes a "does not apply" verdict without an engineer's sign-off.

> Decision-support only. Not an airworthiness determination tool.

## The problem

Airworthiness Directives are legally binding safety orders: inspect or replace a part, on specific aircraft, by a deadline. They come from the regulator of the aircraft's state of design (the **FAA** for Boeing, **EASA** for Airbus), and national authorities such as the UAE's **GCAA** require operators to comply. A mixed-fleet operator therefore tracks directives from several authorities across hundreds of aircraft, and deciding applicability is slow, manual, and high-stakes.

The costly error is the **false negative**: concluding an AD doesn't apply when it does. This project is designed around preventing that.

## Demo

_Add your 2-minute screen recording link here._

## Architecture

```
Question + aircraft profile
        │
        ▼
[1] Applicability Checker   rule-based Python → APPLIES / DOES_NOT_APPLY / CANNOT_DETERMINE
        │
        ▼
[2] Analyst                 RAG (LlamaIndex) + Claude    , cites [AD number p.N]
        │
        ▼
[3] Safety Reviewer         citation check (code) + safety review (Claude)
        │
        ├── problems found and retries left ──► back to Analyst (max 2)
        ▼
[4] Human gate              LangGraph interrupt: engineer signs off negative/uncertain verdicts
        │
        ▼
[5] Final report + audit log (every step: model, prompt version, sources, timestamp)
```

**Offline step (run once):** an extraction agent reads each AD PDF and fills a strict Pydantic schema (`ADRecord`): models, serial ranges, engines, compliance time, superseded ADs.

## Design for safety-critical use

1. **Applicability is decided by code, not by the LLM.** The LLM extracts facts once; deterministic Python checks serial ranges and models. Exact, repeatable, and covered by unit tests, including boundary serial numbers.
2. **Three verdicts, not two.** Many ADs define affected aircraft by reference to a service bulletin the system cannot see. These return `CANNOT_DETERMINE` rather than a guess.
3. **Every ambiguity leans toward the safe side.** Family names and engine prefixes can only widen applicability, never narrow it.
4. **Humans sign off every negative.** `DOES_NOT_APPLY` and `CANNOT_DETERMINE` verdicts, and any unresolved reviewer flags, pause the workflow for an engineer's approval.
5. **Citations are verified, not trusted.** The reviewer checks in code that every `[AD … p.N]` citation points to a page that was actually retrieved, and an LLM reviewer flags uncited or overconfident statements. Failures trigger a rewrite.
6. **Full audit trail.** `audit_log.jsonl` records each step's model, prompt version, sources, output, and the engineer's decision.

## Evaluation

Ground truth: hand-checked applicability for aircraft/AD pairs (`evals/test_cases.json`). Headline metric is false negatives.

Ground truth: 10 aircraft/AD cases labeled from the source PDFs by an independent AI reviewer, with page-level evidence notes in `evals/test_cases.json`; 2 spot-checked by hand. Headline metric: false negatives.

| Extractor prompt | False negatives | Other mismatches | Correct |
|---|---|---|---|
| v2 | 2 | 4 | 4/10 |
| v3 | 0 | 0 | 10/10 |

What the evaluation caught:
- **Part vs aircraft serial numbers.** v2 read a table of fire-panel *part* serial numbers as *aircraft* serial numbers, wrongly excluding two aircraft from a fire-protection AD. v3 restricts serial numbers to the Applicability paragraph.
- **Proposed rules and fabricated identifiers.** 5 of 10 FAA documents turned out to be proposed rules (NPRMs) with no AD number. v1 extracted docket numbers; v2's strict format rule pushed the model to *invent* plausible AD numbers. v3 labels them as NPRMs, and the rules treat them as not in force.
- **Regression risk.** Each prompt fix was re-evaluated, because v2 fixed one problem while silently creating another.

## Tech stack

| Component | Tool | Purpose |
|---|---|---|
| Orchestration | LangGraph | Multi-agent graph, retry loop, checkpointing, human-in-the-loop interrupt |
| Retrieval | LlamaIndex (built-in vector store) | Chunking, metadata-filtered vector search, saved locally |
| Embeddings | bge-small-en-v1.5 (fastembed) | Free, runs locally |
| LLM | Claude (Haiku for extraction, Sonnet for analysis and review) | Structured output, reasoning |
| Validation | Pydantic | Strict schemas for extraction and review |
| Testing | pytest | Unit tests for rules and citation checks |

## Data handling

Uses only public-domain regulatory documents: FAA ADs (Federal Register), EASA ADs (EASA public AD site), and 14 CFR Part 39. No maintenance manuals, proprietary service bulletins, or export-controlled (ITAR/EAR) technical data. Fleet data is fictional (`DEMO-xxx`).
Swapped Chroma for LlamaIndex’s built-in vector store after Windows Application Control blocked an unsigned native dependency.

## Limitations

- Cannot read referenced service bulletins, so those ADs are escalated as `CANNOT_DETERMINE`.
- Small dataset (one aircraft type per authority).
- Does not track compliance status or recurring inspection intervals.
- Extraction quality depends on the LLM; measured in the evaluation.

## Run it

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # then add your Anthropic API key to .env

python -m src.extract              # PDFs -> data/extracted.json
python -m src.index                # build the search index
pytest                             # unit tests
python -m src.main DEMO-001 "Which ADs apply and what is due?"
python -m evals.run_evals --draft  # then fill in expected verdicts
python -m evals.run_evals
```

## Project layout

```
src/schema.py         data shapes (ADRecord, Verdict, ...)
src/extract.py        PDF -> structured ADRecord via Claude
src/applicability.py  rule-based applicability (no AI)
src/index.py          LlamaIndex search index
src/graph.py          LangGraph multi-agent workflow
src/audit.py          audit trail
src/main.py           command-line entry point
prompts/              versioned prompts
evals/                evaluation cases and results
tests/                unit tests
```
