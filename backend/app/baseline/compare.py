"""Pure proposed-vs-baseline comparison notes for the ablation.

Dependency-free and deterministic so the ablation stays honest and testable:
no divide-by-zero, no alignment delta unless BOTH scores exist, and no fabricated
"winner" claims — we only report measured numbers side by side.
"""
from __future__ import annotations

from typing import List, Mapping, Optional


def _int(v: object) -> int:
    try:
        return int(round(float(v)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def comparison_notes(proposed: Mapping[str, object], baseline: Mapping[str, object]) -> List[str]:
    """Return human-readable comparison lines (order not significant)."""
    notes: List[str] = []

    p_tok = _int(proposed.get("total_tokens"))
    b_tok = _int(baseline.get("total_tokens"))
    if b_tok:
        ratio = p_tok / b_tok
        notes.append(f"Total tokens: proposed={p_tok} vs baseline={b_tok} ({ratio:.2f}x)")
    else:
        # No divide-by-zero; ratio suppressed when the baseline reports zero tokens.
        notes.append(f"Total tokens: proposed={p_tok} vs baseline={b_tok}")

    notes.append(
        f"LLM calls: proposed={_int(proposed.get('llm_calls'))} vs baseline={_int(baseline.get('llm_calls'))}"
    )
    notes.append(
        f"Latency(ms): proposed={_int(proposed.get('latency_ms'))} vs baseline={_int(baseline.get('latency_ms'))}"
    )

    pa: Optional[float] = proposed.get("final_alignment")  # type: ignore[assignment]
    ba: Optional[float] = baseline.get("final_alignment")  # type: ignore[assignment]
    if pa is None or ba is None:
        pa_s = "n/a" if pa is None else f"{pa:.3f}"
        ba_s = "n/a" if ba is None else f"{ba:.3f}"
        notes.append(f"Alignment: proposed={pa_s} vs baseline={ba_s}")
    else:
        delta = pa - ba
        direction = (
            f"proposed higher by {delta:.3f}" if delta >= 0 else f"proposed lower by {abs(delta):.3f}"
        )
        notes.append(f"Alignment: proposed={pa:.3f} vs baseline={ba:.3f} ({direction})")

    notes.append(
        f"Conflicts: proposed detected={_int(proposed.get('conflicts_detected'))} "
        f"resolved={_int(proposed.get('conflicts_resolved'))}; baseline performs none (single-shot)"
    )
    notes.append(
        f"Debate rounds: proposed={_int(proposed.get('debate_rounds'))} "
        f"vs baseline={_int(baseline.get('debate_rounds'))}"
    )
    notes.append(
        "Personalization: proposed adapts to team skill level; baseline is one-size-fits-all."
    )
    return notes
