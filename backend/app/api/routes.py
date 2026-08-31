"""Aggregate API router mounted under /api."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import projects

api_router = APIRouter(prefix="/api")
api_router.include_router(projects.router)
