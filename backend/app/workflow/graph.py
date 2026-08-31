"""LangGraph assembly for the planner workflow.

Binds client/settings into the node functions and wires the graph with a
human-review interrupt and a bounded re-debate loop. Compiled with a checkpointer
so the interrupt can be resumed by thread_id (= project_id).
"""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from app.workflow.nodes import (
    alignment_node,
    assemble_node,
    debate_node,
    human_review_node,
    ideas_node,
    persona_node,
    route_after_alignment,
    route_after_review,
)
from app.workflow.state import WorkflowState


def build_graph(client, settings, checkpointer):
    g = StateGraph(WorkflowState)

    g.add_node("ideas", partial(ideas_node, client=client, settings=settings))
    g.add_node("human_review", partial(human_review_node, client=client, settings=settings))
    g.add_node("debate", partial(debate_node, client=client, settings=settings))
    g.add_node("alignment", partial(alignment_node, client=client, settings=settings))
    g.add_node("assemble", partial(assemble_node, client=client, settings=settings))
    g.add_node("persona", partial(persona_node, client=client, settings=settings))

    g.add_edge(START, "ideas")
    g.add_edge("ideas", "human_review")
    g.add_conditional_edges(
        "human_review", route_after_review, {"regenerate": "ideas", "proceed": "debate"}
    )
    g.add_edge("debate", "alignment")
    g.add_conditional_edges(
        "alignment",
        partial(route_after_alignment, settings=settings),
        {"redebate": "debate", "finalize": "assemble"},
    )
    g.add_edge("assemble", "persona")
    g.add_edge("persona", END)

    return g.compile(checkpointer=checkpointer)
