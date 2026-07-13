"""Public facade for the portfolio weights analysis subtab."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from shiny import module, ui
from shinywidgets import output_widget

from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
    normalize_weights_source_frame,
)
from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_rendering import (
    register_weights_analysis_outputs,
)
from src.dashboard.shiny_utils.utils_data import validate_portfolio_data
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

OUTPUT_DIR = Path("output")


@module.ui
def subtab_weights_analysis_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:  # pragma: no cover
    """Build the public weights-analysis UI for the portfolio tab."""
    del data_utils, data_inputs

    return ui.div(
        ui.h3("Portfolio Weight Analysis"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("📅 Time Period Selection", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_weights_analysis_time_period",
                    "Select Time Period",
                    {
                        "custom": "Custom",
                        "1y": "Last 1 Year",
                        "3y": "Last 3 Years",
                        "5y": "Last 5 Years",
                        "10y": "Last 10 Years",
                        "ytd": "Year to Date",
                    },
                    selected="5y",
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_portfolios_subtab_weights_analysis_time_period === 'custom'",
                    ui.div(
                        ui.input_date_range(
                            "input_ID_tab_portfolios_subtab_weights_analysis_date_range",
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
                    "input.input_ID_tab_portfolios_subtab_weights_analysis_time_period !== 'custom'",
                    ui.div(
                        ui.output_text(
                            "output_ID_tab_portfolios_subtab_weights_analysis_calculated_date_range",
                        ),
                        class_="mt-2 p-2 bg-light rounded text-muted small",
                    ),
                ),
                ui.hr(),
                ui.h5("🔧 Select Components", class_="mb-3"),
                ui.div(
                    ui.input_checkbox(
                        "input_ID_tab_portfolios_subtab_weights_analysis_select_all_components",
                        "Select All ETFs",
                        value=False,
                    ),
                    class_="mb-2",
                ),
                ui.div(
                    ui.output_ui(
                        "output_ID_tab_portfolios_subtab_weights_analysis_component_checkboxes",
                    ),
                    class_="component-selection-container",
                    style=(
                        "max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; "
                        "border-radius: 0.375rem; padding: 0.5rem;"
                    ),
                ),
                ui.div(
                    ui.output_text(
                        "output_ID_tab_portfolios_subtab_weights_analysis_selected_components_count",
                    ),
                    class_="mt-1 text-muted small",
                ),
                ui.hr(),
                ui.h5("📊 Visualization Options", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_portfolios_subtab_weights_analysis_viz_type",
                    "Visualization Type",
                    {
                        "area": "Stacked Area Chart",
                        "bar": "Stacked Bar Chart",
                        "line": "Line Chart",
                        "heatmap": "Heatmap",
                    },
                    selected="area",
                ),
                ui.input_checkbox(
                    "input_ID_tab_portfolios_subtab_weights_analysis_show_pct",
                    "Show as Percentage",
                    value=True,
                ),
                ui.input_checkbox(
                    "input_ID_tab_portfolios_subtab_weights_analysis_sort_components",
                    "Sort Components by Weight",
                    value=True,
                ),
                ui.hr(),
                ui.h5("ℹ️ Data Information", class_="mb-3"),
                ui.output_ui("output_ID_tab_portfolios_subtab_weights_analysis_data_info"),
                width=350,
                position="left",
            ),
            ui.div(
                ui.output_ui("output_ID_tab_portfolios_subtab_weights_analysis_loading_status"),
                ui.card(
                    ui.card_header("Portfolio Weight Distribution Over Time"),
                    output_widget(
                        "output_ID_tab_portfolios_subtab_weights_analysis_plot_main",
                        height="600px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                ui.div(
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Current Portfolio Composition"),
                            output_widget(
                                "output_ID_tab_portfolios_subtab_weights_analysis_plot_secondary",
                                height="400px",
                                width="100%",
                            ),
                            class_="h-100",
                        ),
                        ui.card(
                            ui.card_header("Weight Statistics"),
                            ui.output_ui(
                                "output_ID_tab_portfolios_subtab_weights_analysis_table_summary",
                            ),
                            class_="h-100",
                        ),
                        col_widths=[6, 6],
                    ),
                    class_="mt-3",
                ),
                class_="flex-fill",
            ),
        ),
    )


@module.server
def subtab_weights_analysis_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Validate inputs and register the extracted weights-analysis outputs."""
    del session

    data_portfolio = data_inputs.get("My_Portfolio")
    data_benchmark = data_inputs.get("Benchmark_Portfolio")
    weights_portfolio = data_inputs.get("Weights_My_Portfolio")

    _logger.debug(
        "Weights Analysis MODULE — data_inputs keys: %s, weights type: %s",
        list(data_inputs.keys()),
        type(weights_portfolio),
    )

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

    weights_frame = normalize_weights_source_frame(weights_source = weights_portfolio)

    register_weights_analysis_outputs(
        input=input,
        output=output,
        data_utils=data_utils,
        weights_frame=weights_frame,
        reactives_shiny=reactives_shiny,
    )