"""Covariance-estimation data export for the QWIM client report."""

from __future__ import annotations

import polars as pl

from pathlib import Path
from typing import Any

from src.num_methods.covariance.covariance_backtest import (
    Covariance_Backtest_Config,
    run_covariance_backtest,
    summarize_covariance_backtest,
)
from src.num_methods.covariance.covariance_data import load_etf_returns
from src.num_methods.covariance.utils_cov_corr import Covariance_Estimator


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ETF_DATA_PATH = _PROJECT_ROOT / "inputs" / "raw" / "data_ETFs.csv"

_DEFAULT_TRAIN_WINDOW = 252
_DEFAULT_TEST_WINDOW = 21
_DEFAULT_STEP_SIZE = 21

_ESTIMATORS = [
    Covariance_Estimator.EMPIRICAL,
    Covariance_Estimator.LEDOIT_WOLF,
    Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE,
    Covariance_Estimator.EXPONENTIALLY_WEIGHTED,
]


def _get_public_report_data_export_module_QWIM() -> Any:
    """Return the public reporting module without creating a circular import."""

    from src.dashboard.reporting import report_data_export

    return report_data_export


def export_inputs_covariance_impl_QWIM(
    *,
    reactives_shiny: dict | None,
) -> Path:
    """Export covariance backtest settings to ``inputs_covariance.json``."""

    del reactives_shiny

    public_module = _get_public_report_data_export_module_QWIM()

    data = {
        "train_window": _DEFAULT_TRAIN_WINDOW,
        "test_window": _DEFAULT_TEST_WINDOW,
        "step_size": _DEFAULT_STEP_SIZE,
        "data_source": "data_ETFs.csv",
        "estimators": [
            "Empirical",
            "Ledoit-Wolf",
            "Oracle Approximating Shrinkage",
            "Exponentially Weighted",
        ],
    }

    output_path = (
        public_module._INPUTS_JSON_DIR
        / "inputs_covariance.json"
    )
    public_module._write_json(
        file_path=output_path,
        data=data,
    )

    return output_path


def export_outputs_covariance_impl_QWIM(
    *,
    reactives_shiny: dict | None,
) -> Path:
    """Run the covariance backtest and export report-ready results."""

    del reactives_shiny

    public_module = _get_public_report_data_export_module_QWIM()

    try:
        returns = load_etf_returns(
            file_path=_ETF_DATA_PATH,
        )

        backtest_results = run_covariance_backtest(
            returns_data=returns,
            estimators=_ESTIMATORS,
            config=Covariance_Backtest_Config(
                train_window=_DEFAULT_TRAIN_WINDOW,
                test_window=_DEFAULT_TEST_WINDOW,
                step_size=_DEFAULT_STEP_SIZE,
            ),
        )

        summary = summarize_covariance_backtest(
            backtest_results=backtest_results,
        ).sort("average_relative_frobenius_loss")

        ranked_rows: list[dict[str, Any]] = []

        for rank, row in enumerate(
            summary.to_dicts(),
            start=1,
        ):
            ranked_rows.append(
                {
                    "rank": rank,
                    "estimator": str(row["estimator"]),
                    "number_of_windows": int(
                        row["number_of_windows"]
                    ),
                    "average_relative_frobenius_loss": float(
                        row["average_relative_frobenius_loss"]
                    ),
                    "average_condition_number": float(
                        row["average_condition_number"]
                    ),
                }
            )

        best_row = ranked_rows[0] if ranked_rows else {}



        diagnostic_summary = (
            backtest_results.group_by("estimator")
            .agg(
                pl.col("relative_frobenius_loss")
                .std()
                .alias("loss_volatility"),
                pl.col("condition_number")
                .median()
                .alias("median_condition_number"),
                pl.col("condition_number")
                .max()
                .alias("maximum_condition_number"),
                pl.col("minimum_eigenvalue")
                .min()
                .alias("minimum_eigenvalue"),
                (pl.col("minimum_eigenvalue") <= 0)
                .sum()
                .alias("non_positive_eigenvalue_windows"),
                pl.col("volatility_forecast_error")
                .abs()
                .mean()
                .alias("mean_absolute_volatility_error"),
            )
            .sort("loss_volatility")
            .to_dicts()
        )

        data = {
            "analysis_success": True,
            "best_estimator": best_row.get(
                "estimator",
                "N/A",
            ),
            "best_relative_frobenius_loss": best_row.get(
                "average_relative_frobenius_loss",
                0.0,
            ),
            "number_of_windows": best_row.get(
                "number_of_windows",
                0,
            ),
            "ranked_estimators": ranked_rows,
            "diagnostics": diagnostic_summary,
            "rolling_results": backtest_results.to_dicts(),
        }

    except Exception as exc:  # noqa: BLE001
        public_module._logger.warning(
            "Covariance report export failed: %s",
            exc,
        )

        data = {
            "analysis_success": False,
            "best_estimator": "N/A",
            "best_relative_frobenius_loss": 0.0,
            "number_of_windows": 0,
            "ranked_estimators": [],
            "diagnostics": [],
            "rolling_results": [],
        }

    output_path = (
        public_module._OUTPUTS_JSON_DIR
        / "outputs_covariance.json"
    )
    public_module._write_json(
        file_path=output_path,
        data=data,
    )

    return output_path