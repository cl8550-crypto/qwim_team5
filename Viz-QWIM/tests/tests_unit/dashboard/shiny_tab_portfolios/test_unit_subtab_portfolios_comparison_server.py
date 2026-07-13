"""Unit tests for private portfolio comparison server helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pandas as pd
import polars as pl
import pytest

from src.dashboard.shiny_tab_portfolios import (
    _subtab_portfolios_comparison_server as comparison_server,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


def _naive_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
) -> datetime:
    """Create intentionally naive datetimes for helper comparisons."""
    return datetime(year, month, day, hour, minute, second, microsecond)  # noqa: DTZ001


class _Input_Portfolios_Comparison:
    def __init__(
        self,
        *,
        value_time_period: str = "1y",
        value_date_range: tuple[str, str] | None = None,
        value_viz_type: str = "normalized",
        value_show_diff: bool = False,
    ) -> None:
        self._value_time_period = value_time_period
        self._value_date_range = value_date_range
        self._value_viz_type = value_viz_type
        self._value_show_diff = value_show_diff

    def input_ID_tab_portfolios_subtab_comparison_time_period(self) -> str:
        return self._value_time_period

    def input_ID_tab_portfolios_subtab_comparison_date_range(self) -> tuple[str, str] | None:
        return self._value_date_range

    def input_ID_tab_portfolios_subtab_comparison_viz_type(self) -> str:
        return self._value_viz_type

    def input_ID_tab_portfolios_subtab_comparison_show_diff(self) -> bool:
        return self._value_show_diff


class _Value_With_To_Pydatetime:
    def __init__(
        self,
        value_datetime: datetime,
    ) -> None:
        self._value_datetime = value_datetime

    def to_pydatetime(self) -> datetime:
        return self._value_datetime


class _Empty_State_Frame_Fake:
    def __init__(
        self,
        values_empty: list[bool],
    ) -> None:
        self._values_empty = list(values_empty)

    def is_empty(self) -> bool:
        if len(self._values_empty) > 1:
            return self._values_empty.pop(0)
        return self._values_empty[0]


@pytest.fixture()
def fixture_comparison_frame_portfolio() -> pl.DataFrame:
    """Return a small portfolio frame with string dates."""
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "Value": [100.0, 101.0, 102.0, 103.0],
        },
    )


@pytest.fixture()
def fixture_comparison_frame_benchmark() -> pl.DataFrame:
    """Return a small benchmark frame with string dates."""
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "Value": [100.0, 100.5, 101.0, 101.5],
        },
    )


@pytest.fixture()
def fixture_captured_outputs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace Shiny decorators with identity wrappers and capture outputs."""
    monkeypatch.setattr(comparison_server.reactive, "calc", lambda function: function)
    monkeypatch.setattr(comparison_server.render, "text", lambda function: function)
    monkeypatch.setattr(comparison_server.render, "ui", lambda function: function)
    monkeypatch.setattr(comparison_server, "render_widget", lambda function: function)

    dict_output_captured: dict[str, Any] = {}

    def output_decorator(function: Any) -> Any:
        dict_output_captured[function.__name__] = function
        return function

    dict_output_captured["output_decorator"] = output_decorator
    return dict_output_captured


def _register_validated_outputs(
    *,
    input_comparison: Any,
    fixture_captured_outputs: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        comparison_server,
        "validate_portfolio_data",
        lambda data_portfolio: (True, ""),
    )
    comparison_server.register_portfolios_comparison_server_outputs(
        input=input_comparison,
        output=fixture_captured_outputs["output_decorator"],
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )


