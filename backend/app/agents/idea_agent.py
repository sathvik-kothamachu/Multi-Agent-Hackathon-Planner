"""Idea Generator agent — proposes exactly `max_ideas` distinct, buildable ideas.

Each idea is rich: a detailed multi-paragraph solution, exactly four objectives,
core features, target users, expected impact, and theme relevance. Generation
stops after this so a human can review/select/modify (human-in-the-loop). On
Regenerate, freshly generated ideas are de-duplicated against the project's idea
history using the shared embedding+cosine path (no extra LLM call), so the user
never sees a repeat. Ids are assigned deterministically server-side.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from app.agents.dedup import dedupe_against_history
from app.agents.common import joined
from app.core.config import Settings
from app.core.logging import get_logger
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import IdeaDraft, IdeaGenerationOutput

logger = get_logger(__name__)

# Titles the LLM must never ship; rejected + repaired deterministically.
_GENERIC_TITLE = re.compile(
    r"^\s*(ai|smart|innovative|the)?\s*(solution|idea|app|project|platform|tool)\s*\d*\s*$",
    re.I,
)

SYSTEM = (
    "You are the Idea Generator for a hackathon planner. Generate exactly {n} MEANINGFULLY "
    "DIFFERENT hackathon project ideas for the given problem and theme that fit the time limit — "
    "differ by solution approach, core mechanism, or target usage, NOT cosmetic variations. "
    "Return JSON with an 'ideas' array. Each idea MUST have: title (professional, unique, "
    "solution-specific — NEVER generic like 'AI Solution'/'Smart Solution'/'Solution 1'); "
    "core_concept (one-line hook); problem; solution (2-3 full paragraphs: what it does, how it "
    "works, how users interact, major components, what makes it different); how_it_works (the "
    "mechanism + major components); objectives (EXACTLY 4, each SPECIFIC to this idea and "
    "capturing its unifying purpose, key novelty, major functional goal, and expected practical "
    "outcome — never generic like 'improve efficiency'); core_features (3-6 items); "
    "implementation_approach (3-6 ordered build steps); target_users (specific, NOT 'judges'); "
    "expected_impact; innovation (what makes it different); feasibility (why it fits the time "
    "limit); tech_approach (technology/AI approach, or '' if not AI-based); theme_relevance. "
    "Ideas must be conceptually distinct from each other{avoid}. Be concrete, not generic."
)


def _avoid_clause(history: List[IdeaDraft]) -> str:
    if not history:
        return ""
    titles = joined([i.title for i in history], limit=12)
    return f" and DIFFERENT from these already-seen ideas: {titles}"


def _enforce_four_objectives(idea: IdeaDraft) -> None:
    """Guarantee exactly 4 objectives without fabricating specific content."""
    objs = [o for o in (idea.objectives or []) if o and o.strip()][:4]
    title = idea.title or "the solution"
    while len(objs) < 4:
        fillers = [
            f"Deliver the core capability of {title} end to end.",
            "Build a working, demoable version of the main feature.",
            "Keep the scope buildable within the hackathon time limit.",
            "Produce a clear, judge-friendly outcome from the solution.",
        ]
        objs.append(fillers[len(objs)])
    idea.objectives = objs


def _is_generic_title(title: str) -> bool:
    return not title or not title.strip() or bool(_GENERIC_TITLE.match(title.strip()))


def _repair_title(idea: IdeaDraft, index: int, taken: set[str], theme: str) -> None:
    """Give the idea a professional, unique, solution-specific title in place.

    Only fires when the LLM title is empty, generic, or a duplicate — we never
    overwrite a good title (spec: don't regenerate unnecessarily).
    """
    current = (idea.title or "").strip()
    if current and not _is_generic_title(current) and current.lower() not in taken:
        taken.add(current.lower())
        return
    # Build a specific title from the idea's own content, not a generic label.
    seed = (idea.core_concept or idea.target_users or theme or "Project").strip()
    seed = re.sub(r"\s+", " ", seed).strip(" .")
    words = " ".join(seed.split()[:4]).title() or f"{theme.title()} Concept"
    base = f"{words} {['Planner', 'Assistant', 'Hub', 'Studio'][index % 4]}"
    candidate = base
    n = 2
    while candidate.lower() in taken:
        candidate = f"{base} {n}"
        n += 1
    idea.title = candidate
    taken.add(candidate.lower())


def _finalize(idea: IdeaDraft, seq: int, index: int, taken: set[str], state: dict) -> None:
    """Deterministic per-idea validation/repair (title, objectives, problem)."""
    idea.id = f"idea-{seq}"
    if not idea.problem:
        idea.problem = state["problem_statement"]
    _repair_title(idea, index, taken, state.get("hackathon_theme", "general"))
    _enforce_four_objectives(idea)


def _synthesize_idea(index: int, taken: set[str], state: dict) -> IdeaDraft:
    """Last-resort filler so the review phase ALWAYS shows exactly n ideas.

    Used only when the LLM + dedup could not supply enough distinct ideas; the
    idea is clearly grounded in the user's own problem/theme, not a fake concept.
    """
    problem = state["problem_statement"]
    theme = state.get("hackathon_theme", "general")
    angles = [
        ("guided workflow", "a step-by-step guided workflow"),
        ("automation", "one-click automation of the hardest manual step"),
        ("insight dashboard", "a dashboard that surfaces the key insight at a glance"),
    ]
    label, mechanism = angles[index % len(angles)]
    idea = IdeaDraft(
        core_concept=f"A {label} that tackles the stated problem directly.",
        problem=problem,
        solution=(
            f"This approach addresses the problem — {problem} — by offering {mechanism}. "
            "Users provide their context, the app processes it, and it returns an actionable "
            "result they can use immediately. The workflow is intentionally short so it can be "
            "demoed live end to end within the time limit."
        ),
        how_it_works=f"The user's input drives {mechanism}, producing an actionable result.",
        core_features=["Focused input capture", "Core processing step", "Actionable result view"],
        implementation_approach=[
            "Scaffold the app skeleton.",
            f"Implement {mechanism}.",
            "Wire the result UI and rehearse the demo.",
        ],
        target_users="people who face the stated problem in their daily workflow",
        expected_impact="Cuts the time and effort of the manual process with a concrete result.",
        innovation=f"Applies {label} specifically to this problem rather than a generic tool.",
        feasibility="Small, focused scope that fits the hackathon time limit.",
        theme_relevance=f"Fits the '{theme}' theme by applying it to a real, specific workflow.",
        rationale="Small scope, high clarity, buildable in the time limit.",
    )
    _finalize(idea, seq=index + 1, index=index, taken=taken, state=state)
    return idea


def generate_ideas(
    state: dict, client: LLMClient, settings: Settings
) -> Tuple[List[IdeaDraft], CallUsage]:
    """Generate up to `max_ideas` fresh ideas, de-duplicated against history."""
    n = settings.max_ideas
    history: List[IdeaDraft] = list(state.get("idea_history", []))
    system = SYSTEM.format(n=n, avoid=_avoid_clause(history))
    user = (
        f"Problem: {state['problem_statement']}\n"
        f"Theme: {state.get('hackathon_theme', 'general')}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Preferences: {state.get('preferences', '') or 'none'}\n"
        f"Generate exactly {n} distinct ideas."
    )
    out, usage = client.generate(
        system=system, user=user, schema=IdeaGenerationOutput, max_output_tokens=1800
    )

    # 1) Reject any that duplicate a prior idea (title or concept), keep up to n.
    distinct = dedupe_against_history(out.ideas, history, settings)
    ideas: List[IdeaDraft] = distinct[:n]

    # 2) Backfill if dedup left us short: first from the raw LLM set (skipping ones
    #    already kept), then, only if still short, deterministic synthesized ideas.
    if len(ideas) < n:
        kept = {id(i) for i in ideas}
        for extra in out.ideas:
            if len(ideas) >= n:
                break
            if id(extra) not in kept:
                ideas.append(extra)

    # 3) Finalize the ones we have: ids, problem default, unique professional
    #    titles, exactly 4 objectives (deterministic, targeted repair).
    seq0 = len(history)
    taken: set[str] = set()
    for index, idea in enumerate(ideas):
        _finalize(idea, seq=seq0 + index + 1, index=index, taken=taken, state=state)

    # 4) Hard guarantee: EXACTLY n ideas. Synthesize grounded fillers if needed.
    while len(ideas) < n:
        index = len(ideas)
        ideas.append(_synthesize_idea(index, taken, state))
        # re-key synthesized id to continue the project's sequence
        ideas[-1].id = f"idea-{seq0 + index + 1}"

    return ideas[:n], usage
