"""Pitch Specialist — builds the full pitch for the SAME idea.

Consumes the selected idea (problem, objectives, features) plus the tech
analysis so the pitch never overpromises beyond what the build can show.
Produces a complete pitch: aim, value proposition, differentiation, impact, why
this solution, implementation approach, future scope, and a 2-minute demo flow.
"""
from __future__ import annotations

from typing import Tuple

from app.agents.common import idea_context, joined
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import PitchAnalysis

SYSTEM = (
    "You are the Pitch Specialist. Build the FULL pitch for the SAME idea, grounded in the given "
    "tech stack (never claim more than the build can show). Return PitchAnalysis JSON with: aim; "
    "value_proposition; target_user; differentiation (list); impact; why_this_solution; "
    "implementation_approach (list); future_scope (list); demo_flow (ordered 2-minute demo steps); "
    "pitch_structure (list). If a claim exceeds what is feasible, flag it in 'cross_domain_flags'. "
    "Be concise; short lists, not essays. Return PitchAnalysis JSON."
)


def analyze_pitch(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[PitchAnalysis, CallUsage]:
    idea = state["selected_idea"]
    tech = state.get("tech_analysis")
    stack = joined(tech.recommended_stack) if tech else ""
    user = (
        f"{idea_context(idea)}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        f"Expected impact: {idea.expected_impact or 'n/a'}\n"
        f"Recommended stack: {stack or 'unspecified'}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return PitchAnalysis JSON."
    )
    return client.generate(
        system=SYSTEM, user=user, schema=PitchAnalysis, max_output_tokens=750
    )
