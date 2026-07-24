"""Return/value-over-time plot builders and exporters.

Shared infrastructure (paths, theme, helpers) lives here and is imported by
``_report_plot_allocation`` and ``_report_plot_risk``.

Public API re-exported via ``report_plot_export``:
- ``ensure_all_svg_files_exist``
- ``build_plotnine_portfolio_analysis_returns_distribution``
- ``build_plotnine_portfolio_comparison_portfolio_vs_benchmark``
- ``export_plot_portfolio_analysis``
- ``export_plot_portfolio_comparison``

Shared internals (used by sibling sub-modules):
- ``_QWIM_THEME``, ``_PALETTE``, ``_IMAGES_DIR``, ``_EXPECTED_SVG_FILES``
- ``_ensure_dir``, ``_create_placeholder_svg``
- ``_safe_reactive_get``, ``_safe_float``
- ``_get_inner_variables``, ``_get_visual_objects``
- ``_parse_dates_as_naive``
- ``_load_sample_csv_for_plots``
- ``_save_plot``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd  # pandas-boundary: plotnine requires pandas DataFrame input.
import polars as pl

from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_hline,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_date,
    theme,
    theme_minimal,
)

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPORTING_DIR = Path(__file__).resolve().parent
_IMAGES_DIR = _REPORTING_DIR / "outputs_images"

_PROJECT_ROOT_PLOTS = Path(__file__).resolve().parents[3]
_PROCESSED_DIR_PLOTS = _PROJECT_ROOT_PLOTS / "inputs" / "processed"
_SAMPLE_PORTFOLIO_CSV_PLOTS = _PROCESSED_DIR_PLOTS / "sample_portfolio_values.csv"
_BENCHMARK_PORTFOLIO_CSV_PLOTS = _PROCESSED_DIR_PLOTS / "benchmark_portfolio_values.csv"

# ---------------------------------------------------------------------------
# Theme and palette
# ---------------------------------------------------------------------------

_QWIM_THEME = theme_minimal() + theme(
    plot_title=element_text(size=14, weight="bold"),
    axis_title=element_text(size=11),
    axis_text=element_text(size=9),
    legend_title=element_text(size=10, weight="bold"),
    legend_text=element_text(size=9),
    panel_grid_minor=element_blank(),
    panel_grid_major=element_line(color="#e0e0e0", size=0.4),
    plot_background=element_rect(fill="white", color="white"),
    figure_size=(10, 6),
)

_PALETTE = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # yellow-green
    "#17becf",  # teal
    "#aec7e8",  # light-blue
    "#ffbb78",  # light-orange
]

# ---------------------------------------------------------------------------
# Expected SVG filenames (used by ensure_all_svg_files_exist)
# ---------------------------------------------------------------------------

_EXPECTED_SVG_FILES: dict[str, str] = {
    "portfolio_analysis": "chart_portfolio_analysis_returns_distribution.svg",
    "portfolio_comparison": "chart_portfolio_comparison_portfolio_vs_benchmark.svg",
    "weights_analysis": "chart_weights_analysis_portfolio_weight_distribution_over_time.svg",
    "weights_composition": "chart_weights_analysis_portfolio_current_composition.svg",
    "skfolio_weights": "chart_skfolio_optimization_portfolio_weights_comparison.svg",
    "skfolio_performance": "chart_skfolio_optimization_comparison_portfolio_performance.svg",
    "optimalportfolios_weights": "chart_optimalportfolios_optimization_portfolio_weights_comparison.svg",
    "optimalportfolios_performance": "chart_optimalportfolios_optimization_comparison_portfolio_performance.svg",
    "simulation_fan_chart": "chart_simulation_portfolio_value_fan_chart.svg",
    "simulation_histogram": "chart_simulation_terminal_value_distribution.svg",
    "goal_parity_weights": "chart_goal_parity_weights.svg",
    "goal_parity_goal_powers": "chart_goal_parity_goal_powers.svg",
}

# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------


def _ensure_dir() -> None:
    """Create the images output directory if it does not already exist."""
    _IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _create_placeholder_svg(*, filename: str, title: str = "Chart Unavailable") -> Path:
    """Create a minimal placeholder SVG when chart data is unavailable.

    This prevents Typst ``image()`` calls from crashing on missing files.

    Parameters
    ----------
    filename : str
        SVG filename to create inside ``_IMAGES_DIR``.
    title : str
        Text displayed in the placeholder.

    Returns
    -------
    Path
        Absolute path to the created placeholder SVG.
    """
    _ensure_dir()
    svg_path = _IMAGES_DIR / filename
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" '
        'viewBox="0 0 800 400">\n'
        '  <rect width="800" height="400" fill="#f8fafc" stroke="#cbd5e1" '
        'stroke-width="2" rx="8"/>\n'
        f'  <text x="400" y="190" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="18" fill="#64748b">{title}</text>\n'
        '  <text x="400" y="220" text-anchor="middle" font-family="Arial, sans-serif" '
        'font-size="12" fill="#94a3b8">Insufficient data to render this chart</text>\n'
        "</svg>\n"
    )
    svg_path.write_text(svg_content, encoding="utf-8")
    _logger.info("Created placeholder SVG: %s", filename)
    return svg_path


def ensure_all_svg_files_exist() -> dict[str, str]:
    """Guarantee every SVG expected by the Typst template exists on disk.

    For any file that is missing or empty (0 bytes), a placeholder SVG
    is created.  Returns a mapping of chart key to status:

    * ``"ok"`` — real chart SVG already present
    * ``"placeholder"`` — placeholder was created (data was unavailable)

    This MUST be called after all chart-export functions and before
    Typst compilation.

    Returns
    -------
    dict[str, str]
        ``{chart_key: "ok"|"placeholder"}``.
    """
    _ensure_dir()
    status: dict[str, str] = {}
    for key, filename in _EXPECTED_SVG_FILES.items():
        svg_path = _IMAGES_DIR / filename
        if svg_path.exists() and svg_path.stat().st_size > 0:
            status[key] = "ok"
        else:
            _create_placeholder_svg(
                filename = filename,
                title=key.replace("_", " ").title(),
            )
            status[key] = "placeholder"
            _logger.warning("Created placeholder SVG for missing chart: %s", key)
    return status


# ---------------------------------------------------------------------------
# Reactive and safe-access helpers
# ---------------------------------------------------------------------------


def _safe_reactive_get(*, reactive_value: Any) -> Any:
    """Safely retrieve the current value from a reactive; return None on error or if absent."""
    if reactive_value is None:
        return None
    if hasattr(reactive_value, "get"):
        try:
            return reactive_value.get()
        except Exception as exc:  # noqa: BLE001 - reactive boundary treats getter failures as missing values.
            _logger.debug("Reactive get failed: %s", exc)
            return None
    return reactive_value


def _safe_float(*, value: Any, default: float = 0.0) -> float:
    """Convert *value* to float, returning *default* on error or None."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _build_returns_distribution_frame(
    *, values_df: pl.DataFrame, series_name: str) -> pd.DataFrame | None:
    """Build a plot-ready returns frame, or ``None`` for invalid value data.

    Parameters
    ----------
    values_df : polars.DataFrame
        Value time-series with at least two rows.
    series_name : str
        Label assigned to the plotted series.

    Returns
    -------
    pandas.DataFrame | None
        DataFrame with ``return`` and ``series`` columns, or ``None`` when
        the input value column is missing, boolean, or otherwise unusable.
    """
    if not isinstance(values_df, pl.DataFrame) or values_df.height < 2:
        return None

    value_column_name = (
        "portfolio_value" if "portfolio_value" in values_df.columns else values_df.columns[-1]
    )
    if values_df.schema.get(value_column_name) == pl.Boolean:
        return None

    returns_df = (
        values_df.with_columns(
            pl.col(value_column_name).cast(pl.Float64, strict=False).alias(value_column_name),
        )
        .with_columns(
            (pl.col(value_column_name) / pl.col(value_column_name).shift(1) - 1.0).alias("return"),
        )
        .drop_nulls("return")
    )
    if returns_df.height == 0:
        return None

    return (
        returns_df.select(["return"])
        .with_columns(pl.lit(series_name).alias("series"))
        .to_pandas()
    )


