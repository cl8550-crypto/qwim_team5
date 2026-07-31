"""Tests for GBI historical-policy performance reporting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.goal_based_investing.portfolio_performance import (
    build_policy_performance_table,
    calculate_portfolio_performance,
    performance_table_to_latex,
)
from src.models.goal_based_investing.risk_portfolio_policy import (
    Predefined_Portfolio_Policy,
    Risk_Profile_Band,
)


def test_calculate_portfolio_performance_uses_monthly_rebalanced_returns() -> None:
    returns = pd.DataFrame({"BIL": [0.0, 0.0, 0.0, 0.0], "XLK": [0.10, -0.05, 0.10, -0.05]})

    result = calculate_portfolio_performance(
        returns,
        weights={"BIL": 0.0, "XLK": 1.0},
        risk_free_monthly_returns=returns["BIL"],
        profile="Example",
    )

    assert result.observations == 4
    assert result.annualized_return == pytest.approx((1.10 * 0.95 * 1.10 * 0.95) ** 3 - 1)
    assert result.annualized_volatility == pytest.approx(returns["XLK"].std(ddof=1) * np.sqrt(12))
    assert result.maximum_drawdown == pytest.approx(-0.05)
    assert result.expected_shortfall_95 == pytest.approx(0.05)
    assert result.sharpe_ratio > 0


def test_policy_table_and_latex_include_the_required_presentation_metrics() -> None:
    returns = pd.DataFrame({"BIL": [0.001, 0.001, 0.001], "XLK": [0.01, -0.02, 0.03]})
    policy = Predefined_Portfolio_Policy(
        profile="Moderate",
        weights={"BIL": 0.4, "XLK": 0.6},
        expected_shortfall=0.03,
        confidence_level=0.95,
        equity_band=Risk_Profile_Band("Moderate", 0.4, 0.55),
    )

    table = build_policy_performance_table(returns, policies={"Moderate": policy})
    latex = performance_table_to_latex(table, caption="Example", label="tab:example")

    assert list(table["Risk profile"]) == ["Moderate"]
    assert {"Annualized return", "Annualized volatility", "Sharpe ratio", "Maximum drawdown", "Historical ES (95%)"}.issubset(table)
    assert "\\begin{table}" in latex
    assert "Max drawdown" in latex
    assert "tab:example" in latex
