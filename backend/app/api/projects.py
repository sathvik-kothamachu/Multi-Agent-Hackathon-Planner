"""Project endpoints — the human-in-the-loop workflow surface.

Route map (mounted under /api):
  POST   /projects                 create + generate ideas -> pause for review
  POST   /projects/{id}/regenerate regenerate ideas (loops back)
  POST   /projects/{id}/select     pick a candidate -> run to final blueprint
  POST   /projects/{id}/modify     pick an edited idea -> run to final blueprint
  GET    /projects/{id}/debate     tech/timeline/pitch analyses + conflicts + alignment history
  GET    /projects/{id}/blueprint  final blueprint + persona plan + metrics
  GET    /projects/{id}/metrics    token/latency/round metrics
  POST   /projects/{id}/persona    on-demand re-adaptation to a chosen skill level (non-mutating)
  POST   /projects/{id}/baseline   single-shot baseline (cached)
  POST   /projects/{id}/evaluation proposed-vs-baseline report
  GET    /projects                 list projects
"""
from __future__ import annotations

from typing import Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.persona_agent import adapt_persona
from app.alignment.semantic_alignment import compute_alignment
from app.api.deps import get_runner, get_settings_dep
from app.baseline.evaluate import build_evaluation
from app.baseline.single_shot import run_baseline
from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.db import repository
from app.db.database import get_session
from app.models.schemas import (
    Blueprint,
    EvaluationReport,
    ModifyIdeaRequest,
    PersonaAdaptedPlan,
    PersonaRequest,
    ProjectCreateRequest,
    RunMetrics,
    SelectIdeaRequest,
    TeamProfile,
    WorkflowStepResponse,
)
from app.services.runner import WorkflowRunner

router = APIRouter(prefix="/projects", tags=["projects"])


