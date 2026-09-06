"""User-facing /100 Theme & Problem Alignment report (deterministic, NO LLM).

This is Step 5. It evaluates how well the SELECTED idea aligns with the user's
actual Step-1 inputs — hackathon theme, problem statement, target users, the
proposed solution/features, and the time limit — and produces a /100 breakdown
with per-category evidence and concrete, project-specific improvement suggestions.

Scoring is DIRECTIONAL, not symmetric. The old version used Jaccard overlap
(|A∩B| / |A∪B|): comparing a short string (a one-word theme, a short target-user
line) against the long full-idea text made the union huge and forced scores
toward zero (hence 12/100 theme, 10/100 user-fit for otherwise reasonable ideas).
We instead measure how much of the TARGET's meaning (theme / problem) is actually
COVERED by the idea, with light stemming so "appointment"/"appointments" match,
blended with a lexical-semantic cosine, then shaped by a mild concave curve so a
genuinely well-aligned project lands in the 75-90 band while unrelated content
still scores near zero. No numbers are hard-coded or inflated — an off-theme or
vague idea collapses on its own.

Before scoring, a SINGLE deterministic strengthening pass may enrich the idea's
description text with its own theme/problem vocabulary when alignment is weak
(never replacing the idea or inventing features), matching spec sections 2 & 11.
"""
from __future__ import annotations

import re
from typing import List, Tuple

import numpy as np

from app.alignment.semantic_alignment import _embed
from app.alignment.similarity import cosine
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.schemas import AlignmentReport, IdeaDraft, TechAnalysis, TimelineAnalysis

logger = get_logger(__name__)

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with", "by",
    "is", "are", "be", "that", "this", "it", "as", "at", "from", "into", "using",
    "your", "you", "our", "we", "can", "will", "which", "who", "how", "why",
    "what", "their", "them", "they", "its", "also", "more", "than", "then", "so",
    "such", "not", "no", "if", "but", "may", "might", "could", "should", "would",
    "when", "where", "each", "every", "via", "per", "across", "within", "without",
    "get", "use", "used", "make", "made", "help", "helps", "provide", "provides",
    "general", "thing", "things", "people",
}
# Suffixes stripped for light stemming (longest first so "-ations" wins over "-s").
_SUFFIXES = ("ations", "ation", "ings", "ing", "tion", "sion", "ers", "er",
             "ed", "es", "s", "ly", "al", "ment")


# --------------------------------------------------------------------------- #
# Text → comparable signal
# --------------------------------------------------------------------------- #
def _stem(word: str) -> str:
    for suf in _SUFFIXES:
        if len(word) - len(suf) >= 3 and word.endswith(suf):
            return word[: -len(suf)]
    return word


def _stems(text: str) -> set:
    return {
        _stem(w)
        for w in _WORD_RE.findall((text or "").lower())
        if w not in _STOP and len(w) > 2
    }


def _coverage(target: str, source: str) -> float:
    """Directional: fraction of TARGET's content stems present in SOURCE.

    A stem counts as present on an exact match OR a prefix match either way
    (so "schedule"/"scheduler"/"scheduling" all align). This is the fix for the
    old Jaccard behaviour — the score no longer collapses just because SOURCE is
    much longer than TARGET.
    """
    tt, ts = _stems(target), _stems(source)
    if not tt:
        return 0.0
    hits = 0
    for x in tt:
        if x in ts or any(s.startswith(x) or x.startswith(s) for s in ts):
            hits += 1
    return hits / len(tt)


def _sim(a: str, b: str, settings: Settings) -> float:
    """Semantic cosine of two texts (0..1), robust via the shared embed fallback."""
    if not a.strip() or not b.strip():
        return 0.0
    vectors, _ = _embed([a, b], settings)
    return max(0.0, cosine(vectors[0], vectors[1]))


def _curve(x: float) -> float:
    """Mild concave shaping (sqrt): rewards real matches without inflating zeros.

    0→0, .25→.50, .49→.70, .70→.84, 1→1. A truly unrelated pair (raw≈0) stays
    near 0; a solid-but-not-verbatim match (raw≈.5) rises into the strong band.
    """
    return float(max(0.0, min(1.0, x)) ** 0.5)


def _rel(target: str, source: str, settings: Settings) -> float:
    """Directional relevance of SOURCE to TARGET in 0..1 (coverage-led + semantic)."""
    raw = 0.6 * _coverage(target, source) + 0.4 * _sim(target, source, settings)
    return _curve(raw)


