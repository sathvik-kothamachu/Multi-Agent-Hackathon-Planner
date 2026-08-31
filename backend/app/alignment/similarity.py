"""Deterministic cosine similarity + alignment classification.

Pure math — NO LLM is ever used to compute similarity (research objective #2).
Import-clean (numpy only) so it runs offline and in unit tests without the LLM/
framework stack. The embedding model that produces the vectors lives in
`semantic_alignment.py`; this module only scores vectors that already exist.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

# Alignment status labels (shared with routing).
ALIGNED = "aligned"
DRIFT = "drift"


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors.

    Returns 0.0 if either vector has zero magnitude (undefined direction) instead
    of raising — keeps the alignment gate robust to degenerate embeddings.
    """
    va = np.asarray(a, dtype=float).ravel()
    vb = np.asarray(b, dtype=float).ravel()
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def classify(score: float, threshold: float) -> str:
    """At/above threshold is ALIGNED; strictly below is DRIFT (equality passes)."""
    return ALIGNED if score >= threshold else DRIFT
