"""Unit tests for report_plot_export module.

Tests cover:
    - ``_parse_dates_as_naive``    — no FutureWarning for mixed-tz dates (regression)
    - ``_safe_reactive_get``       — None, ``.get()`` protocol, plain value
    - ``_safe_float``              — None, valid number, invalid input
    - ``_get_inner_variables``     — None, empty dict, valid structure
    - ``_get_visual_objects``      — same structure as above
    - ``_create_placeholder_svg``  — creates well-formed SVG at correct path
    - ``ensure_all_svg_files_exist`` — ok vs placeholder status mapping
    - ``build_plotnine_portfolio_analysis_returns_distribution``
    - ``build_plotnine_portfolio_comparison_portfolio_vs_benchmark``
    - ``build_plotnine_weights_analysis_distribution_over_time``
    - ``build_plotnine_weights_analysis_current_composition``
    - ``build_plotnine_skfolio_weights_comparison``
    - ``build_plotnine_skfolio_performance_comparison``
    - ``build_plotnine_optimalportfolios_weights_comparison``
    - ``build_plotnine_optimalportfolios_performance_comparison``
    - ``build_plotnine_simulation_fan_chart``
    - ``build_plotnine_simulation_terminal_value_distribution``
    - ``export_plot_portfolio_analysis``
    - ``export_plot_portfolio_comparison``
    - ``export_plot_weights_analysis``
    - ``export_plot_weights_pie``
    - ``export_plot_skfolio_weights``
    - ``export_plot_skfolio_performance``
    - ``export_plot_simulation_fan_chart``
    - ``export_plot_simulation_histogram``
    - ``export_all_report_plots``

Regression notes:
    All ``build_plotnine_*`` functions that accept a ``Date`` column now route
    through ``_parse_dates_as_naive`` which applies ``pd.to_datetime(...,
    utc=True).dt.tz_convert(None)``.  Any regression to the old bare
    ``pd.to_datetime(col)`` call would immediately surface the
    ``FutureWarning`` in the tests that use
    ``warnings.simplefilter("error", FutureWarning)``.
"""

from __future__ import annotations

import datetime
import warnings

# Force a non-interactive matplotlib backend before any plotnine/matplotlib
# import so that tests can run without a display (CI / headless environments).
import matplotlib
matplotlib.use("Agg")

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Optional import guard — skip entire module if dashboard deps unavailable
# ---------------------------------------------------------------------------
try:
    from plotnine import ggplot

    import src.dashboard.reporting.report_plot_export as report_plot_export
    import src.dashboard.reporting._report_plot_returns as _rpe_returns_mod
    import src.dashboard.reporting._report_plot_allocation as _rpe_alloc_mod
    import src.dashboard.reporting._report_plot_risk as _rpe_risk_mod

    from src.dashboard.reporting.report_plot_export import (
        _create_placeholder_svg,
        _get_inner_variables,
        _get_visual_objects,
        _parse_dates_as_naive,
        _save_plot,
        _safe_float,
        _safe_reactive_get,
        build_plotnine_optimalportfolios_performance_comparison,
        build_plotnine_optimalportfolios_weights_comparison,
        build_plotnine_portfolio_analysis_returns_distribution,
        build_plotnine_portfolio_comparison_portfolio_vs_benchmark,
        build_plotnine_simulation_fan_chart,
        build_plotnine_simulation_terminal_value_distribution,
        build_plotnine_skfolio_performance_comparison,
        build_plotnine_skfolio_weights_comparison,
        build_plotnine_weights_analysis_current_composition,
        build_plotnine_weights_analysis_distribution_over_time,
        ensure_all_svg_files_exist,
        export_all_report_plots,
        export_plot_portfolio_analysis,
        export_plot_portfolio_comparison,
        export_plot_simulation_fan_chart,
        export_plot_simulation_histogram,
        export_plot_skfolio_performance,
        export_plot_skfolio_weights,
        export_plot_weights_analysis,
        export_plot_weights_pie,
    )

    MODULE_AVAILABLE = True
except ImportError as exc:
    MODULE_AVAILABLE = False
    _logger.warning(f"report_plot_export import failed — tests will be skipped: {exc}")

pytestmark = pytest.mark.skipif(not MODULE_AVAILABLE, reason="report_plot_export unavailable")


# ============================================================================
# Shared fixtures and test-data helpers
# ============================================================================


class MockReactiveValue:
    """Minimal stand-in for ``shiny.reactive.Value`` with no Shiny dependency."""

    def __init__(self, value: Any = None) -> None:
        """Init."""
        self._value = value

    def get(self) -> Any:
        """Get."""
        return self._value


def _make_reactives_shiny(**inner_kwargs: Any) -> dict[str, Any]:
    """Build a minimal ``reactives_shiny`` dict for export-function tests."""
    return {
        "Inner_Variables_Shiny": {k: MockReactiveValue(v) for k, v in inner_kwargs.items()},
        "Visual_Objects_Shiny": {},
    }


def _portfolio_df(n: int = 10) -> pl.DataFrame:
    """Return a Polars portfolio DataFrame with *n* rows."""
    dates = [datetime.date(2024, 1, i + 1) for i in range(n)]
    return pl.DataFrame({"Date": dates, "portfolio_value": [100.0 + i for i in range(n)]})


@pytest.mark.unit()
class Class_Test_Build_Simulation_Fan_Data:
    """Tests for ``_build_simulation_fan_data``."""

    @pytest.mark.unit()
    def Test_boolean_portfolio_values_return_empty_dataframe(self) -> None:
        """Boolean portfolio values should not be converted into simulation returns."""
        portfolio_values = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )

        result = _rpe_risk_mod._build_simulation_fan_data(pv = portfolio_values)

        assert result.is_empty()

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("parameter_name", "parameter_value"),
        [
            ("num_scenarios", True),
            ("num_days", False),
            ("initial_value", True),
            ("seed", False),
        ],
        ids=["num_scenarios_true", "num_days_false", "initial_value_true", "seed_false"],
    )
    def Test_boolean_numeric_parameters_return_empty_dataframe(
        self,
        parameter_name: str,
        parameter_value: bool,
    ) -> None:
        """Boolean simulation controls should use the existing empty-data fallback."""
        portfolio_values = _portfolio_df()
        build_kwargs = {parameter_name: parameter_value}

        result = _rpe_risk_mod._build_simulation_fan_data(pv = portfolio_values, **build_kwargs)

        assert result.is_empty()


def _perf_df(n: int = 10) -> pl.DataFrame:
    """Return a Polars performance DataFrame (Date + Value) with *n* rows."""
    dates = [datetime.date(2024, 1, i + 1) for i in range(n)]
    return pl.DataFrame({"Date": dates, "Value": [100.0 + i for i in range(n)]})


