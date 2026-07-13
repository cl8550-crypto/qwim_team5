"""Focused helper tests for the portfolio analysis subtab split."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pandas as pd
import polars as pl
import pytest

import src.dashboard.shiny_tab_portfolios._subtab_portfolios_analysis_data as analysis_data
import src.dashboard.shiny_tab_portfolios._subtab_portfolios_analysis_rendering as rendering
from src.dashboard.shiny_tab_portfolios._subtab_portfolios_analysis_data import (
    _normalize_date_strings,
    build_calculated_date_range_text,
    build_filtered_analysis_data,
    create_empty_analysis_frame,
    filter_analysis_dataframe,
    resolve_analysis_date_range,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)


class _FakeFigure:
    """Simple figure stub for plot helper tests."""

    def __init__(self) -> None:
        self.layout_calls: list[dict[str, Any]] = []

    def update_layout(self, **kwargs: Any) -> None:
        self.layout_calls.append(kwargs)


class _FakeSelectResult:
    """Minimal select-result stub exposing Polars dtype metadata."""

    def __init__(
        self,
        date_dtype: pl.DataType,
    ) -> None:
        self.dtypes = [date_dtype]


class _FakeNormalizationFrame:
    """Minimal frame stub for private date-normalization helper tests."""

    def __init__(
        self,
        date_dtype: pl.DataType,
        outcomes: list[Any],
    ) -> None:
        self._date_dtype = date_dtype
        self._outcomes = list(outcomes)

    def select(
        self,
        _column_name: str,
    ) -> _FakeSelectResult:
        return _FakeSelectResult(self._date_dtype)

    def with_columns(
        self,
        _expressions: list[Any],
    ) -> Any:
        outcome_current = self._outcomes.pop(0)
        if isinstance(outcome_current, Exception):
            raise outcome_current
        return outcome_current


class _FakeFilteredFrame:
    """Minimal filtered-frame stub for datetime-conversion error coverage."""

    def __init__(
        self,
        *,
        should_raise_on_with_columns: bool,
    ) -> None:
        self.height = 1
        self._should_raise_on_with_columns = should_raise_on_with_columns

    def filter(
        self,
        _expression: Any,
    ) -> _FakeFilteredFrame:
        return self

    def is_empty(self) -> bool:
        return False

    def with_columns(
        self,
        _expressions: list[Any],
    ) -> _FakeFilteredFrame:
        if self._should_raise_on_with_columns:
            raise ValueError("bad Date_String")
        return self

    def select(
        self,
        _columns: list[str],
    ) -> _FakeFilteredFrame:
        return self

    def sort(
        self,
        _column_name: str,
    ) -> _FakeFilteredFrame:
        return self


class _Input_Value_Fake:
    """Simple callable input stub used by registered-output tests."""

    def __init__(
        self,
        value_current: Any = None,
        error_current: Exception | None = None,
    ) -> None:
        self._value_current = value_current
        self._error_current = error_current

    def __call__(self) -> Any:
        if self._error_current is not None:
            raise self._error_current
        return self._value_current


@pytest.fixture()
def fixture_large_string_frame() -> pl.DataFrame:
    """Return a large frame with string dates for filtering/downsampling checks."""
    base_date = datetime(2024, 1, 1, tzinfo=UTC)
    dates = [(base_date + timedelta(days=index)).strftime("%Y-%m-%d") for index in range(260)]
    values = [float(index + 1) for index in range(260)]
    return pl.DataFrame({"Date": dates, "Value": values})


@pytest.fixture()
def fixture_small_datetime_frame() -> pl.DataFrame:
    """Return a small frame with datetime values for rendering helpers."""
    base_date = datetime(2024, 1, 1, tzinfo=UTC)
    dates = [base_date + timedelta(days=index) for index in range(4)]
    values = [100.0, 101.0, 102.0, 103.0]
    return pl.DataFrame({"Date": dates, "Value": values})


@pytest.fixture()
def fixture_captured_portfolios_analysis_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    monkeypatch.setattr(rendering.reactive, "calc", lambda function: function)
    monkeypatch.setattr(rendering.render, "text", lambda function: function)
    monkeypatch.setattr(rendering.render, "ui", lambda function: function)
    monkeypatch.setattr(rendering.render, "table", lambda function: function)
    monkeypatch.setattr(rendering, "render_widget", lambda function: function)

    captured_outputs: dict[str, Any] = {}

    def decorator_output(function: Any) -> Any:
        captured_outputs[function.__name__] = function
        return function

    captured_outputs["decorator_output"] = decorator_output
    return captured_outputs


def _build_input_portfolios_analysis_fake(
    *,
    time_period: Any = "1y",
    analysis_type: Any = "returns",
    include_benchmark: Any = True,
    rolling_window: Any = 30,
    date_range: Any = None,
    time_period_error: Exception | None = None,
) -> Any:
    return SimpleNamespace(
        input_ID_tab_portfolios_subtab_portfolios_analysis_time_period=_Input_Value_Fake(
            time_period,
            error_current=time_period_error,
        ),
        input_ID_tab_portfolios_subtab_portfolios_analysis_type=_Input_Value_Fake(
            analysis_type,
        ),
        input_ID_tab_portfolios_subtab_portfolios_analysis_include_benchmark=_Input_Value_Fake(
            include_benchmark,
        ),
        input_ID_tab_portfolios_subtab_portfolios_analysis_rolling_window=_Input_Value_Fake(
            rolling_window,
        ),
        input_ID_tab_portfolios_subtab_portfolios_analysis_date_range=_Input_Value_Fake(
            date_range,
        ),
    )


@pytest.mark.unit()
class Class_Test_Subtab_Portfolios_Analysis_Data_Helpers:
    """Exercise the extracted date-range and dataframe helpers."""

    def test_resolve_analysis_date_range_custom_normalizes_values(self) -> None:
        """Custom date ranges normalize date-like objects into filter strings."""
        start_date, end_date = resolve_analysis_date_range(
            time_period = "custom",
            custom_date_range=[date(2024, 1, 1), "2024-02-15T10:30:00"],
        )

        assert start_date == "2024-01-01"
        assert end_date == "2024-02-15"

    def test_build_calculated_date_range_text_uses_expected_bounds(self) -> None:
        """Preset date labels reflect the same helper date arithmetic."""
        text = build_calculated_date_range_text(
            time_period = "1y",
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert text == "📅 2025-05-29 to 2026-05-29"

    def test_resolve_analysis_date_range_custom_invalid_values_fall_back_to_one_year(self) -> None:
        """Invalid custom inputs fall back to a 1-year range ending today."""
        start_date, end_date = resolve_analysis_date_range(
            time_period = "custom",
            custom_date_range=object(),
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert start_date == "2025-05-29"
        assert end_date == "2026-05-29"

    def test_resolve_analysis_date_range_custom_incomplete_values_fall_back_to_one_year(self) -> None:
        """Incomplete custom ranges also fall back to the default 1-year window."""
        start_date, end_date = resolve_analysis_date_range(
            time_period = "custom",
            custom_date_range=[date(2024, 1, 1)],
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert start_date == "2025-05-29"
        assert end_date == "2026-05-29"

    @pytest.mark.parametrize(
        ("time_period", "expected_start_date"),
        [
            ("3y", "2023-05-30"),
            ("5y", "2021-05-30"),
            ("10y", "2016-05-31"),
            ("ytd", "2026-01-01"),
            ("unexpected", "2025-05-29"),
        ],
    )
    def test_resolve_analysis_date_range_supports_remaining_presets(
        self,
        time_period: str,
        expected_start_date: str,
    ) -> None:
        """All preset branches resolve deterministic start dates."""
        start_date, end_date = resolve_analysis_date_range(
            time_period = time_period,
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert start_date == expected_start_date
        assert end_date == "2026-05-29"

    def test_build_calculated_date_range_text_returns_empty_for_custom(self) -> None:
        """Custom ranges omit the derived preset label text."""
        assert build_calculated_date_range_text(time_period = "custom") == ""

    def test_normalize_date_strings_uses_unknown_type_attempts_after_string_failures(self) -> None:
        """String normalization exhausts its first attempts before using fallback casts."""
        frame_fake = _FakeNormalizationFrame(
            pl.String,
            [
                ValueError("datetime parse failed"),
                TypeError("date parse failed"),
                pl.exceptions.ComputeError("slice failed"),
                AttributeError("cast datetime failed"),
                "normalized-frame",
            ],
        )

        normalized_frame = _normalize_date_strings(data_frame = frame_fake, label="Portfolio")

        assert normalized_frame == "normalized-frame"

    def test_normalize_date_strings_uses_last_resort_cast_for_unknown_types(self) -> None:
        """Unknown dtypes fall through to the final string-cast fallback."""
        frame_fake = _FakeNormalizationFrame(
            pl.Int64,
            [
                ValueError("unknown cast failed"),
                TypeError("slice fallback failed"),
                "fallback-normalized-frame",
            ],
        )

        normalized_frame = _normalize_date_strings(data_frame = frame_fake, label="Portfolio")

        assert normalized_frame == "fallback-normalized-frame"

    def test_filter_analysis_dataframe_accepts_date_dtype(self) -> None:
        """Date-typed source frames are filtered and converted to datetime output."""
        source_frame = pl.DataFrame(
            {
                "Date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
                "Value": [1.0, 2.0, 3.0],
            },
        )

        filtered_frame = filter_analysis_dataframe(
            data_frame = source_frame,
            start_date_str="2024-01-01",
            end_date_str="2024-01-03",
            label="Portfolio",
        )

        assert filtered_frame.height == 3
        assert str(filtered_frame.schema["Date"]).startswith("Datetime")

    def test_filter_analysis_dataframe_returns_empty_for_missing_columns(self) -> None:
        """Missing Value columns fall back to the canonical empty frame."""
        filtered_frame = filter_analysis_dataframe(
            data_frame = pl.DataFrame({"Date": ["2024-01-01"]}),
            start_date_str="2024-01-01",
            end_date_str="2024-01-02",
            label="Portfolio",
        )

        assert filtered_frame.equals(create_empty_analysis_frame())

    def test_filter_analysis_dataframe_returns_empty_for_none_input(self) -> None:
        """None inputs return the canonical empty analysis frame."""
        filtered_frame = filter_analysis_dataframe(
            data_frame = None,
            start_date_str="2024-01-01",
            end_date_str="2024-01-02",
            label="Portfolio",
        )

        assert filtered_frame.equals(create_empty_analysis_frame())

    def test_filter_analysis_dataframe_returns_empty_when_range_removes_all_rows(self) -> None:
        """Ranges outside the available dates return the canonical empty frame."""
        filtered_frame = filter_analysis_dataframe(
            data_frame = pl.DataFrame(
                {
                    "Date": ["2024-01-01", "2024-01-02"],
                    "Value": [1.0, 2.0],
                },
            ),
            start_date_str="2025-01-01",
            end_date_str="2025-01-02",
            label="Portfolio",
        )

        assert filtered_frame.equals(create_empty_analysis_frame())

    def test_filter_analysis_dataframe_returns_empty_when_datetime_conversion_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Datetime conversion failures fall back to the canonical empty frame."""
        monkeypatch.setattr(
            analysis_data,
            "_normalize_date_strings",
            lambda data_frame, *, label: _FakeFilteredFrame(
                should_raise_on_with_columns=True,
            ),
        )

        filtered_frame = filter_analysis_dataframe(
            data_frame = pl.DataFrame({"Date": ["2024-01-01"], "Value": [1.0]}),
            start_date_str="2024-01-01",
            end_date_str="2024-01-02",
            label="Portfolio",
        )

        assert filtered_frame.equals(create_empty_analysis_frame())

    def test_build_filtered_analysis_data_downsamples_large_frames(
        self,
        fixture_large_string_frame: pl.DataFrame,
    ) -> None:
        """Large portfolio and benchmark frames are filtered and downsampled."""
        filtered_portfolio, filtered_benchmark = build_filtered_analysis_data(
            data_portfolio=fixture_large_string_frame,
            data_benchmark=fixture_large_string_frame,
            time_period="custom",
            custom_date_range=[date(2024, 1, 1), date(2024, 9, 16)],
        )

        assert filtered_portfolio.height <= 200
        assert filtered_benchmark.height <= 200
        assert filtered_portfolio.height > 0

    def test_build_filtered_analysis_data_returns_empty_frames_when_inputs_missing(self) -> None:
        """Missing portfolio and benchmark inputs return the canonical empty tuple."""
        filtered_portfolio, filtered_benchmark = build_filtered_analysis_data(
            data_portfolio=None,
            data_benchmark=None,
            time_period="1y",
        )

        assert filtered_portfolio.equals(create_empty_analysis_frame())
        assert filtered_benchmark.equals(create_empty_analysis_frame())

    def test_build_filtered_analysis_data_skips_portfolio_downsampling_when_empty(
        self,
        fixture_large_string_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Only non-empty filtered frames are downsampled."""
        downsampled_labels: list[int] = []

        monkeypatch.setattr(
            analysis_data,
            "downsample_dataframe",
            lambda *, polars_DF, **kwargs: downsampled_labels.append(polars_DF.height) or polars_DF,
        )

        filtered_portfolio, filtered_benchmark = build_filtered_analysis_data(
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=fixture_large_string_frame,
            time_period="custom",
            custom_date_range=[date(2024, 1, 1), date(2024, 9, 16)],
        )

        assert filtered_portfolio.equals(create_empty_analysis_frame())
        assert filtered_benchmark.height > 0
        assert downsampled_labels == [filtered_benchmark.height]

    def test_build_filtered_analysis_data_skips_benchmark_downsampling_when_empty(
        self,
        fixture_large_string_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Benchmark downsampling is skipped when the filtered benchmark is empty."""
        downsampled_labels: list[int] = []

        monkeypatch.setattr(
            analysis_data,
            "downsample_dataframe",
            lambda *, polars_DF, **kwargs: downsampled_labels.append(polars_DF.height) or polars_DF,
        )

        filtered_portfolio, filtered_benchmark = build_filtered_analysis_data(
            data_portfolio=fixture_large_string_frame,
            data_benchmark=create_empty_analysis_frame(),
            time_period="custom",
            custom_date_range=[date(2024, 1, 1), date(2024, 9, 16)],
        )

        assert filtered_portfolio.height > 0
        assert filtered_benchmark.equals(create_empty_analysis_frame())
        assert downsampled_labels == [filtered_portfolio.height]

    def test_build_filtered_analysis_data_wraps_helper_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unexpected helper failures are wrapped in Exception_Configuration."""
        monkeypatch.setattr(
            analysis_data,
            "resolve_analysis_date_range",
            lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad range")),
        )

        with pytest.raises(Exception_Configuration, match="bad range"):
            build_filtered_analysis_data(
                data_portfolio=pl.DataFrame({"Date": ["2024-01-01"], "Value": [1.0]}),
                data_benchmark=None,
                time_period="1y",
            )


@pytest.mark.unit()
class Class_Test_Subtab_Portfolios_Analysis_Rendering_Helpers:
    """Exercise the extracted rendering and formatting helpers."""

    def test_resolve_analysis_and_period_labels_use_expected_defaults(self) -> None:
        """Unknown labels fall back to the generic analysis and period labels."""
        assert rendering.resolve_analysis_label(analysis_type = "drawdowns") == "Drawdowns Analysis"
        assert rendering.resolve_analysis_label(analysis_type = "unknown") == "Analysis"
        assert rendering.resolve_period_label(time_period = "5y") == "Last 5 Years"
        assert rendering.resolve_period_label(time_period = "unknown") == "Selected Period"

    @pytest.mark.parametrize(
        ("portfolio_count", "benchmark_count", "expected_text"),
        [
            (40, 20, "Ready for analysis"),
            (10, 0, "Limited data available"),
            (0, 0, "No portfolio data"),
        ],
    )
    def test_build_analysis_data_info_ui_covers_status_variants(
        self,
        portfolio_count: int,
        benchmark_count: int,
        expected_text: str,
    ) -> None:
        """The sidebar info panel reflects ready, limited, and empty states."""
        value_ui = rendering.build_analysis_data_info_ui(
            time_period="1y",
            analysis_type="returns",
            portfolio_count=portfolio_count,
            benchmark_count=benchmark_count,
        )

        assert expected_text in str(value_ui)

    @pytest.mark.parametrize(
        ("portfolio_count", "analysis_type", "expected_text"),
        [
            (0, "returns", "No portfolio data available for the selected period"),
            (10, "rolling", "Limited data available (10 points)"),
            (40, "comparison", "Ready for Portfolio vs Benchmark"),
        ],
    )
    def test_build_loading_status_ui_covers_status_variants(
        self,
        portfolio_count: int,
        analysis_type: str,
        expected_text: str,
    ) -> None:
        """The loading alert reflects empty, limited, and ready states."""
        value_ui = rendering.build_loading_status_ui(portfolio_count = portfolio_count, analysis_type = analysis_type)

        assert expected_text in str(value_ui)

    def test_resolve_benchmark_data_requires_selection_and_non_empty_frame(self) -> None:
        """Benchmark data is returned only when enabled and non-empty."""
        frame_benchmark = pl.DataFrame(
            {"Date": [datetime(2024, 1, 1, tzinfo=UTC)], "Value": [1.0]},
        )

        assert (
            rendering._resolve_benchmark_data(
                data_benchmark_filtered = frame_benchmark,
                include_benchmark=False,
            )
            is None
        )
        assert (
            rendering._resolve_benchmark_data(
                data_benchmark_filtered = create_empty_analysis_frame(),
                include_benchmark=True,
            )
            is None
        )

    @pytest.mark.parametrize(
        ("analysis_type", "plot_helper_name"),
        [
            ("drawdowns", "create_plot_drawdowns_analysis"),
            ("rolling", "create_plot_rolling_statistics"),
            ("comparison", "create_plot_portfolios_comparison"),
        ],
    )
    def test_build_analysis_figure_supports_remaining_plot_types(
        self,
        analysis_type: str,
        plot_helper_name: str,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Each explicit analysis type selects its matching plot helper."""
        captured_calls: dict[str, Any] = {}
        fake_figure = _FakeFigure()

        monkeypatch.setattr(
            rendering,
            plot_helper_name,
            lambda **kwargs: captured_calls.update(kwargs) or fake_figure,
        )
        monkeypatch.setattr(
            rendering,
            "build_plotnine_portfolio_analysis_returns_distribution",
            lambda **kwargs: "plotnine-snapshot",
        )
        monkeypatch.setattr(
            rendering,
            "update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure: reactives_shiny.setdefault("Visual_Objects_Shiny", {})
            .update({chart_key: figure}),
        )

        reactives_shiny: dict[str, Any] = {}
        figure = rendering.build_analysis_figure(
            analysis_type=analysis_type,
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=fixture_small_datetime_frame,
            include_benchmark=True,
            rolling_window=45,
            reactives_shiny=reactives_shiny,
        )

        assert figure is fake_figure
        assert captured_calls["data_portfolio"].equals(fixture_small_datetime_frame)
        assert reactives_shiny["Visual_Objects_Shiny"][
            "Chart_Portfolio_Analysis_Returns_Distribution"
        ] == "plotnine-snapshot"

    def test_build_analysis_figure_returns_error_when_plot_builder_fails(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A missing figure from the plot helper falls back to an error figure."""
        monkeypatch.setattr(
            rendering,
            "create_plot_returns_distribution",
            lambda **kwargs: None,
        )
        monkeypatch.setattr(
            rendering,
            "create_error_figure",
            lambda *, message_text, **_: {"message": message_text},
        )

        figure = rendering.build_analysis_figure(
            analysis_type="returns",
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
            rolling_window=30,
            reactives_shiny={},
        )

        assert figure == {"message": "Failed to generate analysis plot"}

    def test_build_analysis_figure_returns_error_for_empty_portfolio_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty portfolio inputs return the no-data error figure."""
        monkeypatch.setattr(
            rendering,
            "create_error_figure",
            lambda *, message_text, **_: {"message": message_text},
        )

        figure = rendering.build_analysis_figure(
            analysis_type="returns",
            data_portfolio_filtered=create_empty_analysis_frame(),
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
            rolling_window=30,
            reactives_shiny={},
        )

        assert figure == {"message": "No portfolio data available for the selected time period"}

    def test_metric_format_type_treats_drawdowns_as_percentages(self) -> None:
        """Drawdown-style metric labels use percentage formatting."""
        assert rendering._metric_format_type(metric_name = "max drawdown") == "percentage"

    @pytest.mark.parametrize(
        ("statistic_name", "expected_format_type"),
        [
            ("min return", "decimal"),
            ("observations", "integer"),
            ("other statistic", "decimal"),
        ],
    )
    def test_statistic_format_type_covers_remaining_label_groups(
        self,
        statistic_name: str,
        expected_format_type: str,
    ) -> None:
        """Statistic labels map to the expected remaining format branches."""
        assert rendering._statistic_format_type(metric_name = statistic_name) == expected_format_type

    def test_format_metrics_table_keeps_original_value_when_formatting_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Formatting errors leave the original numeric value in place."""
        monkeypatch.setattr(
            rendering,
            "format_value_for_display",
            lambda *, value_input, format_type, **___: (_ for _ in ()).throw(ValueError("bad format")),
        )
        metrics_table = pd.DataFrame(
            {
                "Metric": ["Annual Return"],
                "Portfolio": [0.12],
                "Benchmark": [0.03],
            },
        )

        formatted_table = rendering.format_metrics_table_for_display(metrics_table = metrics_table)

        assert formatted_table.at[0, "Portfolio"] == 0.12
        assert formatted_table.at[0, "Benchmark"] == 0.03

    def test_format_table_values_skips_missing_columns_and_non_numeric_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Formatting skips absent columns and rows with non-numeric, boolean, or NaN values."""
        format_calls: list[tuple[Any, str]] = []

        monkeypatch.setattr(
            rendering,
            "format_value_for_display",
            lambda *, value_input, format_type, **___: format_calls.append((value_input, format_type)) or f"{format_type}:{value_input}",
        )
        metrics_table = pd.DataFrame(
            {
                "Metric": ["Annual Return", "Days Held", "Alpha", "Boolean Flag"],
                "Portfolio": [0.12, "not numeric", float("nan"), True],
            },
        )

        formatted_table = rendering._format_table_values(
            table = metrics_table,
            label_column="Metric",
            value_columns=("Portfolio", "Benchmark"),
            format_selector=rendering._metric_format_type,
        )

        assert format_calls == [(0.12, "percentage")]
        assert formatted_table.at[1, "Portfolio"] == "not numeric"
        assert pd.isna(formatted_table.at[2, "Portfolio"])
        assert formatted_table.at[3, "Portfolio"] is True

    def test_build_fallback_table_omits_benchmark_when_disabled(self) -> None:
        """Benchmark columns are omitted when benchmark display is disabled."""
        fallback_table = rendering.build_fallback_table(
            label_column="Metric",
            label_value="No Data Available",
            include_benchmark=False,
        )

        assert list(fallback_table.columns) == ["Metric", "Portfolio"]

    def test_format_metrics_table_for_display_uses_expected_formats(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Metrics formatting selects percentage, integer, and decimal output types."""
        monkeypatch.setattr(
            rendering,
            "format_value_for_display",
            lambda *, value_input, format_type, **___: f"{format_type}:{value_input}",
        )
        metrics_table = pd.DataFrame(
            {
                "Metric": ["Annual Return", "Days Held", "Alpha"],
                "Portfolio": [0.12, 10, 1.5],
                "Benchmark": [0.03, 8, 1.0],
            },
        )

        formatted_table = rendering.format_metrics_table_for_display(metrics_table = metrics_table)

        assert formatted_table.at[0, "Portfolio"] == "percentage:0.12"
        assert formatted_table.at[1, "Portfolio"] == "integer:10"
        assert formatted_table.at[2, "Portfolio"] == "decimal:1.5"

    def test_format_stats_table_for_display_uses_expected_formats(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Statistics formatting selects decimal and integer output types."""
        monkeypatch.setattr(
            rendering,
            "format_value_for_display",
            lambda *, value_input, format_type, **___: f"{format_type}:{value_input}",
        )
        stats_table = pd.DataFrame(
            {
                "Statistic": ["Mean", "Count", "Skew"],
                "Portfolio": [1.25, 20, 0.4],
                "Benchmark": [1.0, 18, 0.2],
            },
        )

        formatted_table = rendering.format_stats_table_for_display(stats_table = stats_table)

        assert formatted_table.at[0, "Portfolio"] == "decimal:1.25"
        assert formatted_table.at[1, "Portfolio"] == "integer:20"
        assert formatted_table.at[2, "Portfolio"] == "decimal:0.4"

    def test_build_analysis_figure_defaults_to_returns_and_updates_snapshot(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unknown analysis types fall back to returns and still update shared visuals."""
        captured_plot_call: dict[str, Any] = {}
        fake_figure = _FakeFigure()

        def _fake_returns_plot(**kwargs: Any) -> _FakeFigure:
            captured_plot_call.update(kwargs)
            return fake_figure

        monkeypatch.setattr(rendering, "create_plot_returns_distribution", _fake_returns_plot)
        monkeypatch.setattr(
            rendering,
            "build_plotnine_portfolio_analysis_returns_distribution",
            lambda **kwargs: "plotnine-snapshot",
        )
        monkeypatch.setattr(
            rendering,
            "update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure: reactives_shiny.setdefault("Visual_Objects_Shiny", {})
            .update({chart_key: figure}),
        )

        reactives_shiny: dict[str, Any] = {}
        figure = rendering.build_analysis_figure(
            analysis_type="unknown",
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
            rolling_window=30,
            reactives_shiny=reactives_shiny,
        )

        assert figure is fake_figure
        assert captured_plot_call["include_benchmark"] is False
        assert fake_figure.layout_calls
        assert reactives_shiny["Visual_Objects_Shiny"][
            "Chart_Portfolio_Analysis_Returns_Distribution"
        ] == "plotnine-snapshot"

    def test_build_metrics_table_returns_no_data_fallback(self) -> None:
        """Empty portfolio inputs return the no-data metrics table."""
        metrics_table = rendering.build_metrics_table(
            data_portfolio_filtered=create_empty_analysis_frame(),
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert list(metrics_table.columns) == ["Metric", "Portfolio"]
        assert metrics_table.at[0, "Metric"] == "No Data Available"

    def test_build_metrics_table_returns_calculation_error_fallback(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty metrics calculations return the calculation-error fallback table."""
        monkeypatch.setattr(
            rendering,
            "calculate_table_metrics_performance",
            lambda **_kwargs: pd.DataFrame(),
        )

        metrics_table = rendering.build_metrics_table(
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert list(metrics_table.columns) == ["Metric", "Portfolio"]
        assert metrics_table.at[0, "Metric"] == "Calculation Error"

    def test_build_metrics_table_formats_successful_calculation(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Successful metrics calculations are passed through the formatter."""
        metrics_source = pd.DataFrame({"Metric": ["Annual Return"], "Portfolio": [0.12]})

        monkeypatch.setattr(
            rendering,
            "calculate_table_metrics_performance",
            lambda **_kwargs: metrics_source,
        )
        monkeypatch.setattr(
            rendering,
            "format_metrics_table_for_display",
            lambda *, metrics_table, **___: metrics_table.assign(Portfolio=["formatted-metric"]),
        )

        metrics_table = rendering.build_metrics_table(
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert metrics_table.at[0, "Portfolio"] == "formatted-metric"

    def test_build_stats_table_returns_calculation_error_fallback(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty stats calculations return the calculation-error fallback table."""
        monkeypatch.setattr(
            rendering,
            "calculate_table_stats_basic",
            lambda **_kwargs: pd.DataFrame(),
        )

        stats_table = rendering.build_stats_table(
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert list(stats_table.columns) == ["Statistic", "Portfolio"]
        assert stats_table.at[0, "Statistic"] == "Calculation Error"

    def test_build_stats_table_returns_no_data_fallback(self) -> None:
        """Empty portfolio inputs return the no-data stats table."""
        stats_table = rendering.build_stats_table(
            data_portfolio_filtered=create_empty_analysis_frame(),
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert list(stats_table.columns) == ["Statistic", "Portfolio"]
        assert stats_table.at[0, "Statistic"] == "No Data Available"

    def test_build_stats_table_formats_successful_calculation(
        self,
        fixture_small_datetime_frame: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Successful stats calculations are passed through the formatter."""
        stats_source = pd.DataFrame({"Statistic": ["Mean"], "Portfolio": [1.25]})

        monkeypatch.setattr(
            rendering,
            "calculate_table_stats_basic",
            lambda **_kwargs: stats_source,
        )
        monkeypatch.setattr(
            rendering,
            "format_stats_table_for_display",
            lambda *, stats_table, **___: stats_table.assign(Portfolio=["formatted-stat"]),
        )

        stats_table = rendering.build_stats_table(
            data_portfolio_filtered=fixture_small_datetime_frame,
            data_benchmark_filtered=create_empty_analysis_frame(),
            include_benchmark=False,
        )

        assert stats_table.at[0, "Portfolio"] == "formatted-stat"

    def test_register_portfolios_analysis_outputs_captures_expected_functions(
        self,
        fixture_captured_portfolios_analysis_outputs: dict[str, Any],
    ) -> None:
        """Registered outputs expose the expected rendering callbacks."""
        rendering.register_portfolios_analysis_outputs(
            input=_build_input_portfolios_analysis_fake(),
            output=fixture_captured_portfolios_analysis_outputs["decorator_output"],
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=create_empty_analysis_frame(),
            reactives_shiny={},
        )

        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_calculated_date_range" in fixture_captured_portfolios_analysis_outputs
        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_data_info" in fixture_captured_portfolios_analysis_outputs
        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_loading_status" in fixture_captured_portfolios_analysis_outputs
        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_plot_main" in fixture_captured_portfolios_analysis_outputs
        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_table_quantstats_metrics" in fixture_captured_portfolios_analysis_outputs
        assert "output_ID_tab_portfolios_subtab_portfolios_analysis_table_stats" in fixture_captured_portfolios_analysis_outputs

    def test_registered_calculated_date_range_output_wraps_errors(
        self,
        fixture_captured_portfolios_analysis_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Calculated-date output wraps helper failures in Exception_Configuration."""
        monkeypatch.setattr(
            rendering,
            "build_calculated_date_range_text",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad range")),
        )

        rendering.register_portfolios_analysis_outputs(
            input=_build_input_portfolios_analysis_fake(),
            output=fixture_captured_portfolios_analysis_outputs["decorator_output"],
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=create_empty_analysis_frame(),
            reactives_shiny={},
        )

        with pytest.raises(Exception_Configuration, match="bad range"):
            fixture_captured_portfolios_analysis_outputs[
                "output_ID_tab_portfolios_subtab_portfolios_analysis_calculated_date_range"
            ]()

    def test_registered_loading_status_output_falls_back_on_error(
        self,
        fixture_captured_portfolios_analysis_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Loading-status output falls back to the loading message on failures."""
        monkeypatch.setattr(
            rendering,
            "build_loading_status_ui",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        rendering.register_portfolios_analysis_outputs(
            input=_build_input_portfolios_analysis_fake(),
            output=fixture_captured_portfolios_analysis_outputs["decorator_output"],
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=create_empty_analysis_frame(),
            reactives_shiny={},
        )

        value_ui = fixture_captured_portfolios_analysis_outputs[
            "output_ID_tab_portfolios_subtab_portfolios_analysis_loading_status"
        ]()

        assert "Loading analysis data" in str(value_ui)

    def test_registered_plot_output_returns_error_figure_on_exception(
        self,
        fixture_captured_portfolios_analysis_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Plot output returns the error figure when figure generation fails."""
        monkeypatch.setattr(
            rendering,
            "build_analysis_figure",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("plot broke")),
        )
        monkeypatch.setattr(
            rendering,
            "create_error_figure",
            lambda *, message_text, **_: {"message": message_text},
        )

        rendering.register_portfolios_analysis_outputs(
            input=_build_input_portfolios_analysis_fake(),
            output=fixture_captured_portfolios_analysis_outputs["decorator_output"],
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=create_empty_analysis_frame(),
            reactives_shiny={},
        )

        value_plot = fixture_captured_portfolios_analysis_outputs[
            "output_ID_tab_portfolios_subtab_portfolios_analysis_plot_main"
        ]()

        assert value_plot == {"message": "Error generating analysis plot: plot broke"}

    def test_registered_table_outputs_return_error_fallbacks(
        self,
        fixture_captured_portfolios_analysis_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Table outputs fall back to explicit error rows when builders fail."""
        monkeypatch.setattr(
            rendering,
            "build_metrics_table",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("metrics broke")),
        )
        monkeypatch.setattr(
            rendering,
            "build_stats_table",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stats broke")),
        )

        rendering.register_portfolios_analysis_outputs(
            input=_build_input_portfolios_analysis_fake(),
            output=fixture_captured_portfolios_analysis_outputs["decorator_output"],
            data_portfolio=create_empty_analysis_frame(),
            data_benchmark=create_empty_analysis_frame(),
            reactives_shiny={},
        )

        metrics_table = fixture_captured_portfolios_analysis_outputs[
            "output_ID_tab_portfolios_subtab_portfolios_analysis_table_quantstats_metrics"
        ]()
        stats_table = fixture_captured_portfolios_analysis_outputs[
            "output_ID_tab_portfolios_subtab_portfolios_analysis_table_stats"
        ]()

        assert metrics_table.at[0, "Metric"] == "Error"
        assert "metrics broke" in metrics_table.at[0, "Portfolio"]
        assert stats_table.at[0, "Statistic"] == "Error"
        assert "stats broke" in stats_table.at[0, "Portfolio"]
