from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from shiny import ui

from src.dashboard.reporting.report_plot_export import (
    build_plotnine_optimalportfolios_performance_comparison,
    build_plotnine_optimalportfolios_weights_comparison,
)
from src.dashboard.shiny_utils.reactives_shiny import update_visual_object_in_reactives
from src.dashboard.shiny_utils.utils_visuals import create_error_figure


def compute_optimalportfolios_performance_series_impl_QWIM(
    *, portfolio_1: Any, portfolio_2: Any, etf_data: pl.DataFrame | None, time_period: Any, default_time_period: str) -> tuple[pl.DataFrame | None, pl.DataFrame | None]:
    """Compute base-100 value series for both portfolios over the selected window."""
    if portfolio_1 is None or portfolio_2 is None:
        return None, None
    if etf_data is None or etf_data.is_empty():
        return None, None

    try:
        data_max_date_raw = etf_data["Date"].max()
        ts_max = pd.Timestamp(data_max_date_raw)
        anchor = ts_max.tz_convert(None) if ts_max.tzinfo is not None else ts_max
    except Exception:
        anchor = pd.Timestamp(datetime.now(UTC)).tz_convert(None)

    end_date = anchor.strftime("%Y-%m-%d")
    selected_period = str(time_period or default_time_period)
    if selected_period == "1y":
        start_date = (anchor - timedelta(days=365)).strftime("%Y-%m-%d")
    elif selected_period == "3y":
        start_date = (anchor - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
    elif selected_period == "5y":
        start_date = (anchor - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
    elif selected_period == "10y":
        start_date = (anchor - timedelta(days=10 * 365)).strftime("%Y-%m-%d")
    else:
        start_date = str(etf_data["Date"].min())

    prices = etf_data.filter(
        (pl.col("Date") >= start_date) & (pl.col("Date") <= end_date),
    ).sort("Date")
    if prices.is_empty() or prices.height < 2:
        return None, None

    def _value_series(*, portfolio_obj: Any) -> pl.DataFrame | None:
        weights_df = portfolio_obj.get_portfolio_weights()
        assets = [column_name for column_name in weights_df.columns if column_name != "Date"]
        common_assets = [asset_name for asset_name in assets if asset_name in prices.columns]
        if not common_assets:
            return None

        weights = np.array(
            [float(weights_df[asset_name][0]) for asset_name in common_assets],
            dtype=np.float64,
        )
        price_matrix = prices.select(common_assets).to_numpy().astype(np.float64)
        returns_matrix = np.diff(price_matrix, axis=0) / price_matrix[:-1]
        portfolio_returns = returns_matrix @ weights
        cumulative_values = np.empty(len(portfolio_returns) + 1, dtype=np.float64)
        cumulative_values[0] = 100.0
        for index_value, period_return in enumerate(portfolio_returns):
            cumulative_values[index_value + 1] = cumulative_values[index_value] * (
                1.0 + period_return
            )

        return pl.DataFrame(
            {
                "Date": prices["Date"].to_list(),
                "Value": cumulative_values.tolist(),
            },
        )

    return _value_series(portfolio_obj = portfolio_1), _value_series(portfolio_obj = portfolio_2)


def build_optimalportfolios_statistics_rows_impl_QWIM(
    *, series_1: pl.DataFrame | None, series_2: pl.DataFrame | None, has_quantstats: bool, qs_module: Any) -> list[dict[str, Any]]:
    """Build portfolio comparison metric rows from two normalized value series."""
    if series_1 is None or series_2 is None:
        return []
    if len(series_1) < 2 or len(series_2) < 2:
        return []

    values_1 = np.array(series_1["Value"].to_list(), dtype=np.float64)
    values_2 = np.array(series_2["Value"].to_list(), dtype=np.float64)
    returns_1 = pd.Series(np.diff(values_1) / values_1[:-1])
    returns_2 = pd.Series(np.diff(values_2) / values_2[:-1])

    def _safe_metric(*, metric_func: Any, returns_series: pd.Series) -> float:
        try:
            raw_value = metric_func(returns_series)
            numeric_value = (
                float(raw_value.iloc[-1])
                if isinstance(raw_value, pd.Series) and not raw_value.empty
                else float(raw_value)
            )
            return 0.0 if np.isnan(numeric_value) or np.isinf(numeric_value) else numeric_value
        except Exception:
            return 0.0

    if has_quantstats:

        def _cagr(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.cagr(returns_series)

        def _vol(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.volatility(returns_series)

        def _sharpe(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.sharpe(returns_series, rf=0.02)

        def _sortino(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.sortino(returns_series, rf=0.02)

        def _mdd(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.max_drawdown(returns_series)

        def _calmar(*, returns_series: pd.Series) -> Any:
            return qs_module.stats.calmar(returns_series)

    else:

        def _cagr(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            returns_array = np.array(returns_series, dtype=np.float64)
            return (
                float(np.prod(1.0 + returns_array) ** (252.0 / len(returns_array)) - 1.0)
                if len(returns_array) > 0
                else 0.0
            )

        def _vol(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            returns_array = np.array(returns_series, dtype=np.float64)
            return float(np.std(returns_array, ddof=1) * np.sqrt(252.0))

        def _sharpe(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            cagr_value, volatility_value = _cagr(returns_series = returns_series), _vol(returns_series = returns_series)
            return float((cagr_value - 0.02) / volatility_value) if volatility_value > 1e-12 else 0.0

        def _sortino(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            returns_array = np.array(returns_series, dtype=np.float64)
            cagr_value = _cagr(returns_series = returns_series)
            downside = returns_array[returns_array < 0.0]
            downside_vol = (
                float(np.std(downside, ddof=1) * np.sqrt(252.0)) if len(downside) > 1 else 1e-12
            )
            return float((cagr_value - 0.02) / downside_vol) if downside_vol > 1e-12 else 0.0

        def _mdd(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            returns_array = np.array(returns_series, dtype=np.float64)
            cumulative = np.cumprod(1.0 + returns_array)
            peak = np.maximum.accumulate(cumulative)
            return float(np.min(cumulative / peak - 1.0))

        def _calmar(*, returns_series: pd.Series) -> float:  # type: ignore[misc]
            cagr_value, max_drawdown_value = _cagr(returns_series = returns_series), abs(_mdd(returns_series = returns_series))
            return float(cagr_value / max_drawdown_value) if max_drawdown_value > 1e-12 else 0.0

    specs: list[tuple[str, Any, str]] = [
        ("CAGR", _cagr, "pct"),
        ("Volatility", _vol, "pct"),
        ("Sharpe Ratio", _sharpe, "ratio"),
        ("Sortino Ratio", _sortino, "ratio"),
        ("Max Drawdown", _mdd, "pct"),
        ("Calmar Ratio", _calmar, "ratio"),
    ]
    return [
        {
            "metric": metric_name,
            "method1": _safe_metric(metric_func = metric_func, returns_series = returns_1),
            "method2": _safe_metric(metric_func = metric_func, returns_series = returns_2),
            "difference": _safe_metric(metric_func = metric_func, returns_series = returns_2)
            - _safe_metric(metric_func = metric_func, returns_series = returns_1),
            "format": format_kind,
        }
        for metric_name, metric_func, format_kind in specs
    ]


def render_optimalportfolios_weights_plot_impl_QWIM(
    *, portfolio_1: Any, portfolio_2: Any, reactives_shiny: dict[str, Any]) -> Any:
    """Render the grouped weights comparison plot for two optimized portfolios."""
    if portfolio_1 is None or portfolio_2 is None:
        return create_error_figure(
            message_text = "Run optimization to see weights comparison",
            title_text = "Click 'Run Optimization' to compare portfolios",
        )

    try:
        import plotly.graph_objects as go

        weights_1 = portfolio_1.get_portfolio_weights()
        weights_2 = portfolio_2.get_portfolio_weights()
        assets = [column_name for column_name in weights_1.columns if column_name != "Date"]
        method_1_values = [weights_1[asset_name][0] * 100 for asset_name in assets]
        method_2_values = [weights_2[asset_name][0] * 100 for asset_name in assets]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name=portfolio_1.get_portfolio_name,
                x=assets,
                y=method_1_values,
                marker_color="rgb(55, 83, 109)",
            ),
        )
        fig.add_trace(
            go.Bar(
                name=portfolio_2.get_portfolio_name,
                x=assets,
                y=method_2_values,
                marker_color="rgb(26, 118, 255)",
            ),
        )
        fig.update_layout(
            barmode="group",
            title="Portfolio Weights Comparison",
            xaxis_title="Assets",
            yaxis_title="Weight (%)",
            template="plotly_white",
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        plotnine_fig = build_plotnine_optimalportfolios_weights_comparison(
            assets = assets,
            weights1 = method_1_values,
            weights2 = method_2_values,
            name1=portfolio_1.get_portfolio_name,
            name2=portfolio_2.get_portfolio_name,
        )
        update_visual_object_in_reactives(
            reactives_shiny = reactives_shiny,
            chart_key = "Chart_OptimalPortfolios_Optimization_Portfolio_Weights_Comparison",
            figure = plotnine_fig,
        )
        return fig
    except Exception as exc:
        return create_error_figure(message_text = "Error creating plot", title_text = str(exc))


def render_optimalportfolios_results_table_impl_QWIM(
    *, portfolio_1: Any, portfolio_2: Any) -> Any:
    """Render the side-by-side weights comparison table."""
    if portfolio_1 is None or portfolio_2 is None:
        return ui.p("Run optimization to see results", class_="text-muted text-center p-4")

    try:
        weights_1 = portfolio_1.get_portfolio_weights()
        weights_2 = portfolio_2.get_portfolio_weights()
        assets = [column_name for column_name in weights_1.columns if column_name != "Date"]

        table_rows: list[str] = [
            "<tr><th>Asset</th><th>Portfolio 1 (%)</th><th>Portfolio 2 (%)</th><th>Difference</th></tr>",
        ]
        for asset_name in assets:
            method_1_weight = weights_1[asset_name][0] * 100
            method_2_weight = weights_2[asset_name][0] * 100
            difference = method_2_weight - method_1_weight
            diff_color = (
                "text-success"
                if difference > 0
                else "text-danger"
                if difference < 0
                else "text-muted"
            )
            table_rows.append(
                f"<tr><td><strong>{asset_name}</strong></td>"
                f"<td>{method_1_weight:.2f}%</td><td>{method_2_weight:.2f}%</td>"
                f"<td class='{diff_color}'>{difference:+.2f}%</td></tr>",
            )

        return ui.HTML(
            f"""
            <div class=\"table-responsive\">
                <table class=\"table table-sm table-hover\">
                    <thead class=\"table-light\">{"".join(table_rows[:1])}</thead>
                    <tbody>{"".join(table_rows[1:])}</tbody>
                </table>
            </div>
            <div class=\"mt-3 p-3 bg-light rounded\">
                <p class=\"mb-1\"><strong>Portfolio 1:</strong> {portfolio_1.get_portfolio_name}</p>
                <p class=\"mb-1\"><strong>Portfolio 2:</strong> {portfolio_2.get_portfolio_name}</p>
                <p class=\"mb-0 text-muted small\"><i>Number of assets: {len(assets)} |
                Optimization date: {weights_1["Date"][0]}</i></p>
            </div>
            """,
        )
    except Exception as exc:
        return ui.p(f"Error: {exc!s}", class_="text-danger")


def render_optimalportfolios_statistics_table_impl_QWIM(
    *, portfolio_1: Any, portfolio_2: Any, stats_rows: list[dict[str, Any]]) -> Any:
    """Render the statistics comparison table for two optimized portfolios."""
    if portfolio_1 is None or portfolio_2 is None:
        return ui.p(
            "Run optimization to see portfolio statistics",
            class_="text-muted text-center p-4",
        )
    if not stats_rows:
        return ui.p(
            "No statistics data available for selected time period.",
            class_="text-muted text-center p-3",
        )

    def _fmt_pct(*, value: float) -> str:
        return f"{value * 100:.2f}%"

    def _fmt_ratio(*, value: float) -> str:
        return f"{value:.3f}"

    table_rows = [
        f"<tr><th>Metric</th><th>{portfolio_1.get_portfolio_name}</th>"
        f"<th>{portfolio_2.get_portfolio_name}</th><th>Difference</th></tr>",
    ]
    for row in stats_rows:
        is_pct = row.get("format") == "pct"
        method_1_string = (
            _fmt_pct(value = float(row["method1"])) if is_pct else _fmt_ratio(value = float(row["method1"]))
        )
        method_2_string = (
            _fmt_pct(value = float(row["method2"])) if is_pct else _fmt_ratio(value = float(row["method2"]))
        )
        diff_value = float(row["difference"])
        diff_string = f"{diff_value * 100:+.2f}%" if is_pct else f"{diff_value:+.3f}"
        diff_color = (
            "text-success"
            if diff_value > 0
            else "text-danger"
            if diff_value < 0
            else "text-muted"
        )
        table_rows.append(
            f"<tr><td><strong>{row['metric']}</strong></td>"
            f"<td>{method_1_string}</td><td>{method_2_string}</td>"
            f"<td class='{diff_color}'>{diff_string}</td></tr>",
        )

    return ui.HTML(
        f"""
        <div class=\"table-responsive\">
            <table class=\"table table-sm table-hover\">
                <thead class=\"table-light\">{"".join(table_rows[:1])}</thead>
                <tbody>{"".join(table_rows[1:])}</tbody>
            </table>
        </div>
        """,
    )


def render_optimalportfolios_performance_plot_impl_QWIM(
    *, portfolio_1: Any, portfolio_2: Any, perf_1: pl.DataFrame | None, perf_2: pl.DataFrame | None, reactives_shiny: dict[str, Any]) -> Any:
    """Render the normalized performance comparison chart for two portfolios."""
    if portfolio_1 is None or portfolio_2 is None:
        return create_error_figure(
            message_text = "Run optimization to see performance comparison",
            title_text = "Click 'Run Optimization' to compare portfolio performance over time",
        )
    if perf_1 is None and perf_2 is None:
        return create_error_figure(
            message_text = "Insufficient Price Data",
            title_text = "Could not compute portfolio values - check that ETF price data is available for the selected period.",
        )

    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        if perf_1 is not None:
            fig.add_trace(
                go.Scatter(
                    x=perf_1["Date"].to_list(),
                    y=perf_1["Value"].to_list(),
                    mode="lines",
                    name=portfolio_1.get_portfolio_name,
                    line={"color": "rgb(55, 83, 109)", "width": 2},
                    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Value: %{y:.2f}<extra></extra>",
                ),
            )
        if perf_2 is not None:
            fig.add_trace(
                go.Scatter(
                    x=perf_2["Date"].to_list(),
                    y=perf_2["Value"].to_list(),
                    mode="lines",
                    name=portfolio_2.get_portfolio_name,
                    line={"color": "rgb(26, 118, 255)", "width": 2},
                    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Value: %{y:.2f}<extra></extra>",
                ),
            )

        fig.update_layout(
            title="Portfolio Performance Comparison (Normalized, Base = 100)",
            xaxis_title="Date",
            yaxis_title="Portfolio Value",
            template="plotly_white",
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            xaxis={
                "rangeslider": {"visible": True},
                "rangeselector": {
                    "buttons": [
                        {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                        {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                        {"count": 1, "label": "YTD", "step": "year", "stepmode": "todate"},
                        {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                        {"step": "all", "label": "All"},
                    ],
                },
            },
        )

        plotnine_fig = build_plotnine_optimalportfolios_performance_comparison(
            perf1_df = perf_1,
            perf2_df = perf_2,
            name1=portfolio_1.get_portfolio_name,
            name2=portfolio_2.get_portfolio_name,
        )
        update_visual_object_in_reactives(
            reactives_shiny = reactives_shiny,
            chart_key = "Chart_OptimalPortfolios_Optimization_Comparison_Portfolio_Performance",
            figure = plotnine_fig,
        )
        return fig
    except Exception as exc:
        return create_error_figure(message_text = "Error creating performance plot", title_text = str(exc))