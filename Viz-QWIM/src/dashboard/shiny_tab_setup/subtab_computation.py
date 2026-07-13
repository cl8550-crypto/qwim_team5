"""Computation subtab for the QWIM dashboard Setup area.

This module provides the ``Computation`` subtab under the dashboard ``Setup``
tab.  It lets users choose the computation engine and developer / debug options
for each computation-heavy subtab in the application.

Two UI sections are rendered:

1. **Computation Type** — a table with one ``input_select`` per subtab row,
   defaulting to ``"standard"``.
2. **Developer / Debug Options** — a collapsible ``<details>`` block with
   ``input_select`` / ``input_radio_buttons`` for Logger Display, Execution
   Thread Mode, and Profiler.

Subtab rows (in both tables)
-----------------------------
- Portfolio Comparison  (Portfolios tab)
- skfolio Optimization  (Portfolios tab)
- OptimalPortfolios Optimization  (Portfolios tab)
- Simulation  (Results tab)

Debug-only rows (in Developer / Debug Options table only)
---------------------------------------------------------
- Outline  (Clients tab)

Input ID naming follows the project convention::

    input_ID_tab_setup_subtab_computation_<subtab_key>_<param>

where ``<subtab_key>`` is one of
``portfolio_comparison`` / ``skfolio_optimization`` /
``optimalportfolios_optimization`` / ``simulation``
and ``<param>`` is one of
``computation_type`` / ``logger_display`` / ``execution_thread_mode`` /
``profiler``.

The server stores all selections in
``reactives_shiny["User_Inputs_Shiny"]`` via ``reactive.effect``.

Pure getter helpers
-------------------
:func:`get_computation_type_for_subtab` and
:func:`get_debug_options_for_subtab` allow other subtabs to retrieve
computation settings without importing Shiny internals.
"""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, reactive, ui

from src.dashboard.shiny_utils.reactives_shiny import (
    create_reactive_value_safely,
    safe_get_reactive_value,
)
from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
    create_enhanced_card_section,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    get_logger,
    set_console_level_for_subtab,
)


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Ordered sequence of (subtab_key, label, tab_name) for the table rows.
COMPUTATION_SUBTAB_ROWS: tuple[tuple[str, str, str], ...] = (
    ("portfolio_comparison", "Portfolio Comparison", "Portfolios"),
    ("skfolio_optimization", "skfolio Optimization", "Portfolios"),
    ("optimalportfolios_optimization", "OptimalPortfolios Optimization", "Portfolios"),
    ("simulation", "Simulation", "Results"),
)

#: Subtab rows that only appear in the Developer / Debug Options table
#: (no computation-type selector).  Each entry is (subtab_key, label, tab_name).
DEBUG_ONLY_SUBTAB_ROWS: tuple[tuple[str, str, str], ...] = (
    ("outline_clients", "Outline", "Clients"),
)

#: Available computation engines.
COMPUTATION_TYPE_CHOICES: dict[str, str] = {
    "asyncio": "asyncio",
    "standard": "standard",
    "asyncio + anyio": "asyncio + anyio",
    "trio": "trio",
    "trio + anyio": "trio + anyio",
    "joblib": "joblib",
}

DEFAULT_COMPUTATION_TYPE: str = "standard"

#: Logger display choices.
LOGGER_DISPLAY_CHOICES: dict[str, str] = {
    "no_display": "No Display",
    "info": "INFO",
    "debug": "DEBUG",
    "info_debug": "INFO + DEBUG",
}

DEFAULT_LOGGER_DISPLAY: str = "no_display"

#: Execution thread mode choices.
EXECUTION_THREAD_MODE_CHOICES: dict[str, str] = {
    "background": "Background Thread (asyncio.to_thread)",
    "synchronous": "Synchronous (Main Thread — for breakpoints)",
}

DEFAULT_EXECUTION_THREAD_MODE: str = "background"

#: Profiler choices.
PROFILER_CHOICES: dict[str, str] = {
    "none": "None",
    "line_profiler": "line_profiler",
    "scalene": "scalene",
}

DEFAULT_PROFILER: str = "none"

# ---------------------------------------------------------------------------
# Reactive-key helpers
# ---------------------------------------------------------------------------

_SUBTAB_KEY_TO_REACTIVE_STEM: dict[str, str] = {
    "portfolio_comparison": "Portfolio_Comparison",
    "skfolio_optimization": "Skfolio_Optimization",
    "optimalportfolios_optimization": "OptimalPortfolios_Optimization",
    "simulation": "Simulation",
    "outline_clients": "Outline_Clients",
}

