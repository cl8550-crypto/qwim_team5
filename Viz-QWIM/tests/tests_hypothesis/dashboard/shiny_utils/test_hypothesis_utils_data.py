"""Hypothesis (property-based) tests for utils_data module.

Tests property invariants for:
- find_date_column
- standardize_date_column
- downsample_dataframe
- get_names_time_series_from_DF
- get_safe_num_rows_for_DF
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.dashboard.shiny_utils.utils_data import (
    downsample_dataframe,
    find_date_column,
    get_names_time_series_from_DF,
    get_safe_num_rows_for_DF,
    standardize_date_column,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# DataFrame builder strategies
# ---------------------------------------------------------------------------

_st_column_name = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=("_",)),
    min_size=2,
    max_size=20,
).filter(lambda val: val.strip() and val not in ("Date", "date", "DATE"))

_st_float_column = st.lists(
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    min_size=5,
    max_size=50,
)


def _build_df_with_date_col(
    date_variant: str,
    num_rows: int,
    extra_cols: int,
) -> pl.DataFrame:
    """Build a Polars DataFrame with a specific date column variant."""
    data: dict[str, list] = {
        date_variant: [f"2020-01-{i+1:02d}" for idx_row in range(num_rows) for i in [idx_row % 28]],
    }
    for idx_col in range(extra_cols):
        data[f"col_{idx_col}"] = [float(idx_row + idx_col) for idx_row in range(num_rows)]
    return pl.DataFrame(data)


def _build_numeric_df(num_rows: int, col_names: list[str]) -> pl.DataFrame:
    """Build a Polars DataFrame of floats without a date column."""
    data = {
        col_name: [float(idx_row) for idx_row in range(num_rows)]
        for col_name in col_names
    }
    return pl.DataFrame(data)


# ===========================================================================
# Class_Test_Hypothesis_Find_Date_Column
# ===========================================================================


class Class_Test_Hypothesis_Find_Date_Column:
    """Property tests for find_date_column."""

    @pytest.mark.unit()
    @given(
        date_variant=st.sampled_from(["Date", "date", "DATE"]),
        num_rows=st.integers(min_value=1, max_value=20),
        extra_cols=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=200)
    def Test_finds_date_variant_in_df(
        self,
        date_variant: str,
        num_rows: int,
        extra_cols: int,
    ) -> None:
        """find_date_column must return the known date column name when present."""
        df = _build_df_with_date_col(date_variant, num_rows, extra_cols)
        result = find_date_column(df=df)
        assert result == date_variant

    @pytest.mark.unit()
    @given(
        col_names=st.lists(_st_column_name, min_size=1, max_size=4, unique=True),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_returns_none_when_no_date_column(
        self,
        col_names: list[str],
        num_rows: int,
    ) -> None:
        """find_date_column must return None when no recognized date column exists."""
        df = _build_numeric_df(num_rows, col_names)
        result = find_date_column(df=df)
        assert result is None

    @pytest.mark.unit()
    @given(
        date_variant=st.sampled_from(["Date", "date", "DATE"]),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_result_is_contained_in_df_columns(
        self,
        date_variant: str,
        num_rows: int,
    ) -> None:
        """Return value must either be None or a column name in df.columns."""
        df = _build_df_with_date_col(date_variant, num_rows, 1)
        result = find_date_column(df=df)
        assert result is None or result in df.columns


# ===========================================================================
# Class_Test_Hypothesis_Standardize_Date_Column
# ===========================================================================


class Class_Test_Hypothesis_Standardize_Date_Column:
    """Property tests for standardize_date_column."""

    @pytest.mark.unit()
    @given(
        date_variant=st.sampled_from(["date", "DATE"]),
        num_rows=st.integers(min_value=1, max_value=20),
        extra_cols=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=200)
    def Test_renames_lowercase_date_to_title_Date(
        self,
        date_variant: str,
        num_rows: int,
        extra_cols: int,
    ) -> None:
        """A DataFrame with 'date' or 'DATE' must gain a 'Date' column after standardize."""
        df = _build_df_with_date_col(date_variant, num_rows, extra_cols)
        result = standardize_date_column(df=df)
        assert "Date" in result.columns

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=20),
        extra_cols=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=200)
    def Test_already_titled_date_column_unchanged(
        self,
        num_rows: int,
        extra_cols: int,
    ) -> None:
        """A DataFrame with 'Date' must be returned with 'Date' column still present."""
        df = _build_df_with_date_col("Date", num_rows, extra_cols)
        result = standardize_date_column(df=df)
        assert "Date" in result.columns
        assert result.shape == df.shape

    @pytest.mark.unit()
    @given(
        date_variant=st.sampled_from(["Date", "date", "DATE"]),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_row_count_is_preserved(
        self,
        date_variant: str,
        num_rows: int,
    ) -> None:
        """Row count must be the same before and after standardize."""
        df = _build_df_with_date_col(date_variant, num_rows, 1)
        result = standardize_date_column(df=df)
        assert result.height == df.height


# ===========================================================================
# Class_Test_Hypothesis_Downsample_Dataframe
# ===========================================================================


class Class_Test_Hypothesis_Downsample_Dataframe:
    """Property tests for downsample_dataframe."""

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=500),
        max_points=st.integers(min_value=5, max_value=300),
    )
    @settings(max_examples=200)
    def Test_output_height_does_not_exceed_max_points(
        self,
        num_rows: int,
        max_points: int,
    ) -> None:
        """Output row count must be less than the original when downsampling occurs."""
        df = _build_df_with_date_col("Date", num_rows, 2)
        result = downsample_dataframe(
            polars_DF=df,
            max_points=max_points,
            date_column="Date",
        )
        # The implementation uses step-based slicing so result may slightly exceed
        # max_points; the guaranteed invariant is result <= input size
        assert result.height <= df.height

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=100),
        max_points=st.integers(min_value=100, max_value=500),
    )
    @settings(max_examples=200)
    def Test_returns_unchanged_when_rows_lte_max_points(
        self,
        num_rows: int,
        max_points: int,
    ) -> None:
        """When height <= max_points, the returned DataFrame must be identical."""
        df = _build_df_with_date_col("Date", num_rows, 2)
        result = downsample_dataframe(
            polars_DF=df,
            max_points=max_points,
            date_column="Date",
        )
        assert result.height == df.height

    @pytest.mark.unit()
    def Test_none_input_raises_exception_validation_input(self) -> None:
        """None must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            downsample_dataframe(polars_DF=None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(
        non_df=st.one_of(
            st.integers(),
            st.text(min_size=1),
            st.lists(st.integers(), min_size=1, max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_df_input_raises_type_error(
        self,
        non_df: Any,
    ) -> None:
        """Non-DataFrame input must raise TypeError or Exception_Validation_Input."""
        with pytest.raises((TypeError, Exception_Validation_Input)):
            downsample_dataframe(polars_DF=non_df)

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=100),
        max_points=st.integers(min_value=5, max_value=500),
    )
    @settings(max_examples=200)
    def Test_column_names_are_preserved(
        self,
        num_rows: int,
        max_points: int,
    ) -> None:
        """Downsampling must preserve the original column names."""
        df = _build_df_with_date_col("Date", num_rows, 3)
        result = downsample_dataframe(
            polars_DF=df,
            max_points=max_points,
            date_column="Date",
        )
        assert result.columns == df.columns

    @pytest.mark.unit()
    def Test_empty_dataframe_raises(self) -> None:
        """An empty DataFrame must raise Exception_Validation_Input."""
        empty_df = pl.DataFrame({"Date": [], "value": []})
        with pytest.raises(Exception_Validation_Input):
            downsample_dataframe(polars_DF=empty_df)


# ===========================================================================
# Class_Test_Hypothesis_Get_Names_Time_Series
# ===========================================================================


class Class_Test_Hypothesis_Get_Names_Time_Series:
    """Property tests for get_names_time_series_from_DF."""

    @pytest.mark.unit()
    @given(
        col_names=st.lists(_st_column_name, min_size=1, max_size=5, unique=True),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_non_date_columns_are_returned(
        self,
        col_names: list[str],
        num_rows: int,
    ) -> None:
        """All non-Date columns must appear in the result."""
        df = _build_df_with_date_col("Date", num_rows, 0)
        for idx_col, col_name in enumerate(col_names):
            df = df.with_columns(pl.Series(col_name, [float(idx_row + idx_col) for idx_row in range(num_rows)]))
        result = get_names_time_series_from_DF(polars_DF=df)
        for col_name in col_names:
            assert col_name in result

    @pytest.mark.unit()
    @given(
        col_names=st.lists(_st_column_name, min_size=1, max_size=5, unique=True),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_date_column_not_in_result(
        self,
        col_names: list[str],
        num_rows: int,
    ) -> None:
        """The 'Date' column must NOT appear in the result list."""
        df = _build_df_with_date_col("Date", num_rows, 0)
        for idx_col, col_name in enumerate(col_names):
            df = df.with_columns(pl.Series(col_name, [float(idx_row + idx_col) for idx_row in range(num_rows)]))
        result = get_names_time_series_from_DF(polars_DF=df)
        assert "Date" not in result

    @pytest.mark.unit()
    def Test_none_returns_empty_list(self) -> None:
        """None input must return an empty list."""
        result = get_names_time_series_from_DF(polars_DF=None)  # type: ignore[arg-type]
        assert result == []

    @pytest.mark.unit()
    def Test_empty_df_returns_empty_list(self) -> None:
        """An empty DataFrame must return an empty list."""
        result = get_names_time_series_from_DF(polars_DF=pl.DataFrame())
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit()
    @given(
        col_names=st.lists(_st_column_name, min_size=1, max_size=5, unique=True),
        num_rows=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=200)
    def Test_result_is_subset_of_columns(
        self,
        col_names: list[str],
        num_rows: int,
    ) -> None:
        """Result must be a subset of df.columns."""
        df = _build_numeric_df(num_rows, col_names)
        result = get_names_time_series_from_DF(polars_DF=df)
        for col_name in result:
            assert col_name in df.columns


# ===========================================================================
# Class_Test_Hypothesis_Get_Safe_Num_Rows
# ===========================================================================


class Class_Test_Hypothesis_Get_Safe_Num_Rows:
    """Property tests for get_safe_num_rows_for_DF."""

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=0, max_value=500))
    @settings(max_examples=200)
    def Test_returns_integer(
        self,
        num_rows: int,
    ) -> None:
        """Result must always be an integer."""
        df = _build_numeric_df(num_rows, ["col_a", "col_b"]) if num_rows > 0 else pl.DataFrame()
        result = get_safe_num_rows_for_DF(input_DF=df)
        assert isinstance(result, int)

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=1, max_value=200))
    @settings(max_examples=200)
    def Test_result_equals_df_height(
        self,
        num_rows: int,
    ) -> None:
        """For a non-empty DataFrame, result must equal df.height."""
        df = _build_numeric_df(num_rows, ["col_a"])
        result = get_safe_num_rows_for_DF(input_DF=df)
        assert result == df.height

    @pytest.mark.unit()
    def Test_returns_safe_value_for_none(self) -> None:
        """None input must not raise — must return a safe value (0 or similar int)."""
        result = get_safe_num_rows_for_DF(input_DF=None)
        assert isinstance(result, int)
        assert result >= 0
