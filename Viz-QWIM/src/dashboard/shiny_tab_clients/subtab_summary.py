"""Client summary facade for the Clients dashboard tab.

This public module keeps the Shiny UI entry point and stable import surface for
the client summary subtab. The heavier data-building and renderer registration
logic now lives in private helper modules so this file remains below the
project size limit while preserving the public summary keywords and output
identifiers used by source-facing tests.
"""

from __future__ import annotations

from typing import Any

from shiny import module, ui

from src.dashboard.shiny_tab_clients._subtab_summary_data import (
    normalize_data_personal_info_summary,
)
from src.dashboard.shiny_tab_clients._subtab_summary_rendering import (
    register_clients_summary_server_outputs,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


__all__ = [
    "normalize_data_personal_info_summary",
    "subtab_clients_summary_server",
    "subtab_clients_summary_ui",
]



_logger = get_logger(name = __name__)



@module.ui
def subtab_clients_summary_ui(
    *, data_utils: dict, data_inputs: dict) -> Any:  # pragma: no cover
    """Create the client summary user interface."""
    return ui.div(
        ui.h3("client Summary", class_="text-center mb-4"),
        ui.row(
            ui.column(
                12,
                ui.card(
                    ui.card_header(ui.h4("Personal Information Summary", class_="text-center")),
                    ui.card_body(
                        ui.output_ui(
                            "output_ID_tab_clients_subtab_clients_summary_table_personal_info",
                        ),
                        class_="text-center",
                    ),
                ),
            ),
        ),
        ui.row(
            ui.column(
                12,
                ui.card(
                    ui.card_header(ui.h4("Financial Assets Summary", class_="text-center")),
                    ui.card_body(
                        ui.output_ui("output_ID_tab_clients_subtab_clients_summary_table_assets"),
                        class_="text-center",
                    ),
                ),
            ),
        ),
        ui.row(
            ui.column(
                12,
                ui.card(
                    ui.card_header(ui.h4("Financial Goals Summary", class_="text-center")),
                    ui.card_body(
                        ui.output_ui("output_ID_tab_clients_subtab_clients_summary_table_goals"),
                        class_="text-center",
                    ),
                ),
            ),
        ),
        ui.row(
            ui.column(
                12,
                ui.card(
                    ui.card_header(ui.h4("Income Sources Summary", class_="text-center")),
                    ui.card_body(
                        ui.output_ui("output_ID_tab_clients_subtab_clients_summary_table_income"),
                        class_="text-center",
                    ),
                ),
            ),
        ),
    )



@module.server
def subtab_clients_summary_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:
    """Register the client summary server outputs."""
    register_clients_summary_server_outputs(
        _input_events=input,
        output=output,
        reactives_shiny=reactives_shiny,
    )
