"""Pydantic v2 schemas — the typed contracts shared by agents, the API, and the
frontend. LLM-parsed models set `extra='ignore'` so an over-eager model response
never breaks validation. Field names here are the single source of truth for the
React client.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


# --------------------------------------------------------------------------- #
# Team / input
# --------------------------------------------------------------------------- #
class TeamMember(BaseModel):
    role: str = ""
    skill_level: SkillLevel = SkillLevel.intermediate


class TeamProfile(BaseModel):
    members: List[TeamMember] = Field(default_factory=list)
    # Optional explicit override used by the on-demand persona comparison; when
    # None the effective persona is derived from members (lowest skill wins).
    overall_persona: Optional[SkillLevel] = None


class ProjectCreateRequest(BaseModel):
    problem_statement: str
    hackathon_theme: str = "general"
    time_limit_hours: int = 24
    preferences: str = ""
    team_members: List[TeamMember] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Ideas
# --------------------------------------------------------------------------- #
class IdeaDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    title: str = ""
    problem: str = ""
    solution: str = ""
    target_users: str = ""
    rationale: str = ""


class IdeaGenerationOutput(BaseModel):
    """Raw LLM output for the idea generator (ids are assigned server-side)."""

    model_config = ConfigDict(extra="ignore")

    ideas: List[IdeaDraft] = Field(default_factory=list)


class SelectIdeaRequest(BaseModel):
    idea_id: str


class ModifyIdeaRequest(BaseModel):
    idea: IdeaDraft


# --------------------------------------------------------------------------- #
# Agent analyses (concise, list-based — never essays)
# --------------------------------------------------------------------------- #
class Milestone(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    duration: str = ""
    dependencies: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)


class TechAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feasibility: str = "medium"
    complexity: str = "medium"
    recommended_stack: List[str] = Field(default_factory=list)
    architecture: List[str] = Field(default_factory=list)
    technical_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    critique: List[str] = Field(default_factory=list)
    cross_domain_flags: List[str] = Field(default_factory=list)


class TimelineAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feasible: bool = True
    milestones: List[Milestone] = Field(default_factory=list)
    critical_dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    critique: List[str] = Field(default_factory=list)
    cross_domain_flags: List[str] = Field(default_factory=list)


class PitchAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value_proposition: str = ""
    target_user: str = ""
    differentiation: List[str] = Field(default_factory=list)
    impact: str = ""
    pitch_structure: List[str] = Field(default_factory=list)
    critique: List[str] = Field(default_factory=list)
    cross_domain_flags: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Debate / arbiter
# --------------------------------------------------------------------------- #
class Conflict(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    description: str
    severity: str = "medium"
    resolution: str = ""
    resolved: bool = False


class RevisionDirective(BaseModel):
    model_config = ConfigDict(extra="ignore")

    agent: str
    change: str = ""


class ArbiterOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    conflicts: List[Conflict] = Field(default_factory=list)
    revision_directives: List[RevisionDirective] = Field(default_factory=list)
    current_solution_text: str = ""


# --------------------------------------------------------------------------- #
# Alignment gate (research objective #2)
# --------------------------------------------------------------------------- #
class AlignmentResult(BaseModel):
    alignment_score: float
    threshold: float
    status: str  # "aligned" | "drift" | "max_rounds_exceeded"
    reason: str = ""
    round: int = 1


# --------------------------------------------------------------------------- #
# Persona adaptation (research objective #3)
# --------------------------------------------------------------------------- #
class PersonaAdaptedPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    persona: SkillLevel = SkillLevel.intermediate
    summary: str = ""
    tech_guidance: str = ""
    timeline_guidance: str = ""
    pitch_guidance: str = ""
    pitfalls: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class PersonaRequest(BaseModel):
    """On-demand re-adaptation of the SAME final plan to a chosen skill level.
    Powers the UI's beginner/intermediate/advanced comparison (research objective #3)."""

    persona: SkillLevel


# --------------------------------------------------------------------------- #
# Final blueprint
# --------------------------------------------------------------------------- #
class Blueprint(BaseModel):
    problem_statement: str
    selected_idea: IdeaDraft
    target_users: str = ""
    recommended_stack: List[str] = Field(default_factory=list)
    architecture: List[str] = Field(default_factory=list)
    timeline: List[Milestone] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    technical_risks: List[str] = Field(default_factory=list)
    value_proposition: str = ""
    differentiation: List[str] = Field(default_factory=list)
    pitch_structure: List[str] = Field(default_factory=list)
    alignment_score: Optional[float] = None
    alignment_status: str = ""
    debate_summary: str = ""


# --------------------------------------------------------------------------- #
# Baseline (single-shot) — for the ablation
# --------------------------------------------------------------------------- #
class BaselinePlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    idea: IdeaDraft
    recommended_stack: List[str] = Field(default_factory=list)
    architecture: List[str] = Field(default_factory=list)
    timeline: List[Milestone] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    technical_risks: List[str] = Field(default_factory=list)
    value_proposition: str = ""
    differentiation: List[str] = Field(default_factory=list)
    pitch_structure: List[str] = Field(default_factory=list)
    solution_summary: str = ""


# --------------------------------------------------------------------------- #
# Metrics + API responses
# --------------------------------------------------------------------------- #
class RunMetrics(BaseModel):
    mode: str = "proposed"  # "proposed" | "baseline"
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    debate_rounds: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    initial_alignment: Optional[float] = None
    final_alignment: Optional[float] = None


class WorkflowStepResponse(BaseModel):
    project_id: str
    status: str
    ideas: Optional[List[IdeaDraft]] = None
    blueprint: Optional[Blueprint] = None
    persona_adapted_plan: Optional[PersonaAdaptedPlan] = None
    metrics: Optional[RunMetrics] = None


class EvaluationReport(BaseModel):
    project_id: str
    proposed_metrics: RunMetrics
    baseline_metrics: RunMetrics
    proposed_alignment: Optional[float] = None
    baseline_alignment: Optional[float] = None
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    debate_rounds: int = 0
    notes: List[str] = Field(default_factory=list)