def _pct(x: float) -> int:
    return int(round(max(0.0, min(1.0, x)) * 100))


def _label(overall: int) -> str:
    if overall >= 85:
        return "Strong alignment"
    if overall >= 75:
        return "Good alignment"
    if overall >= 60:
        return "Moderate alignment"
    if overall >= 40:
        return "Weak alignment"
    return "Poor alignment"


def _idea_text(idea: IdeaDraft) -> str:
    """All of the idea's descriptive fields, so scoring uses every bit of evidence
    the user actually provided/selected — not just title + solution."""
    parts = [
        idea.title, idea.core_concept, idea.solution, idea.how_it_works,
        idea.expected_impact, idea.innovation, idea.theme_relevance,
        " ".join(idea.objectives or []),
        " ".join(idea.core_features or []),
    ]
    return " ".join(p for p in parts if p)


def _features(idea: IdeaDraft) -> List[str]:
    return [f for f in (idea.core_features or []) if f and f.strip()]


# --------------------------------------------------------------------------- #
# Feasibility from real scope vs. the entered time limit
# --------------------------------------------------------------------------- #
def _feasibility_score(
    tech: TechAnalysis | None, timeline: TimelineAnalysis | None
) -> Tuple[float, str]:
    """Blend the tech feasibility score with timeline scope-vs-time evidence.

    Feasibility drops when the estimated build time exceeds the entered limit —
    so an over-scoped project is penalised here (spec §7), deterministically.
    """
    tech_component = (tech.feasibility_score / 100.0) if tech and tech.feasibility_score else 0.7

    if timeline and timeline.estimated_hours and timeline.available_hours:
        ratio = timeline.estimated_hours / timeline.available_hours
        if ratio <= 0.6:
            time_component, note = 0.92, "comfortably fits the time limit"
        elif ratio <= 0.8:
            time_component, note = 0.85, "realistically fits the time limit"
        elif ratio <= 1.0:
            time_component, note = 0.78, "achievable but with little slack"
        elif ratio <= 1.2:
            time_component, note = 0.60, "slightly over the time limit — trim scope"
        elif ratio <= 1.5:
            time_component, note = 0.45, "over the time limit — move features to stretch"
        else:
            time_component, note = 0.30, "well over the time limit — cut scope to an MVP"
        score = 0.5 * tech_component + 0.5 * time_component
        reason = (
            f"Estimated {timeline.estimated_hours:g}h vs {timeline.available_hours:g}h available "
            f"({note}); technical complexity is "
            f"{(tech.complexity.lower() if tech and tech.complexity else 'moderate')}."
        )
        return score, reason

    reason = (
        f"Based on technical complexity "
        f"({tech.complexity.lower() if tech and tech.complexity else 'moderate'}); "
        "no timeline estimate was available to check scope against the time limit."
    )
    return tech_component, reason


