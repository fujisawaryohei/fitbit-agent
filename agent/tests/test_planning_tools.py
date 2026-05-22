import pytest

from agent.tools.planning_tools import calculate_calorie_deficit

KCAL_PER_KG = 7200


def invoke(current: float, target: float, pace: float = 0.5) -> str:
    return calculate_calorie_deficit.invoke(  # type: ignore[union-attr]
        {"current_weight_kg": current, "target_weight_kg": target, "pace_kg_per_week": pace}
    )


class TestCalculateCalorieDeficit:
    def test_normal(self) -> None:
        result = invoke(75.0, 70.0)
        assert "1日の目標カロリー赤字" in result
        assert "週次カロリー赤字" in result
        assert "目標達成まで" in result

    def test_daily_deficit_calculation(self) -> None:
        result = invoke(75.0, 70.0, pace=0.5)
        # 0.5kg/week * 7200kcal/kg / 7days = 514kcal → clamp で 514
        assert "514kcal" in result

    def test_weeks_to_goal(self) -> None:
        result = invoke(75.0, 70.0, pace=0.5)
        # 5kg / 0.5kg/week = 10.0週
        assert "10.0週間" in result

    def test_pace_min_boundary(self) -> None:
        result = invoke(75.0, 70.0, pace=0.1)
        assert "1日の目標カロリー赤字" in result
        # 0.1 * 7200 / 7 ≈ 103 → clamp で 200
        assert "200kcal" in result

    def test_pace_max_boundary(self) -> None:
        result = invoke(75.0, 70.0, pace=1.0)
        assert "1日の目標カロリー赤字" in result
        # 1.0 * 7200 / 7 ≈ 1028 → clamp で 1000
        assert "1000kcal" in result

    def test_error_target_gte_current(self) -> None:
        with pytest.raises(ValueError, match="目標体重は現在体重より軽くしてください"):
            invoke(70.0, 75.0)

    def test_error_target_equals_current(self) -> None:
        with pytest.raises(ValueError, match="目標体重は現在体重より軽くしてください"):
            invoke(70.0, 70.0)

    def test_error_pace_too_high(self) -> None:
        with pytest.raises(ValueError, match="pace_kg_per_week は 0.1〜1.0"):
            invoke(75.0, 70.0, pace=1.1)

    def test_error_pace_too_low(self) -> None:
        with pytest.raises(ValueError, match="pace_kg_per_week は 0.1〜1.0"):
            invoke(75.0, 70.0, pace=0.05)

    def test_total_loss_kg(self) -> None:
        result = invoke(80.0, 70.0, pace=0.5)
        assert "10.0kg" in result
