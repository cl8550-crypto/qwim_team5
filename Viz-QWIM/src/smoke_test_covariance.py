"""Quick smoke test for the covariance backtest engine."""

import numpy as np
import polars as pl

from src.num_methods.covariance.covariance_backtest import (
    Covariance_Backtest_Config,
    run_covariance_backtest,
    summarize_covariance_backtest,
)
from src.num_methods.covariance.utils_cov_corr import (
    Covariance_Estimator,
)


rng = np.random.default_rng(42)

number_of_observations = 400

returns_data = pl.DataFrame(
    {
        "Date": pl.date_range(
            start=pl.date(2024, 1, 1),
            end=pl.date(2025, 2, 3),
            interval="1d",
            eager=True,
        )[:number_of_observations],
        "Asset_A": rng.normal(0.0004, 0.01, number_of_observations),
        "Asset_B": rng.normal(0.0003, 0.012, number_of_observations),
        "Asset_C": rng.normal(0.0002, 0.008, number_of_observations),
    }
)

results = run_covariance_backtest(
    returns_data=returns_data,
    estimators=[
        Covariance_Estimator.EMPIRICAL,
        Covariance_Estimator.LEDOIT_WOLF,
        Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE,
        Covariance_Estimator.EXPONENTIALLY_WEIGHTED,
    ],
    config=Covariance_Backtest_Config(
        train_window=252,
        test_window=21,
        step_size=21,
    ),
)

summary = summarize_covariance_backtest(
    backtest_results=results
)

print(results.head())
print(summary)