"""Public compatibility facade for dashboard visual utilities.

This module preserves the historical import surface while delegating the
implementation to smaller private helper modules. The split keeps the public API
stable and brings the file under the project line-count limit.
"""

from __future__ import annotations

from src.dashboard.shiny_utils.utils_data import (
    calculate_portfolio_returns,
    downsample_dataframe,
    validate_portfolio_and_benchmark_data_if_not_already_validated,
    validate_portfolio_data,
)

from ._utils_visuals_plotting import (
    create_plot_comparison_portfolios,
    create_plot_drawdowns_analysis,
    create_plot_portfolios_comparison,
    create_plot_returns_distribution,
    create_plot_rolling_statistics,
)
from ._utils_visuals_shared import (
    OUTPUT_DIR,
    create_error_figure,
    format_value_for_display,
    safe_numeric_conversion,
    validate_data_visuals,
)
from ._utils_visuals_tables import (
    calculate_table_metrics_performance,
    calculate_table_stats_basic,
    create_enhanced_summary_table,
    create_enhanced_summary_table_multi_column,
    create_table_comparison_stats,
    create_table_summary_weights_analysis,
)


__all__ = [
    "OUTPUT_DIR",
    "calculate_portfolio_returns",
    "calculate_table_metrics_performance",
    "calculate_table_stats_basic",
    "create_enhanced_summary_table",
    "create_enhanced_summary_table_multi_column",
    "create_error_figure",
    "create_plot_comparison_portfolios",
    "create_plot_drawdowns_analysis",
    "create_plot_portfolios_comparison",
    "create_plot_returns_distribution",
    "create_plot_rolling_statistics",
    "create_table_comparison_stats",
    "create_table_summary_weights_analysis",
    "downsample_dataframe",
    "format_value_for_display",
    "safe_numeric_conversion",
    "validate_portfolio_and_benchmark_data_if_not_already_validated",
    "validate_data_visuals",
    "validate_portfolio_data",
]


for exported_symbol in (
    calculate_table_metrics_performance,
    calculate_table_stats_basic,
    create_enhanced_summary_table,
    create_enhanced_summary_table_multi_column,
    create_error_figure,
    create_plot_comparison_portfolios,
    create_plot_drawdowns_analysis,
    create_plot_portfolios_comparison,
    create_plot_returns_distribution,
    create_plot_rolling_statistics,
    create_table_comparison_stats,
    create_table_summary_weights_analysis,
    format_value_for_display,
    safe_numeric_conversion,
    validate_data_visuals,
):
    exported_symbol.__module__ = __name__

del exported_symbol
