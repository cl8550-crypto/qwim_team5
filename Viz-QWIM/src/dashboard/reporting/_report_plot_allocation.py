"""Allocation and weight-distribution plot builders and exporters.

Covers portfolio weight-over-time, current composition, and optimization
method comparisons (skfolio and optimalportfolios).

Public API re-exported via ``report_plot_export``:
- ``build_plotnine_weights_analysis_distribution_over_time``
- ``build_plotnine_weights_analysis_current_composition``
- ``build_plotnine_skfolio_weights_comparison``
- ``build_plotnine_skfolio_performance_comparison``
- ``build_plotnine_optimalportfolios_weights_comparison``
- ``build_plotnine_optimalportfolios_performance_comparison``
- ``export_plot_weights_analysis``
- ``export_plot_weights_pie``
- ``export_plot_skfolio_weights``
- ``export_plot_skfolio_performance``
"""

from __future__ import annotations

from typing import Any

import pandas as pd  # pandas-boundary: plotnine requires pandas DataFrame input.
import polars as pl

from plotnine import (
    aes,
    element_text,
    geom_area,
    geom_col,
    geom_hline,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_date,
    theme,
)

from ._report_plot_returns import (
    _PALETTE,
    _QWIM_THEME,
    _get_inner_variables,
    _parse_dates_as_naive,
    _safe_reactive_get,
    _save_plot,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# =========================================================================
# PLOTNINE BUILDER FUNCTIONS — Allocation / weights
# =========================================================================


def build_plotnine_weights_analysis_distribution_over_time(
    *, weights_df: Any) -> Any:
    """Build a stacked-area weight-distribution-over-time chart as a plotnine ggplot.

    Parameters
    ----------
    weights_df : pandas.DataFrame | None
        DataFrame with ``Date`` column and one column per asset/component.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if weights_df is None:
            return None
        df = weights_df if isinstance(weights_df, pd.DataFrame) else pd.DataFrame(weights_df)
        if df.empty or "Date" not in df.columns:
            return None
        component_cols = [c for c in df.columns if c != "Date"]
        if not component_cols:
            return None

        melted = df.melt(
            id_vars=["Date"],
            value_vars=component_cols,
            var_name="asset",
            value_name="weight",
        )
        melted["Date"] = _parse_dates_as_naive(date_col = melted["Date"])

        return (
            ggplot(melted, aes(x="Date", y="weight", fill="asset"))
            + geom_area(position="stack", alpha=0.8)
            + scale_x_date(date_labels="%Y-%m")
            + labs(
                title="Portfolio Weight Distribution Over Time",
                x="Date",
                y="Weight",
                fill="Asset",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_weights_analysis_distribution_over_time: %s", exc)
        return None


def build_plotnine_weights_analysis_current_composition(
    *, labels: list[str], values: list[float]) -> Any:
    """Build a bar chart of current portfolio composition as a plotnine ggplot.

    Parameters
    ----------
    labels : list[str]
        Asset names.
    values : list[float]
        Corresponding weights.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if not labels or not values or len(labels) != len(values):
            return None
        df = pd.DataFrame({"asset": labels, "weight": values})
        df = df.sort_values("weight", ascending=False).reset_index(drop=True)
        return (
            ggplot(df, aes(x="asset", y="weight", fill="asset"))
            + geom_col(show_legend=False)
            + labs(title="Current Portfolio Composition", x="Asset", y="Weight")
            + _QWIM_THEME
            + theme(axis_text_x=element_text(angle=45, hjust=1))
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_weights_analysis_current_composition: %s", exc)
        return None


def build_plotnine_skfolio_weights_comparison(
    *, assets: list[str], weights1: list[float], weights2: list[float], name1: str = "Method 1", name2: str = "Method 2") -> Any:
    """Build a grouped bar chart comparing two sets of portfolio weights.

    Parameters
    ----------
    assets : list[str]
    weights1 : list[float]
    weights2 : list[float]
    name1, name2 : str
        Labels for the two methods.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if not assets or not weights1 or not weights2:
            return None
        rows = [
            {"asset": a, "weight": w, "method": name1}
            for a, w in zip(assets, weights1, strict=False)
        ] + [
            {"asset": a, "weight": w, "method": name2}
            for a, w in zip(assets, weights2, strict=False)
        ]
        df = pd.DataFrame(rows)
        return (
            ggplot(df, aes(x="asset", y="weight", fill="method"))
            + geom_col(position="dodge", alpha=0.85)
            + scale_fill_manual(values=["#37536d", "#1a76ff"])
            + labs(title="Portfolio Weights Comparison", x="Asset", y="Weight (%)", fill="Method")
            + _QWIM_THEME
            + theme(axis_text_x=element_text(angle=45, hjust=1))
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_skfolio_weights_comparison: %s", exc)
        return None


def build_plotnine_skfolio_performance_comparison(
    *, perf1_df: Any, perf2_df: Any, name1: str = "Method 1", name2: str = "Method 2") -> Any:
    """Build a normalised performance comparison line chart as a plotnine ggplot.

    Parameters
    ----------
    perf1_df, perf2_df : polars.DataFrame | None
        DataFrames with ``Date`` and ``Value`` columns.
    name1, name2 : str
        Display labels.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        frames = []
        for df_raw, label in [(perf1_df, name1), (perf2_df, name2)]:
            if df_raw is None:
                continue
            df = pl.from_pandas(df_raw) if not isinstance(df_raw, pl.DataFrame) else df_raw
            if df.height < 2:
                continue
            pdf = (
                df.select(["Date", "Value"]).with_columns(pl.lit(label).alias("method")).to_pandas()
            )
            pdf["Date"] = _parse_dates_as_naive(date_col = pdf["Date"])
            frames.append(pdf)

        if not frames:
            return None

        combined = pd.concat(frames, ignore_index=True)
        return (
            ggplot(combined, aes(x="Date", y="Value", color="method"))
            + geom_line(size=1)
            + scale_color_manual(values=["#37536d", "#1a76ff"])
            + scale_x_date(date_labels="%Y-%m")
            + labs(
                title="Portfolio Performance Comparison (Normalised, Base = 100)",
                x="Date",
                y="Portfolio Value",
                color="Method",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_skfolio_performance_comparison: %s", exc)
        return None


def build_plotnine_optimalportfolios_weights_comparison(
    *, assets: list[str], weights1: list[float], weights2: list[float], name1: str = "Method 1", name2: str = "Method 2") -> Any:
    """Build a grouped bar chart comparing two OptimalPortfolios portfolio weights.

    Parameters
    ----------
    assets : list[str]
    weights1 : list[float]
    weights2 : list[float]
    name1, name2 : str
        Labels for the two methods.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if not assets or not weights1 or not weights2:
            return None
        rows = [
            {"asset": a, "weight": w, "method": name1}
            for a, w in zip(assets, weights1, strict=False)
        ] + [
            {"asset": a, "weight": w, "method": name2}
            for a, w in zip(assets, weights2, strict=False)
        ]
        df = pd.DataFrame(rows)
        return (
            ggplot(df, aes(x="asset", y="weight", fill="method"))
            + geom_col(position="dodge", alpha=0.85)
            + scale_fill_manual(values=["#37536d", "#1a76ff"])
            + labs(title="Portfolio Weights Comparison", x="Asset", y="Weight (%)", fill="Method")
            + _QWIM_THEME
            + theme(axis_text_x=element_text(angle=45, hjust=1))
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_optimalportfolios_weights_comparison: %s", exc)
        return None


def build_plotnine_optimalportfolios_performance_comparison(
    *, perf1_df: Any, perf2_df: Any, name1: str = "Method 1", name2: str = "Method 2") -> Any:
    """Build a normalised performance comparison line chart for OptimalPortfolios methods.

    Parameters
    ----------
    perf1_df, perf2_df : polars.DataFrame | None
        DataFrames with ``Date`` and ``Value`` columns.
    name1, name2 : str
        Display labels.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        frames = []
        for df_raw, label in [(perf1_df, name1), (perf2_df, name2)]:
            if df_raw is None:
                continue
            df = pl.from_pandas(df_raw) if not isinstance(df_raw, pl.DataFrame) else df_raw
            if df.height < 2:
                continue
            pdf = (
                df.select(["Date", "Value"]).with_columns(pl.lit(label).alias("method")).to_pandas()
            )
            pdf["Date"] = _parse_dates_as_naive(date_col = pdf["Date"])
            frames.append(pdf)

        if not frames:
            return None

        combined = pd.concat(frames, ignore_index=True)
        return (
            ggplot(combined, aes(x="Date", y="Value", color="method"))
            + geom_line(size=1)
            + scale_color_manual(values=["#37536d", "#1a76ff"])
            + scale_x_date(date_labels="%Y-%m")
            + labs(
                title="Portfolio Performance Comparison (Normalised, Base = 100)",
                x="Date",
                y="Portfolio Value",
                color="Method",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_optimalportfolios_performance_comparison: %s", exc)
        return None


# =========================================================================
# EXPORT FUNCTIONS — Allocation / weights
# =========================================================================


def export_plot_weights_analysis(
    *, reactives_shiny: dict | None) -> Any:
    """Render the Weights Analysis stacked-area chart as SVG.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    weights_df = _safe_reactive_get(reactive_value = inner.get("Weights_Data"))
    if not isinstance(weights_df, pl.DataFrame) or weights_df.height == 0:
        _logger.warning("No weights data for distribution plot")
        return None

    value_cols = [
        c
        for c in weights_df.columns
        if c != "Date" and weights_df.schema.get(c) != pl.Boolean
    ]
    if not value_cols:
        return None

    long = weights_df.unpivot(
        index="Date",
        on=value_cols,
        variable_name="component",
        value_name="weight",
    ).to_pandas()
    long["Date"] = _parse_dates_as_naive(date_col = long["Date"])

    num_components = len(value_cols)
    colors = (_PALETTE * ((num_components // len(_PALETTE)) + 1))[:num_components]

    p = (
        ggplot(long, aes(x="Date", y="weight", fill="component"))
        + geom_area(alpha=0.85, position="stack")
        + scale_fill_manual(values=colors)
        + labs(
            title="Portfolio Weights Analysis Over Time",
            x="Date",
            y="Weight",
            fill="Component",
        )
        + scale_x_date(date_labels="%Y-%m")
        + _QWIM_THEME
    )

    return _save_plot(plot = p, filename = "chart_weights_analysis_portfolio_weight_distribution_over_time.svg")


def export_plot_weights_pie(
    *, reactives_shiny: dict | None) -> Any:
    """Render current portfolio composition as a bar chart (plotnine lacks native pie).

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    weights_df = _safe_reactive_get(reactive_value = inner.get("Weights_Data"))
    if not isinstance(weights_df, pl.DataFrame) or weights_df.height == 0:
        return None

    value_cols = [
        c
        for c in weights_df.columns
        if c != "Date" and weights_df.schema.get(c) != pl.Boolean
    ]
    if not value_cols:
        return None

    last_row = weights_df.sort("Date").tail(1)
    data_dict: dict[str, list[Any]] = {"component": [], "weight": []}
    for col in value_cols:
        data_dict["component"].append(col)
        data_dict["weight"].append(float(last_row[col][0]))

    pdf = pd.DataFrame(data_dict)

    num_components = len(value_cols)
    colors = (_PALETTE * ((num_components // len(_PALETTE)) + 1))[:num_components]

    p = (
        ggplot(pdf, aes(x="component", y="weight", fill="component"))
        + geom_col(alpha=0.85)
        + scale_fill_manual(values=colors)
        + labs(
            title="Current Portfolio Composition",
            x="Component",
            y="Weight",
            fill="Component",
        )
        + _QWIM_THEME
        + theme(figure_size=(10, 5))
    )

    return _save_plot(
        plot = p,
        filename = "chart_weights_analysis_portfolio_current_composition.svg",
        width=10,
        height=5,
    )


def export_plot_skfolio_weights(
    *, reactives_shiny: dict | None) -> Any:
    """Render skfolio optimised weights comparison as grouped bar chart.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    results_raw = _safe_reactive_get(reactive_value = inner.get("Skfolio_Results_Table"))
    if results_raw is None:
        return None

    if isinstance(results_raw, pl.DataFrame):
        pdf = results_raw.to_pandas()
    elif isinstance(results_raw, pd.DataFrame):
        pdf = results_raw
    elif isinstance(results_raw, list):
        pdf = pd.DataFrame(results_raw)
    else:
        return None

    if pdf.empty:
        return None

    asset_col = pdf.columns[0]
    if len(pdf.columns) < 3:
        return None

    p1_col = pdf.columns[1]
    p2_col = pdf.columns[2]

    melted = pdf.melt(
        id_vars=[asset_col],
        value_vars=[p1_col, p2_col],
        var_name="portfolio",
        value_name="weight",
    )
    melted = melted.rename(columns={asset_col: "asset"})

    p = (
        ggplot(melted, aes(x="asset", y="weight", fill="portfolio"))
        + geom_col(position="dodge", alpha=0.85)
        + scale_fill_manual(values=["#1f77b4", "#ff7f0e"])
        + labs(
            title="Optimised Portfolio Weights Comparison",
            x="Asset",
            y="Weight (%)",
            fill="Portfolio",
        )
        + _QWIM_THEME
        + theme(axis_text_x=element_text(angle=45, ha="right"))
    )

    return _save_plot(plot = p, filename = "chart_skfolio_optimization_portfolio_weights_comparison.svg")


def export_plot_skfolio_performance(
    *, reactives_shiny: dict | None) -> Any:
    """Render skfolio normalised performance comparison as line chart.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    perf_data = _safe_reactive_get(reactive_value = inner.get("Skfolio_Performance_Data"))
    if not isinstance(perf_data, pl.DataFrame) or perf_data.height < 2:
        return None

    pdf = perf_data.to_pandas()
    pdf["Date"] = _parse_dates_as_naive(date_col = pdf["Date"])

    value_cols = [c for c in pdf.columns if c != "Date"]
    if not value_cols:
        return None

    melted = pdf.melt(
        id_vars=["Date"],
        value_vars=value_cols,
        var_name="portfolio",
        value_name="value",
    )

    colors = ["#1f77b4", "#ff7f0e"][: len(value_cols)]

    p = (
        ggplot(melted, aes(x="Date", y="value", color="portfolio"))
        + geom_line(size=1)
        + scale_color_manual(values=colors)
        + geom_hline(yintercept=100, linetype="dashed", color="#888888", size=0.5)
        + labs(
            title="Optimised Portfolio Performance (Normalised, Base = 100)",
            x="Date",
            y="Value (Base = 100)",
            color="Portfolio",
        )
        + scale_x_date(date_labels="%Y-%m")
        + _QWIM_THEME
    )

    return _save_plot(plot = p, filename = "chart_skfolio_optimization_comparison_portfolio_performance.svg")
