"""Goal Parity subtab: Historical Backtest (walk-forward, no look-ahead).

Lets the user choose the date range, training window, test window, and step
size, then walk-forwards the full pipeline: every model input is re-estimated
per fold from training data only, the resulting strategic weights are held
over each step, and the realized out-of-sample equity curve is compared with
a 60/40-style benchmark. Runs on button click (each run re-solves the
optimizer once per fold).
"""

from __future__ import annotations

import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.models.goal_parity import BacktestResult, load_default_universe, run_walk_forward
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)

_STAT_LABELS: dict[str, str] = {
    "total_return": "Total return",
    "annualized_return": "Annualized return",
    "annualized_volatility": "Annualized volatility",
    "sharpe_ratio": "Sharpe ratio (rf = 0)",
    "max_drawdown": "Max drawdown",
}


def _data_date_range() -> tuple[datetime.date, datetime.date]:
    dates = load_default_universe().aligned_returns()["Date"]
    return dates.min(), dates.max()


@module.ui
def subtab_goal_parity_backtest_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    data_start, data_end = _data_date_range()
    return ui.div(
        ui.h3("Historical Backtest (Walk-Forward)"),
        ui.markdown(
            "Rolls a training window through history **without look-ahead**: at "
            "each step, every model input is re-estimated from past data only, "
            "the optimized portfolio is held for one step, and realized returns "
            "accumulate into the out-of-sample curve below, next to a 60/40 "
            "sectors/bonds benchmark. Uses the investor profile from Step 1 and "
            "the asset selection from Step 2."
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_date_range(
                    "input_date_range",
                    "Backtest date range",
                    start=data_start,
                    end=data_end,
                    min=data_start,
                    max=data_end,
                ),
                ui.input_numeric(
                    "input_train_years", "Training window (years)",
                    value=3.0, min=1.0, max=6.0, step=0.5,
                ),
                ui.input_numeric(
                    "input_test_months", "Test window (months)",
                    value=6, min=1, max=24, step=1,
                ),
                ui.input_numeric(
                    "input_step_months", "Step size (months)",
                    value=6, min=1, max=12, step=1,
                ),
                ui.markdown(
                    "*Step size defaults to the review frequency τ; the test "
                    "window is a per-fold reporting horizon and may overlap "
                    "the next fold when it exceeds the step.*"
                ),
                ui.input_action_button("input_run_backtest", "Run backtest", class_="btn-primary"),
                width=320,
            ),
            ui.output_ui("output_backtest_messages"),
            ui.output_text("output_backtest_summary"),
            output_widget("output_backtest_nav_plot"),
            ui.output_table("output_backtest_stats_table"),
            ui.output_table("output_backtest_folds_table"),
        ),
    )


@module.server
def subtab_goal_parity_backtest_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    *,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
    profile: Any,
    selected_tickers: Any,
):
    del output, session, data_utils, data_inputs, reactives_shiny

    result_value: reactive.Value[BacktestResult | None] = reactive.Value(None)
    error_value: reactive.Value[str | None] = reactive.Value(None)

    @reactive.effect
    @reactive.event(input.input_run_backtest)
    def _run() -> None:
        start, end = input.input_date_range()
        try:
            result = run_walk_forward(
                load_default_universe(),
                profile(),
                tickers=selected_tickers(),
                start_date=start,
                end_date=end,
                train_years=float(input.input_train_years() or 3.0),
                test_months=int(input.input_test_months() or 6),
                step_months=int(input.input_step_months() or 0) or None,
            )
        except ValueError as exc:
            _logger.warning("Backtest configuration rejected: %s", exc)
            error_value.set(str(exc))
            result_value.set(None)
            return
        error_value.set(None)
        result_value.set(result)

    @render.ui
    def output_backtest_messages() -> Any:
        error = error_value()
        if error is not None:
            return ui.div(
                ui.strong("Cannot run backtest: "), error, class_="alert alert-danger"
            )
        result = result_value()
        if result is None:
            return ui.div(
                "Choose the windows in the sidebar, then click Run backtest.",
                class_="alert alert-info",
            )
        if result.warnings:
            return ui.div(
                ui.strong("Please note: "), " ".join(result.warnings),
                class_="alert alert-warning",
            )
        return None

    @render.text
    def output_backtest_summary() -> str | None:
        result = result_value()
        if result is None:
            return None
        return (
            f"{len(result.folds)} walk-forward folds, out-of-sample "
            f"{result.dates[0]} to {result.dates[-1]} "
            f"({len(result.dates)} trading days). "
            f"Benchmark: {result.benchmark_description}."
        )

    @render_widget
    def output_backtest_nav_plot() -> go.Figure:
        result = result_value()
        figure = go.Figure()
        if result is not None:
            figure.add_trace(go.Scatter(
                x=result.dates, y=result.portfolio_nav,
                name="Goal Parity", line={"color": "#18bc9c", "width": 2},
            ))
            figure.add_trace(go.Scatter(
                x=result.dates, y=result.benchmark_nav,
                name="Benchmark (60/40)", line={"color": "#95a5a6", "width": 2},
            ))
            for fold in result.folds:
                figure.add_vline(x=fold.test_start, line_width=1, line_dash="dot",
                                 line_color="#dee2e6")
        figure.update_layout(
            title="Out-of-sample growth of $1 (dotted lines mark re-estimation dates)",
            yaxis_title="Growth of $1",
            template="plotly_white",
            legend={"orientation": "h", "y": 1.02, "x": 0},
            margin={"t": 80},
        )
        return figure

    @render.table
    def output_backtest_stats_table() -> pd.DataFrame | None:
        result = result_value()
        if result is None:
            return None
        rows = []
        for key, label in _STAT_LABELS.items():
            gp = result.summary["Goal Parity"][key]
            bench = result.summary["Benchmark"][key]
            fmt = "{:.2f}" if key == "sharpe_ratio" else "{:.2%}"
            rows.append({"Metric": label, "Goal Parity": fmt.format(gp),
                         "Benchmark": fmt.format(bench)})
        return pd.DataFrame(rows)

    @render.table
    def output_backtest_folds_table() -> pd.DataFrame | None:
        result = result_value()
        if result is None:
            return None
        return pd.DataFrame(
            {
                "#": i + 1,
                "Trained on": f"{f.train_start} → {f.train_end}",
                "Tested on": f"{f.test_start} → {f.test_end}",
                "Goal Parity": f"{f.portfolio_test_return:.2%}",
                "Benchmark": f"{f.benchmark_test_return:.2%}",
                "Solver": "ok" if f.solver_success else "did not converge",
            }
            for i, f in enumerate(result.folds)
        )
