"""Assemble the proposed-vs-baseline EvaluationReport.

Pure aggregation: pulls measured numbers from both runs and delegates the
human-readable side-by-side to compare.comparison_notes. No LLM, no fabrication.
"""
from __future__ import annotations

from app.baseline.compare import comparison_notes
from app.debate.conflicts import count_conflicts
from app.models.schemas import EvaluationReport, RunMetrics


def build_evaluation(
    project_id: str,
    proposed_values: dict,
    proposed_metrics: RunMetrics,
    baseline_metrics: RunMetrics,
) -> EvaluationReport:
    detected, resolved = count_conflicts(proposed_values.get("conflicts", []) or [])
    notes = comparison_notes(proposed_metrics.model_dump(), baseline_metrics.model_dump())
    return EvaluationReport(
        project_id=project_id,
        proposed_metrics=proposed_metrics,
        baseline_metrics=baseline_metrics,
        proposed_alignment=proposed_metrics.final_alignment,
        baseline_alignment=baseline_metrics.final_alignment,
        conflicts_detected=detected,
        conflicts_resolved=resolved,
        debate_rounds=proposed_values.get("debate_round", 0),
        notes=notes,
    )
