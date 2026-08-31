"""FastAPI dependencies: settings + a process-wide WorkflowRunner singleton.

The runner compiles the LangGraph and opens the checkpointer once; lru_cache keeps
a single instance so requests share the compiled graph.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.runner import WorkflowRunner


@lru_cache
def get_runner() -> WorkflowRunner:
    return WorkflowRunner(get_settings())


def get_settings_dep() -> Settings:
    return get_settings()
