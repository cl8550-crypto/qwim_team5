"""Shared helpers for the Simulation results subtab.

This private module contains the pure constants and helper functions used by
the public Simulation subtab facade. Keeping these helpers separate reduces
the size of the public module while preserving its import surface.
"""

from __future__ import annotations

import contextlib
import datetime as dt

from typing import Any

import numpy as np
import polars as pl

from shiny import ui

from src.models.simulation.model_simulation_standard import (
    DEFAULT_INITIAL_VALUE,
    DEFAULT_NUM_DAYS,
    DEFAULT_NUM_SCENARIOS,
    DEFAULT_RANDOM_SEED,
)
from src.models.simulation.simulation_dispatch import (
    COMPUTATION_TYPES_SIMULATION_COMPARE,
)
from src.num_methods.rng import create_rng_QWIM
from src.num_methods.scenarios.scenarios_distrib import Distribution_Type


_SIM_COMPARE_PROGRESS_CSS: str = """
/* ============================================================
   Simulation Compute-and-Compare - progress card & table styles
   ============================================================ */

/* --- Card states ----------------------------------------- */
.sim-compare-card {
    border: 2px solid rgba(23, 162, 184, 0.5);
    border-radius: 12px;
    padding: 20px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 50%, #f8f9fa 100%);
    animation: sim-pulse-border 2s ease-in-out infinite;
    margin-bottom: 1rem;
}
.sim-compare-card-done {
    border: 2px solid #28a745;
    border-radius: 12px;
    padding: 20px;
    background: linear-gradient(135deg, #f8fff9 0%, #eaf7ee 50%, #f8fff9 100%);
    margin-bottom: 1rem;
}
.sim-compare-card-failed {
    border: 2px solid #dc3545;
    border-radius: 12px;
    padding: 20px;
    background: linear-gradient(135deg, #fff8f8 0%, #f8e8e8 50%, #fff8f8 100%);
    margin-bottom: 1rem;
}
@keyframes sim-pulse-border {
    0%,100% { border-color: rgba(23,162,184,0.35); box-shadow: 0 0 8px rgba(23,162,184,0.12); }
    50%      { border-color: rgba(23,162,184,0.9);  box-shadow: 0 0 20px rgba(23,162,184,0.4); }
}

/* --- Shimmer animation ------------------------------------ */
@keyframes sim-compare-shimmer-anim {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* --- Overall progress bar --------------------------------- */
.sim-compare-progress-bar-wrap {
    position: relative;
    height: 28px;
    border-radius: 14px;
    background-color: #e9ecef;
    overflow: hidden;
    margin: 12px 0 16px 0;
}
.sim-compare-progress-bar-fill {
    height: 100%;
    border-radius: 14px;
    background: linear-gradient(90deg, #17a2b8 0%, #20c997 40%, #17a2b8 80%);
    background-size: 200% 100%;
    animation: sim-compare-shimmer-anim 1.5s linear infinite;
    transition: width 0.4s ease-in-out;
}
.sim-compare-progress-bar-fill-done {
    background: linear-gradient(90deg, #28a745 0%, #5cb85c 100%);
    background-size: 100% 100%;
    animation: none;
}
.sim-compare-progress-bar-text {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85em;
    color: #0c5460;
}

/* --- Per-backend pill rows -------------------------------- */
.sim-backend-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 2px;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    font-size: 0.88em;
}
.sim-backend-row:last-child { border-bottom: none; }
.sim-backend-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 0.82em;
    font-weight: 600;
    min-width: 72px;
    text-align: center;
}
.sim-pill-pending { background: #e9ecef; color: #6c757d; }
.sim-pill-running {
    background: linear-gradient(90deg, #17a2b8 0%, #20c997 50%, #17a2b8 100%);
    background-size: 200% 100%;
    animation: sim-compare-shimmer-anim 1.5s linear infinite;
    color: white;
}
.sim-pill-success { background: #d4edda; color: #155724; }
.sim-pill-error   { background: #f8d7da; color: #721c24; }

/* --- Compare results table -------------------------------- */
.sim-compare-results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82em;
    margin-top: 10px;
}
.sim-compare-results-table th {
    background: #0c5460;
    color: white;
    padding: 6px 10px;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 1;
    white-space: nowrap;
}
.sim-compare-results-table td {
    padding: 4px 8px;
    border-bottom: 1px solid #dee2e6;
    white-space: nowrap;
}
.sim-compare-results-table td:first-child  { text-align: left; }
.sim-compare-results-table td:not(:first-child) { text-align: right; }
.sim-compare-results-table tr:nth-child(even) { background: #f8f9fa; }
.sim-compare-results-table tr.sim-row-delta   { color: #6c757d; font-size: 0.9em; }
.sim-compare-results-table tr.sim-row-error   { background: #fff3f3 !important; font-weight: 600; }
.sim-compare-results-table tr.sim-row-status  { background: #f0f8ff; font-weight: 700; }
.sim-compare-results-table tr.sim-row-elapsed { background: #fafafa; font-style: italic; }
.sim-cell-ok     { color: #155724; font-weight: 600; }
.sim-cell-failed { color: #721c24; font-weight: 600; }
.sim-compare-table-scroll { max-height: 500px; overflow-y: auto; overflow-x: auto; }

/* --- Legacy shimmer (kept for backward compatibility) ----- */
.sim-compare-shimmer {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: sim-compare-shimmer-anim 1.5s infinite;
    border-radius: 0.25rem;
    height: 1rem;
    margin: 0.4rem 0;
}
.sim-compare-progress-label {
    font-size: 0.85rem;
    color: #6c757d;
    margin-bottom: 0.25rem;
}
"""


