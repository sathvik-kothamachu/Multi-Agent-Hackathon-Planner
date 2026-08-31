"""LLM provider factory — one configurable provider (research requirement #8).

`mock` needs no key/network and powers offline runs, tests, and demos. `google`
(Gemini) is the default real provider and is imported lazily so the mock path has
zero heavy dependencies.
"""
from __future__ import annotations

from app.core.config import Settings
from app.llm.base import LLMClient
from app.llm.mock_client import MockLLMClient


def get_llm_client(settings: Settings) -> LLMClient:
    provider = (settings.llm_provider or "").strip().lower()
    if provider in ("mock", "test", "fake", "offline"):
        return MockLLMClient(settings)
    if provider in ("google", "gemini"):
        from app.llm.google_client import GoogleLLMClient  # lazy: heavy import

        return GoogleLLMClient(settings)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
