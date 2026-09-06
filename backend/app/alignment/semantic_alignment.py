"""Semantic alignment gate (research objective #2).

Embeds the original problem statement and the current solution text with a
Sentence-Transformers model, then scores them with the deterministic cosine in
`similarity.py`. NO LLM is used for similarity. The embedding model is loaded
lazily and cached so repeated rounds do not reload it.

Robustness: if the Sentence-Transformers model cannot be loaded or run — e.g.
an offline first-use download, a missing/incompatible wheel, or the host getting
memory-pressured while loading torch — we degrade to a deterministic hashing
"bag-of-words" embedding instead of letting the exception (or a native OOM/crash)
take down the API process. The fallback is still pure cosine (no LLM), is clearly
logged, and is flagged in the result so its scores are not mistaken for the real
Sentence-Transformers metric. In normal operation the model loads and the
fallback never runs, so measured alignment is unchanged.
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import List, Tuple

import numpy as np

from app.alignment.similarity import classify, cosine
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.schemas import AlignmentResult

logger = get_logger(__name__)

# Fallback embedding config (only used when the real model is unavailable).
_FALLBACK_DIM = 512
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@lru_cache(maxsize=2)
def _load_model(name: str):
    from sentence_transformers import SentenceTransformer  # lazy heavy import

    logger.info("loading embedding model: %s", name)
    return SentenceTransformer(name)


def _fallback_vector(text: str) -> np.ndarray:
    """Deterministic hashing bag-of-words vector (numpy only, no network/torch).

    Tokens are lower-cased alphanumerics, each hashed (md5, process-independent
    unlike Python's salted hash) into a fixed-width vector. This yields a real
    lexical cosine — shared vocabulary between goal and solution scores higher —
    so the alignment gate keeps producing a meaningful, deterministic number even
    when the semantic model is unavailable.
    """
    vec = np.zeros(_FALLBACK_DIM, dtype=np.float32)
    for tok in _TOKEN_RE.findall(text.lower()):
        bucket = int.from_bytes(hashlib.md5(tok.encode()).digest()[:4], "little")
        vec[bucket % _FALLBACK_DIM] += 1.0
    return vec


def _embed(texts: List[str], settings: Settings) -> Tuple[np.ndarray, bool]:
    """Embed texts, returning (vectors, used_fallback).

    Never raises for model problems: any failure loading or running the
    Sentence-Transformers model is caught and served by the deterministic
    lexical fallback, so the alignment step can never 500 or crash the process.
    """
    try:
        model = _load_model(settings.embedding_model)
        return np.asarray(model.encode(list(texts))), False
    except Exception as exc:  # offline download, OOM, missing/ABI-mismatched wheel, ...
        logger.warning(
            "embedding model '%s' unavailable (%s: %s); using deterministic "
            "lexical fallback for alignment",
            settings.embedding_model,
            type(exc).__name__,
            exc,
        )
        return np.vstack([_fallback_vector(t) for t in texts]), True


def compute_alignment(
    problem_statement: str,
    solution_text: str,
    settings: Settings,
    debate_round: int = 1,
) -> AlignmentResult:
    """Score how well the current solution still matches the original goal."""
    vectors, used_fallback = _embed([problem_statement, solution_text], settings)
    score = cosine(vectors[0], vectors[1])
    status = classify(score, settings.alignment_threshold)
    reason = (
        "Solution stays aligned with the original goal."
        if status == "aligned"
        else "Solution has drifted from the original goal; re-debate to realign."
    )
    if used_fallback:
        reason += (
            " (lexical fallback embedding — Sentence-Transformers model unavailable)"
        )
    return AlignmentResult(
        alignment_score=float(score),
        threshold=settings.alignment_threshold,
        status=status,
        reason=reason,
        round=debate_round,
    )