# --------------------------------------------------------------------------- #
# Serialization helpers — tolerate both pydantic objects and plain dicts,
# since the checkpointer may round-trip state either way.
# --------------------------------------------------------------------------- #
def _dump(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj


def _to_model(obj: Any, model_cls):
    if obj is None:
        return None
    if isinstance(obj, model_cls):
        return obj
    if hasattr(obj, "model_dump"):
        return model_cls.model_validate(obj.model_dump())
    return model_cls.model_validate(obj)


def _step_response(pid: str, values: dict, runner: WorkflowRunner) -> WorkflowStepResponse:
    return WorkflowStepResponse(
        project_id=pid,
        status=runner.status_of(values),
        ideas=values.get("candidate_ideas") or None,
        blueprint=values.get("final_plan"),
        persona_adapted_plan=values.get("persona_adapted_plan"),
        metrics=runner.metrics(values),
    )


def _require_record(db: Session, project_id: str):
    rec = repository.get_project(db, project_id)
    if rec is None:
        raise NotFoundError(f"Project '{project_id}' not found")
    return rec


def _baseline_metrics(plan, usage, problem_statement: str, settings: Settings) -> RunMetrics:
    solution = plan.solution_summary or plan.idea.solution
    align = compute_alignment(problem_statement, solution, settings).alignment_score
    return RunMetrics(
        mode="baseline",
        llm_calls=1,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        latency_ms=usage.latency_ms,
        debate_rounds=0,
        conflicts_detected=0,
        conflicts_resolved=0,
        initial_alignment=align,
        final_alignment=align,
    )


# --------------------------------------------------------------------------- #
# Lifecycle
# --------------------------------------------------------------------------- #
@router.post("", response_model=WorkflowStepResponse)
def create_project(
    req: ProjectCreateRequest,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> WorkflowStepResponse:
    pid = uuid4().hex
    repository.create_project(db, pid, req)
    values = runner.start(pid, req)
    repository.set_status(db, pid, runner.status_of(values))
    return _step_response(pid, values, runner)


@router.post("/{project_id}/regenerate", response_model=WorkflowStepResponse)
def regenerate_ideas(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> WorkflowStepResponse:
    _require_record(db, project_id)
    values = runner.regenerate(project_id)
    repository.set_status(db, project_id, runner.status_of(values))
    return _step_response(project_id, values, runner)


@router.post("/{project_id}/select", response_model=WorkflowStepResponse)
def select_idea(
    project_id: str,
    body: SelectIdeaRequest,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> WorkflowStepResponse:
    _require_record(db, project_id)
    values = runner.select(project_id, body.idea_id)
    repository.set_status(db, project_id, runner.status_of(values))
    return _step_response(project_id, values, runner)


@router.post("/{project_id}/modify", response_model=WorkflowStepResponse)
def modify_idea(
    project_id: str,
    body: ModifyIdeaRequest,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> WorkflowStepResponse:
    _require_record(db, project_id)
    values = runner.modify(project_id, body.idea.model_dump())
    repository.set_status(db, project_id, runner.status_of(values))
    return _step_response(project_id, values, runner)


# --------------------------------------------------------------------------- #
# Views
# --------------------------------------------------------------------------- #
@router.get("/{project_id}/debate")
def get_debate(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> dict:
    _require_record(db, project_id)
    values = runner.values(project_id)
    return {
        "project_id": project_id,
        "status": runner.status_of(values),
        "tech_analysis": _dump(values.get("tech_analysis")),
        "timeline_analysis": _dump(values.get("timeline_analysis")),
        "pitch_analysis": _dump(values.get("pitch_analysis")),
        "conflicts": [_dump(c) for c in values.get("conflicts", []) or []],
        "revision_directives": [_dump(d) for d in values.get("revision_directives", []) or []],
        "alignment_score": values.get("alignment_score"),
        "alignment_status": values.get("alignment_status", ""),
        "alignment_history": values.get("alignment_history", []) or [],
        "debate_round": values.get("debate_round", 0),
    }


@router.get("/{project_id}/blueprint", response_model=WorkflowStepResponse)
def get_blueprint(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> WorkflowStepResponse:
    _require_record(db, project_id)
    values = runner.values(project_id)
    if not values.get("final_plan"):
        raise NotFoundError("Blueprint not ready — select an idea to run the workflow first")
    return _step_response(project_id, values, runner)


@router.get("/{project_id}/metrics", response_model=RunMetrics)
def get_metrics(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
) -> RunMetrics:
    _require_record(db, project_id)
    return runner.metrics(runner.values(project_id))


# --------------------------------------------------------------------------- #
# Persona comparison (research objective #3) — non-mutating re-adaptation
# --------------------------------------------------------------------------- #
@router.post("/{project_id}/persona", response_model=PersonaAdaptedPlan)
def adapt_to_persona(
    project_id: str,
    body: PersonaRequest,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
    settings: Settings = Depends(get_settings_dep),
) -> PersonaAdaptedPlan:
    _require_record(db, project_id)
    values = runner.values(project_id)
    if not values.get("final_plan"):
        raise ValidationAppError("Run the workflow to completion before comparing personas")
    blueprint = _to_model(values["final_plan"], Blueprint)
    # Explicit override wins over derivation, so members are not needed here.
    tmp_state = {
        "final_plan": blueprint,
        "team_profile": TeamProfile(members=[], overall_persona=body.persona),
    }
    plan, _usage = adapt_persona(tmp_state, runner.client, settings)
    return plan


# --------------------------------------------------------------------------- #
# Baseline + evaluation (research requirement #16)
# --------------------------------------------------------------------------- #
@router.post("/{project_id}/baseline")
def run_project_baseline(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
    settings: Settings = Depends(get_settings_dep),
) -> dict:
    rec = _require_record(db, project_id)
    plan, usage = run_baseline(
        rec.problem_statement,
        rec.hackathon_theme,
        rec.time_limit_hours,
        rec.preferences or "",
        runner.client,
        settings,
    )
    metrics = _baseline_metrics(plan, usage, rec.problem_statement, settings)
    repository.set_baseline(
        db,
        project_id,
        {"plan": plan.model_dump(mode="json"), "metrics": metrics.model_dump(mode="json")},
    )
    return {"project_id": project_id, "plan": plan, "metrics": metrics}


@router.post("/{project_id}/evaluation", response_model=EvaluationReport)
def get_evaluation(
    project_id: str,
    db: Session = Depends(get_session),
    runner: WorkflowRunner = Depends(get_runner),
    settings: Settings = Depends(get_settings_dep),
) -> EvaluationReport:
    rec = _require_record(db, project_id)
    values = runner.values(project_id)
    if not values.get("final_plan"):
        raise ValidationAppError("Run the proposed workflow to completion before evaluating")
    proposed_metrics = runner.metrics(values, mode="proposed")

    cached = repository.get_baseline(db, project_id)
    if cached is not None:
        baseline_metrics = RunMetrics.model_validate(cached["metrics"])
    else:
        plan, usage = run_baseline(
            rec.problem_statement,
            rec.hackathon_theme,
            rec.time_limit_hours,
            rec.preferences or "",
            runner.client,
            settings,
        )
        baseline_metrics = _baseline_metrics(plan, usage, rec.problem_statement, settings)
        repository.set_baseline(
            db,
            project_id,
            {"plan": plan.model_dump(mode="json"), "metrics": baseline_metrics.model_dump(mode="json")},
        )

    return build_evaluation(project_id, values, proposed_metrics, baseline_metrics)


# --------------------------------------------------------------------------- #
# Listing
# --------------------------------------------------------------------------- #
@router.get("")
def list_all_projects(db: Session = Depends(get_session)) -> List[dict]:
    return [
        {
            "id": r.id,
            "status": r.status,
            "problem_statement": r.problem_statement,
            "hackathon_theme": r.hackathon_theme,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in repository.list_projects(db)
    ]