def _weights_df_pandas(n: int = 10) -> Any:
    """Return a pandas weights DataFrame with two asset columns."""
    import pandas as pd

    dates = [datetime.date(2024, 1, i + 1) for i in range(n)]
    return pd.DataFrame({"Date": dates, "AssetA": [0.6] * n, "AssetB": [0.4] * n})


def _mixed_tz_perf_df() -> pl.DataFrame:
    """Polars DataFrame with heterogeneous UTC-offset Date strings.

    Confirms that ``_parse_dates_as_naive`` silences the FutureWarning.
    """
    return pl.DataFrame({
        "Date": [
            "2024-01-01T00:00:00+01:00",
            "2024-01-02T00:00:00-05:00",
            "2024-01-03T00:00:00+00:00",
        ],
        "Value": [100.0, 101.0, 102.0],
    })


# ============================================================================
# _parse_dates_as_naive
# ============================================================================


@pytest.mark.unit()
class Class_Test_Parse_Dates_As_Naive:
    """Tests for ``_parse_dates_as_naive``."""

    @pytest.mark.unit()
    def Test_naive_string_dates_produce_naive_series(self) -> None:
        """Plain ISO date strings yield timezone-naive datetime64."""
        import pandas as pd

        raw = pd.Series(["2024-01-01", "2024-01-02", "2024-01-03"])
        result = _parse_dates_as_naive(date_col = raw)
        assert result.dt.tz is None

    @pytest.mark.unit()
    def Test_mixed_timezone_strings_no_future_warning(self) -> None:
        """Mixed UTC-offset strings produce no FutureWarning (regression)."""
        import pandas as pd

        raw = pd.Series([
            "2024-01-01T00:00:00+01:00",
            "2024-01-02T00:00:00-05:00",
            "2024-01-03T00:00:00+00:00",
        ])
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = _parse_dates_as_naive(date_col = raw)
        assert result.dt.tz is None

    @pytest.mark.unit()
    def Test_date_objects_produce_naive_series(self) -> None:
        """Python ``datetime.date`` objects produce timezone-naive Series."""
        import pandas as pd

        raw = pd.Series([datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)])
        result = _parse_dates_as_naive(date_col = raw)
        assert result.dt.tz is None


# ============================================================================
# _safe_reactive_get
# ============================================================================


@pytest.mark.unit()
class Class_Test_Safe_Reactive_Get:
    """Tests for ``_safe_reactive_get``."""

    @pytest.mark.unit()
    def Test_none_input_returns_none(self) -> None:
        """Test that none input returns none."""
        assert _safe_reactive_get(reactive_value = None) is None

    @pytest.mark.unit()
    def Test_object_with_get_method_returns_get_result(self) -> None:
        """Test that object with get method returns get result."""
        obj = MockReactiveValue(42)
        assert _safe_reactive_get(reactive_value = obj) == 42

    @pytest.mark.unit()
    def Test_get_method_raising_returns_none(self) -> None:
        """Test that get method raising returns none."""
        bad = MagicMock()
        bad.get.side_effect = RuntimeError("shiny not ready")
        assert _safe_reactive_get(reactive_value = bad) is None

    @pytest.mark.unit()
    def Test_plain_value_returned_unchanged(self) -> None:
        """Test that plain value returned unchanged."""
        assert _safe_reactive_get(reactive_value = "hello") == "hello"
        assert _safe_reactive_get(reactive_value = 3.14) == 3.14


# ============================================================================
# _safe_float
# ============================================================================


@pytest.mark.unit()
class Class_Test_Safe_Float:
    """Tests for ``_safe_float``."""

    @pytest.mark.unit()
    def Test_none_returns_default(self) -> None:
        """Test that none returns default."""
        assert _safe_float(value = None) == 0.0
        assert _safe_float(value = None, default=99.9) == 99.9

    @pytest.mark.unit()
    def Test_valid_number_converted_to_float(self) -> None:
        """Test that valid number converted to float."""
        assert _safe_float(value = 1) == 1.0
        assert _safe_float(value = "3.14") == pytest.approx(3.14)

    @pytest.mark.unit()
    def Test_boolean_returns_default(self) -> None:
        """Boolean values should stay on the helper's existing default path."""
        assert _safe_float(value = True) == 0.0
        assert _safe_float(value = False, default=7.0) == 7.0

    @pytest.mark.unit()
    def Test_invalid_string_returns_default(self) -> None:
        """Test that invalid string returns default."""
        assert _safe_float(value = "not-a-number") == 0.0
        assert _safe_float(value = "bad", default=7.0) == 7.0

    @pytest.mark.unit()
    def Test_non_convertible_type_returns_default(self) -> None:
        """Test that non convertible type returns default."""
        assert _safe_float(value = [1, 2]) == 0.0


# ============================================================================
# _get_inner_variables
# ============================================================================


@pytest.mark.unit()
class Class_Test_Get_Inner_Variables:
    """Tests for ``_get_inner_variables``."""

    @pytest.mark.unit()
    def Test_none_returns_empty_dict(self) -> None:
        """Test that none returns empty dict."""
        assert _get_inner_variables(reactives_shiny = None) == {}

    @pytest.mark.unit()
    def Test_non_dict_argument_returns_empty_dict(self) -> None:
        """Test that non dict argument returns empty dict."""
        assert _get_inner_variables(reactives_shiny = "not a dict") == {}  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_missing_inner_variables_key_returns_empty_dict(self) -> None:
        """Test that missing inner variables key returns empty dict."""
        assert _get_inner_variables(reactives_shiny = {}) == {}

    @pytest.mark.unit()
    def Test_non_dict_value_for_key_returns_empty_dict(self) -> None:
        """Test that non dict value for key returns empty dict."""
        assert _get_inner_variables(reactives_shiny = {"Inner_Variables_Shiny": "bad"}) == {}

    @pytest.mark.unit()
    def Test_valid_structure_returns_inner_dict(self) -> None:
        """Test that valid structure returns inner dict."""
        inner = {"foo": 1, "bar": 2}
        result = _get_inner_variables(reactives_shiny = {"Inner_Variables_Shiny": inner})
        assert result == inner


# ============================================================================
# _get_visual_objects
# ============================================================================


@pytest.mark.unit()
class Class_Test_Get_Visual_Objects:
    """Tests for ``_get_visual_objects``."""

    @pytest.mark.unit()
    def Test_none_returns_empty_dict(self) -> None:
        """Test that none returns empty dict."""
        assert _get_visual_objects(reactives_shiny = None) == {}

    @pytest.mark.unit()
    def Test_missing_key_returns_empty_dict(self) -> None:
        """Test that missing key returns empty dict."""
        assert _get_visual_objects(reactives_shiny = {}) == {}

    @pytest.mark.unit()
    def Test_valid_structure_returns_visual_dict(self) -> None:
        """Test that valid structure returns visual dict."""
        objs = {"chart_1": object()}
        result = _get_visual_objects(reactives_shiny = {"Visual_Objects_Shiny": objs})
        assert result is objs


# ============================================================================
# _create_placeholder_svg
# ============================================================================