def _get_inner_variables(*, reactives_shiny: dict | None) -> dict[str, Any]:
    """Extract the Inner_Variables_Shiny dict from *reactives_shiny*, or return empty."""
    if not reactives_shiny or not isinstance(reactives_shiny, dict):
        return {}
    raw = reactives_shiny.get("Inner_Variables_Shiny", {})
    return raw if isinstance(raw, dict) else {}


def _get_visual_objects(*, reactives_shiny: dict | None) -> dict[str, Any]:
    """Extract the Visual_Objects_Shiny dict from *reactives_shiny*, or return empty."""
    if not reactives_shiny or not isinstance(reactives_shiny, dict):
        return {}
    raw = reactives_shiny.get("Visual_Objects_Shiny", {})
    return raw if isinstance(raw, dict) else {}


# ---------------------------------------------------------------------------
# Date parsing helper
# ---------------------------------------------------------------------------


def _parse_dates_as_naive(*, date_col: Any) -> Any:
    """Parse a date column tolerating mixed time zones; return timezone-naive.

    Wraps ``pd.to_datetime(..., utc=True).dt.tz_convert(None)`` to silence
    the ``FutureWarning`` raised when a Series contains heterogeneous UTC
    offsets, and then strips the timezone information so the result is a
    plain ``datetime64[ns]`` Series that is compatible with plotnine's
    ``scale_x_date``, which requires naive ``datetime64`` values.

    Parameters
    ----------
    date_col : array-like
        Date values — strings, Python ``datetime.date`` objects, or pandas
        ``Timestamp`` objects, with or without timezone information.

    Returns
    -------
    pandas.Series
        Timezone-naive ``datetime64[ns]`` Series.
    """
    return pd.to_datetime(date_col, utc=True).dt.tz_convert(None)


