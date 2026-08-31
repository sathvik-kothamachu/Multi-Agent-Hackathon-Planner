"""ORM models. Only project metadata is stored relationally."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.database import Base


class ProjectRecord(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    problem_statement = Column(Text, nullable=False)
    hackathon_theme = Column(String, default="general")
    time_limit_hours = Column(Integer, default=24)
    preferences = Column(Text, default="")
    team_members_json = Column(Text, default="[]")
    status = Column(String, default="started")
    # Cached single-shot baseline for the ablation: {"plan": {...}, "metrics": {...}}
    baseline_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
