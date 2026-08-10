"""Smoke test using the project's real ETF dataset."""

from src.num_methods.covariance.covariance_backtest import (
    Covariance_Backtest_Config,
    run_covariance_backtest,
    summarize_covariance_backtest,
)
from src.num_methods.covariance.covariance_data import (
    load_etf_returns,
)
from src.num_methods.covariance.utils_cov_corr import (
    Covariance_Estimator,
)


returns_data = load_etf_returns(
    file_path="inputs/raw/data_ETFs.csv"
)

print("Returns shape:", returns_data.shape)
print(returns_data.head())

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

print("\nRolling results:")
print(results.head())

print("\nEstimator summary:")
print(summary)