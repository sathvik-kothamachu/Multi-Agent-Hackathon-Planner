"""WorkflowRunner — thin orchestration around the compiled LangGraph.

Owns the (single, configurable) LLM client, the SQLite checkpointer, and the
compiled graph. Exposes start / regenerate / select / modify / get_state and
derives RunMetrics from the accumulated usage_log. thread_id == project_id, so
the human-review interrupt resumes exactly where it paused.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional

from app.core.config import Settings
from app.core.logging import get_logger
from app.debate.conflicts import count_conflicts
from app.llm.provider import get_llm_client
from app.models.schemas import ProjectCreateRequest, RunMetrics, TeamProfile
from app.workflow.graph import build_graph

logger = get_logger(__name__)


class WorkflowRunner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = get_llm_client(settings)

        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect(settings.checkpoint_db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(conn)
        self.graph = build_graph(self.client, self.settings, self.checkpointer)

    # ---- config helpers ------------------------------------------------- #
    def _config(self, project_id: str) -> dict:
        return {"configurable": {"thread_id": project_id}}

    def values(self, project_id: str) -> dict:
        """Current merged channel values for a project (may be empty)."""
        snapshot = self.graph.get_state(self._config(project_id))
        return dict(snapshot.values) if snapshot and snapshot.values else {}

    # ---- lifecycle ------------------------------------------------------ #
    def start(self, project_id: str, req: ProjectCreateRequest) -> dict:
        profile = TeamProfile(members=req.team_members)
        inputs = {
            "project_id": project_id,
            "problem_statement": req.problem_statement,
            "hackathon_theme": req.hackathon_theme,
            "time_limit_hours": req.time_limit_hours,
            "preferences": req.preferences,
            "team_profile": profile,
            "usage_log": [],
            "alignment_history": [],
        }
        self.graph.invoke(inputs, self._config(project_id))
        return self.values(project_id)

    def _resume(self, project_id: str, decision: dict) -> dict:
        from langgraph.types import Command

        self.graph.invoke(Command(resume=decision), self._config(project_id))
        return self.values(project_id)

    def regenerate(self, project_id: str) -> dict:
        return self._resume(project_id, {"action": "regenerate"})

    def select(self, project_id: str, idea_id: str) -> dict:
        return self._resume(project_id, {"action": "select", "idea_id": idea_id})

    def modify(self, project_id: str, idea: dict) -> dict:
        return self._resume(project_id, {"action": "modify", "idea": idea})

    # ---- derived views -------------------------------------------------- #
    @staticmethod
    def status_of(values: dict) -> str:
        if values.get("final_plan") is not None:
            return "completed"
        if values.get("candidate_ideas"):
            return "awaiting_selection"
        return "started"

    def metrics(self, values: dict, mode: str = "proposed") -> RunMetrics:
        log: List[Dict] = values.get("usage_log", []) or []
        input_tokens = sum(int(u.get("input_tokens", 0)) for u in log)
        output_tokens = sum(int(u.get("output_tokens", 0)) for u in log)
        latency = sum(float(u.get("latency_ms", 0.0)) for u in log)
        detected, resolved = count_conflicts(values.get("conflicts", []))
        return RunMetrics(
            mode=mode,
            llm_calls=len(log),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            debate_rounds=values.get("debate_round", 0),
            conflicts_detected=detected,
            conflicts_resolved=resolved,
            initial_alignment=values.get("initial_alignment"),
            final_alignment=values.get("alignment_score"),
        )
