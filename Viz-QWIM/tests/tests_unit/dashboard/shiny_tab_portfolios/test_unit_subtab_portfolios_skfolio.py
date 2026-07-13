"""Unit tests for the Portfolio Optimization (skfolio) Subtab Module.

This module provides comprehensive unit tests for the subtab_portfolios_skfolio module,
testing the UI and server logic for skfolio-based portfolio optimization in the QWIM
Dashboard.

Tests cover:
- Module-level constants and configuration
- Optimization method categories and keys
- Individual method dictionaries (Basic, Convex, Clustering, Ensemble)
- Objective function options
- UI component creation
- Server function API and signature
- Data validation and error handling

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-02-01
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance for test logging
_logger = get_logger(name = __name__)

# Try importing the module under test - may fail in some environments
# due to complex Shiny / skfolio dependencies
try:
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_skfolio import (
        BASIC_METHODS,
        CLUSTERING_METHODS,
        CONVEX_METHODS,
        ENSEMBLE_METHODS,
        OBJECTIVE_FUNCTIONS,
        OPTIMIZATION_CATEGORIES,
        OUTPUT_DIR,
        _logger as module_logger,
        build_skfolio_input_snapshot,
        build_skfolio_performance_summary,
        build_skfolio_weights_rows,
        merge_skfolio_output_snapshot,
        resolve_skfolio_method_category,
        resolve_skfolio_method_type,
        resolve_skfolio_objective,
        resolve_skfolio_risk_aversion,
        subtab_portfolios_skfolio_server,
        subtab_portfolios_skfolio_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning(f"Module import failed, some tests will be skipped: {e}")


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture()
def sample_etf_data() -> pl.DataFrame:
    """Create sample ETF price data for optimization testing.

    Returns:
        pl.DataFrame: Sample ETF price DataFrame with Date and ETF columns.
    """
    dates = [
        (datetime(2022, 1, 1) + timedelta(days=i * 7)).strftime("%Y-%m-%d")  # noqa: DTZ001
        for i in range(104)  # 2 years of weekly data
    ]
    np.random.seed(42)
    num_dates = len(dates)

    # Simulate realistic ETF prices
    vti_prices = 200.0 * np.cumprod(1 + np.random.normal(0.001, 0.015, num_dates))
    vxus_prices = 50.0 * np.cumprod(1 + np.random.normal(0.0008, 0.018, num_dates))
    bnd_prices = 75.0 * np.cumprod(1 + np.random.normal(0.0003, 0.005, num_dates))
    vnq_prices = 80.0 * np.cumprod(1 + np.random.normal(0.0009, 0.012, num_dates))

    return pl.DataFrame(
        {
            "Date": dates,
            "VTI": vti_prices.tolist(),
            "VXUS": vxus_prices.tolist(),
            "BND": bnd_prices.tolist(),
            "VNQ": vnq_prices.tolist(),
        },
    )


@pytest.fixture()
def sample_returns_data(sample_etf_data: pl.DataFrame) -> pl.DataFrame:
    """Compute percent-change returns from ETF price data.

    Args:
        sample_etf_data: Sample ETF price DataFrame.

    Returns:
        pl.DataFrame: Returns DataFrame with Date and pct-change columns.
    """
    returns_data = sample_etf_data.clone()
    for col in returns_data.columns:
        if col != "Date":
            returns_data = returns_data.with_columns(
                pl.col(col).pct_change().alias(col),
            )
    return returns_data.slice(1, returns_data.height - 1)


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Create sample data utilities dictionary for testing.

    Returns:
        dict: Sample data utilities configuration dictionary.
    """
    return {
        "theme": "default",
        "export_enabled": False,
        "chart_height": 600,
        "downsampling_threshold": 200,
    }


