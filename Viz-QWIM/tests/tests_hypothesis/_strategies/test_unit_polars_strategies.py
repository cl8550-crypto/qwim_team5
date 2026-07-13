"""Self-tests for the shared Polars hypothesis strategies.

Each test verifies that the corresponding composite strategy yields at least
one value satisfying its structural invariants without requiring a large
number of examples (``max_examples=50``).

Tests cover:
- ``strategy_time_series_df`` — Date-first, sorted, correct column names and types.
- ``strategy_client_record_df`` — schema fields present, age constraints met.
- ``strategy_instrument_struct_df`` — Struct column with the correct field names.
- ``strategy_monetary_decimal_series`` — Decimal dtype, length in bounds.
- ``strategy_returns_series`` — Float64 dtype, values in (-1, +10).

Version: 1.0.0
"""

from __future__ import annotations

import pytest
import polars as pl

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.tests_hypothesis._strategies.polars_strategies import (
    strategy_client_record_df,
    strategy_instrument_struct_df,
    strategy_monetary_decimal_series,
    strategy_returns_series,
    strategy_time_series_df,
)


# ---------------------------------------------------------------------------
# strategy_time_series_df
# ---------------------------------------------------------------------------


class Class_Test_Strategy_Time_Series_Df:
    """Self-tests for ``strategy_time_series_df``."""

    @pytest.mark.unit()
    @given(df=strategy_time_series_df(min_rows=2, max_rows=30))
    @settings(max_examples=50)
    def Test_first_column_is_date(self, df: pl.DataFrame) -> None:
        """First column is named ``Date`` and has dtype ``pl.Date``."""
        assert df.columns[0] == "Date"
        assert df.schema["Date"] == pl.Date

    @pytest.mark.unit()
    @given(df=strategy_time_series_df(min_rows=2, max_rows=30))
    @settings(max_examples=50)
    def Test_date_column_sorted_ascending(self, df: pl.DataFrame) -> None:
        """``Date`` column is sorted ascending with no duplicates."""
        dates = df["Date"].to_list()
        assert dates == sorted(set(dates))

    @pytest.mark.unit()
    @given(
        df=strategy_time_series_df(
            min_rows=3,
            max_rows=10,
            value_columns=["Nav", "Benchmark"],
        ),
    )
    @settings(max_examples=50)
    def Test_custom_columns_present(self, df: pl.DataFrame) -> None:
        """Custom value columns are present with dtype ``Float64``."""
        assert "Nav" in df.columns
        assert "Benchmark" in df.columns
        assert df.schema["Nav"] == pl.Float64
        assert df.schema["Benchmark"] == pl.Float64

    @pytest.mark.unit()
    @given(
        df=strategy_time_series_df(min_rows=2, max_rows=20, null_density=0.3),
    )
    @settings(max_examples=30)
    def Test_row_count_in_bounds(self, df: pl.DataFrame) -> None:
        """Row count is within [min_rows, max_rows]."""
        assert 2 <= len(df) <= 20


# ---------------------------------------------------------------------------
# strategy_client_record_df
# ---------------------------------------------------------------------------


class Class_Test_Strategy_Client_Record_Df:
    """Self-tests for ``strategy_client_record_df``."""

    @pytest.mark.unit()
    @given(df=strategy_client_record_df(min_rows=1, max_rows=10))
    @settings(max_examples=50)
    def Test_expected_columns_present(self, df: pl.DataFrame) -> None:
        """DataFrame contains all expected column names."""
        expected = {
            "Client_ID",
            "Current_Age",
            "Retirement_Age",
            "Marital_Status",
            "Employment_Status",
            "Client_Type",
            "Risk_Profile",
            "Total_Assets",
        }
        assert expected.issubset(set(df.columns))

    @pytest.mark.unit()
    @given(df=strategy_client_record_df(min_rows=1, max_rows=10))
    @settings(max_examples=50)
    def Test_retirement_age_gte_current_age(self, df: pl.DataFrame) -> None:
        """``Retirement_Age`` is always ≥ ``Current_Age`` for every row."""
        result = df.filter(pl.col("Retirement_Age") < pl.col("Current_Age"))
        assert len(result) == 0, f"Found {len(result)} rows where Retirement_Age < Current_Age"

    @pytest.mark.unit()
    @given(df=strategy_client_record_df(min_rows=1, max_rows=5))
    @settings(max_examples=50)
    def Test_total_assets_non_negative(self, df: pl.DataFrame) -> None:
        """``Total_Assets`` is always ≥ 0.0."""
        result = df.filter(pl.col("Total_Assets") < 0.0)
        assert len(result) == 0

    @pytest.mark.unit()
    @given(df=strategy_client_record_df(min_rows=1, max_rows=5))
    @settings(max_examples=50)
    def Test_client_id_unique(self, df: pl.DataFrame) -> None:
        """``Client_ID`` values are unique within each generated DataFrame."""
        assert df["Client_ID"].n_unique() == len(df)


