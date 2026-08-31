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
    return (
        f"Title: {idea.title}\n"
        f"Problem: {idea.problem}\n"
        f"Solution: {idea.solution}\n"
        f"Target users: {idea.target_users}"
    )


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