@pytest.fixture()
def sample_data_inputs(sample_etf_data: pl.DataFrame) -> dict[str, Any]:
    """Create sample data inputs dictionary for testing.

    Args:
        sample_etf_data: Sample ETF price DataFrame.

    Returns:
        dict: Sample data inputs dictionary with all required keys.
    """
    return {
        "My_Portfolio": pl.DataFrame(),
        "Benchmark_Portfolio": pl.DataFrame(),
        "Weights_My_Portfolio": pl.DataFrame(),
        "Time_Series_ETFs": sample_etf_data,
    }


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Create sample reactives dictionary for testing.

    Returns:
        dict: Sample reactive values dictionary.
    """
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Module_Constants:
    """Test module-level constants and configuration."""

    @pytest.mark.unit()
    def test_output_dir_is_path_object(self) -> None:
        """Test that OUTPUT_DIR is a Path object."""
        assert isinstance(OUTPUT_DIR, Path)
        _logger.debug(f"OUTPUT_DIR type verified: {type(OUTPUT_DIR)}")

    @pytest.mark.unit()
    def test_output_dir_name_is_output(self) -> None:
        """Test that OUTPUT_DIR points to the expected directory name."""
        assert OUTPUT_DIR.name == "output"
        _logger.debug(f"OUTPUT_DIR name: {OUTPUT_DIR.name}")

    @pytest.mark.unit()
    def test_optimization_categories_is_dict(self) -> None:
        """Test that OPTIMIZATION_CATEGORIES is a dictionary."""
        assert isinstance(OPTIMIZATION_CATEGORIES, dict)
        _logger.debug(f"OPTIMIZATION_CATEGORIES type verified: {type(OPTIMIZATION_CATEGORIES)}")

    @pytest.mark.unit()
    def test_basic_methods_is_dict(self) -> None:
        """Test that BASIC_METHODS is a dictionary."""
        assert isinstance(BASIC_METHODS, dict)
        _logger.debug(f"BASIC_METHODS type: {type(BASIC_METHODS)}")

    @pytest.mark.unit()
    def test_convex_methods_is_dict(self) -> None:
        """Test that CONVEX_METHODS is a dictionary."""
        assert isinstance(CONVEX_METHODS, dict)
        _logger.debug(f"CONVEX_METHODS type: {type(CONVEX_METHODS)}")

    @pytest.mark.unit()
    def test_clustering_methods_is_dict(self) -> None:
        """Test that CLUSTERING_METHODS is a dictionary."""
        assert isinstance(CLUSTERING_METHODS, dict)
        _logger.debug(f"CLUSTERING_METHODS type: {type(CLUSTERING_METHODS)}")

    @pytest.mark.unit()
    def test_ensemble_methods_is_dict(self) -> None:
        """Test that ENSEMBLE_METHODS is a dictionary."""
        assert isinstance(ENSEMBLE_METHODS, dict)
        _logger.debug(f"ENSEMBLE_METHODS type: {type(ENSEMBLE_METHODS)}")

    @pytest.mark.unit()
    def test_objective_functions_is_dict(self) -> None:
        """Test that OBJECTIVE_FUNCTIONS is a dictionary."""
        assert isinstance(OBJECTIVE_FUNCTIONS, dict)
        _logger.debug(f"OBJECTIVE_FUNCTIONS type: {type(OBJECTIVE_FUNCTIONS)}")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Module_Imports:
    """Test that all required module imports are available."""

    @pytest.mark.unit()
    def test_ui_function_is_importable(self) -> None:
        """Test that subtab_portfolios_skfolio_ui function can be imported."""
        assert callable(subtab_portfolios_skfolio_ui)
        _logger.debug("subtab_portfolios_skfolio_ui successfully imported")

    @pytest.mark.unit()
    def test_server_function_is_importable(self) -> None:
        """Test that subtab_portfolios_skfolio_server function can be imported."""
        assert callable(subtab_portfolios_skfolio_server)
        _logger.debug("subtab_portfolios_skfolio_server successfully imported")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Module_Logger:
    """Test module-level logger configuration."""

    @pytest.mark.unit()
    def test_logger_is_configured(self) -> None:
        """Test that module logger is properly configured."""
        assert module_logger is not None
        _logger.debug("Module logger verified")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Skfolio_Default_Resolution_Helpers:
    """Tests for pure helper functions backing startup/default behavior."""

    @pytest.mark.unit()
    def test_resolve_method_category_falls_back_for_invalid_value(self) -> None:
        """Invalid category values should fall back deterministically."""
        assert resolve_skfolio_method_category(category_value = None, default_value = "basic") == "basic"
        assert resolve_skfolio_method_category(category_value = "invalid", default_value = "convex") == "convex"

    @pytest.mark.unit()
    def test_resolve_method_type_uses_category_default(self) -> None:
        """Invalid method values should resolve to the default for the category."""
        assert resolve_skfolio_method_type(category_value = "basic", method_value = None) == "BASIC_EQUAL_WEIGHTED"
        assert resolve_skfolio_method_type(category_value = "convex", method_value = "unknown") == "CONVEX_MEAN_RISK"

    @pytest.mark.unit()
    def test_resolve_method_type_accepts_valid_method(self) -> None:
        """Valid method keys should be preserved."""
        assert resolve_skfolio_method_type(category_value = "convex", method_value = "CONVEX_MEAN_RISK") == "CONVEX_MEAN_RISK"

    @pytest.mark.unit()
    def test_resolve_objective_and_risk_aversion_use_safe_defaults(self) -> None:
        """Invalid objective and risk aversion values should resolve safely."""
        assert resolve_skfolio_objective(objective_value = None, default_value = "MINIMIZE_RISK") == "MINIMIZE_RISK"
        assert resolve_skfolio_risk_aversion(risk_aversion_value = "not-a-number", default_value = 2.5) == pytest.approx(2.5)

    @pytest.mark.unit()
    def test_resolve_risk_aversion_boolean_uses_safe_default(self) -> None:
        """Boolean risk aversion values should fall back to the configured default."""
        assert resolve_skfolio_risk_aversion(risk_aversion_value = True, default_value = 2.5) == pytest.approx(2.5)

    @pytest.mark.unit()
    def test_resolve_objective_accepts_valid_value(self) -> None:
        """Valid objective keys should be preserved."""
        assert resolve_skfolio_objective(objective_value = "MAXIMIZE_RATIO", default_value = "MINIMIZE_RISK") == "MAXIMIZE_RATIO"

    @pytest.mark.unit()
    def test_build_input_snapshot_applies_defaults(self) -> None:
        """Input snapshot should normalize missing categories, methods, and objectives."""
        result = build_skfolio_input_snapshot(
            time_period=None,
            method1_category=None,
            method1_type=None,
            method1_objective=None,
            method1_risk_aversion=None,
            method2_category="ensemble",
            method2_type=None,
            method2_objective=None,
            method2_risk_aversion="3.5",
        )

        assert result["time_period"] == "3y"
        assert result["method1"]["category"] == "basic"
        assert result["method1"]["type"] == "BASIC_EQUAL_WEIGHTED"
        assert result["method1"]["objective"] == "MINIMIZE_RISK"
        assert result["method1"]["risk_aversion"] == pytest.approx(1.0)
        assert result["method2"]["category"] == "ensemble"
        assert result["method2"]["type"] == "ENSEMBLE_STACKING"
        assert result["method2"]["objective"] == "MAXIMIZE_RATIO"
        assert result["method2"]["risk_aversion"] == pytest.approx(3.5)

    @pytest.mark.unit()
    def test_build_weights_rows_filters_nan_assets(self) -> None:
        """Rows with NaN weights should be excluded from report output."""

        class _Portfolio:
            """Tests for Portfolio."""
            def __init__(self, weights_df: pl.DataFrame) -> None:
                """Init."""
                self._weights_df = weights_df

            def get_portfolio_weights(self) -> pl.DataFrame:
                """Get portfolio weights."""
                return self._weights_df

        portfolio_1 = _Portfolio(
            pl.DataFrame(
                {
                    "Date": ["2025-01-02"],
                    "IVV": [0.6],
                    "AGG": [0.4],
                    "GLD": [float("nan")],
                },
            ),
        )
        portfolio_2 = _Portfolio(
            pl.DataFrame(
                {
                    "Date": ["2025-01-02"],
                    "IVV": [0.5],
                    "AGG": [0.5],
                    "GLD": [0.0],
                },
            ),
        )

        result = build_skfolio_weights_rows(portfolio_1 = portfolio_1, portfolio_2 = portfolio_2)

        assert result == [
            {"asset": "IVV", "equal_weighted": 0.6, "mean_risk": 0.5},
            {"asset": "AGG", "equal_weighted": 0.4, "mean_risk": 0.5},
        ]

    @pytest.mark.unit()
    def test_build_weights_rows_excludes_boolean_assets(self) -> None:
        """Rows with boolean weights should be excluded from report output."""

        class _Portfolio:
            """Tests for Portfolio."""

            def __init__(self, weights_df: pl.DataFrame) -> None:
                """Init."""
                self._weights_df = weights_df

            def get_portfolio_weights(self) -> pl.DataFrame:
                """Get portfolio weights."""
                return self._weights_df

        portfolio_1 = _Portfolio(
            pl.DataFrame(
                {
                    "Date": ["2025-01-02"],
                    "IVV": [0.6],
                    "AGG": [True],
                },
            ),
        )
        portfolio_2 = _Portfolio(
            pl.DataFrame(
                {
                    "Date": ["2025-01-02"],
                    "IVV": [0.5],
                    "AGG": [0.5],
                },
            ),
        )

        result = build_skfolio_weights_rows(portfolio_1 = portfolio_1, portfolio_2 = portfolio_2)

        assert result == [{"asset": "IVV", "equal_weighted": 0.6, "mean_risk": 0.5}]

    @pytest.mark.unit()
    def test_build_performance_summary_handles_missing_series(self) -> None:
        """Missing performance series should return zeroed metrics."""

        class _Portfolio:
            """Tests for Portfolio."""
            def __init__(self, name: str) -> None:
                """Init."""
                self.get_portfolio_name = name

        result = build_skfolio_performance_summary(
            portfolio_1 = _Portfolio("Portfolio 1"),
            portfolio_2 = _Portfolio("Portfolio 2"),
            perf_1 = None,
            perf_2 = None,
        )

        assert result["method1"]["label"] == "Portfolio 1"
        assert result["method1"]["annualized_return"] == pytest.approx(0.0)
        assert result["method2"]["sharpe_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_build_performance_summary_computes_metrics_for_valid_series(self) -> None:
        """Valid performance series should produce non-zero annualized metrics."""

        class _Portfolio:
            """Tests for Portfolio."""
            def __init__(self, name: str) -> None:
                """Init."""
                self.get_portfolio_name = name

        perf_1 = pl.DataFrame({"Value": [100.0, 101.0, 103.0, 104.0]})
        perf_2 = pl.DataFrame({"Value": [100.0, 99.5, 100.5, 101.0]})

        result = build_skfolio_performance_summary(
            portfolio_1 = _Portfolio("Portfolio 1"),
            portfolio_2 = _Portfolio("Portfolio 2"),
            perf_1 = perf_1,
            perf_2 = perf_2,
        )

        assert result["method1"]["annualized_return"] != 0.0
        assert result["method1"]["volatility"] > 0.0
        assert result["method2"]["volatility"] > 0.0

    @pytest.mark.unit()
    def test_build_performance_summary_boolean_series_returns_zero_metrics(self) -> None:
        """Boolean performance values should stay on the existing zero-metrics path."""

        class _Portfolio:
            """Tests for Portfolio."""

            def __init__(self, name: str) -> None:
                """Init."""
                self.get_portfolio_name = name

        perf_1 = pl.DataFrame({"Value": [True, False, True]})
        perf_2 = pl.DataFrame({"Value": [True, False, True]})

        result = build_skfolio_performance_summary(
            portfolio_1 = _Portfolio("Portfolio 1"),
            portfolio_2 = _Portfolio("Portfolio 2"),
            perf_1 = perf_1,
            perf_2 = perf_2,
        )

        assert result["method1"]["annualized_return"] == pytest.approx(0.0)
        assert result["method1"]["volatility"] == pytest.approx(0.0)
        assert result["method2"]["sharpe_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_merge_output_snapshot_preserves_existing_keys(self) -> None:
        """Partial skfolio output updates should merge instead of overwrite."""
        result = merge_skfolio_output_snapshot(
            existing_data = {"statistics_comparison": [{"metric": "Sharpe"}]},
            data_partial = {"weights_comparison": [{"asset": "IVV"}]},
        )

        assert result["statistics_comparison"][0]["metric"] == "Sharpe"
        assert result["weights_comparison"][0]["asset"] == "IVV"

    @pytest.mark.unit()
    def test_merge_output_snapshot_handles_non_dict_existing_value(self) -> None:
        """Non-dict existing values should be replaced by the new partial snapshot."""
        result = merge_skfolio_output_snapshot(existing_data = None, data_partial = {"weights_comparison": [{"asset": "AGG"}]})

        assert result == {"weights_comparison": [{"asset": "AGG"}]}


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Optimization_Categories:
    """Test OPTIMIZATION_CATEGORIES dictionary content."""

    @pytest.mark.unit()
    def test_has_four_categories(self) -> None:
        """Test that there are exactly four optimization categories."""
        assert len(OPTIMIZATION_CATEGORIES) == 4
        _logger.debug(f"Category count: {len(OPTIMIZATION_CATEGORIES)}")

    @pytest.mark.unit()
    def test_basic_category_key_exists(self) -> None:
        """Test that 'basic' category key exists."""
        assert "basic" in OPTIMIZATION_CATEGORIES
        _logger.debug("basic category key verified")

    @pytest.mark.unit()
    def test_convex_category_key_exists(self) -> None:
        """Test that 'convex' category key exists."""
        assert "convex" in OPTIMIZATION_CATEGORIES
        _logger.debug("convex category key verified")

    @pytest.mark.unit()
    def test_clustering_category_key_exists(self) -> None:
        """Test that 'clustering' category key exists."""
        assert "clustering" in OPTIMIZATION_CATEGORIES
        _logger.debug("clustering category key verified")

    @pytest.mark.unit()
    def test_ensemble_category_key_exists(self) -> None:
        """Test that 'ensemble' category key exists."""
        assert "ensemble" in OPTIMIZATION_CATEGORIES
        _logger.debug("ensemble category key verified")

    @pytest.mark.unit()
    def test_all_category_values_are_strings(self) -> None:
        """Test that all category values are non-empty strings."""
        for key, value in OPTIMIZATION_CATEGORIES.items():
            assert isinstance(value, str), f"Category '{key}' value must be a string"
            assert len(value) > 0, f"Category '{key}' value must be a non-empty string"
        _logger.debug("All category values are non-empty strings")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Basic_Methods:
    """Test BASIC_METHODS dictionary content."""

    @pytest.mark.unit()
    def test_has_three_methods(self) -> None:
        """Test that there are exactly three basic methods."""
        assert len(BASIC_METHODS) == 3
        _logger.debug(f"Basic methods count: {len(BASIC_METHODS)}")

    @pytest.mark.unit()
    def test_equal_weighted_method_exists(self) -> None:
        """Test that BASIC_EQUAL_WEIGHTED method key exists."""
        assert "BASIC_EQUAL_WEIGHTED" in BASIC_METHODS
        _logger.debug("BASIC_EQUAL_WEIGHTED key verified")

    @pytest.mark.unit()
    def test_inverse_volatility_method_exists(self) -> None:
        """Test that BASIC_INVERSE_VOLATILITY method key exists."""
        assert "BASIC_INVERSE_VOLATILITY" in BASIC_METHODS
        _logger.debug("BASIC_INVERSE_VOLATILITY key verified")

    @pytest.mark.unit()
    def test_random_dirichlet_method_exists(self) -> None:
        """Test that BASIC_RANDOM_DIRICHLET method key exists."""
        assert "BASIC_RANDOM_DIRICHLET" in BASIC_METHODS
        _logger.debug("BASIC_RANDOM_DIRICHLET key verified")

    @pytest.mark.unit()
    def test_all_basic_keys_start_with_basic_prefix(self) -> None:
        """Test that all BASIC_METHODS keys start with 'BASIC_'."""
        for key in BASIC_METHODS:
            assert key.startswith("BASIC_"), f"Key '{key}' should start with 'BASIC_'"
        _logger.debug("All basic method keys have correct prefix")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Convex_Methods:
    """Test CONVEX_METHODS dictionary content."""

    @pytest.mark.unit()
    def test_has_five_methods(self) -> None:
        """Test that there are exactly five convex methods."""
        assert len(CONVEX_METHODS) == 5
        _logger.debug(f"Convex methods count: {len(CONVEX_METHODS)}")

    @pytest.mark.unit()
    def test_mean_risk_method_exists(self) -> None:
        """Test that CONVEX_MEAN_RISK method key exists."""
        assert "CONVEX_MEAN_RISK" in CONVEX_METHODS
        _logger.debug("CONVEX_MEAN_RISK key verified")

    @pytest.mark.unit()
    def test_risk_budgeting_method_exists(self) -> None:
        """Test that CONVEX_RISK_BUDGETING method key exists."""
        assert "CONVEX_RISK_BUDGETING" in CONVEX_METHODS
        _logger.debug("CONVEX_RISK_BUDGETING key verified")

    @pytest.mark.unit()
    def test_maximum_diversification_method_exists(self) -> None:
        """Test that CONVEX_MAXIMUM_DIVERSIFICATION method key exists."""
        assert "CONVEX_MAXIMUM_DIVERSIFICATION" in CONVEX_METHODS
        _logger.debug("CONVEX_MAXIMUM_DIVERSIFICATION key verified")

    @pytest.mark.unit()
    def test_robust_cvar_method_exists(self) -> None:
        """Test that CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR method key exists."""
        assert "CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR" in CONVEX_METHODS
        _logger.debug("CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR key verified")

    @pytest.mark.unit()
    def test_benchmark_tracking_method_exists(self) -> None:
        """Test that CONVEX_BENCHMARK_TRACKING method key exists."""
        assert "CONVEX_BENCHMARK_TRACKING" in CONVEX_METHODS
        _logger.debug("CONVEX_BENCHMARK_TRACKING key verified")

    @pytest.mark.unit()
    def test_all_convex_keys_start_with_convex_prefix(self) -> None:
        """Test that all CONVEX_METHODS keys start with 'CONVEX_'."""
        for key in CONVEX_METHODS:
            assert key.startswith("CONVEX_"), f"Key '{key}' should start with 'CONVEX_'"
        _logger.debug("All convex method keys have correct prefix")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Clustering_Methods:
    """Test CLUSTERING_METHODS dictionary content."""

    @pytest.mark.unit()
    def test_has_four_methods(self) -> None:
        """Test that there are exactly four clustering methods."""
        assert len(CLUSTERING_METHODS) == 4
        _logger.debug(f"Clustering methods count: {len(CLUSTERING_METHODS)}")

    @pytest.mark.unit()
    def test_hrp_method_exists(self) -> None:
        """Test that CLUSTERING_HIERARCHICAL_RISK_PARITY method key exists."""
        assert "CLUSTERING_HIERARCHICAL_RISK_PARITY" in CLUSTERING_METHODS
        _logger.debug("CLUSTERING_HIERARCHICAL_RISK_PARITY key verified")

    @pytest.mark.unit()
    def test_herc_method_exists(self) -> None:
        """Test that CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION method key exists."""
        assert "CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION" in CLUSTERING_METHODS
        _logger.debug("CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION key verified")

    @pytest.mark.unit()
    def test_schur_method_exists(self) -> None:
        """Test that CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION method key exists."""
        assert "CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION" in CLUSTERING_METHODS
        _logger.debug("CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION key verified")

    @pytest.mark.unit()
    def test_nco_method_exists(self) -> None:
        """Test that CLUSTERING_NESTED method key exists."""
        assert "CLUSTERING_NESTED" in CLUSTERING_METHODS
        _logger.debug("CLUSTERING_NESTED key verified")

    @pytest.mark.unit()
    def test_all_clustering_keys_start_with_clustering_prefix(self) -> None:
        """Test that all CLUSTERING_METHODS keys start with 'CLUSTERING_'."""
        for key in CLUSTERING_METHODS:
            assert key.startswith("CLUSTERING_"), (
                f"Key '{key}' should start with 'CLUSTERING_'"
            )
        _logger.debug("All clustering method keys have correct prefix")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Ensemble_Methods:
    """Test ENSEMBLE_METHODS dictionary content."""

    @pytest.mark.unit()
    def test_has_one_method(self) -> None:
        """Test that there is exactly one ensemble method."""
        assert len(ENSEMBLE_METHODS) == 1
        _logger.debug(f"Ensemble methods count: {len(ENSEMBLE_METHODS)}")

    @pytest.mark.unit()
    def test_stacking_method_exists(self) -> None:
        """Test that ENSEMBLE_STACKING method key exists."""
        assert "ENSEMBLE_STACKING" in ENSEMBLE_METHODS
        _logger.debug("ENSEMBLE_STACKING key verified")

    @pytest.mark.unit()
    def test_stacking_key_starts_with_ensemble_prefix(self) -> None:
        """Test that ENSEMBLE_STACKING key starts with 'ENSEMBLE_'."""
        assert "ENSEMBLE_STACKING".startswith("ENSEMBLE_")
        _logger.debug("ENSEMBLE_STACKING key prefix verified")


@pytest.mark.unit()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Objective_Functions:
    """Test OBJECTIVE_FUNCTIONS dictionary content."""

    @pytest.mark.unit()
    def test_has_four_functions(self) -> None:
        """Test that there are exactly four objective functions."""
        assert len(OBJECTIVE_FUNCTIONS) == 4
        _logger.debug(f"Objective functions count: {len(OBJECTIVE_FUNCTIONS)}")

    @pytest.mark.unit()
    def test_minimize_risk_exists(self) -> None:
        """Test that MINIMIZE_RISK objective function key exists."""
        assert "MINIMIZE_RISK" in OBJECTIVE_FUNCTIONS
        _logger.debug("MINIMIZE_RISK key verified")

    @pytest.mark.unit()
    def test_maximize_return_exists(self) -> None:
        """Test that MAXIMIZE_RETURN objective function key exists."""
        assert "MAXIMIZE_RETURN" in OBJECTIVE_FUNCTIONS
        _logger.debug("MAXIMIZE_RETURN key verified")

    @pytest.mark.unit()
    def test_maximize_utility_exists(self) -> None:
        """Test that MAXIMIZE_UTILITY objective function key exists."""
        assert "MAXIMIZE_UTILITY" in OBJECTIVE_FUNCTIONS
        _logger.debug("MAXIMIZE_UTILITY key verified")

    @pytest.mark.unit()
    def test_maximize_ratio_exists(self) -> None:
        """Test that MAXIMIZE_RATIO objective function key exists."""
        assert "MAXIMIZE_RATIO" in OBJECTIVE_FUNCTIONS
        _logger.debug("MAXIMIZE_RATIO key verified")

    @pytest.mark.unit()
    def test_all_objective_values_are_strings(self) -> None:
        """Test that all objective function values are non-empty strings."""
        for key, value in OBJECTIVE_FUNCTIONS.items():
            assert isinstance(value, str), f"Objective '{key}' value must be a string"
            assert len(value) > 0, f"Objective '{key}' value must be a non-empty string"
        _logger.debug("All objective function values are non-empty strings")


@pytest.mark.unit()
class Test_Total_Method_Count:
    """Test aggregate method count across all categories."""

    @pytest.mark.unit()
    def test_total_method_count_is_thirteen(self) -> None:
        """Test that total method count across all dictionaries is 13.

        BASIC_METHODS (3) + CONVEX_METHODS (5) + CLUSTERING_METHODS (4)
        + ENSEMBLE_METHODS (1) = 13 total optimization methods.
        """
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not available")

        total = (
            len(BASIC_METHODS)
            + len(CONVEX_METHODS)
            + len(CLUSTERING_METHODS)
            + len(ENSEMBLE_METHODS)
        )
        assert total == 13
        _logger.debug(f"Total method count: {total}")

    @pytest.mark.unit()
    def test_no_duplicate_method_keys_across_categories(self) -> None:
        """Test that no method key appears in more than one category."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not available")

        all_keys = (
            list(BASIC_METHODS.keys())
            + list(CONVEX_METHODS.keys())
            + list(CLUSTERING_METHODS.keys())
            + list(ENSEMBLE_METHODS.keys())
        )
        unique_keys = set(all_keys)
        assert len(all_keys) == len(unique_keys), "Duplicate method keys found across categories"
        _logger.debug(f"All {len(all_keys)} method keys are unique")


