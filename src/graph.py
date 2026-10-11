"""
graph.py — STEP 3. The multi-agent workflow, built with LangGraph.

LangGraph models a workflow as a graph:
  - STATE: a shared dictionary every step can read and update (class ADState below).
  - NODES: Python functions, one per step/agent.
  - EDGES: arrows saying which node runs next. A CONDITIONAL edge picks the next
    node based on the state (that's how we build the retry loop).

Our flow:

  applicability_checker -> analyst -> safety_reviewer --(problems & retries left)--> analyst
                                              |
                                              v
                                        human_gate  (pauses for sign-off when needed)
                                              |
                                              v
                                          finalize

The LLMs and the retriever are passed IN to build_graph() ("dependency injection").
That lets the tests run the whole graph with fake LLMs, no API key needed.
"""
import re
from typing import Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from . import config
from .applicability import check_all
from .audit import log_event
from .schema import ADRecord, Aircraft, ReviewResult, Verdict

CITATION_RE = re.compile(r"\[AD\s+([A-Za-z0-9\-]+)\s+p\.\s?(\d+)\]")
NEEDS_REVIEW = {Verdict.DOES_NOT_APPLY.value, Verdict.CANNOT_DETERMINE.value}


class ADState(TypedDict, total=False):
    run_id: str
    question: str
    aircraft: dict
    verdicts: list[dict]           # [{ad_number, verdict, reason}]
    evidence: dict[str, list]      # {ad_number: [{ad_number, page, text}]}
    analysis: str
    review_flags: list[str]
    retries: int
    human_decision: Optional[dict]
    final_report: str


def message_text(msg) -> str:
    """Newer models can return a list of content blocks instead of one string; keep only the text."""
    content = msg.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)

def find_citations(text: str) -> set[tuple[str, int]]:
    return {(ad, int(p)) for ad, p in CITATION_RE.findall(text)}


def check_citations_exist(analysis: str, evidence: dict[str, list]) -> list[str]:
    """Pure-Python check: every citation must point to a page we actually retrieved."""
    allowed = {(c["ad_number"], c["page"]) for chunks in evidence.values() for c in chunks}
    flags = []
    for ad, page in sorted(find_citations(analysis)):
        if (ad, page) not in allowed:
            flags.append(f"Citation [AD {ad} p.{page}] does not match any retrieved source text.")
    if evidence and not find_citations(analysis):
        flags.append("The analysis contains no citations at all.")
    return flags


