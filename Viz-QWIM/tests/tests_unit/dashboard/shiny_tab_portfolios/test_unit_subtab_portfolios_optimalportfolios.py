"""Unit tests for the Portfolio Optimization (OptimalPortfolios) Subtab Module.

Tests cover:
- Module-level constants and configuration
- Optimization method keys and labels
- Pure helper functions (resolve_*, build_*, merge_*)
- UI component creation
- Server function API and signature
- Logger configuration

Author:
    QWIM Development Team

Version:
    0.5.1

Last Modified:
    2026-05-01
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name = __name__)

# Try importing the module under test
try:
    from src.dashboard.shiny_tab_portfolios.subtab_portfolios_optimalportfolios import (
        DEFAULT_METHOD1,
        DEFAULT_METHOD2,
        DEFAULT_TIME_PERIOD,
        OPTIMALPORTFOLIOS_METHODS,
        OUTPUT_DIR,
        _logger as module_logger,
        build_optimalportfolios_input_snapshot,
        build_optimalportfolios_performance_summary,
        build_optimalportfolios_weights_rows,
        merge_optimalportfolios_output_snapshot,
        resolve_optimalportfolios_method,
        resolve_optimalportfolios_n_components,
        resolve_optimalportfolios_risk_aversion,
        resolve_optimalportfolios_risk_free_rate,
        subtab_portfolios_optimalportfolios_server,
        subtab_portfolios_optimalportfolios_ui,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError as e:
    MODULE_IMPORT_AVAILABLE = False
    _logger.warning("Module import failed, some tests will be skipped: %s", e)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_etf_data() -> pl.DataFrame:
    """Sample etf data."""
    dates = [
        (datetime(2022, 1, 1) + timedelta(days=i * 7)).strftime("%Y-%m-%d")  # noqa: DTZ001
        for i in range(104)
    ]
    np.random.seed(42)
    n = len(dates)
    return pl.DataFrame(
        {
            "Date": dates,
            "VTI": (200.0 * np.cumprod(1 + np.random.normal(0.001, 0.015, n))).tolist(),
            "VXUS": (50.0 * np.cumprod(1 + np.random.normal(0.0008, 0.018, n))).tolist(),
            "BND": (75.0 * np.cumprod(1 + np.random.normal(0.0003, 0.005, n))).tolist(),
            "VNQ": (80.0 * np.cumprod(1 + np.random.normal(0.0009, 0.012, n))).tolist(),
        }
    )


@pytest.fixture()
def sample_data_inputs(sample_etf_data: pl.DataFrame) -> dict[str, Any]:
    """Sample data inputs."""
    return {
        "My_Portfolio": pl.DataFrame(),
        "Benchmark_Portfolio": pl.DataFrame(),
        "Weights_My_Portfolio": pl.DataFrame(),
        "Time_Series_ETFs": sample_etf_data,
    }


@pytest.fixture()
def sample_data_utils() -> dict[str, Any]:
    """Sample data utils."""
    return {"theme": "default", "export_enabled": False, "chart_height": 600}


@pytest.fixture()
def sample_reactives_shiny() -> dict[str, Any]:
    """Sample reactives shiny."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