#: Maps subtab key → dotted module-path prefix owned by that subtab.
#: Used by :func:`set_console_level_for_subtab` so the console filter
#: can gate DEBUG/INFO output per subtab module.
_SUBTAB_KEY_TO_MODULE_PREFIX: dict[str, str] = {
    "portfolio_comparison": ("src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"),
    "skfolio_optimization": ("src.dashboard.shiny_tab_portfolios.subtab_portfolios_skfolio"),
    "optimalportfolios_optimization": (
        "src.dashboard.shiny_tab_portfolios.subtab_portfolios_optimalportfolios"
    ),
    "simulation": "src.dashboard.shiny_tab_results.subtab_simulation",
    "outline_clients": "src.dashboard.shiny_tab_clients.subtab_outline",
}


def _reactive_key(*, subtab_key: str, param: str) -> str:
    """Return the ``User_Inputs_Shiny`` key for a given subtab/param pair.

    Parameters
    ----------
    subtab_key : str
        One of the keys in :data:`_SUBTAB_KEY_TO_REACTIVE_STEM`.
    param : str
        One of ``Computation_Type``, ``Logger_Display``,
        ``Execution_Thread_Mode``, ``Profiler``.

    Returns
    -------
    str
        Fully qualified reactive key, e.g.
        ``"Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Computation_Type"``.
    """
    stem = _SUBTAB_KEY_TO_REACTIVE_STEM.get(subtab_key, "")
    return f"Input_Tab_Setup_Subtab_Computation_{stem}_{param}"


# ---------------------------------------------------------------------------
# Pure getter helpers (usable without a live Shiny session)
# ---------------------------------------------------------------------------


def get_computation_type_for_subtab(
    *, reactives_shiny: dict[str, Any], subtab_key: str) -> str:
    """Return the currently selected computation type for *subtab_key*.

    Parameters
    ----------
    reactives_shiny : dict
        Shared reactive state dictionary.
    subtab_key : str
        Row key, e.g. ``"portfolio_comparison"``.

    Returns
    -------
    str
        Selected computation type string, or :data:`DEFAULT_COMPUTATION_TYPE`
        if the value is missing or unreadable.
    """
    if not isinstance(reactives_shiny, dict):
        return DEFAULT_COMPUTATION_TYPE
    user_inputs = reactives_shiny.get("User_Inputs_Shiny", {})
    if not isinstance(user_inputs, dict):
        return DEFAULT_COMPUTATION_TYPE
    reactive_key = _reactive_key(subtab_key = subtab_key, param = "Computation_Type")
    return safe_get_reactive_value(reactive_input = user_inputs.get(reactive_key), default_value = DEFAULT_COMPUTATION_TYPE)


def get_debug_options_for_subtab(
    *, reactives_shiny: dict[str, Any], subtab_key: str) -> dict[str, str]:
    """Return the currently selected developer/debug options for *subtab_key*.

    Parameters
    ----------
    reactives_shiny : dict
        Shared reactive state dictionary.
    subtab_key : str
        Row key, e.g. ``"portfolio_comparison"``.

    Returns
    -------
    dict
        Dictionary with keys ``"logger_display"``, ``"execution_thread_mode"``,
        and ``"profiler"``.  Each value falls back to its default when missing.
    """
    if not isinstance(reactives_shiny, dict):
        return {
            "logger_display": DEFAULT_LOGGER_DISPLAY,
            "execution_thread_mode": DEFAULT_EXECUTION_THREAD_MODE,
            "profiler": DEFAULT_PROFILER,
        }
    user_inputs = reactives_shiny.get("User_Inputs_Shiny", {})
    if not isinstance(user_inputs, dict):
        user_inputs = {}

    return {
        "logger_display": safe_get_reactive_value(
            reactive_input = user_inputs.get(_reactive_key(subtab_key = subtab_key, param = "Logger_Display")),
            default_value = DEFAULT_LOGGER_DISPLAY,
        ),
        "execution_thread_mode": safe_get_reactive_value(
            reactive_input = user_inputs.get(_reactive_key(subtab_key = subtab_key, param = "Execution_Thread_Mode")),
            default_value = DEFAULT_EXECUTION_THREAD_MODE,
        ),
        "profiler": safe_get_reactive_value(
            reactive_input = user_inputs.get(_reactive_key(subtab_key = subtab_key, param = "Profiler")),
            default_value = DEFAULT_PROFILER,
        ),
    }


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

