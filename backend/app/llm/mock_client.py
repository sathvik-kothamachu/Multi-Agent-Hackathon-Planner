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
            # A rotating pool so Regenerate yields genuinely different concepts
            # (the server-side dedup rejects repeats; more concepts = fewer collisions).
            import hashlib

            seed = int(hashlib.md5(user.encode()).hexdigest(), 16)
            pool = [
                ("Helper", "web app", "individuals and small teams facing the problem daily",
                 "guided step-by-step workflow"),
                ("Assistant", "guided assistant", "busy professionals who want the painful step automated",
                 "one-click automation of the hardest manual task"),
                ("Dashboard", "insight dashboard", "decision-makers who need the key metric at a glance",
                 "visual surfacing of the core insight"),
                ("Coach", "interactive coach", "newcomers who need structured guidance",
                 "adaptive prompts that walk the user through the process"),
                ("Hub", "collaboration hub", "distributed teams coordinating the workflow",
                 "shared workspace that keeps everyone in sync"),
                ("Tracker", "progress tracker", "people who need to monitor and improve outcomes over time",
                 "tracking plus lightweight recommendations"),
            ]
            picks = [pool[(seed + k) % len(pool)] for k in (0, 2, 4)]
            ideas = []
            for suffix, kind, users, workflow in picks:
                ideas.append({
                    "title": f"{theme.title()} {suffix}",
                    "core_concept": f"A {kind} offering {workflow} for the stated problem.",
                    "problem": problem,
                    "solution": (
                        f"This {kind} directly tackles the stated problem: {problem}. "
                        f"It solves it by offering {workflow}, removing the friction users hit today. "
                        "\n\nUsers interact through a clean, focused interface: they enter their context, "
                        "the app processes it, and it returns an actionable result they can immediately use. "
                        "The main workflow is intentionally short so it can be demoed live end to end. "
                        "\n\nThe outcome is a tangible, measurable improvement over the manual approach, "
                        "delivered within the hackathon time limit and easy for judges to understand."
                    ),
                    "how_it_works": (
                        f"The user's input drives {workflow}; a small backend processes it and returns "
                        "an actionable result rendered in the UI. Major components: input capture, "
                        "processing service, and result view."
                    ),
                    "objectives": [
                        f"Deliver {workflow} as a working end-to-end flow.",
                        "Automate the single most painful manual step for these users.",
                        "Keep the build scoped to the hackathon time limit.",
                        "Produce a clear, judge-friendly outcome that shows measurable improvement.",
                    ],
                    "core_features": [
                        "Focused input capture",
                        "Core processing / automation step",
                        "Actionable result view",
                        "Simple, demoable UI",
                    ],
                    "implementation_approach": [
                        "Scaffold the frontend + API skeleton.",
                        f"Implement {workflow} as the core flow.",
                        "Wire the result view and persistence.",
                        "Polish the UI and rehearse the live demo.",
                    ],
                    "target_users": users,
                    "expected_impact": "Cuts the time and effort of the manual process and shows a concrete result.",
                    "innovation": f"Applies {kind} specifically to this problem instead of a generic tool.",
                    "feasibility": "Small, focused scope with a conventional stack fits the time limit.",
                    "tech_approach": "React + FastAPI + SQLite; add a pre-trained model only if it earns its place.",
                    "theme_relevance": f"Fits the '{theme}' theme by applying it to a real, specific workflow.",
                    "rationale": "Small scope, high clarity, buildable in the time limit.",
                })
            return {"ideas": ideas}

        if name == "IdeaEvaluationOutput":
            # Score each idea id found in the prompt. Ids look like "[idea-1]".
            ids = re.findall(r"\[(idea-[\w-]+)\]", user)
            evals = []
            for k, iid in enumerate(ids):
                base = 70 + (k * 5) % 20  # spread scores a little across ideas
                def crit(delta: int, why: str) -> dict:
                    return {"score": max(40, min(95, base + delta)), "reason": why}
                evals.append({
                    "idea_id": iid,
                    "title": "",
                    "theme_alignment": crit(6, "Fits the stated theme directly."),
                    "problem_relevance": crit(8, "Targets the core problem."),
                    "innovation": crit(-4, "Solid but not groundbreaking."),
                    "technical_feasibility": crit(4, "Buildable with a standard stack."),
                    "time_feasibility": crit(2, "Scoped to fit the time limit."),
                    "team_skill_fit": crit(0, "Matches common team skills."),
                    "impact": crit(3, "Clear, demonstrable outcome."),
                    "demo_potential": crit(7, "Easy to show live end to end."),
                    "overall": 0,  # computed server-side
                    "strongest_point": "Clear scope with a demoable core flow.",
                    "biggest_weakness": "Differentiation could be sharper.",
                    "biggest_risk": "Integration takes longer than expected.",
                    "why_fits": "Solves the stated problem within the theme and time limit.",
                })
            return {"evaluations": evals}

        if name == "TechAnalysis":
            return {
                "feasibility": "medium" if heavy else "high",
                "feasibility_score": 62 if heavy else 84,
                "complexity": "High" if heavy else "Low",
                "recommended_stack": ["React", "FastAPI", "SQLite"],
                "stack_details": [
                    {"name": "React", "purpose": "Fast, demoable single-page UI for the core flow."},
                    {"name": "FastAPI", "purpose": "Lightweight Python API to serve the processing step."},
                    {"name": "SQLite", "purpose": "Zero-config local persistence that fits the time limit."},
                ],
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
                "estimated_hours": 26 if heavy else 12,
                "schedule": [
                    {"task": "Setup & scaffold", "technology": "React, FastAPI", "duration": "2h", "dependency": "none", "expected_output": "Running skeleton"},
                    {"task": "Core feature", "technology": "FastAPI, SQLite", "duration": "6h", "dependency": "Setup & scaffold", "expected_output": "Working main flow"},
                    {"task": "Polish & demo", "technology": "React", "duration": "4h", "dependency": "Core feature", "expected_output": "Demo + slides"},
                ],
                "milestones": [
                    {"name": "Setup & scaffold", "duration": "2h", "dependencies": [], "deliverables": ["repo", "skeleton"]},
                    {"name": "Core feature", "duration": "6h", "dependencies": ["Setup & scaffold"], "deliverables": ["main flow"]},
                    {"name": "Polish & demo", "duration": "4h", "dependencies": ["Core feature"], "deliverables": ["demo", "slides"]},
                ],
                "critical_dependencies": ["Core feature before polish"],
                "risks": (["Advanced component may overrun the schedule"] if heavy else ["Underestimating integration time"]),
                "critique": ["Cut non-essential features early"],
                "cross_domain_flags": (["Pitch may overpromise vs. what fits the schedule"] if heavy else []),
            }

        if name == "PitchAnalysis":
            return {
                "value_proposition": "Saves users time by automating the hardest step of the workflow.",
                "aim": "Deliver a working, demoable tool that removes the biggest manual bottleneck.",
                "target_user": "teams facing the stated problem",
                "differentiation": ["Simplicity", "Live end-to-end demo", "Clear time-to-value"],
                "impact": "Reduces manual effort and demonstrates a tangible outcome.",
                "why_this_solution": "It is the smallest build that produces a visible, valuable result within the time limit.",
                "implementation_approach": ["Scaffold the app", "Build the core flow", "Wire the UI", "Rehearse the demo"],
                "future_scope": ["Add richer automation", "Support more data sources", "Team collaboration features"],
                "demo_flow": ["Open the app (15s)", "Enter sample input (30s)", "Run the core step (45s)", "Show the result + impact (30s)"],
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
                "phases": [
                    {
                        "name": "Setup & scaffold",
                        "time_allocation": "0-2h",
                        "technologies": ["React", "FastAPI"],
                        "guidance": depth + "Get the skeleton running before anything else.",
                        "expected_output": "A running app skeleton",
                        "dependencies": [],
                        "completion_criteria": "App boots and serves an empty page/endpoint.",
                    },
                    {
                        "name": "Core feature",
                        "time_allocation": "2-8h",
                        "technologies": ["FastAPI", "SQLite"],
                        "guidance": depth + "Implement the single most important flow end to end.",
                        "expected_output": "Working main flow",
                        "dependencies": ["Setup & scaffold"],
                        "completion_criteria": "A user can complete the core task successfully.",
                    },
                    {
                        "name": "Polish & demo",
                        "time_allocation": "8-12h",
                        "technologies": ["React"],
                        "guidance": depth + "Tidy the UI and rehearse the 2-minute demo.",
                        "expected_output": "Demo + slides",
                        "dependencies": ["Core feature"],
                        "completion_criteria": "Demo runs start to finish without errors.",
                    },
                ],
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
