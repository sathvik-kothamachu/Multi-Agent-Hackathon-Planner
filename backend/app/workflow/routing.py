"""Pure routing logic for the debate/alignment loop.

Deterministic, dependency-free (no LLM, no framework) so the loop can never spin
forever and can be unit-tested offline. The LangGraph graph delegates its
conditional edges to these functions (research objective #1/#2 control flow).
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from app.alignment.similarity import ALIGNED, DRIFT

# Extra terminal status when the loop is force-stopped at the round cap.
MAX_ROUNDS_EXCEEDED = "max_rounds_exceeded"

# Route names (graph edges).
ROUTE_FINALIZE = "finalize"
ROUTE_REDEBATE = "redebate"

# The only agents that may be targeted by a revision directive. Pitch is no
# longer part of the early debate (it is generated at the final stage), so it is
# not a valid revision target here.
VALID_AGENTS = ("tech", "timeline")


def is_max_rounds(current_round: int, max_rounds: int) -> bool:
    """True once we have used up the configured debate-round budget."""
    return current_round >= max_rounds


def next_round(current_round: int) -> int:
    return current_round + 1


def terminal_status(status: str) -> bool:
    """A status that must stop the loop (converged or force-stopped)."""
    return status in (ALIGNED, MAX_ROUNDS_EXCEEDED)


def decide_route(alignment_status: str, current_round: int, max_rounds: int) -> str:
    """Decide whether to finalize or run another debate round.

    - ALIGNED -> finalize (converged).
    - DRIFT with rounds remaining -> redebate.
    - DRIFT at the round cap -> finalize (controlled stop; never loops forever).
    """
    if alignment_status == ALIGNED:
        return ROUTE_FINALIZE
    if is_max_rounds(current_round, max_rounds):
        return ROUTE_FINALIZE
    return ROUTE_REDEBATE


def _agent_name(directive: Any) -> Optional[str]:
    agent = directive.get("agent") if isinstance(directive, dict) else getattr(directive, "agent", None)
    if agent is None:
        return None
    if hasattr(agent, "value"):  # tolerate enum-like values
        agent = agent.value
    return str(agent).strip().lower()


def next_agents(directives: Iterable[Any]) -> list[str]:
    """Ordered, de-duplicated list of valid agents named by revision directives.

    Unknown agents and directives without an agent are dropped. This is how a
    re-debate round targets ONLY the agents the arbiter asked to revise, instead
    of re-running everything (token discipline, research objective #1).
    """
    out: list[str] = []
    for d in directives or []:
        name = _agent_name(d)
        if name and name in VALID_AGENTS and name not in out:
            out.append(name)
    return out
