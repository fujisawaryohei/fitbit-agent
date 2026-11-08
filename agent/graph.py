from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    fitness_assistant_node,
    memory_inject_node,
    memory_save_node,
    should_continue,
    tool_node,
)
from agent.state import AgentState

_builder = StateGraph(AgentState)
_builder.add_node("memory_inject_node", memory_inject_node)
_builder.add_node("fitness_assistant_node", fitness_assistant_node)
_builder.add_node("tool_node", tool_node)
_builder.add_node("memory_save_node", memory_save_node)

_builder.add_edge(START, "memory_inject_node")
_builder.add_edge("memory_inject_node", "fitness_assistant_node")
_builder.add_conditional_edges(
    "fitness_assistant_node",
    should_continue,
    {
        "tool_node": "tool_node",
        END: "memory_save_node",
    },
)
_builder.add_edge("tool_node", "fitness_assistant_node")
_builder.add_edge("memory_save_node", END)

agent = _builder.compile(checkpointer=MemorySaver())


def get_agent() -> Any:
    return agent
