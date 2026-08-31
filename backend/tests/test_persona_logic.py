"""Unit tests for pure persona derivation (research objective #3, no LLM)."""
from __future__ import annotations

from app.agents.persona_logic import DEFAULT, derive_persona


def test_lowest_skill_wins():
    assert derive_persona(["advanced", "beginner", "intermediate"]) == "beginner"


def test_all_advanced():
    assert derive_persona(["advanced", "advanced"]) == "advanced"


def test_intermediate_when_mixed_without_beginner():
    assert derive_persona(["advanced", "intermediate"]) == "intermediate"


def test_empty_defaults_intermediate():
    assert derive_persona([]) == DEFAULT
    assert derive_persona(None) == DEFAULT


def test_unknowns_ignored():
    assert derive_persona(["wizard", "advanced"]) == "advanced"


def test_all_unknown_defaults():
    assert derive_persona(["wizard", "ninja"]) == DEFAULT


def test_enum_like_values():
    class _Level:
        def __init__(self, v):
            self.value = v

    assert derive_persona([_Level("intermediate"), _Level("beginner")]) == "beginner"