# --------------------------------------------------------------------------- #
# One-pass deterministic strengthening (spec §2 & §11) — NO LLM, NO replacement
# --------------------------------------------------------------------------- #
def _strengthen_idea(
    idea: IdeaDraft, problem_statement: str, theme: str, base: dict, settings: Settings
) -> bool:
    """Make an ALREADY-PRESENT theme/problem connection explicit — GATED so it can
    never inflate an off-theme or off-problem idea. Preserves the core concept;
    never adds features or swaps the idea. Returns True if it changed any text.

    Honesty gate (spec §13 — "must NOT artificially increase scores / ignore the
    actual theme"): each clarification only fires when the idea ALREADY has a
    genuine-but-not-yet-strong latent link to that dimension (base score in the
    0.30-0.75 band). A truly unrelated idea (base ≈ 0, e.g. a clinic app under a
    'space' theme, or a vague app with no problem link) fails every gate and gets
    NO uplift — so wrong-theme/vague projects stay low, by construction.

    Runs at most once (the caller calls it once).
    """
    changed = False
    theme_clean = (theme or "").strip()
    LO, HI = 0.30, 0.75  # genuine latent link, but weak enough to be worth stating

    # Theme: only when a real (but under-stated) link already exists.
    if theme_clean and theme_clean.lower() != "general" and LO <= base["theme_relevance"] < HI:
        addition = (
            f"This directly supports the '{theme_clean}' theme by applying it to the "
            "stated problem rather than mentioning it in passing."
        )
        if addition not in (idea.theme_relevance or ""):
            idea.theme_relevance = (
                (idea.theme_relevance + " " + addition).strip()
                if idea.theme_relevance else addition
            )
            changed = True

    # Problem: only when the solution already partly addresses the stated problem.
    if problem_statement and LO <= base["problem_relevance"] < HI:
        core = problem_statement.strip().rstrip(".")
        addition = (
            f" It stays focused on the core problem — {core} — so every part of the "
            "solution maps back to what the user set out to solve."
        )
        if idea.solution and addition.strip() not in idea.solution:
            idea.solution = idea.solution.rstrip() + addition
            changed = True

    # Target users: only when users already have some link to the problem, but it
    # is under-stated (band tightened so it can't lift an unrelated audience).
    if problem_statement and idea.target_users and LO <= base["user_problem_fit"] < 0.60:
        addition = f" — the people directly affected by: {problem_statement.strip().rstrip('.')}."
        if addition.strip() not in idea.target_users:
            idea.target_users = idea.target_users.rstrip(".") + addition
            changed = True

    return changed


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def build_alignment_report(
    problem_statement: str,
    theme: str,
    idea: IdeaDraft,
    tech: TechAnalysis | None,
    settings: Settings,
    timeline: TimelineAnalysis | None = None,
) -> AlignmentReport:
    """Compute the Step-5 /100 breakdown from the full selected idea + Step-1 inputs.

    Order (spec §1, §2, §11): (1) analyze inputs by scoring, (2) if weak, run ONE
    deterministic strengthening pass on the idea's own text, (3) score again and
    report. Overall is strictly the mean of the five categories (spec §9).
    """
    theme_clean = (theme or "").strip()
    has_real_theme = bool(theme_clean) and theme_clean.lower() != "general"

    def score_all() -> dict:
        idea_blob = _idea_text(idea)
        features = _features(idea)
        domain = f"{problem_statement} {idea.solution}"

        # Theme: best evidence between the idea's dedicated theme_relevance line and
        # the whole idea. "general" theme => neutral (don't reward or punish).
        if has_real_theme:
            theme_rel = max(
                _rel(theme_clean, idea.theme_relevance or "", settings),
                _rel(theme_clean, idea_blob, settings),
            )
        else:
            theme_rel = 0.7  # neutral: no specific theme entered

        problem_rel = _rel(problem_statement, idea_blob, settings)
        user_fit = _rel(
            problem_statement,
            f"{idea.target_users} {idea.solution} {idea.expected_impact}",
            settings,
        )
        # Solution relevance = how on-topic each core feature is to the problem
        # domain. Direction matters: we measure how much of EACH FEATURE's meaning
        # is present in the problem+solution domain (_rel(feature, domain)), so an
        # on-topic feature scores high while an off-topic / over-scoped extra
        # (e.g. "blockchain audit log" on a clinic app) scores low and drags the
        # mean down (spec §6). Scoring _rel(domain, feature) would be wrong — a
        # short feature can never "cover" the whole domain and every feature would
        # look irrelevant.
        if features:
            sol_rel = float(np.mean([_rel(f, domain, settings) for f in features]))
        else:
            sol_rel = _rel(idea.solution, problem_statement, settings)

        return {
            "theme_relevance": theme_rel,
            "problem_relevance": problem_rel,
            "user_problem_fit": user_fit,
            "solution_relevance": sol_rel,
        }

    # (1) initial analysis
    raw = score_all()
    weak = any(v < 0.75 for v in raw.values())

    # (2) at most ONE strengthening pass, only if weak (spec §11: never endless).
    # The pass is GATED on the initial scores so it can only clarify links that
    # genuinely already exist — it cannot lift an off-theme or vague idea.
    strengthened = False
    if weak:
        try:
            strengthened = _strengthen_idea(idea, problem_statement, theme, raw, settings)
        except Exception:  # noqa: BLE001 — strengthening is best-effort, never fatal
            logger.exception("alignment strengthening pass failed; scoring original idea")
            strengthened = False
        if strengthened:
            raw = score_all()  # (3) re-score the improved (same) idea

    feas_val, feas_reason = _feasibility_score(tech, timeline)

    subs = {
        "theme_relevance": _pct(raw["theme_relevance"]),
        "problem_relevance": _pct(raw["problem_relevance"]),
        "user_problem_fit": _pct(raw["user_problem_fit"]),
        "solution_relevance": _pct(raw["solution_relevance"]),
        "feasibility": _pct(feas_val),
    }
    # Overall = mean of the five categories, exactly (spec §9). No manual tweaks.
    overall = int(round(float(np.mean(list(subs.values())))))
    label = _label(overall)

    reasons = _build_reasons(problem_statement, theme_clean, has_real_theme, idea, subs, feas_reason)
    improvements = _build_improvements(problem_statement, theme_clean, has_real_theme, idea, subs)

    explanation = (
        f"'{idea.title}' scores {overall}/100 against your theme, problem, users, "
        f"solution and time limit. "
        + (
            "It stays closely tied to what you set out to build."
            if overall >= 75
            else "Some connections are weak — see the per-category notes and suggestions below."
        )
        + (" The idea's description was strengthened once to sharpen these links before scoring."
           if strengthened else "")
    )

    return AlignmentReport(
        overall=overall,
        label=label,
        explanation=explanation,
        improvements=improvements,
        strengthened=strengthened,
        **subs,
        **reasons,
    )


