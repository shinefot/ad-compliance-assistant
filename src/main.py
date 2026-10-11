"""
main.py — STEP 4. Ask a question about one aircraft.

Run:  python -m src.main DEMO-001 "Which ADs apply and what is due?"

If sign-off is needed, the program pauses and asks you (the engineer) to approve.
The final report is printed and saved to reports/<aircraft>_<run_id>.md
"""
import json
import sys
import uuid

from langgraph.types import Command

from . import config
from .extract import load_records
from .graph import build_graph
from .index import load_index, make_retriever
from .llm import get_llm


def load_fleet() -> dict[str, dict]:
    return {a["id"]: a for a in json.loads(config.FLEET_FILE.read_text(encoding="utf-8"))}


def ask_engineer(payload: dict) -> dict:
    print("\n" + "=" * 70)
    print("PAUSED: " + payload["message"])
    for v in payload["negative_or_uncertain_verdicts"]:
        print(f"  - AD {v['ad_number']}: {v['verdict']} -> {v['reason']}")
    if payload["unresolved_review_flags"]:
        print("\nUnresolved safety-review flags:")
        for f in payload["unresolved_review_flags"]:
            print(f"  ! {f}")
    print("=" * 70)
    name = input("Your name (reviewer): ").strip() or "anonymous"
    ok = input("Approve these verdicts? (y/n): ").strip().lower() == "y"
    note = input("Note (optional): ").strip()
    return {"approved": ok, "reviewer": name, "note": note}


def run(aircraft_id: str, question: str) -> str:
    fleet = load_fleet()
    if aircraft_id not in fleet:
        raise SystemExit(f"Unknown aircraft '{aircraft_id}'. Options: {', '.join(fleet)}")
    records = load_records()
    if not records:
        raise SystemExit("No extracted ADs. Run `python -m src.extract` first.")

    retrieve = make_retriever(load_index())
    graph = build_graph(records, get_llm("analyst"), get_llm("reviewer"), retrieve)

    run_id = uuid.uuid4().hex[:8]
    cfg = {"configurable": {"thread_id": run_id}}  # thread_id lets the graph resume after a pause
    state = graph.invoke({"run_id": run_id, "question": question, "aircraft": fleet[aircraft_id]}, cfg)

    while "__interrupt__" in state:  # the graph paused at human_gate
        decision = ask_engineer(state["__interrupt__"][0].value)
        state = graph.invoke(Command(resume=decision), cfg)

    report = state["final_report"]
    out_dir = config.ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{aircraft_id}_{run_id}.md"
    path.write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"Saved to {path.relative_to(config.ROOT)}  |  audit trail: audit_log.jsonl (run_id {run_id})")
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit('Usage: python -m src.main DEMO-001 "Which ADs apply and what is due?"')
    run(sys.argv[1], sys.argv[2])
