from dotenv import load_dotenv
from langchain_core.tools import tool

from agent.context import get_fitbit_client

load_dotenv()


@tool
def get_steps(date: str | None = None) -> str:
    """指定日の歩数を取得する。date は YYYY-MM-DD 形式（省略時は今日）。"""
    try:
        result = get_fitbit_client().get_activities(date)
        steps = result.get("summary", {}).get("steps", 0)
        return f"歩数: {steps}歩"
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"


@tool
def get_calories_burned(date: str | None = None) -> str:
    """指定日の消費カロリーを取得する。date は YYYY-MM-DD 形式（省略時は今日）。"""
    try:
        result = get_fitbit_client().get_activities(date)
        calories = result.get("summary", {}).get("caloriesOut", 0)
        return f"消費カロリー: {calories}kcal"
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"


@tool
def get_weight(date: str | None = None) -> str:
    """指定日の体重を取得する。date は YYYY-MM-DD 形式（省略時は今日）。"""
    try:
        result = get_fitbit_client().get_body_data(date)
        entries = result.get("weight", [])
        if not entries:
            return "指定日の体重データが見つかりません。"
        latest = entries[-1]
        weight = latest.get("weight", 0)
        bmi = latest.get("bmi", 0)
        return f"体重: {weight}kg, BMI: {bmi:.1f}"
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"


@tool
def get_heart_rate(date: str | None = None, period: str = "1d") -> str:
    """指定日の心拍数データを取得する。date は YYYY-MM-DD 形式、period は '1d'/'7d'/'30d' など。"""
    try:
        result = get_fitbit_client().get_heart_rate(date, period)
        entries = result.get("activities-heart", [])
        if not entries:
            return "心拍数データが見つかりません。"
        latest = entries[-1]
        value = latest.get("value", {})
        resting = value.get("restingHeartRate")
        date_str = latest.get("dateTime", "")
        if resting:
            return f"安静時心拍数: {resting}bpm（{date_str}）"
        return f"安静時心拍数データなし（{date_str}）"
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"


@tool
def get_calories_in(date: str | None = None) -> str:
    """指定日の摂取カロリーを取得する。date は YYYY-MM-DD 形式（省略時は今日）。"""
    try:
        result = get_fitbit_client().get_food_log(date)
        calories = result.get("summary", {}).get("calories", 0)
        if calories == 0:
            return "食事ログが登録されていません。今日の食事内容を教えてください。"
        return f"摂取カロリー: {calories}kcal"
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"
