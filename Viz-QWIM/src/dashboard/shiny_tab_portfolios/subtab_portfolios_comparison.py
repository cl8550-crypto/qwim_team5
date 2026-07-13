"""Portfolio comparison facade for the Portfolios dashboard tab.

This public module keeps the Shiny UI entry point and public server facade for
portfolio-versus-benchmark analysis. The heavy server implementation lives in a
private helper module so this file stays below the project size limit while
preserving the existing import surface.
"""

from __future__ import annotations

import typing

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from shiny import module, ui
from shinywidgets import output_widget

from src.dashboard.shiny_tab_portfolios._subtab_portfolios_comparison_server import (
    register_portfolios_comparison_server_outputs,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


OUTPUT_DIR = Path("output")


@module.ui
def subtab_portfolios_comparison_ui(
    *, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create the Portfolio Comparison subtab user interface."""
    return ui.div(
        ui.h3("Portfolio vs Benchmark Comparison"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("📅 Time Period Selection", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_comparison_time_period",
                    "Select Time Period",
                    {
                        "custom": "Custom",
                        "1y": "Last 1 Year",
                        "3y": "Last 3 Years",
                        "5y": "Last 5 Years",
                        "10y": "Last 10 Years",
                        "ytd": "Year to Date",
                    },
                    selected="3y",
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_portfolios_subtab_comparison_time_period === 'custom'",
                    ui.div(
                        ui.input_date_range(
                            "input_ID_tab_portfolios_subtab_comparison_date_range",
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
                    "input.input_ID_tab_portfolios_subtab_comparison_time_period !== 'custom'",
                    ui.div(
                        ui.output_text(
                            "output_ID_tab_portfolios_subtab_comparison_calculated_date_range",
                        ),
                        class_="mt-2 p-2 bg-light rounded text-muted small",
                    ),
                ),
                ui.hr(),
                ui.h5("📊 Visualization Options", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_comparison_viz_type",
                    "Visualization Type",
                    {
                        "value": "Absolute Value",
                        "normalized": "Normalized (Base=100)",
                        "pct_change": "Percent Change",
                        "cum_return": "Cumulative Return",
                    },
                    selected="normalized",
                ),
                ui.input_checkbox(
                    "input_ID_tab_portfolios_subtab_comparison_show_diff",
                    "Show Difference Between Portfolio & Benchmark",
                    value=False,
                ),
                ui.hr(),
                ui.h5("ℹ️ Data Information", class_="mb-3"),
                ui.output_ui("output_ID_tab_portfolios_subtab_comparison_data_info"),
                width=350,
                position="left",
            ),
            ui.div(
                ui.output_ui("output_ID_tab_portfolios_subtab_comparison_loading_status"),
                ui.card(
                    ui.card_header("Portfolio vs Benchmark Performance"),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_comparison_plot_main",
                        height="600px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                ui.card(
                    ui.card_header("Performance Statistics"),
                    ui.output_ui("output_ID_tab_portfolios_subtab_comparison_table_stats"),
                    class_="mb-4",
                ),
                class_="flex-fill",
            ),
        ),
    )


@module.server
def subtab_portfolios_comparison_server(
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:  # pragma: no cover
    """Register the Portfolio Comparison server outputs."""
    register_portfolios_comparison_server_outputs(
        input=input,
        output=output,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
