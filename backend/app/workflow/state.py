"""Centralized LangGraph workflow state.

A single TypedDict holds only the relevant, structured fields (research
requirement #9). Agents read/write this instead of passing uncontrolled
variables around; nodes return partial dicts that LangGraph merges in.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

from app.models.schemas import (
    Blueprint,
    Conflict,
    IdeaDraft,
    PersonaAdaptedPlan,
    PitchAnalysis,
    RevisionDirective,
    TeamProfile,
    TechAnalysis,
    TimelineAnalysis,
)


class WorkflowState(TypedDict, total=False):
    # ---- inputs ----
    project_id: str
    problem_statement: str
    hackathon_theme: str
    time_limit_hours: int
    preferences: str
    team_profile: TeamProfile

    # ---- ideation + human review ----
    candidate_ideas: List[IdeaDraft]
    selected_idea: Optional[IdeaDraft]

    # ---- debate ----
    tech_analysis: Optional[TechAnalysis]
    timeline_analysis: Optional[TimelineAnalysis]
    pitch_analysis: Optional[PitchAnalysis]
    conflicts: List[Conflict]
    revision_directives: List[RevisionDirective]
    current_solution_text: str
    debate_round: int
    agents_to_revise: List[str]

    # ---- alignment gate ----
    alignment_score: Optional[float]
    alignment_status: str
    alignment_history: List[Dict[str, object]]
    initial_alignment: Optional[float]

    # ---- outputs ----
    final_plan: Optional[Blueprint]
    persona_adapted_plan: Optional[PersonaAdaptedPlan]

    # ---- metrics accumulation (per-call usage records) ----
    usage_log: List[Dict[str, object]]
