from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph

from agent.nodes import agent_node, should_continue, tool_node
from agent.state import AgentState

_builder = StateGraph(AgentState)
_builder.add_node("agent_node", agent_node)
_builder.add_node("tool_node", tool_node)

_builder.add_edge(START, "agent_node")
_builder.add_conditional_edges("agent_node", should_continue)
_builder.add_edge("tool_node", "agent_node")

agent = _builder.compile(checkpointer=MemorySaver())
