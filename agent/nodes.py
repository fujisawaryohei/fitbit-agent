import textwrap

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langgraph.graph import END
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from tools.fitbit_tools import (
    get_calories_burned,
    get_calories_in,
    get_heart_rate,
    get_steps,
    get_weight,
)
from tools.planning_tools import (
    calculate_calorie_deficit,
    generate_home_workout_plan,
    get_weekly_progress,
)

load_dotenv()

_tools = [
    get_steps,
    get_calories_burned,
    get_weight,
    get_heart_rate,
    get_calories_in,
    calculate_calorie_deficit,
    generate_home_workout_plan,
    get_weekly_progress,
]

_llm = ChatAnthropic(model_name="claude-haiku-4-5-20251001").bind_tools(_tools)  # type: ignore[call-arg]


def agent_node(state: AgentState) -> dict[str, list[AnyMessage]]:
    system_prompt = textwrap.dedent("""
    あなたは、フィットネスサポートのアシスタントです。以下のような事を行います。
        **📊 健康データの確認**
        - 歩数、消費カロリー、摂取カロリー
        - 体重、心拍数

        **🎯 目標設定と計画**
        - カロリー赤字の計算
        - 減量目標の設定
        - 自宅でできる運動プラン作成

        **📈 進捗管理**
        - 週単位の減量進捗評価
        - コーチ目線でのアドバイス

        何かお手伝いできることはありますか？例えば：
        - 「今日の歩数を教えて」
        - 「体重を知りたい」
        - 「目標カロリー赤字を計算して」
        - 「運動プランを作成して」
    """).strip()
    messages: list[AnyMessage] = [SystemMessage(content=system_prompt)] + state.messages
    response = _llm.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(_tools)


def should_continue(state: AgentState) -> str:
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_node"
    return END