@pytest.mark.unit()
class Class_Test_Create_Placeholder_Svg:
    """Tests for ``_create_placeholder_svg``."""

    @pytest.mark.unit()
    def Test_creates_svg_file_at_images_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that creates svg file at images dir."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = _create_placeholder_svg(filename = "test_chart.svg", title="Test Chart")
        assert result == tmp_path / "test_chart.svg"
        assert result.exists()

    @pytest.mark.unit()
    def Test_file_contains_well_formed_svg_xml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that file contains well formed svg xml."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        svg_path = _create_placeholder_svg(filename = "check.svg", title="My Title")
        content = svg_path.read_text(encoding="utf-8")
        assert "<?xml" in content
        assert "<svg" in content
        assert "My Title" in content

    @pytest.mark.unit()
    def Test_default_title_present_when_omitted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default title present when omitted."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        svg_path = _create_placeholder_svg(filename = "default.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert "Chart Unavailable" in content


# ============================================================================
# _save_plot
# ============================================================================


@pytest.mark.unit()
class Class_Test_Save_Plot:
    """Tests for ``_save_plot``."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("dimension_name", "dimension_value"),
        [
            ("width", True),
            ("width", False),
            ("height", True),
            ("height", False),
        ],
        ids=["width_true", "width_false", "height_true", "height_false"],
    )
    def Test_boolean_dimensions_raise_validation_input(
        self,
        dimension_name: str,
        dimension_value: bool,
    ) -> None:
        """Boolean plot dimensions should be rejected before plot save."""
        plot_mock = MagicMock()
        save_kwargs = {dimension_name: dimension_value}

        with pytest.raises(Exception_Validation_Input, match=dimension_name):
            _save_plot(plot = plot_mock, filename = "test.svg", **save_kwargs)

        plot_mock.save.assert_not_called()


# ============================================================================
# ensure_all_svg_files_exist
# ============================================================================


@pytest.mark.unit()
class Class_Test_Ensure_All_Svg_Files_Exist:
    """Tests for ``ensure_all_svg_files_exist``."""

    @pytest.mark.unit()
    def Test_all_missing_files_produce_placeholder_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that all missing files produce placeholder status."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = ensure_all_svg_files_exist()
        assert all(v == "placeholder" for v in result.values())
        assert set(result.keys()) == set(report_plot_export._EXPECTED_SVG_FILES.keys())

    @pytest.mark.unit()
    def Test_present_non_empty_files_produce_ok_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that present non empty files produce ok status."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        for filename in report_plot_export._EXPECTED_SVG_FILES.values():
            (tmp_path / filename).write_text("<svg/>", encoding="utf-8")
        result = ensure_all_svg_files_exist()
        assert all(v == "ok" for v in result.values())

    @pytest.mark.unit()
    def Test_empty_file_produces_placeholder_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that empty file produces placeholder status."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        first_key = next(iter(report_plot_export._EXPECTED_SVG_FILES))
        first_filename = report_plot_export._EXPECTED_SVG_FILES[first_key]
        (tmp_path / first_filename).write_text("", encoding="utf-8")
        result = ensure_all_svg_files_exist()
        assert result[first_key] == "placeholder"


# ============================================================================
# build_plotnine_portfolio_analysis_returns_distribution
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Portfolio_Analysis_Returns_Distribution:
    """Tests for ``build_plotnine_portfolio_analysis_returns_distribution``."""

    @pytest.mark.unit()
    def Test_none_portfolio_returns_none(self) -> None:
        """Test that none portfolio returns none."""
        assert build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = None) is None

    @pytest.mark.unit()
    def Test_single_row_returns_none(self) -> None:
        """Test that single row returns none."""
        assert build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = _portfolio_df(1)) is None

    @pytest.mark.unit()
    def Test_valid_portfolio_only_returns_ggplot(self) -> None:
        """Test that valid portfolio only returns ggplot."""
        result = build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = _portfolio_df())
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_valid_portfolio_with_benchmark_returns_ggplot(self) -> None:
        """Test that valid portfolio with benchmark returns ggplot."""
        df = _portfolio_df()
        result = build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = df, benchmark_df=df)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_benchmark_with_single_row_is_skipped(self) -> None:
        """Test that benchmark with single row is skipped."""
        df = _portfolio_df()
        result = build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = df, benchmark_df=_portfolio_df(1))
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_boolean_portfolio_values_return_none(self) -> None:
        """Boolean portfolio values should not be treated as numeric returns."""
        portfolio_df = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )

        result = build_plotnine_portfolio_analysis_returns_distribution(portfolio_df = portfolio_df)

        assert result is None

    @pytest.mark.unit()
    def Test_boolean_benchmark_values_are_skipped(self) -> None:
        """Boolean benchmark values should be ignored instead of plotted as numeric returns."""
        benchmark_df = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )

        result = build_plotnine_portfolio_analysis_returns_distribution(
            portfolio_df = _portfolio_df(),
            benchmark_df=benchmark_df,
        )

        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_portfolio_comparison_portfolio_vs_benchmark
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Portfolio_Comparison_Vs_Benchmark:
    """Tests for ``build_plotnine_portfolio_comparison_portfolio_vs_benchmark``."""

    @pytest.mark.unit()
    def Test_none_portfolio_returns_none(self) -> None:
        """Test that none portfolio returns none."""
        assert build_plotnine_portfolio_comparison_portfolio_vs_benchmark(portfolio_df = None, benchmark_df = None) is None

    @pytest.mark.unit()
    def Test_single_row_portfolio_returns_none(self) -> None:
        """Test that single row portfolio returns none."""
        assert build_plotnine_portfolio_comparison_portfolio_vs_benchmark(
            portfolio_df = _portfolio_df(1), benchmark_df = None
        ) is None

    @pytest.mark.unit()
    def Test_valid_no_benchmark_returns_ggplot(self) -> None:
        """Test that valid no benchmark returns ggplot."""
        result = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(portfolio_df = _portfolio_df(), benchmark_df = None)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_valid_with_benchmark_returns_ggplot(self) -> None:
        """Test that valid with benchmark returns ggplot."""
        df = _portfolio_df()
        result = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(portfolio_df = df, benchmark_df = df)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_benchmark_with_single_row_is_skipped(self) -> None:
        """Test that benchmark with single row is skipped."""
        df = _portfolio_df()
        result = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(portfolio_df = df, benchmark_df = _portfolio_df(1))
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(self) -> None:
        """Regression: mixed-tz Date column must not raise FutureWarning."""
        import pandas as pd

        df = pl.from_pandas(pd.DataFrame({
            "Date": [
                "2024-01-01T00:00:00+01:00",
                "2024-01-02T00:00:00-05:00",
                "2024-01-03T00:00:00+00:00",
            ],
            "portfolio_value": [100.0, 101.0, 102.0],
        }))
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(portfolio_df = df, benchmark_df = None)
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_weights_analysis_distribution_over_time
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Weights_Distribution_Over_Time:
    """Tests for ``build_plotnine_weights_analysis_distribution_over_time``."""

    @pytest.mark.unit()
    def Test_none_returns_none(self) -> None:
        """Test that none returns none."""
        assert build_plotnine_weights_analysis_distribution_over_time(weights_df = None) is None

    @pytest.mark.unit()
    def Test_empty_dataframe_returns_none(self) -> None:
        """Test that empty dataframe returns none."""
        import pandas as pd

        assert build_plotnine_weights_analysis_distribution_over_time(weights_df = pd.DataFrame()) is None

    @pytest.mark.unit()
    def Test_no_date_column_returns_none(self) -> None:
        """Test that no date column returns none."""
        import pandas as pd

        df = pd.DataFrame({"AssetA": [0.6, 0.7], "AssetB": [0.4, 0.3]})
        assert build_plotnine_weights_analysis_distribution_over_time(weights_df = df) is None

    @pytest.mark.unit()
    def Test_only_date_column_no_assets_returns_none(self) -> None:
        """Test that only date column no assets returns none."""
        import pandas as pd

        df = pd.DataFrame({"Date": ["2024-01-01", "2024-01-02"]})
        assert build_plotnine_weights_analysis_distribution_over_time(weights_df = df) is None

    @pytest.mark.unit()
    def Test_valid_dataframe_returns_ggplot(self) -> None:
        """Test that valid dataframe returns ggplot."""
        result = build_plotnine_weights_analysis_distribution_over_time(weights_df = _weights_df_pandas())
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(self) -> None:
        """Regression: mixed-tz Date column must not raise FutureWarning."""
        import pandas as pd

        df = pd.DataFrame({
            "Date": [
                "2024-01-01T00:00:00+01:00",
                "2024-01-02T00:00:00-05:00",
                "2024-01-03T00:00:00+00:00",
            ],
            "AssetA": [0.6, 0.55, 0.5],
            "AssetB": [0.4, 0.45, 0.5],
        })
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = build_plotnine_weights_analysis_distribution_over_time(weights_df = df)
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_weights_analysis_current_composition
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Weights_Current_Composition:
    """Tests for ``build_plotnine_weights_analysis_current_composition``."""

    @pytest.mark.unit()
    def Test_empty_lists_return_none(self) -> None:
        """Test that empty lists return none."""
        assert build_plotnine_weights_analysis_current_composition(labels = [], values = []) is None

    @pytest.mark.unit()
    def Test_mismatched_list_lengths_return_none(self) -> None:
        """Test that mismatched list lengths return none."""
        assert build_plotnine_weights_analysis_current_composition(labels = ["A"], values = [0.5, 0.5]) is None

    @pytest.mark.unit()
    def Test_valid_labels_and_values_return_ggplot(self) -> None:
        """Test that valid labels and values return ggplot."""
        result = build_plotnine_weights_analysis_current_composition(
            labels = ["AssetA", "AssetB", "AssetC"], values = [0.5, 0.3, 0.2]
        )
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_skfolio_weights_comparison
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Skfolio_Weights_Comparison:
    """Tests for ``build_plotnine_skfolio_weights_comparison``."""

    @pytest.mark.unit()
    def Test_empty_assets_returns_none(self) -> None:
        """Test that empty assets returns none."""
        assert build_plotnine_skfolio_weights_comparison(assets = [], weights1 = [], weights2 = []) is None

    @pytest.mark.unit()
    def Test_valid_inputs_return_ggplot(self) -> None:
        """Test that valid inputs return ggplot."""
        result = build_plotnine_skfolio_weights_comparison(
            assets = ["AAPL", "MSFT", "GOOG"],
            weights1 = [0.4, 0.35, 0.25],
            weights2 = [0.3, 0.4, 0.3],
            name1 = "MVO",
            name2 = "ERC",
        )
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_default_method_names_still_returns_ggplot(self) -> None:
        """Test that default method names still returns ggplot."""
        result = build_plotnine_skfolio_weights_comparison(assets = ["A", "B"], weights1 = [0.6, 0.4], weights2 = [0.5, 0.5])
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_skfolio_performance_comparison
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Skfolio_Performance_Comparison:
    """Tests for ``build_plotnine_skfolio_performance_comparison``."""

    @pytest.mark.unit()
    def Test_both_none_returns_none(self) -> None:
        """Test that both none returns none."""
        assert build_plotnine_skfolio_performance_comparison(perf1_df = None, perf2_df = None) is None

    @pytest.mark.unit()
    def Test_single_row_dfs_return_none(self) -> None:
        """Test that single row dfs return none."""
        df = _perf_df(1)
        assert build_plotnine_skfolio_performance_comparison(perf1_df = df, perf2_df = df) is None

    @pytest.mark.unit()
    def Test_one_valid_df_returns_ggplot(self) -> None:
        """Test that one valid df returns ggplot."""
        result = build_plotnine_skfolio_performance_comparison(perf1_df = _perf_df(), perf2_df = None)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_two_valid_dfs_return_ggplot(self) -> None:
        """Test that two valid dfs return ggplot."""
        df = _perf_df()
        result = build_plotnine_skfolio_performance_comparison(perf1_df = df, perf2_df = df, name1 = "A", name2 = "B")
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(self) -> None:
        """Regression: mixed-tz Date column must not raise FutureWarning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = build_plotnine_skfolio_performance_comparison(perf1_df = _mixed_tz_perf_df(), perf2_df = None)
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_optimalportfolios_weights_comparison
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Optimalportfolios_Weights_Comparison:
    """Tests for ``build_plotnine_optimalportfolios_weights_comparison``."""

    @pytest.mark.unit()
    def Test_empty_assets_returns_none(self) -> None:
        """Test that empty assets returns none."""
        assert build_plotnine_optimalportfolios_weights_comparison(assets = [], weights1 = [], weights2 = []) is None

    @pytest.mark.unit()
    def Test_valid_inputs_return_ggplot(self) -> None:
        """Test that valid inputs return ggplot."""
        result = build_plotnine_optimalportfolios_weights_comparison(
            assets = ["AAPL", "MSFT", "GOOG"],
            weights1 = [0.4, 0.35, 0.25],
            weights2 = [0.3, 0.4, 0.3],
        )
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_optimalportfolios_performance_comparison
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Optimalportfolios_Performance_Comparison:
    """Tests for ``build_plotnine_optimalportfolios_performance_comparison``."""

    @pytest.mark.unit()
    def Test_both_none_returns_none(self) -> None:
        """Test that both none returns none."""
        assert build_plotnine_optimalportfolios_performance_comparison(perf1_df = None, perf2_df = None) is None

    @pytest.mark.unit()
    def Test_one_valid_df_returns_ggplot(self) -> None:
        """Test that one valid df returns ggplot."""
        result = build_plotnine_optimalportfolios_performance_comparison(perf1_df = _perf_df(), perf2_df = None)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_two_valid_dfs_return_ggplot(self) -> None:
        """Test that two valid dfs return ggplot."""
        df = _perf_df()
        result = build_plotnine_optimalportfolios_performance_comparison(perf1_df = df, perf2_df = df, name1 = "X", name2 = "Y")
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(self) -> None:
        """Regression: mixed-tz Date column must not raise FutureWarning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = build_plotnine_optimalportfolios_performance_comparison(
                perf1_df = _mixed_tz_perf_df(), perf2_df = None
            )
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_simulation_fan_chart
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Simulation_Fan_Chart:
    """Tests for ``build_plotnine_simulation_fan_chart``."""

    @pytest.mark.unit()
    def Test_none_returns_none(self) -> None:
        """Test that none returns none."""
        assert build_plotnine_simulation_fan_chart(results_df = None) is None

    @pytest.mark.unit()
    def Test_no_scenario_columns_returns_none(self) -> None:
        """Test that no scenario columns returns none."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"], "other": [1.0, 2.0]})
        assert build_plotnine_simulation_fan_chart(results_df = df) is None

    @pytest.mark.unit()
    def Test_boolean_scenario_columns_return_none(self) -> None:
        """Boolean scenario columns should not be treated as numeric fan-chart data."""
        df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "Scenario_0": [True, False],
                "Scenario_1": [False, True],
            },
        )
        assert build_plotnine_simulation_fan_chart(results_df = df) is None

    @pytest.mark.unit()
    def Test_valid_scenario_df_returns_ggplot(self) -> None:
        """Test that valid scenario df returns ggplot."""
        import numpy as np

        rng = np.random.default_rng(0)
        n = 5
        data: dict[str, Any] = {
            "Date": [datetime.date(2024, 1, i + 1) for i in range(n)],
        }
        for j in range(3):
            data[f"Scenario_{j}"] = list(rng.uniform(100, 120, n))
        result = build_plotnine_simulation_fan_chart(results_df = pl.DataFrame(data))
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(self) -> None:
        """Regression: mixed-tz Date column must not raise FutureWarning."""
        import numpy as np

        rng = np.random.default_rng(0)
        n = 3
        data: dict[str, Any] = {
            "Date": [
                "2024-01-01T00:00:00+01:00",
                "2024-01-02T00:00:00-05:00",
                "2024-01-03T00:00:00+00:00",
            ],
        }
        for j in range(3):
            data[f"Scenario_{j}"] = list(rng.uniform(100, 120, n))
        df = pl.DataFrame(data)
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = build_plotnine_simulation_fan_chart(results_df = df)
        assert isinstance(result, ggplot)


