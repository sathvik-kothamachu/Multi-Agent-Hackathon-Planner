"""Single-shot baseline (research requirement #16).

User Input -> ONE LLM call -> Final Plan. No debate, no alignment gate, no persona
adaptation. This is the ablation control the proposed pipeline is measured against.
"""
from __future__ import annotations

from typing import Tuple

from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import BaselinePlan

SYSTEM = (
    "You are a hackathon planning assistant. Given a problem statement, produce ONE complete "
    "hackathon plan in a single pass. Return BaselinePlan JSON only."
)


def run_baseline(
    problem_statement: str,
    hackathon_theme: str,
    time_limit_hours: int,
    preferences: str,
    client: LLMClient,
    settings: Settings,
) -> Tuple[BaselinePlan, CallUsage]:
    user = (
        f"Problem: {problem_statement}\n"
        f"Theme: {hackathon_theme}\n"
        f"Time limit: {time_limit_hours} hours\n"
        + (f"Preferences: {preferences}\n" if preferences else "")
        + "Return fields: idea, recommended_stack, architecture, timeline (milestones), "
        "dependencies, technical_risks, value_proposition, differentiation, pitch_structure, "
        "solution_summary."
    )
    return client.generate(system=SYSTEM, user=user, schema=BaselinePlan, max_output_tokens=900)
