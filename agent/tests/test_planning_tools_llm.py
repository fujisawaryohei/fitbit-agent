from unittest.mock import MagicMock, patch

from agent.tools.planning_tools import generate_home_workout_plan, get_weekly_progress


def make_llm_mock(content: str) -> MagicMock:
    response = MagicMock()
    response.content = content
    llm = MagicMock()
    llm.invoke.return_value = response
    return llm


class TestGenerateHomeWorkoutPlan:
    def test_returns_llm_response(self) -> None:
        llm_mock = make_llm_mock("週3日の運動プラン...")
        with patch("tools.planning_tools.ChatAnthropic", return_value=llm_mock):
            result = generate_home_workout_plan.invoke(  # type: ignore[union-attr]
                {
                    "daily_deficit_kcal": 500,
                    "fitness_level": "beginner",
                    "available_days_per_week": 3,
                    "duration_minutes": 30,
                }
            )
        assert result == "週3日の運動プラン..."
        llm_mock.invoke.assert_called_once()

    def test_prompt_contains_fitness_level(self) -> None:
        llm_mock = make_llm_mock("プラン")
        with patch("tools.planning_tools.ChatAnthropic", return_value=llm_mock):
            generate_home_workout_plan.invoke(  # type: ignore[union-attr]
                {
                    "daily_deficit_kcal": 500,
                    "fitness_level": "advanced",
                    "available_days_per_week": 5,
                    "duration_minutes": 60,
                }
            )
        prompt = llm_mock.invoke.call_args[0][0]
        assert "advanced" in prompt


class TestGetWeeklyProgress:
    def test_returns_llm_response(self) -> None:
        llm_mock = make_llm_mock("順調に進んでいます。")
        with patch("tools.planning_tools.ChatAnthropic", return_value=llm_mock):
            result = get_weekly_progress.invoke(  # type: ignore[union-attr]
                {
                    "current_weight_kg": 73.0,
                    "start_weight_kg": 75.0,
                    "target_pace_kg_per_week": 0.5,
                    "weeks_elapsed": 4,
                }
            )
        assert result == "順調に進んでいます。"
        llm_mock.invoke.assert_called_once()

    def test_prompt_contains_weight_info(self) -> None:
        llm_mock = make_llm_mock("アドバイス")
        with patch("tools.planning_tools.ChatAnthropic", return_value=llm_mock):
            get_weekly_progress.invoke(  # type: ignore[union-attr]
                {
                    "current_weight_kg": 73.0,
                    "start_weight_kg": 75.0,
                    "target_pace_kg_per_week": 0.5,
                    "weeks_elapsed": 4,
                }
            )
        prompt = llm_mock.invoke.call_args[0][0]
        assert "75.0" in prompt
        assert "73.0" in prompt
