"""Deterministic offline/test LLM double.

Enabled with LLM_PROVIDER=mock. Produces schema-valid canned JSON so the full
pipeline (and tests) can run without network or an API key. This is a TEST
DOUBLE, not a source of research results — real experiments use a real provider.
Some fields react to keywords in the prompt (e.g. 'real-time', 'ml', 'blockchain')
so the debate/alignment stages have realistic material to work on.
"""
from __future__ import annotations

import json
import re
from typing import Type

from pydantic import BaseModel

from app.core.config import Settings
from app.llm.base import CallUsage, LLMClient
from app.llm.utils import estimate_tokens


def _field(user: str, label: str, default: str = "") -> str:
    m = re.search(rf"{label}:\s*(.+)", user, re.IGNORECASE)
    return m.group(1).strip() if m else default


class MockLLMClient(LLMClient):
    def _raw_generate(
        self, *, system: str, user: str, schema: Type[BaseModel], max_output_tokens: int
    ) -> tuple[str, CallUsage]:
        payload = self._payload_for(schema.__name__, user)
        text = json.dumps(payload)
        usage = CallUsage(
            input_tokens=estimate_tokens(system + user),
            output_tokens=estimate_tokens(text),
            latency_ms=1.0,
        )
        return text, usage

    def _payload_for(self, name: str, user: str) -> dict:
        problem = _field(user, "Problem", "the stated problem")[:160]
        theme = _field(user, "Theme", "general")
        heavy = bool(re.search(r"real-?time|\bml\b|machine learning|blockchain|deep learning", user, re.I))

        if name == "IdeaGenerationOutput":
            base = {
                "problem": problem,
                "target_users": "hackathon judges and early adopters",
            }
            return {
                "ideas": [
                    {
                        "title": f"{theme.title()} Helper",
                        "solution": "A focused web app that solves the core problem with a simple, demoable flow.",
                        "rationale": "Small scope, high clarity, buildable in the time limit.",
                        **base,
                    },
                    {
                        "title": f"{theme.title()} Assistant",
                        "solution": "A guided assistant that automates the most painful manual step.",
                        "rationale": "Clear value proposition and an obvious live demo.",
                        **base,
                    },
                    {
                        "title": f"{theme.title()} Dashboard",
                        "solution": "A dashboard that surfaces the key insight behind the problem.",
                        "rationale": "Visual, judge-friendly, and technically modest.",
                        **base,
                    },
                ]
            }

        if name == "TechAnalysis":
            return {
                "feasibility": "medium" if heavy else "high",
                "complexity": "high" if heavy else "low",
                "recommended_stack": ["React", "FastAPI", "SQLite"],
                "architecture": ["SPA frontend", "REST API", "single service", "SQLite store"],
                "technical_risks": (
                    ["Model/real-time component may not finish in time"] if heavy else ["Scope creep"]
                ),
                "recommendations": (
                    ["Replace heavy ML/real-time part with a rule-based or pre-trained shortcut"]
                    if heavy
                    else ["Keep the stack minimal and pre-scaffold"]
                ),
                "critique": ["Ensure the core demo path works end-to-end first"],
                "cross_domain_flags": (
                    ["Timeline: advanced component conflicts with short duration"] if heavy else []
                ),
            }

        if name == "TimelineAnalysis":
            return {
                "feasible": not heavy,
                "milestones": [
                    {"name": "Setup & scaffold", "duration": "0-2h", "dependencies": [], "deliverables": ["repo", "skeleton"]},
                    {"name": "Core feature", "duration": "2-8h", "dependencies": ["Setup & scaffold"], "deliverables": ["main flow"]},
                    {"name": "Polish & demo", "duration": "8-12h", "dependencies": ["Core feature"], "deliverables": ["demo", "slides"]},
                ],
                "critical_dependencies": ["Core feature before polish"],
                "risks": (["Advanced component may overrun the schedule"] if heavy else ["Underestimating integration time"]),
                "critique": ["Cut non-essential features early"],
                "cross_domain_flags": (["Pitch may overpromise vs. what fits the schedule"] if heavy else []),
            }

        if name == "PitchAnalysis":
            return {
                "value_proposition": "Saves users time by automating the hardest step of the workflow.",
                "target_user": "teams facing the stated problem",
                "differentiation": ["Simplicity", "Live end-to-end demo", "Clear time-to-value"],
                "impact": "Reduces manual effort and demonstrates a tangible outcome.",
                "pitch_structure": ["Problem", "Solution", "Live demo", "Impact", "Next steps"],
                "critique": (["Avoid claiming real-time/AI capability the build can't show"] if heavy else ["Tighten the problem framing"]),
                "cross_domain_flags": (["Claim exceeds feasible implementation"] if heavy else []),
            }

        if name == "ArbiterOutput":
            conflicts = []
            directives = []
            if heavy:
                conflicts.append(
                    {
                        "type": "technical_vs_timeline",
                        "description": "Advanced ML/real-time component is unlikely to be completed within the time limit.",
                        "severity": "high",
                        "resolution": "Swap the heavy component for a pre-trained model or rule-based heuristic and scope the demo to one flow.",
                        "resolved": True,
                    }
                )
                directives.append({"agent": "tech", "change": "Recommend a simpler pre-trained/rule-based alternative."})
                directives.append({"agent": "pitch", "change": "Reframe the claim to match the simplified implementation."})
            return {
                "conflicts": conflicts,
                "revision_directives": directives,
                "current_solution_text": (
                    f"Problem: {problem}. Solution: a focused, demoable app using React+FastAPI+SQLite, "
                    "scoped to one core flow that fits the time limit."
                ),
            }

        if name == "PersonaAdaptedPlan":
            persona = _field(user, "Persona", "intermediate").lower()
            if "beginner" in persona:
                depth = "Follow each step in order; don't skip setup. "
                pitfalls = ["Trying advanced features first", "Skipping a working demo path"]
            elif "advanced" in persona:
                depth = "Parallelize setup and core feature; stub integrations early. "
                pitfalls = ["Over-engineering", "Premature optimization"]
            else:
                depth = "Build the core flow first, then polish. "
                pitfalls = ["Scope creep", "Leaving integration to the end"]
            return {
                "persona": persona if persona in ("beginner", "intermediate", "advanced") else "intermediate",
                "summary": depth + "Ship one clear end-to-end demo.",
                "tech_guidance": "Use React + FastAPI + SQLite; keep the service single and simple.",
                "timeline_guidance": "Setup (0-2h) -> core feature (2-8h) -> polish & demo (8-12h).",
                "pitch_guidance": "Lead with the problem, show a live demo, state the impact.",
                "pitfalls": pitfalls,
                "next_steps": ["Scaffold repo", "Build core flow", "Prepare a 2-minute demo"],
            }

        if name == "BaselinePlan":
            return {
                "idea": {
                    "title": f"{theme.title()} Helper",
                    "problem": problem,
                    "solution": "A focused web app that solves the core problem with a simple, demoable flow.",
                    "target_users": "hackathon judges and early adopters",
                    "rationale": "Small scope, high clarity, buildable in the time limit.",
                },
                "recommended_stack": ["React", "FastAPI", "SQLite"],
                "architecture": ["SPA frontend", "REST API", "single service", "SQLite store"],
                "timeline": [
                    {"name": "Setup & scaffold", "duration": "0-2h", "dependencies": [], "deliverables": ["repo"]},
                    {"name": "Core feature", "duration": "2-8h", "dependencies": ["Setup & scaffold"], "deliverables": ["main flow"]},
                    {"name": "Polish & demo", "duration": "8-12h", "dependencies": ["Core feature"], "deliverables": ["demo"]},
                ],
                "dependencies": ["Core feature before polish"],
                "technical_risks": (["Heavy component may overrun"] if heavy else ["Scope creep"]),
                "value_proposition": "Saves users time by automating the hardest step of the workflow.",
                "differentiation": ["Simplicity", "Live demo"],
                "pitch_structure": ["Problem", "Solution", "Live demo", "Impact"],
                "solution_summary": "A focused, demoable React+FastAPI+SQLite app scoped to one core flow.",
            }

        # Fallback: empty object (schema will supply defaults or error clearly).
        return {}
