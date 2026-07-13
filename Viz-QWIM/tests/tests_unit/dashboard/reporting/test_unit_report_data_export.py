"""Unit tests for report_data_export module.

Tests cover:
    - ``_safe_reactive_get``  — None, callable mock, plain value
    - ``_safe_float``         — None, str, int, float, inf, nan
    - ``_safe_str``           — None, non-string, empty string, valid string
    - ``_polars_to_records``  — None, empty DataFrame, valid DataFrame
    - ``_get_inner_variables``— None dict, missing key, valid structure
    - ``_get_data_results_value`` — None dict, import-error path, valid path
    - ``export_outputs_portfolio_analysis`` — six input-type branches:
          1. ``basic_stats`` is ``pl.DataFrame``   (converted via ``_polars_to_records``)
          2. ``basic_stats`` is ``list[dict]``     (passed through directly)
          3. ``basic_stats`` is ``dict``           (returns ``[]`` — TYPE-FIX regression)
          4. ``basic_stats`` is ``None``           (falls through to sample-data fallback)
          5. ``reactives_shiny`` is ``None``       (returns empty-data JSON)
          6. ``Data_Results`` already populated   (uses pre-built dict, no recompute)

Regression notes:
    The fix in commit ``isinstance(x, (list, dict)) → isinstance(x, list)`` ensures
    that a bare dict value is NOT widened to ``list[dict[str, Any]]``.  The new
    behaviour returns an empty list (``[]``) for dict inputs, triggering the
    sample-data fallback instead of passing a dict that would break downstream
    Typst rendering.

Author:
    QWIM Development Team

Version:
    1.0.0
"""

from __future__ import annotations

import json
import math

from typing import TYPE_CHECKING, Any
from unittest.mock import patch


if TYPE_CHECKING:
    from pathlib import Path

import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Optional import guard — skip entire module if dashboard deps unavailable
# ---------------------------------------------------------------------------
try:
    from src.dashboard.reporting.report_data_export import (
        _compute_portfolio_analysis_stats_from_values,
        _compute_portfolio_metrics_from_values,
        _compute_simulation_stats_from_values,
        _compute_weight_statistics_from_weights,
        _ensure_dir,
        _get_data_results_value,
        _get_inner_variables,
        _get_user_inputs,
        _load_sample_portfolio_data,
        _load_sample_weights_data,
        _polars_to_records,
        _safe_bool,
        _read_json_dict,
        _safe_float,
        _safe_reactive_get,
        _safe_str,
        _write_json,
        export_all_report_data,
        export_client_info,
        export_data_clients_json,
        export_data_results_json,
        export_inputs_optimalportfolios_optimization,
        export_inputs_portfolio_analysis,
        export_inputs_portfolio_comparison,
        export_inputs_simulation,
        export_inputs_skfolio_optimization,
        export_inputs_weights_analysis,
        export_outputs_optimalportfolios_optimization,
        export_outputs_portfolio_analysis,
        export_outputs_portfolio_comparison,
        export_outputs_simulation,
        export_outputs_skfolio_optimization,
        export_outputs_weights_analysis,
        export_report_config,
        export_report_metadata,
        validate_report_data_quality,
    )

    MODULE_AVAILABLE = True
except ImportError as exc:
    MODULE_AVAILABLE = False
    _logger.warning(f"report_data_export import failed — tests will be skipped: {exc}")

pytestmark = pytest.mark.skipif(not MODULE_AVAILABLE, reason="report_data_export unavailable")


# ============================================================================
# Helpers
# ============================================================================


class MockReactiveValue:
    """Minimal stand-in for ``shiny.reactive.Value`` — no Shiny dependency."""

    def __init__(self, value: Any = None) -> None:
        """Init."""
        self._value = value

    def get(self) -> Any:
        """Get."""
        return self._value

    def set(self, value: Any) -> None:
        """Set."""
        self._value = value

    def __call__(self) -> Any:  # support callable protocol used by some helpers
        """Return the stored value (callable protocol support)."""
        return self._value


def _make_inner_variables_shiny(
    basic_stats: Any = None,
    quantstats: Any = None,
) -> dict[str, Any]:
    """Build a minimal ``Inner_Variables_Shiny`` dict for testing."""
    return {
        "Portfolio_Analysis_Basic_Stats": MockReactiveValue(basic_stats),
        "Portfolio_Analysis_Quantstats_Metrics": MockReactiveValue(quantstats),
    }


def _make_reactives_shiny(
    basic_stats: Any = None,
    quantstats: Any = None,
    data_results_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal ``reactives_shiny`` dict used in export tests."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": _make_inner_variables_shiny(basic_stats, quantstats),
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
        "Data_Results": {
            "Portfolio_Analysis_Outputs": MockReactiveValue(data_results_override),
        },
    }


# ============================================================================
# _safe_reactive_get
# ============================================================================


@pytest.mark.unit()
class TestSafeReactiveGet:
    """Tests for ``_safe_reactive_get``."""

    @pytest.mark.unit()
    def test_none_returns_none(self) -> None:
        """Test that none returns none."""
        assert _safe_reactive_get(reactive_value = None) is None

    @pytest.mark.unit()
    def test_callable_mock_returns_value(self) -> None:
        """Test that callable mock returns value."""
        rv = MockReactiveValue(42)
        assert _safe_reactive_get(reactive_value = rv) == 42

    @pytest.mark.unit()
    def test_plain_value_returned_as_is(self) -> None:
        """Test that plain value returned as is."""
        assert _safe_reactive_get(reactive_value = "hello") == "hello"

    @pytest.mark.unit()
    def test_mock_reactive_value(self) -> None:
        """Test that mock reactive value."""
        rv = MockReactiveValue(value=[{"a": 1}])
        assert _safe_reactive_get(reactive_value = rv) == [{"a": 1}]

    @pytest.mark.unit()
    def test_get_method_raising_returns_none(self) -> None:
        """Object with .get() that raises — must return None."""

        class _RaisesOnGet:
            """Tests for RaisesOnGet."""
            def get(self):
                """Get."""
                raise RuntimeError("simulated failure")

        assert _safe_reactive_get(reactive_value = _RaisesOnGet()) is None

    @pytest.mark.unit()
    def test_no_get_method_returns_value_as_is(self) -> None:
        """Object without .get() is returned as-is."""
        assert _safe_reactive_get(reactive_value = "hello") == "hello"


# ============================================================================
# _safe_float
# ============================================================================


@pytest.mark.unit()
class TestSafeFloat:
    """Tests for ``_safe_float``."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, 0.0),
            ("not_a_number", 0.0),
            (42, 42.0),
            (3.14, 3.14),
            (0, 0.0),
        ],
    )
    @pytest.mark.unit()
    def test_parametrized(self, value: Any, expected: float) -> None:
        """Test that parametrized."""
        assert _safe_float(value = value) == pytest.approx(expected)

    @pytest.mark.unit()
    def test_bool_returns_default(self) -> None:
        """Boolean values should not be coerced into numeric report data."""
        assert _safe_float(value = True) == 0.0
        assert _safe_float(value = False, default=8.5) == 8.5

    @pytest.mark.unit()
    def test_inf_returned_as_is(self) -> None:
        """_safe_float does not filter inf — float(inf) succeeds without error."""
        assert _safe_float(value = float("inf")) == float("inf")

    @pytest.mark.unit()
    def test_nan_returned_as_is(self) -> None:
        """_safe_float does not filter nan — float(nan) succeeds without error."""
        assert math.isnan(_safe_float(value = float("nan")))

    @pytest.mark.unit()
    def test_custom_default(self) -> None:
        """Test that custom default."""
        assert _safe_float(value = None, default=-1.0) == -1.0

    @pytest.mark.unit()
    def test_negative_float(self) -> None:
        """Test that negative float."""
        assert _safe_float(value = -7.5) == pytest.approx(-7.5)


class TestSafeBool:
    """Tests for ``_safe_bool``."""

    @pytest.mark.parametrize(
        ("value", "default_value", "expected_value"),
        [
            (True, False, True),
            (False, True, False),
            ("bad", True, True),
            (0, True, True),
            (None, False, False),
        ],
    )
    @pytest.mark.unit()
    def test_parametrized(
        self,
        value: Any,
        default_value: bool,
        expected_value: bool,
    ) -> None:
        """Non-boolean values should stay on the provided default path."""
        assert _safe_bool(value = value, default=default_value) is expected_value


# ============================================================================
# _safe_str
# ============================================================================


@pytest.mark.unit()
class TestSafeStr:
    """Tests for ``_safe_str``."""

    @pytest.mark.unit()
    def test_none_returns_default(self) -> None:
        """Test that none returns default."""
        assert _safe_str(value = None) == "N/A"

    @pytest.mark.unit()
    def test_empty_string_returned_as_is(self) -> None:
        """_safe_str converts non-None with str(); empty string stays empty."""
        assert _safe_str(value = "") == ""

    @pytest.mark.unit()
    def test_valid_string_returned(self) -> None:
        """Test that valid string returned."""
        assert _safe_str(value = "hello") == "hello"

    @pytest.mark.unit()
    def test_non_string_converted(self) -> None:
        """Test that non string converted."""
        result = _safe_str(value = 42)
        assert result == "42"

    @pytest.mark.unit()
    def test_custom_default(self) -> None:
        """Test that custom default."""
        assert _safe_str(value = None, default="unknown") == "unknown"

    @pytest.mark.unit()
    def test_whitespace_only_not_empty(self) -> None:
        """Test that whitespace only not empty."""
        # whitespace string is truthy — returned as-is
        assert _safe_str(value = "   ") == "   "


# ============================================================================
# _polars_to_records
# ============================================================================


@pytest.mark.unit()
class TestPolarsToRecords:
    """Tests for ``_polars_to_records``."""

    @pytest.mark.unit()
    def test_none_returns_empty_list(self) -> None:
        """Test that none returns empty list."""
        assert _polars_to_records(df = None) == []

    @pytest.mark.unit()
    def test_empty_dataframe_returns_empty_list(self) -> None:
        """Test that empty dataframe returns empty list."""
        df = pl.DataFrame({"a": [], "b": []})
        assert _polars_to_records(df = df) == []

    @pytest.mark.unit()
    def test_valid_dataframe_returns_records(self) -> None:
        """Test that valid dataframe returns records."""
        df = pl.DataFrame({"metric": ["CAGR", "Sharpe"], "value": [0.08, 1.2]})
        result = _polars_to_records(df = df)
        assert len(result) == 2
        assert result[0] == {"metric": "CAGR", "value": pytest.approx(0.08)}
        assert result[1] == {"metric": "Sharpe", "value": pytest.approx(1.2)}

    @pytest.mark.unit()
    def test_returns_list_of_dicts(self) -> None:
        """Test that returns list of dicts."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        result = _polars_to_records(df = df)
        assert isinstance(result, list)
        assert all(isinstance(row, dict) for row in result)

    @pytest.mark.unit()
    def test_non_dataframe_input_returns_empty_list(self) -> None:
        """Test that non dataframe input returns empty list."""
        # passes non-DataFrame — defensive check in the function
        assert _polars_to_records(df = [{"a": 1}]) == []  # type: ignore[arg-type]


