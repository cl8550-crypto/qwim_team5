"""Risk and simulation plot builders and exporters.

Covers Monte Carlo fan charts and terminal-value distribution histograms.

Public API re-exported via ``report_plot_export``:
- ``build_plotnine_simulation_fan_chart``
- ``build_plotnine_simulation_terminal_value_distribution``
- ``export_plot_simulation_fan_chart``
- ``export_plot_simulation_histogram``
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from plotnine import (
    aes,
    geom_histogram,
    geom_hline,
    geom_line,
    geom_ribbon,
    geom_vline,
    ggplot,
    labs,
    scale_x_date,
    theme,
)

from ._report_plot_returns import (
    _QWIM_THEME,
    _get_inner_variables,
    _load_sample_csv_for_plots,
    _parse_dates_as_naive,
    _safe_float,
    _save_plot,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Internal simulation helper
# ---------------------------------------------------------------------------


def _build_simulation_fan_data(
    *, pv: pl.DataFrame, num_scenarios: int = 1000, num_days: int = 252, initial_value: float = 100.0, seed: int = 42) -> pl.DataFrame:
    """Simulate portfolio paths and return per-day percentile bands.

    Parameters
    ----------
    pv : pl.DataFrame
        Portfolio value history used to estimate return mean and std.
    num_scenarios : int
        Number of Monte Carlo paths to simulate.
    num_days : int
        Number of trading days to project.
    initial_value : float
        Starting portfolio value for simulated paths.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pl.DataFrame
        Columns: ``day``, ``p5``, ``p25``, ``median``, ``mean``, ``p75``, ``p95``.
        Returns an empty frame when the input portfolio values are invalid.

    Notes
    -----
    Boolean simulation control parameters are treated as invalid input and
    keep the helper on its existing empty-data fallback path.
    """
    if any(
        isinstance(value_current, (bool, np.bool_))
        for value_current in (num_scenarios, num_days, initial_value, seed)
    ):
        return pl.DataFrame()

    portfolio_value_series = pv.get_column("portfolio_value").drop_nulls()
    if portfolio_value_series.len() < 2 or portfolio_value_series.dtype == pl.Boolean:
        return pl.DataFrame()

    pv_arr = portfolio_value_series.cast(pl.Float64, strict=False).drop_nulls().to_numpy()
    if pv_arr.size < 2:
        return pl.DataFrame()

    rets = np.diff(pv_arr) / pv_arr[:-1]
    mu = float(np.mean(rets))
    sigma = float(np.std(rets, ddof=1))

    rng = np.random.default_rng(seed)
    sim_rets = rng.normal(mu, sigma, size=(num_scenarios, num_days))
    cum_rets = np.cumprod(1.0 + sim_rets, axis=1) * initial_value

    days = np.arange(1, num_days + 1)
    data = {
        "day": days,
        "p5": np.percentile(cum_rets, 5, axis=0),
        "p25": np.percentile(cum_rets, 25, axis=0),
        "median": np.percentile(cum_rets, 50, axis=0),
        "mean": np.mean(cum_rets, axis=0),
        "p75": np.percentile(cum_rets, 75, axis=0),
        "p95": np.percentile(cum_rets, 95, axis=0),
    }
    return pl.DataFrame(data)


# =========================================================================
# PLOTNINE BUILDER FUNCTIONS — Risk / simulation
# =========================================================================


def build_plotnine_simulation_fan_chart(
    *, results_df: Any) -> Any:
    """Build a Monte-Carlo fan chart as a plotnine ggplot.

    Parameters
    ----------
    results_df : polars.DataFrame | None
        DataFrame with ``Date`` and ``Scenario_*`` columns, or with
        percentile columns (``p5``, ``p25``, ``median``, ``p75``, ``p95``).

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        # pandas required by plotnine API — plotnine demands DataFrame input; Polars not accepted here
        import pandas as pd

        if results_df is None:
            return None
        df = pl.from_pandas(results_df) if not isinstance(results_df, pl.DataFrame) else results_df
        scenario_cols = [
            c for c in df.columns if c.startswith("Scenario_") and df.schema.get(c) != pl.Boolean
        ]
        if not scenario_cols:
            return None

        arr = df.select(scenario_cols).to_numpy()
        date_col = df["Date"].to_list() if "Date" in df.columns else list(range(df.height))

        band_df = pd.DataFrame(
            {
                "Date": date_col,
                "p5": [float(np.percentile(r, 5)) for r in arr],
                "p25": [float(np.percentile(r, 25)) for r in arr],
                "median": [float(np.percentile(r, 50)) for r in arr],
                "p75": [float(np.percentile(r, 75)) for r in arr],
                "p95": [float(np.percentile(r, 95)) for r in arr],
            },
        )
        band_df["Date"] = _parse_dates_as_naive(date_col = band_df["Date"])

        return (
            ggplot(band_df, aes(x="Date"))
            + geom_ribbon(aes(ymin="p5", ymax="p95"), fill="#aec7e8", alpha=0.4)
            + geom_ribbon(aes(ymin="p25", ymax="p75"), fill="#1f77b4", alpha=0.4)
            + geom_line(aes(y="median"), color="#1f77b4", size=1)
            + scale_x_date(date_labels="%Y-%m")
            + labs(
                title="Monte Carlo Simulation — Portfolio Value Fan Chart",
                x="Date",
                y="Portfolio Value ($)",
            )
            + _QWIM_THEME
        )
    except Exception as exc:  # pragma: no cover
        _logger.warning("build_plotnine_simulation_fan_chart: %s", exc)
        return None


