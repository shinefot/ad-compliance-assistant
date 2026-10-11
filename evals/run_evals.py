"""
run_evals.py — STEP 5. Measures how often the system gets applicability right.

Two commands:

  python -m evals.run_evals --draft
      Creates evals/test_cases.json with aircraft/AD pairs and "expected": "TODO".
      YOU open each AD PDF (file and pages are listed), read its applicability
      section, and replace TODO with APPLIES, DOES_NOT_APPLY or CANNOT_DETERMINE.
      Your hand-checked answers are the "ground truth".

  python -m evals.run_evals
      Compares the system against your answers and writes evals/results.md.

Why the headline metric is FALSE NEGATIVES: the system said "does not apply"
when it actually does. In aviation that is a missed safety action. A false
positive (extra inspection) costs time; a false negative can cost an aircraft.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from src import config
from src.applicability import build_superseded_map, check
from src.extract import load_records
from src.schema import Aircraft

HERE = Path(__file__).parent
CASES_FILE = HERE / "test_cases.json"
RESULTS_FILE = HERE / "results.md"


def draft(n: int = 10) -> None:
    """Pick a balanced set of aircraft/AD pairs: every aircraft gets cases, and the
    most informative ADs (serial lists, by-reference, superseded) are included first."""
    if CASES_FILE.exists():
        raise SystemExit(f"{CASES_FILE.name} already exists; delete it first if you want a new draft.")
    records = load_records()
    sup = build_superseded_map(records)
    fleet = json.loads(config.FLEET_FILE.read_text(encoding="utf-8"))

    def interest(r) -> int:
        return (2 * bool(r.serial_ranges) + bool(r.applicability_by_reference)
                + bool(r.ad_number in sup or r.supersedes))

    per_aircraft = {}
    for idx, a in enumerate(fleet):
        is_airbus = a["model"].upper().startswith("A3")
        cands = [r for r in records if (r.issuing_authority == "EASA") == is_airbus]
        cands.sort(key=interest, reverse=True)
        if cands:  # keep the most informative AD first, rotate the rest so aircraft get different ADs
            rest = cands[1:]
            k = idx % len(rest) if rest else 0
            cands = [cands[0]] + rest[k:] + rest[:k]
        per_aircraft[a["id"]] = cands

    cases, round_no = [], 0
    while len(cases) < n and any(len(c) > round_no for c in per_aircraft.values()):
        for aid, cands in per_aircraft.items():
            if round_no < len(cands) and len(cases) < n:
                rec = cands[round_no]
                cases.append({"aircraft_id": aid, "ad_number": rec.ad_number, "expected": "TODO",
                              "read": f"data/{rec.source_file} pages {rec.source_pages}", "note": ""})
        round_no += 1

    CASES_FILE.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {CASES_FILE}. Fill in every 'expected' field by reading the AD.")


def evaluate() -> None:
    all_records = load_records()
    # Look cases up by SOURCE FILE, not AD number: a new prompt version may extract a
    # different AD number for the same document, and the test case must still find it.
    by_file = {r.source_file: r for r in all_records}
    sup = build_superseded_map(all_records)
    fleet = {a["id"]: Aircraft(**a) for a in json.loads(config.FLEET_FILE.read_text(encoding="utf-8"))}
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    todo = [c for c in cases if c["expected"] == "TODO"]
    if todo:
        raise SystemExit(f"{len(todo)} cases still say TODO. Fill them in first.")

    counts = Counter()
    rows = []
    for c in cases:
        source = c["read"].split(" pages")[0].removeprefix("data/")
        if source not in by_file:
            raise SystemExit(f"No extracted record for {source}. Re-run `python -m src.extract`.")
        rec = by_file[source]
        got = check(rec, fleet[c["aircraft_id"]], sup)
        exp, pred = c["expected"], got.verdict.value
        if exp == pred:
            outcome = "correct"
        elif exp == "APPLIES" and pred == "DOES_NOT_APPLY":
            outcome = "FALSE NEGATIVE"
        elif exp == "APPLIES" and pred == "CANNOT_DETERMINE":
            outcome = "escalated (safe)"
        elif exp == "DOES_NOT_APPLY" and pred == "APPLIES":
            outcome = "false positive"
        else:
            outcome = "other mismatch"
        counts[outcome] += 1
        rows.append(f"| {c['aircraft_id']} | {rec.ad_number} | {exp} | {pred} | {outcome} | {got.reason} |")

    total = len(cases)
    summary = (
        f"# Evaluation results\n\n"
        f"Prompt: {config.PROMPT_VERSIONS['extractor']} | Extraction model: {config.EXTRACT_MODEL} | Cases: {total}\n\n"
        f"| Metric | Count | Rate |\n|---|---|---|\n"
        + "\n".join(f"| {k} | {counts[k]} | {counts[k] / total:.0%} |"
                    for k in ["FALSE NEGATIVE", "false positive", "escalated (safe)", "other mismatch", "correct"])
        + "\n\n## Case details\n| Aircraft | AD | Expected | System | Outcome | System reason |\n"
          "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
    )
    RESULTS_FILE.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Saved to {RESULTS_FILE}")


if __name__ == "__main__":
    draft() if "--draft" in sys.argv else evaluate()
