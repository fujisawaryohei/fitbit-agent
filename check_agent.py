import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent.graph import agent
from agent.langfuse_setup import get_langfuse_handler

load_dotenv()

config = {"configurable": {"thread_id": "test-session", "callbacks": [get_langfuse_handler()]}}

try:
    result = agent.invoke(
        {
            "messages": [HumanMessage(content="間食をやめるコツを教えて")],
            "session_id": "test-session",
        },
        config=config,
    )
    print(result["messages"][-1].content)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
