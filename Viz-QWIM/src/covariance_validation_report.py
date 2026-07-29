"""
Covariance Validation Report

Runs the rolling covariance backtest on the ETF dataset and exports
validation tables and figures for comparison of covariance estimators.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

from src.num_methods.covariance.covariance_backtest import (
    Covariance_Backtest_Config,
    run_covariance_backtest,
    summarize_covariance_backtest,
)
from src.num_methods.covariance.covariance_data import load_etf_returns
from src.num_methods.covariance.utils_cov_corr import Covariance_Estimator


OUTPUT_DIR = Path("outputs/covariance_validation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ESTIMATOR_ORDER = [
    "Empirical",
    "Ledoit-Wolf",
    "Oracle Approximating Shrinkage",
    "Exponentially Weighted",
]


def save_bar_chart(
    data: pl.DataFrame,
    value_column: str,
    title: str,
    y_label: str,
    file_name: str,
) -> None:
    """Save a bar chart from the estimator summary."""

    plot_data = (
        data.with_columns(
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

    estimator_names = plot_data["estimator"].to_list()
    values = plot_data[value_column].to_list()

    plt.figure(figsize=(10, 6))
    plt.bar(estimator_names, values)

    plt.title(title)
    plt.xlabel("Covariance estimator")
    plt.ylabel(y_label)
    plt.xticks(rotation=20, ha="right")

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / file_name,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def save_rolling_loss_chart(results: pl.DataFrame) -> None:
    """Save rolling relative Frobenius loss for each estimator."""

    plt.figure(figsize=(12, 7))

    for estimator in ESTIMATOR_ORDER:
        estimator_results = (
            results
            .filter(pl.col("estimator") == estimator)
            .sort("test_start")
        )

        if estimator_results.is_empty():
            continue

        plt.plot(
            estimator_results["test_start"].to_list(),
            estimator_results["relative_frobenius_loss"].to_list(),
            linewidth=2,
            alpha=0.9,
            label=estimator,
        )

    plt.title("Rolling Relative Frobenius Loss")
    plt.xlabel("Test-window start date")
    plt.ylabel("Relative Frobenius loss")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "rolling_relative_frobenius_loss.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def save_loss_boxplot(results: pl.DataFrame) -> None:
    """Save the distribution of relative Frobenius loss."""

    estimators = [
        estimator
        for estimator in ESTIMATOR_ORDER
        if not results.filter(
            pl.col("estimator") == estimator
        ).is_empty()
    ]

    loss_values = [
        results
        .filter(pl.col("estimator") == estimator)[
            "relative_frobenius_loss"
        ]
        .to_list()
        for estimator in estimators
    ]

    plt.figure(figsize=(10, 6))
    plt.boxplot(
        loss_values,
        tick_labels=estimators,
        showmeans=True,
    )

    plt.title("Distribution of Relative Frobenius Loss")
    plt.xlabel("Covariance estimator")
    plt.ylabel("Relative Frobenius loss")
    plt.xticks(rotation=20, ha="right")

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "relative_frobenius_loss_boxplot.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def main() -> None:
    """Run the covariance backtest and export validation outputs."""

    print("=" * 60)
    print("Covariance Validation Report")
    print("=" * 60)

    returns = load_etf_returns(
        file_path="inputs/raw/data_ETFs.csv"
    )

    print(f"\nLoaded returns dataset: {returns.shape}")

    results = run_covariance_backtest(
        returns_data=returns,
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

    print("\nBacktest complete.")
    print(summary)

    results.write_csv(
        OUTPUT_DIR / "rolling_results.csv"
    )

    summary.write_csv(
        OUTPUT_DIR / "estimator_summary.csv"
    )

    save_bar_chart(
        data=summary,
        value_column="average_relative_frobenius_loss",
        title="Average Relative Frobenius Loss by Estimator",
        y_label="Average relative Frobenius loss",
        file_name="average_relative_frobenius_loss.png",
    )

    save_bar_chart(
        data=summary,
        value_column="average_condition_number",
        title="Average Condition Number by Estimator",
        y_label="Average condition number",
        file_name="average_condition_number.png",
    )

    save_rolling_loss_chart(results)
    save_loss_boxplot(results)

    print("\nCSV files exported successfully.")
    print("Charts exported successfully.")
    print(f"\nLocation: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()