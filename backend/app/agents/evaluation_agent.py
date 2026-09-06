"""Idea Evaluator — scores ALL candidate ideas in a SINGLE LLM call.

Advisory stage between idea generation and human selection: the user sees each
idea scored on 8 criteria so they can compare before choosing. It NEVER
auto-selects — the human decides. Token discipline (research requirement #7):
one call for all ideas (never one-per-idea), a compact idea view (not full
solutions), and `overall` is averaged deterministically server-side rather than
asking the LLM to do arithmetic.
"""
from __future__ import annotations

from typing import List, Tuple

from app.agents.common import joined, team_context
from app.core.config import Settings
from app.core.logging import get_logger
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import (
    IdeaDraft,
    IdeaEvaluation,
    IdeaEvaluationOutput,
)

logger = get_logger(__name__)

# The 8 criteria whose scores are averaged into `overall`.
_CRITERIA = (
    "theme_alignment",
    "problem_relevance",
    "innovation",
    "technical_feasibility",
    "time_feasibility",
    "team_skill_fit",
    "impact",
    "demo_potential",
)

SYSTEM = (
    "You are the Idea Evaluator for a hackathon planner. Score EACH candidate idea on 8 criteria, "
    "each 0-100 with a one-line reason: theme_alignment, problem_relevance, innovation, "
    "technical_feasibility, time_feasibility, team_skill_fit, impact, demo_potential. For each idea "
    "also give: strongest_point, biggest_weakness, biggest_risk (implementation), why_fits (why it "
    "fits the problem/theme). Set each idea's 'idea_id' to the id given. Be objective and concise; "
    "do NOT recommend or pick a winner — the human chooses. Return IdeaEvaluationOutput JSON with an "
    "'evaluations' array, one entry per idea."
)


def _idea_line(idea: IdeaDraft) -> str:
    """One compact line per idea (token-efficient; no full solution paragraphs)."""
    return (
        f"[{idea.id}] {idea.title} — problem: {(idea.problem or '')[:140]}; "
        f"solution: {(idea.solution or '')[:220]}; "
        f"features: {joined(idea.core_features, limit=5)}; "
        f"users: {idea.target_users}"
    )


def _overall(ev: IdeaEvaluation) -> int:
    """Deterministic average of the 8 criteria (0-100). No LLM arithmetic."""
    scores = [max(0, min(100, int(getattr(ev, c).score))) for c in _CRITERIA]
    return round(sum(scores) / len(scores)) if scores else 0


def evaluate_ideas(
    ideas: List[IdeaDraft],
    state: dict,
    client: LLMClient,
    settings: Settings,
) -> Tuple[List[IdeaEvaluation], CallUsage]:
    """Evaluate every candidate idea in one call; overall averaged server-side."""
    if not ideas:
        return [], CallUsage(input_tokens=0, output_tokens=0, latency_ms=0.0)

    listing = "\n".join(_idea_line(i) for i in ideas)
    user = (
        f"Problem: {state.get('problem_statement', '')}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Team: {team_context(state.get('team_profile'))}\n"
        f"Candidate ideas ({len(ideas)}):\n{listing}\n"
        "Return IdeaEvaluationOutput JSON with one evaluation per idea."
    )
    out, usage = client.generate(
        system=SYSTEM, user=user, schema=IdeaEvaluationOutput, max_output_tokens=1200
    )

    # Map by id so we can reconcile the LLM output back to the real ideas and fill
    # any it skipped, guaranteeing exactly one evaluation per candidate.
    by_id = {e.idea_id: e for e in out.evaluations if e.idea_id}
    by_title = {(e.title or "").strip().lower(): e for e in out.evaluations}
    results: List[IdeaEvaluation] = []
    for idea in ideas:
        ev = by_id.get(idea.id) or by_title.get((idea.title or "").strip().lower())
        if ev is None:
            logger.warning("evaluator returned no entry for idea %s; using neutral fallback", idea.id)
            ev = IdeaEvaluation()
        ev.idea_id = idea.id
        ev.title = idea.title or ev.title
        ev.overall = _overall(ev)  # always deterministic
        results.append(ev)
    return results, usage
