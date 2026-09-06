"""Data-access helpers for ProjectRecord. Thin, typed, no business logic."""
from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import ProjectRecord
from app.models.schemas import ProjectCreateRequest, TeamMember


def create_project(db: Session, project_id: str, req: ProjectCreateRequest) -> ProjectRecord:
    rec = ProjectRecord(
        id=project_id,
        problem_statement=req.problem_statement,
        hackathon_theme=req.hackathon_theme,
        time_limit_hours=req.time_limit_hours,
        preferences=req.preferences,
        team_members_json=json.dumps([m.model_dump(mode="json") for m in req.team_members]),
        using_ai=1 if req.using_ai else 0,
        status="awaiting_selection",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def get_project(db: Session, project_id: str) -> Optional[ProjectRecord]:
    return db.get(ProjectRecord, project_id)


def list_projects(db: Session) -> List[ProjectRecord]:
    return list(db.query(ProjectRecord).order_by(ProjectRecord.created_at.desc()).all())


def set_status(db: Session, project_id: str, status: str) -> None:
    rec = db.get(ProjectRecord, project_id)
    if rec is not None:
        rec.status = status
        db.commit()


def set_baseline(db: Session, project_id: str, baseline: dict) -> None:
    rec = db.get(ProjectRecord, project_id)
    if rec is not None:
        rec.baseline_json = json.dumps(baseline)
        db.commit()


def get_baseline(db: Session, project_id: str) -> Optional[dict]:
    rec = db.get(ProjectRecord, project_id)
    if rec is None or not rec.baseline_json:
        return None
    return json.loads(rec.baseline_json)


def to_request(rec: ProjectRecord) -> ProjectCreateRequest:
    """Reconstruct the original create request from a stored record."""
    members = [TeamMember.model_validate(m) for m in json.loads(rec.team_members_json or "[]")]
    return ProjectCreateRequest(
        problem_statement=rec.problem_statement,
        hackathon_theme=rec.hackathon_theme,
        time_limit_hours=rec.time_limit_hours,
        preferences=rec.preferences or "",
        team_members=members,
        using_ai=bool(getattr(rec, "using_ai", 1)),
    )