# ---------------------------------------------------------------------------
# Sample-data helpers
# ---------------------------------------------------------------------------


def _load_sample_csv_for_plots() -> tuple[pl.DataFrame | None, pl.DataFrame | None]:
    """Load sample portfolio and benchmark CSVs for plot fallback."""

    def _load(*, path: Path) -> pl.DataFrame | None:
        """Read a CSV at *path* and return a cleaned DataFrame, or None on failure."""
        try:
            df = pl.read_csv(path)
            df = df.with_columns(
                pl.col("Date").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("Date"),
            )
            df = df.rename({"Value": "portfolio_value"})
            return df.sort("Date")
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - sample-data fallback must tolerate heterogeneous file failures.
            _logger.debug("Could not load sample CSV %s: %s", path, exc)
            return None

    return _load(path = _SAMPLE_PORTFOLIO_CSV_PLOTS), _load(path = _BENCHMARK_PORTFOLIO_CSV_PLOTS)


# ---------------------------------------------------------------------------
# Plot save helper
# ---------------------------------------------------------------------------


def _save_plot(*, plot: ggplot, filename: str, width: float = 10, height: float = 6) -> Path:
    """Save a plotnine ggplot as SVG and return the path.

    Notes
    -----
    Boolean width and height values are rejected instead of being coerced
    into numeric plot dimensions.
    """
    if isinstance(width, bool):
        raise Exception_Validation_Input("width must be a real number, not a boolean")
    if isinstance(height, bool):
        raise Exception_Validation_Input("height must be a real number, not a boolean")

    _ensure_dir()
    out_path = _IMAGES_DIR / filename
    plot.save(
        str(out_path),
        width=width,
        height=height,
        dpi=150,
        verbose=False,
    )
    _logger.info("Saved SVG: %s (%d bytes)", filename, out_path.stat().st_size)
    return out_path


# =========================================================================
# PLOTNINE BUILDER FUNCTIONS — Returns / value-over-time
# =========================================================================


