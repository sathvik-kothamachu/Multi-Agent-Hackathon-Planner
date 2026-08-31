"""Unit tests for the pure proposed-vs-baseline comparison notes.

Guards the properties that keep the ablation honest: no divide-by-zero, no
alignment delta unless BOTH scores exist, and no fabricated 'winner' claims.
"""
from __future__ import annotations

from app.baseline.compare import comparison_notes

PROPOSED = {
    "total_tokens": 4200,
    "llm_calls": 6,
    "latency_ms": 5300.0,
    "final_alignment": 0.82,
    "conflicts_detected": 3,
    "conflicts_resolved": 3,
    "debate_rounds": 2,
}
BASELINE = {
    "total_tokens": 1400,
    "llm_calls": 1,
    "latency_ms": 1200.0,
    "final_alignment": 0.71,
    "conflicts_detected": 0,
    "conflicts_resolved": 0,
    "debate_rounds": 1,
}


def _joined(notes):
    return "\n".join(notes)


def test_token_ratio_present_when_baseline_nonzero():
    text = _joined(comparison_notes(PROPOSED, BASELINE))
    assert "proposed=4200" in text and "baseline=1400" in text
    assert "3.00x" in text  # 4200 / 1400


def test_zero_baseline_tokens_does_not_divide():
    notes = comparison_notes(PROPOSED, {**BASELINE, "total_tokens": 0})
    text = _joined(notes)
    assert "baseline=0" in text
    assert "x)" not in text  # ratio line is suppressed, no crash


def test_alignment_delta_only_when_both_present():
    text = _joined(comparison_notes(PROPOSED, BASELINE))
    assert "proposed higher by 0.110" in text


def test_no_delta_when_alignment_missing():
    p = {**PROPOSED, "final_alignment": None}
    text = _joined(comparison_notes(p, BASELINE))
    assert "n/a" in text
    assert "higher by" not in text and "lower by" not in text


def test_reports_conflicts_rounds_and_personalization():
    text = _joined(comparison_notes(PROPOSED, BASELINE))
    assert "detected=3" in text and "resolved=3" in text
    assert "baseline performs none" in text
    assert "Debate rounds: proposed=2 vs baseline=1" in text
    assert "Personalization" in text


def test_llm_calls_and_latency_lines():
    text = _joined(comparison_notes(PROPOSED, BASELINE))
    assert "LLM calls: proposed=6 vs baseline=1" in text
    assert "Latency(ms): proposed=5300 vs baseline=1200" in text