def build_plotnine_simulation_terminal_value_distribution(
    *, terminal_values: Any) -> Any:
    """Build a terminal-value histogram as a plotnine ggplot.

    Parameters
    ----------
    terminal_values : numpy.ndarray | list | None
        Array of terminal portfolio values from simulation scenarios.

    Returns
    -------
    plotnine.ggplot | None
    """
    try:
        # pandas required by plotnine API — plotnine demands DataFrame input; Polars not accepted here
        import pandas as pd

        if terminal_values is None:
            return None
        raw_vals = np.asarray(terminal_values, dtype=object).flatten()
        if any(isinstance(value, (bool, np.bool_)) for value in raw_vals):
            return None
        vals_arr = np.asarray(terminal_values, dtype=float).flatten()
        if vals_arr.size < 2:
            return None
        df = pd.DataFrame({"terminal_value": vals_arr})
        mean_val = float(vals_arr.mean())
        median_val = float(np.median(vals_arr))

        return (
            ggplot(df, aes(x="terminal_value"))
            + geom_histogram(bins=50, fill="#1f77b4", alpha=0.7, color="white")
            + geom_vline(xintercept=mean_val, linetype="dashed", color="#ff7f0e", size=1)
            + geom_vline(xintercept=median_val, linetype="solid", color="#2ca02c", size=1)
            + labs(
                title="Terminal Value Distribution",
                x="Terminal Portfolio Value ($)",
                y="Frequency",
            )
            + _QWIM_THEME
            + theme(figure_size=(10, 5))
        )
    except Exception as exc:  # pragma: no cover
        _logger.warning("build_plotnine_simulation_terminal_value_distribution: %s", exc)
        return None


# =========================================================================
# EXPORT FUNCTIONS — Risk / simulation
# =========================================================================


