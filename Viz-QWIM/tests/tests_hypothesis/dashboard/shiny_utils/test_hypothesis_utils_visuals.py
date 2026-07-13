"""Hypothesis (property-based) tests for utils_visuals module.

Tests property invariants for the pure, non-Shiny functions:
- validate_data_visuals
- format_value_for_display
- safe_numeric_conversion
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.dashboard.shiny_utils.utils_visuals import (
        format_value_for_display,
        safe_numeric_conversion,
        validate_data_visuals,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Guard: skip whole module if heavy visual deps not installed
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not MODULE_IMPORT_AVAILABLE,
    reason="utils_visuals deps (plotly, great_tables, …) not importable",
)


# ---------------------------------------------------------------------------
# Helper strategies
# ---------------------------------------------------------------------------

_st_valid_float = st.floats(
    min_value=-1e10,
    max_value=1e10,
    allow_nan=False,
    allow_infinity=False,
)

_st_format_type = st.sampled_from(["decimal", "percentage", "integer"])

_st_col_name = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=("_",)),
    min_size=2,
    max_size=15,
).filter(lambda val: val.strip() and val != "Date")


def _build_valid_df(num_rows: int = 5, extra_cols: int = 2) -> pl.DataFrame:
    """Build a minimal valid Polars DataFrame for visual validation tests."""
    data: dict[str, list] = {
        "Date": [f"2020-01-{idx+1:02d}" for idx in range(num_rows)],
    }
    for idx_col in range(extra_cols):
        data[f"series_{idx_col}"] = [float(idx_row + idx_col) for idx_row in range(num_rows)]
    return pl.DataFrame(data)


# ===========================================================================
# Class_Test_Hypothesis_Validate_Data_Visuals
# ===========================================================================


class Class_Test_Hypothesis_Validate_Data_Visuals:
    """Property tests for validate_data_visuals."""

    @pytest.mark.unit()
    def Test_none_dataframe_returns_false(self) -> None:
        """None DataFrame must return (False, non-empty message)."""
        is_valid, msg = validate_data_visuals(data_frame=None)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_empty_dataframe_returns_false(self) -> None:
        """Empty DataFrame must return (False, non-empty message)."""
        is_valid, msg = validate_data_visuals(data_frame=pl.DataFrame())
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=50),
        extra_cols=st.integers(min_value=1, max_value=4),
    )
    @settings(max_examples=200)
    def Test_valid_dataframe_without_series_returns_true(
        self,
        num_rows: int,
        extra_cols: int,
    ) -> None:
        """Valid DataFrame with 'Date' col and no series_list must return (True, '')."""
        df = _build_valid_df(num_rows=num_rows, extra_cols=extra_cols)
        is_valid, msg = validate_data_visuals(data_frame=df)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def Test_dataframe_missing_date_column_returns_false(
        self,
        num_rows: int,
    ) -> None:
        """DataFrame without 'Date' column must return (False, message)."""
        df = pl.DataFrame(
            {"series_a": [float(idx) for idx in range(num_rows)]}
        )
        is_valid, msg = validate_data_visuals(data_frame=df)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=50),
        extra_cols=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=200)
    def Test_valid_df_with_valid_series_list_returns_true(
        self,
        num_rows: int,
        extra_cols: int,
    ) -> None:
        """Valid DataFrame with existing series_list returns (True, '')."""
        df = _build_valid_df(num_rows=num_rows, extra_cols=extra_cols)
        series_names = [col_name for col_name in df.columns if col_name != "Date"]
        is_valid, msg = validate_data_visuals(
            data_frame=df,
            selected_series_list=series_names[:1],
        )
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def Test_empty_series_list_returns_false(self) -> None:
        """Empty series_list must return (False, message)."""
        df = _build_valid_df()
        is_valid, msg = validate_data_visuals(
            data_frame=df,
            selected_series_list=[],
        )
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        col_name=_st_col_name,
    )
    @settings(max_examples=200)
    def Test_nonexistent_series_returns_false(
        self,
        col_name: str,
    ) -> None:
        """series_list with no matching df columns must return (False, message)."""
        df = _build_valid_df(num_rows=5, extra_cols=2)
        # Ensure the column isn't already in the DataFrame
        if col_name in df.columns:
            return
        is_valid, msg = validate_data_visuals(
            data_frame=df,
            selected_series_list=[col_name],
        )
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    @given(
        non_df=st.one_of(
            st.integers(),
            st.text(min_size=0, max_size=10),
        )
    )
    @settings(max_examples=200)
    def Test_non_dataframe_type_returns_false(
        self,
        non_df: Any,
    ) -> None:
        """Non-DataFrame types must return (False, message)."""
        is_valid, msg = validate_data_visuals(data_frame=non_df)  # type: ignore[arg-type]
        assert is_valid is False
        assert len(msg) > 0


# ===========================================================================
# Class_Test_Hypothesis_Format_Value_For_Display
# ===========================================================================


class Class_Test_Hypothesis_Format_Value_For_Display:
    """Property tests for format_value_for_display."""

    @pytest.mark.unit()
    def Test_none_returns_none_string(self) -> None:
        """None must return the string 'None'."""
        result = format_value_for_display(value_input=None)
        assert result == "None"

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_float_returns_string(
        self,
        val: float,
    ) -> None:
        """Any finite float must return a string."""
        result = format_value_for_display(value_input=val)
        assert isinstance(result, str)

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_decimal_format_has_four_decimal_places(
        self,
        val: float,
    ) -> None:
        """'decimal' format must produce a string with exactly 4 decimal places."""
        result = format_value_for_display(value_input=val, format_type="decimal")
        # Should match pattern like "-1.2345" or "0.0000"
        if "." in result:
            decimal_part = result.split(".")[-1]
            assert len(decimal_part) == 4

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_percentage_format_ends_with_percent_sign(
        self,
        val: float,
    ) -> None:
        """'percentage' format must produce a string ending with '%'."""
        result = format_value_for_display(value_input=val, format_type="percentage")
        assert result.endswith("%")

    @pytest.mark.unit()
    @given(val=st.integers(min_value=0, max_value=1_000_000))
    @settings(max_examples=200)
    def Test_integer_format_contains_no_decimal(
        self,
        val: int,
    ) -> None:
        """'integer' format must not contain a decimal point."""
        result = format_value_for_display(value_input=val, format_type="integer")
        assert "." not in result

    @pytest.mark.unit()
    @given(
        text_val=st.text(min_size=1, max_size=30).filter(
            lambda val: val.lower() not in ("error", "none", "null", "nan")
        )
    )
    @settings(max_examples=200)
    def Test_string_input_returns_same_string(
        self,
        text_val: str,
    ) -> None:
        """A plain string that is not a sentinel must be returned as-is."""
        result = format_value_for_display(value_input=text_val)
        assert result == text_val

    @pytest.mark.unit()
    @given(fmt=_st_format_type)
    @settings(max_examples=200)
    def Test_all_format_types_return_string(
        self,
        fmt: str,
    ) -> None:
        """All known format_type values must produce a str for the value 1.5."""
        result = format_value_for_display(value_input=1.5, format_type=fmt)
        assert isinstance(result, str)


# ===========================================================================
# Class_Test_Hypothesis_Safe_Numeric_Conversion
# ===========================================================================


class Class_Test_Hypothesis_Safe_Numeric_Conversion:
    """Property tests for safe_numeric_conversion."""

    @pytest.mark.unit()
    def Test_none_returns_none(self) -> None:
        """None must return None."""
        result = safe_numeric_conversion(input_value=None)
        assert result is None

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_float_returns_float(
        self,
        val: float,
    ) -> None:
        """A finite float must return a float."""
        result = safe_numeric_conversion(input_value=val)
        assert isinstance(result, float)

    @pytest.mark.unit()
    @given(val=st.integers(min_value=-10_000, max_value=10_000))
    @settings(max_examples=200)
    def Test_integer_returns_float(
        self,
        val: int,
    ) -> None:
        """An integer must return a float (upcasted)."""
        result = safe_numeric_conversion(input_value=val)
        assert isinstance(result, float)

    @pytest.mark.unit()
    @given(
        val=st.from_regex(r"-?[0-9]{1,6}(\.[0-9]{1,4})?", fullmatch=True),
    )
    @settings(max_examples=200)
    def Test_numeric_string_returns_float(
        self,
        val: str,
    ) -> None:
        """Numeric string must be converted to float."""
        result = safe_numeric_conversion(input_value=val)
        assert isinstance(result, float)
        assert abs(result - float(val)) < 1e-9

    @pytest.mark.unit()
    @given(
        non_numeric=st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
            min_size=2,
            max_size=15,
        ).filter(lambda val: val.lower() not in ("none", "null", "nan", "error", "", "inf", "infinity"))
    )
    @settings(max_examples=200)
    def Test_non_numeric_string_returns_original(
        self,
        non_numeric: str,
    ) -> None:
        """A non-numeric alphabetic string must be returned unchanged."""
        # Skip strings that Python's float() accepts (e.g. 'inf', 'nan')
        try:
            float(non_numeric)
            return
        except ValueError:
            pass
        result = safe_numeric_conversion(input_value=non_numeric)
        assert result == non_numeric

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_roundtrip_float_is_idempotent(
        self,
        val: float,
    ) -> None:
        """safe_numeric_conversion(safe_numeric_conversion(x)) == safe_numeric_conversion(x)."""
        first_pass = safe_numeric_conversion(input_value=val)
        if isinstance(first_pass, float):
            second_pass = safe_numeric_conversion(input_value=first_pass)
            assert first_pass == second_pass
