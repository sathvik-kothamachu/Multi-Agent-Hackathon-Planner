"""Pure list-merge helpers for assembling the final blueprint.

Dependency-free so it is unit-testable offline. Used to combine
recommendations/stacks/risks emitted by different agents without duplicates.
"""
from __future__ import annotations

from typing import Iterable


def dedupe(items: Iterable[object]) -> list[str]:
    """Order-preserving de-duplication of strings.

    Drops None and empty/whitespace-only entries. Comparison is
    case-insensitive, but the first-seen casing is preserved.
    """
    out: list[str] = []
    seen: set[str] = set()
    for it in items or []:
        if it is None:
            continue
        s = str(it).strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def merge_lists(*lists: Iterable[object]) -> list[str]:
    """Concatenate several lists then de-duplicate, preserving first-seen order."""
    combined: list[object] = []
    for lst in lists:
        combined.extend(lst or [])
    return dedupe(combined)
