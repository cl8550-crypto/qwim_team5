"""Monte Carlo Simulation Subtab for QWIM Dashboard.

Provides an interactive UI for running Monte Carlo simulations on a
QWIM portfolio.  The user selects ETF components, configures scenario
parameters (distribution type, number of paths, horizon, RNG seed),
and launches the simulation.  Results are presented as a fan-chart
of portfolio value paths with confidence bands plus a summary
statistics table.

Author
------
QWIM Team

Version
-------
0.6.0 (2026-03-01)
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import threading

from datetime import datetime
from typing import TYPE_CHECKING, Any

import plotly.graph_objects as go

from shiny import module, reactive, render, ui
from shiny.types import SilentException
from shinywidgets import output_widget, render_widget

from src.dashboard.shiny_tab_results._subtab_simulation_rendering import (
    build_compare_progress_ui_for_simulation,
    build_compare_table_ui_for_simulation,
    build_fan_chart_figure_for_simulation,
    build_histogram_figure_for_simulation,
    build_simulation_run_config_for_subtab,
    build_stats_table_ui_for_simulation,
    resolve_available_etf_components_for_simulation,
    resolve_selected_etf_components_for_simulation,
)
from src.dashboard.shiny_tab_results._subtab_simulation_shared import (
    _SIM_COMPARE_PROGRESS_CSS,
    ALL_ETF_SYMBOLS,
    DEFAULT_SELECTED_ETFS,
    DISTRIBUTION_CHOICES,
    NUM_DEFAULT_SELECTED,
    RNG_TYPE_CHOICES,
    _compare_entry_is_successful,
    _create_rng,
    _map_distribution_key,
    _parse_start_date_value,
    _read_compute_and_compare_toggle_enabled,
    _read_simulation_run_parameters,
    _resolve_compare_canonical_results,
    _resolve_compare_progress_running_display,
    _resolve_compare_progress_running_pill,
    _summarize_compare_completion,
    format_compare_table_as_html,
)
from src.dashboard.shiny_tab_setup.subtab_computation import (
    get_computation_type_for_subtab,
)
from src.models.simulation.model_simulation_standard import (
    DEFAULT_INITIAL_VALUE,
    DEFAULT_NUM_DAYS,
    DEFAULT_NUM_SCENARIOS,
    DEFAULT_RANDOM_SEED,
)
from src.models.simulation.simulation_dispatch import (
    COMPUTATION_TYPES_SIMULATION_COMPARE,
    compute_compare_results,
    compute_simulation_stats,
    dispatch_simulation_run,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


if TYPE_CHECKING:
    import polars as pl

    from src.models.simulation.simulation_dispatch import Simulation_Run_Config


_logger = get_logger(name = __name__)

__all__ = [
    "ALL_ETF_SYMBOLS",
    "DEFAULT_SELECTED_ETFS",
    "DISTRIBUTION_CHOICES",
    "NUM_DEFAULT_SELECTED",
    "RNG_TYPE_CHOICES",
    "_SIM_COMPARE_PROGRESS_CSS",
    "_compare_entry_is_successful",
    "_coerce_compare_elapsed_or_default",
    "_create_rng",
    "_map_distribution_key",
    "_parse_start_date_value",
    "_read_compute_and_compare_toggle_enabled",
    "_read_simulation_run_parameters",
    "_resolve_compare_canonical_results",
    "_resolve_compare_progress_running_display",
    "_resolve_compare_progress_running_pill",
    "_summarize_compare_completion",
    "format_compare_table_as_html",
    "subtab_simulation_server",
    "subtab_simulation_ui",
]


# ======================================================================
# Helper — empty Plotly figure
# ======================================================================


def _coerce_compare_elapsed_or_default(
    *, raw_value: Any, default_value: float = 0.0) -> float:
    """Convert compare elapsed metadata to ``float`` while rejecting booleans."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default_value


