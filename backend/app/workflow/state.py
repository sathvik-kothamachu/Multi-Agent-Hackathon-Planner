"""Centralized LangGraph workflow state.

A single TypedDict holds only the relevant, structured fields (research
requirement #9). Agents read/write this instead of passing uncontrolled
variables around; nodes return partial dicts that LangGraph merges in.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

from app.models.schemas import (
    AlignmentReport,
    Blueprint,
    Conflict,
    IdeaDraft,
    IdeaEvaluation,
    MemberAllocation,
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
    using_ai: bool

    # ---- ideation + human review ----
    candidate_ideas: List[IdeaDraft]
    # Advisory /100 scores for the current candidate_ideas (one per idea), shown
    # to the human before they select. Never used to auto-select.
    idea_evaluations: List[IdeaEvaluation]
    # Every idea ever generated for this project (title-keyed), so Regenerate can
    # reject semantic/title duplicates and never return a prior idea.
    idea_history: List[IdeaDraft]
    selected_idea: Optional[IdeaDraft]
    # Human decision injected on resume (runner.update_state) and read by
    # human_review_node; declared here so it is a tracked LangGraph channel.
    pending_decision: Optional[Dict[str, object]]
    review_action: Optional[str]

    # ---- debate ----
    tech_analysis: Optional[TechAnalysis]
    timeline_analysis: Optional[TimelineAnalysis]
    pitch_analysis: Optional[PitchAnalysis]
    conflicts: List[Conflict]
    revision_directives: List[RevisionDirective]
    current_solution_text: str
    debate_round: int
    agents_to_revise: List[str]

    # ---- team allocation (deterministic, skill-matched) ----
    team_allocation: List[MemberAllocation]

    # ---- alignment gate ----
    alignment_score: Optional[float]
    alignment_status: str
    alignment_history: List[Dict[str, object]]
    initial_alignment: Optional[float]
    alignment_report: Optional[AlignmentReport]

    # ---- outputs ----
    final_plan: Optional[Blueprint]
    persona_adapted_plan: Optional[PersonaAdaptedPlan]

    # ---- metrics accumulation (per-call usage records) ----
    usage_log: List[Dict[str, object]]