def build_graph(records: list[ADRecord], analyst_llm, reviewer_llm, retrieve, checkpointer=None):
    analyst_prompt = config.load_prompt("analyst")
    reviewer_prompt = config.load_prompt("reviewer")
    model = config.REASON_MODEL

    # ---------- Node 1: deterministic applicability (no AI) ----------
    def applicability_checker(state: ADState) -> dict:
        aircraft = Aircraft(**state["aircraft"])
        results = [r.model_dump(mode="json") for r in check_all(records, aircraft)]
        log_event(state["run_id"], "applicability_checker",
                  {"aircraft": aircraft.model_dump(), "verdicts": results, "model": "none (rule-based)"})
        return {"verdicts": results, "retries": 0, "review_flags": []}

    # ---------- Node 2: Analyst (RAG + LLM) ----------
    def analyst(state: ADState) -> dict:
        to_explain = [v for v in state["verdicts"] if v["verdict"] != Verdict.DOES_NOT_APPLY.value]
        to_explain = to_explain[: config.MAX_ADS_TO_ANALYZE]

        evidence = state.get("evidence") or {}
        if not evidence:  # retrieve once; retries reuse the same evidence
            for v in to_explain:
                evidence[v["ad_number"]] = retrieve(
                    f"{state['question']} applicability required actions compliance time", v["ad_number"])

        if not to_explain:
            analysis = "No AD in the current dataset was found to apply to this aircraft. All negative verdicts require engineer sign-off."
        else:
            verdict_lines = "\n".join(f"- AD {v['ad_number']}: {v['verdict']} ({v['reason']})" for v in to_explain)
            source_blocks = "\n\n".join(
                f"[AD {c['ad_number']} p.{c['page']}]\n{c['text']}"
                for chunks in evidence.values() for c in chunks)
            feedback = ""
            if state.get("review_flags"):
                feedback = ("\n\nYour previous draft was rejected by the safety reviewer for these reasons. "
                            "Fix every one:\n- " + "\n- ".join(state["review_flags"]))
            human_msg = (f"Aircraft: {state['aircraft']}\nQuestion: {state['question']}\n\n"
                         f"Applicability verdicts (decided by rules, do not change them):\n{verdict_lines}\n\n"
                         f"SOURCE TEXT:\n{source_blocks}{feedback}")
            analysis = message_text(analyst_llm.invoke([("system", analyst_prompt), ("human", human_msg)]))

        retries = state.get("retries", 0) + (1 if state.get("review_flags") else 0)
        log_event(state["run_id"], "analyst", {
            "model": model, "prompt_version": config.PROMPT_VERSIONS["analyst"], "attempt": retries + 1,
            "sources": sorted({(c["ad_number"], c["page"]) for ch in evidence.values() for c in ch}),
            "analysis": analysis})
        return {"analysis": analysis, "evidence": evidence, "retries": retries}

    # ---------- Node 3: Safety Reviewer (rules + LLM) ----------
    def safety_reviewer(state: ADState) -> dict:
        flags = check_citations_exist(state["analysis"], state.get("evidence", {}))
        if state.get("evidence"):
            review: ReviewResult = reviewer_llm.with_structured_output(ReviewResult).invoke(
                [("system", reviewer_prompt), ("human", f"ANALYSIS TO REVIEW:\n\n{state['analysis']}")])
            flags += [f"Uncited claim: {c}" for c in review.uncited_claims]
            flags += [f"Unsafe statement: {s}" for s in review.unsafe_statements]
        log_event(state["run_id"], "safety_reviewer", {
            "model": model, "prompt_version": config.PROMPT_VERSIONS["reviewer"], "flags": flags})
        return {"review_flags": flags}

    def route_after_review(state: ADState) -> str:
        if state["review_flags"] and state.get("retries", 0) < config.MAX_RETRIES:
            return "analyst"      # send it back for a rewrite
        return "human_gate"

    # ---------- Node 4: Human-in-the-loop ----------
    def human_gate(state: ADState) -> dict:
        negatives = [v for v in state["verdicts"] if v["verdict"] in NEEDS_REVIEW]
        unresolved = state.get("review_flags", [])
        if not negatives and not unresolved:
            return {"human_decision": {"required": False}}
        # interrupt() PAUSES the whole graph here and hands this payload to the person.
        # The graph's memory (checkpointer) remembers where it stopped.
        decision = interrupt({
            "message": "Engineer sign-off required before this report is final.",
            "negative_or_uncertain_verdicts": negatives,
            "unresolved_review_flags": unresolved,
        })
        decision = {"required": True, **decision}
        log_event(state["run_id"], "human_gate", {"decision": decision,
                                                  "items_reviewed": len(negatives) + len(unresolved)})
        return {"human_decision": decision}

    # ---------- Node 5: Final report ----------
    def finalize(state: ADState) -> dict:
        rows = "\n".join(f"| {v['ad_number']} | {v['verdict']} | {v['reason']} |" for v in state["verdicts"])
        d = state.get("human_decision") or {}
        if not d.get("required"):
            signoff = "Not required (no negative or uncertain verdicts, no unresolved flags)."
        else:
            status = "APPROVED" if d.get("approved") else "REJECTED, do not rely on this report"
            signoff = f"{status} by {d.get('reviewer', 'unknown')}. Note: {d.get('note') or '-'}"
        flags = state.get("review_flags") or []
        flag_text = ("\n".join(f"- {f}" for f in flags)) if flags else "None"
        report = (f"# AD applicability report: {state['aircraft']['id']}\n\n"
                  f"Aircraft: {state['aircraft']}\nQuestion: {state['question']}\n\n"
                  f"## Verdicts (rule-based)\n| AD | Verdict | Reason |\n|---|---|---|\n{rows}\n\n"
                  f"## Analysis\n{state['analysis']}\n\n## Unresolved review flags\n{flag_text}\n\n"
                  f"## Engineer sign-off\n{signoff}\n\n"
                  "_Decision-support only. Not an airworthiness determination._\n")
        log_event(state["run_id"], "finalize", {"signoff": signoff})
        return {"final_report": report}

    g = StateGraph(ADState)
    g.add_node("applicability_checker", applicability_checker)
    g.add_node("analyst", analyst)
    g.add_node("safety_reviewer", safety_reviewer)
    g.add_node("human_gate", human_gate)
    g.add_node("finalize", finalize)
    g.add_edge(START, "applicability_checker")
    g.add_edge("applicability_checker", "analyst")
    g.add_edge("analyst", "safety_reviewer")
    g.add_conditional_edges("safety_reviewer", route_after_review, ["analyst", "human_gate"])
    g.add_edge("human_gate", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())
