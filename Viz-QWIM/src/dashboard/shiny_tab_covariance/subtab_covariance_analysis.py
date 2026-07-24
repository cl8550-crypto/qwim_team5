"""Covariance estimator analysis subtab."""

from __future__ import annotations

import typing

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import polars as pl

from shiny import module, reactive, render, ui

from src.num_methods.covariance.covariance_backtest import (
    Covariance_Backtest_Config,
    run_covariance_backtest,
    summarize_covariance_backtest,
)
from src.num_methods.covariance.covariance_data import load_etf_returns
from src.num_methods.covariance.utils_cov_corr import Covariance_Estimator


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ETF_DATA_PATH = PROJECT_ROOT / "inputs" / "raw" / "data_ETFs.csv"

ESTIMATOR_ORDER = [
    "Empirical",
    "Ledoit-Wolf",
    "Oracle Approximating Shrinkage",
    "Exponentially Weighted",
]


@module.ui
def subtab_covariance_analysis_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create covariance-analysis controls and outputs."""

    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Backtest settings"),
            ui.input_numeric(
                "input_train_window",
                "Training window",
                value=252,
                min=60,
                step=21,
            ),
            ui.input_numeric(
                "input_test_window",
                "Test window",
                value=21,
                min=5,
                step=1,
            ),
            ui.input_numeric(
                "input_step_size",
                "Step size",
                value=21,
                min=1,
                step=1,
            ),
            ui.input_action_button(
                "input_run_backtest",
                "Run covariance analysis",
                class_="btn-primary",
            ),
            width=300,
        ),
        ui.h3("Covariance Estimator Validation"),
        ui.p(
            "Compare out-of-sample covariance forecast accuracy "
            "and numerical stability."
        ),
        ui.card(
            ui.card_header("Estimator summary"),
            ui.output_data_frame("output_summary_table"),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Average Relative Frobenius Loss"),
                ui.output_plot("output_loss_plot"),
            ),
            ui.card(
                ui.card_header("Average Condition Number"),
                ui.output_plot("output_condition_plot"),
            ),
            col_widths=(6, 6),
        ),
    )


@module.server
def subtab_covariance_analysis_server(
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> dict[str, Any]:
    """Run the covariance backtest and render outputs."""

    @reactive.calc
    @reactive.event(input.input_run_backtest)
    def covariance_results() -> tuple[pl.DataFrame, pl.DataFrame]:
        returns = load_etf_returns(
            file_path=ETF_DATA_PATH,
        )

        results = run_covariance_backtest(
            returns_data=returns,
            estimators=[
                Covariance_Estimator.EMPIRICAL,
                Covariance_Estimator.LEDOIT_WOLF,
                Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE,
                Covariance_Estimator.EXPONENTIALLY_WEIGHTED,
            ],
            config=Covariance_Backtest_Config(
                train_window=int(input.input_train_window()),
                test_window=int(input.input_test_window()),
                step_size=int(input.input_step_size()),
            ),
        )

        summary = summarize_covariance_backtest(
            backtest_results=results,
        )

        return results, summary

    @output
    @render.data_frame
    def output_summary_table():
        _, summary = covariance_results()

        return render.DataGrid(
            summary.to_pandas(),
            filters=True,
            width="100%",
        )

    @output
    @render.plot
    def output_loss_plot():
        _, summary = covariance_results()

        plot_data = (
            summary.with_columns(
                pl.col("estimator")
                .replace_strict(
                    {
                        name: index
                        for index, name in enumerate(ESTIMATOR_ORDER)
                    },
                    default=999,
                )
                .alias("sort_order")
            )
            .sort("sort_order")
        )

        figure, axis = plt.subplots(figsize=(8, 5))

        axis.bar(
            plot_data["estimator"].to_list(),
            plot_data["average_relative_frobenius_loss"].to_list(),
        )

        axis.set_title("Average Relative Frobenius Loss")
        axis.set_xlabel("Estimator")
        axis.set_ylabel("Relative Frobenius loss")
        axis.tick_params(axis="x", rotation=20)

        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_condition_plot():
        _, summary = covariance_results()

        plot_data = (
            summary.with_columns(
                pl.col("estimator")
                .replace_strict(
                    {
                        name: index
                        for index, name in enumerate(ESTIMATOR_ORDER)
                    },
                    default=999,
                )
                .alias("sort_order")
            )
            .sort("sort_order")
        )

        figure, axis = plt.subplots(figsize=(8, 5))

        axis.bar(
            plot_data["estimator"].to_list(),
            plot_data["average_condition_number"].to_list(),
        )

        axis.set_title("Average Condition Number")
        axis.set_xlabel("Estimator")
        axis.set_ylabel("Condition number")
        axis.tick_params(axis="x", rotation=20)

        figure.tight_layout()
        return figure

    return {
        "covariance_results": covariance_results,
    }