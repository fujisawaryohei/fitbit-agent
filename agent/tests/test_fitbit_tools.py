from unittest.mock import patch

import pytest

from agent.tools.fitbit_tools import (
    get_calories_burned,
    get_calories_in,
    get_heart_rate,
    get_steps,
    get_weight,
)

MODULE = "agent.tools.fitbit_tools._client"


class TestGetSteps:
    def test_normal(self) -> None:
        with patch(f"{MODULE}.get_activities", return_value={"summary": {"steps": 8000}}):
            result = get_steps.invoke({"date": "2026-05-20"})  # type: ignore[union-attr]
        assert result == "歩数: 8000歩"

    def test_no_data(self) -> None:
        with patch(f"{MODULE}.get_activities", return_value={"summary": {}}):
            result = get_steps.invoke({})  # type: ignore[union-attr]
        assert "0歩" in result

    def test_api_error(self) -> None:
        with patch(f"{MODULE}.get_activities", side_effect=RuntimeError("401")):
            result = get_steps.invoke({})  # type: ignore[union-attr]
        assert "Error" in result

    def test_invalid_date(self) -> None:
        with patch(f"{MODULE}.get_activities", side_effect=ValueError("YYYY-MM-DD")):
            result = get_steps.invoke({"date": "2026-5-1"})  # type: ignore[union-attr]
        assert "Error" in result


class TestGetCaloriesBurned:
    def test_normal(self) -> None:
        with patch(f"{MODULE}.get_activities", return_value={"summary": {"caloriesOut": 2500}}):
            result = get_calories_burned.invoke({"date": "2026-05-20"})  # type: ignore[union-attr]
        assert result == "消費カロリー: 2500kcal"

    def test_api_error(self) -> None:
        with patch(f"{MODULE}.get_activities", side_effect=RuntimeError("429")):
            result = get_calories_burned.invoke({})  # type: ignore[union-attr]
        assert "Error" in result


class TestGetWeight:
    def test_normal(self) -> None:
        with patch(f"{MODULE}.get_body_data", return_value={"weight": [{"weight": 70.5, "bmi": 23.1}]}):
            result = get_weight.invoke({})  # type: ignore[union-attr]
        assert "70.5kg" in result
        assert "23.1" in result

    def test_no_entries(self) -> None:
        with patch(f"{MODULE}.get_body_data", return_value={"weight": []}):
            result = get_weight.invoke({})  # type: ignore[union-attr]
        assert "見つかりません" in result

    def test_api_error(self) -> None:
        with patch(f"{MODULE}.get_body_data", side_effect=RuntimeError("404")):
            result = get_weight.invoke({})  # type: ignore[union-attr]
        assert "Error" in result


class TestGetHeartRate:
    def test_normal_with_resting(self) -> None:
        with patch(f"{MODULE}.get_heart_rate", return_value={
            "activities-heart": [{"dateTime": "2026-05-20", "value": {"restingHeartRate": 62}}]
        }):
            result = get_heart_rate.invoke({})  # type: ignore[union-attr]
        assert "62bpm" in result

    def test_no_resting_heart_rate(self) -> None:
        with patch(f"{MODULE}.get_heart_rate", return_value={
            "activities-heart": [{"dateTime": "2026-05-20", "value": {}}]
        }):
            result = get_heart_rate.invoke({})  # type: ignore[union-attr]
        assert "データなし" in result

    def test_no_entries(self) -> None:
        with patch(f"{MODULE}.get_heart_rate", return_value={"activities-heart": []}):
            result = get_heart_rate.invoke({})  # type: ignore[union-attr]
        assert "見つかりません" in result

    def test_api_error(self) -> None:
        with patch(f"{MODULE}.get_heart_rate", side_effect=RuntimeError("401")):
            result = get_heart_rate.invoke({})  # type: ignore[union-attr]
        assert "Error" in result


class TestGetCaloriesIn:
    def test_normal(self) -> None:
        with patch(f"{MODULE}.get_food_log", return_value={"summary": {"calories": 1800}}):
            result = get_calories_in.invoke({})  # type: ignore[union-attr]
        assert "1800kcal" in result

    def test_no_log(self) -> None:
        with patch(f"{MODULE}.get_food_log", return_value={"summary": {"calories": 0}}):
            result = get_calories_in.invoke({})  # type: ignore[union-attr]
        assert "登録されていません" in result

    def test_api_error(self) -> None:
        with patch(f"{MODULE}.get_food_log", side_effect=RuntimeError("429")):
            result = get_calories_in.invoke({})  # type: ignore[union-attr]
        assert "Error" in result
