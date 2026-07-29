"""Covariance estimator overview subtab."""

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
def subtab_covariance_overview_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create covariance-analysis controls and outputs."""

    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Backtest settings"),
            ui.p(
                "Choose the rolling estimation and evaluation windows used "
                "to compare covariance estimators.",
                class_="text-muted",
            ),
            ui.input_numeric(
                "input_train_window",
                "Training window",
                value=252,
                min=60,
                step=21,
            ),
            ui.help_text(
                "Number of historical observations used to estimate "
                "each covariance matrix."
            ),
            ui.input_numeric(
                "input_test_window",
                "Test window",
                value=21,
                min=5,
                step=1,
            ),
            ui.help_text(
                "Number of future observations used to evaluate "
                "out-of-sample accuracy."
            ),
            ui.input_numeric(
                "input_step_size",
                "Step size",
                value=21,
                min=1,
                step=1,
            ),
            ui.help_text(
                "Number of observations between successive rolling windows."
            ),
            ui.input_action_button(
                "input_run_backtest",
                "Run covariance analysis",
                class_="btn-primary w-100",
            ),
            width=300,
        ),
        ui.h2("Covariance Estimator Validation"),
        ui.p(
            "Compare out-of-sample covariance forecast accuracy and "
            "numerical stability across four estimation methods."
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Recommended estimator"),
                ui.h3(
                    ui.output_text("output_best_estimator"),
                    class_="mb-1",
                ),
                ui.p(
                    ui.output_text("output_best_estimator_reason"),
                    class_="text-muted mb-0",
                ),
            ),
            ui.card(
                ui.card_header("Analysis coverage"),
                ui.h3(
                    ui.output_text("output_window_count"),
                    class_="mb-1",
                ),
                ui.p(
                    "Rolling out-of-sample evaluation windows",
                    class_="text-muted mb-0",
                ),
            ),
            col_widths=(6, 6),
        ),
            
            ui.card(
                ui.card_header("Interpretation"),
                ui.p(ui.output_text("output_interpretation")),
            ),
        )

@module.server
def subtab_covariance_overview_server(
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

    @reactive.calc
    def ranked_summary() -> pl.DataFrame:
        """Return a client-facing estimator summary ranked by accuracy."""

        _, summary = covariance_results()

        return (
            summary.sort("average_relative_frobenius_loss")
            .with_row_index(name="Accuracy Rank", offset=1)
            .select(
                pl.col("Accuracy Rank"),
                pl.col("estimator").alias("Estimator"),
                pl.col("number_of_windows").alias("Windows"),
                pl.col("average_relative_frobenius_loss")
                .round(4)
                .alias("Relative Frobenius Loss"),
                pl.col("average_condition_number")
                .round(1)
                .alias("Condition Number"),
            )
        )

    @reactive.calc
    def best_estimator_row() -> dict[str, Any]:
        """Return the estimator with the lowest relative Frobenius loss."""

        _, summary = covariance_results()

        best_row = (
            summary.sort("average_relative_frobenius_loss")
            .head(1)
            .to_dicts()[0]
        )

        return best_row

    @output
    @render.text
    def output_best_estimator() -> str:
        best = best_estimator_row()
        return str(best["estimator"])

    @output
    @render.text
    def output_best_estimator_reason() -> str:
        best = best_estimator_row()
        loss = float(best["average_relative_frobenius_loss"])

        return (
            f"Lowest relative Frobenius loss: {loss:.4f}"
        )

    @output
    @render.text
    def output_window_count() -> str:
        best = best_estimator_row()
        windows = int(best["number_of_windows"])

        return f"{windows:,}"

    @output
    @render.data_frame
    def output_summary_table():
        return render.DataGrid(
            ranked_summary().to_pandas(),
            filters=False,
            width="100%",
            height="auto",
        )

    @output
    @render.plot
    def output_loss_plot():
        _, summary = covariance_results()

        plot_data = summary.sort(
            "average_relative_frobenius_loss"
        )

        estimators = plot_data["estimator"].to_list()
        values = plot_data[
            "average_relative_frobenius_loss"
        ].to_list()

        figure, axis = plt.subplots(figsize=(8, 5))

        bars = axis.barh(
            estimators,
            values,
        )

        axis.invert_yaxis()
        axis.set_title("Relative Frobenius Loss: Best to Worst")
        axis.set_xlabel("Average relative Frobenius loss")
        axis.set_ylabel("")

        for bar, value in zip(bars, values, strict=True):
            axis.text(
                value,
                bar.get_y() + bar.get_height() / 2,
                f" {value:.3f}",
                va="center",
            )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_condition_plot():
        _, summary = covariance_results()

        plot_data = summary.sort(
            "average_condition_number"
        )

        estimators = plot_data["estimator"].to_list()
        values = plot_data[
            "average_condition_number"
        ].to_list()

        figure, axis = plt.subplots(figsize=(8, 5))

        bars = axis.barh(
            estimators,
            values,
        )

        axis.invert_yaxis()
        axis.set_title("Condition Number: Most to Least Stable")
        axis.set_xlabel("Average condition number")
        axis.set_ylabel("")

        for bar, value in zip(bars, values, strict=True):
            axis.text(
                value,
                bar.get_y() + bar.get_height() / 2,
                f" {value:,.0f}",
                va="center",
            )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        figure.tight_layout()
        return figure

    @output
    @render.text
    def output_interpretation() -> str:
        _, summary = covariance_results()

        accuracy_row = (
            summary.sort("average_relative_frobenius_loss")
            .head(1)
            .to_dicts()[0]
        )

        stability_row = (
            summary.sort("average_condition_number")
            .head(1)
            .to_dicts()[0]
        )

        accuracy_estimator = str(accuracy_row["estimator"])
        stability_estimator = str(stability_row["estimator"])

        if accuracy_estimator == stability_estimator:
            return (
                f"{accuracy_estimator} achieved both the lowest "
                "out-of-sample covariance forecast error and the lowest "
                "average condition number. It therefore provided the "
                "strongest combination of accuracy and numerical stability "
                "for the selected backtest settings."
            )

        return (
            f"{accuracy_estimator} produced the lowest out-of-sample "
            "relative Frobenius loss, while "
            f"{stability_estimator} produced the lowest average condition "
            "number. This indicates a trade-off between forecast accuracy "
            "and numerical stability. The preferred estimator should depend "
            "on whether prediction quality or optimization robustness is "
            "more important for the intended portfolio application."
        )

    return {
        "covariance_results": covariance_results,
        "ranked_summary": ranked_summary,
        "best_estimator_row": best_estimator_row,
    }