def export_plot_simulation_fan_chart(
    *, reactives_shiny: dict | None) -> Any:
    """Render the Monte Carlo simulation fan chart as SVG.

    The fan chart shows P5-P95 and P25-P75 confidence bands plus median.

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
    Boolean percentile or mean columns are treated as invalid fan-chart data.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    fan_data = inner.get("Simulation_Fan_Data")
    if fan_data is not None:
        from ._report_plot_returns import _safe_reactive_get  # noqa: PLC0415

        fan_data = _safe_reactive_get(reactive_value = fan_data)

    if not isinstance(fan_data, pl.DataFrame) or fan_data.height < 2:
        _logger.info("Building simulation fan data from sample CSV")
        _pv_fan, _ = _load_sample_csv_for_plots()
        if _pv_fan is not None and _pv_fan.height >= 2:
            fan_data = _build_simulation_fan_data(pv = _pv_fan)

    if not isinstance(fan_data, pl.DataFrame) or fan_data.height < 2:
        _logger.warning("No simulation fan data for fan chart")
        return None

    invalid_fan_columns = [
        column_name
        for column_name in ("p5", "p25", "median", "mean", "p75", "p95")
        if column_name in fan_data.columns and fan_data.schema.get(column_name) == pl.Boolean
    ]
    if invalid_fan_columns:
        _logger.warning(
            "Simulation fan data contains boolean plot columns: %s",
            invalid_fan_columns,
        )
        return None

    pdf = fan_data.to_pandas()
    if "day" not in pdf.columns:
        pdf["day"] = range(len(pdf))

    p = ggplot(pdf, aes(x="day"))

    if "p5" in pdf.columns and "p95" in pdf.columns:
        p = p + geom_ribbon(aes(ymin="p5", ymax="p95"), fill="#1f77b4", alpha=0.15)

    if "p25" in pdf.columns and "p75" in pdf.columns:
        p = p + geom_ribbon(aes(ymin="p25", ymax="p75"), fill="#1f77b4", alpha=0.3)

    if "median" in pdf.columns:
        p = p + geom_line(aes(y="median"), color="#1f77b4", size=1.2)

    if "mean" in pdf.columns:
        p = p + geom_line(aes(y="mean"), color="#ff7f0e", size=1, linetype="dashed")

    initial = _safe_float(value = pdf.get("median", [100])[0] if "median" in pdf.columns else 100)
    p = p + geom_hline(yintercept=initial, linetype="dotted", color="#888888", size=0.5)

    p = (
        p
        + labs(
            title="Monte Carlo Simulation — Portfolio Value Paths",
            x="Trading Day",
            y="Portfolio Value ($)",
        )
        + _QWIM_THEME
    )

    return _save_plot(plot = p, filename = "chart_simulation_portfolio_value_fan_chart.svg")


def export_plot_simulation_histogram(
    *, reactives_shiny: dict | None) -> Any:
    """Render the terminal-value distribution histogram as SVG.

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
    Boolean terminal values are treated as invalid histogram input.
    """
    inner = _get_inner_variables(reactives_shiny = reactives_shiny)

    terminal_values = inner.get("Simulation_Terminal_Values")
    if terminal_values is not None:
        from ._report_plot_returns import _safe_reactive_get  # noqa: PLC0415

        terminal_values = _safe_reactive_get(reactive_value = terminal_values)

    if terminal_values is None:
        _logger.info("Building simulation terminal values from sample CSV")
        _pv_hist, _ = _load_sample_csv_for_plots()
        if _pv_hist is not None and _pv_hist.height >= 2:
            portfolio_value_series = _pv_hist.get_column("portfolio_value").drop_nulls()
            if portfolio_value_series.dtype != pl.Boolean:
                pv_arr = portfolio_value_series.cast(pl.Float64, strict=False).drop_nulls().to_numpy()
                if pv_arr.size >= 2:
                    rets = np.diff(pv_arr) / pv_arr[:-1]
                    mu = float(np.mean(rets))
                    sigma = float(np.std(rets, ddof=1))
                    rng = np.random.default_rng(42)
                    terminal_values = 100.0 * np.prod(
                        1.0 + rng.normal(mu, sigma, size=(1000, 252)),
                        axis=1,
                    )

    if terminal_values is None:
        return None

    # pandas required by plotnine API — plotnine demands DataFrame input; Polars not accepted here
    import pandas as pd

    if isinstance(terminal_values, pl.DataFrame):
        vals = terminal_values.to_pandas()
    elif isinstance(terminal_values, (list, np.ndarray)):
        vals = pd.DataFrame({"terminal_value": terminal_values})
    else:
        return None

    if vals.empty:
        return None

    val_col = "terminal_value" if "terminal_value" in vals.columns else vals.columns[0]
    vals = vals.rename(columns={val_col: "terminal_value"})

    if any(isinstance(value_item, (bool, np.bool_)) for value_item in vals["terminal_value"].tolist()):
        _logger.warning("Simulation histogram data contains boolean terminal values")
        return None

    mean_val = float(vals["terminal_value"].mean())
    median_val = float(vals["terminal_value"].median())

    p = (
        ggplot(vals, aes(x="terminal_value"))
        + geom_histogram(bins=50, fill="#1f77b4", alpha=0.7, color="white")
        + geom_vline(xintercept=mean_val, linetype="dashed", color="#ff7f0e", size=1)
        + geom_vline(xintercept=median_val, linetype="solid", color="#2ca02c", size=1)
        + labs(
            title="Terminal Value Distribution",
            x="Terminal Portfolio Value ($)",
            y="Frequency",
        )
        + _QWIM_THEME
        + theme(figure_size=(10, 5))
    )

    return _save_plot(plot = p, filename = "chart_simulation_terminal_value_distribution.svg", width=10, height=5)
