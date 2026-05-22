import pytest
from pydantic import ValidationError

from agent.tools.models import CalorieDeficitResult, WeightGoal


class TestWeightGoal:
    def test_valid(self) -> None:
        goal = WeightGoal(current_weight_kg=75.0, target_weight_kg=70.0)
        assert goal.pace_kg_per_week == 0.5

    def test_invalid_pace_too_high(self) -> None:
        with pytest.raises(ValidationError):
            WeightGoal(current_weight_kg=75.0, target_weight_kg=70.0, pace_kg_per_week=1.5)

    def test_invalid_pace_too_low(self) -> None:
        with pytest.raises(ValidationError):
            WeightGoal(current_weight_kg=75.0, target_weight_kg=70.0, pace_kg_per_week=0.05)

    def test_invalid_target_gte_current(self) -> None:
        with pytest.raises(ValidationError):
            WeightGoal(current_weight_kg=70.0, target_weight_kg=75.0)


class TestCalorieDeficitResult:
    def test_valid(self) -> None:
        result = CalorieDeficitResult(
            daily_deficit_kcal=500,
            weekly_deficit_kcal=3500,
            weeks_to_goal=10.0,
            days_to_goal=70,
            total_loss_kg=5.0,
            pace_kg_per_week=0.5,
        )
        assert result.daily_deficit_kcal == 500

    def test_invalid_deficit_too_low(self) -> None:
        with pytest.raises(ValidationError):
            CalorieDeficitResult(
                daily_deficit_kcal=100,
                weekly_deficit_kcal=700,
                weeks_to_goal=10.0,
                days_to_goal=70,
                total_loss_kg=5.0,
                pace_kg_per_week=0.5,
            )

    def test_invalid_deficit_too_high(self) -> None:
        with pytest.raises(ValidationError):
            CalorieDeficitResult(
                daily_deficit_kcal=1500,
                weekly_deficit_kcal=10500,
                weeks_to_goal=10.0,
                days_to_goal=70,
                total_loss_kg=5.0,
                pace_kg_per_week=0.5,
            )
