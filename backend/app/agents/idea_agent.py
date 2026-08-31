"""Idea Generator agent — proposes at most `max_ideas` distinct, buildable ideas.

Stops after generation so a human can review/select/modify (research objective:
human-in-the-loop). Ids are assigned deterministically server-side.
"""
from __future__ import annotations

from typing import List, Tuple

from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import IdeaDraft, IdeaGenerationOutput

SYSTEM = (
    "You are the Idea Generator for a hackathon planner. Propose at most {n} DISTINCT, "
    "concrete, buildable ideas for the given problem and theme that fit the time limit. "
    "Return JSON with an 'ideas' array; each idea has title, problem, solution, "
    "target_users, rationale. Keep every field to one or two sentences."
)


def generate_ideas(
    state: dict, client: LLMClient, settings: Settings
) -> Tuple[List[IdeaDraft], CallUsage]:
    n = settings.max_ideas
    system = SYSTEM.format(n=n)
    user = (
        f"Problem: {state['problem_statement']}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Preferences: {state.get('preferences', '') or 'none'}\n"
        f"Generate at most {n} ideas."
    )
    out, usage = client.generate(
        system=system, user=user, schema=IdeaGenerationOutput, max_output_tokens=700
    )
    ideas = out.ideas[:n]
    for i, idea in enumerate(ideas, start=1):
        idea.id = f"idea-{i}"
        if not idea.problem:
            idea.problem = state["problem_statement"]
    return ideas, usage
