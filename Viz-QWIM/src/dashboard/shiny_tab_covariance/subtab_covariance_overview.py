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


def automatic_backtest_config(
    *,
    investment_horizon: str,
    review_frequency: str,
) -> Covariance_Backtest_Config:
    """Translate customer-friendly portfolio inputs into backtest settings."""
    horizon_training_windows = {
        "Short term (1-3 years)": 126,
        "Medium term (4-10 years)": 252,
        "Long term (10+ years)": 504,
    }
    review_windows = {
        "Monthly": 21,
        "Quarterly": 63,
        "Annually": 126,
    }

    if investment_horizon not in horizon_training_windows:
        raise ValueError(f"Unsupported investment horizon: {investment_horizon}")
    if review_frequency not in review_windows:
        raise ValueError(f"Unsupported review frequency: {review_frequency}")

    training_window = horizon_training_windows[investment_horizon]
    evaluation_window = review_windows[review_frequency]
    return Covariance_Backtest_Config(
        train_window=training_window,
        test_window=evaluation_window,
        step_size=evaluation_window,
    )


def rank_covariance_estimators(
    *,
    summary: pl.DataFrame,
    portfolio_priority: str,
) -> pl.DataFrame:
    """Rank estimators according to the customer's modelling priority."""
    accuracy_rank = pl.col("average_relative_frobenius_loss").rank(method="average")
    stability_rank = pl.col("average_condition_number").rank(method="average")

    if portfolio_priority == "Accuracy":
        recommendation_score = accuracy_rank
    elif portfolio_priority == "Stability":
        recommendation_score = stability_rank
    elif portfolio_priority == "Balanced":
        recommendation_score = (accuracy_rank + stability_rank) / 2.0
    else:
        raise ValueError(f"Unsupported portfolio priority: {portfolio_priority}")

    return (
        summary.with_columns(recommendation_score.alias("recommendation_score"))
        .sort(["recommendation_score", "average_relative_frobenius_loss"])
        .with_row_index(name="Recommendation Rank", offset=1)
    )