def build_plotnine_portfolio_analysis_returns_distribution(
    *, portfolio_df: Any, benchmark_df: Any = None) -> Any:
    """Build a returns-distribution histogram as a plotnine ggplot.

    Parameters
    ----------
    portfolio_df : polars.DataFrame | pandas.DataFrame | None
        Portfolio value time-series with a numeric value column.
    benchmark_df : polars.DataFrame | pandas.DataFrame | None
        Optional benchmark value time-series.

    Returns
    -------
    plotnine.ggplot | None
        ggplot object, or ``None`` when data is insufficient.

    Notes
    -----
    Boolean value columns are treated as invalid input and are not coerced
    into numeric returns.
    """
    try:
        if portfolio_df is None:
            return None
        pv = (
            pl.from_pandas(portfolio_df)
            if not isinstance(portfolio_df, pl.DataFrame)
            else portfolio_df
        )
        pdf = _build_returns_distribution_frame(values_df = pv, series_name = "Portfolio")
        if pdf is None:
            return None

        if benchmark_df is not None:
            bv = (
                pl.from_pandas(benchmark_df)
                if not isinstance(benchmark_df, pl.DataFrame)
                else benchmark_df
            )
            bpdf = _build_returns_distribution_frame(values_df = bv, series_name = "Benchmark")
            if bpdf is not None:
                pdf = pd.concat([pdf, bpdf], ignore_index=True)

        return (
            ggplot(pdf, aes(x="return", fill="series"))
            + geom_histogram(alpha=0.6, bins=50, position="identity")
            + scale_fill_manual(values=["#1f77b4", "#ff7f0e"])
            + labs(title="Returns Distribution", x="Daily Return", y="Frequency", fill="Series")
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_portfolio_analysis_returns_distribution: %s", exc)
        return None


def build_plotnine_portfolio_comparison_portfolio_vs_benchmark(
    *, portfolio_df: Any, benchmark_df: Any = None) -> Any:
    """Build a normalised portfolio-vs-benchmark line chart as a plotnine ggplot.

    Parameters
    ----------
    portfolio_df : polars.DataFrame | pandas.DataFrame | None
        Portfolio value time-series with ``Date`` and a value column.
    benchmark_df : polars.DataFrame | pandas.DataFrame | None
        Optional benchmark value time-series.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        if portfolio_df is None:
            return None
        pv = (
            pl.from_pandas(portfolio_df)
            if not isinstance(portfolio_df, pl.DataFrame)
            else portfolio_df
        )
        if pv.height < 2:
            return None
        pv_col = "portfolio_value" if "portfolio_value" in pv.columns else pv.columns[-1]
        start_val = _safe_float(value = pv[pv_col][0], default = 1.0) or 1.0
        pv = pv.with_columns((pl.col(pv_col) / start_val * 100).alias("normalised"))
        pdf_p = (
            pv.select(["Date", "normalised"])
            .with_columns(pl.lit("Portfolio").alias("series"))
            .to_pandas()
        )
        pdf_p["Date"] = _parse_dates_as_naive(date_col = pdf_p["Date"])
        frames = [pdf_p]

        if benchmark_df is not None:
            bv = (
                pl.from_pandas(benchmark_df)
                if not isinstance(benchmark_df, pl.DataFrame)
                else benchmark_df
            )
            if bv.height >= 2:
                bv_col = "portfolio_value" if "portfolio_value" in bv.columns else bv.columns[-1]
                bv_start = _safe_float(value = bv[bv_col][0], default = 1.0) or 1.0
                bv = bv.with_columns((pl.col(bv_col) / bv_start * 100).alias("normalised"))
                pdf_b = (
                    bv.select(["Date", "normalised"])
                    .with_columns(pl.lit("Benchmark").alias("series"))
                    .to_pandas()
                )
                pdf_b["Date"] = _parse_dates_as_naive(date_col = pdf_b["Date"])
                frames.append(pdf_b)

        combined = pd.concat(frames, ignore_index=True)
        return (
            ggplot(combined, aes(x="Date", y="normalised", color="series"))
            + geom_line(size=1)
            + scale_color_manual(values=["#ff7f0e", "#1f77b4"])
            + geom_hline(yintercept=100, linetype="dashed", color="#888888", size=0.5)
            + scale_x_date(date_labels="%Y-%m")
            + labs(
                title="Portfolio vs Benchmark (Normalised, Base = 100)",
                x="Date",
                y="Normalised Value",
                color="Series",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - report boundary tolerates heterogeneous plotting failures.
        _logger.warning("build_plotnine_portfolio_comparison_portfolio_vs_benchmark: %s", exc)
        return None


# =========================================================================
# EXPORT FUNCTIONS — Returns / value-over-time
# =========================================================================


def export_plot_portfolio_analysis(
    *, reactives_shiny: dict | None) -> Path | None:
    """Render the Portfolio Analysis main chart as SVG.

    Attempts to reconstruct a *returns distribution* histogram from stored
    data.  Falls back to a placeholder chart when data is unavailable.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.

    Notes
    -----
    Boolean value columns are treated as invalid portfolio-analysis input.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    portfolio_values = _safe_reactive_get(reactive_value = inner.get("Portfolio_Values"))
    benchmark_values = _safe_reactive_get(reactive_value = inner.get("Benchmark_Values"))

    if not isinstance(portfolio_values, pl.DataFrame) or portfolio_values.height < 2:
        _logger.info("Loading sample CSV for portfolio analysis plot")
        portfolio_values, benchmark_values = _load_sample_csv_for_plots()

    if not isinstance(portfolio_values, pl.DataFrame) or portfolio_values.height < 2:
        _logger.warning("Not enough portfolio data for analysis plot")
        return None

    pv = portfolio_values.sort("Date")
    pdf = _build_returns_distribution_frame(values_df = pv, series_name = "Portfolio")
    if pdf is None:
        _logger.warning("Portfolio analysis plot has invalid portfolio value data")
        return None

    if isinstance(benchmark_values, pl.DataFrame) and benchmark_values.height >= 2:
        bv = benchmark_values.sort("Date")
        bpdf = _build_returns_distribution_frame(values_df = bv, series_name = "Benchmark")
        if bpdf is not None:
            pdf = pd.concat([pdf, bpdf], ignore_index=True)

    p = (
        ggplot(pdf, aes(x="return", fill="series"))
        + geom_histogram(alpha=0.6, bins=50, position="identity")
        + scale_fill_manual(values=["#1f77b4", "#ff7f0e"])
        + labs(
            title="Returns Distribution",
            x="Daily Return",
            y="Frequency",
            fill="Series",
        )
        + _QWIM_THEME
    )

    return _save_plot(plot = p, filename = "chart_portfolio_analysis_returns_distribution.svg")


def export_plot_portfolio_comparison(
    *, reactives_shiny: dict | None) -> Path | None:
    """Render Portfolio vs Benchmark normalised value chart as SVG.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    Path | None
        Path to SVG file, or ``None`` if data is insufficient.

    Notes
    -----
    Boolean starting values use the existing ``1.0`` normalization fallback
    instead of raw numeric coercion.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    portfolio_values = _safe_reactive_get(reactive_value = inner.get("Portfolio_Values"))
    benchmark_values = _safe_reactive_get(reactive_value = inner.get("Benchmark_Values"))

    if not isinstance(portfolio_values, pl.DataFrame) or portfolio_values.height < 2:
        _logger.info("Loading sample CSV for portfolio comparison plot")
        portfolio_values, benchmark_values = _load_sample_csv_for_plots()

    if not isinstance(portfolio_values, pl.DataFrame) or portfolio_values.height < 2:
        _logger.warning("Not enough data for comparison plot")
        return None

    pv = portfolio_values.sort("Date")
    pv_col = "portfolio_value" if "portfolio_value" in pv.columns else pv.columns[1]

    start_val = _safe_float(value = pv[pv_col][0], default = 1.0) or 1.0
    pv = pv.with_columns(
        (pl.col(pv_col) / start_val * 100).alias("normalised"),
    )
    pdf_p = (
        pv.select(["Date", "normalised"])
        .with_columns(
            pl.lit("Portfolio").alias("series"),
        )
        .to_pandas()
    )
    pdf_p["Date"] = _parse_dates_as_naive(date_col = pdf_p["Date"])

    frames = [pdf_p]

    if isinstance(benchmark_values, pl.DataFrame) and benchmark_values.height >= 2:
        bv = benchmark_values.sort("Date")
        bv_col = "portfolio_value" if "portfolio_value" in bv.columns else bv.columns[1]
        bv_start = _safe_float(value = bv[bv_col][0], default = 1.0) or 1.0
        bv = bv.with_columns(
            (pl.col(bv_col) / bv_start * 100).alias("normalised"),
        )
        pdf_b = (
            bv.select(["Date", "normalised"])
            .with_columns(
                pl.lit("Benchmark").alias("series"),
            )
            .to_pandas()
        )
        pdf_b["Date"] = _parse_dates_as_naive(date_col = pdf_b["Date"])
        frames.append(pdf_b)

    combined = pd.concat(frames, ignore_index=True)

    p = (
        ggplot(combined, aes(x="Date", y="normalised", color="series"))
        + geom_line(size=1)
        + scale_color_manual(values=["#ff7f0e", "#1f77b4"])
        + geom_hline(yintercept=100, linetype="dashed", color="#888888", size=0.5)
        + labs(
            title="Portfolio vs Benchmark (Normalised, Base = 100)",
            x="Date",
            y="Value (Base = 100)",
            color="Series",
        )
        + scale_x_date(date_labels="%Y-%m")
        + _QWIM_THEME
    )

    return _save_plot(plot = p, filename = "chart_portfolio_comparison_portfolio_vs_benchmark.svg")