# ============================================================================
# build_plotnine_simulation_terminal_value_distribution
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Simulation_Terminal_Value_Distribution:
    """Tests for ``build_plotnine_simulation_terminal_value_distribution``."""

    @pytest.mark.unit()
    def Test_none_returns_none(self) -> None:
        """Test that none returns none."""
        assert build_plotnine_simulation_terminal_value_distribution(terminal_values = None) is None

    @pytest.mark.unit()
    def Test_single_element_returns_none(self) -> None:
        """Test that single element returns none."""
        assert build_plotnine_simulation_terminal_value_distribution(terminal_values = [100.0]) is None

    @pytest.mark.unit()
    def Test_boolean_terminal_values_return_none(self) -> None:
        """Boolean terminal values should not be treated as numeric histogram inputs."""
        assert build_plotnine_simulation_terminal_value_distribution(terminal_values = [100.0, True, 110.0]) is None

    @pytest.mark.unit()
    def Test_numpy_array_returns_ggplot(self) -> None:
        """Test that numpy array returns ggplot."""
        import numpy as np

        vals = np.random.default_rng(0).normal(100, 10, 200)
        result = build_plotnine_simulation_terminal_value_distribution(terminal_values = vals)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_python_list_returns_ggplot(self) -> None:
        """Test that python list returns ggplot."""
        vals = [90.0 + i * 0.5 for i in range(50)]
        result = build_plotnine_simulation_terminal_value_distribution(terminal_values = vals)
        assert isinstance(result, ggplot)


