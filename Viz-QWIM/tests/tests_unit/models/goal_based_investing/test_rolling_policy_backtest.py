"""Tests for the offline six-ETF rolling CVaR policy backtest."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.goal_based_investing.rolling_policy_backtest import (
    MODERATE_BENCHMARK_WEIGHTS,
    SIX_ETF_ASSETS,
    backtest_fixed_cvar_policies,
    backtest_fixed_weight_benchmark,
    backtest_rolling_cvar_policies,
    rolling_backtest_performance_table,
)


def test_rolling_backtest_uses_only_post_lookback_returns_and_returns_all_profiles() -> None:
    dates = pd.date_range("2020-01-31", periods=15, freq="ME")
    returns = pd.DataFrame(
        {
            asset: np.linspace(-0.01 + index * 0.001, 0.02 + index * 0.001, len(dates))
            for index, asset in enumerate(SIX_ETF_ASSETS)
        },
        index=dates,
    )

    results = backtest_rolling_cvar_policies(returns, lookback_months=12, rebalance_months=3)
    table = rolling_backtest_performance_table(results)

    assert set(results) == {
        "Conservative",
        "Moderate Conservative",
        "Moderate",
        "Moderate Aggressive",
        "Aggressive",
    }
    assert all(len(result.monthly_returns) == 3 for result in results.values())
    assert all(result.rebalance_count == 1 for result in results.values())
    assert set(table["Risk profile"]) == set(results)
    assert set(table["Monthly observations"]) == {3}


def test_fixed_comparator_has_the_same_out_of_sample_months_as_rolling_policy() -> None:
    dates = pd.date_range("2020-01-31", periods=15, freq="ME")
    returns = pd.DataFrame(
        {
            asset: np.linspace(-0.01 + index * 0.001, 0.02 + index * 0.001, len(dates))
            for index, asset in enumerate(SIX_ETF_ASSETS)
        },
        index=dates,
    )

    fixed = backtest_fixed_cvar_policies(returns, lookback_months=12, rebalance_months=3)

    assert all(len(result.monthly_returns) == 3 for result in fixed.values())
    assert all(result.target_weights.shape == (1, 6) for result in fixed.values())


def test_fixed_weight_benchmark_matches_the_rolling_out_of_sample_window() -> None:
    dates = pd.date_range("2020-01-31", periods=15, freq="ME")
    returns = pd.DataFrame(
        {
            asset: np.linspace(-0.01 + index * 0.001, 0.02 + index * 0.001, len(dates))
            for index, asset in enumerate(SIX_ETF_ASSETS)
        },
        index=dates,
    )

    benchmark = backtest_fixed_weight_benchmark(
        returns,
        weights_by_asset=MODERATE_BENCHMARK_WEIGHTS,
        lookback_months=12,
    )

    assert len(benchmark.monthly_returns) == 3
    assert benchmark.profile == "Benchmark"
    assert benchmark.target_weights.iloc[0].sum() == 1.0