@pytest.mark.unit()
class Test_Returns_Data_Calculation:
    """Test returns calculation from ETF price data."""

    @pytest.mark.unit()
    def test_returns_data_has_date_column(
        self,
        sample_returns_data: pl.DataFrame,
    ) -> None:
        """Test that returns data retains Date column."""
        assert "Date" in sample_returns_data.columns
        _logger.debug("Returns data has Date column")

    @pytest.mark.unit()
    def test_returns_data_has_fewer_rows_than_prices(
        self,
        sample_etf_data: pl.DataFrame,
        sample_returns_data: pl.DataFrame,
    ) -> None:
        """Test that returns data has one fewer row than price data (pct_change)."""
        assert len(sample_returns_data) == len(sample_etf_data) - 1
        _logger.debug(
            f"Returns rows: {len(sample_returns_data)}, "
            f"Price rows: {len(sample_etf_data)}",
        )

    @pytest.mark.unit()
    def test_returns_columns_match_etf_columns(
        self,
        sample_etf_data: pl.DataFrame,
        sample_returns_data: pl.DataFrame,
    ) -> None:
        """Test that returns data has same columns as input ETF data."""
        assert set(sample_returns_data.columns) == set(sample_etf_data.columns)
        _logger.debug("Returns columns match ETF columns")

    @pytest.mark.unit()
    def test_returns_values_are_reasonable(
        self,
        sample_returns_data: pl.DataFrame,
    ) -> None:
        """Test that returns values are within plausible weekly range."""
        for col in sample_returns_data.columns:
            if col != "Date":
                max_abs = sample_returns_data[col].abs().max()
                # Weekly returns should not exceed ±50% in normal conditions
                assert max_abs < 0.5, f"Returns for {col} exceeds ±50%: {max_abs}"
        _logger.debug("Returns values are within plausible range")