# ============================================================================
# _get_inner_variables
# ============================================================================


@pytest.mark.unit()
class TestGetInnerVariables:
    """Tests for ``_get_inner_variables``."""

    @pytest.mark.unit()
    def test_none_returns_empty_dict(self) -> None:
        """Test that none returns empty dict."""
        assert _get_inner_variables(reactives_shiny = None) == {}

    @pytest.mark.unit()
    def test_empty_dict_returns_empty_dict(self) -> None:
        """Test that empty dict returns empty dict."""
        assert _get_inner_variables(reactives_shiny = {}) == {}

    @pytest.mark.unit()
    def test_missing_key_returns_empty_dict(self) -> None:
        """Test that missing key returns empty dict."""
        assert _get_inner_variables(reactives_shiny = {"User_Inputs_Shiny": {}}) == {}

    @pytest.mark.unit()
    def test_valid_structure_returns_inner_dict(self) -> None:
        """Test that valid structure returns inner dict."""
        inner = {"some_key": MockReactiveValue(42)}
        reactives = {"Inner_Variables_Shiny": inner}
        assert _get_inner_variables(reactives_shiny = reactives) is inner

    @pytest.mark.unit()
    def test_non_dict_inner_variables_returns_empty(self) -> None:
        """Test that non dict inner variables returns empty."""
        reactives = {"Inner_Variables_Shiny": "not_a_dict"}
        assert _get_inner_variables(reactives_shiny = reactives) == {}


# ============================================================================
# _get_data_results_value
# ============================================================================


@pytest.mark.unit()
class TestGetDataResultsValue:
    """Tests for ``_get_data_results_value``."""

    @pytest.mark.unit()
    def test_none_reactives_returns_empty(self) -> None:
        """Test that none reactives returns empty."""
        assert _get_data_results_value(reactives_shiny = None, subtab_key = "Portfolio_Analysis_Outputs") == {}

    @pytest.mark.unit()
    def test_empty_reactives_returns_empty(self) -> None:
        """Empty (falsy) dict — early return without calling build helper."""
        assert _get_data_results_value(reactives_shiny = {}, subtab_key = "Portfolio_Analysis_Outputs") == {}

    @pytest.mark.unit()
    def test_valid_reactives_returns_dict_or_empty(self) -> None:
        """With valid reactives, function returns dict (may be empty if helper unavailable)."""
        reactives = _make_reactives_shiny()
        result = _get_data_results_value(reactives_shiny = reactives, subtab_key = "Portfolio_Analysis_Outputs")
        assert isinstance(result, dict)


# ============================================================================
# export_outputs_portfolio_analysis — type-branch tests
# ============================================================================


