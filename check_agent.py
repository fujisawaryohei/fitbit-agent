import sys
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent.graph import agent

load_dotenv()

session_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": session_id}}

try:
    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="体重を2ヶ月で5kg落とすためには、4月の消費カロリーの平均から考えると、1日辺りどれくらいの摂取カロリーを消費する必要がありますか？"
                )
            ],
            "session_id": session_id,
        },
        config=config,
    )
    print(result["messages"][-1].content)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
