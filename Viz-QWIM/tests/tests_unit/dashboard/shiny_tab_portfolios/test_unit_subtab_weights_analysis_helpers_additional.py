"""Additional focused unit tests for extracted weights-analysis data helpers."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd
import polars as pl
import pytest

import src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data as weights_data
from src.dashboard.shiny_tab_portfolios._subtab_weights_analysis_data import (
    build_report_weights_statistics_payload,
    build_weights_calculated_date_range_text,
    build_weights_statistics_rows,
    create_empty_weights_frame,
    filter_weights_frame_by_date,
    filter_weights_frame_by_selected_ETF_components,
    normalize_weights_source_frame,
    resolve_available_ETF_components,
    resolve_max_points_from_data_utils,
    resolve_selected_ETF_components,
    resolve_weights_anchor_datetime,
    resolve_weights_analysis_date_range,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


class Select_Result_Fake:
    """Minimal select-result stub exposing Polars dtype metadata."""

    def __init__(
        self,
        date_dtype: pl.DataType,
    ) -> None:
        self.dtypes = [date_dtype]


class Weights_Normalization_Frame_Fake:
    """Minimal frame stub for private date-normalization helper tests."""

    def __init__(
        self,
        date_dtype: pl.DataType,
        outcomes: list[Any],
    ) -> None:
        self.m_date_dtype = date_dtype
        self.m_outcomes = list(outcomes)

    def select(
        self,
        _column_name: str,
    ) -> Select_Result_Fake:
        return Select_Result_Fake(self.m_date_dtype)

    def with_columns(
        self,
        _expression: Any,
    ) -> Any:
        outcome_current = self.m_outcomes.pop(0)
        if isinstance(outcome_current, Exception):
            raise outcome_current
        return outcome_current


@pytest.fixture()
def fixture_weights_frame_large() -> pl.DataFrame:
    """Return a large source dataframe for weights-helper tests."""
    base_datetime = datetime(2024, 1, 1, tzinfo=UTC)
    date_values = [
        (base_datetime + timedelta(days=idx_day)).strftime("%Y-%m-%d")
        for idx_day in range(260)
    ]
    return pl.DataFrame(
        {
            "Date": date_values,
            "VTI": [0.40 + idx_day * 0.0001 for idx_day in range(260)],
            "VXUS": [0.30 for _ in range(260)],
            "BND": [0.20 for _ in range(260)],
            "VNQ": [0.10 - idx_day * 0.0001 for idx_day in range(260)],
        },
    )


@pytest.fixture()
def fixture_weights_frame_normalized(
    fixture_weights_frame_large: pl.DataFrame,
) -> pl.DataFrame:
    """Return the normalized weights dataframe used in helper tests."""
    return normalize_weights_source_frame(weights_source = fixture_weights_frame_large)


class Class_Test_Subtab_Weights_Analysis_Data_Helpers_Additional:
    """Additional unit tests for pure weights-analysis data helpers."""

    @pytest.mark.unit()
    def Test_Create_Empty_Weights_Frame_Builds_Component_Schema(self) -> None:
        """The empty-frame helper should preserve component columns and schema types."""
        empty_frame = create_empty_weights_frame(component_columns = ["VTI", "BND"])

        assert empty_frame.columns == ["Date", "VTI", "BND"]
        assert empty_frame.schema["Date"] == pl.Datetime
        assert empty_frame.schema["VTI"] == pl.Float64
        assert empty_frame.schema["BND"] == pl.Float64

    @pytest.mark.unit()
    def Test_Coerce_Datetime_Value_Accepts_Date_Object(self) -> None:
        """Date-like objects should normalize to a naive start-of-day datetime."""
        normalized_datetime = weights_data._coerce_datetime_value(
            date_value = date(2024, 2, 1),
            use_end_of_day=False,
        )

        assert normalized_datetime == datetime(2024, 2, 1, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Coerce_Datetime_Value_Accepts_Datetime_Instance(self) -> None:
        """Datetime inputs should normalize through the direct datetime branch."""
        normalized_datetime = weights_data._coerce_datetime_value(
            date_value = datetime(2024, 2, 1, 14, 30, 0, tzinfo=UTC),
            use_end_of_day=False,
        )

        assert normalized_datetime == datetime(2024, 2, 1, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Coerce_Datetime_Value_Raises_For_Unsupported_Text(self) -> None:
        """Unsupported date text should raise a validation error after all parse attempts."""
        with pytest.raises(Exception_Validation_Input, match="Unsupported date value"):
            weights_data._coerce_datetime_value(
                date_value = "not-a-date",
                use_end_of_day=True,
            )

    @pytest.mark.unit()
    def Test_Coerce_Datetime_Value_Raises_For_Blank_Text(self) -> None:
        """Blank date text should exercise the empty-candidate fallback path."""
        with pytest.raises(Exception_Validation_Input, match="Unsupported date value"):
            weights_data._coerce_datetime_value(
                date_value = "   ",
                use_end_of_day=False,
            )

    @pytest.mark.unit()
    def Test_Normalize_Weights_Date_Column_Covers_Date_And_Datetime_Fallbacks(self) -> None:
        """Date and datetime source dtypes should normalize through their dedicated paths."""
        date_frame = pl.DataFrame(
            {"Date": [date(2024, 1, 1)], "VTI": [0.5]},
        )
        fake_datetime_frame = Weights_Normalization_Frame_Fake(
            pl.Datetime,
            [ValueError("tz replacement failed"), "normalized-datetime-frame"],
        )

        normalized_date_frame = weights_data._normalize_weights_date_column(weights_frame = date_frame)
        normalized_datetime_frame = weights_data._normalize_weights_date_column(
            weights_frame = fake_datetime_frame,
        )

        assert str(normalized_date_frame.schema["Date"]).startswith("Datetime")
        assert normalized_datetime_frame == "normalized-datetime-frame"

    @pytest.mark.unit()
    def Test_Normalize_Weights_Date_Column_Covers_String_Fallback_And_Final_Error(self) -> None:
        """String and unknown dtypes should exercise fallback normalization branches."""
        fake_string_frame = Weights_Normalization_Frame_Fake(
            pl.String,
            [
                ValueError("datetime parse failed"),
                TypeError("date parse failed"),
                "normalized-string-frame",
            ],
        )
        fake_unknown_frame = Weights_Normalization_Frame_Fake(
            pl.Int64,
            [
                ValueError("cast datetime failed"),
                TypeError("cast date failed"),
                pl.exceptions.ComputeError("slice parse failed"),
            ],
        )

        normalized_string_frame = weights_data._normalize_weights_date_column(
            weights_frame = fake_string_frame,
        )

        assert normalized_string_frame == "normalized-string-frame"

        with pytest.raises(Exception_Validation_Input, match="Unable to normalize"):
            weights_data._normalize_weights_date_column(weights_frame = fake_unknown_frame)

    @pytest.mark.unit()
    def Test_Normalize_Weights_Date_Column_Covers_Final_Fallbacks_For_Datetime_And_String(self) -> None:
        """Datetime and string dtypes should also fall through to the generic normalization attempts."""
        fake_datetime_fallback_frame = Weights_Normalization_Frame_Fake(
            pl.Datetime,
            [
                ValueError("replace tz failed"),
                TypeError("cast failed"),
                "normalized-from-generic-datetime-fallback",
            ],
        )
        fake_string_fallback_frame = Weights_Normalization_Frame_Fake(
            pl.String,
            [
                ValueError("string datetime failed"),
                TypeError("string date failed"),
                pl.exceptions.ComputeError("string slice failed"),
                "normalized-from-generic-string-fallback",
            ],
        )

        normalized_datetime_frame = weights_data._normalize_weights_date_column(
            weights_frame = fake_datetime_fallback_frame,
        )
        normalized_string_frame = weights_data._normalize_weights_date_column(
            weights_frame = fake_string_fallback_frame,
        )

        assert normalized_datetime_frame == "normalized-from-generic-datetime-fallback"
        assert normalized_string_frame == "normalized-from-generic-string-fallback"

    @pytest.mark.unit()
    def Test_Normalize_Weights_Source_Frame_Accepts_Pandas_Boundary(self) -> None:
        """A pandas source frame should normalize through the documented boundary."""
        weights_source = pd.DataFrame(
            {"Date": ["2024-01-01", "2024-01-02"], "VTI": [0.4, 0.5]},
        )

        normalized_frame = normalize_weights_source_frame(weights_source = weights_source)

        assert normalized_frame.columns == ["Date", "VTI"]
        assert str(normalized_frame.schema["Date"]).startswith("Datetime")

    @pytest.mark.unit()
    def Test_Normalize_Weights_Source_Frame_Raises_On_Pandas_Conversion_Error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pandas conversion failures should be wrapped in a validation error."""
        monkeypatch.setattr(
            weights_data.pl,
            "from_pandas",
            lambda _frame: (_ for _ in ()).throw(ValueError("bad pandas conversion")),
        )

        with pytest.raises(Exception_Validation_Input, match="bad pandas conversion"):
            normalize_weights_source_frame(
                weights_source = pd.DataFrame({"Date": ["2024-01-01"], "VTI": [0.4]}),
            )

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("weights_source", "expected_fragment"),
        [
            (None, "Weights_My_Portfolio"),
            ({"Date": []}, "must be a Polars DataFrame"),
            (pl.DataFrame({"Date": [], "VTI": []}), "empty (0 rows)"),
            (pl.DataFrame({"VTI": [0.4]}), "must contain a 'Date' column"),
            (pl.DataFrame({"Date": [datetime(2024, 1, 1)]}), "at least one ETF component"),
        ],
    )
    def Test_Normalize_Weights_Source_Frame_Validates_Input_Boundaries(
        self,
        weights_source: Any,
        expected_fragment: str,
    ) -> None:
        """Boundary validation should reject missing, malformed, or empty inputs."""
        with pytest.raises(Exception_Validation_Input, match=re.escape(expected_fragment)):
            normalize_weights_source_frame(weights_source = weights_source)

    @pytest.mark.unit()
    def Test_Normalize_Weights_Source_Frame_Raises_When_Normalized_Dates_Are_All_Null(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Inputs with no valid normalized dates should raise a validation error."""
        monkeypatch.setattr(
            weights_data,
            "_normalize_weights_date_column",
            lambda *, weights_frame, **___: pl.DataFrame({"Date": [None], "VTI": [0.4]}),
        )

        with pytest.raises(Exception_Validation_Input, match="contains no valid dates"):
            normalize_weights_source_frame(
                weights_source = pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.4]}),
            )

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("data_utils", "expected_value"),
        [
            (None, 200),
            ({"downsampling_threshold": "bad"}, 200),
            ({"downsampling_threshold": True}, 200),
            ({"downsampling_threshold": 0}, 200),
            ({"downsampling_threshold": 150}, 150),
        ],
    )
    def Test_Resolve_Max_Points_From_Data_Utils_Covers_Fallbacks(
        self,
        data_utils: dict[str, Any] | None,
        expected_value: int,
    ) -> None:
        """Downsampling-threshold resolution should cover defaults and validation fallbacks."""
        assert resolve_max_points_from_data_utils(data_utils = data_utils) == expected_value

    @pytest.mark.unit()
    def Test_Resolve_Weights_Anchor_Datetime_Falls_Back_For_Missing_Frame(self) -> None:
        """Missing or unusable source frames should fall back to the provided current date."""
        anchor_datetime = resolve_weights_anchor_datetime(
            weights_frame = None,
            today_datetime=datetime(2026, 5, 29, 12, 0, 0, tzinfo=UTC),
        )

        assert anchor_datetime == datetime(2026, 5, 29, 23, 59, 59)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Anchor_Datetime_Returns_Today_When_Select_Fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unexpected select failures should fall back to the provided current date."""
        monkeypatch.setattr(
            weights_data.pl,
            "col",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad select")),
        )

        anchor_datetime = resolve_weights_anchor_datetime(
            weights_frame = pl.DataFrame({"Date": [datetime(2024, 1, 1)], "VTI": [0.4]}),
            today_datetime=datetime(2026, 5, 29, 12, 0, 0, tzinfo=UTC),
        )

        assert anchor_datetime == datetime(2026, 5, 29, 23, 59, 59)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Anchor_Datetime_Handles_None_And_String_Max_Values(
        self,
        fixture_weights_frame_large: pl.DataFrame,
    ) -> None:
        """Anchor resolution should support null maxima and raw string-date source frames."""
        null_anchor_datetime = resolve_weights_anchor_datetime(
            weights_frame = pl.DataFrame({"Date": [None], "VTI": [0.4]}),
            today_datetime=datetime(2026, 5, 29, 12, 0, 0, tzinfo=UTC),
        )
        string_anchor_datetime = resolve_weights_anchor_datetime(
            weights_frame = fixture_weights_frame_large,
            today_datetime=datetime(2026, 5, 29, 12, 0, 0, tzinfo=UTC),
        )

        assert null_anchor_datetime == datetime(2026, 5, 29, 23, 59, 59)
        assert string_anchor_datetime == datetime(2024, 9, 16, 23, 59, 59)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Custom_Swaps_Reversed_Endpoints(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Reversed custom endpoints should be normalized into ascending order."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "custom",
            weights_frame = fixture_weights_frame_normalized,
            custom_date_range=[date(2024, 3, 15), date(2024, 2, 1)],
        )

        assert start_datetime == datetime(2024, 2, 1, 23, 59, 59)
        assert end_datetime == datetime(2024, 3, 15, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Custom_Invalid_Falls_Back_To_Five_Years(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Invalid custom inputs should fall back to the default 5-year anchored range."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "custom",
            weights_frame = fixture_weights_frame_normalized,
            custom_date_range=["not-a-date", "still-not-a-date"],
        )

        assert end_datetime == datetime(2024, 9, 16, 23, 59, 59)
        assert start_datetime == end_datetime - timedelta(days=365 * 5)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Custom_Incomplete_Falls_Back_To_Five_Years(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Incomplete custom ranges should use the same default 5-year fallback."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "custom",
            weights_frame = fixture_weights_frame_normalized,
            custom_date_range=["2024-01-01"],
        )

        assert end_datetime == datetime(2024, 9, 16, 23, 59, 59)
        assert start_datetime == end_datetime - timedelta(days=365 * 5)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("time_period", "expected_days_delta"),
        [
            ("3y", 365 * 3),
            ("5y", 365 * 5),
            ("10y", 365 * 10),
            (None, 365 * 5),
            ("unexpected", 365 * 5),
        ],
    )
    def Test_Resolve_Weights_Analysis_Date_Range_Covers_Remaining_Presets(
        self,
        time_period: str | None,
        expected_days_delta: int,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Remaining preset and fallback branches should resolve deterministic spans."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = time_period,
            weights_frame = fixture_weights_frame_normalized,
        )

        assert end_datetime == datetime(2024, 9, 16, 23, 59, 59)
        assert start_datetime == end_datetime - timedelta(days=expected_days_delta)

    @pytest.mark.unit()
    def Test_Build_Weights_Calculated_Date_Range_Text_Uses_Public_Format(self) -> None:
        """The displayed date-range text should use the public analysis-period prefix."""
        value_text = build_weights_calculated_date_range_text(
            start_datetime = datetime(2024, 1, 1, 0, 0, 0),
            end_datetime = datetime(2024, 9, 16, 23, 59, 59),
        )

        assert value_text == "Analysis Period: 2024-01-01 to 2024-09-16"

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Anchors_To_Data_Max(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Preset periods should anchor to the latest available weights date."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "1y",
            weights_frame = fixture_weights_frame_normalized,
            today_datetime=datetime(2026, 5, 29, tzinfo=UTC),
        )

        assert end_datetime == datetime(2024, 9, 16, 23, 59, 59)
        assert start_datetime == datetime(2023, 9, 17, 23, 59, 59)

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Uses_Naive_YTD_Start(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """The YTD branch should use the anchored year start without timezone mixing."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "ytd",
            weights_frame = fixture_weights_frame_normalized,
        )

        assert start_datetime == datetime(2024, 1, 1, 0, 0, 0)
        assert start_datetime.tzinfo is None
        assert end_datetime.tzinfo is None

    @pytest.mark.unit()
    def Test_Resolve_Weights_Analysis_Date_Range_Custom_Accepts_Mixed_Values(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Custom date ranges should normalize string and date inputs."""
        start_datetime, end_datetime = resolve_weights_analysis_date_range(
            time_period = "custom",
            weights_frame = fixture_weights_frame_normalized,
            custom_date_range=[date(2024, 2, 1), "2024-03-15T09:30:00"],
        )

        assert start_datetime == datetime(2024, 2, 1, 0, 0, 0)
        assert end_datetime == datetime(2024, 3, 15, 23, 59, 59)

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Date_Returns_Empty_Frame_For_Empty_Input(self) -> None:
        """Empty normalized inputs should return the canonical empty weights frame."""
        filtered_frame = filter_weights_frame_by_date(
            weights_frame = create_empty_weights_frame(component_columns = ["VTI", "BND"]),
            start_datetime=datetime(2024, 1, 1, 0, 0, 0),
            end_datetime=datetime(2024, 1, 2, 23, 59, 59),
            max_points=200,
        )

        assert filtered_frame.columns == ["Date"]
        assert filtered_frame.is_empty()

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Date_Returns_Component_Aware_Empty_Frame_When_No_Rows_Match(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Ranges with no matching rows should keep the component schema in the empty result."""
        filtered_frame = filter_weights_frame_by_date(
            weights_frame = fixture_weights_frame_normalized,
            start_datetime=datetime(2026, 1, 1, 0, 0, 0),
            end_datetime=datetime(2026, 1, 2, 23, 59, 59),
            max_points=200,
        )

        assert filtered_frame.is_empty()
        assert filtered_frame.columns == ["Date", "VTI", "VXUS", "BND", "VNQ"]

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Date_Returns_Small_Sorted_Frame_Without_Downsampling(
        self,
    ) -> None:
        """Filtered subsets at or below the cap should return sorted rows without downsampling."""
        weights_frame = pl.DataFrame(
            {
                "Date": [
                    datetime(2024, 1, 3, 0, 0, 0),
                    datetime(2024, 1, 1, 0, 0, 0),
                    datetime(2024, 1, 2, 0, 0, 0),
                ],
                "VTI": [0.4, 0.5, 0.6],
            },
        )

        filtered_frame = filter_weights_frame_by_date(
            weights_frame = weights_frame,
            start_datetime=datetime(2024, 1, 1, 0, 0, 0),
            end_datetime=datetime(2024, 1, 3, 23, 59, 59),
            max_points=10,
        )

        assert filtered_frame.get_column("Date").to_list() == [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 3, 0, 0, 0),
        ]

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Date_Returns_Sorted_Frame_When_Downsampling_Fails(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Downsampling failures should leave the filtered frame intact and sorted."""
        monkeypatch.setattr(
            weights_data,
            "downsample_dataframe",
            lambda *args, **kwargs: (_ for _ in ()).throw(Exception_Configuration("boom")),
        )

        filtered_frame = filter_weights_frame_by_date(
            weights_frame = fixture_weights_frame_normalized,
            start_datetime=datetime(2024, 1, 1, 0, 0, 0),
            end_datetime=datetime(2024, 9, 16, 23, 59, 59),
            max_points=50,
        )

        assert filtered_frame.height == fixture_weights_frame_normalized.height
        assert filtered_frame.get_column("Date").to_list()[0] == datetime(2024, 1, 1, 0, 0, 0)

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Date_Downsamples_Large_Frames(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Large filtered weights frames should be downsampled by helper logic."""
        filtered_frame = filter_weights_frame_by_date(
            weights_frame = fixture_weights_frame_normalized,
            start_datetime=datetime(2024, 1, 1, 0, 0, 0),
            end_datetime=datetime(2024, 9, 16, 23, 59, 59),
            max_points=200,
        )

        assert filtered_frame.height <= 200
        assert filtered_frame.height > 0

    @pytest.mark.unit()
    def Test_Resolve_Available_ETF_Components_Covers_Empty_And_Populated_Frames(self) -> None:
        """Available-component resolution should handle both empty and populated inputs."""
        empty_components = resolve_available_ETF_components(weights_frame = create_empty_weights_frame())
        populated_components = resolve_available_ETF_components(
            weights_frame = pl.DataFrame(
                {"Date": [datetime(2024, 1, 1, 0, 0, 0)], "VTI": [0.4], "BND": [0.6]},
            ),
        )

        assert empty_components == []
        assert populated_components == ["VTI", "BND"]

    @pytest.mark.unit()
    def Test_Resolve_Available_ETF_Components_Excludes_Boolean_Columns(self) -> None:
        """Boolean component columns should be excluded from the available ETF list."""
        populated_components = resolve_available_ETF_components(
            weights_frame = pl.DataFrame(
                {
                    "Date": [datetime(2024, 1, 1, 0, 0, 0)],
                    "VTI": [0.4],
                    "BND": [True],
                    "GLD": [0.6],
                },
            ),
        )

        assert populated_components == ["VTI", "GLD"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_ETF_Components_Covers_None_And_Explicit_Checkbox_Selections(
        self,
    ) -> None:
        """Selection resolution should cover empty, default, and explicit checkbox paths."""
        no_components = resolve_selected_ETF_components(
            available_components = [],
            select_all_components=None,
            checkbox_values_by_component=None,
        )
        default_components = resolve_selected_ETF_components(
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            select_all_components=False,
            checkbox_values_by_component=None,
        )
        explicit_components = resolve_selected_ETF_components(
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            select_all_components=False,
            checkbox_values_by_component={"VXUS": True, "VNQ": True},
        )

        assert no_components == []
        assert default_components == ["VTI", "VXUS", "BND"]
        assert explicit_components == ["VXUS", "VNQ"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_ETF_Components_Defaults_To_First_Three(self) -> None:
        """The helper should default to the first three components when nothing is selected."""
        selected_components = resolve_selected_ETF_components(
            available_components = ["VTI", "VXUS", "BND", "VNQ"],
            select_all_components=None,
            checkbox_values_by_component={},
        )

        assert selected_components == ["VTI", "VXUS", "BND"]

    @pytest.mark.unit()
    def Test_Resolve_Selected_ETF_Components_Honors_Select_All(self) -> None:
        """The helper should return all components when select-all is active."""
        available_components = ["VTI", "VXUS", "BND", "VNQ"]
        selected_components = resolve_selected_ETF_components(
            available_components = available_components,
            select_all_components=True,
            checkbox_values_by_component={"VTI": True},
        )

        assert selected_components == available_components

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Selected_ETF_Components_Keeps_Date_And_Selection(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """The selected-components helper should keep Date plus the requested ETF columns."""
        filtered_frame = filter_weights_frame_by_selected_ETF_components(
            weights_frame = fixture_weights_frame_normalized,
            selected_components = ["VXUS", "BND"],
        )

        assert filtered_frame.columns == ["Date", "VXUS", "BND"]

    @pytest.mark.unit()
    def Test_Filter_Weights_Frame_By_Selected_ETF_Components_Returns_Empty_For_Missing_Selections(
        self,
        fixture_weights_frame_normalized: pl.DataFrame,
    ) -> None:
        """Missing or invalid component selections should return the canonical empty frame."""
        no_selection_frame = filter_weights_frame_by_selected_ETF_components(
            weights_frame = fixture_weights_frame_normalized,
            selected_components = [],
        )
        invalid_selection_frame = filter_weights_frame_by_selected_ETF_components(
            weights_frame = fixture_weights_frame_normalized,
            selected_components = ["GLD"],
        )

        assert no_selection_frame.columns == ["Date"]
        assert invalid_selection_frame.columns == ["Date"]

    @pytest.mark.unit()
    def Test_Build_Weights_Statistics_Rows_Normalizes_Single_Value_STD(self) -> None:
        """Single-row statistics should normalize NaN standard deviation to 0.0."""
        weights_frame = pl.DataFrame(
            {"Date": [datetime(2024, 1, 1)], "VTI": [0.5], "BND": [0.5]},
        )

        statistics_rows = build_weights_statistics_rows(weights_frame = weights_frame)

        assert statistics_rows[0]["Std Dev"] == 0.0

    @pytest.mark.unit()
    def Test_Build_Weights_Statistics_Rows_Normalizes_NaN_STD(self) -> None:
        """NaN standard deviation values should also normalize to 0.0."""
        weights_frame = pl.DataFrame(
            {
                "Date": [datetime(2024, 1, 1), datetime(2024, 1, 2)],
                "VTI": [float("nan"), 0.5],
            },
        )

        statistics_rows = build_weights_statistics_rows(weights_frame = weights_frame)

        assert statistics_rows[0]["Std Dev"] == 0.0

    @pytest.mark.unit()
    def Test_Build_Weights_Statistics_Rows_Returns_Empty_For_Empty_And_Date_Only_Frames(
        self,
    ) -> None:
        """Statistics rows should be empty when no component data is available."""
        empty_rows = build_weights_statistics_rows(weights_frame = create_empty_weights_frame())
        date_only_rows = build_weights_statistics_rows(
            weights_frame = pl.DataFrame({"Date": [datetime(2024, 1, 1, 0, 0, 0)]}),
        )

        assert empty_rows == []
        assert date_only_rows == []

    @pytest.mark.unit()
    def Test_Build_Weights_Statistics_Rows_Excludes_Boolean_Component_Series(self) -> None:
        """Boolean component series should be skipped instead of exported as numeric statistics."""
        weights_frame = pl.DataFrame(
            {
                "Date": [datetime(2024, 1, 1), datetime(2024, 1, 2)],
                "VTI": [0.4, 0.5],
                "BND": [True, False],
            },
        )

        statistics_rows = build_weights_statistics_rows(weights_frame = weights_frame)

        assert statistics_rows == [
            {
                "Component": "VTI",
                "Current": 0.5,
                "Average": 0.45,
                "Min": 0.4,
                "Max": 0.5,
                "Std Dev": pytest.approx(0.07071067811865474),
            },
        ]

    @pytest.mark.unit()
    def Test_Build_Report_Weights_Statistics_Payload_Converts_Public_Row_Shape(self) -> None:
        """The report payload helper should convert public statistic rows into report keys."""
        payload_rows = build_report_weights_statistics_payload(
            statistics_rows = [
                {
                    "Component": "VTI",
                    "Current": 0.4,
                    "Average": 0.35,
                    "Min": 0.3,
                    "Max": 0.4,
                    "Std Dev": 0.05,
                },
            ],
        )

        assert payload_rows == [
            {
                "component": "VTI",
                "current_weight": 0.4,
                "mean_weight": 0.35,
                "min_weight": 0.3,
                "max_weight": 0.4,
                "std_weight": 0.05,
            },
        ]

    @pytest.mark.unit()
    def Test_Build_Report_Weights_Statistics_Payload_Excludes_Boolean_Values(self) -> None:
        """Boolean statistic values should be skipped instead of coerced into numeric report payloads."""
        payload_rows = build_report_weights_statistics_payload(
            statistics_rows = [
                {
                    "Component": "VTI",
                    "Current": 0.4,
                    "Average": 0.35,
                    "Min": 0.3,
                    "Max": 0.4,
                    "Std Dev": 0.05,
                },
                {
                    "Component": "BND",
                    "Current": True,
                    "Average": 0.2,
                    "Min": 0.1,
                    "Max": 0.3,
                    "Std Dev": 0.01,
                },
            ],
        )

        assert payload_rows == [
            {
                "component": "VTI",
                "current_weight": 0.4,
                "mean_weight": 0.35,
                "min_weight": 0.3,
                "max_weight": 0.4,
                "std_weight": 0.05,
            },
        ]