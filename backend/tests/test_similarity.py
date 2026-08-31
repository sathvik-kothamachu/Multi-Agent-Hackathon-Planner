"""Unit tests for the deterministic cosine similarity + classification.

Guards research objective #2: alignment is pure math, never an LLM call.
"""
from __future__ import annotations

import math

from app.alignment.similarity import ALIGNED, DRIFT, classify, cosine


def test_identity_is_one():
    assert abs(cosine([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9


def test_orthogonal_is_zero():
    assert abs(cosine([1, 0], [0, 1])) < 1e-9


def test_opposite_is_negative_one():
    assert abs(cosine([1, 0], [-1, 0]) + 1.0) < 1e-9


def test_zero_vector_returns_zero_not_nan():
    v = cosine([0, 0, 0], [1, 2, 3])
    assert v == 0.0 and not math.isnan(v)


def test_scale_invariance():
    assert abs(cosine([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9


def test_classify_equal_threshold_is_aligned():
    assert classify(0.75, 0.75) == ALIGNED


def test_classify_below_is_drift():
    assert classify(0.7499, 0.75) == DRIFT


def test_classify_above_is_aligned():
    assert classify(0.9, 0.75) == ALIGNED
