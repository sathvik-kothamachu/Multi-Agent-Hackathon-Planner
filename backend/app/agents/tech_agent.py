"""Tech Stack Architect — critiques the SAME idea for technical feasibility only."""
from __future__ import annotations

from typing import Tuple

from app.agents.common import idea_context
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import TechAnalysis

SYSTEM = (
    "You are the Tech Stack Architect. Critique the SAME idea for TECHNICAL feasibility only. "
    "Recommend a minimal stack and architecture that fit the time limit. If a requirement "
    "conflicts with the timeline or the pitch, note it in 'cross_domain_flags'. Be concise; "
    "use short lists, not prose. Return TechAnalysis JSON."
)


def analyze_tech(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[TechAnalysis, CallUsage]:
    idea = state["selected_idea"]
    user = (
        f"{idea_context(idea)}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return TechAnalysis JSON."
    )
    return client.generate(
        system=SYSTEM, user=user, schema=TechAnalysis, max_output_tokens=500
    )