@module.ui
def subtab_covariance_overview_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:
    """Create covariance-analysis controls and outputs."""
    del data_utils, data_inputs
    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Portfolio preferences"),
            ui.p(
                "Tell us how this portfolio will be managed. "
                "The model will select the technical covariance settings automatically.",
                class_="text-muted",
            ),
            ui.input_select(
                "input_investment_horizon",
                "Investment horizon",
                choices=[
                    "Short term (1-3 years)",
                    "Medium term (4-10 years)",
                    "Long term (10+ years)",
                ],
                selected="Medium term (4-10 years)",
            ),
            ui.help_text("How long the client expects to keep the portfolio invested."),
            ui.input_select(
                "input_review_frequency",
                "Portfolio review frequency",
                choices=["Monthly", "Quarterly", "Annually"],
                selected="Monthly",
            ),
            ui.help_text("How often the portfolio is expected to be reviewed or rebalanced."),
            ui.input_select(
                "input_portfolio_priority",
                "Portfolio modelling priority",
                choices={
                    "Balanced": "Balanced recommendation",
                    "Accuracy": "Forecast accuracy",
                    "Stability": "Optimization stability",
                },
                selected="Balanced",
            ),
            ui.help_text(
                "Choose whether the covariance recommendation should emphasize "
                "forecast accuracy, numerical stability, or both."
            ),
            ui.card(
                ui.card_header("Automatically selected settings"),
                ui.card_body(ui.output_ui("output_automatic_settings")),
                class_="mt-3",
            ),
            ui.input_action_button(
                "input_run_backtest",
                "Generate covariance recommendation",
                class_="btn-primary w-100 mt-3",
            ),
            width=320,
        ),
        ui.h2("Personalized Covariance Recommendation"),
        ui.p(
            "The model compares four covariance estimators and recommends the "
            "most suitable method for the client's portfolio preferences."
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Recommended estimator"),
                ui.h3(ui.output_text("output_best_estimator"), class_="mb-1"),
                ui.p(
                    ui.output_text("output_best_estimator_reason"),
                    class_="text-muted mb-0",
                ),
            ),
            ui.card(
                ui.card_header("Analysis coverage"),
                ui.h3(ui.output_text("output_window_count"), class_="mb-1"),
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
    del session, data_utils, data_inputs, reactives_shiny

    @output
    @render.ui
    def output_automatic_settings() -> Any:
        """Display the technical settings selected from portfolio preferences."""
        config = automatic_backtest_config(
            investment_horizon=str(input.input_investment_horizon()),
            review_frequency=str(input.input_review_frequency()),
        )
        return ui.tags.dl(
            ui.tags.dt("Historical estimation period"),
            ui.tags.dd(f"{config.train_window} daily observations"),
            ui.tags.dt("Evaluation period"),
            ui.tags.dd(f"{config.test_window} daily observations"),
            ui.tags.dt("Rolling step"),
            ui.tags.dd(f"{config.step_size} daily observations"),
            class_="mb-0",
        )

    @reactive.calc
    @reactive.event(input.input_run_backtest)
    def covariance_results() -> tuple[pl.DataFrame, pl.DataFrame]:
        """Run the estimator comparison using automatic technical settings."""
        returns = load_etf_returns(file_path=ETF_DATA_PATH)
        config = automatic_backtest_config(
            investment_horizon=str(input.input_investment_horizon()),
            review_frequency=str(input.input_review_frequency()),
        )
        results = run_covariance_backtest(
            returns_data=returns,
            estimators=[
                Covariance_Estimator.EMPIRICAL,
                Covariance_Estimator.LEDOIT_WOLF,
                Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE,
                Covariance_Estimator.EXPONENTIALLY_WEIGHTED,
            ],
            config=config,
        )
        summary = summarize_covariance_backtest(backtest_results=results)
        return results, summary

    @reactive.calc
    def ranked_results() -> pl.DataFrame:
        """Return the complete estimator ranking for the selected priority."""
        _, summary = covariance_results()
        return rank_covariance_estimators(
            summary=summary,
            portfolio_priority=str(input.input_portfolio_priority()),
        )

    @reactive.calc
    def ranked_summary() -> pl.DataFrame:
        """Return a client-facing estimator summary."""
        return ranked_results().select(
            pl.col("Recommendation Rank"),
            pl.col("estimator").alias("Estimator"),
            pl.col("number_of_windows").alias("Windows"),
            pl.col("average_relative_frobenius_loss").round(4).alias("Relative Frobenius Loss"),
            pl.col("average_condition_number").round(1).alias("Condition Number"),
            pl.col("recommendation_score").round(2).alias("Priority Score"),
        )

    @reactive.calc
    def best_estimator_row() -> dict[str, Any]:
        """Return the best estimator for the selected portfolio priority."""
        return ranked_results().head(1).to_dicts()[0]

    @output
    @render.text
    def output_best_estimator() -> str:
        return str(best_estimator_row()["estimator"])

    @output
    @render.text
    def output_best_estimator_reason() -> str:
        """Explain why the estimator was recommended."""
        best = best_estimator_row()
        priority = str(input.input_portfolio_priority())
        loss = float(best["average_relative_frobenius_loss"])
        condition_number = float(best["average_condition_number"])

        if priority == "Accuracy":
            return f"Selected for the lowest covariance forecast error: {loss:.4f}."
        if priority == "Stability":
            return (
                "Selected for the strongest numerical stability: "
                f"condition number {condition_number:,.1f}."
            )
        return (
            "Selected for the best combined accuracy and stability rank. "
            f"Forecast error: {loss:.4f}; condition number: {condition_number:,.1f}."
        )

    @output
    @render.text
    def output_window_count() -> str:
        return f"{int(best_estimator_row()['number_of_windows']):,}"

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
        figure, axis = plt.subplots(figsize=(8, 5))
        bars = axis.barh(estimators, values)
        axis.invert_yaxis()
        axis.set_title("Relative Frobenius Loss: Best to Worst")
        axis.set_xlabel("Average relative Frobenius loss")
        axis.set_ylabel("")
        for bar, value in zip(bars, values, strict=True):
            axis.text(value, bar.get_y() + bar.get_height() / 2, f" {value:.3f}", va="center")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_condition_plot():
        _, summary = covariance_results()
        plot_data = summary.sort("average_condition_number")
        estimators = plot_data["estimator"].to_list()
        values = plot_data["average_condition_number"].to_list()
        figure, axis = plt.subplots(figsize=(8, 5))
        bars = axis.barh(estimators, values)
        axis.invert_yaxis()
        axis.set_title("Condition Number: Most to Least Stable")
        axis.set_xlabel("Average condition number")
        axis.set_ylabel("")
        for bar, value in zip(bars, values, strict=True):
            axis.text(value, bar.get_y() + bar.get_height() / 2, f" {value:,.0f}", va="center")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        figure.tight_layout()
        return figure

    @output
    @render.text
    def output_interpretation() -> str:
        """Explain the recommendation in terms of the selected priority."""
        best = best_estimator_row()
        estimator = str(best["estimator"])
        priority = str(input.input_portfolio_priority())
        horizon = str(input.input_investment_horizon())
        frequency = str(input.input_review_frequency()).lower()

        if priority == "Accuracy":
            rationale = "it produced the strongest out-of-sample covariance forecast accuracy"
        elif priority == "Stability":
            rationale = "it produced the most numerically stable covariance estimates"
        else:
            rationale = (
                "it achieved the best combined rank for forecast accuracy and numerical stability"
            )

        return (
            f"{estimator} is recommended because {rationale}. "
            f"The analysis automatically used settings suited to a {horizon.lower()} "
            f"portfolio reviewed {frequency}."
        )

    return {
        "covariance_results": covariance_results,
        "ranked_summary": ranked_summary,
        "best_estimator_row": best_estimator_row,
    }
