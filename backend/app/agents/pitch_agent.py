"""Pitch Specialist — evaluates value proposition, differentiation, impact, pitch."""
from __future__ import annotations

from typing import Tuple

from app.agents.common import idea_context
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import PitchAnalysis

SYSTEM = (
    "You are the Pitch Specialist. Evaluate the SAME idea's value proposition, differentiation, "
    "impact, and pitch structure. If any claim exceeds what is technically or temporally feasible, "
    "flag it in 'cross_domain_flags'. Be concise; short lists only. Return PitchAnalysis JSON."
)


def analyze_pitch(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[PitchAnalysis, CallUsage]:
    idea = state["selected_idea"]
    user = (
        f"{idea_context(idea)}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return PitchAnalysis JSON."
    )
    return client.generate(
        system=SYSTEM, user=user, schema=PitchAnalysis, max_output_tokens=500
    )
