"""LangGraph node functions.

Each node has the signature (state, client, settings) and returns a PARTIAL state
dict that LangGraph merges. graph.py binds client/settings with functools.partial.

Flow: ideas -> human_review (interrupt) -> debate -> alignment
      -> (redebate loop, max N rounds) -> assemble -> persona -> END
"""
from __future__ import annotations

from typing import Dict

from langgraph.types import interrupt

from app.agents.common import append_usage
from app.agents.idea_agent import generate_ideas
from app.agents.persona_agent import adapt_persona
from app.agents.pitch_agent import analyze_pitch
from app.agents.tech_agent import analyze_tech
from app.agents.timeline_agent import analyze_timeline
from app.alignment.semantic_alignment import compute_alignment
from app.alignment.similarity import DRIFT
from app.blueprint.assemble import assemble_blueprint
from app.debate.arbiter import run_arbiter
from app.models.schemas import IdeaDraft
from app.workflow.routing import (
    MAX_ROUNDS_EXCEEDED,
    ROUTE_FINALIZE,
    ROUTE_REDEBATE,
    decide_route,
    is_max_rounds,
    next_agents,
)


# --------------------------------------------------------------------------- #
# Ideation + human-in-the-loop
# --------------------------------------------------------------------------- #
def ideas_node(state: dict, client, settings) -> Dict:
    ideas, usage = generate_ideas(state, client, settings)
    return {
        "candidate_ideas": ideas,
        "usage_log": append_usage(state, usage),
        # reset any prior debate artifacts so regenerate starts clean
        "tech_analysis": None,
        "timeline_analysis": None,
        "pitch_analysis": None,
        "conflicts": [],
        "revision_directives": [],
        "debate_round": 0,
    }


def human_review_node(state: dict, client, settings) -> Dict:
    """Pause for human review. Resumed with a decision dict:

    {"action": "select", "idea_id": "idea-2"}      -> pick a candidate
    {"action": "modify", "idea": {...}}            -> pick an edited idea
    {"action": "regenerate"}                       -> loop back to ideas
    """
    decision = interrupt(
        {
            "type": "human_review",
            "ideas": [i.model_dump() for i in state.get("candidate_ideas", [])],
        }
    ) or {}
    action = decision.get("action", "select")

    if action == "regenerate":
        return {"review_action": "regenerate"}

    ideas = state.get("candidate_ideas", [])
    if action == "modify" and decision.get("idea"):
        chosen = IdeaDraft.model_validate(decision["idea"])
        if not chosen.id:
            chosen.id = "idea-modified"
    else:
        idea_id = decision.get("idea_id")
        chosen = next((i for i in ideas if i.id == idea_id), ideas[0] if ideas else None)

    return {"review_action": "proceed", "selected_idea": chosen}


def route_after_review(state: dict) -> str:
    return "regenerate" if state.get("review_action") == "regenerate" else "proceed"


# --------------------------------------------------------------------------- #
# Debate (detect -> critique -> resolve -> converge)
# --------------------------------------------------------------------------- #
def debate_node(state: dict, client, settings) -> Dict:
    """Run the specialist agents + arbiter for one debate round.

    First round runs all three specialists. Re-debate rounds re-run ONLY the
    agents the arbiter asked to revise (token discipline); if the arbiter named
    none but we still drifted, all three re-run.
    """
    first_round = state.get("tech_analysis") is None
    to_revise = [] if first_round else next_agents(state.get("revision_directives", []))
    run_all = first_round or not to_revise
    directives = {d.agent: d.change for d in state.get("revision_directives", [])}

    updates: Dict = {}
    usages = []

    if run_all or "tech" in to_revise:
        ta, u = analyze_tech(state, client, settings, revision=directives.get("tech", ""))
        updates["tech_analysis"] = ta
        usages.append(u)
    if run_all or "timeline" in to_revise:
        tl, u = analyze_timeline(state, client, settings, revision=directives.get("timeline", ""))
        updates["timeline_analysis"] = tl
        usages.append(u)
    if run_all or "pitch" in to_revise:
        pt, u = analyze_pitch(state, client, settings, revision=directives.get("pitch", ""))
        updates["pitch_analysis"] = pt
        usages.append(u)

    # Arbiter sees the freshest analyses (existing state + this round's updates).
    merged = {**state, **updates}
    arb, ua = run_arbiter(merged, client, settings)
    usages.append(ua)

    updates["conflicts"] = arb.conflicts
    updates["revision_directives"] = arb.revision_directives
    updates["current_solution_text"] = arb.current_solution_text
    updates["debate_round"] = state.get("debate_round", 0) + 1
    updates["usage_log"] = append_usage(state, *usages)
    return updates


# --------------------------------------------------------------------------- #
# Alignment gate (pure math, no LLM)
# --------------------------------------------------------------------------- #
def alignment_node(state: dict, client, settings) -> Dict:
    round_no = state.get("debate_round", 1)
    solution_text = state.get("current_solution_text") or state["selected_idea"].solution
    result = compute_alignment(
        state["problem_statement"], solution_text, settings, debate_round=round_no
    )
    status = result.status
    # Controlled stop: if still drifting at the round cap, mark it explicitly.
    if status == DRIFT and is_max_rounds(round_no, settings.max_debate_rounds):
        status = MAX_ROUNDS_EXCEEDED

    history = list(state.get("alignment_history", []))
    history.append({"round": round_no, "score": result.alignment_score, "status": status})

    updates: Dict = {
        "alignment_score": result.alignment_score,
        "alignment_status": status,
        "alignment_history": history,
    }
    if state.get("initial_alignment") is None:
        updates["initial_alignment"] = result.alignment_score
    return updates


def route_after_alignment(state: dict, settings) -> str:
    route = decide_route(
        state.get("alignment_status", ""),
        state.get("debate_round", 1),
        settings.max_debate_rounds,
    )
    return "redebate" if route == ROUTE_REDEBATE else "finalize"


# --------------------------------------------------------------------------- #
# Finalization
# --------------------------------------------------------------------------- #
def assemble_node(state: dict, client, settings) -> Dict:
    return {"final_plan": assemble_blueprint(state)}


def persona_node(state: dict, client, settings) -> Dict:
    plan, usage = adapt_persona(state, client, settings)
    return {"persona_adapted_plan": plan, "usage_log": append_usage(state, usage)}
