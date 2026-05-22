from hypothesis import assume, given, settings
from hypothesis import strategies as st

from agent.tools.planning_tools import calculate_calorie_deficit

KCAL_PER_KG = 7200


def invoke(current: float, target: float, pace: float) -> str:
    return calculate_calorie_deficit.invoke(  # type: ignore[union-attr]
        {"current_weight_kg": current, "target_weight_kg": target, "pace_kg_per_week": pace}
    )


@given(
    current=st.floats(min_value=50, max_value=120),
    target=st.floats(min_value=40, max_value=119),
    pace=st.floats(min_value=0.1, max_value=1.0),
)
@settings(max_examples=100)
def test_daily_deficit_always_in_safe_range(current: float, target: float, pace: float) -> None:
    assume(target < current)
    result = invoke(current, target, pace)
    # daily_deficit_kcal は 200〜1000 の範囲に clamp される
    daily_deficit = round(min(1000, max(200, round(pace * KCAL_PER_KG / 7))))
    assert str(daily_deficit) in result


@given(
    current=st.floats(min_value=50, max_value=120),
    target=st.floats(min_value=40, max_value=119),
    pace=st.floats(min_value=0.1, max_value=1.0),
)
@settings(max_examples=100)
def test_weeks_to_goal_is_positive(current: float, target: float, pace: float) -> None:
    assume(target < current)
    result = invoke(current, target, pace)
    assert "週間" in result


@given(
    current=st.floats(min_value=50, max_value=120),
    target=st.floats(min_value=40, max_value=119),
)
@settings(max_examples=100)
def test_total_loss_is_positive(current: float, target: float) -> None:
    assume(target < current)
    result = invoke(current, target, 0.5)
    total_loss = round(current - target, 1)
    assert f"{total_loss}kg" in result


@given(
    current=st.floats(min_value=50, max_value=120),
    target=st.floats(min_value=40, max_value=119),
)
@settings(max_examples=50)
def test_invalid_target_always_raises(current: float, target: float) -> None:
    assume(target >= current)
    try:
        invoke(current, target, 0.5)
        assert False, "ValueError が発生するべき"
    except ValueError:
        pass
