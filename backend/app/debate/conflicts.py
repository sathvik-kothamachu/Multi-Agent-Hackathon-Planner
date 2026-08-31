"""Pure, dependency-free debate helpers.

Deterministic signal collection and conflict bookkeeping used by the arbiter node
and blueprint assembly. No LLM here — the LLM's job is to resolve conflicts, not
to count them.
"""
from __future__ import annotations

from typing import List, Tuple


def collect_flags(*analyses: object) -> List[str]:
    """Gather all cross_domain_flags emitted by the specialist agents."""
    flags: List[str] = []
    for a in analyses:
        if a is not None:
            flags.extend(getattr(a, "cross_domain_flags", []) or [])
    return flags


def count_conflicts(conflicts: List[object]) -> Tuple[int, int]:
    """Return (detected, resolved) counts for a list of Conflict-like objects."""
    total = len(conflicts or [])
    resolved = sum(1 for c in (conflicts or []) if getattr(c, "resolved", False))
    return total, resolved


def has_cross_domain_signal(*analyses: object) -> bool:
    """True if any specialist flagged a cross-domain concern worth debating."""
    return len(collect_flags(*analyses)) > 0
