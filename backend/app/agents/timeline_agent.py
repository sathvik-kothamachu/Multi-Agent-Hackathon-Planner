"""Timeline Scheduler — judges whether the SAME idea fits the time limit.

Consumes the Tech agent's recommended stack + complexity (structured state hand-
off, not an independent prompt) and produces an ordered, chronological schedule
plus an honest estimate vs. the available hours. Time risk is computed
deterministically from the estimate so the UI warning never depends on the LLM.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.agents.common import idea_context, joined, team_context
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import TimelineAnalysis

SYSTEM = (
    "You are the Timeline Scheduler. Decide whether the SAME idea can realistically be built within "
    "the time limit, using the provided tech stack. Return TimelineAnalysis JSON with: estimated_hours "
    "(number), feasible (bool), a 'schedule' list of ordered items {{task, technology, duration, "
    "dependency, expected_output}}, milestones, critical_dependencies, risks, critique. If scope or a "
    "claim does not fit, note it in 'cross_domain_flags'. Be concise. Return TimelineAnalysis JSON."
)


def _num(text: str) -> float:
    m = re.search(r"\d+(\.\d+)?", str(text))
    return float(m.group()) if m else 0.0


def analyze_timeline(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[TimelineAnalysis, CallUsage]:
    idea = state["selected_idea"]
    tech = state.get("tech_analysis")
    available = float(state.get("time_limit_hours", 24))
    stack = joined(tech.recommended_stack) if tech else ""
    complexity = tech.complexity if tech else "medium"
    user = (
        f"{idea_context(idea)}\n"
        f"Time limit (hours): {available}\n"
        f"Recommended stack: {stack or 'unspecified'}\n"
        f"Complexity: {complexity}\n"
        f"Team: {team_context(state.get('team_profile'))}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return TimelineAnalysis JSON."
    )
    analysis, usage = client.generate(
        system=SYSTEM, user=user, schema=TimelineAnalysis, max_output_tokens=650
    )
    # Deterministic estimate + risk so the UI warning never depends on the LLM.
    analysis.available_hours = available
    if not analysis.estimated_hours:
        analysis.estimated_hours = sum(_num(t.duration) for t in analysis.schedule) or sum(
            _num(m.duration) for m in analysis.milestones
        )
    est = analysis.estimated_hours
    if est and available and est > available:
        analysis.feasible = False
        analysis.time_risk = (
            f"Estimated {est:g}h exceeds the {available:g}h limit by {est - available:g}h — "
            "cut scope or simplify the hardest component."
        )
    return analysis, usage
