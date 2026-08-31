"""Pure persona-derivation logic (research objective #3).

Deterministic and dependency-free (no LLM) so it can be unit-tested offline and
never costs a token. Rule: the team persona is the LOWEST skill level present, so
guidance never over-assumes expertise the weakest member lacks. Unknown labels are
ignored; an empty/all-unknown team defaults to 'intermediate'.
"""
from __future__ import annotations

from typing import Iterable, Optional

# Ordinal rank; lower == less experienced == "wins" (drives more hand-holding).
RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}
ORDER = ["beginner", "intermediate", "advanced"]
DEFAULT = "intermediate"


def _norm(level: object) -> Optional[str]:
    if level is None:
        return None
    if hasattr(level, "value"):  # tolerate enum-like skill levels
        level = level.value
    s = str(level).strip().lower()
    return s if s in RANK else None


def derive_persona(skill_levels: Iterable[object]) -> str:
    """Return the effective team persona from a list of member skill levels."""
    ranks = [RANK[s] for s in (_norm(lv) for lv in (skill_levels or [])) if s is not None]
    if not ranks:
        return DEFAULT
    return ORDER[min(ranks)]