ALL_ETF_SYMBOLS: list[str] = [
    "IVV",
    "IJH",
    "IWM",
    "EFA",
    "EEM",
    "AGG",
    "SPTL",
    "HYG",
    "SPBO",
    "IYR",
    "DBC",
    "GLD",
]


DEFAULT_SELECTED_ETFS: list[str] = ["IVV", "IJH", "IWM"]


NUM_DEFAULT_SELECTED: int = 3


DISTRIBUTION_CHOICES: dict[str, str] = {
    "normal": "Normal (Gaussian)",
    "lognormal": "Lognormal",
    "student_t": "Student-t",
}


RNG_TYPE_CHOICES: dict[str, str] = {
    "pcg64": "PCG-64 (NumPy default)",
    "mt19937": "Mersenne Twister (MT19937)",
    "philox": "Philox 4x32",
    "sfc64": "SFC-64",
}


def _map_distribution_key(*, key: str) -> Distribution_Type:
    """Convert a UI dropdown key to a distribution enum member."""
    mapping: dict[str, Distribution_Type] = {
        "normal": Distribution_Type.NORMAL,
        "lognormal": Distribution_Type.LOGNORMAL,
        "student_t": Distribution_Type.STUDENT_T,
    }
    if key in mapping:
        return mapping[key]
    return Distribution_Type.NORMAL


def _create_rng(*, rng_type: str, seed: int) -> np.random.Generator:
    """Create a NumPy generator using the selected bit generator."""
    return create_rng_QWIM(
        rng_type = rng_type,
        seed = seed,
        supported_rng_types=RNG_TYPE_CHOICES.keys(),
        fallback_rng_type="pcg64",
    )


def _parse_start_date_value(*, raw_date: str | dt.date | Any) -> dt.date:
    """Normalize a start-date input to ``datetime.date``."""
    if isinstance(raw_date, str):
        return dt.date.fromisoformat(raw_date)
    if isinstance(raw_date, dt.date):
        return raw_date
    return dt.datetime.now(tz=dt.UTC).date()


def _read_compute_and_compare_toggle_enabled(*, input_obj: Any) -> bool:
    """Read the compare-toggle input safely."""
    with contextlib.suppress(Exception):
        return bool(
            input_obj.input_ID_tab_results_subtab_simulation_compute_and_compare(),
        )
    return False


def _read_simulation_run_parameters(*, input_obj: Any) -> dict[str, Any]:
    """Read and normalize Simulation subtab run parameters.

    Boolean numeric inputs are treated as invalid and fall back to the same
    defaults used for missing or unparsable UI values.
    """

    def _coerce_numeric_or_default(
        *, raw_value: Any, default_value: int | float, cast_type: type[int] | type[float]) -> int | float:
        if raw_value is None or isinstance(raw_value, bool):
            return default_value

        try:
            return cast_type(raw_value)
        except (TypeError, ValueError):
            return default_value

    num_scenarios = int(
        _coerce_numeric_or_default(
            raw_value = input_obj.input_ID_tab_results_subtab_simulation_num_scenarios(),
            default_value = DEFAULT_NUM_SCENARIOS,
            cast_type = int,
        ),
    )
    num_days = int(
        _coerce_numeric_or_default(
            raw_value = input_obj.input_ID_tab_results_subtab_simulation_num_days(),
            default_value = DEFAULT_NUM_DAYS,
            cast_type = int,
        ),
    )
    initial_value = float(
        _coerce_numeric_or_default(
            raw_value = input_obj.input_ID_tab_results_subtab_simulation_initial_value(),
            default_value = DEFAULT_INITIAL_VALUE,
            cast_type = float,
        ),
    )
    random_seed = int(
        _coerce_numeric_or_default(
            raw_value = input_obj.input_ID_tab_results_subtab_simulation_seed(),
            default_value = DEFAULT_RANDOM_SEED,
            cast_type = int,
        ),
    )
    distribution_key = str(
        input_obj.input_ID_tab_results_subtab_simulation_distribution_type() or "normal",
    )
    distribution_type = _map_distribution_key(key = distribution_key)
    rng_type = str(
        input_obj.input_ID_tab_results_subtab_simulation_rng_type() or "pcg64",
    )
    degrees_of_freedom = 5.0
    if distribution_key == "student_t":
        degrees_of_freedom = float(
            _coerce_numeric_or_default(
                raw_value = input_obj.input_ID_tab_results_subtab_simulation_degrees_of_freedom(),
                default_value = 5.0,
                cast_type = float,
            ),
        )

    raw_date = input_obj.input_ID_tab_results_subtab_simulation_start_date()
    start_date = _parse_start_date_value(raw_date = raw_date)

    return {
        "num_scenarios": num_scenarios,
        "num_days": num_days,
        "initial_value": initial_value,
        "random_seed": random_seed,
        "distribution_key": distribution_key,
        "distribution_type": distribution_type,
        "rng_type": rng_type,
        "degrees_of_freedom": degrees_of_freedom,
        "start_date": start_date,
    }