# ============================================================================
# export_plot_portfolio_analysis
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Portfolio_Analysis:
    """Tests for ``export_plot_portfolio_analysis``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none_or_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """With no reactives, the function falls back to sample CSV or returns None."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        # Sample CSV likely absent in test env; result is None or a Path
        result = export_plot_portfolio_analysis(reactives_shiny = None)
        assert result is None or isinstance(result, Path)

    @pytest.mark.unit()
    def Test_valid_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=_portfolio_df(20),
                Benchmark_Values=_portfolio_df(20),
            )
            result = export_plot_portfolio_analysis(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_portfolio_comparison
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Portfolio_Comparison:
    """Tests for ``export_plot_portfolio_comparison``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none_or_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that none reactives returns none or path."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_portfolio_comparison(reactives_shiny = None)
        assert result is None or isinstance(result, Path)

    @pytest.mark.unit()
    def Test_valid_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Portfolio_Values=_portfolio_df(20))
            result = export_plot_portfolio_comparison(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_weights_analysis
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Weights_Analysis:
    """Tests for ``export_plot_weights_analysis``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that none reactives returns none."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_weights_analysis(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_valid_weights_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid weights data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        weights_data = pl.DataFrame({
            "Date": [datetime.date(2024, 1, i + 1) for i in range(10)],
            "AssetA": [0.6] * 10,
            "AssetB": [0.4] * 10,
        })
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Weights_Data=weights_data)
            result = export_plot_weights_analysis(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_weights_pie
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Weights_Pie:
    """Tests for ``export_plot_weights_pie``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that none reactives returns none."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_weights_pie(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_valid_weights_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid weights data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        weights_data = pl.DataFrame({
            "Date": [datetime.date(2024, 1, i + 1) for i in range(5)],
            "AssetA": [0.6] * 5,
            "AssetB": [0.4] * 5,
        })
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Weights_Data=weights_data)
            result = export_plot_weights_pie(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_skfolio_weights
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Skfolio_Weights:
    """Tests for ``export_plot_skfolio_weights``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that none reactives returns none."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_skfolio_weights(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_valid_results_table_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid results table saves svg."""
        import pandas as pd

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        results_table = pd.DataFrame({
            "Asset": ["AAPL", "MSFT", "GOOG"],
            "Portfolio_MVO": [0.4, 0.35, 0.25],
            "Portfolio_ERC": [0.33, 0.33, 0.34],
        })
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Skfolio_Results_Table=results_table)
            result = export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_skfolio_performance
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Skfolio_Performance:
    """Tests for ``export_plot_skfolio_performance``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none(self) -> None:
        """Test that none reactives returns none."""
        result = export_plot_skfolio_performance(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_insufficient_data_returns_none(self) -> None:
        """Test that insufficient data returns none."""
        reactives = _make_reactives_shiny(Skfolio_Performance_Data=_perf_df(1))
        result = export_plot_skfolio_performance(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_valid_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Skfolio_Performance_Data=_perf_df(10))
            result = export_plot_skfolio_performance(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_mixed_timezone_dates_no_future_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression: export function must not trigger FutureWarning on mixed-tz data."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Skfolio_Performance_Data=_mixed_tz_perf_df())
            with warnings.catch_warnings():
                warnings.simplefilter("error", FutureWarning)
                result = export_plot_skfolio_performance(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_simulation_fan_chart
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Simulation_Fan_Chart:
    """Tests for ``export_plot_simulation_fan_chart``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none_or_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that none reactives returns none or path."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_simulation_fan_chart(reactives_shiny = None)
        assert result is None or isinstance(result, Path)

    @pytest.mark.unit()
    def Test_valid_fan_data_saves_svg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that valid fan data saves svg."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "p5": [80.0] * 10,
            "p25": [90.0] * 10,
            "median": [100.0] * 10,
            "mean": [101.0] * 10,
            "p75": [110.0] * 10,
            "p95": [120.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_plot_simulation_histogram
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_Plot_Simulation_Histogram:
    """Tests for ``export_plot_simulation_histogram``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_none_or_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that none reactives returns none or path."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_plot_simulation_histogram(reactives_shiny = None)
        assert result is None or isinstance(result, Path)

    @pytest.mark.unit()
    def Test_valid_terminal_values_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that valid terminal values saves svg."""
        import numpy as np

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        vals = np.random.default_rng(0).normal(100, 10, 200)
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Terminal_Values=vals)
            result = export_plot_simulation_histogram(reactives_shiny = reactives)
        assert result == fake_path


