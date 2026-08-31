"""LLM helper utilities: deterministic token estimation + robust JSON extraction.

Token estimation is a cheap heuristic (~4 chars/token) so we can always report a
number even if the provider omits usage metadata. NEVER calls an LLM.
"""
from __future__ import annotations

import json
import re
from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough, deterministic token estimate (~4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def extract_json(text: str) -> Any:
    """Parse a JSON object from model text, tolerating markdown code fences and
    surrounding prose. Raises json.JSONDecodeError if nothing parseable is found.
    """
    if text is None:
        raise json.JSONDecodeError("empty response", "", 0)
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9]*", "", s).strip()
        if s.endswith("```"):
            s = s[:-3].strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", s, re.S)
        if match:
            return json.loads(match.group(0))
        raise