_TABLE_CELL_STYLE = "padding: 6px 10px; vertical-align: middle;"
_TABLE_HEADER_STYLE = (
    "padding: 6px 10px; text-align: left; background-color: #E8EDF1; font-weight: 600;"
)


def _build_computation_type_table() -> Any:
    """Build the Computation Type HTML table with one dropdown per row."""
    header_row = ui.tags.tr(
        ui.tags.th("Subtab", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Tab", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Computation Type", style=_TABLE_HEADER_STYLE),
    )
    data_rows = []
    for subtab_key, subtab_label, tab_label in COMPUTATION_SUBTAB_ROWS:
        input_id = f"input_ID_tab_setup_subtab_computation_{subtab_key}_computation_type"
        data_rows.append(
            ui.tags.tr(
                ui.tags.td(subtab_label, style=_TABLE_CELL_STYLE),
                ui.tags.td(tab_label, style=_TABLE_CELL_STYLE),
                ui.tags.td(
                    ui.input_select(
                        input_id,
                        label=None,
                        choices=COMPUTATION_TYPE_CHOICES,
                        selected=DEFAULT_COMPUTATION_TYPE,
                    ),
                    style=_TABLE_CELL_STYLE,
                ),
            ),
        )
    return ui.tags.table(
        ui.tags.thead(header_row),
        ui.tags.tbody(*data_rows),
        style="width: 100%; border-collapse: collapse;",
        class_="table table-bordered table-sm",
    )


