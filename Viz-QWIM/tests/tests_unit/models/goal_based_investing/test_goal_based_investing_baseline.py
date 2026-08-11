"""Unit tests for the goal-based investing baseline."""

from __future__ import annotations

import pytest

from src.models.goal_based_investing import Goal_Based_Investing_Baseline
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.fixture()
def retirement_goal() -> Goal_Based_Investing_Baseline:
    """A simple retirement goal with no additional contributions."""
    return Goal_Based_Investing_Baseline(
        goal_name="Retirement",
        target_amount=150_000.0,
        current_amount=100_000.0,
        years_to_goal=10,
    )


@pytest.mark.unit()
def test_assess_compounds_current_amount(retirement_goal: Goal_Based_Investing_Baseline) -> None:
    """The deterministic assessment uses annual compounding."""
    assessment = retirement_goal.assess(annual_return=0.05)

    assert assessment.projected_amount == pytest.approx(162_889.4627)
    assert assessment.funding_ratio == pytest.approx(1.085929751)
    assert assessment.is_funded is True
    assert assessment.shortfall_amount == 0.0
    assert assessment.success_probability is None


@pytest.mark.unit()
def test_zero_return_uses_uncompounded_end_of_year_contributions() -> None:
    """A zero-rate projection includes every annual contribution exactly once."""
    goal = Goal_Based_Investing_Baseline(
        goal_name="Education",
        target_amount=200_000.0,
        current_amount=100_000.0,
        years_to_goal=5,
        annual_contribution=10_000.0,
    )

    assessment = goal.assess(annual_return=0.0)

    assert assessment.projected_amount == 150_000.0
    assert assessment.shortfall_amount == 50_000.0
    assert assessment.surplus_amount == 0.0
    assert assessment.is_funded is False


@pytest.mark.unit()
def test_scenario_assessment_reports_mean_and_success_probability(
    retirement_goal: Goal_Based_Investing_Baseline,
) -> None:
    """Scenario success is the share of terminal values meeting the goal."""
    assessment = retirement_goal.assess_terminal_values([140_000.0, 150_000.0, 170_000.0])

    assert assessment.projected_amount == pytest.approx(153_333.3333)
    assert assessment.success_probability == pytest.approx(2.0 / 3.0)
    assert assessment.is_funded is True


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("kwargs", "annual_return"),
    [
        ({"target_amount": 0.0}, 0.05),
        ({"years_to_goal": -1}, 0.05),
        ({}, -1.0),
    ],
)
def test_invalid_goal_inputs_raise_validation_error(
    kwargs: dict[str, float | int],
    annual_return: float,
) -> None:
    """Invalid goal fields and invalid return assumptions fail early."""
    fields: dict[str, object] = {
        "goal_name": "Home deposit",
        "target_amount": 100_000.0,
        "current_amount": 10_000.0,
        "years_to_goal": 5,
    }
    fields.update(kwargs)

    if kwargs:
        with pytest.raises(Exception_Validation_Input):
            Goal_Based_Investing_Baseline(**fields)
    else:
        goal = Goal_Based_Investing_Baseline(**fields)
        with pytest.raises(Exception_Validation_Input):
            goal.assess(annual_return=annual_return)


@pytest.mark.unit()
def test_invalid_terminal_values_raise_validation_error(
    retirement_goal: Goal_Based_Investing_Baseline,
) -> None:
    """Scenario inputs must be finite, non-negative, and one-dimensional."""
    with pytest.raises(Exception_Validation_Input):
        retirement_goal.assess_terminal_values([100_000.0, float("nan")])
