"""Deterministic final-blueprint assembly (NO LLM).

Merges the converged specialist analyses into one Blueprint. Pure data
transformation — research requirement #7 forbids using an LLM for merges/counts.
"""
from __future__ import annotations

from app.blueprint.merge import dedupe, merge_lists
from app.debate.conflicts import count_conflicts
from app.models.schemas import Blueprint


def assemble_blueprint(state: dict) -> Blueprint:
    idea = state["selected_idea"]
    tech = state.get("tech_analysis")
    timeline = state.get("timeline_analysis")
    pitch = state.get("pitch_analysis")
    conflicts = state.get("conflicts", []) or []

    detected, resolved = count_conflicts(conflicts)
    rounds = state.get("debate_round", 1)
    if detected:
        debate_summary = (
            f"{detected} conflict(s) detected, {resolved} resolved over {rounds} debate round(s)."
        )
    else:
        debate_summary = f"No cross-domain conflicts detected over {rounds} debate round(s)."

    return Blueprint(
        problem_statement=state["problem_statement"],
        selected_idea=idea,
        target_users=idea.target_users or (pitch.target_user if pitch else ""),
        recommended_stack=dedupe(tech.recommended_stack if tech else []),
        architecture=dedupe(tech.architecture if tech else []),
        timeline=(timeline.milestones if timeline else []),
        dependencies=merge_lists(timeline.critical_dependencies if timeline else []),
        technical_risks=merge_lists(
            tech.technical_risks if tech else [],
            timeline.risks if timeline else [],
        ),
        value_proposition=(pitch.value_proposition if pitch else ""),
        differentiation=dedupe(pitch.differentiation if pitch else []),
        pitch_structure=(pitch.pitch_structure if pitch else []),
        alignment_score=state.get("alignment_score"),
        alignment_status=state.get("alignment_status", ""),
        debate_summary=debate_summary,
    )
