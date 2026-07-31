"""Covariance estimator diagnostics subtab."""

from __future__ import annotations

import typing

from typing import Any

import matplotlib.pyplot as plt
import polars as pl

from shiny import module, render, ui


@module.ui
def subtab_covariance_diagnostics_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create the covariance-diagnostics user interface."""

    return ui.div(
        ui.h2("Diagnostics"),
        ui.p(
            "Inspect how covariance-estimator accuracy and matrix stability "
            "change across rolling out-of-sample windows."
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Rolling forecast error"),
                ui.p(
                    "Relative Frobenius loss through time. Lower values "
                    "indicate more accurate covariance forecasts.",
                    class_="text-muted",
                ),
                ui.output_plot("output_rolling_loss_plot"),
            ),
            ui.card(
                ui.card_header("Rolling condition number"),
                ui.p(
                    "Condition number through time. Lower values generally "
                    "indicate better numerical stability.",
                    class_="text-muted",
                ),
                ui.output_plot("output_rolling_condition_plot"),
            ),
            col_widths=(6, 6),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Minimum eigenvalue"),
                ui.p(
                    "A positive minimum eigenvalue indicates a positive-"
                    "definite covariance estimate.",
                    class_="text-muted",
                ),
                ui.output_plot("output_minimum_eigenvalue_plot"),
            ),
            ui.card(
                ui.card_header("Volatility forecast error"),
                ui.p(
                    "Difference between estimated and subsequently realized "
                    "portfolio volatility.",
                    class_="text-muted",
                ),
                ui.output_plot("output_volatility_error_plot"),
            ),
            col_widths=(6, 6),
        ),
        ui.card(
            ui.card_header("Stability summary"),
            ui.output_data_frame("output_diagnostics_table"),
        ),
    )


@module.server
def subtab_covariance_diagnostics_server(
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
    overview: dict[str, Any],
) -> dict[str, Any]:
    """Render rolling diagnostics from the shared covariance backtest."""

    covariance_results = overview["covariance_results"]

    @output
    @render.plot
    def output_rolling_loss_plot():
        results, _ = covariance_results()

        figure, axis = plt.subplots(figsize=(9, 5))

        for estimator in results["estimator"].unique().to_list():
            estimator_data = (
                results.filter(pl.col("estimator") == estimator)
                .sort("test_start")
            )

            axis.plot(
                estimator_data["test_start"].to_list(),
                estimator_data["relative_frobenius_loss"].to_list(),
                label=estimator,
                linewidth=1.5,
            )

        axis.set_title("Rolling Relative Frobenius Loss")
        axis.set_xlabel("Test period")
        axis.set_ylabel("Relative Frobenius loss")
        axis.legend(fontsize=8)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", rotation=30)

        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_rolling_condition_plot():
        results, _ = covariance_results()

        figure, axis = plt.subplots(figsize=(9, 5))

        for estimator in results["estimator"].unique().to_list():
            estimator_data = (
                results.filter(pl.col("estimator") == estimator)
                .sort("test_start")
            )

            axis.plot(
                estimator_data["test_start"].to_list(),
                estimator_data["condition_number"].to_list(),
                label=estimator,
                linewidth=1.5,
            )

        axis.set_title("Rolling Condition Number")
        axis.set_xlabel("Test period")
        axis.set_ylabel("Condition number")
        axis.legend(fontsize=8)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", rotation=30)

        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_minimum_eigenvalue_plot():
        results, _ = covariance_results()

        figure, axis = plt.subplots(figsize=(9, 5))

        for estimator in results["estimator"].unique().to_list():
            estimator_data = (
                results.filter(pl.col("estimator") == estimator)
                .sort("test_start")
            )

            axis.plot(
                estimator_data["test_start"].to_list(),
                estimator_data["minimum_eigenvalue"].to_list(),
                label=estimator,
                linewidth=1.5,
            )

        axis.axhline(
            0.0,
            linewidth=1.0,
            linestyle="--",
        )
        axis.set_title("Rolling Minimum Eigenvalue")
        axis.set_xlabel("Test period")
        axis.set_ylabel("Minimum eigenvalue")
        axis.legend(fontsize=8)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", rotation=30)

        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_volatility_error_plot():
        results, _ = covariance_results()

        figure, axis = plt.subplots(figsize=(9, 5))

        for estimator in results["estimator"].unique().to_list():
            estimator_data = (
                results.filter(pl.col("estimator") == estimator)
                .sort("test_start")
            )

            axis.plot(
                estimator_data["test_start"].to_list(),
                estimator_data["volatility_forecast_error"].to_list(),
                label=estimator,
                linewidth=1.5,
            )

        axis.axhline(
            0.0,
            linewidth=1.0,
            linestyle="--",
        )
        axis.set_title("Rolling Volatility Forecast Error")
        axis.set_xlabel("Test period")
        axis.set_ylabel("Forecast error")
        axis.legend(fontsize=8)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", rotation=30)

        figure.tight_layout()
        return figure

    @output
    @render.data_frame
    def output_diagnostics_table():
        results, _ = covariance_results()

        diagnostics = (
            results.group_by("estimator")
            .agg(
                pl.col("relative_frobenius_loss")
                .std()
                .round(4)
                .alias("Loss Volatility"),
                pl.col("condition_number")
                .median()
                .round(1)
                .alias("Median Condition Number"),
                pl.col("condition_number")
                .max()
                .round(1)
                .alias("Maximum Condition Number"),
                pl.col("minimum_eigenvalue")
                .min()
                .round(6)
                .alias("Minimum Eigenvalue"),
                (pl.col("minimum_eigenvalue") <= 0)
                .sum()
                .alias("Non-Positive Eigenvalue Windows"),
                pl.col("volatility_forecast_error")
                .abs()
                .mean()
                .round(4)
                .alias("Mean Absolute Volatility Error"),
            )
            .rename({"estimator": "Estimator"})
            .sort("Loss Volatility")
        )

        return render.DataGrid(
            diagnostics.to_pandas(),
            filters=False,
            width="100%",
            height="auto",
        )

    return {
        "covariance_results": covariance_results,
    }