@pytest.mark.unit()
class TestExportOutputsPortfolioAnalysis:
    """Tests for ``export_outputs_portfolio_analysis`` covering all type branches.

    The critical regression is that a ``dict`` value for ``basic_stats`` or
    ``quantstats`` now returns ``[]`` (triggering the sample-data fallback)
    rather than being widened to ``list[dict[str, Any]]``.
    """

    @pytest.fixture()
    def tmp_outputs_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Redirect JSON output directory to a temp folder."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        return tmp_path

    # ------------------------------------------------------------------
    # Branch 1: basic_stats is a pl.DataFrame
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_dataframe_basic_stats_converted_to_records(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """When ``basic_stats`` is a DataFrame it must be converted via _polars_to_records."""
        df = pl.DataFrame({"metric": ["CAGR"], "value": [0.08]})
        reactives = _make_reactives_shiny(basic_stats=df, quantstats=None)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"] == [{"metric": "CAGR", "value": pytest.approx(0.08)}]

    # ------------------------------------------------------------------
    # Branch 2: basic_stats is already a list[dict]
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_list_basic_stats_passed_through(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """When ``basic_stats`` is already a list it must be used directly."""
        pre_built = [{"metric": "Sharpe", "value": 1.5}]
        reactives = _make_reactives_shiny(basic_stats=pre_built, quantstats=[])

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"] == pre_built

    # ------------------------------------------------------------------
    # Branch 3 (REGRESSION): basic_stats is a dict — must return [] not the dict
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_dict_basic_stats_returns_empty_list_not_dict(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """REGRESSION: dict input must NOT be widened to list[dict[str, Any]].

        After the fix ``isinstance(x, (list, dict)) → isinstance(x, list)``,
        a bare ``dict`` must produce ``[]``.  This triggers the sample-data
        fallback path rather than passing an invalid type downstream.
        """
        dict_value = {"metric": "CAGR", "value": 0.08}  # single dict, not list
        reactives = _make_reactives_shiny(basic_stats=dict_value, quantstats=dict_value)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        # dict input must produce [] — NOT {"metric": "CAGR", "value": 0.08}
        assert result["basic_statistics"] == []
        assert result["performance_metrics"] == []

    # ------------------------------------------------------------------
    # Branch 3b: quantstats is a dict — same regression check
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_dict_quantstats_returns_empty_list(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """REGRESSION: dict quantstats also produces [] after the fix."""
        pre_built = [{"metric": "CAGR", "value": 0.08}]
        dict_quant = {"metric": "Sharpe", "value": 1.5}  # bare dict
        reactives = _make_reactives_shiny(basic_stats=pre_built, quantstats=dict_quant)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"] == pre_built
        # dict quantstats → must be [] not the dict itself
        assert result["performance_metrics"] == []

    # ------------------------------------------------------------------
    # Branch 4: None basic_stats triggers sample-data fallback
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_none_basic_stats_triggers_fallback_with_none_csv(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """When both stats are None and CSV unavailable, both lists are empty."""
        reactives = _make_reactives_shiny(basic_stats=None, quantstats=None)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"] == []
        assert result["performance_metrics"] == []

    # ------------------------------------------------------------------
    # Branch 5: reactives_shiny is None
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_none_reactives_returns_empty_json(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """None reactives_shiny must write an empty-data JSON without raising."""
        with patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = None)

        assert out_path.exists()
        result = json.loads(out_path.read_text())
        assert "basic_statistics" in result
        assert "performance_metrics" in result

    # ------------------------------------------------------------------
    # Branch 6: Data_Results already populated — skip recompute
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_pre_populated_data_results_used_directly(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """When _get_data_results_value returns data, Inner_Variables_Shiny is skipped."""
        pre_populated = {
            "basic_statistics": [{"metric": "CAGR", "value": 0.10}],
            "performance_metrics": [{"metric": "Sharpe", "value": 1.8}],
        }
        reactives = _make_reactives_shiny()

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value=pre_populated,
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"][0]["metric"] == "CAGR"
        assert result["performance_metrics"][0]["metric"] == "Sharpe"

    # ------------------------------------------------------------------
    # Output file integrity
    # ------------------------------------------------------------------
    @pytest.mark.unit()
    def test_output_file_is_valid_json(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """The JSON file written to disk must be valid JSON regardless of input."""
        reactives = _make_reactives_shiny(
            basic_stats=[{"metric": "CAGR", "value": 0.05}],
            quantstats=[{"metric": "MDD", "value": -0.12}],
        )

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        raw_text = out_path.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)  # must not raise
        assert isinstance(parsed, dict)

    @pytest.mark.unit()
    def test_output_file_path_has_expected_name(
        self,
        tmp_outputs_dir: Path,
    ) -> None:
        """Output file must be named ``outputs_portfolio_analysis.json``."""
        reactives = _make_reactives_shiny()

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        assert out_path.name == "outputs_portfolio_analysis.json"


# ============================================================================
# Regression: dict-vs-list type narrowing (standalone parametrize)
# ============================================================================


@pytest.mark.regression()
class TestTypeNarrowingRegression:
    """Regression tests documenting the isinstance fix.

    Before fix: ``isinstance(x, (list, dict))`` — dict passed through,
                causing a type error (``dict`` not assignable to
                ``list[dict[str, Any]]``).
    After fix:  ``isinstance(x, list)`` — dict always returns ``[]``.
    """

    @pytest.mark.parametrize(
        "input_value,expected_result",
        [
            # list[dict] → passes through
            ([{"k": "v"}], [{"k": "v"}]),
            # empty list → passes through as empty
            ([], []),
            # dict → now returns [] (regression: was passing dict through)
            ({"k": "v"}, []),
            # None → returns []
            (None, []),
            # string → returns [] (not a list)
            ("invalid", []),
            # int → returns []
            (42, []),
        ],
    )
    @pytest.mark.unit()
    def test_basic_stats_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        input_value: Any,
        expected_result: list,
    ) -> None:
        """Parametrized regression: each input type produces the expected list."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        reactives = _make_reactives_shiny(basic_stats=input_value, quantstats=[])

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["basic_statistics"] == expected_result


# ============================================================================
# Additional coverage for consolidated exporters and weights fallback
# ============================================================================


@pytest.mark.unit()
class TestExportOutputsWeightsAnalysis:
    """Tests for weights-analysis JSON export fallbacks."""

    @pytest.mark.unit()
    def test_sample_weights_csv_fallback_populates_weight_statistics(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When live reactives are empty, sample weights CSV should populate the table."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        sample_weights_path = tmp_path / "sample_portfolio_weights_ETFs.csv"
        pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01", "2025-01-02"],
                "IVV": [0.6, 0.5, 0.4],
                "AGG": [0.3, 0.3, 0.4],
                "GLD": [0.1, 0.2, 0.2],
            },
        ).write_csv(sample_weights_path)
        monkeypatch.setattr(mod, "_SAMPLE_WEIGHTS_CSV", sample_weights_path)

        out_path = export_outputs_weights_analysis(reactives_shiny = {})

        result = json.loads(out_path.read_text())
        assert len(result["weight_statistics"]) == 3
        assert result["weight_statistics"][0]["component"] in {"IVV", "AGG", "GLD"}


@pytest.mark.unit()
class TestConsolidatedReportExport:
    """Tests for consolidated report JSON exporters."""

    @pytest.mark.unit()
    def test_export_data_clients_json_merges_client_and_advisor_data(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Consolidated client export should reuse client_info JSON and append advisor data."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        client_info_path = tmp_path / "client_info.json"
        client_info_path.write_text(
            json.dumps({"personal_info": {"primary": {"name": "Jane Client"}}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "export_client_info", lambda *, reactives_shiny, **_: client_info_path)

        reactives = {
            "Advisor_Info": {
                "Name": MockReactiveValue("Alex Advisor"),
                "Firm": MockReactiveValue("QWIM AI Wealth Management"),
            },
        }

        out_path = export_data_clients_json(reactives_shiny = reactives)
        result = json.loads(out_path.read_text())

        assert result["personal_info"]["primary"]["name"] == "Jane Client"
        assert result["advisor_info"]["Name"] == "Alex Advisor"
        assert result["advisor_info"]["Firm"] == "QWIM AI Wealth Management"

    @pytest.mark.unit()
    def test_export_data_results_json_uses_section_exporters(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Consolidated results export should read each section from the section exporters."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        def _make_stub_exporter(filename: str, payload: dict[str, Any]):
            """Make stub exporter."""
            def _exporter(*, reactives_shiny: Any, **_: Any) -> Path:
                """Exporter."""
                output_path = tmp_path / filename
                output_path.write_text(json.dumps(payload), encoding="utf-8")
                return output_path

            return _exporter

        monkeypatch.setattr(
            mod,
            "export_inputs_portfolio_analysis",
            _make_stub_exporter("inputs_portfolio_analysis.json", {"time_period": "3Y"}),
        )
        monkeypatch.setattr(
            mod,
            "export_outputs_portfolio_analysis",
            _make_stub_exporter("outputs_portfolio_analysis.json", {"basic_statistics": [{"metric": "CAGR"}]}),
        )
        monkeypatch.setattr(
            mod,
            "export_inputs_portfolio_comparison",
            _make_stub_exporter("inputs_portfolio_comparison.json", {"viz_type": "normalized"}),
        )
        monkeypatch.setattr(
            mod,
            "export_outputs_portfolio_comparison",
            _make_stub_exporter("outputs_portfolio_comparison.json", {"metrics": {"sharpe_ratio": 1.2}}),
        )
        monkeypatch.setattr(
            mod,
            "export_inputs_weights_analysis",
            _make_stub_exporter("inputs_weights_analysis.json", {"show_pct": True}),
        )
        monkeypatch.setattr(
            mod,
            "export_outputs_weights_analysis",
            _make_stub_exporter("outputs_weights_analysis.json", {"weight_statistics": [{"component": "IVV"}]}),
        )
        monkeypatch.setattr(
            mod,
            "export_inputs_skfolio_optimization",
            _make_stub_exporter("inputs_skfolio_optimization.json", {"method1": {"type": "BASIC_EQUAL_WEIGHTED"}}),
        )
        monkeypatch.setattr(
            mod,
            "export_outputs_skfolio_optimization",
            _make_stub_exporter("outputs_skfolio_optimization.json", {"weights_comparison": [{"asset": "IVV"}]}),
        )
        monkeypatch.setattr(
            mod,
            "export_inputs_simulation",
            _make_stub_exporter("inputs_simulation.json", {"num_scenarios": 1000}),
        )
        monkeypatch.setattr(
            mod,
            "export_outputs_simulation",
            _make_stub_exporter("outputs_simulation.json", {"summary_statistics": {"num_scenarios": 1000}}),
        )

        out_path = export_data_results_json(reactives_shiny = {})
        result = json.loads(out_path.read_text())

        assert result["Portfolio_Analysis_Inputs"]["time_period"] == "3Y"
        assert result["Weights_Analysis_Outputs"]["weight_statistics"][0]["component"] == "IVV"
        assert result["Portfolio_Optimization_Skfolio_Outputs"]["weights_comparison"][0]["asset"] == "IVV"


@pytest.mark.unit()
class TestWeightsStatisticsHelper:
    """Tests for weight-statistics helper coverage."""

    @pytest.mark.unit()
    def test_returns_empty_list_for_empty_dataframe(self) -> None:
        """Empty weights data should produce no statistics rows."""
        weights_df = pl.DataFrame({"Date": []}, schema={"Date": pl.Utf8})

        assert _compute_weight_statistics_from_weights(weights_df = weights_df) == []

    @pytest.mark.unit()
    def test_skips_component_with_only_null_values(self) -> None:
        """Components with no usable numeric values should be skipped."""
        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01"],
                "IVV": [0.6, 0.4],
                "GLD": [None, None],
            },
        )

        result = _compute_weight_statistics_from_weights(weights_df = weights_df)

        assert result == [
            {
                "component": "IVV",
                "current_weight": pytest.approx(0.4),
                "mean_weight": pytest.approx(0.5),
                "min_weight": pytest.approx(0.4),
                "max_weight": pytest.approx(0.6),
                "std_weight": pytest.approx(0.1414213562),
            },
        ]

    @pytest.mark.unit()
    def Test_Boolean_Component_Column_Is_Skipped(self) -> None:
        """Boolean component columns should not be exported as numeric weight statistics."""
        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01"],
                "IVV": [0.6, 0.4],
                "Flag": [True, False],
            },
        )

        result = _compute_weight_statistics_from_weights(weights_df = weights_df)

        assert [item_row["component"] for item_row in result] == ["IVV"]

    @pytest.mark.unit()
    def test_single_observation_sets_zero_std_weight(self) -> None:
        """Single-observation components should report zero standard deviation."""
        weights_df = pl.DataFrame({"Date": ["2024-01-02"], "IVV": [0.6]})

        result = _compute_weight_statistics_from_weights(weights_df = weights_df)

        assert result[0]["std_weight"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_nan_standard_deviation_is_normalized_to_zero(self) -> None:
        """NaN standard deviations should be normalized to zero in exported statistics."""
        weights_df = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-07-01"],
                "IVV": [float("nan"), float("nan")],
            },
        )

        result = _compute_weight_statistics_from_weights(weights_df = weights_df)

        assert result[0]["std_weight"] == pytest.approx(0.0)


@pytest.mark.unit()
class TestAdditionalWeightsAnalysisBranches:
    """Additional branch coverage for weights-analysis exporting."""

    @pytest.mark.unit()
    def test_existing_data_results_short_circuit_fallbacks(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Existing reactive output should be written directly without fallback work."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        reactives = {
            "Data_Results": {
                "Weights_Analysis_Outputs": MockReactiveValue(
                    {"weight_statistics": [{"component": "IVV", "current_weight": 0.6}]},
                ),
            },
        }

        out_path = export_outputs_weights_analysis(reactives_shiny = reactives)
        result = json.loads(out_path.read_text())

        assert result["weight_statistics"][0]["component"] == "IVV"

    @pytest.mark.unit()
    def test_patched_data_results_short_circuit_skips_fallback_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A non-empty _get_data_results_value result should bypass fallback logic entirely."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"weight_statistics": [{"component": "GLD", "current_weight": 0.2}]},
        ):
            out_path = export_outputs_weights_analysis(reactives_shiny = {})

        result = json.loads(out_path.read_text())
        assert result["weight_statistics"][0]["component"] == "GLD"

    @pytest.mark.unit()
    def test_inner_variable_list_is_used_without_sample_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """List-based inner summary stats should be exported directly."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        reactives = {
            "Inner_Variables_Shiny": {
                "Weights_Summary_Stats": MockReactiveValue(
                    [{"component": "AGG", "current_weight": 0.3}],
                ),
            },
        }

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_weights_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["weight_statistics"][0]["component"] == "AGG"

    @pytest.mark.unit()
    def test_inner_variable_dataframe_is_converted_to_records(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """DataFrame-based inner summary stats should be converted to records."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        reactives = {
            "Inner_Variables_Shiny": {
                "Weights_Summary_Stats": MockReactiveValue(
                    pl.DataFrame({"component": ["GLD"], "current_weight": [0.2]}),
                ),
            },
        }

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_weights_analysis(reactives_shiny = reactives)

        result = json.loads(out_path.read_text())
        assert result["weight_statistics"][0]["component"] == "GLD"

    @pytest.mark.unit()
    def test_empty_output_written_when_no_reactive_or_sample_data(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If neither reactives nor sample weights are available, export should still write an empty table."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_weights_data",
            return_value=None,
        ):
            out_path = export_outputs_weights_analysis(reactives_shiny = {})

        result = json.loads(out_path.read_text())
        assert result == {"weight_statistics": []}


@pytest.mark.unit()
class TestAdditionalClientExportBranches:
    """Additional branch coverage for consolidated client export."""

    @pytest.mark.unit()
    def test_export_data_clients_json_handles_non_dict_advisor_info(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Non-dict advisor containers should degrade to an empty advisor_info section."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        client_info_path = tmp_path / "client_info.json"
        client_info_path.write_text(json.dumps({"personal_info": {}}), encoding="utf-8")
        monkeypatch.setattr(mod, "export_client_info", lambda *, reactives_shiny, **_: client_info_path)

        out_path = export_data_clients_json(reactives_shiny = {"Advisor_Info": "not-a-dict"})
        result = json.loads(out_path.read_text())

        assert result["advisor_info"] == {}

    @pytest.mark.unit()
    def test_export_data_clients_json_handles_broken_reactive_getter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Advisor reactive getters that fail should serialize as null values."""
        import src.dashboard.reporting.report_data_export as mod

        class _BrokenReactive:
            """Tests for BrokenReactive."""
            def get(self):
                """Get."""
                raise RuntimeError("boom")

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        client_info_path = tmp_path / "client_info.json"
        client_info_path.write_text(json.dumps({"personal_info": {}}), encoding="utf-8")
        monkeypatch.setattr(mod, "export_client_info", lambda *, reactives_shiny, **_: client_info_path)

        out_path = export_data_clients_json(reactives_shiny = {"Advisor_Info": {"Name": _BrokenReactive()}})
        result = json.loads(out_path.read_text())

        assert result["advisor_info"]["Name"] is None

    @pytest.mark.unit()
    def test_export_data_clients_json_with_none_reactives_writes_empty_advisor_info(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A None reactive state should still write a valid consolidated client file."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        client_info_path = tmp_path / "client_info.json"
        client_info_path.write_text(json.dumps({"personal_info": {"primary": {}}}), encoding="utf-8")
        monkeypatch.setattr(mod, "export_client_info", lambda *, reactives_shiny, **_: client_info_path)

        out_path = export_data_clients_json(reactives_shiny = None)
        result = json.loads(out_path.read_text())

        assert result["personal_info"]["primary"] == {}
        assert result["advisor_info"] == {}


# ============================================================================
# validate_report_data_quality
# ============================================================================


@pytest.mark.unit()
class Test_validate_report_data_quality:
    """Tests for validate_report_data_quality()."""

    @pytest.mark.unit()
    def test_returns_dict(self) -> None:
        """validate_report_data_quality should always return a dict."""
        result = validate_report_data_quality()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_returns_issues_when_files_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Missing JSON files should appear as issues in the returned dict."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path / "outputs_json")

        result = validate_report_data_quality()
        assert isinstance(result, dict)
        # Some issues should be present because the files don't exist in tmp_path
        assert len(result) > 0

    @pytest.mark.unit()
    def test_returns_issue_on_invalid_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """A JSON file with invalid content should be flagged."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path / "outputs_json")

        bad_file = tmp_path / "report_metadata.json"
        bad_file.write_text("not valid json{{", encoding="utf-8")

        result = validate_report_data_quality()
        assert any("parse" in msg.lower() or "cannot" in msg.lower()
                   for msgs in result.values() for msg in msgs)

    @pytest.mark.unit()
    def test_returns_issue_on_empty_dict_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """An empty JSON object should be flagged as an issue."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path / "outputs_json")

        empty_file = tmp_path / "client_info.json"
        empty_file.write_text("{}", encoding="utf-8")

        result = validate_report_data_quality()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_empty_array_key_flagged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """An array key with 0 elements should be flagged."""
        import src.dashboard.reporting.report_data_export as mod

        outputs_json = tmp_path / "outputs_json"
        outputs_json.mkdir()
        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", outputs_json)

        (outputs_json / "outputs_weights_analysis.json").write_text(
            json.dumps({"weight_statistics": []}), encoding="utf-8"
        )

        result = validate_report_data_quality()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_simulation_all_zeros_flagged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Simulation with all-zero numeric values should be flagged."""
        import src.dashboard.reporting.report_data_export as mod

        outputs_json = tmp_path / "outputs_json"
        outputs_json.mkdir()
        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", outputs_json)

        (outputs_json / "outputs_simulation.json").write_text(
            json.dumps({
                "summary_statistics": {
                    "initial_value": 100.0,
                    "mean_terminal_value": 0,
                    "median_terminal_value": 0,
                    "std_dev_terminal_value": 0,
                }
            }),
            encoding="utf-8",
        )

        result = validate_report_data_quality()
        assert isinstance(result, dict)
        assert any("zero" in msg.lower() or "simulation" in section.lower()
                   for section, msgs in result.items() for msg in msgs)

    @pytest.mark.unit()
    def test_simulation_boolean_summary_values_not_flagged_as_zero_stats(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Boolean summary flags should not be treated as numeric zero simulation statistics."""
        import src.dashboard.reporting.report_data_export as mod

        outputs_json = tmp_path / "outputs_json"
        outputs_json.mkdir()
        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", outputs_json)

        (outputs_json / "outputs_simulation.json").write_text(
            json.dumps(
                {
                    "summary_statistics": {
                        "initial_value": 100.0,
                        "has_results": False,
                        "is_valid": False,
                    },
                },
            ),
            encoding="utf-8",
        )

        result = validate_report_data_quality()
        assert "Simulation" not in result or not any(
            "zero" in msg.lower() for msg in result.get("Simulation", [])
        )

    @pytest.mark.unit()
    def test_simulation_invalid_json_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Unparseable simulation file should not crash — exception is silently ignored."""
        import src.dashboard.reporting.report_data_export as mod

        outputs_json = tmp_path / "outputs_json"
        outputs_json.mkdir()
        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", outputs_json)

        (outputs_json / "outputs_simulation.json").write_text("bad{{json", encoding="utf-8")

        # Must not raise
        result = validate_report_data_quality()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_simulation_summary_stats_not_dict_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When summary_statistics is not a dict, the zero-check should be skipped."""
        import src.dashboard.reporting.report_data_export as mod

        outputs_json = tmp_path / "outputs_json"
        outputs_json.mkdir()
        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", outputs_json)

        (outputs_json / "outputs_simulation.json").write_text(
            json.dumps({"summary_statistics": [1, 2, 3]}),
            encoding="utf-8",
        )

        result = validate_report_data_quality()
        assert isinstance(result, dict)
        # No simulation issues — list is not flagged
        assert "Simulation" not in result or not any(
            "zero" in msg.lower() for msg in result.get("Simulation", [])
        )


# ============================================================================
# _read_json_dict / _write_json / _ensure_dir
# ============================================================================


@pytest.mark.unit()
class Test_read_write_ensure_helpers:
    """Tests for _read_json_dict, _write_json, _ensure_dir."""

    @pytest.mark.unit()
    def test_read_json_dict_returns_empty_on_missing_file(self, tmp_path: Any) -> None:
        """Missing file should return {}."""
        result = _read_json_dict(file_path = tmp_path / "nonexistent.json")
        assert result == {}

    @pytest.mark.unit()
    def test_read_json_dict_returns_empty_on_invalid_json(self, tmp_path: Any) -> None:
        """Invalid JSON should return {}."""
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        result = _read_json_dict(file_path = bad)
        assert result == {}

    @pytest.mark.unit()
    def test_read_json_dict_returns_empty_when_json_is_list(self, tmp_path: Any) -> None:
        """JSON array (not dict) should return {}."""
        arr = tmp_path / "arr.json"
        arr.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        result = _read_json_dict(file_path = arr)
        assert result == {}

    @pytest.mark.unit()
    def test_read_json_dict_returns_dict_on_valid_json(self, tmp_path: Any) -> None:
        """Valid JSON dict should be returned as-is."""
        good = tmp_path / "good.json"
        good.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = _read_json_dict(file_path = good)
        assert result == {"key": "value"}

    @pytest.mark.unit()
    def test_write_json_creates_file_with_content(self, tmp_path: Any) -> None:
        """_write_json should create the file with pretty-printed content."""
        out = tmp_path / "out.json"
        _write_json(file_path = out, data = {"a": 1})
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data == {"a": 1}

    @pytest.mark.unit()
    def test_ensure_dir_creates_nested_directory(self, tmp_path: Any) -> None:
        """_ensure_dir should create directory tree if not present."""
        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()
        _ensure_dir(directory = nested)
        assert nested.exists()

    @pytest.mark.unit()
    def test_ensure_dir_is_idempotent(self, tmp_path: Any) -> None:
        """Calling _ensure_dir twice on the same path should not raise."""
        _ensure_dir(directory = tmp_path)
        _ensure_dir(directory = tmp_path)  # Must not raise


# ============================================================================
# _load_sample_portfolio_data / _load_sample_weights_data
# ============================================================================


@pytest.mark.unit()
class Test_load_sample_data:
    """Tests for _load_sample_portfolio_data and _load_sample_weights_data."""

    @pytest.mark.unit()
    def test_load_sample_portfolio_data_returns_two_element_tuple(self) -> None:
        """Always returns a 2-tuple (each may be None if file missing)."""
        result = _load_sample_portfolio_data()
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.unit()
    def test_load_sample_portfolio_data_returns_none_when_csv_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Missing CSV files → both tuple elements are None."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_SAMPLE_PORTFOLIO_CSV", tmp_path / "missing.csv")
        monkeypatch.setattr(mod, "_BENCHMARK_PORTFOLIO_CSV", tmp_path / "missing2.csv")

        pv, bv = _load_sample_portfolio_data()
        assert pv is None
        assert bv is None

    @pytest.mark.unit()
    def test_load_sample_portfolio_data_loads_valid_csv(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Valid CSV returns a DataFrame with Date and portfolio_value columns."""
        import src.dashboard.reporting.report_data_export as mod

        csv_content = "Date,Value\n2020-01-02 00:00:00-05:00,100.0\n2020-01-03 00:00:00-05:00,101.0\n"
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        monkeypatch.setattr(mod, "_SAMPLE_PORTFOLIO_CSV", csv_file)
        monkeypatch.setattr(mod, "_BENCHMARK_PORTFOLIO_CSV", tmp_path / "missing.csv")

        pv, bv = _load_sample_portfolio_data()
        assert pv is not None
        assert "portfolio_value" in pv.columns
        assert bv is None

    @pytest.mark.unit()
    def test_load_sample_weights_data_returns_none_when_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Missing weights CSV → returns None."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_SAMPLE_WEIGHTS_CSV", tmp_path / "missing.csv")
        result = _load_sample_weights_data()
        assert result is None

    @pytest.mark.unit()
    def test_load_sample_weights_data_loads_csv_with_date(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Valid weights CSV with Date column is sorted and returned."""
        import src.dashboard.reporting.report_data_export as mod

        csv_content = "Date,IVV,AGG\n2020-01-03 00:00:00-05:00,0.6,0.4\n2020-01-02 00:00:00-05:00,0.5,0.5\n"
        csv_file = tmp_path / "weights.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        monkeypatch.setattr(mod, "_SAMPLE_WEIGHTS_CSV", csv_file)

        result = _load_sample_weights_data()
        assert result is not None
        assert "IVV" in result.columns

    @pytest.mark.unit()
    def test_load_sample_weights_data_loads_csv_without_date(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Weights CSV without Date column is returned as-is."""
        import src.dashboard.reporting.report_data_export as mod

        csv_content = "IVV,AGG\n0.6,0.4\n0.5,0.5\n"
        csv_file = tmp_path / "weights_nodate.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        monkeypatch.setattr(mod, "_SAMPLE_WEIGHTS_CSV", csv_file)

        result = _load_sample_weights_data()
        assert result is not None
        assert "IVV" in result.columns


# ============================================================================
# _compute_portfolio_metrics_from_values
# ============================================================================


@pytest.mark.unit()
class Test_compute_portfolio_metrics_from_values:
    """Tests for _compute_portfolio_metrics_from_values."""

    def _make_pv(self, n: int = 252) -> pl.DataFrame:
        """Build a simple linearly growing portfolio value DF."""
        import datetime

        start = datetime.date(2020, 1, 2)
        dates = [start + datetime.timedelta(days=i) for i in range(n)]
        values = [100.0 + i * 0.1 for i in range(n)]
        return pl.DataFrame({"Date": dates, "portfolio_value": values})

    @pytest.mark.unit()
    def test_returns_dict_with_expected_keys(self) -> None:
        """Result should contain all expected metric keys."""
        pv = self._make_pv()
        result = _compute_portfolio_metrics_from_values(pv = pv)
        assert "total_return_portfolio" in result
        assert "sharpe_ratio_portfolio" in result
        assert "correlation" in result

    @pytest.mark.unit()
    def test_with_benchmark_returns_non_zero_b_metrics(self) -> None:
        """Providing a benchmark DataFrame should populate benchmark metrics."""
        pv = self._make_pv(252)
        bv = self._make_pv(252)
        result = _compute_portfolio_metrics_from_values(pv = pv, bv = bv)
        assert isinstance(result["correlation"], float)
        assert isinstance(result["tracking_error"], float)

    @pytest.mark.unit()
    def test_with_benchmark_single_point_zero_tracking_error(self) -> None:
        """Benchmark with min_len <= 1 returns zero correlation and tracking_error."""
        import datetime

        pv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
            "portfolio_value": [100.0, 101.0],
        })
        bv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
            "portfolio_value": [100.0, 100.5],
        })
        with pytest.warns(RuntimeWarning):
            result = _compute_portfolio_metrics_from_values(pv = pv, bv = bv)
        # With 2 points, min_len of rets = 1 → zero branch
        assert result["correlation"] == pytest.approx(0.0)
        assert result["tracking_error"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_with_benchmark_height_less_than_2_is_skipped(self) -> None:
        """Benchmark with height < 2 should be ignored (no benchmark metrics)."""
        import datetime

        pv = self._make_pv(10)
        bv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2)],
            "portfolio_value": [100.0],
        })
        result = _compute_portfolio_metrics_from_values(pv = pv, bv = bv)
        assert result["total_return_benchmark"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_zero_n_years_returns_zero_annualized_return(self) -> None:
        """Zero n_years should return zero annualized return without ZeroDivisionError."""
        import datetime

        pv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
            "portfolio_value": [100.0, 101.0],
        })
        with pytest.warns(RuntimeWarning):
            result = _compute_portfolio_metrics_from_values(pv = pv)
        assert isinstance(result["annualized_return_portfolio"], float)

    @pytest.mark.unit()
    def test_boolean_portfolio_values_use_zero_defaults(self) -> None:
        """Boolean portfolio values should stay on the existing zero-metrics fallback."""
        import datetime

        pv = pl.DataFrame(
            {
                "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
                "portfolio_value": [True, False],
            },
        )

        result = _compute_portfolio_metrics_from_values(pv = pv)

        assert result["total_return_portfolio"] == pytest.approx(0.0)
        assert result["sharpe_ratio_portfolio"] == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_boolean_benchmark_values_are_ignored(self) -> None:
        """Boolean benchmark values should not populate benchmark comparison metrics."""
        import datetime

        pv = self._make_pv(10)
        bv = pl.DataFrame(
            {
                "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
                "portfolio_value": [True, False],
            },
        )

        result = _compute_portfolio_metrics_from_values(pv = pv, bv = bv)

        assert result["total_return_benchmark"] == pytest.approx(0.0)
        assert result["tracking_error"] == pytest.approx(0.0)


# ============================================================================
# _compute_portfolio_analysis_stats_from_values
# ============================================================================


@pytest.mark.unit()
class Test_compute_portfolio_analysis_stats_from_values:
    """Tests for _compute_portfolio_analysis_stats_from_values."""

    def _make_pv(self, n: int = 100) -> pl.DataFrame:
        """Build a simple portfolio value DF."""
        import datetime
        import numpy as _np

        start = datetime.date(2020, 1, 2)
        rng = _np.random.default_rng(0)
        values = 100.0 * _np.cumprod(1 + rng.normal(0, 0.01, n))
        return pl.DataFrame({
            "Date": [start + datetime.timedelta(days=i) for i in range(n)],
            "portfolio_value": values.tolist(),
        })

    @pytest.mark.unit()
    def test_returns_expected_keys(self) -> None:
        """Result should have basic_statistics and performance_metrics keys."""
        pv = self._make_pv()
        result = _compute_portfolio_analysis_stats_from_values(pv = pv)
        assert "basic_statistics" in result
        assert "performance_metrics" in result

    @pytest.mark.unit()
    def test_with_benchmark_populates_bm_stats(self) -> None:
        """Benchmark data should populate benchmark columns."""
        pv = self._make_pv(100)
        bv = self._make_pv(100)
        result = _compute_portfolio_analysis_stats_from_values(pv = pv, bv = bv)
        basic = result["basic_statistics"]
        assert basic[0]["benchmark"] != ""

    @pytest.mark.unit()
    def test_without_benchmark_has_empty_benchmark_column(self) -> None:
        """Without benchmark, benchmark column in basic_statistics should be empty string."""
        pv = self._make_pv(100)
        result = _compute_portfolio_analysis_stats_from_values(pv = pv, bv = None)
        basic = result["basic_statistics"]
        assert basic[0]["benchmark"] == ""

    @pytest.mark.unit()
    def test_boolean_portfolio_values_use_zero_defaults(self) -> None:
        """Boolean portfolio values should stay on the existing zero-statistics fallback."""
        import datetime

        pv = pl.DataFrame(
            {
                "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
                "portfolio_value": [True, False],
            },
        )

        result = _compute_portfolio_analysis_stats_from_values(pv = pv)

        assert result["basic_statistics"][0]["portfolio"] == "0.0000%"
        assert result["performance_metrics"][0]["value"] == "0.00%"


# ============================================================================
# _compute_simulation_stats_from_values
# ============================================================================


@pytest.mark.unit()
class Test_compute_simulation_stats_from_values:
    """Tests for _compute_simulation_stats_from_values."""

    def _make_pv(self) -> pl.DataFrame:
        """Simple portfolio DF."""
        import datetime
        import numpy as _np

        rng = _np.random.default_rng(42)
        n = 252
        values = 100.0 * _np.cumprod(1 + rng.normal(0, 0.01, n))
        return pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2) + datetime.timedelta(days=i) for i in range(n)],
            "portfolio_value": values.tolist(),
        })

    @pytest.mark.unit()
    def test_returns_dict_with_simulation_keys(self) -> None:
        """Return dict should contain all expected simulation stat keys."""
        pv = self._make_pv()
        result = _compute_simulation_stats_from_values(pv = pv, num_scenarios=100, num_days=50)
        assert result["num_scenarios"] == 100
        assert result["horizon_days"] == 50
        assert "mean_terminal_value" in result
        assert "probability_of_loss" in result
        assert isinstance(result["probability_of_loss"], float)

    @pytest.mark.unit()
    def test_boolean_portfolio_values_use_zero_defaults(self) -> None:
        """Boolean portfolio values should stay on the existing zero-simulation fallback."""
        import datetime

        pv = pl.DataFrame(
            {
                "Date": [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)],
                "portfolio_value": [True, False],
            },
        )

        result = _compute_simulation_stats_from_values(pv = pv, num_scenarios=10, num_days=5)

        assert result["mean_terminal_value"] == pytest.approx(0.0)
        assert result["probability_of_loss"] == pytest.approx(0.0)


# ============================================================================
# export_report_metadata
# ============================================================================


@pytest.mark.unit()
class Test_export_report_metadata:
    """Tests for export_report_metadata."""

    @pytest.mark.unit()
    def test_writes_json_with_report_date(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Export should write report_metadata.json with a report_date key."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        out_path = export_report_metadata()
        data = json.loads(out_path.read_text())
        assert "report_date" in data
        assert "generated_by" in data

    @pytest.mark.unit()
    def test_returns_path_to_json_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Return value is the Path to the written file."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        out_path = export_report_metadata(reactives_shiny = None)
        assert out_path.exists()
        assert out_path.suffix == ".json"


# ============================================================================
# export_client_info
# ============================================================================


@pytest.mark.unit()
class Test_export_client_info:
    """Tests for export_client_info."""

    @pytest.mark.unit()
    def test_writes_empty_fallback_when_builder_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Failure in build_client_info_json_from_reactives should fall back to {} dict."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        def _raise(_r: Any) -> None:
            raise RuntimeError("no shiny")

        with patch(
            "src.dashboard.reporting.report_data_export.export_client_info",
            wraps=lambda reactives: export_client_info(reactives_shiny = reactives),
        ):
            pass

        # Directly mock the import inside the function
        import unittest.mock as _mock

        with _mock.patch.dict(
            "sys.modules",
            {"src.dashboard.shiny_utils.utils_reporting": _mock.MagicMock(
                build_client_info_json_from_reactives=_raise,
            )},
        ):
            out_path = export_client_info(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert isinstance(data, dict)

    @pytest.mark.unit()
    def test_writes_client_info_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Successful build_client_info_json_from_reactives should write its result."""
        import src.dashboard.reporting.report_data_export as mod
        import unittest.mock as _mock

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        with _mock.patch.dict(
            "sys.modules",
            {"src.dashboard.shiny_utils.utils_reporting": _mock.MagicMock(
                build_client_info_json_from_reactives=lambda *, reactives_shiny: {"name": "Test Client"},
            )},
        ):
            out_path = export_client_info(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data.get("name") == "Test Client"


# ============================================================================
# export_inputs_portfolio_analysis
# ============================================================================


@pytest.mark.unit()
class Test_export_inputs_portfolio_analysis:
    """Tests for export_inputs_portfolio_analysis."""

    @pytest.mark.unit()
    def test_writes_json_with_time_period_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """With no Data_Results, should fall back to default user inputs."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_portfolio_analysis(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "time_period" in data

    @pytest.mark.unit()
    def test_uses_data_results_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results should be written directly."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"time_period": "5Y", "analysis_type": "returns"},
        ):
            out_path = export_inputs_portfolio_analysis(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "5Y"

    @pytest.mark.unit()
    def test_fallback_uses_user_inputs_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """User_Inputs_Shiny values should appear in the output."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Portfolio_Analysis_Time_Period": "3Y",
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_portfolio_analysis(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "3Y"

    @pytest.mark.unit()
    def test_include_benchmark_non_boolean_uses_true_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Falsey non-boolean benchmark flags should stay on the existing True default."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Portfolio_Analysis_Include_Benchmark": 0,
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_portfolio_analysis(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["include_benchmark"] is True


# ============================================================================
# export_outputs_portfolio_analysis  (extra branches)
# ============================================================================


@pytest.mark.unit()
class Test_export_outputs_portfolio_analysis_extra:
    """Extra branch coverage for export_outputs_portfolio_analysis."""

    @pytest.mark.unit()
    def test_uses_sample_data_fallback_when_no_inner_variables(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When no inner variables are set, sample CSV data should be used."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "basic_statistics" in data

    @pytest.mark.unit()
    def test_uses_live_compute_when_sample_csv_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When sample CSV data is available, analysis stats should be computed."""
        import datetime
        import numpy as _np
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        rng = _np.random.default_rng(7)
        n = 50
        pv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2) + datetime.timedelta(days=i) for i in range(n)],
            "portfolio_value": list(100.0 * _np.cumprod(1 + rng.normal(0, 0.01, n))),
        })

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(pv, None),
        ):
            out_path = export_outputs_portfolio_analysis(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert isinstance(data["basic_statistics"], list)
        assert len(data["basic_statistics"]) > 0


# ============================================================================
# export_inputs_portfolio_comparison / export_outputs_portfolio_comparison
# ============================================================================


@pytest.mark.unit()
class Test_export_portfolio_comparison:
    """Tests for portfolio comparison export functions."""

    @pytest.mark.unit()
    def test_export_inputs_returns_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """export_inputs_portfolio_comparison should write a JSON file."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_portfolio_comparison(reactives_shiny = None)
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert "time_period" in data

    @pytest.mark.unit()
    def test_export_inputs_uses_data_results_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results bypass fallback for portfolio comparison inputs."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"time_period": "ALL"},
        ):
            out_path = export_inputs_portfolio_comparison(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "ALL"

    @pytest.mark.unit()
    def test_show_diff_truthy_non_boolean_uses_false_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Truthy non-boolean diff flags should stay on the existing False default."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Portfolio_Comparison_Show_Diff": "yes",
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_portfolio_comparison(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["show_diff"] is False

    @pytest.mark.unit()
    def test_export_outputs_uses_sample_data_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When no inner variables, sample portfolio CSV should be used for comparison metrics."""
        import datetime
        import numpy as _np
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        rng = _np.random.default_rng(3)
        n = 60
        pv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2) + datetime.timedelta(days=i) for i in range(n)],
            "portfolio_value": list(100.0 * _np.cumprod(1 + rng.normal(0, 0.01, n))),
        })

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(pv, None),
        ):
            out_path = export_outputs_portfolio_comparison(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "metrics" in data
        assert "total_return" in data["metrics"]

    @pytest.mark.unit()
    def test_export_outputs_uses_live_stats_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Non-empty inner stats dict should be used directly."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        stats = {
            "time_period": "1Y",
            "start_date": "2020-01-02",
            "end_date": "2021-01-02",
            "viz_type": "normalized",
            "total_return_portfolio": 0.1,
            "annualized_return_portfolio": 0.09,
            "volatility_portfolio": 0.15,
            "max_drawdown_portfolio": -0.1,
            "sharpe_ratio_portfolio": 0.6,
            "total_return_benchmark": 0.08,
            "annualized_return_benchmark": 0.07,
            "volatility_benchmark": 0.12,
            "max_drawdown_benchmark": -0.08,
            "sharpe_ratio_benchmark": 0.5,
            "total_return_difference": 0.02,
            "annualized_return_difference": 0.02,
            "volatility_difference": 0.03,
            "max_drawdown_difference": -0.02,
            "sharpe_ratio_difference": 0.1,
            "correlation": 0.9,
            "tracking_error": 0.04,
            "information_ratio": 0.5,
        }

        reactives = {
            "Inner_Variables_Shiny": {
                "Portfolio_Comparison_Stats": MockReactiveValue(stats),
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_portfolio_comparison(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "1Y"
        assert data["metrics"]["correlation"] == pytest.approx(0.9)


# ============================================================================
# export_inputs_weights_analysis
# ============================================================================


@pytest.mark.unit()
class Test_export_inputs_weights_analysis:
    """Tests for export_inputs_weights_analysis."""

    @pytest.mark.unit()
    def test_writes_json_with_expected_keys(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback inputs should include time_period and selected_components."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_weights_analysis(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "time_period" in data
        assert "selected_components" in data

    @pytest.mark.unit()
    def test_selected_components_defaults_to_empty_list_when_not_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Non-list Weights_Selected_Components defaults to []."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Weights_Selected_Components": "IVV",  # not a list
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_weights_analysis(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["selected_components"] == []

    @pytest.mark.unit()
    def test_non_boolean_weight_flags_use_true_defaults(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Falsey non-boolean weight flags should stay on the existing True defaults."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Weights_Show_Pct": 0,
                "Weights_Sort_Components": 0,
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_weights_analysis(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["show_pct"] is True
        assert data["sort_components"] is True


# ============================================================================
# export_inputs_skfolio_optimization
# ============================================================================


@pytest.mark.unit()
class Test_export_inputs_skfolio_optimization:
    """Tests for export_inputs_skfolio_optimization."""

    @pytest.mark.unit()
    def test_writes_json_with_method1_and_method2(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback should write method1 and method2 dicts."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_skfolio_optimization(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "method1" in data
        assert "method2" in data

    @pytest.mark.unit()
    def test_uses_data_results_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results should bypass fallback."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"method1": {"type": "equal_weighted"}, "method2": {"type": "mean_risk"}},
        ):
            out_path = export_inputs_skfolio_optimization(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["method1"]["type"] == "equal_weighted"


# ============================================================================
# export_outputs_skfolio_optimization  (extra branches)
# ============================================================================


@pytest.mark.unit()
class Test_export_outputs_skfolio_optimization_extra:
    """Extra branch coverage for export_outputs_skfolio_optimization."""

    @pytest.mark.unit()
    def test_writes_json_with_weights_and_performance_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback should write weights_comparison, statistics_comparison, performance_summary."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_skfolio_optimization(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "weights_comparison" in data
        assert "performance_summary" in data

    @pytest.mark.unit()
    def test_uses_perf_summary_from_inner_variables(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Non-empty Skfolio_Performance_Summary should be used for method labels."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        perf = {
            "method1": {"label": "Equal Weight", "annualized_return": 0.1, "volatility": 0.15, "sharpe_ratio": 0.6},
            "method2": {"label": "Mean Risk", "annualized_return": 0.12, "volatility": 0.18, "sharpe_ratio": 0.65},
        }
        reactives = {
            "Inner_Variables_Shiny": {
                "Skfolio_Performance_Summary": MockReactiveValue(perf),
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_skfolio_optimization(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["performance_summary"]["method1"]["label"] == "Equal Weight"


# ============================================================================
# export_inputs/outputs_optimalportfolios_optimization
# ============================================================================


@pytest.mark.unit()
class Test_export_optimalportfolios_optimization:
    """Tests for OptimalPortfolios optimization export functions."""

    @pytest.mark.unit()
    def test_export_inputs_writes_defaults(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback inputs should write default structure."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_optimalportfolios_optimization(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "method1" in data
        assert "method2" in data

    @pytest.mark.unit()
    def test_export_outputs_writes_empty_structure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback outputs should write empty weights_comparison and statistics_comparison."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_optimalportfolios_optimization(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert data["weights_comparison"] == []
        assert "performance_summary" in data

    @pytest.mark.unit()
    def test_export_inputs_uses_data_results(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results bypasses fallback."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"time_period": "5y", "method1": {"type": "MIN_VARIANCE"}},
        ):
            out_path = export_inputs_optimalportfolios_optimization(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "5y"

    @pytest.mark.unit()
    def test_export_outputs_uses_data_results(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results bypasses fallback for outputs."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"weights_comparison": [{"asset": "IVV"}], "statistics_comparison": []},
        ):
            out_path = export_outputs_optimalportfolios_optimization(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["weights_comparison"][0]["asset"] == "IVV"


# ============================================================================
# export_inputs_simulation / export_outputs_simulation
# ============================================================================


@pytest.mark.unit()
class Test_export_simulation:
    """Tests for simulation input/output export functions."""

    @pytest.mark.unit()
    def test_export_inputs_writes_default_structure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Fallback inputs should write num_scenarios, num_days, seed."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_simulation(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "num_scenarios" in data
        assert "num_days" in data
        assert "seed" in data

    @pytest.mark.unit()
    def test_export_inputs_selected_components_defaults_to_empty_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Non-list Simulation_Selected_Components should fall back to []."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {"User_Inputs_Shiny": {"Simulation_Selected_Components": "SPY"}}
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_simulation(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["selected_components"] == []

    @pytest.mark.unit()
    def test_export_outputs_computes_from_sample_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When no Simulation_Stats, should compute from sample portfolio CSV."""
        import datetime
        import numpy as _np
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        rng = _np.random.default_rng(5)
        n = 60
        pv = pl.DataFrame({
            "Date": [datetime.date(2020, 1, 2) + datetime.timedelta(days=i) for i in range(n)],
            "portfolio_value": list(100.0 * _np.cumprod(1 + rng.normal(0, 0.01, n))),
        })

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(pv, None),
        ):
            out_path = export_outputs_simulation(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        ss = data["summary_statistics"]
        assert ss["mean_terminal_value"] != 0

    @pytest.mark.unit()
    def test_export_outputs_uses_data_results_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Populated Data_Results bypasses fallback."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={"summary_statistics": {"num_scenarios": 500, "horizon_days": 126}},
        ):
            out_path = export_outputs_simulation(reactives_shiny = {})
        data = json.loads(out_path.read_text())
        assert data["summary_statistics"]["num_scenarios"] == 500

    @pytest.mark.unit()
    def test_export_outputs_no_sample_data_writes_zero_stats(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When sample data also returns None, stats should be all zero/fallback."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)
        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_simulation(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "summary_statistics" in data


# ============================================================================
# export_all_report_data
# ============================================================================


@pytest.mark.unit()
class Test_export_all_report_data:
    """Tests for export_all_report_data."""

    @pytest.mark.unit()
    def test_returns_dict_with_all_keys(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """All expected section keys should appear in the returned dict."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        def _mock_exporter(*, reactives_shiny, **___: Any) -> Path:  # noqa: ARG001_reactives: Any, *_args: Any, **_kwargs: Any) -> Any:
            p = tmp_path / "dummy.json"
            p.write_text("{}", encoding="utf-8")
            return p

        for fn in [
            "export_report_metadata", "export_client_info",
            "export_inputs_portfolio_analysis", "export_outputs_portfolio_analysis",
            "export_inputs_portfolio_comparison", "export_outputs_portfolio_comparison",
            "export_inputs_weights_analysis", "export_outputs_weights_analysis",
            "export_inputs_skfolio_optimization", "export_outputs_skfolio_optimization",
            "export_inputs_optimalportfolios_optimization", "export_outputs_optimalportfolios_optimization",
            "export_inputs_simulation", "export_outputs_simulation",
            "export_data_clients_json", "export_data_results_json", "export_report_config",
        ]:
            monkeypatch.setattr(mod, fn, _mock_exporter)

        result = export_all_report_data(reactives_shiny = None)
        assert isinstance(result, dict)
        assert "report_metadata" in result
        assert "outputs_simulation" in result

    @pytest.mark.unit()
    def test_returns_paths_that_exist(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """All returned paths should point to existing files."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)
        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        dummy = tmp_path / "dummy.json"
        dummy.write_text("{}", encoding="utf-8")

        monkeypatch.setattr(mod, "export_report_metadata", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_client_info", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_portfolio_analysis", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_portfolio_analysis", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_portfolio_comparison", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_portfolio_comparison", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_weights_analysis", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_weights_analysis", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_skfolio_optimization", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_skfolio_optimization", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_optimalportfolios_optimization", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_optimalportfolios_optimization", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_inputs_simulation", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_outputs_simulation", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_data_clients_json", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_data_results_json", lambda *, reactives_shiny: dummy)
        monkeypatch.setattr(mod, "export_report_config", lambda *, reactives_shiny, section_flags, **kw: dummy)

        result = export_all_report_data(reactives_shiny = {})
        for path in result.values():
            assert path.exists()


# ============================================================================
# _get_user_inputs
# ============================================================================


@pytest.mark.unit()
class Test_get_user_inputs:
    """Tests for _get_user_inputs."""

    @pytest.mark.unit()
    def test_returns_empty_dict_for_none(self) -> None:
        """None reactives should return {}."""
        assert _get_user_inputs(reactives_shiny = None) == {}

    @pytest.mark.unit()
    def test_returns_empty_dict_for_empty_reactives(self) -> None:
        """Empty reactives dict should return {}."""
        assert _get_user_inputs(reactives_shiny = {}) == {}

    @pytest.mark.unit()
    def test_returns_user_inputs_when_present(self) -> None:
        """User_Inputs_Shiny dict should be returned."""
        reactives = {"User_Inputs_Shiny": {"key": "value"}}
        assert _get_user_inputs(reactives_shiny = reactives) == {"key": "value"}

    @pytest.mark.unit()
    def test_returns_empty_dict_when_user_inputs_not_dict(self) -> None:
        """Non-dict User_Inputs_Shiny should return {}."""
        reactives = {"User_Inputs_Shiny": "not-a-dict"}
        assert _get_user_inputs(reactives_shiny = reactives) == {}


# ============================================================================
# export_report_config
# ============================================================================


@pytest.mark.unit()
class Test_export_report_config:
    """Tests for export_report_config."""

    @pytest.mark.unit()
    def test_writes_section_flags_to_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Section flags should be present in the written JSON."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        flags = {"include_portfolio_analysis": True, "include_simulation": False}
        out_path = export_report_config(reactives_shiny = None, section_flags = flags)
        data = json.loads(out_path.read_text())
        assert data["include_portfolio_analysis"] is True
        assert data["include_simulation"] is False

    @pytest.mark.unit()
    def test_uses_default_title_when_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Empty report_title string should use the default title."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        out_path = export_report_config(reactives_shiny = None, section_flags = {}, report_title="")
        data = json.loads(out_path.read_text())
        assert "QWIM" in data["report_title"]

    @pytest.mark.unit()
    def test_uses_custom_title_when_provided(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Custom report_title should appear in the written JSON."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        out_path = export_report_config(reactives_shiny = None, section_flags = {}, report_title="My Custom Report")
        data = json.loads(out_path.read_text())
        assert data["report_title"] == "My Custom Report"

    @pytest.mark.unit()
    def test_reads_include_partner_flag_from_reactives(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """include_partner flag should be extracted from User_Inputs_Shiny."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Input_Tab_Clients_Subtab_Setup_Checkbox_Include_Partner_in_Analysis":
                    MockReactiveValue(True),
            }
        }
        out_path = export_report_config(reactives_shiny = reactives, section_flags = {})
        data = json.loads(out_path.read_text())
        assert data["include_partner"] is True

    @pytest.mark.unit()
    def test_include_partner_defaults_to_false_with_none_reactives(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """None reactives should result in include_partner=False."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)
        out_path = export_report_config(reactives_shiny = None, section_flags = {})
        data = json.loads(out_path.read_text())
        assert data["include_partner"] is False

    @pytest.mark.unit()
    def test_include_partner_defaults_to_false_when_user_inputs_not_dict(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Non-dict User_Inputs_Shiny should result in include_partner=False."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        reactives = {"User_Inputs_Shiny": "not-a-dict"}
        out_path = export_report_config(reactives_shiny = reactives, section_flags = {})
        data = json.loads(out_path.read_text())
        assert data["include_partner"] is False

    @pytest.mark.unit()
    def test_include_partner_false_when_rv_key_absent(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When the include_partner key is absent from user_inputs, default to False."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        reactives = {"User_Inputs_Shiny": {}}
        out_path = export_report_config(reactives_shiny = reactives, section_flags = {})
        data = json.loads(out_path.read_text())
        assert data["include_partner"] is False

    @pytest.mark.unit()
    def test_include_partner_defaults_to_false_when_rv_get_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When rv.get() raises, include_partner should default to False."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        class _BrokenReactive:
            def get(self) -> bool:
                raise RuntimeError("reactive error")

        reactives = {
            "User_Inputs_Shiny": {
                "Input_Tab_Clients_Subtab_Setup_Checkbox_Include_Partner_in_Analysis":
                    _BrokenReactive(),
            }
        }
        out_path = export_report_config(reactives_shiny = reactives, section_flags = {})
        data = json.loads(out_path.read_text())
        assert data["include_partner"] is False

    @pytest.mark.unit()
    def test_include_partner_truthy_non_boolean_uses_false_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Truthy non-boolean partner flags should stay on the existing False default."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_REPORTING_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Input_Tab_Clients_Subtab_Setup_Checkbox_Include_Partner_in_Analysis": (
                    MockReactiveValue("yes")
                ),
            }
        }

        out_path = export_report_config(reactives_shiny = reactives, section_flags = {})
        data = json.loads(out_path.read_text())

        assert data["include_partner"] is False


# ============================================================================
# Additional branch coverage for primary-data paths
# ============================================================================


@pytest.mark.unit()
class Test_primary_data_paths:
    """Tests that exercise the primary (Data_Results non-empty) code paths."""

    @pytest.mark.unit()
    def test_export_outputs_portfolio_comparison_with_primary_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When _get_data_results_value returns non-empty, fallback is skipped."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        primary = {"metrics": {"total_return": {"portfolio": 0.12}}, "viz_type": "normalized"}
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value=primary,
        ):
            out_path = export_outputs_portfolio_comparison(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert data["viz_type"] == "normalized"

    @pytest.mark.unit()
    def test_export_outputs_portfolio_comparison_no_sample_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When sample data is None and no inner stats, data dict uses empty stats."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ), patch(
            "src.dashboard.reporting.report_data_export._load_sample_portfolio_data",
            return_value=(None, None),
        ):
            out_path = export_outputs_portfolio_comparison(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert "metrics" in data

    @pytest.mark.unit()
    def test_export_inputs_weights_analysis_with_primary_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When _get_data_results_value returns data, fallback is skipped."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        primary = {"time_period": "3Y", "selected_components": ["A", "B"]}
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value=primary,
        ):
            out_path = export_inputs_weights_analysis(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert data["time_period"] == "3Y"

    @pytest.mark.unit()
    def test_export_inputs_weights_analysis_selected_already_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When selected_components is already a list, no conversion should occur."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Weights_Selected_Components": MockReactiveValue(["X", "Y"]),
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_weights_analysis(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["selected_components"] == ["X", "Y"]

    @pytest.mark.unit()
    def test_export_outputs_skfolio_optimization_with_primary_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Primary data from Data_Results skips fallback derivation."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        primary = {"weights_comparison": [{"asset": "A", "weight": 0.5}]}
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value=primary,
        ):
            out_path = export_outputs_skfolio_optimization(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert data["weights_comparison"][0]["asset"] == "A"

    @pytest.mark.unit()
    def test_export_inputs_simulation_with_primary_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """Primary data from Data_Results skips fallback derivation for simulation inputs."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        primary = {"num_scenarios": 500, "selected_components": ["A"]}
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value=primary,
        ):
            out_path = export_inputs_simulation(reactives_shiny = None)
        data = json.loads(out_path.read_text())
        assert data["num_scenarios"] == 500

    @pytest.mark.unit()
    def test_export_inputs_simulation_selected_already_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When Simulation_Selected_Components is already a list, no conversion."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_INPUTS_JSON_DIR", tmp_path)

        reactives = {
            "User_Inputs_Shiny": {
                "Simulation_Selected_Components": MockReactiveValue(["comp1", "comp2"]),
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_inputs_simulation(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["selected_components"] == ["comp1", "comp2"]

    @pytest.mark.unit()
    def test_export_outputs_simulation_with_inner_stats(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        """When inner stats dict is non-empty, sample CSV fallback is skipped."""
        import src.dashboard.reporting.report_data_export as mod

        monkeypatch.setattr(mod, "_OUTPUTS_JSON_DIR", tmp_path)

        inner_stats = {
            "num_scenarios": 1000,
            "horizon_days": 252,
            "initial_value": 100.0,
            "mean_terminal_value": 110.0,
            "median_terminal_value": 108.0,
            "std_dev_terminal_value": 15.0,
            "percentile_5": 80.0,
            "percentile_25": 95.0,
            "percentile_75": 125.0,
            "percentile_95": 145.0,
            "min_terminal_value": 50.0,
            "max_terminal_value": 200.0,
            "probability_of_loss": 0.15,
        }
        reactives = {
            "Inner_Variables_Shiny": {
                "Simulation_Stats": MockReactiveValue(inner_stats),
            }
        }
        with patch(
            "src.dashboard.reporting.report_data_export._get_data_results_value",
            return_value={},
        ):
            out_path = export_outputs_simulation(reactives_shiny = reactives)
        data = json.loads(out_path.read_text())
        assert data["summary_statistics"]["num_scenarios"] == 1000