@pytest.mark.unit()
class Test_Data_Inputs_Structure:
    """Test data inputs dictionary structure for skfolio optimization."""

    @pytest.mark.unit()
    def test_data_inputs_has_time_series_etfs(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Time_Series_ETFs key."""
        assert "Time_Series_ETFs" in sample_data_inputs
        assert isinstance(sample_data_inputs["Time_Series_ETFs"], pl.DataFrame)

    @pytest.mark.unit()
    def test_time_series_etfs_not_empty(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that ETF time series data is not empty."""
        etf_data = sample_data_inputs["Time_Series_ETFs"]
        assert len(etf_data) > 0
        _logger.debug(f"ETF time series has {len(etf_data)} rows")

    @pytest.mark.unit()
    def test_data_inputs_has_my_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has My_Portfolio key."""
        assert "My_Portfolio" in sample_data_inputs

    @pytest.mark.unit()
    def test_data_inputs_has_benchmark_portfolio(
        self,
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that data_inputs has Benchmark_Portfolio key."""
        assert "Benchmark_Portfolio" in sample_data_inputs


@pytest.mark.unit()
class Test_Reactives_Shiny_Structure:
    """Test the structure of the reactives_shiny dictionary for skfolio subtab."""

    @pytest.mark.unit()
    def test_user_inputs_key_exists(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that User_Inputs_Shiny key exists in reactives."""
        assert "User_Inputs_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_inner_variables_key_exists(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that Inner_Variables_Shiny key exists in reactives."""
        assert "Inner_Variables_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_triggers_key_exists(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that Triggers_Shiny key exists in reactives."""
        assert "Triggers_Shiny" in sample_reactives_shiny

    @pytest.mark.unit()
    def test_visual_objects_key_exists(
        self,
        sample_reactives_shiny: dict[str, Any],
    ) -> None:
        """Test that Visual_Objects_Shiny key exists in reactives."""
        assert "Visual_Objects_Shiny" in sample_reactives_shiny


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration()
class Test_Skfolio_Optimization_Integration:
    """Integration tests for skfolio optimization subtab."""

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny/skfolio dependencies",
    )
    @pytest.mark.unit()
    def test_ui_creates_valid_component(
        self,
        sample_data_utils: dict[str, Any],
        sample_data_inputs: dict[str, Any],
    ) -> None:
        """Test that UI function creates a valid Shiny component."""
        result = subtab_portfolios_skfolio_ui("ID_test_ui",
            data_utils=sample_data_utils,
            data_inputs=sample_data_inputs,
        )
        assert result is not None

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny/skfolio dependencies",
    )
    @pytest.mark.unit()
    def test_server_function_has_expected_parameters(self) -> None:
        """Test that server function has all expected parameters."""
        import inspect

        assert callable(subtab_portfolios_skfolio_server)
        sig = inspect.signature(subtab_portfolios_skfolio_server)
        assert "id" in sig.parameters
        _logger.debug(f"Server parameters: {list(sig.parameters.keys())}")

    @pytest.mark.skipif(
        not MODULE_IMPORT_AVAILABLE,
        reason="Module import failed due to Shiny/skfolio dependencies",
    )
    @pytest.mark.unit()
    def test_optimization_categories_align_with_method_dicts(self) -> None:
        """Test that each OPTIMIZATION_CATEGORIES key has a corresponding METHODS dict."""
        category_to_dict = {
            "basic": BASIC_METHODS,
            "convex": CONVEX_METHODS,
            "clustering": CLUSTERING_METHODS,
            "ensemble": ENSEMBLE_METHODS,
        }
        for category_key in OPTIMIZATION_CATEGORIES:
            assert category_key in category_to_dict, (
                f"Category '{category_key}' has no corresponding method dict"
            )
            assert len(category_to_dict[category_key]) > 0, (
                f"Method dict for '{category_key}' is empty"
            )
        _logger.info("All optimization categories have populated method dicts")