def _compare_entry_is_successful(
    *, compare_results: dict[str, dict[str, Any]] | None, computation_type: str) -> bool:
    """Return ``True`` when compare output for one backend is successful."""
    if not isinstance(compare_results, dict):
        return False

    entry = compare_results.get(computation_type)
    if not isinstance(entry, dict):
        return False

    return (
        entry.get("status") == "success"
        and isinstance(entry.get("results_df"), pl.DataFrame)
        and isinstance(entry.get("stats_df"), pl.DataFrame)
    )


def _resolve_compare_canonical_results(
    *, compare_results: dict[str, dict[str, Any]] | None) -> tuple[pl.DataFrame | None, pl.DataFrame | None, float, str]:
    """Return the canonical display payload for compare mode.

    Boolean elapsed values are treated as invalid compare metadata and fall
    back to ``0.0`` seconds.
    """
    if not _compare_entry_is_successful(compare_results = compare_results, computation_type = "standard"):
        return None, None, 0.0, "standard (compare mode - unavailable)"

    standard_entry = compare_results["standard"]
    results_df = standard_entry["results_df"]
    stats_df = standard_entry["stats_df"]
    elapsed_raw = standard_entry.get("elapsed", 0.0)
    assert isinstance(results_df, pl.DataFrame)
    assert isinstance(stats_df, pl.DataFrame)

    return (
        results_df,
        stats_df,
        0.0 if isinstance(elapsed_raw, bool) else float(elapsed_raw),
        "standard (compare mode)",
    )


def _summarize_compare_completion(
    *, compare_results: dict[str, dict[str, Any]] | None) -> tuple[int, int]:
    """Return the number of successful and failed compare backends."""
    if not isinstance(compare_results, dict):
        return 0, len(COMPUTATION_TYPES_SIMULATION_COMPARE)

    num_success = sum(
        1
        for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE
        if _compare_entry_is_successful(compare_results = compare_results, computation_type = computation_type)
    )
    return num_success, len(COMPUTATION_TYPES_SIMULATION_COMPARE) - num_success


def _resolve_compare_progress_running_display(
    *, current_index: int, total_types: int) -> tuple[int, int]:
    """Return the running backend number and completion percent."""
    if isinstance(current_index, bool) or isinstance(total_types, bool):
        return 0, 0

    if total_types <= 0:
        return 0, 0

    current_backend_number = min(total_types, max(1, current_index + 1))
    percent_complete = int(current_backend_number / total_types * 100)
    return current_backend_number, percent_complete


def _resolve_compare_progress_running_pill(
    *, idx_backend: int, current_index: int) -> tuple[str, str]:
    """Return the CSS class and label for a running compare pill."""
    if idx_backend < current_index:
        return "sim-pill-success", "Done"
    if idx_backend == current_index:
        return "sim-pill-running", "Running"
    return "sim-pill-pending", "Pending"


def format_compare_table_as_html(
    *, table_df: pl.DataFrame, css_class: str = "sim-compare-results-table") -> ui.HTML:
    """Convert a compare-summary frame to a styled HTML table."""
    backends = [
        column_name
        for column_name in [
            "standard",
            "asyncio",
            "asyncio + anyio",
            "trio",
            "trio + anyio",
            "joblib",
        ]
        if column_name in table_df.columns
    ]
    column_order = ["Metric", *backends]

    header_cells = "".join(f"<th>{column_name}</th>" for column_name in column_order)

    body_rows = ""
    for row_dict in table_df.iter_rows(named=True):
        metric = str(row_dict.get("Metric") or "")
        if metric == "Status":
            row_class = " class='sim-row-status'"
        elif metric == "Error":
            row_class = " class='sim-row-error'"
        elif metric == "Elapsed time (s)":
            row_class = " class='sim-row-elapsed'"
        elif "Δ" in metric:
            row_class = " class='sim-row-delta'"
        else:
            row_class = ""

        cells = f"<td>{metric}</td>"
        for backend in backends:
            cell_value = str(row_dict.get(backend) or "")
            if metric == "Status":
                if cell_value == "OK":
                    cells += f"<td class='sim-cell-ok'>{cell_value}</td>"
                else:
                    cells += f"<td class='sim-cell-failed'>{cell_value}</td>"
            else:
                cells += f"<td>{cell_value}</td>"

        body_rows += f"<tr{row_class}>{cells}</tr>"

    table_html = (
        '<div class="sim-compare-table-scroll">'
        f'<table class="{css_class}">'
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{body_rows}</tbody>"
        "</table></div>"
    )
    return ui.HTML(table_html)