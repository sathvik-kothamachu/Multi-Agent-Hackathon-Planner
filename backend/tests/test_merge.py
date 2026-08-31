"""Unit tests for pure list-merge helpers used by blueprint assembly."""
from __future__ import annotations

from app.blueprint.merge import dedupe, merge_lists


def test_dedupe_preserves_order():
    assert dedupe(["a", "b", "c"]) == ["a", "b", "c"]


def test_dedupe_case_insensitive_keeps_first_casing():
    assert dedupe(["React", "react", "FastAPI"]) == ["React", "FastAPI"]


def test_dedupe_drops_empty_and_none():
    assert dedupe(["a", "", "   ", None, "b"]) == ["a", "b"]


def test_merge_lists_combines_and_dedupes():
    assert merge_lists(["React", "FastAPI"], ["fastapi", "SQLite"], None) == [
        "React",
        "FastAPI",
        "SQLite",
    ]


def test_merge_lists_all_empty():
    assert merge_lists([], None) == []