def _build_developer_debug_table() -> Any:
    """Build the Developer / Debug Options HTML table inside a <details> block."""
    header_row = ui.tags.tr(
        ui.tags.th("Subtab", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Tab", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Logger Display", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Execution Thread Mode", style=_TABLE_HEADER_STYLE),
        ui.tags.th("Profiler", style=_TABLE_HEADER_STYLE),
    )
    data_rows = []
    all_debug_rows = list(COMPUTATION_SUBTAB_ROWS) + list(DEBUG_ONLY_SUBTAB_ROWS)
    for subtab_key, subtab_label, tab_label in all_debug_rows:
        id_logger = f"input_ID_tab_setup_subtab_computation_{subtab_key}_logger_display"
        id_thread = f"input_ID_tab_setup_subtab_computation_{subtab_key}_execution_thread_mode"
        id_profiler = f"input_ID_tab_setup_subtab_computation_{subtab_key}_profiler"
        data_rows.append(
            ui.tags.tr(
                ui.tags.td(subtab_label, style=_TABLE_CELL_STYLE),
                ui.tags.td(tab_label, style=_TABLE_CELL_STYLE),
                ui.tags.td(
                    ui.input_select(
                        id_logger,
                        label=None,
                        choices=LOGGER_DISPLAY_CHOICES,
                        selected=DEFAULT_LOGGER_DISPLAY,
                    ),
                    style=_TABLE_CELL_STYLE,
                ),
                ui.tags.td(
                    ui.input_radio_buttons(
                        id_thread,
                        label=None,
                        choices=EXECUTION_THREAD_MODE_CHOICES,
                        selected=DEFAULT_EXECUTION_THREAD_MODE,
                    ),
                    style=_TABLE_CELL_STYLE,
                ),
                ui.tags.td(
                    ui.input_select(
                        id_profiler,
                        label=None,
                        choices=PROFILER_CHOICES,
                        selected=DEFAULT_PROFILER,
                    ),
                    style=_TABLE_CELL_STYLE,
                ),
            ),
        )
    table = ui.tags.table(
        ui.tags.thead(header_row),
        ui.tags.tbody(*data_rows),
        style="width: 100%; border-collapse: collapse;",
        class_="table table-bordered table-sm",
    )
    return ui.tags.details(
        ui.tags.summary(
            ui.tags.i(class_="fas fa-bug me-2"),
            "Developer / Debug Options",
            style="cursor: pointer; font-weight: 600; font-size: 0.95em; color: #6c757d;",
        ),
        ui.div(
            table,
            ui.tags.small(
                ui.tags.i(class_="fas fa-exclamation-triangle me-1"),
                "Synchronous mode blocks the UI until computation completes. "
                "Use only for debugging with VS Code breakpoints.",
                class_="text-warning d-block mt-2",
            ),
            class_="p-3 border rounded mt-2",
            style="background: #fefefe; border-color: #dee2e6 !important;",
        ),
    )


# ---------------------------------------------------------------------------
# Shiny module
# ---------------------------------------------------------------------------


@module.ui
def subtab_computation_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:
    """Create the Computation settings subtab UI.

    Parameters
    ----------
    data_utils : dict
        Shared dashboard utility functions.
    data_inputs : dict
        Default input values and configuration.

    Returns
    -------
    ui.div
        Complete Computation subtab UI.

    Raises
    ------
    Exception_Configuration
        If the UI cannot be assembled.
    """
    try:
        computation_type_section = create_enhanced_card_section(
            title="Computation Type",
            content=[_build_computation_type_table()],
            icon_class="fas fa-cogs",
            card_class="border-secondary",
        )
        developer_debug_section = create_enhanced_card_section(
            title="Developer / Debug Options",
            content=[_build_developer_debug_table()],
            icon_class="fas fa-bug",
            card_class="border-warning",
        )
        return ui.div(
            ui.h3("Computation Settings", class_="text-center mb-4"),
            ui.row(ui.column(12, computation_type_section)),
            ui.row(ui.column(12, developer_debug_section)),
        )
    except (TypeError, ValueError, AttributeError, KeyError) as exc_error:
        error_message = f"Unexpected error creating computation subtab UI: {exc_error}"
        raise Exception_Configuration(error_message) from exc_error


@module.server
def subtab_computation_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Store computation and debug selections in ``reactives_shiny``.

    Parameters
    ----------
    input, output, session : typing.Any
        Shiny server objects.
    data_utils : dict
        Shared dashboard utility functions.
    data_inputs : dict
        Default input values and configuration.
    reactives_shiny : dict
        Shared reactive state dictionary.
    """
    if not isinstance(reactives_shiny, dict):
        _logger.error(
            "VALIDATION_ERROR: reactives_shiny is not a dict",
            extra={"event_type": "validation_error", "subtab": "computation"},
        )
        return

    _logger.info(
        "SERVER_INIT: Computation subtab server",
        extra={"event_type": "server_init", "subtab": "computation"},
    )

    user_inputs = reactives_shiny.get("User_Inputs_Shiny")
    if not isinstance(user_inputs, dict):
        _logger.error(
            "VALIDATION_ERROR: User_Inputs_Shiny is not a dict",
            extra={"event_type": "validation_error", "subtab": "computation"},
        )
        return

    # Ensure all reactive keys exist in user_inputs (computation rows get
    # Computation_Type; all rows get debug options).
    _default_values: dict[str, str] = {}
    for subtab_key, _, _ in COMPUTATION_SUBTAB_ROWS:
        _default_values[_reactive_key(subtab_key = subtab_key, param = "Computation_Type")] = DEFAULT_COMPUTATION_TYPE
    for subtab_key, _, _ in list(COMPUTATION_SUBTAB_ROWS) + list(DEBUG_ONLY_SUBTAB_ROWS):
        _default_values[_reactive_key(subtab_key = subtab_key, param = "Logger_Display")] = DEFAULT_LOGGER_DISPLAY
        _default_values[_reactive_key(subtab_key = subtab_key, param = "Execution_Thread_Mode")] = (
            DEFAULT_EXECUTION_THREAD_MODE
        )
        _default_values[_reactive_key(subtab_key = subtab_key, param = "Profiler")] = DEFAULT_PROFILER

    for reactive_key_name, default_value in _default_values.items():
        if reactive_key_name not in user_inputs or user_inputs[reactive_key_name] is None:
            user_inputs[reactive_key_name] = create_reactive_value_safely(initial_value = default_value)

    @reactive.effect
    def _observer_computation_type() -> None:
        """Sync computation type selections to reactives_shiny."""
        for subtab_key, _, _ in COMPUTATION_SUBTAB_ROWS:
            input_id = f"input_ID_tab_setup_subtab_computation_{subtab_key}_computation_type"
            try:
                raw_value = input[input_id]()
            except Exception:
                raw_value = None
            value = raw_value if raw_value in COMPUTATION_TYPE_CHOICES else DEFAULT_COMPUTATION_TYPE
            reactive_key_name = _reactive_key(subtab_key = subtab_key, param = "Computation_Type")
            rv = user_inputs.get(reactive_key_name)
            if rv is not None and hasattr(rv, "set"):
                rv.set(value)

    # ------------------------------------------------------------------
    # Poll-based debug options observer.
    #
    # The poll reads UI inputs and syncs them into User_Inputs_Shiny
    # reactives.  When a subtab's inputs are inaccessible (because the
    # user is on a different tab) the poll skips that row so the
    # reactive value retains its last-known setting.
    #
    # A separate effect then reads from User_Inputs_Shiny and calls
    # set_console_level_for_subtab, ensuring the console rule survives
    # tab switches.
    # ------------------------------------------------------------------

    _ALL_DEBUG_ROWS = list(COMPUTATION_SUBTAB_ROWS) + list(DEBUG_ONLY_SUBTAB_ROWS)

    def _poll_all_debug_inputs():
        """Return a snapshot of every accessible debug-option input value.

        Rows whose inputs cannot be read (e.g. because the Computation
        tab is hidden) are omitted from the snapshot so the downstream
        effect does not reset the persisted reactive value to its
        default.
        """
        snapshot: dict[str, dict[str, object]] = {}
        for subtab_key, _, _ in _ALL_DEBUG_ROWS:
            id_logger = f"input_ID_tab_setup_subtab_computation_{subtab_key}_logger_display"
            try:
                raw_logger = input[id_logger]()
            except Exception:
                continue  # input inaccessible — skip, keep last known reactive value

            snapshot[subtab_key] = {"logger": raw_logger}
        return snapshot

    @reactive.poll(_poll_all_debug_inputs, interval_secs=0.5)
    def _poll_debug_snapshot():
        """Reactive calc that re-evaluates when any debug input changes."""
        return _poll_all_debug_inputs()

    @reactive.effect
    def _observer_sync_debug_to_reactives() -> None:
        """Sync debug-option inputs into User_Inputs_Shiny reactives."""
        polled = _poll_debug_snapshot()
        if not polled:
            return

        for subtab_key, values in polled.items():
            raw_logger = values.get("logger", DEFAULT_LOGGER_DISPLAY)
            logger_value = (
                raw_logger if raw_logger in LOGGER_DISPLAY_CHOICES else DEFAULT_LOGGER_DISPLAY
            )
            reactive_key_name = _reactive_key(subtab_key = subtab_key, param = "Logger_Display")
            rv = user_inputs.get(reactive_key_name)
            if rv is not None and hasattr(rv, "set"):
                rv.set(logger_value)

    # ------------------------------------------------------------------
    # Console-level propagation — reads from User_Inputs_Shiny (which
    # survives tab switches) rather than from input[id]() (which fails
    # when the Computation tab is hidden).
    # ------------------------------------------------------------------

    # Per-subtab cached last-known logger value so we only call
    # set_console_level_for_subtab when the value actually changes.
    _last_console_levels: dict[str, str] = {}

    @reactive.effect
    def _observer_propagate_console_levels() -> None:
        """Propagate Logger_Display changes to the console filter.

        Reads from the persisted User_Inputs_Shiny reactives so that
        the console rule is maintained even when the Computation tab
        is hidden and its input widgets are inaccessible.
        """
        for subtab_key, _, _ in _ALL_DEBUG_ROWS:
            reactive_key_name = _reactive_key(subtab_key = subtab_key, param = "Logger_Display")
            rv = user_inputs.get(reactive_key_name)
            if rv is None:
                continue
            try:
                current_level = rv.get()
            except Exception:
                current_level = DEFAULT_LOGGER_DISPLAY
            if not isinstance(current_level, str) or current_level not in LOGGER_DISPLAY_CHOICES:
                current_level = DEFAULT_LOGGER_DISPLAY

            # Only call set_console_level_for_subtab when the value
            # actually changes — avoids redundant calls from reactive
            # invalidations.
            previous = _last_console_levels.get(subtab_key, "")
            if current_level != previous:
                _last_console_levels[subtab_key] = current_level
                module_prefix = _SUBTAB_KEY_TO_MODULE_PREFIX.get(subtab_key, "")
                _logger.warning(
                    "_observer_propagate_console_levels: subtab=%s level=%s",
                    subtab_key,
                    current_level,
                    extra={"event_type": "debug_options_sync"},
                )
                if module_prefix:
                    set_console_level_for_subtab(
                        _subtab_key = subtab_key,
                        module_prefix = module_prefix,
                        level_key = current_level,
                    )