# ============================================================================
# export_all_report_plots
# ============================================================================


@pytest.mark.unit()
class Class_Test_Export_All_Report_Plots:
    """Tests for ``export_all_report_plots``."""

    @pytest.mark.unit()
    def Test_none_reactives_returns_dict_with_all_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that none reactives returns dict with all keys."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_all_report_plots(reactives_shiny = None)
        assert isinstance(result, dict)
        expected_keys = {
            "portfolio_analysis",
            "portfolio_comparison",
            "weights_analysis",
            "weights_composition",
            "skfolio_weights",
            "skfolio_performance",
            "simulation_fan_chart",
            "simulation_histogram",
        }
        assert expected_keys.issubset(set(result.keys()))

    @pytest.mark.unit()
    def Test_missing_charts_get_placeholder_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Charts that return None must be replaced by placeholder SVG paths."""
        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        result = export_all_report_plots(reactives_shiny = None)
        # All values must be non-None (placeholders created for missing charts)
        for val in result.values():
            assert val is not None
            assert isinstance(val, Path)

    @pytest.mark.unit()
    def Test_all_export_functions_called_and_none_results_get_placeholders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When all individual export funcs return None, placeholders are created."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        # Force every individual export function to return None
        for fn_name in [
            "export_plot_portfolio_analysis",
            "export_plot_portfolio_comparison",
            "export_plot_weights_analysis",
            "export_plot_weights_pie",
            "export_plot_skfolio_weights",
            "export_plot_skfolio_performance",
            "export_plot_simulation_fan_chart",
            "export_plot_simulation_histogram",
        ]:
            monkeypatch.setattr(rpe, fn_name, lambda reactives_shiny: None)
        result = rpe.export_all_report_plots(reactives_shiny = {"Inner_Variables_Shiny": {}, "Visual_Objects_Shiny": {}})
        assert isinstance(result, dict)
        for key, val in result.items():
            assert val is not None, f"Key {key!r} should have a placeholder but got None"
            assert isinstance(val, Path)

    @pytest.mark.unit()
    def Test_all_export_functions_return_paths_no_placeholders_needed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When all individual export funcs return a valid Path, no placeholder is created."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "fake.svg"
        fake_path.write_text("<svg/>")
        for fn_name in [
            "export_plot_portfolio_analysis",
            "export_plot_portfolio_comparison",
            "export_plot_weights_analysis",
            "export_plot_weights_pie",
            "export_plot_skfolio_weights",
            "export_plot_skfolio_performance",
            "export_plot_simulation_fan_chart",
            "export_plot_simulation_histogram",
        ]:
            monkeypatch.setattr(rpe, fn_name, lambda reactives_shiny, _p=fake_path: _p)
        result = rpe.export_all_report_plots(reactives_shiny = {"Inner_Variables_Shiny": {}, "Visual_Objects_Shiny": {}})
        assert isinstance(result, dict)
        for val in result.values():
            assert val == fake_path


# ============================================================================
# Additional branch-coverage tests
# ============================================================================


@pytest.mark.unit()
class Class_Test_Build_Optimalportfolios_Performance_Comparison_Extra:
    """Extra tests for build_plotnine_optimalportfolios_performance_comparison."""

    @pytest.mark.unit()
    def Test_pandas_df_input_triggers_from_pandas_path(self) -> None:
        """Passing a pandas DataFrame triggers the pl.from_pandas branch (line ~656)."""
        import pandas as pd

        pdf = pd.DataFrame({
            "Date": [datetime.date(2024, 1, i + 1) for i in range(5)],
            "Value": [100.0 + i for i in range(5)],
        })
        result = build_plotnine_optimalportfolios_performance_comparison(perf1_df = pdf, perf2_df = None)
        assert isinstance(result, ggplot)

    @pytest.mark.unit()
    def Test_single_row_df_skipped_and_returns_none(self) -> None:
        """A single-row DataFrame is skipped (height < 2) — covers 'continue' branch."""
        result = build_plotnine_optimalportfolios_performance_comparison(perf1_df = _perf_df(1), perf2_df = _perf_df(1))
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Portfolio_Analysis_Extra:
    """Extra branch tests for export_plot_portfolio_analysis."""

    @pytest.mark.unit()
    def Test_portfolio_only_no_benchmark_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Portfolio data only (no benchmark) — covers False branch of benchmark check."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=_portfolio_df(20),
            )
            result = rpe.export_plot_portfolio_analysis(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_no_data_and_no_sample_csv_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No portfolio data and no sample CSV — covers lines 893-894 (warning + return None)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        monkeypatch.setattr(_rpe_returns_mod, "_load_sample_csv_for_plots", lambda: (None, None))
        result = rpe.export_plot_portfolio_analysis(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_boolean_portfolio_values_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean portfolio values should not be exported as numeric return distributions."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        reactives = _make_reactives_shiny(
            Portfolio_Values=pl.DataFrame(
                {
                    "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                    "portfolio_value": [True, False],
                },
            ),
        )

        result = rpe.export_plot_portfolio_analysis(reactives_shiny = reactives)

        assert result is None

    @pytest.mark.unit()
    def Test_boolean_benchmark_values_are_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean benchmark values should be ignored in the exported returns plot."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        benchmark_df = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )

        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=_portfolio_df(20),
                Benchmark_Values=benchmark_df,
            )
            result = rpe.export_plot_portfolio_analysis(reactives_shiny = reactives)

        assert result == fake_path


@pytest.mark.unit()
class Class_Test_Export_Plot_Portfolio_Comparison_Extra:
    """Extra branch tests for export_plot_portfolio_comparison."""

    @pytest.mark.unit()
    def Test_with_benchmark_data_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Portfolio + benchmark data — covers lines 968-969, 977 (benchmark branch)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=_portfolio_df(20),
                Benchmark_Values=_portfolio_df(20),
            )
            result = rpe.export_plot_portfolio_comparison(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_start_val_zero_normalised_to_one(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When first portfolio value is 0, start_val is replaced with 1.0 — covers line 977."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        dates = [datetime.date(2024, 1, i + 1) for i in range(10)]
        pv_zero_start = pl.DataFrame({"Date": dates, "portfolio_value": [0.0] + [100.0] * 9})
        bv_zero_start = pl.DataFrame({"Date": dates, "portfolio_value": [0.0] + [100.0] * 9})
        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=pv_zero_start,
                Benchmark_Values=bv_zero_start,
            )
            result = rpe.export_plot_portfolio_comparison(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_boolean_start_values_use_safe_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean first values route through ``_safe_float`` instead of raw float coercion."""
        safe_float_calls: list[tuple[object, float]] = []
        original_safe_float = _rpe_returns_mod._safe_float

        def _tracking_safe_float(value: object, default: float = 0.0) -> float:
            safe_float_calls.append((value, default))
            return original_safe_float(value=value, default=default)

        monkeypatch.setattr(_rpe_returns_mod, "_safe_float", _tracking_safe_float)
        dates = [datetime.date(2024, 1, i + 1) for i in range(10)]
        pv_bool_start = pl.DataFrame(
            {"Date": dates, "portfolio_value": [True, False] * 5}
        )
        bv_bool_start = pl.DataFrame(
            {"Date": dates, "portfolio_value": [False, True] * 5}
        )

        result = build_plotnine_portfolio_comparison_portfolio_vs_benchmark(
            portfolio_df = pv_bool_start,
            benchmark_df = bv_bool_start,
        )

        assert isinstance(result, ggplot)
        assert safe_float_calls == [(True, 1.0), (False, 1.0)]

    @pytest.mark.unit()
    def Test_export_boolean_start_values_use_safe_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean first values in export path should use ``_safe_float(..., 1.0)``."""
        import src.dashboard.reporting.report_plot_export as rpe

        safe_float_calls: list[tuple[object, float]] = []
        original_safe_float = _rpe_returns_mod._safe_float

        def _tracking_safe_float(value: object, default: float = 0.0) -> float:
            safe_float_calls.append((value, default))
            return original_safe_float(value=value, default=default)

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        monkeypatch.setattr(_rpe_returns_mod, "_safe_float", _tracking_safe_float)
        fake_path = tmp_path / "chart.svg"
        dates = [datetime.date(2024, 1, i + 1) for i in range(10)]
        portfolio_values_bool_start = pl.DataFrame(
            {"Date": dates, "portfolio_value": [True, False] * 5}
        )
        benchmark_values_bool_start = pl.DataFrame(
            {"Date": dates, "portfolio_value": [False, True] * 5}
        )

        with patch.object(_rpe_returns_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(
                Portfolio_Values=portfolio_values_bool_start,
                Benchmark_Values=benchmark_values_bool_start,
            )
            result = rpe.export_plot_portfolio_comparison(reactives_shiny = reactives)

        assert result == fake_path
        assert safe_float_calls == [(True, 1.0), (False, 1.0)]

    @pytest.mark.unit()
    def Test_no_data_and_no_sample_csv_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No data and no sample CSV — covers lines 968-969 (second insufficient-data check)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        monkeypatch.setattr(_rpe_returns_mod, "_load_sample_csv_for_plots", lambda: (None, None))
        result = rpe.export_plot_portfolio_comparison(reactives_shiny = None)
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Weights_Analysis_Extra:
    """Extra branch tests for export_plot_weights_analysis."""

    @pytest.mark.unit()
    def Test_weights_df_only_date_column_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Weights DataFrame with only Date column (no assets) returns None — covers line 1063."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        only_date_df = pl.DataFrame({"Date": [datetime.date(2024, 1, 1)]})
        reactives = _make_reactives_shiny(Weights_Data=only_date_df)
        result = rpe.export_plot_weights_analysis(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_boolean_only_weight_columns_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean-only weight columns are excluded instead of being plotted as numeric weights."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        bool_weight_df = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1)],
                "Flag": [True],
            }
        )
        reactives = _make_reactives_shiny(Weights_Data=bool_weight_df)
        result = rpe.export_plot_weights_analysis(reactives_shiny = reactives)
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Weights_Pie_Extra:
    """Extra branch tests for export_plot_weights_pie."""

    @pytest.mark.unit()
    def Test_weights_df_only_date_column_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Weights DataFrame with only Date column (no assets) returns None — covers line 1116."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        only_date_df = pl.DataFrame({"Date": [datetime.date(2024, 1, 1)]})
        reactives = _make_reactives_shiny(Weights_Data=only_date_df)
        result = rpe.export_plot_weights_pie(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_boolean_only_weight_columns_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean-only weight columns are excluded instead of being coerced into pie weights."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        bool_weight_df = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1)],
                "Flag": [False],
            }
        )
        reactives = _make_reactives_shiny(Weights_Data=bool_weight_df)
        result = rpe.export_plot_weights_pie(reactives_shiny = reactives)
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Skfolio_Weights_Extra:
    """Extra branch tests for export_plot_skfolio_weights."""

    @pytest.mark.unit()
    def Test_polars_df_input_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Polars DataFrame input — covers line 1178 (to_pandas branch)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        results_table = pl.DataFrame({
            "Asset": ["AAPL", "MSFT", "GOOG"],
            "Portfolio_MVO": [0.4, 0.35, 0.25],
            "Portfolio_ERC": [0.33, 0.33, 0.34],
        })
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Skfolio_Results_Table=results_table)
            result = rpe.export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_list_input_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List input — covers lines 1181-1184 (pd.DataFrame(results_raw) branch)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        results_list = [
            {"Asset": "AAPL", "Portfolio_MVO": 0.4, "Portfolio_ERC": 0.33},
            {"Asset": "MSFT", "Portfolio_MVO": 0.35, "Portfolio_ERC": 0.33},
            {"Asset": "GOOG", "Portfolio_MVO": 0.25, "Portfolio_ERC": 0.34},
        ]
        with patch.object(_rpe_alloc_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Skfolio_Results_Table=results_list)
            result = rpe.export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_unsupported_type_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unsupported type for results_raw returns None — covers line 1187."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        reactives = _make_reactives_shiny(Skfolio_Results_Table="invalid_type")
        result = rpe.export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_too_few_columns_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Results table with fewer than 3 columns returns None — covers line 1192."""
        import pandas as pd
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        two_col_df = pd.DataFrame({"Asset": ["AAPL", "MSFT"], "Portfolio_MVO": [0.5, 0.5]})
        reactives = _make_reactives_shiny(Skfolio_Results_Table=two_col_df)
        result = rpe.export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_empty_results_table_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty results table (pdf.empty) returns None — covers line 1187."""
        import pandas as pd
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        empty_df = pd.DataFrame()
        reactives = _make_reactives_shiny(Skfolio_Results_Table=empty_df)
        result = rpe.export_plot_skfolio_weights(reactives_shiny = reactives)
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Skfolio_Performance_Extra:
    """Extra branch tests for export_plot_skfolio_performance."""

    @pytest.mark.unit()
    def Test_no_value_cols_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Performance DataFrame with only Date column returns None — covers line 1250."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        only_date_df = pl.DataFrame({
            "Date": [datetime.date(2024, 1, i + 1) for i in range(5)],
        })
        reactives = _make_reactives_shiny(Skfolio_Performance_Data=only_date_df)
        result = rpe.export_plot_skfolio_performance(reactives_shiny = reactives)
        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Simulation_Fan_Chart_Extra:
    """Extra branch tests for export_plot_simulation_fan_chart."""

    @pytest.mark.unit()
    def Test_fan_data_without_p5_p95_skips_outer_band(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fan data missing p5/p95 columns — covers 1307->1310 False branch."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "median": [100.0] * 10,
            "mean": [101.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_fan_data_without_p25_p75_skips_inner_band(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fan data missing p25/p75 columns — covers 1321->1325 False branch."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "p5": [80.0] * 10,
            "p95": [120.0] * 10,
            "mean": [101.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_fan_data_without_median_skips_median_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fan data missing median column — covers 1329->1333 False branch."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "p5": [80.0] * 10,
            "p25": [90.0] * 10,
            "p75": [110.0] * 10,
            "p95": [120.0] * 10,
            "mean": [101.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_fan_data_without_mean_skips_mean_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fan data missing mean column — covers 1333->1337 False branch."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "p5": [80.0] * 10,
            "p25": [90.0] * 10,
            "median": [100.0] * 10,
            "p75": [110.0] * 10,
            "p95": [120.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_fan_data_without_day_column_adds_range_index(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fan data without 'day' column — covers line 1311-1312."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        fan_data = pl.DataFrame({
            "p5": [80.0] * 10,
            "p25": [90.0] * 10,
            "median": [100.0] * 10,
            "mean": [101.0] * 10,
            "p75": [110.0] * 10,
            "p95": [120.0] * 10,
        })
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_boolean_fan_columns_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean percentile columns should not be exported as numeric fan data."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fan_data = pl.DataFrame({
            "day": list(range(10)),
            "median": [True, False] * 5,
            "mean": [True, False] * 5,
        })

        reactives = _make_reactives_shiny(Simulation_Fan_Data=fan_data)

        result = rpe.export_plot_simulation_fan_chart(reactives_shiny = reactives)

        assert result is None

    @pytest.mark.unit()
    def Test_no_fan_data_but_sample_csv_available_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When Simulation_Fan_Data is None but sample CSV loads OK — covers 1307->1310."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        # Provide a sample CSV that will be loaded via _load_sample_csv_for_plots
        sample_pv = _portfolio_df(30)
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (sample_pv, None))
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            result = rpe.export_plot_simulation_fan_chart(reactives_shiny = None)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_no_data_and_csv_unavailable_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No fan data and no sample CSV — covers 1307->1310 False branch and 1311-1312."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (None, None))
        result = rpe.export_plot_simulation_fan_chart(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_boolean_sample_csv_values_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean sample portfolio values should not generate fallback fan data."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        sample_pv = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (sample_pv, None))

        result = rpe.export_plot_simulation_fan_chart(reactives_shiny = None)

        assert result is None


@pytest.mark.unit()
class Class_Test_Export_Plot_Simulation_Histogram_Extra:
    """Extra branch tests for export_plot_simulation_histogram."""

    @pytest.mark.unit()
    def Test_no_terminal_values_but_sample_csv_available_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When terminal_values is None but sample CSV loads OK — covers lines 1374->1385."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        sample_pv = _portfolio_df(30)
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (sample_pv, None))
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            result = rpe.export_plot_simulation_histogram(reactives_shiny = None)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_no_terminal_values_and_no_csv_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No terminal values and no sample CSV — covers 1374->1385 False branch and 1386."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (None, None))
        result = rpe.export_plot_simulation_histogram(reactives_shiny = None)
        assert result is None

    @pytest.mark.unit()
    def Test_polars_df_terminal_values_saves_svg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Polars DataFrame terminal values — covers line 1391 (to_pandas branch)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        fake_path = tmp_path / "chart.svg"
        terminal_vals = pl.DataFrame({"terminal_value": [100.0, 110.0, 90.0, 95.0, 105.0]})
        with patch.object(_rpe_risk_mod, "_save_plot", return_value=fake_path):
            reactives = _make_reactives_shiny(Simulation_Terminal_Values=terminal_vals)
            result = rpe.export_plot_simulation_histogram(reactives_shiny = reactives)
        assert result == fake_path

    @pytest.mark.unit()
    def Test_unsupported_type_terminal_values_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dict terminal values (unsupported type) — covers line 1395 (else return None)."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        reactives = _make_reactives_shiny(Simulation_Terminal_Values={"bad": "data"})
        result = rpe.export_plot_simulation_histogram(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_empty_list_terminal_values_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty list terminal values — vals.empty → covers line 1398."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        reactives = _make_reactives_shiny(Simulation_Terminal_Values=[])
        result = rpe.export_plot_simulation_histogram(reactives_shiny = reactives)
        assert result is None

    @pytest.mark.unit()
    def Test_boolean_terminal_values_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean terminal values should not be exported as numeric histogram data."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        reactives = _make_reactives_shiny(
            Simulation_Terminal_Values=[100.0, True, 110.0],
        )

        result = rpe.export_plot_simulation_histogram(reactives_shiny = reactives)

        assert result is None

    @pytest.mark.unit()
    def Test_boolean_sample_csv_values_return_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean sample portfolio values should not generate fallback histogram data."""
        import src.dashboard.reporting.report_plot_export as rpe

        monkeypatch.setattr(_rpe_returns_mod, "_IMAGES_DIR", tmp_path)
        sample_pv = pl.DataFrame(
            {
                "Date": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
                "portfolio_value": [True, False],
            },
        )
        monkeypatch.setattr(_rpe_risk_mod, "_load_sample_csv_for_plots", lambda: (sample_pv, None))

        result = rpe.export_plot_simulation_histogram(reactives_shiny = None)

        assert result is None


