"""Shared agent helpers — concise context builders + usage accounting.

Token discipline (research requirement #7): debate agents receive a small,
structured view of the idea, never the full transcript of other agents.
"""
from __future__ import annotations

from typing import List

from app.llm.base import CallUsage
from app.models.schemas import IdeaDraft


def idea_context(idea: IdeaDraft) -> str:
    """A compact, structured description of the idea for debate agents."""
    solution = (idea.solution or "")[:600]
    return (
        f"Title: {idea.title}\n"
        f"Problem: {idea.problem}\n"
        f"Solution: {solution}\n"
        f"Objectives: {joined(idea.objectives)}\n"
        f"Core features: {joined(idea.core_features)}\n"
        f"Target users: {idea.target_users}"
    )


def team_context(team) -> str:
    """Compact team summary (names + skills + level) for skill-aware agents."""
    members = getattr(team, "members", []) or []
    if not members:
        return "unknown team"
    parts = []
    for m in members:
        name = getattr(m, "name", "") or getattr(m, "role", "") or "member"
        skills = joined(getattr(m, "skills", []), limit=6)
        level = getattr(getattr(m, "skill_level", None), "value", "intermediate")
        parts.append(f"{name} ({level}; skills: {skills or 'n/a'})")
    return "; ".join(parts)


def joined(items: List[str], limit: int = 8) -> str:
    return "; ".join(str(i) for i in (items or [])[:limit])


def append_usage(state: dict, *usages: CallUsage) -> list:
    """Return a NEW usage_log list with the given usages appended.

    Nodes return this so LangGraph's default overwrite-merge accumulates cost
    correctly without needing a custom reducer.
    """
    log = list(state.get("usage_log", []))
    for u in usages:
        log.append(u.as_dict())
    return log
