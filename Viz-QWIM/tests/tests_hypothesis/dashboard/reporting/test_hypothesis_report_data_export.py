"""Hypothesis (property-based) tests for report_data_export module.

Tests property invariants for the internal helper functions:
- _safe_float
- _safe_str
- _polars_to_records
- _compute_weight_statistics_from_weights
- _compute_portfolio_metrics_from_values
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.dashboard.reporting.report_data_export import (
    _compute_portfolio_metrics_from_values,
    _compute_weight_statistics_from_weights,
    _polars_to_records,
    _safe_float,
    _safe_str,
)


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

_st_valid_float = st.floats(
    min_value=-1e12,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False,
)

_st_col_name = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=("_",)),
    min_size=2,
    max_size=15,
).filter(lambda val: val.strip() and val != "Date")


def _build_portfolio_value_df(num_rows: int, start_value: float = 100.0) -> pl.DataFrame:
    """Build a synthetic portfolio-value DataFrame with Date and portfolio_value columns."""
    # Use a simple monotone growth so there are no edge cases from random data
    values = [start_value * (1.0 + 0.001 * idx) for idx in range(num_rows)]
    dates = [f"2020-01-{(idx % 28) + 1:02d}" if idx < 28 else f"2020-{(idx // 28) + 1:02d}-{(idx % 28) + 1:02d}" for idx in range(num_rows)]

    # Keep dates unique and parseable with a simpler approach:
    import datetime
    start_dt = datetime.date(2020, 1, 1)
    date_list = [(start_dt + datetime.timedelta(days=idx)) for idx in range(num_rows)]

    return pl.DataFrame(
        {
            "Date": date_list,
            "portfolio_value": values,
        }
    )


# ===========================================================================
# Class_Test_Hypothesis_Safe_Float
# ===========================================================================


class Class_Test_Hypothesis_Safe_Float:
    """Property tests for _safe_float."""

    @pytest.mark.unit()
    def Test_none_returns_default(self) -> None:
        """None must return the default value (0.0)."""
        result = _safe_float(value=None)
        assert result == 0.0
        assert isinstance(result, float)

    @pytest.mark.unit()
    def Test_none_with_custom_default_returns_custom(self) -> None:
        """None must return the custom default."""
        result = _safe_float(value=None, default=-1.0)
        assert result == -1.0

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_float_returns_same_float(
        self,
        val: float,
    ) -> None:
        """A finite float must return itself."""
        result = _safe_float(value=val)
        assert isinstance(result, float)
        assert result == val

    @pytest.mark.unit()
    @given(val=st.integers(min_value=-10_000, max_value=10_000))
    @settings(max_examples=200)
    def Test_integer_returns_float_equal_to_int(
        self,
        val: int,
    ) -> None:
        """An integer must be converted to float(val)."""
        result = _safe_float(value=val)
        assert isinstance(result, float)
        assert result == float(val)

    @pytest.mark.unit()
    @given(
        num_str=st.from_regex(r"-?[0-9]{1,8}(\.[0-9]{1,4})?", fullmatch=True),
    )
    @settings(max_examples=200)
    def Test_numeric_string_returns_parsed_float(
        self,
        num_str: str,
    ) -> None:
        """A numeric string must be parsed and returned as float."""
        result = _safe_float(value=num_str)
        assert isinstance(result, float)
        assert abs(result - float(num_str)) < 1e-9

    @pytest.mark.unit()
    @given(
        bad_str=st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
            min_size=2,
            max_size=15,
        )
    )
    @settings(max_examples=200)
    def Test_non_numeric_string_returns_default(
        self,
        bad_str: str,
    ) -> None:
        """A non-numeric string must return the default."""
        # Skip strings that Python's float() accepts (e.g. 'inf', 'nan')
        try:
            float(bad_str)
            return
        except ValueError:
            pass
        result = _safe_float(value=bad_str, default=0.0)
        assert result == 0.0

    @pytest.mark.unit()
    @given(
        val=st.one_of(
            st.lists(st.integers(), min_size=1, max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=2),
        )
    )
    @settings(max_examples=200)
    def Test_unconvertible_type_returns_default(
        self,
        val: Any,
    ) -> None:
        """Container types that cannot be cast to float must return default."""
        default_val = 99.9
        result = _safe_float(value=val, default=default_val)
        assert result == default_val


# ===========================================================================
# Class_Test_Hypothesis_Safe_Str
# ===========================================================================


class Class_Test_Hypothesis_Safe_Str:
    """Property tests for _safe_str."""

    @pytest.mark.unit()
    def Test_none_returns_default_na(self) -> None:
        """None must return 'N/A'."""
        result = _safe_str(value=None)
        assert result == "N/A"

    @pytest.mark.unit()
    def Test_none_with_custom_default_returns_custom(self) -> None:
        """None with custom default must return that custom string."""
        result = _safe_str(value=None, default="missing")
        assert result == "missing"

    @pytest.mark.unit()
    @given(val=st.text(min_size=0, max_size=100))
    @settings(max_examples=200)
    def Test_string_returns_same_string(
        self,
        val: str,
    ) -> None:
        """Any string must be returned as-is."""
        result = _safe_str(value=val)
        assert result == val

    @pytest.mark.unit()
    @given(val=_st_valid_float)
    @settings(max_examples=200)
    def Test_float_returns_string_representation(
        self,
        val: float,
    ) -> None:
        """A float must be returned as str(val)."""
        result = _safe_str(value=val)
        assert isinstance(result, str)
        assert result == str(val)

    @pytest.mark.unit()
    @given(val=st.integers(min_value=-100_000, max_value=100_000))
    @settings(max_examples=200)
    def Test_integer_returns_string_representation(
        self,
        val: int,
    ) -> None:
        """An integer must be returned as str(val)."""
        result = _safe_str(value=val)
        assert result == str(val)

    @pytest.mark.unit()
    @given(
        val=st.one_of(st.text(min_size=1, max_size=50), _st_valid_float, st.integers(-1000, 1000))
    )
    @settings(max_examples=200)
    def Test_result_is_always_string(
        self,
        val: Any,
    ) -> None:
        """Result must always be a str for any non-None input."""
        result = _safe_str(value=val)
        assert isinstance(result, str)


# ===========================================================================
# Class_Test_Hypothesis_Polars_To_Records
# ===========================================================================


class Class_Test_Hypothesis_Polars_To_Records:
    """Property tests for _polars_to_records."""

    @pytest.mark.unit()
    def Test_none_returns_empty_list(self) -> None:
        """None must return []."""
        result = _polars_to_records(df=None)
        assert result == []

    @pytest.mark.unit()
    def Test_empty_dataframe_returns_empty_list(self) -> None:
        """Empty DataFrame must return []."""
        result = _polars_to_records(df=pl.DataFrame())
        assert result == []

    @pytest.mark.unit()
    @given(
        non_df=st.one_of(
            st.integers(),
            st.text(min_size=0, max_size=10),
            st.lists(st.integers(), min_size=0, max_size=3),
        )
    )
    @settings(max_examples=200)
    def Test_non_dataframe_returns_empty_list(
        self,
        non_df: Any,
    ) -> None:
        """Non-DataFrame input must return []."""
        result = _polars_to_records(df=non_df)  # type: ignore[arg-type]
        assert result == []

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=50),
        num_cols=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=200)
    def Test_output_length_equals_df_height(
        self,
        num_rows: int,
        num_cols: int,
    ) -> None:
        """Output list must have same length as df.height."""
        data = {f"col_{idx_c}": [float(idx_r + idx_c) for idx_r in range(num_rows)] for idx_c in range(num_cols)}
        df = pl.DataFrame(data)
        result = _polars_to_records(df=df)
        assert len(result) == num_rows

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=1, max_value=30),
        num_cols=st.integers(min_value=1, max_value=4),
    )
    @settings(max_examples=200)
    def Test_each_record_is_dict_with_all_column_keys(
        self,
        num_rows: int,
        num_cols: int,
    ) -> None:
        """Each item in the result must be a dict with all column names as keys."""
        col_names = [f"col_{idx_c}" for idx_c in range(num_cols)]
        data = {col_name: [float(idx_r) for idx_r in range(num_rows)] for col_name in col_names}
        df = pl.DataFrame(data)
        result = _polars_to_records(df=df)
        for record in result:
            assert isinstance(record, dict)
            for col_name in col_names:
                assert col_name in record


# ===========================================================================
# Class_Test_Hypothesis_Compute_Weight_Statistics
# ===========================================================================


class Class_Test_Hypothesis_Compute_Weight_Statistics:
    """Property tests for _compute_weight_statistics_from_weights."""

    @pytest.mark.unit()
    def Test_empty_df_returns_empty_list(self) -> None:
        """Empty DataFrame must return []."""
        df = pl.DataFrame({"Date": [], "AAA": []}).cast({"AAA": pl.Float64})
        result = _compute_weight_statistics_from_weights(weights_df=df)
        assert result == []

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=3, max_value=50))
    @settings(max_examples=200)
    def Test_single_weight_column_returns_one_row(
        self,
        num_rows: int,
    ) -> None:
        """A DataFrame with one non-Date column must return exactly one row."""
        weights_data = [0.1 * (idx % 10) for idx in range(num_rows)]
        df = pl.DataFrame({"AAA": weights_data})
        result = _compute_weight_statistics_from_weights(weights_df=df)
        assert len(result) == 1

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=3, max_value=50))
    @settings(max_examples=200)
    def Test_each_row_has_required_keys(
        self,
        num_rows: int,
    ) -> None:
        """Each output row must have the expected metric keys."""
        required_keys = {"component", "current_weight", "mean_weight", "min_weight", "max_weight", "std_weight"}
        df = pl.DataFrame(
            {
                "Asset_A": [0.4 + 0.01 * idx for idx in range(num_rows)],
                "Asset_B": [0.6 - 0.01 * idx for idx in range(num_rows)],
            }
        )
        result = _compute_weight_statistics_from_weights(weights_df=df)
        for row in result:
            assert isinstance(row, dict)
            assert required_keys.issubset(row.keys())

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=3, max_value=50))
    @settings(max_examples=200)
    def Test_min_lte_mean_lte_max(
        self,
        num_rows: int,
    ) -> None:
        """For each row, min_weight <= mean_weight <= max_weight must hold."""
        values = [0.3 + 0.01 * (idx % 10) for idx in range(num_rows)]
        df = pl.DataFrame({"Asset_X": values})
        result = _compute_weight_statistics_from_weights(weights_df=df)
        for row in result:
            assert row["min_weight"] <= row["mean_weight"] + 1e-9
            assert row["mean_weight"] <= row["max_weight"] + 1e-9

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=3, max_value=50),
        num_assets=st.integers(min_value=1, max_value=6),
    )
    @settings(max_examples=200)
    def Test_output_row_count_equals_asset_count(
        self,
        num_rows: int,
        num_assets: int,
    ) -> None:
        """Number of output rows must equal number of non-Date asset columns."""
        data = {
            f"Asset_{idx_a}": [0.1 * (idx_a + 1) for _ in range(num_rows)]
            for idx_a in range(num_assets)
        }
        df = pl.DataFrame(data)
        result = _compute_weight_statistics_from_weights(weights_df=df)
        assert len(result) == num_assets

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=3, max_value=50))
    @settings(max_examples=200)
    def Test_current_weight_is_last_value(
        self,
        num_rows: int,
    ) -> None:
        """current_weight must equal the last value in the column."""
        values = [0.1 * (idx + 1) for idx in range(num_rows)]
        df = pl.DataFrame({"MyAsset": values})
        result = _compute_weight_statistics_from_weights(weights_df=df)
        assert len(result) == 1
        expected_last = values[-1]
        assert abs(result[0]["current_weight"] - expected_last) < 1e-9

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=3, max_value=50))
    @settings(max_examples=200)
    def Test_single_value_column_has_zero_std(
        self,
        num_rows: int,
    ) -> None:
        """Column with all-same values must produce std_weight of 0."""
        df = pl.DataFrame({"Constant": [0.5] * num_rows})
        result = _compute_weight_statistics_from_weights(weights_df=df)
        assert len(result) == 1
        assert abs(result[0]["std_weight"]) < 1e-9


# ===========================================================================
# Class_Test_Hypothesis_Compute_Portfolio_Metrics
# ===========================================================================


class Class_Test_Hypothesis_Compute_Portfolio_Metrics:
    """Property tests for _compute_portfolio_metrics_from_values."""

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=5, max_value=100))
    @settings(max_examples=200)
    def Test_returns_dict_with_required_keys(
        self,
        num_rows: int,
    ) -> None:
        """Result must be a dict containing all expected metric keys."""
        required_keys = {
            "time_period",
            "start_date",
            "end_date",
            "total_return_portfolio",
            "annualized_return_portfolio",
            "volatility_portfolio",
            "max_drawdown_portfolio",
            "sharpe_ratio_portfolio",
        }
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv)
        assert isinstance(result, dict)
        assert required_keys.issubset(result.keys())

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=5, max_value=100))
    @settings(max_examples=200)
    def Test_max_drawdown_is_non_positive(
        self,
        num_rows: int,
    ) -> None:
        """Max drawdown must be <= 0 (it's always a drawdown or 0 for monotone)."""
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv)
        assert result["max_drawdown_portfolio"] <= 1e-9  # monotone growth → 0 drawdown

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=5, max_value=100))
    @settings(max_examples=200)
    def Test_monotone_growth_has_positive_total_return(
        self,
        num_rows: int,
    ) -> None:
        """Monotone growing portfolio must have positive total return."""
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv)
        assert result["total_return_portfolio"] > 0.0

    @pytest.mark.unit()
    @given(
        num_rows=st.integers(min_value=5, max_value=100),
        period_label=st.text(min_size=1, max_size=20),
    )
    @settings(max_examples=200)
    def Test_time_period_label_preserved(
        self,
        num_rows: int,
        period_label: str,
    ) -> None:
        """time_period in result must match the input period_label."""
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv, time_period=period_label)
        assert result["time_period"] == period_label

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=5, max_value=100))
    @settings(max_examples=200)
    def Test_all_metric_values_are_floats(
        self,
        num_rows: int,
    ) -> None:
        """All numeric metric values in result must be float instances."""
        numeric_keys = [
            "total_return_portfolio",
            "annualized_return_portfolio",
            "volatility_portfolio",
            "max_drawdown_portfolio",
            "sharpe_ratio_portfolio",
        ]
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv)
        for key in numeric_keys:
            assert isinstance(result[key], float), f"{key} is not float: {type(result[key])}"

    @pytest.mark.unit()
    @given(num_rows=st.integers(min_value=5, max_value=100))
    @settings(max_examples=200)
    def Test_without_benchmark_all_benchmark_metrics_are_zero(
        self,
        num_rows: int,
    ) -> None:
        """When bv=None, all benchmark metrics must be 0.0."""
        pv = _build_portfolio_value_df(num_rows=num_rows)
        result = _compute_portfolio_metrics_from_values(pv=pv, bv=None)
        for key in (
            "total_return_benchmark",
            "annualized_return_benchmark",
            "volatility_benchmark",
            "max_drawdown_benchmark",
            "sharpe_ratio_benchmark",
        ):
            assert result[key] == 0.0
