"""Tech Stack Architect — critiques the SAME idea for technical feasibility.

Consumes the selected idea, theme, time limit, the team's skills, and whether
the team is building WITH AI tooling. The AI-usage rule is enforced in the prompt
AND defensively post-validated: when using_ai is False we do not auto-introduce
AI/LLM technologies the team didn't already list.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.agents.common import idea_context, joined, team_context
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import TechAnalysis

_AI_TERMS = re.compile(
    r"\b(ai|ml|machine learning|deep learning|llm|gpt|openai|neural|transformer|"
    r"sentence-?transformers|langchain|langgraph|tensorflow|pytorch|hugging ?face|embedding)\b",
    re.I,
)

SYSTEM = (
    "You are the Tech Stack Architect. Critique the SAME idea for TECHNICAL feasibility. "
    "Return TechAnalysis JSON with: feasibility_score (0-100 integer), feasibility (low/medium/high), "
    "complexity (Low/Medium/High), recommended_stack (list of names), stack_details (list of "
    "{{name, purpose}} explaining WHY each technology is chosen for THIS idea), architecture, "
    "technical_risks, recommendations, critique. If a requirement conflicts with the timeline or "
    "pitch, note it in 'cross_domain_flags'. {ai_rule} Be concise; short lists, not prose."
)

AI_YES = (
    "The team IS using AI tooling to build, so you MAY recommend AI/LLM technologies where they "
    "genuinely add value."
)
AI_NO = (
    "The team is NOT using AI tooling to build, so DO NOT introduce AI/LLM technologies; prefer the "
    "team's existing skills and conventional tech."
)


def _strip_ai_tech(analysis: TechAnalysis, allowed: set[str]) -> None:
    """Remove AI/LLM stack items the team didn't already list (using_ai=False)."""
    def ok(name: str) -> bool:
        return (name.lower() in allowed) or not _AI_TERMS.search(name or "")

    analysis.recommended_stack = [s for s in analysis.recommended_stack if ok(s)]
    analysis.stack_details = [d for d in analysis.stack_details if ok(d.name)]


def analyze_tech(
    state: dict, client: LLMClient, settings: Settings, revision: str = ""
) -> Tuple[TechAnalysis, CallUsage]:
    idea = state["selected_idea"]
    team = state.get("team_profile")
    using_ai = bool(state.get("using_ai", True))
    system = SYSTEM.format(ai_rule=AI_YES if using_ai else AI_NO)
    user = (
        f"{idea_context(idea)}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        f"Team: {team_context(team)}\n"
        f"Using AI tools to build: {'yes' if using_ai else 'no'}\n"
        + (f"Revision requested by arbiter: {revision}\n" if revision else "")
        + "Return TechAnalysis JSON."
    )
    analysis, usage = client.generate(
        system=system, user=user, schema=TechAnalysis, max_output_tokens=650
    )
    if not using_ai:
        allowed = set()
        for m in getattr(team, "members", []) or []:
            for sk in getattr(m, "skills", []) or []:
                allowed.add(sk.lower())
        _strip_ai_tech(analysis, allowed)
    # Keep the two feasibility representations consistent.
    if analysis.feasibility_score:
        analysis.feasibility = (
            "high" if analysis.feasibility_score >= 75
            else "medium" if analysis.feasibility_score >= 50
            else "low"
        )
    return analysis, usage
