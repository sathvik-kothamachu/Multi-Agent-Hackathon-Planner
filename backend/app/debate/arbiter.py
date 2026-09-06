"""Debate Arbiter — the single LLM step that detects, critiques, and RESOLVES
meaningful conflicts between the tech, timeline, and pitch analyses of the SAME
idea (research objective #1: detect -> critique -> resolve -> converge).

Token discipline: the arbiter receives only a compact, structured summary of each
specialist's analysis, never their full JSON.
"""
from __future__ import annotations

from typing import Tuple

from app.agents.common import joined
from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.models.schemas import ArbiterOutput

SYSTEM = (
    "You are the Debate Arbiter. You are given compact critiques (tech, timeline) of the "
    "SAME idea plus the original problem. Identify MEANINGFUL conflicts between technology, timeline, "
    "and the original requirements (e.g. technical complexity vs. available hours). For each real "
    "conflict, give a concrete resolution and set resolved=true. Emit revision_directives ONLY for "
    "agents whose analysis must change (agent is one of: tech, timeline). Also emit a concise "
    "'current_solution_text' (1-2 sentences) describing the converged solution. Do NOT invent "
    "conflicts. Return ArbiterOutput JSON."
)


def run_arbiter(
    state: dict, client: LLMClient, settings: Settings
) -> Tuple[ArbiterOutput, CallUsage]:
    idea = state["selected_idea"]
    tech = state.get("tech_analysis")
    timeline = state.get("timeline_analysis")
    user = (
        f"Original problem: {state['problem_statement']}\n"
        f"Time limit (hours): {state.get('time_limit_hours', 24)}\n"
        f"Idea: {idea.title} - {idea.solution}\n"
        f"Tech: feasibility={tech.feasibility}, complexity={tech.complexity}, "
        f"stack=[{joined(tech.recommended_stack)}], flags=[{joined(tech.cross_domain_flags)}]\n"
        f"Timeline: feasible={timeline.feasible}, "
        f"milestones=[{joined([m.name for m in timeline.milestones])}], "
        f"flags=[{joined(timeline.cross_domain_flags)}]\n"
        "Return ArbiterOutput JSON."
    )
    return client.generate(
        system=SYSTEM, user=user, schema=ArbiterOutput, max_output_tokens=600
    )
