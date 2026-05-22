from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    agent_node,
    memory_inject_node,
    memory_save_node,
    should_continue,
    tool_node,
)
from agent.state import AgentState

_builder = StateGraph(AgentState)
_builder.add_node("memory_inject_node", memory_inject_node)
_builder.add_node("agent_node", agent_node)
_builder.add_node("tool_node", tool_node)
_builder.add_node("memory_save_node", memory_save_node)

_builder.add_edge(START, "memory_inject_node")
_builder.add_edge("memory_inject_node", "agent_node")
_builder.add_conditional_edges(
    "agent_node",
    should_continue,
    {
        "tool_node": "tool_node",
        END: "memory_save_node",
    },
)
_builder.add_edge("tool_node", "agent_node")
_builder.add_edge("memory_save_node", END)

agent = _builder.compile(checkpointer=MemorySaver())


def get_agent():
    return agent
