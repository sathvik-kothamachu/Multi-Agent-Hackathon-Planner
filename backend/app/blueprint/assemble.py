"""Deterministic final-blueprint assembly (NO LLM).

Merges the converged specialist analyses + team allocation + alignment report
into one complete Blueprint (22 documentation sections). Pure data
transformation — research requirement #7 forbids using an LLM for merges/counts.
MVP vs nice-to-have is split deterministically from the idea's core features.
"""
from __future__ import annotations

from typing import List

from app.blueprint.merge import dedupe, merge_lists
from app.debate.conflicts import count_conflicts
from app.models.schemas import Blueprint, MemberAllocation


def _split_mvp(features: List[str]) -> tuple[list[str], list[str]]:
    """First ~60% of features are MVP; the rest are nice-to-have."""
    feats = dedupe(features)
    if not feats:
        return [], []
    cut = max(1, round(len(feats) * 0.6))
    return feats[:cut], feats[cut:]


def _implementation_procedure(schedule, milestones) -> list[str]:
    if schedule:
        return [
            f"{i}. {s.task} ({s.duration}) using {s.technology} -> {s.expected_output}".strip()
            for i, s in enumerate(schedule, start=1)
        ]
    return [f"{i}. {m.name} ({m.duration})" for i, m in enumerate(milestones, start=1)]


def _risk_mitigation(risks: List[str]) -> list[str]:
    return [f"Mitigate '{r}' by scoping early and keeping a working fallback." for r in risks[:6]]


def _testing_plan(stack: List[str]) -> list[str]:
    plan = [
        "Manually test the core end-to-end flow before adding polish.",
        "Add unit tests for the main processing logic.",
        "Smoke-test the demo path immediately before presenting.",
    ]
    if any("react" in s.lower() for s in stack):
        plan.append("Verify the frontend builds cleanly (production build).")
    if any(s.lower() in ("fastapi", "flask", "django", "node", "express") for s in stack):
        plan.append("Check API endpoints return expected shapes.")
    return plan


def assemble_blueprint(state: dict) -> Blueprint:
    idea = state["selected_idea"]
    tech = state.get("tech_analysis")
    timeline = state.get("timeline_analysis")
    pitch = state.get("pitch_analysis")
    allocation: List[MemberAllocation] = state.get("team_allocation", []) or []
    report = state.get("alignment_report")
    conflicts = state.get("conflicts", []) or []

    detected, resolved = count_conflicts(conflicts)
    rounds = state.get("debate_round", 1)
    if detected:
        debate_summary = (
            f"{detected} conflict(s) detected, {resolved} resolved over {rounds} debate round(s)."
        )
    else:
        debate_summary = f"No cross-domain conflicts detected over {rounds} debate round(s)."

    stack = dedupe(tech.recommended_stack if tech else [])
    risks = merge_lists(
        tech.technical_risks if tech else [],
        timeline.risks if timeline else [],
    )
    mvp, nice = _split_mvp(idea.core_features)
    schedule = timeline.schedule if timeline else []
    milestones = timeline.milestones if timeline else []

    return Blueprint(
        project_name=idea.title,
        problem_statement=state["problem_statement"],
        hackathon_theme=state.get("hackathon_theme", "general"),
        aim=(pitch.aim if pitch and pitch.aim else idea.expected_impact),
        objectives=idea.objectives,
        selected_idea=idea,
        core_features=dedupe(idea.core_features),
        target_users=idea.target_users or (pitch.target_user if pitch else ""),
        expected_impact=idea.expected_impact or (pitch.impact if pitch else ""),
        architecture=dedupe(tech.architecture if tech else []),
        recommended_stack=stack,
        stack_details=(tech.stack_details if tech else []),
        team_allocation=allocation,
        timeline=milestones,
        schedule=schedule,
        implementation_procedure=_implementation_procedure(schedule, milestones),
        dependencies=merge_lists(timeline.critical_dependencies if timeline else []),
        technical_risks=risks,
        risk_mitigation=_risk_mitigation(risks),
        testing_plan=_testing_plan(stack),
        demo_flow=(pitch.demo_flow if pitch else []),
        value_proposition=(pitch.value_proposition if pitch else ""),
        differentiation=dedupe(pitch.differentiation if pitch else []),
        pitch_structure=(pitch.pitch_structure if pitch else []),
        future_scope=dedupe(pitch.future_scope if pitch else []),
        mvp_features=mvp,
        nice_to_have_features=nice,
        alignment_score=state.get("alignment_score"),
        alignment_status=state.get("alignment_status", ""),
        alignment_report=report,
        debate_summary=debate_summary,
    )