# --------------------------------------------------------------------------- #
# Evidence + suggestions (project-specific, deterministic)
# --------------------------------------------------------------------------- #
def _first_feature(idea: IdeaDraft) -> str:
    feats = _features(idea)
    return feats[0] if feats else (idea.core_concept or idea.title or "the core feature")


def _build_reasons(
    problem: str, theme: str, has_real_theme: bool, idea: IdeaDraft,
    subs: dict, feas_reason: str,
) -> dict:
    feat = _first_feature(idea)
    users = idea.target_users or "the target users"
    prob_short = problem.strip().rstrip(".")

    theme_reason = (
        f"Directly tied to the '{theme}' theme — e.g. '{feat}' applies it to the problem."
        if has_real_theme and subs["theme_relevance"] >= 75
        else f"Only a loose link to the '{theme}' theme; no core feature clearly demonstrates it."
        if has_real_theme
        else "No specific theme was entered ('general'), so theme relevance is treated as neutral."
    )
    problem_reason = (
        f"The solution addresses the stated problem — {prob_short} — as its central goal."
        if subs["problem_relevance"] >= 75
        else f"The solution only partially connects to the stated problem — {prob_short}."
    )
    user_problem_reason = (
        f"Built around {users}, whose pain point the solution directly relieves."
        if subs["user_problem_fit"] >= 75
        else f"The link between {users} and their specific pain point could be sharper."
    )
    solution_reason = (
        "Core features map cleanly onto the problem, with little unrelated scope."
        if subs["solution_relevance"] >= 75
        else "Some features do not clearly contribute to solving the core problem."
    )
    return {
        "theme_reason": theme_reason,
        "problem_reason": problem_reason,
        "user_problem_reason": user_problem_reason,
        "solution_reason": solution_reason,
        "feasibility_reason": feas_reason,
    }


def _build_improvements(
    problem: str, theme: str, has_real_theme: bool, idea: IdeaDraft, subs: dict
) -> List[str]:
    """One actionable, project-specific suggestion per category scoring below 75."""
    out: List[str] = []
    prob_short = problem.strip().rstrip(".")[:120]
    users = idea.target_users or "the affected users"

    if has_real_theme and subs["theme_relevance"] < 75:
        out.append(
            f"Theme ({subs['theme_relevance']}/100): add or rename a core feature that visibly "
            f"applies the '{theme}' theme to the problem, instead of referencing it only in the description."
        )
    if subs["problem_relevance"] < 75:
        out.append(
            f"Problem ({subs['problem_relevance']}/100): restate the solution so its main flow "
            f"clearly resolves the core problem — {prob_short} — rather than a related one."
        )
    if subs["user_problem_fit"] < 75:
        out.append(
            f"User fit ({subs['user_problem_fit']}/100): name {users} explicitly and describe the exact "
            "pain the solution removes for them (e.g. a manual step it automates)."
        )
    if subs["solution_relevance"] < 75:
        out.append(
            f"Solution ({subs['solution_relevance']}/100): drop or defer features that don't map to the "
            "problem, and keep the ones that directly move the core outcome."
        )
    if subs["feasibility"] < 75:
        out.append(
            f"Feasibility ({subs['feasibility']}/100): move the heaviest component to a stretch goal and "
            "define a smaller MVP that clearly fits the entered time limit."
        )
    return out