# =============================================================================
# Test classes
# =============================================================================


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Module_Constants:
    """Test module-level constants and configuration."""

    def test_output_dir_is_path(self) -> None:
        """Test that output dir is path."""
        assert isinstance(OUTPUT_DIR, Path)

    def test_output_dir_name(self) -> None:
        """Test that output dir name."""
        assert OUTPUT_DIR.name == "output"

    def test_optimalportfolios_methods_is_dict(self) -> None:
        """Test that optimalportfolios methods is dict."""
        assert isinstance(OPTIMALPORTFOLIOS_METHODS, dict)

    def test_optimalportfolios_methods_has_7_entries(self) -> None:
        """Test that optimalportfolios methods has 7 entries."""
        assert len(OPTIMALPORTFOLIOS_METHODS) == 7

    def test_expected_method_keys_present(self) -> None:
        """Test that expected method keys present."""
        for key in (
            "MIN_VARIANCE",
            "MAX_QUADRATIC_UTILITY",
            "RISK_PARITY",
            "MAX_DIVERSIFICATION",
            "MAX_SHARPE",
            "MAX_CARA_GMM",
            "TRACKING_ERROR_MIN",
        ):
            assert key in OPTIMALPORTFOLIOS_METHODS, f"Missing method key: {key}"

    def test_method_labels_are_strings(self) -> None:
        """Test that method labels are strings."""
        for key, label in OPTIMALPORTFOLIOS_METHODS.items():
            assert isinstance(label, str), f"Label for {key!r} is not a str"
            assert len(label) > 0

    def test_default_method1_is_valid_key(self) -> None:
        """Test that default method1 is valid key."""
        assert DEFAULT_METHOD1 in OPTIMALPORTFOLIOS_METHODS

    def test_default_method2_is_valid_key(self) -> None:
        """Test that default method2 is valid key."""
        assert DEFAULT_METHOD2 in OPTIMALPORTFOLIOS_METHODS

    def test_default_methods_differ(self) -> None:
        """Test that default methods differ."""
        assert DEFAULT_METHOD1 != DEFAULT_METHOD2

    def test_default_time_period_is_string(self) -> None:
        """Test that default time period is string."""
        assert isinstance(DEFAULT_TIME_PERIOD, str)
        assert len(DEFAULT_TIME_PERIOD) > 0


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Module_Imports:
    """Test that all public symbols are importable."""

    def test_ui_function_is_callable(self) -> None:
        """Test that ui function is callable."""
        assert callable(subtab_portfolios_optimalportfolios_ui)

    def test_server_function_is_callable(self) -> None:
        """Test that server function is callable."""
        assert callable(subtab_portfolios_optimalportfolios_server)

    def test_helper_functions_are_callable(self) -> None:
        """Test that helper functions are callable."""
        for fn in (
            resolve_optimalportfolios_method,
            resolve_optimalportfolios_risk_aversion,
            resolve_optimalportfolios_risk_free_rate,
            resolve_optimalportfolios_n_components,
            build_optimalportfolios_input_snapshot,
            build_optimalportfolios_performance_summary,
            build_optimalportfolios_weights_rows,
            merge_optimalportfolios_output_snapshot,
        ):
            assert callable(fn), f"{fn.__name__} is not callable"


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Module_Logger:
    """Test module-level logger configuration."""

    def test_logger_is_not_none(self) -> None:
        """Test that logger is not none."""
        assert module_logger is not None

    def test_logger_name_contains_module_path(self) -> None:
        """Test that logger name contains module path."""
        import src.dashboard.shiny_tab_portfolios.subtab_portfolios_optimalportfolios as mod

        assert "optimalportfolios" in mod.__name__.lower()


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Resolve_Method:
    """Tests for resolve_optimalportfolios_method helper."""

    def test_valid_key_is_returned_unchanged(self) -> None:
        """Test that valid key is returned unchanged."""
        for key in OPTIMALPORTFOLIOS_METHODS:
            assert resolve_optimalportfolios_method(method_value = key, default_value = DEFAULT_METHOD1) == key

    def test_none_falls_back_to_default(self) -> None:
        """Test that none falls back to default."""
        assert resolve_optimalportfolios_method(method_value = None, default_value = "MIN_VARIANCE") == "MIN_VARIANCE"

    def test_invalid_string_falls_back_to_default(self) -> None:
        """Test that invalid string falls back to default."""
        assert resolve_optimalportfolios_method(method_value = "NOT_A_METHOD", default_value = "MAX_SHARPE") == "MAX_SHARPE"

    def test_integer_falls_back_to_default(self) -> None:
        """Test that integer falls back to default."""
        assert resolve_optimalportfolios_method(method_value = 42, default_value = DEFAULT_METHOD2) == DEFAULT_METHOD2


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Resolve_RiskAversion:
    """Tests for resolve_optimalportfolios_risk_aversion helper."""

    def test_positive_float_is_returned(self) -> None:
        """Test that positive float is returned."""
        assert resolve_optimalportfolios_risk_aversion(value = 2.5) == pytest.approx(2.5)

    def test_string_float_is_parsed(self) -> None:
        """Test that string float is parsed."""
        assert resolve_optimalportfolios_risk_aversion(value = "1.5") == pytest.approx(1.5)

    def test_zero_falls_back_to_default(self) -> None:
        """Test that zero falls back to default."""
        result = resolve_optimalportfolios_risk_aversion(value = 0.0, default_value=1.0)
        assert result == pytest.approx(1.0)

    def test_negative_falls_back_to_default(self) -> None:
        """Test that negative falls back to default."""
        result = resolve_optimalportfolios_risk_aversion(value = -3.0, default_value=2.0)
        assert result == pytest.approx(2.0)

    def test_none_falls_back_to_default(self) -> None:
        """Test that none falls back to default."""
        assert resolve_optimalportfolios_risk_aversion(value = None, default_value=1.0) == pytest.approx(1.0)

    def test_invalid_string_falls_back_to_default(self) -> None:
        """Test that invalid string falls back to default."""
        assert resolve_optimalportfolios_risk_aversion(value = "abc", default_value=1.5) == pytest.approx(1.5)

    def test_boolean_falls_back_to_default(self) -> None:
        """Test that boolean values fall back to the configured default."""
        assert resolve_optimalportfolios_risk_aversion(value = True, default_value=2.5) == pytest.approx(2.5)


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Resolve_RiskFreeRate:
    """Tests for resolve_optimalportfolios_risk_free_rate helper."""

    def test_zero_is_valid(self) -> None:
        """Test that zero is valid."""
        assert resolve_optimalportfolios_risk_free_rate(value = 0.0) == pytest.approx(0.0)

    def test_positive_value_is_returned(self) -> None:
        """Test that positive value is returned."""
        assert resolve_optimalportfolios_risk_free_rate(value = 0.02) == pytest.approx(0.02)

    def test_negative_value_is_allowed(self) -> None:
        """Test that negative value is allowed."""
        assert resolve_optimalportfolios_risk_free_rate(value = -0.005) == pytest.approx(-0.005)

    def test_none_falls_back_to_default(self) -> None:
        """Test that none falls back to default."""
        assert resolve_optimalportfolios_risk_free_rate(value = None, default_value=0.0) == pytest.approx(0.0)

    def test_invalid_string_falls_back_to_default(self) -> None:
        """Test that invalid string falls back to default."""
        assert resolve_optimalportfolios_risk_free_rate(value = "xyz", default_value=0.01) == pytest.approx(0.01)

    def test_boolean_falls_back_to_default(self) -> None:
        """Test that boolean values fall back to the configured default."""
        assert resolve_optimalportfolios_risk_free_rate(value = True, default_value=0.03) == pytest.approx(0.03)


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Resolve_NComponents:
    """Tests for resolve_optimalportfolios_n_components helper."""

    def test_valid_integer_is_returned(self) -> None:
        """Test that valid integer is returned."""
        assert resolve_optimalportfolios_n_components(value = 3) == 3

    def test_string_integer_is_parsed(self) -> None:
        """Test that string integer is parsed."""
        assert resolve_optimalportfolios_n_components(value = "4") == 4

    def test_zero_falls_back_to_default(self) -> None:
        """Test that zero falls back to default."""
        assert resolve_optimalportfolios_n_components(value = 0, default_value=2) == 2

    def test_negative_falls_back_to_default(self) -> None:
        """Test that negative falls back to default."""
        assert resolve_optimalportfolios_n_components(value = -1, default_value=2) == 2

    def test_none_falls_back_to_default(self) -> None:
        """Test that none falls back to default."""
        assert resolve_optimalportfolios_n_components(value = None, default_value=2) == 2

    def test_boolean_falls_back_to_default(self) -> None:
        """Test that boolean values fall back to the configured default."""
        assert resolve_optimalportfolios_n_components(value = True, default_value=3) == 3


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Build_Input_Snapshot:
    """Tests for build_optimalportfolios_input_snapshot."""

    def test_returns_dict(self) -> None:
        """Test that returns dict."""
        snap = build_optimalportfolios_input_snapshot(
            time_period="3y",
            benchmark_key="Benchmark_Portfolio",
            method1_type="MIN_VARIANCE",
            method1_params={"is_long_only": True},
            method2_type="MAX_SHARPE",
            method2_params={"risk_free_rate": 0.0, "is_long_only": True},
        )
        assert isinstance(snap, dict)

    def test_has_required_top_level_keys(self) -> None:
        """Test that has required top level keys."""
        snap = build_optimalportfolios_input_snapshot(
            time_period="5y",
            benchmark_key="Benchmark_Portfolio",
            method1_type="MIN_VARIANCE",
            method1_params={},
            method2_type="MAX_SHARPE",
            method2_params={},
        )
        for key in ("time_period", "benchmark_key", "method1", "method2"):
            assert key in snap

    def test_invalid_method_type_falls_back(self) -> None:
        """Test that invalid method type falls back."""
        snap = build_optimalportfolios_input_snapshot(
            time_period="3y",
            benchmark_key="Benchmark_Portfolio",
            method1_type="INVALID_METHOD",
            method1_params={},
            method2_type="ALSO_INVALID",
            method2_params={},
        )
        assert snap["method1"]["type"] == DEFAULT_METHOD1
        assert snap["method2"]["type"] == DEFAULT_METHOD2

    def test_time_period_is_stored(self) -> None:
        """Test that time period is stored."""
        snap = build_optimalportfolios_input_snapshot(
            time_period="10y",
            benchmark_key="Benchmark_Portfolio",
            method1_type="MIN_VARIANCE",
            method1_params={},
            method2_type="MAX_SHARPE",
            method2_params={},
        )
        assert snap["time_period"] == "10y"

    @pytest.mark.parametrize(
        ("method_type", "method_params", "expected_key", "expected_value"),
        [
            (
                "MAX_QUADRATIC_UTILITY",
                {"risk_aversion": True},
                "risk_aversion",
                pytest.approx(1.0),
            ),
            (
                "MAX_SHARPE",
                {"risk_free_rate": True},
                "risk_free_rate",
                pytest.approx(0.0),
            ),
            (
                "MAX_CARA_GMM",
                {"risk_aversion": True, "n_components": True},
                "risk_aversion",
                pytest.approx(1.0),
            ),
            (
                "MAX_CARA_GMM",
                {"risk_aversion": True, "n_components": True},
                "n_components",
                2,
            ),
        ],
    )
    def test_boolean_numeric_params_use_safe_defaults(
        self,
        method_type: str,
        method_params: dict[str, Any],
        expected_key: str,
        expected_value: Any,
    ) -> None:
        """Boolean numeric method params should be normalized to existing defaults."""
        snap = build_optimalportfolios_input_snapshot(
            time_period="3y",
            benchmark_key="Benchmark_Portfolio",
            method1_type=method_type,
            method1_params=method_params,
            method2_type="MIN_VARIANCE",
            method2_params={},
        )

        assert snap["method1"][expected_key] == expected_value


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Merge_Output_Snapshot:
    """Tests for merge_optimalportfolios_output_snapshot."""

    def test_merges_into_empty_existing(self) -> None:
        """Test that merges into empty existing."""
        result = merge_optimalportfolios_output_snapshot(existing_data = None, data_partial = {"key": "value"})
        assert result == {"key": "value"}

    def test_merges_new_keys_over_existing(self) -> None:
        """Test that merges new keys over existing."""
        existing = {"a": 1, "b": 2}
        partial = {"b": 99, "c": 3}
        result = merge_optimalportfolios_output_snapshot(existing_data = existing, data_partial = partial)
        assert result["a"] == 1
        assert result["b"] == 99
        assert result["c"] == 3

    def test_non_dict_existing_replaced(self) -> None:
        """Test that non dict existing replaced."""
        result = merge_optimalportfolios_output_snapshot(existing_data = "bad_value", data_partial = {"x": 1})
        assert result == {"x": 1}


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Build_Weights_Rows:
    """Tests for build_optimalportfolios_weights_rows."""

    @pytest.mark.unit()
    def test_returns_list_of_dicts_with_mock(self) -> None:
        """Returns a list of row dicts when portfolios have valid weight data."""
        from unittest.mock import MagicMock

        weights_df = pl.DataFrame({
            "Date": ["2024-01-01"],
            "VTI": [0.6],
            "BND": [0.4],
        })
        p1 = MagicMock()
        p1.get_portfolio_weights.return_value = weights_df
        p2 = MagicMock()
        p2.get_portfolio_weights.return_value = weights_df

        result = build_optimalportfolios_weights_rows(portfolio_1 = p1, portfolio_2 = p2)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["asset"] in {"VTI", "BND"}
        assert "method1" in result[0]
        assert "method2" in result[0]

    @pytest.mark.unit()
    def test_nan_weights_excluded(self) -> None:
        """Rows with NaN in either portfolio weight are excluded from results."""
        from unittest.mock import MagicMock

        import math

        weights_df_1 = pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.6], "BND": [float("nan")]})
        weights_df_2 = pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.5], "BND": [0.5]})
        p1 = MagicMock()
        p1.get_portfolio_weights.return_value = weights_df_1
        p2 = MagicMock()
        p2.get_portfolio_weights.return_value = weights_df_2

        result = build_optimalportfolios_weights_rows(portfolio_1 = p1, portfolio_2 = p2)

        assert all(not math.isnan(row["method1"]) and not math.isnan(row["method2"]) for row in result)

    @pytest.mark.unit()
    def test_boolean_weights_excluded(self) -> None:
        """Rows with boolean weights should be excluded from report-ready output."""
        from unittest.mock import MagicMock

        weights_df_1 = pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.6], "BND": [True]})
        weights_df_2 = pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.5], "BND": [0.5]})
        p1 = MagicMock()
        p1.get_portfolio_weights.return_value = weights_df_1
        p2 = MagicMock()
        p2.get_portfolio_weights.return_value = weights_df_2

        result = build_optimalportfolios_weights_rows(portfolio_1 = p1, portfolio_2 = p2)

        assert len(result) == 1
        assert result[0]["asset"] == "VTI"


