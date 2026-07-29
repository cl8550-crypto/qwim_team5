"""Static covariance-estimation charts for the QWIM PDF report.

The module reads the already-exported ``outputs_covariance.json`` file and
creates two SVG charts:

* Average Relative Frobenius Loss by Estimator
* Average Condition Number by Estimator
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import pandas as pd

from plotnine import (
    aes,
    coord_flip,
    element_text,
    geom_col,
    geom_text,
    ggplot,
    labs,
    scale_x_discrete,
    theme,
    theme_minimal,
)

from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    get_logger,
)


_logger = get_logger(name=__name__)

_REPORTING_DIR = Path(__file__).resolve().parent
_OUTPUT_JSON_PATH = (
    _REPORTING_DIR
    / "outputs_json"
    / "outputs_covariance.json"
)
_IMAGES_DIR = _REPORTING_DIR / "outputs_images"

_LOSS_CHART_FILENAME = "chart_covariance_loss.svg"
_CONDITION_CHART_FILENAME = "chart_covariance_condition_number.svg"


# =========================================================================
# DATA HELPERS
# =========================================================================


def _load_covariance_output_QWIM() -> dict[str, Any]:
    """Load the exported covariance-results JSON file."""

    if not _OUTPUT_JSON_PATH.exists():
        raise FileNotFoundError(
            "Covariance output JSON was not found: "
            f"{_OUTPUT_JSON_PATH}"
        )

    with _OUTPUT_JSON_PATH.open(
        mode="r",
        encoding="utf-8",
    ) as json_file:
        data = json.load(json_file)

    if not isinstance(data, dict):
        raise TypeError(
            "outputs_covariance.json must contain a JSON object."
        )

    if not data.get("analysis_success", False):
        raise ValueError(
            "Covariance analysis was not completed successfully."
        )

    return data


def _build_covariance_summary_dataframe_QWIM() -> pd.DataFrame:
    """Build a report-friendly DataFrame from ranked estimator results."""

    output_data = _load_covariance_output_QWIM()
    ranked_estimators = output_data.get(
        "ranked_estimators",
        [],
    )

    if not isinstance(ranked_estimators, list):
        raise TypeError(
            "'ranked_estimators' must be a list."
        )

    if not ranked_estimators:
        raise ValueError(
            "No ranked covariance-estimator results are available."
        )

    dataframe = pd.DataFrame(ranked_estimators)

    required_columns = {
        "rank",
        "estimator",
        "average_relative_frobenius_loss",
        "average_condition_number",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )
    if missing_columns:
        raise ValueError(
            "Covariance output is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    dataframe = dataframe[
        [
            "rank",
            "estimator",
            "average_relative_frobenius_loss",
            "average_condition_number",
        ]
    ].copy()

    dataframe["rank"] = pd.to_numeric(
        dataframe["rank"],
        errors="coerce",
    )
    dataframe["average_relative_frobenius_loss"] = (
        pd.to_numeric(
            dataframe[
                "average_relative_frobenius_loss"
            ],
            errors="coerce",
        )
    )
    dataframe["average_condition_number"] = (
        pd.to_numeric(
            dataframe["average_condition_number"],
            errors="coerce",
        )
    )

    dataframe = dataframe.dropna(
        subset=[
            "estimator",
            "average_relative_frobenius_loss",
            "average_condition_number",
        ]
    )

    if dataframe.empty:
        raise ValueError(
            "Covariance results contain no valid numeric rows."
        )

    dataframe = dataframe.sort_values(
        by="rank",
        ascending=True,
    ).reset_index(drop=True)

    return dataframe


# =========================================================================
# PLOT BUILDERS
# =========================================================================


def build_plotnine_covariance_loss_QWIM():
    """Build the average relative Frobenius-loss chart."""

    dataframe = (
        _build_covariance_summary_dataframe_QWIM()
    )

    # Reverse the category order because coord_flip displays the first
    # category at the bottom.
    estimator_order = list(
        reversed(dataframe["estimator"].tolist())
    )

    dataframe["loss_label"] = dataframe[
        "average_relative_frobenius_loss"
    ].map(lambda value: f"{value:.4f}")

    plot = (
        ggplot(
            dataframe,
            aes(
                x="estimator",
                y="average_relative_frobenius_loss",
            ),
        )
        + geom_col(width=0.68)
        + geom_text(
            aes(label="loss_label"),
            ha="left",
            nudge_y=0.015,
            size=9,
        )
        + coord_flip()
        + scale_x_discrete(limits=estimator_order)
        + labs(
            title=(
                "Covariance Estimator Accuracy"
            ),
            subtitle=(
                "Average relative Frobenius loss "
                "across rolling out-of-sample windows"
            ),
            x="Estimator",
            y="Average Relative Frobenius Loss",
            caption=(
                "Lower values indicate more accurate "
                "out-of-sample covariance estimates."
            ),
        )
        + theme_minimal()
        + theme(
            figure_size=(8.5, 4.8),
            plot_title=element_text(
                weight="bold",
                size=14,
            ),
            plot_subtitle=element_text(size=10),
            axis_title=element_text(size=10),
            axis_text=element_text(size=9),
            plot_caption=element_text(
                size=8,
                ha="left",
            ),
        )
    )

    return plot


def build_plotnine_covariance_condition_number_QWIM():
    """Build the average condition-number chart."""

    dataframe = (
        _build_covariance_summary_dataframe_QWIM()
    )

    dataframe = dataframe.sort_values(
        by="average_condition_number",
        ascending=True,
    ).reset_index(drop=True)

    estimator_order = list(
        reversed(dataframe["estimator"].tolist())
    )

    dataframe["condition_label"] = dataframe[
        "average_condition_number"
    ].map(lambda value: f"{value:,.2f}")

    plot = (
        ggplot(
            dataframe,
            aes(
                x="estimator",
                y="average_condition_number",
            ),
        )
        + geom_col(width=0.68)
        + geom_text(
            aes(label="condition_label"),
            ha="left",
            nudge_y=25,
            size=9,
        )
        + coord_flip()
        + scale_x_discrete(limits=estimator_order)
        + labs(
            title=(
                "Covariance Matrix Numerical Stability"
            ),
            subtitle=(
                "Average condition number by estimator"
            ),
            x="Estimator",
            y="Average Condition Number",
            caption=(
                "Lower condition numbers generally indicate "
                "better numerical stability."
            ),
        )
        + theme_minimal()
        + theme(
            figure_size=(8.5, 4.8),
            plot_title=element_text(
                weight="bold",
                size=14,
            ),
            plot_subtitle=element_text(size=10),
            axis_title=element_text(size=10),
            axis_text=element_text(size=9),
            plot_caption=element_text(
                size=8,
                ha="left",
            ),
        )
    )

    return plot


# =========================================================================
# SVG EXPORTS
# =========================================================================


def export_plot_covariance_loss(
    *,
    reactives_shiny: dict | None,
) -> Path | None:
    """Export the covariance-loss comparison chart to SVG."""

    del reactives_shiny

    output_path = _IMAGES_DIR / _LOSS_CHART_FILENAME

    try:
        _IMAGES_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot = build_plotnine_covariance_loss_QWIM()
        plot.save(
            filename=output_path,
            format="svg",
            width=8.5,
            height=4.8,
            units="in",
            dpi=150,
            verbose=False,
        )

        _logger.info(
            "Exported covariance loss chart to %s",
            output_path,
        )
        return output_path

    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "Could not export covariance loss chart: %s",
            exc,
        )
        return None


def export_plot_covariance_condition_number(
    *,
    reactives_shiny: dict | None,
) -> Path | None:
    """Export the covariance condition-number chart to SVG."""

    del reactives_shiny

    output_path = (
        _IMAGES_DIR
        / _CONDITION_CHART_FILENAME
    )

    try:
        _IMAGES_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot = (
            build_plotnine_covariance_condition_number_QWIM()
        )
        plot.save(
            filename=output_path,
            format="svg",
            width=8.5,
            height=4.8,
            units="in",
            dpi=150,
            verbose=False,
        )

        _logger.info(
            "Exported covariance condition-number chart to %s",
            output_path,
        )
        return output_path

    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "Could not export covariance condition-number chart: %s",
            exc,
        )
        return None


__all__ = [
    "build_plotnine_covariance_loss_QWIM",
    "build_plotnine_covariance_condition_number_QWIM",
    "export_plot_covariance_loss",
    "export_plot_covariance_condition_number",
]