from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from agent.tools.models import CalorieDeficitResult

load_dotenv()

KCAL_PER_KG = 7200


@tool
def calculate_calorie_deficit(
    current_weight_kg: float,
    target_weight_kg: float,
    pace_kg_per_week: float = 0.5,
) -> str:
    """1日の目標カロリー赤字と目標達成期間を計算する。pace_kg_per_week は 0.1〜1.0（デフォルト 0.5）。"""

    if target_weight_kg >= current_weight_kg:
        raise ValueError("目標体重は現在体重より軽くしてください。")
    if not (0.1 <= pace_kg_per_week <= 1.0):
        raise ValueError("pace_kg_per_week は 0.1〜1.0 の範囲で指定してください。")

    total_loss_kg = current_weight_kg - target_weight_kg
    weekly_deficit_kcal = pace_kg_per_week * KCAL_PER_KG
    daily_deficit_kcal = max(200, min(1000, round(weekly_deficit_kcal / 7)))
    weeks_to_goal = total_loss_kg / pace_kg_per_week

    result = CalorieDeficitResult(
        daily_deficit_kcal=daily_deficit_kcal,
        weekly_deficit_kcal=round(weekly_deficit_kcal),
        weeks_to_goal=round(weeks_to_goal, 1),
        days_to_goal=round(weeks_to_goal * 7),
        total_loss_kg=round(total_loss_kg, 1),
        pace_kg_per_week=pace_kg_per_week,
    )

    return (
        f"1日の目標カロリー赤字: {result.daily_deficit_kcal}kcal\n"
        f"週次カロリー赤字: {result.weekly_deficit_kcal}kcal\n"
        f"目標達成まで: {result.weeks_to_goal}週間（{result.days_to_goal}日）\n"
        f"総減量目標: {result.total_loss_kg}kg\n"
        f"週次ペース: {result.pace_kg_per_week}kg/週"
    )


@tool
def generate_home_workout_plan(
    daily_deficit_kcal: int,
    fitness_level: str,
    available_days_per_week: int,
    duration_minutes: int,
) -> str:
    """自宅でできる運動プランを生成する。fitness_level は 'beginner'/'intermediate'/'advanced'。"""

    llm = ChatAnthropic(model_name="claude-haiku-4-5-20251001")  # type: ignore[call-arg]
    prompt = (
        f"以下の条件で、自宅でできる運動プランを日本語で生成してください。器具は不要とします。\n\n"
        f"- フィットネスレベル: {fitness_level}\n"
        f"- 週の運動可能日数: {available_days_per_week}日\n"
        f"- 1回の運動時間: {duration_minutes}分\n"
        f"- 運動で補いたいカロリー: {daily_deficit_kcal // 2}kcal程度\n\n"
        f"以下の形式で出力してください:\n"
        f"1. 週次スケジュール\n"
        f"2. 各日のメニュー（種目名・セット数・回数）\n"
        f"3. フォームのポイント\n"
        f"4. 推定カロリー消費量"
    )
    response = llm.invoke(prompt)
    return str(response.content)


@tool
def get_weekly_progress(
    current_weight_kg: float,
    start_weight_kg: float,
    target_pace_kg_per_week: float,
    weeks_elapsed: int,
) -> str:
    """週次の減量進捗をコーチ目線で評価・アドバイスする。"""

    llm = ChatAnthropic(model_name="claude-haiku-4-5-20251001")  # type: ignore[call-arg]
    actual_loss_kg = round(start_weight_kg - current_weight_kg, 1)
    expected_loss_kg = round(target_pace_kg_per_week * weeks_elapsed, 1)

    prompt = (
        f"以下のユーザーの減量進捗をコーチ目線で日本語で評価し、具体的なアドバイスをしてください。\n\n"
        f"- 開始時体重: {start_weight_kg}kg\n"
        f"- 現在体重: {current_weight_kg}kg\n"
        f"- 実際の減量: {actual_loss_kg}kg\n"
        f"- 目標減量（{weeks_elapsed}週×{target_pace_kg_per_week}kg）: {expected_loss_kg}kg\n"
        f"- 経過週数: {weeks_elapsed}週\n\n"
        f"進捗の評価（順調/やや遅れ/遅れ気味）と、次のステップへのアドバイスを含めてください。"
    )
    response = llm.invoke(prompt)
    return str(response.content)