# ---------------------------------------------------------------------------
# strategy_instrument_struct_df
# ---------------------------------------------------------------------------


class Class_Test_Strategy_Instrument_Struct_Df:
    """Self-tests for ``strategy_instrument_struct_df``."""

    @pytest.mark.unit()
    @given(df=strategy_instrument_struct_df(min_rows=1, max_rows=10))
    @settings(max_examples=50)
    def Test_properties_column_is_struct(self, df: pl.DataFrame) -> None:
        """``properties`` column is a ``Struct`` type."""
        assert isinstance(df.schema["properties"], pl.Struct)

    @pytest.mark.unit()
    @given(df=strategy_instrument_struct_df(min_rows=1, max_rows=10))
    @settings(max_examples=50)
    def Test_struct_has_expected_fields(self, df: pl.DataFrame) -> None:
        """Struct fields include ``coupon``, ``strike``, ``rate``, ``maturity``."""
        struct_type = df.schema["properties"]
        assert isinstance(struct_type, pl.Struct)
        field_names = {field_item.name for field_item in struct_type.fields}
        assert {"coupon", "strike", "rate", "maturity"}.issubset(field_names)

    @pytest.mark.unit()
    @given(df=strategy_instrument_struct_df(min_rows=1, max_rows=5))
    @settings(max_examples=50)
    def Test_instrument_id_unique(self, df: pl.DataFrame) -> None:
        """``instrument_id`` values are unique."""
        assert df["instrument_id"].n_unique() == len(df)


# ---------------------------------------------------------------------------
# strategy_monetary_decimal_series
# ---------------------------------------------------------------------------


class Class_Test_Strategy_Monetary_Decimal_Series:
    """Self-tests for ``strategy_monetary_decimal_series``."""

    @pytest.mark.unit()
    @given(series=strategy_monetary_decimal_series(min_rows=1, max_rows=20))
    @settings(max_examples=50)
    def Test_dtype_is_decimal(self, series: pl.Series) -> None:
        """Series dtype is ``pl.Decimal``."""
        assert isinstance(series.dtype, pl.Decimal)

    @pytest.mark.unit()
    @given(series=strategy_monetary_decimal_series(min_rows=2, max_rows=10))
    @settings(max_examples=50)
    def Test_length_in_bounds(self, series: pl.Series) -> None:
        """Series length is within [min_rows, max_rows]."""
        assert 2 <= len(series) <= 10

    @pytest.mark.unit()
    @given(
        series=strategy_monetary_decimal_series(
            min_rows=1,
            max_rows=5,
            min_value=0.0,
            max_value=1000.0,
        ),
    )
    @settings(max_examples=50)
    def Test_all_values_non_negative(self, series: pl.Series) -> None:
        """All monetary values are non-negative when min_value=0.0."""
        float_series = series.cast(pl.Float64)
        assert float_series.min() >= 0.0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# strategy_returns_series
# ---------------------------------------------------------------------------


class Class_Test_Strategy_Returns_Series:
    """Self-tests for ``strategy_returns_series``."""

    @pytest.mark.unit()
    @given(series=strategy_returns_series(min_rows=5, max_rows=50))
    @settings(max_examples=50)
    def Test_dtype_is_float64(self, series: pl.Series) -> None:
        """Series dtype is ``Float64``."""
        assert series.dtype == pl.Float64

    @pytest.mark.unit()
    @given(series=strategy_returns_series(min_rows=5, max_rows=50))
    @settings(max_examples=50)
    def Test_no_nulls_when_null_density_zero(self, series: pl.Series) -> None:
        """No null values when ``null_density=0.0`` (default)."""
        assert series.null_count() == 0

    @pytest.mark.unit()
    @given(series=strategy_returns_series(min_rows=5, max_rows=50))
    @settings(max_examples=50)
    def Test_values_within_bounds(self, series: pl.Series) -> None:
        """All non-null values are within (-1.0, +10.0)."""
        non_null = series.drop_nulls()
        if len(non_null) > 0:
            assert non_null.min() >= -0.999  # type: ignore[operator]
            assert non_null.max() <= 10.0  # type: ignore[operator]

    @pytest.mark.unit()
    @given(series=strategy_returns_series(min_rows=5, max_rows=50))
    @settings(max_examples=50)
    def Test_length_in_bounds(self, series: pl.Series) -> None:
        """Series length is within [min_rows, max_rows]."""
        assert 5 <= len(series) <= 50
