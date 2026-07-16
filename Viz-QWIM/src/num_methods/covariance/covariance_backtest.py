"""Rolling backtest engine for covariance-matrix estimators."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.num_methods.covariance.covariance_losses import (
    calculate_frobenius_loss,
    calculate_gaussian_log_likelihood_loss,
    calculate_portfolio_variance_loss,
    calculate_relative_frobenius_loss,
)
from src.num_methods.covariance.utils_cov_corr import (
    Covariance_Estimator,
    Covariance_Matrix,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@dataclass(frozen=True)
class Covariance_Backtest_Config:
    """Configuration for a rolling covariance-estimation backtest."""

    train_window: int = 252
    test_window: int = 21
    step_size: int = 21
    annualization_factor: int = 252


def _validate_returns_data(*, returns_data: pl.DataFrame) -> None:
    """Validate the returns dataset used in the backtest."""
    if not isinstance(returns_data, pl.DataFrame):
        raise Exception_Validation_Input(
            "returns_data must be a Polars DataFrame."
        )

    if returns_data.is_empty():
        raise Exception_Validation_Input(
            "returns_data cannot be empty."
        )

    if "Date" not in returns_data.columns:
        raise Exception_Validation_Input(
            "returns_data must contain a 'Date' column."
        )

    asset_columns = [
        column for column in returns_data.columns if column != "Date"
    ]

    if len(asset_columns) < 2:
        raise Exception_Validation_Input(
            "At least two asset-return columns are required."
        )


def _validate_config(*, config: Covariance_Backtest_Config) -> None:
    """Validate rolling-window configuration."""
    if config.train_window < 3:
        raise Exception_Validation_Input(
            "train_window must contain at least 3 observations."
        )

    if config.test_window < 2:
        raise Exception_Validation_Input(
            "test_window must contain at least 2 observations."
        )

    if config.step_size < 1:
        raise Exception_Validation_Input(
            "step_size must be at least 1."
        )

    if config.annualization_factor < 1:
        raise Exception_Validation_Input(
            "annualization_factor must be positive."
        )


def _realized_covariance(
    *,
    test_data: pl.DataFrame,
    annualization_factor: int,
) -> np.ndarray:
    """Calculate realized covariance from the out-of-sample test window."""
    asset_columns = [
        column for column in test_data.columns if column != "Date"
    ]

    test_returns = test_data.select(asset_columns).to_numpy()

    covariance_matrix = np.cov(
        test_returns,
        rowvar=False,
        ddof=1,
    )

    return covariance_matrix * annualization_factor


def _annualize_covariance(
    *,
    covariance_matrix: np.ndarray,
    annualization_factor: int,
) -> np.ndarray:
    """Annualize a daily covariance matrix."""
    return covariance_matrix * annualization_factor


def _equal_weight_portfolio(*, number_of_assets: int) -> np.ndarray:
    """Create an equal-weight portfolio."""
    return np.full(
        shape=number_of_assets,
        fill_value=1.0 / number_of_assets,
        dtype=float,
    )


def run_covariance_backtest(
    *,
    returns_data: pl.DataFrame,
    estimators: list[Covariance_Estimator],
    config: Covariance_Backtest_Config | None = None,
) -> pl.DataFrame:
    """Run a rolling out-of-sample covariance-estimator comparison.

    Parameters
    ----------
    returns_data
        Polars DataFrame containing a ``Date`` column and asset-return columns.
    estimators
        Covariance estimators to compare.
    config
        Rolling-window and annualization settings.

    Returns
    -------
    pl.DataFrame
        One row per estimator and rolling test window, containing covariance
        losses and matrix diagnostics.
    """
    _validate_returns_data(returns_data=returns_data)

    if not estimators:
        raise Exception_Validation_Input(
            "At least one covariance estimator must be supplied."
        )

    if config is None:
        config = Covariance_Backtest_Config()

    _validate_config(config=config)

    returns_data = returns_data.sort("Date")

    total_observations = returns_data.height
    required_observations = config.train_window + config.test_window

    if total_observations < required_observations:
        raise Exception_Validation_Input(
            (
                f"Insufficient observations: received {total_observations}, "
                f"but at least {required_observations} are required."
            )
        )

    asset_columns = [
        column for column in returns_data.columns if column != "Date"
    ]
    number_of_assets = len(asset_columns)

    equal_weights = _equal_weight_portfolio(
        number_of_assets=number_of_assets
    )

    result_rows: list[dict[str, object]] = []

    last_start_index = (
        total_observations
        - config.train_window
        - config.test_window
    )

    for start_index in range(
        0,
        last_start_index + 1,
        config.step_size,
    ):
        train_end_index = start_index + config.train_window
        test_end_index = train_end_index + config.test_window

        train_data = returns_data.slice(
            start_index,
            config.train_window,
        )
        test_data = returns_data.slice(
            train_end_index,
            config.test_window,
        )

        realized_covariance = _realized_covariance(
            test_data=test_data,
            annualization_factor=config.annualization_factor,
        )

        train_start_date = train_data["Date"][0]
        train_end_date = train_data["Date"][-1]
        test_start_date = test_data["Date"][0]
        test_end_date = test_data["Date"][-1]

        for estimator in estimators:
            estimated_covariance_object = Covariance_Matrix(
                data_returns=train_data,
                estimator=estimator,
            )

            estimated_covariance = _annualize_covariance(
                covariance_matrix=estimated_covariance_object.m_cov_matrix,
                annualization_factor=config.annualization_factor,
            )

            eigenvalues = np.linalg.eigvalsh(estimated_covariance)

            estimated_portfolio_variance = float(
                equal_weights.T
                @ estimated_covariance
                @ equal_weights
            )

            realized_portfolio_variance = float(
                equal_weights.T
                @ realized_covariance
                @ equal_weights
            )

            result_rows.append(
                {
                    "estimator": estimator.value,
                    "train_start": train_start_date,
                    "train_end": train_end_date,
                    "test_start": test_start_date,
                    "test_end": test_end_date,
                    "frobenius_loss": calculate_frobenius_loss(
                        estimated_covariance=estimated_covariance,
                        realized_covariance=realized_covariance,
                    ),
                    "relative_frobenius_loss": (
                        calculate_relative_frobenius_loss(
                            estimated_covariance=estimated_covariance,
                            realized_covariance=realized_covariance,
                        )
                    ),
                    "portfolio_variance_loss": (
                        calculate_portfolio_variance_loss(
                            estimated_covariance=estimated_covariance,
                            realized_covariance=realized_covariance,
                            portfolio_weights=equal_weights,
                        )
                    ),
                    "gaussian_loss": (
                        calculate_gaussian_log_likelihood_loss(
                            estimated_covariance=estimated_covariance,
                            realized_covariance=realized_covariance,
                        )
                    ),
                    "estimated_portfolio_volatility": float(
                        np.sqrt(max(estimated_portfolio_variance, 0.0))
                    ),
                    "realized_portfolio_volatility": float(
                        np.sqrt(max(realized_portfolio_variance, 0.0))
                    ),
                    "volatility_forecast_error": float(
                        np.sqrt(max(estimated_portfolio_variance, 0.0))
                        - np.sqrt(max(realized_portfolio_variance, 0.0))
                    ),
                    "minimum_eigenvalue": float(eigenvalues.min()),
                    "maximum_eigenvalue": float(eigenvalues.max()),
                    "condition_number": float(
                        np.linalg.cond(estimated_covariance)
                    ),
                }
            )

    return pl.DataFrame(result_rows)


def summarize_covariance_backtest(
    *,
    backtest_results: pl.DataFrame,
) -> pl.DataFrame:
    """Summarize average estimator performance across all test windows."""
    if backtest_results.is_empty():
        raise Exception_Validation_Input(
            "backtest_results cannot be empty."
        )

    return (
        backtest_results.group_by("estimator")
        .agg(
            pl.len().alias("number_of_windows"),
            pl.col("frobenius_loss")
            .mean()
            .alias("average_frobenius_loss"),
            pl.col("relative_frobenius_loss")
            .mean()
            .alias("average_relative_frobenius_loss"),
            pl.col("portfolio_variance_loss")
            .mean()
            .alias("average_portfolio_variance_loss"),
            pl.col("gaussian_loss")
            .mean()
            .alias("average_gaussian_loss"),
            pl.col("estimated_portfolio_volatility")
            .mean()
            .alias("average_estimated_volatility"),
            pl.col("realized_portfolio_volatility")
            .mean()
            .alias("average_realized_volatility"),
            pl.col("volatility_forecast_error")
            .abs()
            .mean()
            .alias("average_absolute_volatility_error"),
            pl.col("condition_number")
            .mean()
            .alias("average_condition_number"),
            pl.col("minimum_eigenvalue")
            .min()
            .alias("minimum_eigenvalue"),
        )
        .sort("average_relative_frobenius_loss")
    )