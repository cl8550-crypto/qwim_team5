"""Detailed covariance estimator comparison subtab."""

from __future__ import annotations

import typing

from typing import Any

import matplotlib.pyplot as plt

from shiny import module, render, ui


@module.ui
def subtab_covariance_comparison_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create the estimator-comparison user interface."""

    return ui.div(
        ui.h2("Estimator Comparison"),
        ui.p("Compare covariance estimators across forecast accuracy and numerical stability."),
        ui.card(
            ui.card_header("Estimator ranking"),
            ui.p(
                "Estimators are ranked according to the selected portfolio "
                "modelling priority. A lower Priority Score indicates a stronger "
                "recommendation based on forecast accuracy, numerical stability, "
                "or their balanced combination.",
                class_="text-muted",
            ),
            ui.output_data_frame("output_summary_table"),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Forecast accuracy"),
                ui.p(
                    "Lower relative Frobenius loss indicates that the "
                    "estimated covariance matrix is closer to the "
                    "subsequently observed covariance matrix.",
                    class_="text-muted",
                ),
                ui.output_plot("output_loss_plot"),
            ),
            ui.card(
                ui.card_header("Numerical stability"),
                ui.p(
                    "A lower condition number generally indicates a more "
                    "stable covariance matrix for portfolio optimization.",
                    class_="text-muted",
                ),
                ui.output_plot("output_condition_plot"),
            ),
            col_widths=(6, 6),
        ),
    )


@module.server
def subtab_covariance_comparison_server(
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
    overview: dict[str, Any],
) -> dict[str, Any]:
    """Render comparison outputs from the shared covariance analysis."""

    covariance_results = overview["covariance_results"]
    ranked_summary = overview["ranked_summary"]

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

        plot_data = summary.sort("average_relative_frobenius_loss")

        estimators = plot_data["estimator"].to_list()
        values = plot_data["average_relative_frobenius_loss"].to_list()

        figure, axis = plt.subplots(figsize=(9, 5))

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

        figure.subplots_adjust(left=0.36, right=0.92)
        return figure

    @output
    @render.plot
    def output_condition_plot():
        _, summary = covariance_results()

        plot_data = summary.sort("average_condition_number")

        estimators = plot_data["estimator"].to_list()
        values = plot_data["average_condition_number"].to_list()

        figure, axis = plt.subplots(figsize=(9, 5))

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

        figure.subplots_adjust(left=0.36, right=0.92)
        return figure

    return {
        "covariance_results": covariance_results,
        "ranked_summary": ranked_summary,
    }