def _create_empty_figure(*, title: str, message: str) -> go.Figure:
    """Return a Plotly figure with a centred annotation and no data."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 16, "color": "gray"},
    )
    fig.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        template="plotly_white",
        height=600,
    )
    return fig


# ======================================================================
# UI
# ======================================================================


@module.ui
def subtab_simulation_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> ui.Tag:
    """Create the Simulation subtab UI.

    Parameters
    ----------
    data_utils : dict[str, Any]
        Dashboard utility functions.
    data_inputs : dict[str, Any]
        Dashboard input data.

    Returns
    -------
    ui.Tag
        Shiny UI layout for the simulation subtab.
    """
    return ui.div(
        ui.h3("Monte Carlo Simulation"),
        ui.layout_sidebar(
            ui.sidebar(
                # =============================================================
                # RUN BUTTON — placed above config for immediate access
                # =============================================================
                ui.input_action_button(
                    "input_ID_tab_results_subtab_simulation_run_btn",
                    "Run Simulation",
                    class_="btn-primary w-100 mb-3",
                ),
                ui.output_text(
                    "output_ID_tab_results_subtab_simulation_status",
                ),
                ui.hr(),
                # =============================================================
                # ETF COMPONENT SELECTION
                # =============================================================
                ui.h5("Select Components", class_="mb-3"),
                ui.div(
                    ui.input_checkbox(
                        "input_ID_tab_results_subtab_simulation_select_all_components",
                        "Select All ETFs",
                        value=False,
                    ),
                    class_="mb-2",
                ),
                ui.div(
                    ui.output_ui(
                        "output_ID_tab_results_subtab_simulation_component_checkboxes",
                    ),
                    style=(
                        "max-height: 200px; overflow-y: auto; "
                        "border: 1px solid #dee2e6; border-radius: 0.375rem; "
                        "padding: 0.5rem;"
                    ),
                ),
                ui.div(
                    ui.output_text(
                        "output_ID_tab_results_subtab_simulation_selected_components_count",
                    ),
                    class_="mt-1 text-muted small",
                ),
                ui.hr(),
                # =============================================================
                # SIMULATION PARAMETERS
                # =============================================================
                ui.h5("Simulation Parameters", class_="mb-3"),
                ui.input_numeric(
                    "input_ID_tab_results_subtab_simulation_num_scenarios",
                    "Number of Scenarios",
                    value=DEFAULT_NUM_SCENARIOS,
                    min=10,
                    max=100_000,
                    step=100,
                ),
                ui.input_numeric(
                    "input_ID_tab_results_subtab_simulation_num_days",
                    "Simulation Horizon (Trading Days)",
                    value=DEFAULT_NUM_DAYS,
                    min=5,
                    max=2520,
                    step=1,
                ),
                ui.input_date(
                    "input_ID_tab_results_subtab_simulation_start_date",
                    "Simulation Start Date",
                    value=datetime.now(dt.UTC).date().isoformat(),
                ),
                ui.input_numeric(
                    "input_ID_tab_results_subtab_simulation_initial_value",
                    "Initial Portfolio Value ($)",
                    value=DEFAULT_INITIAL_VALUE,
                    min=1.0,
                    max=1_000_000_000.0,
                    step=100.0,
                ),
                ui.hr(),
                # =============================================================
                # DISTRIBUTION & RNG
                # =============================================================
                ui.h5("Distribution & RNG", class_="mb-3"),
                ui.input_select(
                    "input_ID_tab_results_subtab_simulation_distribution_type",
                    "Distribution Type",
                    choices=DISTRIBUTION_CHOICES,
                    selected="normal",
                ),
                ui.panel_conditional(
                    "input.input_ID_tab_results_subtab_simulation_distribution_type === 'student_t'",
                    ui.input_numeric(
                        "input_ID_tab_results_subtab_simulation_degrees_of_freedom",
                        "Degrees of Freedom (v > 2)",
                        value=5.0,
                        min=2.1,
                        max=100.0,
                        step=0.5,
                    ),
                ),
                ui.input_select(
                    "input_ID_tab_results_subtab_simulation_rng_type",
                    "Random Number Generator",
                    choices=RNG_TYPE_CHOICES,
                    selected="pcg64",
                ),
                ui.input_numeric(
                    "input_ID_tab_results_subtab_simulation_seed",
                    "RNG Seed",
                    value=DEFAULT_RANDOM_SEED,
                    min=0,
                    max=2**31 - 1,
                    step=1,
                ),
                ui.hr(),
                width=350,
                position="left",
            ),
            # =================================================================
            # MAIN CONTENT
            # =================================================================
            ui.div(
                ui.card(
                    ui.card_header("Portfolio Value Fan Chart"),
                    output_widget(
                        "output_ID_tab_results_subtab_simulation_fan_chart",
                        height="600px",
                        width="100%",
                    ),
                    full_screen=True,
                    class_="mb-4",
                ),
                ui.div(
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Terminal Value Distribution"),
                            output_widget(
                                "output_ID_tab_results_subtab_simulation_histogram",
                                height="400px",
                                width="100%",
                            ),
                            class_="h-100",
                        ),
                        ui.card(
                            ui.card_header("Summary Statistics"),
                            ui.output_ui(
                                "output_ID_tab_results_subtab_simulation_stats_table",
                            ),
                            class_="h-100",
                        ),
                        col_widths=[6, 6],
                    ),
                    class_="mt-3",
                ),
                # Compute-and-Compare section
                ui.div(
                    ui.tags.style(_SIM_COMPARE_PROGRESS_CSS),
                    ui.hr(),
                    ui.h5("Backend Comparison", class_="mb-2"),
                    ui.input_switch(
                        "input_ID_tab_results_subtab_simulation_compute_and_compare",
                        "Compute and Compare all backends",
                        value=False,
                    ),
                    ui.div(
                        ui.p(
                            "Runs all 6 computation backends with identical parameters "
                            "and displays a side-by-side comparison table. "
                            "Results are bit-identical; elapsed-time rows show backend speed.",
                            class_="text-muted small",
                        ),
                    ),
                    ui.input_action_button(
                        "input_ID_tab_results_subtab_simulation_run_compare_btn",
                        "Run Compute & Compare",
                        class_="btn-info w-100 mt-2 mb-2",
                    ),
                    ui.output_ui(
                        "output_ID_tab_results_subtab_simulation_compare_progress",
                    ),
                    ui.output_ui(
                        "output_ID_tab_results_subtab_simulation_compare_table",
                    ),
                    class_="mt-3",
                ),
                class_="flex-fill",
            ),
        ),
    )


# ======================================================================
# Server
# ======================================================================


@module.server
def subtab_simulation_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Server logic for the Simulation subtab.

    Parameters
    ----------
    input : Any
        Shiny input object.
    output : Any
        Shiny output object.
    session : Any
        Shiny session object.
    data_utils : dict[str, Any]
        Utility functions.
    data_inputs : dict[str, Any]
        Dashboard input data (must contain ``'ETF_Prices'``
        :class:`pl.DataFrame`).
    reactives_shiny : dict[str, Any]
        Shared reactive state dictionary with standard 4 categories.
    """
    _logger.info("Initializing Simulation subtab server")

    # ----- reactive values -----
    simulation_results: reactive.Value[pl.DataFrame | None] = reactive.Value(None)
    simulation_stats: reactive.Value[pl.DataFrame | None] = reactive.Value(None)
    compare_results: reactive.Value[dict | None] = reactive.Value(None)
    # Flag to auto-run simulation once on startup (True = run, False = already ran)
    _startup_run: reactive.Value[bool] = reactive.Value(value=True)
    # Backend label shown in status
    _last_backend: reactive.Value[str] = reactive.Value("standard")
    _last_elapsed: reactive.Value[float] = reactive.Value(0.0)
    _status_text: reactive.Value[str] = reactive.Value(
        "Status: Ready — click Run to start simulation",
    )

    # Thread-safe progress tracker for Compare mode
    _compare_progress: dict[str, Any] = {
        "status": "idle",
        "current_index": 0,
        "current_type": "",
        "total_types": len(COMPUTATION_TYPES_SIMULATION_COMPARE),
        "completed": [],
    }
    _compare_lock: threading.Lock = threading.Lock()

    def _set_compare_progress_idle() -> None:  # pragma: no cover
        """Reset compare progress to idle."""
        with _compare_lock:
            _compare_progress["status"] = "idle"
            _compare_progress["current_index"] = 0
            _compare_progress["current_type"] = ""
            _compare_progress["completed"] = []

    def _set_compare_progress_running() -> None:  # pragma: no cover
        """Mark compare execution as running."""
        with _compare_lock:
            _compare_progress["status"] = "running"
            _compare_progress["current_index"] = 0
            _compare_progress["current_type"] = ""
            _compare_progress["completed"] = []

    def _set_compare_progress_done(
        *, compare_payload: dict[str, dict[str, Any]]) -> None:  # pragma: no cover
        """Store completed compare progress entries for the UI."""
        completed_entries: list[dict[str, Any]] = []
        for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE:
            entry = compare_payload.get(computation_type, {})
            completed_entries.append(
                {
                    "type": computation_type,
                    "elapsed": _coerce_compare_elapsed_or_default(raw_value = entry.get("elapsed")),
                    "ok": entry.get("status") == "success",
                },
            )

        with _compare_lock:
            _compare_progress["status"] = "done"
            _compare_progress["current_index"] = len(COMPUTATION_TYPES_SIMULATION_COMPARE)
            _compare_progress["current_type"] = ""
            _compare_progress["completed"] = completed_entries

    def _set_compare_progress_failed() -> None:  # pragma: no cover
        """Mark compare execution as failed before producing compare results."""
        with _compare_lock:
            _compare_progress["status"] = "failed"
            _compare_progress["current_type"] = ""

    def _on_compare_step(
        idx: int, ctype: str) -> None:  # pragma: no cover
        """Update compare progress when a backend starts.

        Notes
        -----
        ``compute_compare_results`` invokes its ``progress_callback`` as
        ``progress_callback(idx, computation_type)`` (positional). The
        callback therefore must accept positional arguments.
        """
        with _compare_lock:
            _compare_progress["current_index"] = idx
            _compare_progress["current_type"] = ctype

    @reactive.extended_task
    async def _task_run_compare(  # pragma: no cover
        *, config: Simulation_Run_Config) -> dict[str, dict[str, Any]]:
        """Run Compute-and-Compare in a background thread.

        Notes
        -----
        ``compute_compare_results`` declares its parameters as keyword-only
        (the ``*`` marker in its signature). Both arguments must therefore be
        passed by name; a positional call raises ``TypeError`` at runtime.
        """
        return await asyncio.to_thread(
            compute_compare_results,
            config=config,
            progress_callback=_on_compare_step,
        )

    @reactive.calc
    def get_available_etf_components() -> list[str]:  # pragma: no cover
        """Get ETF symbols available in the price data."""
        return resolve_available_etf_components_for_simulation(data_inputs = data_inputs, module_file_path = __file__)

    @reactive.calc
    def get_selected_etf_components() -> list[str]:  # pragma: no cover
        """Get currently selected ETF components from checkboxes."""
        return resolve_selected_etf_components_for_simulation(
            input_obj = input,
            available_components = get_available_etf_components(),
            num_default_selected = NUM_DEFAULT_SELECTED,
        )

    # ------------------------------------------------------------------
    # Render component checkboxes (dynamic)
    # ------------------------------------------------------------------

    @output
    @render.ui
    def output_ID_tab_results_subtab_simulation_component_checkboxes() -> (
        ui.Tag
    ):  # pragma: no cover
        """Render ETF component checkboxes."""
        available = get_available_etf_components()
        if not available:
            return ui.div(
                ui.p("No ETF components available", class_="text-muted"),
                class_="p-2",
            )

        try:
            select_all = bool(
                input.input_ID_tab_results_subtab_simulation_select_all_components(),
            )
        except Exception:
            select_all = False
        effective_count = len(available) if select_all else NUM_DEFAULT_SELECTED

        boxes: list[ui.Tag] = []
        for idx, comp in enumerate(available):
            cid = f"input_ID_tab_results_subtab_simulation_component_{comp}"
            default_checked = idx < effective_count
            boxes.append(
                ui.div(
                    ui.input_checkbox(cid, comp, value=default_checked),
                    class_="mb-1",
                ),
            )
        return ui.div(*boxes)

    @output
    @render.text
    def output_ID_tab_results_subtab_simulation_selected_components_count() -> (
        str
    ):  # pragma: no cover
        """Show selected / total count."""
        available = get_available_etf_components()
        selected = get_selected_etf_components()
        return f"Selected: {len(selected)} of {len(available)} components"

    # ------------------------------------------------------------------
    # Simulation execution
    # ------------------------------------------------------------------

    def _execute_simulation() -> None:  # pragma: no cover
        """Run Monte Carlo simulation and store results."""
        selected_components = get_selected_etf_components()
        if not selected_components:
            simulation_results.set(None)
            simulation_stats.set(None)
            _status_text.set("Status: No ETF components selected")
            return

        params_simulation_run = _read_simulation_run_parameters(input_obj = input)

        # Read computation type from Setup tab via helper
        computation_type = get_computation_type_for_subtab(reactives_shiny = reactives_shiny, subtab_key = "simulation")

        # Read Compute-and-Compare toggle
        do_compare = _read_compute_and_compare_toggle_enabled(input_obj = input)

        try:
            config = build_simulation_run_config_for_subtab(
                selected_components=list(selected_components),
                data_inputs=data_inputs,
                degrees_of_freedom=params_simulation_run["degrees_of_freedom"],
                distribution_type=params_simulation_run["distribution_type"],
                initial_value=params_simulation_run["initial_value"],
                module_file_path=__file__,
                num_days=params_simulation_run["num_days"],
                num_scenarios=params_simulation_run["num_scenarios"],
                rng_type=params_simulation_run["rng_type"],
                seed=params_simulation_run["random_seed"],
                start_date=params_simulation_run["start_date"],
            )

            if do_compare:
                if _task_run_compare.status() == "running":
                    _status_text.set(
                        "Status: Compute and Compare is already running",
                    )
                    return

                _set_compare_progress_running()
                compare_results.set(None)
                _status_text.set(
                    "Status: Compute and Compare running — benchmarking all backends",
                )
                _task_run_compare(config = config)
                return

            results_df, elapsed = dispatch_simulation_run(computation_type = computation_type, config = config)
            stats_df = compute_simulation_stats(results_df = results_df)
            backend_label = computation_type
            compare_results.set(None)
            _set_compare_progress_idle()

            simulation_results.set(results_df)
            simulation_stats.set(stats_df)
            _last_backend.set(backend_label)
            _last_elapsed.set(elapsed)
            _status_text.set(
                f"Status: Completed via {backend_label} in {elapsed:.2f}s "
                f"— {params_simulation_run['num_scenarios']} scenarios, "
                f"{params_simulation_run['num_days']} time steps",
            )

            # Store in reactives for other tabs
            if "Inner_Variables_Shiny" in reactives_shiny:
                reactives_shiny["Inner_Variables_Shiny"]["Simulation_Results"] = reactive.Value(
                    results_df,
                )
                reactives_shiny["Inner_Variables_Shiny"]["Simulation_Stats"] = reactive.Value(
                    stats_df,
                )
                reactives_shiny["Inner_Variables_Shiny"]["Simulation_Last_Run_Meta"] = (
                    reactive.Value({"backend": backend_label, "elapsed": elapsed})
                )

            _logger.info(
                "SIMULATION_COMPLETE via dashboard: backend=%s elapsed=%.3fs %d scenarios x %d days",
                backend_label,
                elapsed,
                params_simulation_run["num_scenarios"],
                params_simulation_run["num_days"],
            )

        except Exception as exc:
            _logger.exception("Dashboard simulation failed: %s", exc)
            simulation_results.set(None)
            simulation_stats.set(None)
            _set_compare_progress_idle()
            _status_text.set(
                f"Status: Simulation failed — {type(exc).__name__}: {exc}",
            )

    @reactive.effect
    def _handle_compare_result() -> None:  # pragma: no cover  # noqa: RUF100
        """Store compare results once the background compare task completes.

        Notes
        -----
        This effect relies on Shiny's natural reactive cycle rather than
        manual ``invalidate_later`` timers.  ``ExtendedTask.status`` is a
        ``reactive.Value`` that is set inside Shiny's
        ``_extended_task._execution_wrapper`` (line 210) and followed by
        ``await flush()``; reading ``_task_run_compare.result()`` here
        establishes a reactive dependency on ``status`` and causes the
        effect to re-run exactly once per status transition
        (``"initial"`` → ``"running"`` → ``"success"``/``"error"``/
        ``"cancelled"``).  No manual timer is needed, and using one
        creates a cancellation storm with overlapping flushes that can
        interrupt this effect mid-execution and leave the progress card
        stuck on the last backend (joblib) without ever reaching
        ``status == "done"``.
        """
        try:
            cmp_results = _task_run_compare.result()
        except SilentException:
            # Task is still running or has not been invoked yet; Shiny
            # will display a progress indicator.  The effect will re-run
            # automatically when the ExtendedTask's status transitions.
            return
        except Exception as exc_error:
            _logger.exception("Compute-and-Compare failed: %s", exc_error)
            compare_results.set(None)
            _set_compare_progress_failed()
            _status_text.set(
                f"Status: Compute and Compare failed — {type(exc_error).__name__}: {exc_error}",
            )
            return

        compare_results.set(cmp_results)
        _set_compare_progress_done(compare_payload = cmp_results)

        results_df, stats_df, elapsed, backend_label = _resolve_compare_canonical_results(
            compare_results = cmp_results,
        )
        simulation_results.set(results_df)
        simulation_stats.set(stats_df)
        _last_backend.set(backend_label)
        _last_elapsed.set(elapsed)

        num_success, num_failed = _summarize_compare_completion(compare_results = cmp_results)
        if num_failed == 0:
            _status_text.set(
                f"Status: Compute and Compare completed — {num_success} backends succeeded",
            )
        else:
            _status_text.set(
                f"Status: Compute and Compare completed with {num_failed} backend error(s)",
            )

        if "Inner_Variables_Shiny" in reactives_shiny:
            reactives_shiny["Inner_Variables_Shiny"]["Simulation_Compare_Results"] = reactive.Value(
                cmp_results,
            )
            reactives_shiny["Inner_Variables_Shiny"]["Simulation_Results"] = reactive.Value(
                results_df,
            )
            reactives_shiny["Inner_Variables_Shiny"]["Simulation_Stats"] = reactive.Value(
                stats_df,
            )
            reactives_shiny["Inner_Variables_Shiny"]["Simulation_Last_Run_Meta"] = reactive.Value(
                {"backend": backend_label, "elapsed": elapsed},
            )

    @reactive.effect
    def _auto_run_simulation() -> None:  # pragma: no cover
        """Auto-run simulation on session startup to pre-populate charts."""
        if not _startup_run.get():
            return
        _startup_run.set(False)
        _execute_simulation()

    @reactive.effect
    @reactive.event(input.input_ID_tab_results_subtab_simulation_run_btn)
    def _run_simulation() -> None:
        """Execute Monte Carlo simulation when the Run button is clicked."""  # pragma: no cover
        _execute_simulation()

    @reactive.effect
    @reactive.event(input.input_ID_tab_results_subtab_simulation_run_compare_btn)
    def _run_compare_btn() -> None:  # pragma: no cover
        """Launch Compute-and-Compare when the dedicated button is clicked.

        Enables the compare switch automatically so the progress card and
        results table become visible without the user having to toggle it
        manually.
        """
        with contextlib.suppress(Exception):
            ui.update_switch(
                "input_ID_tab_results_subtab_simulation_compute_and_compare",
                value=True,
            )

        if _task_run_compare.status() == "running":
            _status_text.set("Status: Compute and Compare is already running")
            return

        selected_components = get_selected_etf_components()
        if not selected_components:
            _status_text.set("Status: No ETF components selected")
            return

        params_simulation_run = _read_simulation_run_parameters(input_obj = input)

        try:
            config = build_simulation_run_config_for_subtab(
                selected_components=list(selected_components),
                data_inputs=data_inputs,
                degrees_of_freedom=params_simulation_run["degrees_of_freedom"],
                distribution_type=params_simulation_run["distribution_type"],
                initial_value=params_simulation_run["initial_value"],
                module_file_path=__file__,
                num_days=params_simulation_run["num_days"],
                num_scenarios=params_simulation_run["num_scenarios"],
                rng_type=params_simulation_run["rng_type"],
                seed=params_simulation_run["random_seed"],
                start_date=params_simulation_run["start_date"],
            )
            _set_compare_progress_running()
            compare_results.set(None)
            _status_text.set(
                "Status: Compute and Compare running \u2014 benchmarking all backends",
            )
            _task_run_compare(config = config)
        except Exception as exc:
            _logger.exception("Run Compare button failed: %s", exc)
            _set_compare_progress_failed()
            _status_text.set(
                f"Status: Compute and Compare launch failed \u2014 {type(exc).__name__}: {exc}",
            )

    @reactive.effect
    def _update_run_compare_btn_state() -> None:  # pragma: no cover
        """Disable the Run Compare button while a compare is running."""
        progress = _poll_compare_progress()
        is_running = progress.get("status") == "running"
        with contextlib.suppress(Exception):
            ui.update_action_button(
                "input_ID_tab_results_subtab_simulation_run_compare_btn",
                disabled=is_running,
                label="\u23f3 Running\u2026" if is_running else "Run Compute & Compare",
            )

    # ------------------------------------------------------------------
    # Status text
    # ------------------------------------------------------------------

    @output
    @render.text
    def output_ID_tab_results_subtab_simulation_status() -> str:  # pragma: no cover
        """Show simulation status."""
        return _status_text.get()

    # ------------------------------------------------------------------
    # Fan chart
    # ------------------------------------------------------------------

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]  # go.Figure satisfies Widget protocol at runtime
    def output_ID_tab_results_subtab_simulation_fan_chart() -> go.Figure:  # pragma: no cover
        """Render the portfolio value fan chart with confidence bands."""
        return build_fan_chart_figure_for_simulation(
            create_empty_figure=_create_empty_figure,
            reactives_shiny=reactives_shiny,
            results_df=simulation_results.get(),
            stats_df=simulation_stats.get(),
        )

    # ------------------------------------------------------------------
    # Terminal value histogram
    # ------------------------------------------------------------------

    @output
    @render_widget  # pyright: ignore[reportArgumentType]  # pyrefly: ignore[bad-specialization]  # go.Figure satisfies Widget protocol at runtime
    def output_ID_tab_results_subtab_simulation_histogram() -> go.Figure:  # pragma: no cover
        """Render histogram of terminal portfolio values."""
        return build_histogram_figure_for_simulation(
            create_empty_figure=_create_empty_figure,
            reactives_shiny=reactives_shiny,
            results_df=simulation_results.get(),
        )

    # ------------------------------------------------------------------
    # Summary statistics table
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Compute-and-Compare progress card
    # ------------------------------------------------------------------

    @reactive.poll(  # type: ignore[arg-type]
        lambda: (_compare_progress["status"], _compare_progress["current_index"]),
        0.5,
    )
    def _poll_compare_progress() -> dict:  # pragma: no cover
        """Poll compare progress every 0.5 s."""
        with _compare_lock:
            return dict(_compare_progress)

    @output
    @render.ui
    def output_ID_tab_results_subtab_simulation_compare_progress() -> (
        ui.TagChild
    ):  # pragma: no cover
        """Render the RGA-style compare progress card."""
        reactive.invalidate_later(0.4)
        return build_compare_progress_ui_for_simulation(
            do_compare_enabled=_read_compute_and_compare_toggle_enabled(input_obj = input),
            progress_state=_poll_compare_progress(),
        )

    # ------------------------------------------------------------------
    # Compute-and-Compare results table
    # ------------------------------------------------------------------

    @output
    @render.ui
    def output_ID_tab_results_subtab_simulation_compare_table() -> ui.TagChild:  # pragma: no cover
        """Render backend comparison summary table."""
        return build_compare_table_ui_for_simulation(
            compare_results_payload=compare_results.get(),
            do_compare_enabled=_read_compute_and_compare_toggle_enabled(input_obj = input),
            progress_state=_poll_compare_progress(),
        )

    # ------------------------------------------------------------------
    # Summary statistics table
    # ------------------------------------------------------------------

    @output
    @render.ui
    def output_ID_tab_results_subtab_simulation_stats_table() -> ui.TagChild:  # pragma: no cover
        """Render summary statistics as an HTML table."""
        return build_stats_table_ui_for_simulation(
            results_df=simulation_results.get(),
            stats_df=simulation_stats.get(),
        )
