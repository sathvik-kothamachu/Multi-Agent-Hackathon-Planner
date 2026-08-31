"""Timeline Scheduler — judges whether the SAME idea fits the time limit."""
from __future__ import annotations

from typing import Tuple

from app.agents.common import idea_context
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import TimelineAnalysis

SYSTEM = (
    "You are the Timeline Scheduler. Decide whether the SAME idea can realistically be built "
    "within the time limit. Produce ordered milestones with durations and dependencies, and set "
    "'feasible' honestly. If the scope or a technical/pitch claim does not fit the schedule, note "
    "it in 'cross_domain_flags'. Be concise. Return TimelineAnalysis JSON."
)


def analyze_timeline(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[TimelineAnalysis, CallUsage]:
    idea = state["selected_idea"]
    user = (
        f"{idea_context(idea)}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return TimelineAnalysis JSON."
    )
    return client.generate(
        system=SYSTEM, user=user, schema=TimelineAnalysis, max_output_tokens=500
    )
