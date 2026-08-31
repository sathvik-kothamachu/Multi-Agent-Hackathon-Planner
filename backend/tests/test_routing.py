"""Unit tests for the pure routing logic (loop control, never an LLM).

Guards research objective #1/#2 control flow: bounded rounds, no infinite loop,
and re-debate targets only the agents the arbiter asked to revise.
"""
from __future__ import annotations

from app.alignment.similarity import ALIGNED, DRIFT
from app.workflow.routing import (
    MAX_ROUNDS_EXCEEDED,
    ROUTE_FINALIZE,
    ROUTE_REDEBATE,
    decide_route,
    is_max_rounds,
    next_agents,
    next_round,
    terminal_status,
)


def test_is_max_rounds():
    assert is_max_rounds(3, 3) is True
    assert is_max_rounds(4, 3) is True
    assert is_max_rounds(2, 3) is False


def test_next_round_increments():
    assert next_round(1) == 2


def test_terminal_status():
    assert terminal_status(ALIGNED) is True
    assert terminal_status(MAX_ROUNDS_EXCEEDED) is True
    assert terminal_status(DRIFT) is False


def test_decide_route_aligned_finalizes():
    assert decide_route(ALIGNED, 1, 3) == ROUTE_FINALIZE


def test_decide_route_drift_redebates_when_rounds_remain():
    assert decide_route(DRIFT, 1, 3) == ROUTE_REDEBATE


def test_decide_route_drift_finalizes_at_cap():
    assert decide_route(DRIFT, 3, 3) == ROUTE_FINALIZE


def test_next_agents_dedupes_filters_and_lowercases():
    directives = [
        {"agent": "tech", "change": "a"},
        {"agent": "Tech", "change": "b"},   # case-duplicate
        {"agent": "pitch", "change": "c"},
        {"agent": "database", "change": "d"},  # not a valid agent
        {"change": "no agent key"},            # skipped
    ]
    assert next_agents(directives) == ["tech", "pitch"]


class _Directive:
    def __init__(self, agent):
        self.agent = agent


def test_next_agents_accepts_objects_and_enum_like():
    class _Enum:
        value = "timeline"

    assert next_agents([_Directive("timeline"), _Directive(_Enum())]) == ["timeline"]


def test_next_agents_empty():
    assert next_agents([]) == []
    assert next_agents(None) == []
