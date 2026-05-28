import textwrap

from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.memory.manager import save_memory, search_memories
from agent.tools.fitbit_tools import (
    get_calories_burned,
    get_calories_in,
    get_heart_rate,
    get_steps,
    get_weight,
)
from agent.tools.planning_tools import (
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

_llm = ChatBedrockConverse(model="jp.anthropic.claude-haiku-4-5-20251001-v1:0", region_name="ap-northeast-1").bind_tools(_tools)


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
        - 週単位の減量進捗評価こr
        - コーチ目線でのアドバイス

        何かお手伝いできることはありますか？例えば：
        - 「今日の歩数を教えて」
        - 「体重を知りたい」
        - 「目標カロリー赤字を計算して」
        - 「運動プランを作成して」
    """).strip()
    injected = [m.content for m in state.messages if isinstance(m, SystemMessage)]
    conversation = [m for m in state.messages if not isinstance(m, SystemMessage)]
    full_prompt = "\n\n".join([system_prompt] + injected)
    messages: list[AnyMessage] = [SystemMessage(content=full_prompt)] + conversation
    response = _llm.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(_tools)


def should_continue(state: AgentState) -> str:
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_node"
    return END


def memory_inject_node(state: AgentState) -> dict[str, list[AnyMessage]]:
    last_human = next((m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None)
    query = last_human.content if last_human else ""
    memories = search_memories(state.session_id, str(query))
    if not memories:
        return {"messages": []}
    memory_text = "\n".join(f"- {m}" for m in memories)
    injection = SystemMessage(content=f"【過去の記憶】\n{memory_text}")
    return {"messages": [injection]}


def memory_save_node(state: AgentState) -> dict[str, list[AnyMessage]]:
    _summary_llm = ChatBedrockConverse(model="jp.anthropic.claude-haiku-4-5-20251001-v1:0", region_name="ap-northeast-1")
    conversation = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in state.messages
        if isinstance(m, (HumanMessage, AIMessage))
    )
    summary_prompt = textwrap.dedent(f"""
        以下の会話から、ユーザーの目標・好み・重要情報を日本語で簡潔に要約してください。
        体重・運動・食事・健康状態など保存する価値のある情報がない場合は「SKIP」とだけ返してください。

        {conversation}
    """).strip()
    summary = _summary_llm.invoke(summary_prompt)
    if str(summary.content).strip() != "SKIP":
        save_memory(state.session_id, str(summary.content))
    return {"messages": []}