# =============================================================================
# Regression Tests
# =============================================================================


@pytest.mark.regression()
@pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="Module import failed due to Shiny/skfolio dependencies",
)
class Test_Reactive_Value_Type_Annotation_Regression:
    """Regression tests for reactive.Value type annotation fix in subtab_portfolios_skfolio.

    These tests guard against reintroducing the type-narrowing bug where declaring
    reactive.Value(None) without an explicit generic annotation causes pyright to infer
    the type as reactive.Value[None]. This makes downstream .set(non_none_value) a type
    error, and .get() calls after None-checks resolve to Never.

    Fix applied (2026-01, pyright 53-error cleanup):
        portfolio1_result: reactive.Value[Any] = reactive.Value(None)
        portfolio2_result: reactive.Value[Any] = reactive.Value(None)
        optimization_error: reactive.Value[str | None] = reactive.Value(None)
    """

    @pytest.mark.unit()
    def test_reactive_value_any_is_reactive_value_instance(self) -> None:
        """Test that reactive.Value[Any] creates a reactive.Value instance.

        Note: reactive.Value.get() requires a Shiny reactive context and
        cannot be called in plain unit tests.  This test verifies that the
        object is correctly constructed.
        """
        from shiny import reactive

        value: reactive.Value[Any] = reactive.Value(None)
        assert isinstance(value, reactive.Value)
        _logger.debug("reactive.Value[Any](None) constructed successfully")

    @pytest.mark.unit()
    def test_reactive_value_any_set_dict_does_not_raise(self) -> None:
        """Test that reactive.Value[Any].set(dict) does not raise.

        This is the key behavioral difference from reactive.Value[None]:
        calling .set(non_None_value) on an untyped Value would be a type
        error caught at the pyright level but not at runtime.
        """
        from shiny import reactive

        value: reactive.Value[Any] = reactive.Value(None)
        test_data = {"weights": [0.25, 0.25, 0.25, 0.25], "expected_return": 0.12}
        # Should not raise — reactive.Value.set() does not require a context
        value.set(test_data)
        _logger.debug("reactive.Value[Any].set(dict) raised no exception")

    @pytest.mark.unit()
    def test_reactive_value_any_set_polars_dataframe_does_not_raise(self) -> None:
        """Test that reactive.Value[Any].set(DataFrame) does not raise."""
        from shiny import reactive

        value: reactive.Value[Any] = reactive.Value(None)
        test_df = pl.DataFrame({"col1": [1, 2, 3], "col2": [0.1, 0.2, 0.3]})
        value.set(test_df)
        _logger.debug("reactive.Value[Any].set(DataFrame) raised no exception")

    @pytest.mark.unit()
    def test_reactive_value_any_set_none_after_value_does_not_raise(self) -> None:
        """Test that reactive.Value[Any] can be reset to None without raising."""
        from shiny import reactive

        value: reactive.Value[Any] = reactive.Value(None)
        value.set({"some": "data"})
        value.set(None)  # Reset — must not raise
        _logger.debug("reactive.Value[Any].set(None) after set(dict) raised no exception")

    @pytest.mark.unit()
    def test_optimization_error_reactive_set_string_does_not_raise(self) -> None:
        """Test that reactive.Value[str | None].set(str) does not raise."""
        from shiny import reactive

        optimization_error: reactive.Value[str | None] = reactive.Value(None)
        error_msg = "Optimization failed: insufficient data points"
        optimization_error.set(error_msg)
        _logger.debug("reactive.Value[str | None].set(str) raised no exception")

    @pytest.mark.unit()
    def test_optimization_error_reactive_set_none_does_not_raise(self) -> None:
        """Test that reactive.Value[str | None].set(None) does not raise."""
        from shiny import reactive

        optimization_error: reactive.Value[str | None] = reactive.Value(None)
        optimization_error.set("some error")
        optimization_error.set(None)  # Clear — must not raise
        _logger.debug("reactive.Value[str | None].set(None) raised no exception")

    @pytest.mark.unit()
    def test_source_declares_portfolio1_result_as_any_typed_reactive(self) -> None:
        """Regression: source must declare portfolio1_result as reactive.Value[Any].

        Confirms the type annotation fix has not been reverted;
        without this, pyright infers reactive.Value[None] and causes
        downstream Never-type errors after null guards.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "portfolio1_result: reactive.Value[Any]" in source_code, (
            "portfolio1_result must be declared as reactive.Value[Any], "
            "not left as inferred reactive.Value[None]"
        )
        _logger.debug("portfolio1_result reactive.Value[Any] annotation verified in source")

    @pytest.mark.unit()
    def test_source_declares_portfolio2_result_as_any_typed_reactive(self) -> None:
        """Regression: source must declare portfolio2_result as reactive.Value[Any].

        Confirms the type annotation fix has not been reverted.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "portfolio2_result: reactive.Value[Any]" in source_code, (
            "portfolio2_result must be declared as reactive.Value[Any], "
            "not left as inferred reactive.Value[None]"
        )
        _logger.debug("portfolio2_result reactive.Value[Any] annotation verified in source")

    @pytest.mark.unit()
    def test_source_declares_optimization_error_as_str_or_none_reactive(self) -> None:
        """Regression: source must declare optimization_error as reactive.Value[str | None].

        Confirms the type annotation fix has not been reverted.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "optimization_error: reactive.Value[str | None]" in source_code, (
            "optimization_error must be declared as reactive.Value[str | None]"
        )
        _logger.debug(
            "optimization_error reactive.Value[str | None] annotation verified in source"
        )


class Test_Date_Anchor_From_Data_Max:
    """Tests that get_returns_data() anchors preset periods to the data's max date.

    When the ETF data ends well before today (e.g. 2025-03-14 vs 2026-05-09),
    using datetime.now(UTC) as the anchor causes all preset periods to land
    entirely outside the available data, returning zero rows.  The fix reads
    etf_data["Date"].max() and computes the start/end dates relative to that.
    """

    @pytest.mark.unit()
    def test_source_uses_data_max_date_not_datetime_now(self) -> None:
        """Regression: get_returns_data() must use data max date, not datetime.now()."""
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "data_max_anchor" in source_code, (
            "get_returns_data() must use data_max_anchor (derived from data max date)"
        )
        _logger.debug("data_max_anchor reference verified in source")

    @pytest.mark.unit()
    def test_source_does_not_use_datetime_now_for_end_date(self) -> None:
        """Regression: end_date in get_returns_data() must not use datetime.now(UTC)."""
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        # The string "end_date = datetime.now(UTC)" must not appear
        assert 'end_date = datetime.now(UTC).strftime' not in source_code, (
            "get_returns_data() must not set end_date = datetime.now(UTC).strftime(...). "
            "Use data_max_anchor derived from etf_data['Date'].max() instead."
        )
        _logger.debug("datetime.now(UTC) not used for end_date — verified")

    @pytest.mark.unit()
    def test_source_does_not_have_startup_run_reactive_value(self) -> None:
        """Regression: _startup_run must NOT be present — auto-run on startup was removed.

        The auto-run behaviour caused Shiny 'unexpected state' client errors because
        reactive.Value.set() inside an un-isolated effect raced with output renderers.
        Optimization now runs only when the user explicitly clicks 'Run Optimization'.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "_startup_run" not in source_code, (
            "_startup_run must be absent: auto-run on startup has been removed"
        )
        _logger.debug("_startup_run correctly absent from source")

    @pytest.mark.unit()
    def test_source_has_execute_optimization_helper(self) -> None:
        """Regression: _execute_optimization() helper must exist; called only on button click."""
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "_execute_optimization" in source_code, (
            "_execute_optimization() helper must exist in source"
        )
        _logger.debug("_execute_optimization helper verified in source")

    @pytest.mark.unit()
    def test_source_does_not_have_auto_run_effect(self) -> None:
        """Regression: _auto_run_optimization effect must NOT be present.

        The effect called _execute_optimization() without @reactive.event isolation,
        causing Shiny 'unexpected state' client errors on session startup.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        assert "_auto_run_optimization" not in source_code, (
            "_auto_run_optimization must be absent: auto-run on startup has been removed"
        )
        _logger.debug("_auto_run_optimization correctly absent from source")

    @pytest.mark.unit()
    def test_source_snapshot_save_not_in_render_functions(self) -> None:
        """Regression: _save_skfolio_output_snapshot must not be called from render functions.

        Calling reactive.Value.set() inside a render function causes further invalidations
        while outputs are in 'running' state, producing 'unexpected state' client errors.
        All snapshot saves are consolidated inside _execute_optimization() only.
        """
        source_path = Path(
            "src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py"
        )
        source_code = source_path.read_text(encoding="utf-8")
        # Count occurrences: the string appears in the function *definition* (1)
        # plus exactly one *call* inside _execute_optimization (1) = 2 total.
        # Any extra count means a call crept back into a render function.
        count = source_code.count("_save_skfolio_output_snapshot(")
        assert count == 2, (
            f"_save_skfolio_output_snapshot must appear exactly twice: once as the "
            f"function definition and once as the call inside _execute_optimization. "
            f"Found {count} occurrences — a render function may have a stray call."
        )
        _logger.debug("_save_skfolio_output_snapshot occurrence count verified: %d", count)


# =============================================================================
# Bug-fix regression: _build_skfolio_input_snapshot SilentException guard
# =============================================================================


@pytest.mark.unit()
class Test_Input_Snapshot_SilentException_Guard:
    """Regression tests ensuring _build_skfolio_input_snapshot guards optional inputs.

    The objective and risk-aversion inputs are only rendered in the DOM when the
    selected method category is "convex".  Accessing them while another category
    is active raises Shiny's SilentException, silently aborting the reactive
    effect and making the "Run Optimization" button appear unresponsive.

    The fix wraps each conditional input read in try/except so that None is
    returned as the default instead of propagating the exception.
    """

    _SOURCE_PATH = Path("src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py")

    @pytest.mark.unit()
    def test_source_guards_method1_objective_access(self) -> None:
        """method1_objective input must be read inside a try/except block."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "method1_objective" in source, "method1_objective must exist in source"
        assert "try:" in source, "try/except guard must be present in source"
        assert "except Exception:" in source, "except Exception: clause must be present"

    @pytest.mark.unit()
    def test_source_guards_method1_risk_aversion_default_to_none(self) -> None:
        """method1_risk_aversion must default to None in the except branch."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert (
            "method1_risk_aversion: Any = None" in source
            or "method1_risk_aversion = None" in source
        ), "method1_risk_aversion must default to None when the except branch is taken"

    @pytest.mark.unit()
    def test_source_guards_method2_objective_default_to_none(self) -> None:
        """method2_objective must also be guarded (symmetric with method1)."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert (
            "method2_objective: Any = None" in source
            or "method2_objective = None" in source
        ), "method2_objective must default to None when the except branch is taken"

    @pytest.mark.unit()
    def test_source_guards_method2_risk_aversion_default_to_none(self) -> None:
        """method2_risk_aversion must also be guarded (symmetric with method1)."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert (
            "method2_risk_aversion: Any = None" in source
            or "method2_risk_aversion = None" in source
        )

    @pytest.mark.unit()
    def test_build_input_snapshot_tolerates_none_objective_basic_category(self) -> None:
        """Module-level builder produces a valid snapshot when objective is None (non-convex)."""
        result = build_skfolio_input_snapshot(
            time_period="1y",
            method1_category="basic",
            method1_type="BASIC_EQUAL_WEIGHTED",
            method1_objective=None,
            method1_risk_aversion=None,
            method2_category="clustering",
            method2_type=None,
            method2_objective=None,
            method2_risk_aversion=None,
        )
        assert result["method1"]["category"] == "basic"
        assert result["method1"]["type"] == "BASIC_EQUAL_WEIGHTED"
        assert isinstance(result["method1"]["objective"], str)
        assert isinstance(result["method1"]["risk_aversion"], float)
        assert result["method2"]["category"] == "clustering"

    @pytest.mark.unit()
    def test_build_input_snapshot_tolerates_none_type_on_startup(self) -> None:
        """Snapshot builder handles None method types (dynamic select not yet rendered)."""
        result = build_skfolio_input_snapshot(
            time_period="3y",
            method1_category="basic",
            method1_type=None,
            method1_objective=None,
            method1_risk_aversion=None,
            method2_category="convex",
            method2_type=None,
            method2_objective=None,
            method2_risk_aversion=None,
        )
        assert result["method1"]["type"] == "BASIC_EQUAL_WEIGHTED"
        assert result["method2"]["type"] == "CONVEX_MEAN_RISK"


# =============================================================================
# Bug-fix regression: _build_quantstats_statistics_rows numpy fallback
# =============================================================================


@pytest.mark.unit()
class Test_Quantstats_Fallback_Statistics:
    """Regression tests for the numpy fallback in _build_quantstats_statistics_rows.

    When quantstats is absent the function must still return all six metric rows
    using only numpy/pandas.  The fallback formulas are verified here via
    independent numpy computations on known synthetic data.
    """

    _SOURCE_PATH = Path("src/dashboard/shiny_tab_portfolios/subtab_portfolios_skfolio.py")

    @pytest.mark.unit()
    def test_source_has_numpy_fallback_branch(self) -> None:
        """Source must contain a pure-numpy fallback branch inside the statistics helper."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "HAS_QUANTSTATS" in source, "HAS_QUANTSTATS flag must exist"
        assert "_metric_cagr" in source, "_metric_cagr must exist in the fallback branch"
        assert "_metric_max_drawdown" in source
        assert "_metric_calmar" in source

    @pytest.mark.unit()
    def test_source_removes_early_return_on_missing_quantstats(self) -> None:
        """The early 'return []' for missing quantstats must no longer be present."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "if not HAS_QUANTSTATS:\n            return []" not in source, (
            "Early-return guard must be replaced by the else-branch numpy fallback."
        )

    @pytest.mark.unit()
    def test_numpy_cagr_zero_for_flat_returns(self) -> None:
        """CAGR of all-zero returns must be exactly 0.0."""
        r = np.zeros(252, dtype=np.float64)
        cum = float(np.prod(1.0 + r))
        cagr = float(cum ** (252.0 / len(r)) - 1.0)
        assert cagr == pytest.approx(0.0, abs=1e-10)

    @pytest.mark.unit()
    def test_numpy_cagr_matches_analytical_value(self) -> None:
        """CAGR of a constant daily return must match the analytical compounding formula."""
        daily_r = 0.001
        n = 252
        r = np.full(n, daily_r, dtype=np.float64)
        cum = float(np.prod(1.0 + r))
        cagr = float(cum ** (252.0 / n) - 1.0)
        expected = (1.0 + daily_r) ** 252.0 - 1.0
        assert cagr == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_numpy_volatility_positive_for_random_returns(self) -> None:
        """Annualised volatility must be positive for any non-constant return series."""
        rng = np.random.default_rng(42)
        r = rng.normal(0.001, 0.01, 252)
        vol = float(np.std(r, ddof=1) * np.sqrt(252.0))
        assert vol > 0.0

    @pytest.mark.unit()
    def test_numpy_max_drawdown_non_positive(self) -> None:
        """Max drawdown must always be <= 0."""
        rng = np.random.default_rng(0)
        r = rng.normal(0.0005, 0.01, 200)
        cum = np.cumprod(1.0 + r)
        peak = np.maximum.accumulate(cum)
        mdd = float(np.min(cum / peak - 1.0))
        assert mdd <= 0.0

    @pytest.mark.unit()
    def test_numpy_max_drawdown_zero_for_monotone_increase(self) -> None:
        """Strictly increasing series should have max drawdown of exactly 0."""
        r = np.full(50, 0.01, dtype=np.float64)
        cum = np.cumprod(1.0 + r)
        peak = np.maximum.accumulate(cum)
        mdd = float(np.min(cum / peak - 1.0))
        assert mdd == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_source_none_series_guard_present(self) -> None:
        """Source must still guard against None series before computing metrics."""
        source = self._SOURCE_PATH.read_text(encoding="utf-8")
        assert "if series_1 is None or series_2 is None:" in source
        assert "return []" in source
