r"""A transparent, deterministic baseline for goal-based investing.

The baseline answers the first planning question for one financial goal:
whether a current balance, recurring end-of-year contribution, and annual
return assumption are enough to meet a target amount at the goal horizon.
It can also score externally supplied terminal-value scenarios.  It does not
select securities or optimise portfolio weights; those decisions belong to
the portfolio-optimisation layer.
"""

from __future__ import annotations

import math

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True, slots=True)
class Goal_Assessment:  # noqa: N801
    """Result of evaluating a goal against deterministic or scenario outcomes.

    ``success_probability`` is ``None`` for a deterministic assessment and a
    value in ``[0, 1]`` when terminal-value scenarios were supplied.
    """

    goal_name: str
    target_amount: float
    projected_amount: float
    funding_ratio: float
    shortfall_amount: float
    surplus_amount: float
    is_funded: bool
    success_probability: float | None = None


class Goal_Based_Investing_Baseline:  # noqa: N801
    """Evaluate one financial goal using annual compounding.

    Contributions are assumed to occur at each year end.  For a horizon
    ``n``, initial balance ``B``, annual contribution ``C``, and annual return
    ``r``, the projected value is ``B(1+r)^n + C(((1+r)^n-1)/r)``.  The
    contribution term is ``Cn`` when ``r`` is zero.
    """

    def __init__(
        self,
        *,
        goal_name: str,
        target_amount: float,
        current_amount: float,
        years_to_goal: int,
        annual_contribution: float = 0.0,
    ) -> None:
        self.goal_name = self._validate_name(goal_name)
        self.target_amount = self._validate_amount(target_amount, "target_amount", positive=True)
        self.current_amount = self._validate_amount(current_amount, "current_amount")
        self.years_to_goal = self._validate_years(years_to_goal)
        self.annual_contribution = self._validate_amount(
            annual_contribution,
            "annual_contribution",
        )

    @staticmethod
    def _validate_name(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise Exception_Validation_Input(
                "goal_name must be a non-empty string",
                field_name="goal_name",
                expected_type=str,
                actual_value=value,
            )
        return value.strip()

    @staticmethod
    def _validate_amount(value: float, field_name: str, *, positive: bool = False) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise Exception_Validation_Input(
                f"{field_name} must be a finite non-negative number",
                field_name=field_name,
                expected_type=float,
                actual_value=value,
            )
        amount = float(value)
        if not math.isfinite(amount) or amount < 0.0 or (positive and amount == 0.0):
            qualifier = "positive" if positive else "non-negative"
            raise Exception_Validation_Input(
                f"{field_name} must be a finite {qualifier} number",
                field_name=field_name,
                expected_type=float,
                actual_value=value,
            )
        return amount

    @staticmethod
    def _validate_years(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise Exception_Validation_Input(
                "years_to_goal must be a non-negative integer",
                field_name="years_to_goal",
                expected_type=int,
                actual_value=value,
            )
        return value

    @staticmethod
    def _validate_return(value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise Exception_Validation_Input(
                "annual_return must be a finite number greater than -1.0",
                field_name="annual_return",
                expected_type=float,
                actual_value=value,
            )
        annual_return = float(value)
        if not math.isfinite(annual_return) or annual_return <= -1.0:
            raise Exception_Validation_Input(
                "annual_return must be a finite number greater than -1.0",
                field_name="annual_return",
                expected_type=float,
                actual_value=value,
            )
        return annual_return

    def project_amount(self, *, annual_return: float) -> float:
        """Return the terminal value under the supplied annual return."""
        rate = self._validate_return(annual_return)
        periods = self.years_to_goal
        growth_factor = (1.0 + rate) ** periods
        contribution_value = self.annual_contribution * periods
        if rate != 0.0:
            contribution_value = self.annual_contribution * (growth_factor - 1.0) / rate
        return self.current_amount * growth_factor + contribution_value

    def assess(self, *, annual_return: float) -> Goal_Assessment:
        """Assess the goal using one deterministic annual-return assumption."""
        return self._build_assessment(projected_amount=self.project_amount(annual_return=annual_return))

    def assess_terminal_values(self, terminal_values: Iterable[float]) -> Goal_Assessment:
        """Assess the goal across externally generated terminal-value scenarios.

        The reported projection is the mean terminal value, while funding
        metrics compare each scenario with the same target amount.
        """
        values = np.asarray(list(terminal_values), dtype=float)
        if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all() or (values < 0.0).any():
            raise Exception_Validation_Input(
                "terminal_values must be a non-empty one-dimensional sequence of finite non-negative numbers",
                field_name="terminal_values",
                expected_type="Iterable[float]",
                actual_value=terminal_values,
            )
        probability = float(np.mean(values >= self.target_amount))
        return self._build_assessment(
            projected_amount=float(np.mean(values)),
            success_probability=probability,
        )

    def _build_assessment(
        self,
        *,
        projected_amount: float,
        success_probability: float | None = None,
    ) -> Goal_Assessment:
        shortfall = max(0.0, self.target_amount - projected_amount)
        surplus = max(0.0, projected_amount - self.target_amount)
        return Goal_Assessment(
            goal_name=self.goal_name,
            target_amount=self.target_amount,
            projected_amount=projected_amount,
            funding_ratio=projected_amount / self.target_amount,
            shortfall_amount=shortfall,
            surplus_amount=surplus,
            is_funded=projected_amount >= self.target_amount,
            success_probability=success_probability,
        )