@pytest.mark.unit()
@pytest.mark.skipif(not MODULE_IMPORT_AVAILABLE, reason="Module import unavailable")
class Test_Build_Performance_Summary:
    """Tests for build_optimalportfolios_performance_summary."""

    @pytest.mark.unit()
    def test_returns_dict_with_method_keys(self) -> None:
        """Returns dict with method1 and method2 keys."""
        from unittest.mock import MagicMock

        p1 = MagicMock()
        p1.get_portfolio_name = "Portfolio_1"
        p2 = MagicMock()
        p2.get_portfolio_name = "Portfolio_2"

        result = build_optimalportfolios_performance_summary(portfolio_1 = p1, portfolio_2 = p2, perf_1 = None, perf_2 = None)

        assert "method1" in result
        assert "method2" in result

    @pytest.mark.unit()
    def test_none_series_returns_zero_stats(self) -> None:
        """None performance series results in zero-valued stats."""
        from unittest.mock import MagicMock

        p1 = MagicMock()
        p1.get_portfolio_name = "Portfolio_1"
        p2 = MagicMock()
        p2.get_portfolio_name = "Portfolio_2"

        result = build_optimalportfolios_performance_summary(portfolio_1 = p1, portfolio_2 = p2, perf_1 = None, perf_2 = None)

        assert result["method1"]["annualized_return"] == 0.0
        assert result["method1"]["volatility"] == 0.0

    @pytest.mark.unit()
    def test_valid_series_computes_stats(self) -> None:
        """Valid performance series produces non-trivial statistics."""
        from unittest.mock import MagicMock

        p1 = MagicMock()
        p1.get_portfolio_name = "Portfolio_1"
        p2 = MagicMock()
        p2.get_portfolio_name = "Portfolio_2"

        np.random.seed(0)
        n = 252
        values = (100.0 * np.cumprod(1 + np.random.normal(0.001, 0.01, n))).tolist()
        perf_df = pl.DataFrame({"Value": values})

        result = build_optimalportfolios_performance_summary(portfolio_1 = p1, portfolio_2 = p2, perf_1 = perf_df, perf_2 = perf_df)

        assert isinstance(result["method1"]["annualized_return"], float)
        assert result["method1"]["volatility"] > 0.0

    @pytest.mark.unit()
    def test_boolean_series_returns_zero_stats(self) -> None:
        """Boolean performance values should stay on the existing zero-stats fallback path."""
        from unittest.mock import MagicMock

        p1 = MagicMock()
        p1.get_portfolio_name = "Portfolio_1"
        p2 = MagicMock()
        p2.get_portfolio_name = "Portfolio_2"

        perf_df = pl.DataFrame({"Value": [True, False, True]})

        result = build_optimalportfolios_performance_summary(portfolio_1 = p1, portfolio_2 = p2, perf_1 = perf_df, perf_2 = perf_df)

        assert result["method1"]["annualized_return"] == 0.0
        assert result["method1"]["volatility"] == 0.0
        assert result["method1"]["sharpe_ratio"] == 0.0