class Class_Test_Subtab_Portfolios_Comparison_Server_Helpers:
    """Tests for the extracted private portfolio comparison helpers."""

    @pytest.mark.unit()
    def Test_Datetime_Now_UTC_Naive_Returns_Naive_Datetime(self) -> None:
        """The helper should always return a timezone-naive current UTC timestamp."""
        value_now = comparison_server._datetime_now_UTC_naive()

        assert isinstance(value_now, datetime)
        assert value_now.tzinfo is None

    @pytest.mark.unit()
    def Test_Create_Empty_Comparison_Frame_Uses_Expected_Schema(self) -> None:
        """The empty-frame helper should preserve the canonical comparison schema."""
        data_frame_empty = comparison_server._create_empty_comparison_frame()

        assert data_frame_empty.columns == ["Date", "Value"]
        assert data_frame_empty.schema["Date"] == pl.Datetime
        assert data_frame_empty.schema["Value"] == pl.Float64

    @pytest.mark.unit()
    def Test_Normalize_Datetime_Bound_Handles_Pandas_Timestamp(self) -> None:
        """Timezone-aware pandas timestamps should normalize to naive bounds."""
        value_timestamp = pd.Timestamp("2024-01-04T15:30:00Z")

        value_start = comparison_server._normalize_datetime_bound(
            value_datetime = value_timestamp,
            is_end=False,
        )
        value_end = comparison_server._normalize_datetime_bound(
            value_datetime = value_timestamp,
            is_end=True,
        )

        assert value_start == _naive_datetime(2024, 1, 4, 0, 0, 0)
        assert value_end == _naive_datetime(2024, 1, 4, 23, 59, 59, 999999)

    @pytest.mark.unit()
    def Test_Normalize_Datetime_Bound_Covers_To_Pydatetime_Date_Like_And_Fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Alternate date-like inputs should normalize through their dedicated fallback paths."""
        monkeypatch.setattr(
            comparison_server,
            "_datetime_now_UTC_naive",
            lambda: _naive_datetime(2026, 5, 29, 12, 0, 0),
        )

        value_from_method = comparison_server._normalize_datetime_bound(
            value_datetime = _Value_With_To_Pydatetime(pd.Timestamp("2024-01-03T08:15:00Z").to_pydatetime()),
            is_end=False,
        )
        value_from_date_like = comparison_server._normalize_datetime_bound(
            value_datetime = SimpleNamespace(year=2024, month=1, day=5),
            is_end=True,
        )
        value_from_unknown = comparison_server._normalize_datetime_bound(
            value_datetime = object(),
            is_end=False,
        )

        assert value_from_method == _naive_datetime(2024, 1, 3, 0, 0, 0)
        assert value_from_date_like == _naive_datetime(2024, 1, 5, 23, 59, 59, 999999)
        assert value_from_unknown == _naive_datetime(2026, 5, 29, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Coerce_Date_Frame_Converts_String_Dates(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """String dates should convert to Polars datetimes."""
        data_frame_converted = comparison_server._coerce_date_frame_to_datetime(
            data_frame = fixture_comparison_frame_portfolio,
            label_dataset = "Portfolio",
        )

        assert data_frame_converted.schema["Date"] == pl.Datetime
        assert data_frame_converted.height == 4

    @pytest.mark.unit()
    def Test_Coerce_Date_Frame_Returns_Empty_For_Missing_Columns(self) -> None:
        """Missing required columns should return the canonical empty comparison frame."""
        data_frame_converted = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame({"Date": ["2024-01-01"]}),
            label_dataset = "Portfolio",
        )

        assert data_frame_converted.is_empty()
        assert data_frame_converted.columns == ["Date", "Value"]

    @pytest.mark.unit()
    def Test_Coerce_Date_Frame_Covers_Date_Dtype_And_Unexpected_Fallback(self) -> None:
        """Date columns and unexpected date types should normalize through their respective branches."""
        data_frame_date = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame(
                {
                    "Date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date()],
                    "Value": [100.0, 101.0],
                },
            ),
            label_dataset = "Portfolio",
        )
        data_frame_fallback = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame({"Date": [1, 2], "Value": [100.0, 101.0]}),
            label_dataset = "Portfolio",
        )

        assert data_frame_date.schema["Date"] == pl.Datetime
        assert data_frame_fallback.height == 2
        assert data_frame_fallback.schema["Date"] == pl.Datetime

    @pytest.mark.unit()
    def Test_Coerce_Date_Frame_String_Path_Allows_Naive_Pandas_Dates(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """String-date normalization should also work when pandas returns naive datetimes."""
        monkeypatch.setattr(
            comparison_server.pd,
            "to_datetime",
            lambda *_args, **_kwargs: pd.Series(
                [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
            ),
        )

        data_frame_converted = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"], "Value": [100.0, 101.0]}),
            label_dataset = "Portfolio",
        )

        assert data_frame_converted.height == 2
        assert data_frame_converted.schema["Date"] == pl.Datetime

    @pytest.mark.unit()
    def Test_Coerce_Date_Frame_Covers_Timezone_Aware_Datetime_And_Naive_Unexpected_Fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Timezone-aware datetime columns and naive fallback results should both normalize correctly."""
        data_frame_tz = pl.from_pandas(
            pd.DataFrame(
                {
                    "Date": [
                        pd.Timestamp("2024-01-01T00:00:00Z"),
                        pd.Timestamp("2024-01-02T00:00:00Z"),
                    ],
                    "Value": [100.0, 101.0],
                },
            ),
        )

        data_frame_tz_converted = comparison_server._coerce_date_frame_to_datetime(
            data_frame = data_frame_tz,
            label_dataset = "Portfolio",
        )
        data_frame_naive_datetime = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame(
                {
                    "Date": [_naive_datetime(2024, 1, 1), _naive_datetime(2024, 1, 2)],
                    "Value": [100.0, 101.0],
                },
            ),
            label_dataset = "Portfolio",
        )

        monkeypatch.setattr(
            comparison_server.pd,
            "to_datetime",
            lambda *_args, **_kwargs: pd.Series(
                [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
            ),
        )
        data_frame_fallback_converted = comparison_server._coerce_date_frame_to_datetime(
            data_frame = pl.DataFrame({"Date": [1, 2], "Value": [100.0, 101.0]}),
            label_dataset = "Portfolio",
        )

        assert data_frame_tz_converted.schema["Date"] == pl.Datetime
        assert getattr(data_frame_tz_converted["Date"].dtype, "time_zone", None) is None
        assert data_frame_naive_datetime.schema["Date"] == pl.Datetime
        assert data_frame_fallback_converted.schema["Date"] == pl.Datetime

    @pytest.mark.unit()
    def Test_Resolve_Available_Date_Bounds_Covers_None_And_Empty_Frame_Fallbacks(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing and empty inputs should resolve to the deterministic fallback window."""
        value_now = _naive_datetime(2026, 5, 29, 12, 0, 0)
        monkeypatch.setattr(comparison_server, "_datetime_now_UTC_naive", lambda: value_now)

        value_none = comparison_server._resolve_available_date_bounds(data_frame_portfolio = None)
        value_empty = comparison_server._resolve_available_date_bounds(
            data_frame_portfolio = comparison_server._create_empty_comparison_frame(),
        )

        assert value_none == (value_now - timedelta(days=365 * 10), value_now)
        assert value_empty == (value_now - timedelta(days=365 * 10), value_now)

    @pytest.mark.unit()
    def Test_Resolve_Available_Date_Bounds_Falls_Back_When_Normalization_Fails(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Normalization errors should log and return the deterministic fallback window."""
        value_now = _naive_datetime(2026, 5, 29, 12, 0, 0)
        monkeypatch.setattr(comparison_server, "_datetime_now_UTC_naive", lambda: value_now)
        monkeypatch.setattr(
            comparison_server,
            "_coerce_date_frame_to_datetime",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad normalization")),
        )

        value_bounds = comparison_server._resolve_available_date_bounds(
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert value_bounds == (value_now - timedelta(days=365 * 10), value_now)

    @pytest.mark.unit()
    def Test_Calc_Effective_Date_Range_Caps_Custom_End_Date(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """Custom end dates should cap at the latest available portfolio date."""
        input_comparison = _Input_Portfolios_Comparison(
            value_time_period="custom",
            value_date_range=("2024-01-02", "2026-01-01"),
        )

        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = input_comparison,
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2024, 1, 2, 0, 0, 0)
        assert datetime_end == _naive_datetime(2024, 1, 4, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Calc_Effective_Date_Range_Uses_Custom_End_Date_Within_Data_Window(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """Custom end dates inside the data window should pass through unchanged."""
        input_comparison = _Input_Portfolios_Comparison(
            value_time_period="custom",
            value_date_range=("2024-01-02", "2024-01-03"),
        )

        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = input_comparison,
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2024, 1, 2, 0, 0, 0)
        assert datetime_end == _naive_datetime(2024, 1, 3, 23, 59, 59, 999999)

    @pytest.mark.unit()
    def Test_Calc_Effective_Date_Range_Custom_Error_Falls_Back_To_One_Year(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Custom-range parsing errors should fall back to the default one-year window."""
        input_comparison = _Input_Portfolios_Comparison(value_time_period="custom")
        monkeypatch.setattr(
            input_comparison,
            "input_ID_tab_portfolios_subtab_comparison_date_range",
            lambda: (_ for _ in ()).throw(ValueError("bad custom range")),
        )

        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = input_comparison,
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2023, 1, 4, 0, 0, 0)
        assert datetime_end == _naive_datetime(2024, 1, 4, 23, 59, 59, 999999)

    @pytest.mark.unit()
    def Test_Calc_Effective_Date_Range_Custom_Incomplete_Falls_Back_To_One_Year(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """Missing custom range endpoints should use the same default one-year fallback."""
        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = _Input_Portfolios_Comparison(value_time_period="custom"),
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2023, 1, 4, 0, 0, 0)
        assert datetime_end == _naive_datetime(2024, 1, 4, 23, 59, 59, 999999)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("value_time_period", "value_expected_days"),
        [
            ("3y", 365 * 3),
            ("5y", 365 * 5),
            ("10y", 365 * 10),
            ("unexpected", 365),
        ],
    )
    def Test_Calc_Effective_Date_Range_Covers_Remaining_Presets(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        value_time_period: str,
        value_expected_days: int,
    ) -> None:
        """Remaining preset branches should resolve deterministic start bounds."""
        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = _Input_Portfolios_Comparison(value_time_period=value_time_period),
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2024, 1, 4, 0, 0, 0) - timedelta(days=value_expected_days)
        assert datetime_end == _naive_datetime(2024, 1, 4, 23, 59, 59, 999999)

    @pytest.mark.unit()
    def Test_Calc_Effective_Date_Range_Covers_YTD_Preset(self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """The YTD preset should reset the start date to the anchored calendar-year start."""
        datetime_start, datetime_end = comparison_server._calc_effective_date_range_for_comparison(
            input = _Input_Portfolios_Comparison(value_time_period="ytd"),
            data_frame_portfolio = fixture_comparison_frame_portfolio,
        )

        assert datetime_start == _naive_datetime(2024, 1, 1, 0, 0, 0)
        assert datetime_end == _naive_datetime(2024, 1, 4, 23, 59, 59, 999999)

    @pytest.mark.unit()
    def Test_Filter_Comparison_Frame_Removes_Out_Of_Range_Rows(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """Filtering should keep only rows inside the requested bounds."""
        data_frame_filtered = comparison_server._filter_comparison_frame(
            data_frame_source = fixture_comparison_frame_portfolio,
            datetime_start=_naive_datetime(2024, 1, 2, 0, 0, 0),
            datetime_end=_naive_datetime(2024, 1, 3, 23, 59, 59),
            label_dataset="Portfolio",
        )

        assert data_frame_filtered.height == 2
        assert data_frame_filtered["Value"].to_list() == [101.0, 102.0]

    @pytest.mark.unit()
    def Test_Filter_Comparison_Frame_Covers_None_Empty_And_No_Match_Paths(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
    ) -> None:
        """Filtering should also handle missing inputs, empty normalized data, and empty results."""
        data_frame_none = comparison_server._filter_comparison_frame(
            data_frame_source = None,
            datetime_start=_naive_datetime(2024, 1, 1, 0, 0, 0),
            datetime_end=_naive_datetime(2024, 1, 2, 23, 59, 59),
            label_dataset="Portfolio",
        )
        data_frame_missing_value = comparison_server._filter_comparison_frame(
            data_frame_source = pl.DataFrame({"Date": ["2024-01-01"]}),
            datetime_start=_naive_datetime(2024, 1, 1, 0, 0, 0),
            datetime_end=_naive_datetime(2024, 1, 2, 23, 59, 59),
            label_dataset="Portfolio",
        )
        data_frame_no_match = comparison_server._filter_comparison_frame(
            data_frame_source = fixture_comparison_frame_portfolio,
            datetime_start=_naive_datetime(2025, 1, 1, 0, 0, 0),
            datetime_end=_naive_datetime(2025, 1, 2, 23, 59, 59),
            label_dataset="Portfolio",
        )

        assert data_frame_none.is_empty()
        assert data_frame_missing_value.is_empty()
        assert data_frame_no_match.is_empty()

    @pytest.mark.unit()
    def Test_Resolve_Period_Label_For_Custom_Period(self) -> None:
        """Custom period labels should only show the explicit date range."""
        label_period = comparison_server._resolve_period_label_for_comparison(
            actual_start=pd.Timestamp("2024-01-02"),
            actual_end=pd.Timestamp("2024-01-04"),
            value_time_period="custom",
        )

        assert label_period == "2024-01-02 to 2024-01-04"

    @pytest.mark.unit()
    def Test_Resolve_Period_Label_For_Preset_Period(self) -> None:
        """Preset period labels should include both the label and explicit date span."""
        label_period = comparison_server._resolve_period_label_for_comparison(
            actual_start=pd.Timestamp("2024-01-02"),
            actual_end=pd.Timestamp("2024-01-04"),
            value_time_period="1y",
        )

        assert label_period == "Last 1 Year (2024-01-02 to 2024-01-04)"

    @pytest.mark.unit()
    def Test_Register_Server_Outputs_Captures_Public_Output_Functions(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Registering the helper should capture the expected output callables."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (True, ""),
        )

        comparison_server.register_portfolios_comparison_server_outputs(
            input=_Input_Portfolios_Comparison(),
            output=fixture_captured_outputs["output_decorator"],
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
        )

        assert "output_ID_tab_portfolios_subtab_comparison_calculated_date_range" in fixture_captured_outputs
        assert "output_ID_tab_portfolios_subtab_comparison_data_info" in fixture_captured_outputs
        assert "output_ID_tab_portfolios_subtab_comparison_loading_status" in fixture_captured_outputs
        assert "output_ID_tab_portfolios_subtab_comparison_plot_main" in fixture_captured_outputs
        assert "output_ID_tab_portfolios_subtab_comparison_table_stats" in fixture_captured_outputs

    @pytest.mark.unit()
    def Test_Captured_Date_Range_Output_Returns_Text(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The captured date-range output should render the computed period string."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (True, ""),
        )

        comparison_server.register_portfolios_comparison_server_outputs(
            input=_Input_Portfolios_Comparison(),
            output=fixture_captured_outputs["output_decorator"],
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
        )

        value_text = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_calculated_date_range"
        ]()

        assert value_text == "📅 2023-01-04 to 2024-01-04"

    @pytest.mark.unit()
    def Test_Captured_Date_Range_Output_Returns_Empty_For_Custom_Period(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The calculated date-range output should be blank when custom mode is active."""
        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(
                value_time_period="custom",
                value_date_range=("2024-01-02", "2024-01-03"),
            ),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
            monkeypatch=monkeypatch,
        )

        value_text = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_calculated_date_range"
        ]()

        assert value_text == ""

    @pytest.mark.unit()
    def Test_Captured_Data_Info_Output_Returns_Ready_Status(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The captured data-info output should report ready status with both datasets."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (True, ""),
        )

        comparison_server.register_portfolios_comparison_server_outputs(
            input=_Input_Portfolios_Comparison(),
            output=fixture_captured_outputs["output_decorator"],
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
        )

        tag_data_info = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_data_info"
        ]()

        assert "Ready for comparison" in str(tag_data_info)

    @pytest.mark.unit()
    def Test_Captured_Loading_Status_Output_Returns_Ready_Status(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The loading-status output should render the ready branch when both datasets are present."""
        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
            monkeypatch=monkeypatch,
        )

        tag_loading = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_loading_status"
        ]()

        assert "Data ready: 4 portfolio points, 4 benchmark points" in str(tag_loading)

    @pytest.mark.unit()
    def Test_Captured_Data_Info_And_Loading_Status_Handle_Partial_Data(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Partial-data branches should render warning-oriented status outputs."""
        monkeypatch.setattr(
            comparison_server,
            "_filter_comparison_frame",
            lambda data_frame_source, **kwargs: (
                fixture_comparison_frame_portfolio
                if kwargs["label_dataset"] == "Portfolio"
                else comparison_server._create_empty_comparison_frame()
            ),
        )

        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_portfolio,
            },
            reactives_shiny={},
            monkeypatch=monkeypatch,
        )

        tag_data_info = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_data_info"
        ]()
        tag_loading = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_loading_status"
        ]()

        assert "Partial data available" in str(tag_data_info)
        assert "Partial data: Portfolio (4 points), Benchmark (0 points)" in str(tag_loading)

    @pytest.mark.unit()
    def Test_Captured_No_Data_Status_Plot_And_Table_Outputs_Handle_Empty_Data(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """No-data branches should surface fallback status, chart, and stats-table content."""
        monkeypatch.setattr(
            comparison_server,
            "_filter_comparison_frame",
            lambda *_args, **_kwargs: comparison_server._create_empty_comparison_frame(),
        )
        monkeypatch.setattr(
            comparison_server,
            "create_error_figure",
            lambda *, title_text, message_text, **___: {
                "title": title_text,
                "message": message_text,
            },
        )

        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
            monkeypatch=monkeypatch,
        )

        tag_data_info = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_data_info"
        ]()
        tag_loading = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_loading_status"
        ]()
        value_plot = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_plot_main"
        ]()
        tag_table_stats = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_table_stats"
        ]()

        assert "No data available" in str(tag_data_info)
        assert "No data available for selected period" in str(tag_loading)
        assert value_plot == {
            "title": "Please select a time period with available portfolio and benchmark data.",
            "message": "No Data Available",
        }
        assert "No data available for statistics calculation." in str(tag_table_stats)

    @pytest.mark.unit()
    def Test_Captured_Plot_Output_Returns_Figure_And_Stores_Plotnine(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The captured plot output should call the visual helpers and return the figure."""
        dict_update_calls: dict[str, Any] = {}
        value_figure_expected = SimpleNamespace(data=["trace"])

        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (True, ""),
        )
        monkeypatch.setattr(
            comparison_server,
            "create_plot_comparison_portfolios",
            lambda **kwargs: value_figure_expected,
        )
        monkeypatch.setattr(
            comparison_server,
            "build_plotnine_portfolio_comparison_portfolio_vs_benchmark",
            lambda *_args, **_kwargs: "plotnine-figure",
        )
        monkeypatch.setattr(
            comparison_server,
            "update_visual_object_in_reactives",
            lambda *, reactives_shiny, chart_key, figure, **___: dict_update_calls.update(
                {
                    "reactives": reactives_shiny,
                    "key_name": chart_key,
                    "value_object": figure,
                },
            ),
        )

        comparison_server.register_portfolios_comparison_server_outputs(
            input=_Input_Portfolios_Comparison(),
            output=fixture_captured_outputs["output_decorator"],
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={"Visual_Objects_Shiny": {}},
        )

        value_figure_result = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_plot_main"
        ]()

        assert value_figure_result is value_figure_expected
        assert dict_update_calls["key_name"] == "Chart_Portfolio_Comparison_Portfolio_vs_Benchmark"
        assert dict_update_calls["value_object"] == "plotnine-figure"

    @pytest.mark.unit()
    def Test_Captured_Plot_Output_Uses_Benchmark_Dates_When_Portfolio_Is_Empty(
        self,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The plot output should fall back to benchmark dates when portfolio data is empty."""
        dict_plot_args: dict[str, Any] = {}
        monkeypatch.setattr(
            comparison_server,
            "_filter_comparison_frame",
            lambda data_frame_source, **kwargs: (
                comparison_server._create_empty_comparison_frame()
                if kwargs["label_dataset"] == "Portfolio"
                else comparison_server._coerce_date_frame_to_datetime(
                    data_frame = fixture_comparison_frame_benchmark,
                    label_dataset = "Benchmark",
                )
            ),
        )
        monkeypatch.setattr(
            comparison_server,
            "create_plot_comparison_portfolios",
            lambda **kwargs: dict_plot_args.update(kwargs) or SimpleNamespace(data=["trace"]),
        )
        monkeypatch.setattr(
            comparison_server,
            "build_plotnine_portfolio_comparison_portfolio_vs_benchmark",
            lambda *_args, **_kwargs: "plotnine-figure",
        )
        monkeypatch.setattr(
            comparison_server,
            "update_visual_object_in_reactives",
            lambda *_args, **_kwargs: None,
        )

        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": comparison_server._create_empty_comparison_frame(),
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={"Visual_Objects_Shiny": {}},
            monkeypatch=monkeypatch,
        )

        value_figure_result = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_plot_main"
        ]()

        assert value_figure_result.data == ["trace"]
        assert dict_plot_args["start_date"] == pd.Timestamp("2024-01-01")
        assert dict_plot_args["end_date"] == pd.Timestamp("2024-01-04")

    @pytest.mark.unit()
    def Test_Captured_Plot_Output_Falls_Back_To_Effective_Date_Range_When_Empty_State_Changes(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Stateful emptiness changes should drive the final fallback date-range branch."""
        dict_plot_args: dict[str, Any] = {}
        frame_portfolio_fake = _Empty_State_Frame_Fake([False, True])
        frame_benchmark_fake = _Empty_State_Frame_Fake([True])
        monkeypatch.setattr(
            comparison_server,
            "_filter_comparison_frame",
            lambda data_frame_source, **kwargs: (
                frame_portfolio_fake
                if kwargs["label_dataset"] == "Portfolio"
                else frame_benchmark_fake
            ),
        )
        monkeypatch.setattr(
            comparison_server,
            "create_plot_comparison_portfolios",
            lambda **kwargs: dict_plot_args.update(kwargs) or SimpleNamespace(data=["trace"]),
        )
        monkeypatch.setattr(
            comparison_server,
            "build_plotnine_portfolio_comparison_portfolio_vs_benchmark",
            lambda *_args, **_kwargs: "plotnine-figure",
        )
        monkeypatch.setattr(
            comparison_server,
            "update_visual_object_in_reactives",
            lambda *_args, **_kwargs: None,
        )

        _register_validated_outputs(
            input_comparison=_Input_Portfolios_Comparison(),
            fixture_captured_outputs=fixture_captured_outputs,
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={"Visual_Objects_Shiny": {}},
            monkeypatch=monkeypatch,
        )

        value_figure_result = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_plot_main"
        ]()

        assert value_figure_result.data == ["trace"]
        assert dict_plot_args["start_date"] == pd.Timestamp(_naive_datetime(2023, 1, 4, 0, 0, 0))
        assert dict_plot_args["end_date"] == pd.Timestamp(_naive_datetime(2024, 1, 4, 23, 59, 59, 999999))

    @pytest.mark.unit()
    def Test_Captured_Table_Stats_Output_Returns_HTML_Table(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The captured stats-table output should render the metrics HTML."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (True, ""),
        )

        comparison_server.register_portfolios_comparison_server_outputs(
            input=_Input_Portfolios_Comparison(),
            output=fixture_captured_outputs["output_decorator"],
            data_inputs={
                "My_Portfolio": fixture_comparison_frame_portfolio,
                "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
            },
            reactives_shiny={},
        )

        tag_table_stats = fixture_captured_outputs[
            "output_ID_tab_portfolios_subtab_comparison_table_stats"
        ]()

        assert "stats-table-container" in str(tag_table_stats)
        assert "Total Return (%)" in str(tag_table_stats)

    @pytest.mark.unit()
    def Test_Register_Server_Outputs_Raises_On_Invalid_Portfolio_Data(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Invalid validation results should raise the project input exception."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (False, "invalid"),
        )

        with pytest.raises(Exception_Validation_Input, match="Portfolio data validation failed"):
            comparison_server.register_portfolios_comparison_server_outputs(
                input=_Input_Portfolios_Comparison(),
                output=fixture_captured_outputs["output_decorator"],
                data_inputs={
                    "My_Portfolio": fixture_comparison_frame_portfolio,
                    "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
                },
                reactives_shiny={},
            )

    @pytest.mark.unit()
    def Test_Register_Server_Outputs_Raises_On_Invalid_Benchmark_Data(
        self,
        fixture_comparison_frame_portfolio: pl.DataFrame,
        fixture_comparison_frame_benchmark: pl.DataFrame,
        fixture_captured_outputs: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Invalid benchmark validation results should raise the project input exception."""
        monkeypatch.setattr(
            comparison_server,
            "validate_portfolio_data",
            lambda data_portfolio: (
                (True, "")
                if data_portfolio is fixture_comparison_frame_portfolio
                else (False, "invalid benchmark")
            ),
        )

        with pytest.raises(Exception_Validation_Input, match="Benchmark data validation failed"):
            comparison_server.register_portfolios_comparison_server_outputs(
                input=_Input_Portfolios_Comparison(),
                output=fixture_captured_outputs["output_decorator"],
                data_inputs={
                    "My_Portfolio": fixture_comparison_frame_portfolio,
                    "Benchmark_Portfolio": fixture_comparison_frame_benchmark,
                },
                reactives_shiny={},
            )
