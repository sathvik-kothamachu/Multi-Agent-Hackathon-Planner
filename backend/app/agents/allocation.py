"""Deterministic team task allocation (no LLM).

Assigns concrete responsibilities to each NAMED team member by matching their
declared skills against the recommended stack and the standard build tracks
(frontend, backend, data, integration, pitch/demo). Every assignment is tied to
a member's skills; primary tracks are not double-assigned. Because this is pure
Python it costs no tokens and is fully reproducible.
"""
from __future__ import annotations

from typing import Dict, List

from app.models.schemas import MemberAllocation, TeamProfile, TechAnalysis, TimelineAnalysis

# Canonical build tracks and the skill keywords that map to them.
_TRACKS: List[tuple[str, tuple[str, ...]]] = [
    ("Frontend & UI", ("react", "vue", "angular", "css", "html", "ui", "ux", "frontend", "javascript", "typescript", "tailwind")),
    ("Backend & API", ("python", "fastapi", "django", "flask", "node", "express", "java", "go", "backend", "api", "rest")),
    ("Data & Logic", ("sql", "sqlite", "postgres", "database", "data", "pandas", "ml", "ai", "analytics", "python")),
    ("Integration & DevOps", ("docker", "aws", "gcp", "azure", "devops", "ci", "deploy", "kubernetes", "git")),
    ("Pitch & Demo", ("design", "pitch", "presentation", "product", "writing", "communication", "figma")),
]


def _score(skills: List[str], keywords: tuple[str, ...]) -> int:
    blob = " ".join(skills).lower()
    return sum(1 for k in keywords if k in blob)


def allocate_tasks(
    team: TeamProfile,
    tech: TechAnalysis | None,
    timeline: TimelineAnalysis | None,
) -> List[MemberAllocation]:
    """Return one MemberAllocation per team member, skill-matched to a track."""
    members = getattr(team, "members", []) or []
    if not members:
        return []

    stack = list(tech.recommended_stack) if tech else []
    time_per = ""
    if timeline and timeline.available_hours:
        time_per = f"~{timeline.available_hours / max(len(members), 1):g}h of the build window"

    # Greedy: give each member their best-matching UNCLAIMED track; if all primary
    # tracks are taken, members share the highest-value track (co-owners).
    claimed: set[str] = set()
    allocations: List[MemberAllocation] = []
    for m in members:
        skills = getattr(m, "skills", []) or []
        ranked = sorted(_TRACKS, key=lambda t: _score(skills, t[1]), reverse=True)
        track = next((t for t in ranked if t[0] not in claimed), ranked[0])
        claimed.add(track[0])
        track_name, keywords = track
        # Technologies from the stack that align with this member's skills/track.
        techs = [s for s in stack if any(k in s.lower() for k in keywords)] or stack[:2]
        allocations.append(
            MemberAllocation(
                name=getattr(m, "name", "") or getattr(m, "role", "") or "Team member",
                role=getattr(m, "role", "") or track_name,
                skills=skills,
                responsibilities=[
                    f"Own the {track_name} track for the project.",
                    f"Build and integrate the {track_name.split(' &')[0].lower()} portion of the core flow.",
                ],
                technologies=techs,
                time_allocation=time_per,
            )
        )
    return allocations
