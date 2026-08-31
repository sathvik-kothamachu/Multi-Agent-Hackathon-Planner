"""Google Gemini provider (default real LLM).

Requests JSON output, prefers provider-reported token usage, and falls back to a
heuristic estimate so metrics are never empty. The API key comes only from
settings/env — it is never logged.
"""
from __future__ import annotations

import time
from typing import Tuple, Type

from pydantic import BaseModel

from app.core.config import Settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.llm.base import CallUsage, LLMClient
from app.llm.utils import estimate_tokens

logger = get_logger(__name__)


class GoogleLLMClient(LLMClient):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        if not settings.llm_api_key:
            raise LLMError("LLM_API_KEY is not set for provider 'google'.")
        import google.generativeai as genai  # lazy import

        genai.configure(api_key=settings.llm_api_key)
        self._genai = genai
        self._model = genai.GenerativeModel(settings.model_name)

    def _raw_generate(
        self, *, system: str, user: str, schema: Type[BaseModel], max_output_tokens: int
    ) -> Tuple[str, CallUsage]:
        field_hint = ", ".join(schema.model_fields.keys())
        prompt = (
            f"{system}\n\n"
            f"Respond with ONLY minified JSON containing these top-level keys: {field_hint}.\n\n"
            f"{user}"
        )
        t0 = time.time()
        try:
            resp = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.settings.llm_temperature,
                    "max_output_tokens": max_output_tokens,
                    "response_mime_type": "application/json",
                },
            )
            text = getattr(resp, "text", None) or "{}"
        except Exception as exc:  # noqa: BLE001 - normalize provider/network errors
            raise LLMError(f"Google LLM call failed: {exc}") from exc
        latency_ms = (time.time() - t0) * 1000.0

        input_tokens = output_tokens = 0
        meta = getattr(resp, "usage_metadata", None)
        if meta is not None:
            input_tokens = int(getattr(meta, "prompt_token_count", 0) or 0)
            output_tokens = int(getattr(meta, "candidates_token_count", 0) or 0)
        if not input_tokens:
            input_tokens = estimate_tokens(prompt)
        if not output_tokens:
            output_tokens = estimate_tokens(text)

        logger.info(
            "gemini call schema=%s in=%d out=%d latency_ms=%.0f",
            schema.__name__,
            input_tokens,
            output_tokens,
            latency_ms,
        )
        return text, CallUsage(
            input_tokens=input_tokens, output_tokens=output_tokens, latency_ms=latency_ms
        )
