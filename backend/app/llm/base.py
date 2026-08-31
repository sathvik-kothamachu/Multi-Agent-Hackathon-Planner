"""LLM client base: one narrow interface + validated, typed generation.

`generate()` is the only method agents use. It runs the provider, extracts JSON,
validates it against a Pydantic schema, and returns (model, usage) so token cost
is always tracked. Concrete providers implement only `_raw_generate`.
"""
from __future__ import annotations

import abc
import json
from dataclasses import dataclass
from typing import Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import LLMError
from app.llm.utils import extract_json

T = TypeVar("T", bound=BaseModel)


@dataclass
class CallUsage:
    """Token + latency accounting for a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def as_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
        }


class LLMClient(abc.ABC):
    def __init__(self, settings: Settings):
        self.settings = settings

    @abc.abstractmethod
    def _raw_generate(
        self, *, system: str, user: str, schema: Type[BaseModel], max_output_tokens: int
    ) -> Tuple[str, CallUsage]:
        """Return (raw_text, usage). Provider-specific."""
        raise NotImplementedError

    def generate(
        self, *, system: str, user: str, schema: Type[T], max_output_tokens: int = 700
    ) -> Tuple[T, CallUsage]:
        """Generate, parse JSON, and validate against `schema`."""
        text, usage = self._raw_generate(
            system=system, user=user, schema=schema, max_output_tokens=max_output_tokens
        )
        try:
            data = extract_json(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"{schema.__name__}: response was not valid JSON") from exc
        try:
            model = schema.model_validate(data)
        except ValidationError as exc:
            raise LLMError(f"{schema.__name__}: validation failed: {exc}") from exc
        return model, usage
