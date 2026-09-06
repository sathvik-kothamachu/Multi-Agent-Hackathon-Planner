"""Deterministic idea de-duplication (no LLM).

Regenerate must never return an idea the project has already seen. We reject a
freshly generated idea if its title is a normalized match OR its text is
semantically too close to any prior idea. Similarity reuses the SAME embedding +
cosine path as the alignment gate (Sentence-Transformers with a deterministic
lexical fallback), so no extra LLM call is spent and it works offline.
"""
from __future__ import annotations

import re
from typing import List

from app.alignment.semantic_alignment import _embed  # embedding + fallback
from app.alignment.similarity import cosine
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.schemas import IdeaDraft

logger = get_logger(__name__)

# Above this cosine, two idea descriptions are treated as the same concept.
_DUP_SIM = 0.86
_WORD_RE = re.compile(r"[a-z0-9]+")


def _norm_title(title: str) -> str:
    return " ".join(_WORD_RE.findall((title or "").lower()))


def _idea_text(idea: IdeaDraft) -> str:
    return f"{idea.title}. {idea.problem} {idea.solution}".strip()


def dedupe_against_history(
    fresh: List[IdeaDraft], history: List[IdeaDraft], settings: Settings
) -> List[IdeaDraft]:
    """Return the subset of `fresh` that is distinct from `history` AND each other.

    Title match is exact-after-normalization; concept match uses cosine over the
    embedded idea text. Robust to embedding failure (falls back to title-only).
    """
    if not fresh:
        return []
    seen_titles = {_norm_title(i.title) for i in history}
    kept: List[IdeaDraft] = []

    # Embed everything once; degrade to title-only dedup if embedding is unusable.
    try:
        corpus = [_idea_text(i) for i in history] + [_idea_text(i) for i in fresh]
        vectors, _ = _embed(corpus, settings)
        hist_vecs = vectors[: len(history)]
        fresh_vecs = vectors[len(history) :]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("dedup embedding failed (%s); title-only dedup", exc)
        hist_vecs = fresh_vecs = None

    kept_vecs: List = []
    for idx, idea in enumerate(fresh):
        nt = _norm_title(idea.title)
        if nt and nt in seen_titles:
            continue
        if fresh_vecs is not None:
            v = fresh_vecs[idx]
            compare = list(hist_vecs) + kept_vecs
            if any(cosine(v, other) >= _DUP_SIM for other in compare):
                continue
            kept_vecs.append(v)
        kept.append(idea)
        if nt:
            seen_titles.add(nt)
    return kept
