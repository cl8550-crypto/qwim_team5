"""Static Plot Export Module for QWIM Report Generation — public façade.

Re-exports all public symbols from the three sub-modules:

* ``_report_plot_returns``    — return/value-over-time charts + shared infrastructure
* ``_report_plot_allocation`` — allocation/weight charts
* ``_report_plot_risk``       — risk/simulation charts

Also provides the aggregate helpers:

* :func:`ensure_all_svg_files_exist` — guarantee every SVG the Typst template
  needs is on disk (creates placeholders where data was unavailable).
* :func:`export_all_report_plots` — call every ``export_plot_*`` function in
  one shot and return a ``{name: Path|None}`` mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._report_plot_allocation import (
    build_plotnine_optimalportfolios_performance_comparison,
    build_plotnine_optimalportfolios_weights_comparison,
    build_plotnine_skfolio_performance_comparison,
    build_plotnine_skfolio_weights_comparison,
    build_plotnine_weights_analysis_current_composition,
    build_plotnine_weights_analysis_distribution_over_time,
    export_plot_skfolio_performance,
    export_plot_skfolio_weights,
    export_plot_weights_analysis,
    export_plot_weights_pie,
)
from ._report_plot_returns import (
    _EXPECTED_SVG_FILES,
    _IMAGES_DIR,
    _PALETTE,
    _QWIM_THEME,
    _create_placeholder_svg,
    _ensure_dir,
    _get_inner_variables,
    _get_visual_objects,
    _load_sample_csv_for_plots,
    _parse_dates_as_naive,
    _safe_float,
    _safe_reactive_get,
    _save_plot,
    build_plotnine_portfolio_analysis_returns_distribution,
    build_plotnine_portfolio_comparison_portfolio_vs_benchmark,
    ensure_all_svg_files_exist,
    export_plot_portfolio_analysis,
    export_plot_portfolio_comparison,
)
from ._report_plot_risk import (
    _build_simulation_fan_data,
    build_plotnine_simulation_fan_chart,
    build_plotnine_simulation_terminal_value_distribution,
    export_plot_simulation_fan_chart,
    export_plot_simulation_histogram,
)
from ._report_plot_goal_parity import (
    build_plotnine_goal_parity_goal_powers,
    build_plotnine_goal_parity_weights,
    export_plot_goal_parity_goal_powers,
    export_plot_goal_parity_weights,
)

_logger = get_logger(name = __name__)


# =========================================================================
# AGGREGATE EXPORT
# =========================================================================


def export_all_report_plots(
    *, reactives_shiny: dict | None) -> dict[str, Path | None]:
    """Generate every SVG image required by the Typst report template.

    Parameters
    ----------
    reactives_shiny : dict | None
        Shared reactive state dictionary.

    Returns
    -------
    dict[str, Path | None]
        Mapping of descriptive name to path (``None`` where data is missing).
    """
    _logger.info("Exporting all report plots to SVG")

    paths: dict[str, Path | None] = {}
    paths["portfolio_analysis"] = export_plot_portfolio_analysis(reactives_shiny = reactives_shiny)
    paths["portfolio_comparison"] = export_plot_portfolio_comparison(reactives_shiny = reactives_shiny)
    paths["weights_analysis"] = export_plot_weights_analysis(reactives_shiny = reactives_shiny)
    paths["weights_composition"] = export_plot_weights_pie(reactives_shiny = reactives_shiny)
    paths["skfolio_weights"] = export_plot_skfolio_weights(reactives_shiny = reactives_shiny)
    paths["skfolio_performance"] = export_plot_skfolio_performance(reactives_shiny = reactives_shiny)
    paths["simulation_fan_chart"] = export_plot_simulation_fan_chart(reactives_shiny = reactives_shiny)
    paths["simulation_histogram"] = export_plot_simulation_histogram(reactives_shiny = reactives_shiny)
    paths["goal_parity_weights"] = export_plot_goal_parity_weights(reactives_shiny = reactives_shiny)
    paths["goal_parity_goal_powers"] = export_plot_goal_parity_goal_powers(reactives_shiny = reactives_shiny)

    generated = sum(1 for v in paths.values() if v is not None)
    _logger.info("Generated %d / %d SVG images", generated, len(paths))

    # Create placeholder SVGs for any charts that could not be generated so
    # that the Typst template's image() calls never fail on missing files.
    _placeholder_map: dict[str, str] = {
        "portfolio_analysis": "chart_portfolio_analysis_returns_distribution.svg",
        "portfolio_comparison": "chart_portfolio_comparison_portfolio_vs_benchmark.svg",
        "weights_analysis": "chart_weights_analysis_portfolio_weight_distribution_over_time.svg",
        "weights_composition": "chart_weights_analysis_portfolio_current_composition.svg",
        "skfolio_weights": "chart_skfolio_optimization_portfolio_weights_comparison.svg",
        "skfolio_performance": "chart_skfolio_optimization_comparison_portfolio_performance.svg",
        "simulation_fan_chart": "chart_simulation_portfolio_value_fan_chart.svg",
        "simulation_histogram": "chart_simulation_terminal_value_distribution.svg",
        "goal_parity_weights": "chart_goal_parity_weights.svg",
        "goal_parity_goal_powers": "chart_goal_parity_goal_powers.svg",
    }
    for key, svg_filename in _placeholder_map.items():
        if paths.get(key) is None:
            paths[key] = _create_placeholder_svg(
                filename = svg_filename,
                title=key.replace("_", " ").title(),
            )

    return paths


__all__ = [
    # Infrastructure (from _report_plot_returns)
    "_EXPECTED_SVG_FILES",
    "_IMAGES_DIR",
    "_PALETTE",
    "_QWIM_THEME",
    "_create_placeholder_svg",
    "_ensure_dir",
    "_get_inner_variables",
    "_get_visual_objects",
    "_load_sample_csv_for_plots",
    "_parse_dates_as_naive",
    "_safe_float",
    "_safe_reactive_get",
    "_save_plot",
    "ensure_all_svg_files_exist",
    # Returns / performance (from _report_plot_returns)
    "build_plotnine_portfolio_analysis_returns_distribution",
    "build_plotnine_portfolio_comparison_portfolio_vs_benchmark",
    "export_plot_portfolio_analysis",
    "export_plot_portfolio_comparison",
    # Allocation / weights (from _report_plot_allocation)
    "build_plotnine_optimalportfolios_performance_comparison",
    "build_plotnine_optimalportfolios_weights_comparison",
    "build_plotnine_skfolio_performance_comparison",
    "build_plotnine_skfolio_weights_comparison",
    "build_plotnine_weights_analysis_current_composition",
    "build_plotnine_weights_analysis_distribution_over_time",
    "export_plot_skfolio_performance",
    "export_plot_skfolio_weights",
    "export_plot_weights_analysis",
    "export_plot_weights_pie",
    # Risk / simulation (from _report_plot_risk)
    "_build_simulation_fan_data",
    "build_plotnine_simulation_fan_chart",
    "build_plotnine_simulation_terminal_value_distribution",
    "export_plot_simulation_fan_chart",
    "export_plot_simulation_histogram",
    # Goal Parity (from _report_plot_goal_parity)
    "build_plotnine_goal_parity_goal_powers",
    "build_plotnine_goal_parity_weights",
    "export_plot_goal_parity_goal_powers",
    "export_plot_goal_parity_weights",
    # Aggregate
    "export_all_report_plots",
]
