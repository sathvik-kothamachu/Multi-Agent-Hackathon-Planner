"""Centralized configuration via environment variables (pydantic-settings).

All tunable research knobs (alignment threshold, max debate rounds, max ideas)
live here so they are configurable and never hard-coded across the codebase.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---- LLM (single, configurable provider) ----
    llm_provider: str = "google"
    model_name: str = "gemini-1.5-flash"
    llm_api_key: str = ""
    llm_temperature: float = 0.4
    llm_max_retries: int = 1
    llm_request_timeout_s: int = 60

    # ---- Research knobs (configurable) ----
    alignment_threshold: float = 0.75
    max_debate_rounds: int = 3
    max_ideas: int = 3
    embedding_model: str = "all-MiniLM-L6-v2"

    # ---- Persistence ----
    database_url: str = "sqlite:///./hackathon_planner.db"
    checkpoint_db_path: str = "./checkpoints.sqlite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
