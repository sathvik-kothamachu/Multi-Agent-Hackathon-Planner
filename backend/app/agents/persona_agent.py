"""Persona Adapter (research objective #3).

Adapts ONLY the explanation depth, terminology, and hand-holding of the SAME final
plan to the team's effective skill level. The underlying solution never changes.
Effective persona = explicit override if set, else derived (lowest skill wins).
"""
from __future__ import annotations

from typing import Tuple

from app.agents.persona_logic import derive_persona
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import Blueprint, PersonaAdaptedPlan, SkillLevel

SYSTEM = (
    "You are the Persona Adapter. Given a FIXED final plan, adapt ONLY the explanation depth, "
    "terminology, and level of hand-holding to the team's skill level. Do NOT change the underlying "
    "solution, stack, timeline, or pitch. Return PersonaAdaptedPlan JSON."
)


def _resolve_persona(state: dict) -> str:
    profile = state.get("team_profile")
    override = getattr(profile, "overall_persona", None) if profile is not None else None
    if override:
        return override.value if hasattr(override, "value") else str(override)
    members = getattr(profile, "members", []) if profile is not None else []
    return derive_persona([m.skill_level for m in members])


def adapt_persona(
    state: dict, client: LLMClient, settings: Settings
) -> Tuple[PersonaAdaptedPlan, CallUsage]:
    persona = _resolve_persona(state)
    plan: Blueprint = state["final_plan"]
    user = (
        f"Persona: {persona}\n"
        f"Selected idea: {plan.selected_idea.title}\n"
        f"Stack: {', '.join(plan.recommended_stack)}\n"
        f"Timeline: {', '.join(m.name for m in plan.timeline)}\n"
        f"Value proposition: {plan.value_proposition}\n"
        "Adapt the guidance to this persona only. Return PersonaAdaptedPlan JSON."
    )
    out, usage = client.generate(
        system=SYSTEM, user=user, schema=PersonaAdaptedPlan, max_output_tokens=800
    )
    # Enforce the requested persona regardless of any model drift.
    try:
        out.persona = SkillLevel(persona)
    except ValueError:
        out.persona = SkillLevel.intermediate
    return out, usage
