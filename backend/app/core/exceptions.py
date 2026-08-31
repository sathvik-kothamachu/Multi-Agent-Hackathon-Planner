"""Application error hierarchy mapped to HTTP status codes by the API layer."""
from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    status_code: int = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ValidationAppError(AppError):
    status_code = 422


class LLMError(AppError):
    """Raised when the LLM provider fails or returns unusable output."""

    status_code = 502
