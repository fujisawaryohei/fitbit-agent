import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent.graph import agent

load_dotenv()

config = {"configurable": {"thread_id": "test-session"}}

try:
    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="現在体重78kg、目標体重70kg、週0.5kgペースでカロリー赤字を計算して"
                )
            ],
            "session_id": "test-session",
        },
        config=config,
    )
    print(result["messages"][-1].content)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
