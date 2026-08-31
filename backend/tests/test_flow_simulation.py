"""End-to-end simulation of the alignment-gated debate loop using ONLY the pure
logic modules (no LLM, no framework). Proves the loop converges, respects the
round cap, and can never spin forever — the core control-flow guarantee.
"""
from __future__ import annotations

from app.alignment.similarity import ALIGNED, DRIFT, classify, cosine
from app.workflow.routing import (
    ROUTE_FINALIZE,
    ROUTE_REDEBATE,
    decide_route,
    next_round,
)


def _simulate(scores, threshold=0.75, max_rounds=3):
    """Drive the loop with a pre-baked sequence of per-round alignment scores.

    Returns the visited (round, score, status) history. The last score is reused
    if the loop runs more rounds than scores provided.
    """
    rnd = 1
    history = []
    guard = 0
    while True:
        guard += 1
        assert guard <= max_rounds + 1, "loop exceeded the hard guard — would be infinite"
        score = scores[min(rnd - 1, len(scores) - 1)]
        status = classify(score, threshold)
        history.append((rnd, round(score, 3), status))
        route = decide_route(status, rnd, max_rounds)
        if route == ROUTE_FINALIZE:
            break
        assert route == ROUTE_REDEBATE
        rnd = next_round(rnd)
    return history


def test_converges_when_alignment_improves():
    hist = _simulate([0.60, 0.80])
    assert len(hist) == 2
    assert hist[-1][2] == ALIGNED


def test_immediate_alignment_single_round():
    hist = _simulate([0.90])
    assert len(hist) == 1
    assert hist[0][2] == ALIGNED


def test_stops_at_max_rounds_without_infinite_loop():
    hist = _simulate([0.10, 0.20, 0.30])  # never crosses threshold
    assert len(hist) == 3
    assert hist[-1][0] == 3
    assert hist[-1][2] == DRIFT  # ended in drift but controlled-stopped


def test_cosine_drives_classification_consistently():
    v = [0.1, 0.2, 0.3, 0.4]
    assert classify(cosine(v, v), 0.75) == ALIGNED
    assert classify(cosine(v, [-x for x in v]), 0.75) == DRIFT
