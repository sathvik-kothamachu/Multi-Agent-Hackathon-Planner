"""Semantic alignment gate (research objective #2).

Embeds the original problem statement and the current solution text with a
Sentence-Transformers model, then scores them with the deterministic cosine in
`similarity.py`. NO LLM is used for similarity. The embedding model is loaded
lazily and cached so repeated rounds do not reload it.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from app.alignment.similarity import classify, cosine
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.schemas import AlignmentResult

logger = get_logger(__name__)


@lru_cache(maxsize=2)
def _load_model(name: str):
    from sentence_transformers import SentenceTransformer  # lazy heavy import

    logger.info("loading embedding model: %s", name)
    return SentenceTransformer(name)


def _embed(texts: List[str], settings: Settings):
    model = _load_model(settings.embedding_model)
    return model.encode(list(texts))


def compute_alignment(
    problem_statement: str,
    solution_text: str,
    settings: Settings,
    debate_round: int = 1,
) -> AlignmentResult:
    """Score how well the current solution still matches the original goal."""
    vectors = _embed([problem_statement, solution_text], settings)
    score = cosine(vectors[0], vectors[1])
    status = classify(score, settings.alignment_threshold)
    reason = (
        "Solution stays aligned with the original goal."
        if status == "aligned"
        else "Solution has drifted from the original goal; re-debate to realign."
    )
    return AlignmentResult(
        alignment_score=float(score),
        threshold=settings.alignment_threshold,
        status=status,
        reason=reason,
        round=debate_round,
    )
