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
    model_config = ConfigDict(extra="ignore")

    # `name` and `skills` were added so the planner can allocate concrete tasks to
    # real people; persona still derives from `skill_level` alone (back-compatible).
    name: str = ""
    role: str = ""
    skills: List[str] = Field(default_factory=list)
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
    # Whether the team intends to use AI/LLM tooling to BUILD the project. Drives
    # the Tech agent's stack rule: if False, do not auto-introduce AI/LLM tech.
    using_ai: bool = True


# --------------------------------------------------------------------------- #
# Ideas
# --------------------------------------------------------------------------- #
class IdeaDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    title: str = ""
    # One-line "what this is" hook shown at the top of the review card.
    core_concept: str = ""
    problem: str = ""
    # `solution` is a detailed 2-3 paragraph narrative (what problem is solved,
    # how the product solves it, how users interact, workflow, outcome).
    solution: str = ""
    # How the system actually works end to end (mechanism + major components).
    how_it_works: str = ""
    objectives: List[str] = Field(default_factory=list)  # exactly 4, enforced server-side
    core_features: List[str] = Field(default_factory=list)
    # Ordered, concrete build steps for this specific idea.
    implementation_approach: List[str] = Field(default_factory=list)
    target_users: str = ""
    expected_impact: str = ""
    # What makes this idea different from the obvious approach.
    innovation: str = ""
    # Why it is buildable within the hackathon time limit.
    feasibility: str = ""
    # Technology / AI approach when relevant (empty if not AI-based).
    tech_approach: str = ""
    theme_relevance: str = ""
    rationale: str = ""


class IdeaGenerationOutput(BaseModel):
    """Raw LLM output for the idea generator (ids are assigned server-side)."""

    model_config = ConfigDict(extra="ignore")

    ideas: List[IdeaDraft] = Field(default_factory=list)


class CriterionScore(BaseModel):
    """One evaluation criterion: a 0-100 score plus a one-line reason."""

    model_config = ConfigDict(extra="ignore")

    score: int = 0
    reason: str = ""


class IdeaEvaluation(BaseModel):
    """Structured evaluation of ONE candidate idea across 8 criteria.

    Advisory only — the human still chooses. `overall` is computed
    deterministically server-side (the average of the 8 criteria), never by the
    LLM, per the token-discipline rule.
    """

    model_config = ConfigDict(extra="ignore")

    idea_id: str = ""
    title: str = ""
    theme_alignment: CriterionScore = Field(default_factory=CriterionScore)
    problem_relevance: CriterionScore = Field(default_factory=CriterionScore)
    innovation: CriterionScore = Field(default_factory=CriterionScore)
    technical_feasibility: CriterionScore = Field(default_factory=CriterionScore)
    time_feasibility: CriterionScore = Field(default_factory=CriterionScore)
    team_skill_fit: CriterionScore = Field(default_factory=CriterionScore)
    impact: CriterionScore = Field(default_factory=CriterionScore)
    demo_potential: CriterionScore = Field(default_factory=CriterionScore)
    overall: int = 0  # 0-100, computed server-side
    strongest_point: str = ""
    biggest_weakness: str = ""
    biggest_risk: str = ""
    why_fits: str = ""


class IdeaEvaluationOutput(BaseModel):
    """Raw LLM output: one evaluation per candidate idea (single call)."""

    model_config = ConfigDict(extra="ignore")

    evaluations: List[IdeaEvaluation] = Field(default_factory=list)


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


class StackItem(BaseModel):
    """One recommended technology + why it's chosen for this idea."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    purpose: str = ""


class TechAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feasibility: str = "medium"  # kept for back-compat / debate summaries
    feasibility_score: int = 70  # 0-100, shown in the UI
    complexity: str = "medium"  # Low | Medium | High
    recommended_stack: List[str] = Field(default_factory=list)
    stack_details: List[StackItem] = Field(default_factory=list)  # name+purpose
    architecture: List[str] = Field(default_factory=list)
    technical_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    critique: List[str] = Field(default_factory=list)
    cross_domain_flags: List[str] = Field(default_factory=list)


class ScheduleTask(BaseModel):
    """One ordered, chronological item in the build schedule."""

    model_config = ConfigDict(extra="ignore")

    task: str = ""
    technology: str = ""
    duration: str = ""
    dependency: str = ""
    expected_output: str = ""


class TimelineAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feasible: bool = True
    estimated_hours: float = 0.0
    available_hours: float = 0.0
    time_risk: str = ""  # populated when estimate exceeds the available time
    schedule: List[ScheduleTask] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    critical_dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    critique: List[str] = Field(default_factory=list)
    cross_domain_flags: List[str] = Field(default_factory=list)


class MemberAllocation(BaseModel):
    """Tasks assigned to one named team member (deterministic, skill-matched)."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    role: str = ""
    skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    time_allocation: str = ""


class PitchAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value_proposition: str = ""
    aim: str = ""
    target_user: str = ""
    differentiation: List[str] = Field(default_factory=list)
    impact: str = ""
    why_this_solution: str = ""
    implementation_approach: List[str] = Field(default_factory=list)
    future_scope: List[str] = Field(default_factory=list)
    demo_flow: List[str] = Field(default_factory=list)  # 2-minute demo steps
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


class AlignmentReport(BaseModel):
    """User-facing /100 alignment breakdown (no cosine/threshold jargon).

    Derived deterministically from the semantic cosine score + the tech
    feasibility score + lexical overlap; no extra LLM call.
    """

    model_config = ConfigDict(extra="ignore")

    overall: int = 0  # 0-100
    label: str = ""  # e.g. "Strong alignment"
    theme_relevance: int = 0
    problem_relevance: int = 0
    user_problem_fit: int = 0
    solution_relevance: int = 0
    feasibility: int = 0
    explanation: str = ""
    improvements: List[str] = Field(default_factory=list)
    # Per-category evidence ("why this score") — one line each, project-specific.
    theme_reason: str = ""
    problem_reason: str = ""
    user_problem_reason: str = ""
    solution_reason: str = ""
    feasibility_reason: str = ""
    # Whether the deterministic one-pass strengthening touched the idea text.
    strengthened: bool = False


# --------------------------------------------------------------------------- #
# Persona adaptation (research objective #3)
# --------------------------------------------------------------------------- #
class PersonaPhase(BaseModel):
    """One ordered phase in a persona-adapted build plan.

    The underlying idea never changes across personas — only the depth and
    terminology of these guidance fields do (research objective #3).
    """

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    time_allocation: str = ""
    technologies: List[str] = Field(default_factory=list)
    guidance: str = ""
    expected_output: str = ""
    dependencies: List[str] = Field(default_factory=list)
    completion_criteria: str = ""


class PersonaAdaptedPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    persona: SkillLevel = SkillLevel.intermediate
    summary: str = ""
    phases: List[PersonaPhase] = Field(default_factory=list)
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
    """The complete, assembled documentation workspace (deterministic — no LLM).
    Every field is merged from validated agent state in `blueprint/assemble.py`.
    """

    model_config = ConfigDict(extra="ignore")

    # 1-9: identity + idea
    project_name: str = ""
    problem_statement: str = ""
    hackathon_theme: str = ""
    aim: str = ""
    objectives: List[str] = Field(default_factory=list)
    selected_idea: IdeaDraft
    core_features: List[str] = Field(default_factory=list)
    target_users: str = ""
    expected_impact: str = ""

    # 10-12: architecture + stack
    architecture: List[str] = Field(default_factory=list)
    recommended_stack: List[str] = Field(default_factory=list)
    stack_details: List[StackItem] = Field(default_factory=list)

    # 13-14: team + timeline
    team_allocation: List[MemberAllocation] = Field(default_factory=list)
    timeline: List[Milestone] = Field(default_factory=list)
    schedule: List[ScheduleTask] = Field(default_factory=list)

    # 15-19: procedure, deps, risks, testing
    implementation_procedure: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    technical_risks: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    testing_plan: List[str] = Field(default_factory=list)

    # 20-22: demo, pitch, future
    demo_flow: List[str] = Field(default_factory=list)
    value_proposition: str = ""
    differentiation: List[str] = Field(default_factory=list)
    pitch_structure: List[str] = Field(default_factory=list)
    future_scope: List[str] = Field(default_factory=list)
    mvp_features: List[str] = Field(default_factory=list)
    nice_to_have_features: List[str] = Field(default_factory=list)

    # alignment (kept for internal traceability; UI shows AlignmentReport)
    alignment_score: Optional[float] = None
    alignment_status: str = ""
    alignment_report: Optional[AlignmentReport] = None
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
    evaluations: Optional[List[IdeaEvaluation]] = None
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
