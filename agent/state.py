from typing import Annotated, List

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class AgentState(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages]
    session_id: str

    model_config = {"arbitrary_types_allowed": True}
