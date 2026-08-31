"""End-to-end graph test (requires the real deps; skipped otherwise).

Guarded with importorskip so it NEVER runs in the offline stdlib runner — it is
intentionally excluded from tests/run_offline.py's TEST_MODULES. Uses the mock LLM
provider so it needs no API key and stays deterministic.

Covers: human-in-the-loop interrupt after idea generation, resume-by-select
running through debate -> alignment -> assemble -> persona, and the regenerate loop.
"""
import pytest

pytest.importorskip("langgraph")
pytest.importorskip("pydantic")
pytest.importorskip("langgraph.checkpoint.sqlite")

from app.core.config import Settings  # noqa: E402
from app.models.schemas import ProjectCreateRequest, TeamMember  # noqa: E402
from app.services.runner import WorkflowRunner  # noqa: E402


def _settings(tmp_path) -> Settings:
    return Settings(
        llm_provider="mock",
        checkpoint_db_path=str(tmp_path / "cp.sqlite"),
        database_url=f"sqlite:///{tmp_path / 'app.db'}",
    )


def test_hitl_interrupt_then_select_produces_blueprint(tmp_path):
    runner = WorkflowRunner(_settings(tmp_path))
    req = ProjectCreateRequest(
        problem_statement="Help campus commuters find open parking spots in real time",
        hackathon_theme="smart city",
        time_limit_hours=24,
        team_members=[TeamMember(role="developer", skill_level="beginner")],
    )
    pid = "itest-select"

    values = runner.start(pid, req)
    ideas = values.get("candidate_ideas")
    assert ideas, "workflow should pause at human review with candidate ideas"
    assert len(ideas) <= 3
    assert runner.status_of(values) == "awaiting_selection"
    assert values.get("final_plan") is None

    first = ideas[0]
    idea_id = getattr(first, "id", None) or first["id"]
    done = runner.select(pid, idea_id)

    assert done.get("final_plan") is not None
    assert done.get("persona_adapted_plan") is not None
    assert runner.status_of(done) == "completed"

    m = runner.metrics(done)
    assert m.llm_calls >= 1
    assert m.total_tokens > 0
    assert 1 <= m.debate_rounds <= 3  # bounded loop, never infinite


def test_regenerate_loops_back_to_review(tmp_path):
    runner = WorkflowRunner(_settings(tmp_path))
    req = ProjectCreateRequest(problem_statement="Reduce food waste in dorm cafeterias")
    pid = "itest-regen"

    runner.start(pid, req)
    values = runner.regenerate(pid)

    assert values.get("candidate_ideas")
    assert values.get("final_plan") is None
    assert runner.status_of(values) == "awaiting_selection"
