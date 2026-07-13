"""Portfolio analysis Shiny facade."""

from __future__ import annotations

import typing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from shiny import module, ui
from shinywidgets import output_widget

from src.dashboard.shiny_tab_portfolios._subtab_portfolios_analysis_rendering import (
    register_portfolios_analysis_outputs,
)
from src.dashboard.shiny_utils.utils_data import validate_portfolio_data
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

OUTPUT_DIR = Path("output")


@module.ui
def subtab_portfolios_analysis_ui(*, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create the UI for the portfolio analysis subtab."""
    del data_utils, data_inputs

    return ui.div(
        ui.h3("Portfolio Performance Analysis"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("📅 Time Period Selection", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_portfolios_analysis_time_period",
                    "Select Time Period",
                    {
                        "custom": "Custom",
                        "1y": "Last 1 Year",
                        "3y": "Last 3 Years",
                        "5y": "Last 5 Years",
                        "10y": "Last 10 Years",
                        "ytd": "Year to Date",
                    },
                    selected="1y",
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_portfolios_subtab_portfolios_analysis_time_period === 'custom'",
                    ui.div(
                        ui.input_date_range(
                            "input_ID_tab_portfolios_subtab_portfolios_analysis_date_range",
                            "Custom Date Range",
                            start=datetime.now(UTC) - timedelta(days=365),
                            end=datetime.now(UTC),
                            format="yyyy-mm-dd",
                            separator=" to ",
                            width="100%",
                        ),
                        class_="mt-2",
                    ),
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_portfolios_subtab_portfolios_analysis_time_period !== 'custom'",
                    ui.div(
                        ui.output_text(
                            "output_ID_tab_portfolios_subtab_portfolios_analysis_calculated_date_range",
                        ),
                        class_="mt-2 p-2 bg-light rounded text-muted small",
                    ),
                ),
                ui.hr(),
                ui.h5("📊 Analysis Options", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_portfolios_analysis_type",
                    "Analysis Type",
                    {
                        "returns": "Returns Distribution",
                        "drawdowns": "Drawdowns Analysis",
                        "rolling": "Rolling Statistics",
                        "comparison": "Portfolio vs Benchmark",
                    },
                    selected="returns",
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_portfolios_subtab_portfolios_analysis_type === 'rolling'",
                    ui.div(
                        ui.input_slider(
                            "input_ID_tab_portfolios_subtab_portfolios_analysis_rolling_window",
                            "Rolling Window (days)",
                            min=7,
                            max=90,
                            value=30,
                            step=1,
                            width="100%",
                        ),
                        class_="mt-3",
                    ),
                ),
                ui.input_checkbox(
                    "input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark",
                    "Include Benchmark in Analysis",
                    value=True,
                ),
                ui.hr(),
                ui.h5("ℹ️ Data Information", class_="mb-3"),
                ui.output_ui(
                    "output_ID_tab_portfolios_subtab_portfolios_analysis_data_info",
                ),
                width=350,
                position="left",
            ),
            ui.div(
                ui.output_ui(
                    "output_ID_tab_portfolios_subtab_portfolios_analysis_loading_status",
                ),
                ui.div(
                    ui.h4("Analysis Visualization", class_="mb-3"),
                    ui.div(
                        output_widget(
                            "output_ID_tab_portfolios_subtab_portfolios_analysis_plot_main",
                            width="100%",
                            height="600px",
                        ),
                        style=(
                            "min-height: 600px; width: 100%; border: 1px solid #dee2e6; "
                            "border-radius: 0.375rem; padding: 15px; background-color: white;"
                        ),
                    ),
                    class_="mb-4",
                ),
                ui.div(
                    ui.h4("Performance Statistics", class_="mb-3"),
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.h5(
                                    "Basic Statistics",
                                    class_="card-title text-primary mb-3",
                                ),
                                ui.div(
                                    ui.output_table(
                                        "output_ID_tab_portfolios_subtab_portfolios_analysis_table_stats",
                                    ),
                                    style=(
                                        "max-height: 500px; overflow-y: auto; overflow-x: auto; "
                                        "width: 100%;"
                                    ),
                                ),
                                class_="card card-body h-100",
                                style="min-width: 450px;",
                            ),
                            class_="col-lg-6 col-xl-6 mb-3",
                            style="min-width: 450px;",
                        ),
                        ui.div(
                            ui.div(
                                ui.h5(
                                    "Performance Metrics",
                                    class_="card-title text-primary mb-3",
                                ),
                                ui.div(
                                    ui.output_table(
                                        "output_ID_tab_portfolios_subtab_portfolios_analysis_table_quantstats_metrics",
                                    ),
                                    style=(
                                        "max-height: 500px; overflow-y: auto; overflow-x: auto; "
                                        "width: 100%;"
                                    ),
                                ),
                                class_="card card-body h-100",
                                style="min-width: 450px;",
                            ),
                            class_="col-lg-6 col-xl-6 mb-3",
                            style="min-width: 450px;",
                        ),
                        class_="row",
                        style="min-width: 900px;",
                    ),
                    class_="mt-4",
                    style="width: 100%; overflow-x: auto;",
                ),
                class_="flex-fill",
            ),
        ),
    )


@module.server
def subtab_portfolios_analysis_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:
    """Validate the public inputs and register the private analysis outputs."""
    del session, data_utils

    data_portfolio = data_inputs.get("My_Portfolio")
    data_benchmark = data_inputs.get("Benchmark_Portfolio")

    validation_portfolio = validate_portfolio_data(data_portfolio=data_portfolio)
    validation_benchmark = validate_portfolio_data(data_portfolio=data_benchmark)

    if not validation_portfolio[0]:
        raise Exception_Validation_Input(
            f"Portfolio data validation failed: {validation_portfolio[1]}",
        )

    if not validation_benchmark[0]:
        raise Exception_Validation_Input(
            f"Benchmark data validation failed: {validation_benchmark[1]}",
        )

    register_portfolios_analysis_outputs(
        input=input,
        output=output,
        data_portfolio=data_portfolio,
        data_benchmark=data_benchmark,
        reactives_shiny=reactives_shiny,
    )