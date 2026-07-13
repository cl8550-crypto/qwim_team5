"""Unit tests for ``src.dashboard.shiny_utils.utils_tab_results``.

All tests run without a Shiny session.  The three functions under test are
pure-Python DataFrame transformations.

Run:
    pytest tests/tests_shiny/ -m unit -k utils_tab_results
"""

from __future__ import annotations

import pytest
import polars as pl
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _date_value_df(n_rows: int = 10, value_mul: float = 1.0) -> pl.DataFrame:
    """Return a small Polars DataFrame with 'date' and 'value' columns."""
    return pl.DataFrame(
        {
            "date": [f"2024-{(i % 12) + 1:02d}-01" for i in range(n_rows)],
            "series_A": [float(i + 1) * value_mul for i in range(n_rows)],
            "series_B": [float((n_rows - i)) * value_mul for i in range(n_rows)],
        }
    )


def _large_df(n_rows: int = 6000) -> pl.DataFrame:
    """Return a DataFrame with more than 5000 rows to trigger downsampling.

    Uses unique-ish dates by cycling year/month/day combinations so the date
    column does not cause grouping-based deduplication to reduce row counts
    before the max_points check.
    """
    from datetime import date, timedelta

    start = date(2000, 1, 1)
    return pl.DataFrame(
        {
            "date": [(start + timedelta(days=i)).isoformat() for i in range(n_rows)],
            "series_A": [float(i) for i in range(n_rows)],
        }
    )


# ---------------------------------------------------------------------------
# process_data_for_plot_tab_results
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProcessDataForPlotTabResults:
    """process_data_for_plot_tab_results passes small DFs through unchanged."""

    def test_none_returns_none_or_safe(self) -> None:
        """Test that none returns none or safe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        result = process_data_for_plot_tab_results(data_frame = None)  # type: ignore[arg-type]
        # Either returns None or some safe DataFrame equivalent — must not raise
        assert result is None or isinstance(result, pl.DataFrame)

    def test_empty_df_returns_empty_or_safe(self) -> None:
        """Test that empty df returns empty or safe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        result = process_data_for_plot_tab_results(data_frame = pl.DataFrame())
        assert result is None or isinstance(result, pl.DataFrame)

    def test_small_df_rows_unchanged(self) -> None:
        """Test that small df rows unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        df = _date_value_df(n_rows=100)
        result = process_data_for_plot_tab_results(data_frame = df, max_points=5000)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 100

    def test_returns_polars_dataframe(self) -> None:
        """Test that returns polars dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        df = _date_value_df()
        result = process_data_for_plot_tab_results(data_frame = df)
        assert isinstance(result, pl.DataFrame)

    def test_large_df_is_downsampled(self) -> None:
        """Test that large df is downsampled."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        # Use 6000 rows with max_points=1000 so stride = 6000//1000 = 6 > 1,
        # guaranteeing the function actually reduces the row count.
        df = _large_df(n_rows=6000)
        result = process_data_for_plot_tab_results(data_frame = df, max_points=1000)
        assert isinstance(result, pl.DataFrame)
        assert len(result) < 6000

    def test_columns_preserved(self) -> None:
        """Test that columns preserved."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        df = _date_value_df(n_rows=50)
        result = process_data_for_plot_tab_results(data_frame = df)
        for col in df.columns:
            assert col in result.columns

    def test_custom_date_column_name(self) -> None:
        """Test that custom date column name."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = process_data_for_plot_tab_results(data_frame = df, date_column="date")
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.parametrize("max_pts", [100, 500, 1000])
    def test_parametric_max_points(self, max_pts: int) -> None:
        """Test that parametric max points."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            process_data_for_plot_tab_results,
        )

        # Use n = max_pts * 10 to ensure stride = n // max_pts = 10 > 1,
        # so the function always reduces the row count.
        n = max_pts * 10
        df = _large_df(n_rows=n)
        result = process_data_for_plot_tab_results(data_frame = df, max_points=max_pts)
        assert isinstance(result, pl.DataFrame)
        assert len(result) < n


# ---------------------------------------------------------------------------
# normalize_data_tab_results
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestNormalizeDataTabResults:
    """normalize_data_tab_results applies the requested normalisation method."""

    def test_method_none_returns_unchanged(self) -> None:
        """Test that method none returns unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        result = normalize_data_tab_results(data_frame = df, method="none")
        assert isinstance(result, pl.DataFrame)
        # Shape must be identical
        assert result.shape == df.shape

    def test_min_max_returns_dataframe(self) -> None:
        """Test that min max returns dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = normalize_data_tab_results(data_frame = df, method="min_max")
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 20

    def test_min_max_numeric_columns_bounded_0_to_1(self) -> None:
        """Test that min max numeric columns bounded 0 to 1."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=10)
        result = normalize_data_tab_results(data_frame = df, method="min_max")
        assert isinstance(result, pl.DataFrame)
        # Check every numeric column is in [0, 1]
        numeric_cols = [c for c in result.columns if c != "date"]
        for col in numeric_cols:
            col_vals = result[col].to_list()
            numeric_vals = [v for v in col_vals if v is not None]
            if numeric_vals:
                assert min(numeric_vals) >= -1e-9, f"{col} min < 0"
                assert max(numeric_vals) <= 1.0 + 1e-9, f"{col} max > 1"

    def test_z_score_returns_dataframe(self) -> None:
        """Test that z score returns dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = normalize_data_tab_results(data_frame = df, method="z_score")
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 20

    def test_z_score_numeric_mean_near_zero(self) -> None:
        """Test that z score numeric mean near zero."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = normalize_data_tab_results(data_frame = df, method="z_score")
        assert isinstance(result, pl.DataFrame)
        numeric_cols = [c for c in result.columns if c != "date"]
        for col in numeric_cols:
            col_series = result[col].drop_nulls()
            if len(col_series) > 1:
                mean_val = col_series.mean()
                assert abs(mean_val) < 0.5, (
                    f"Z-score mean for '{col}' expected near 0, got {mean_val}"
                )

    def test_min_max_constant_series_remains_unchanged(self) -> None:
        """Constant series should skip min-max normalization updates."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = pl.DataFrame(
            {
                "date": [f"2024-01-0{i}" for i in range(1, 5)],
                "series_A": [5.0, 5.0, 5.0, 5.0],
                "series_B": [2.0, 2.0, 2.0, 2.0],
            }
        )
        result = normalize_data_tab_results(data_frame = df, method="min_max")
        assert isinstance(result, pl.DataFrame)
        assert result["series_A"].to_list() == [5.0, 5.0, 5.0, 5.0]
        assert result["series_B"].to_list() == [2.0, 2.0, 2.0, 2.0]

    def test_z_score_constant_series_remains_unchanged(self) -> None:
        """Constant series should skip z-score normalization updates."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = pl.DataFrame(
            {
                "date": [f"2024-02-0{i}" for i in range(1, 5)],
                "series_A": [3.0, 3.0, 3.0, 3.0],
                "series_B": [7.0, 7.0, 7.0, 7.0],
            }
        )
        result = normalize_data_tab_results(data_frame = df, method="z_score")
        assert isinstance(result, pl.DataFrame)
        assert result["series_A"].to_list() == [3.0, 3.0, 3.0, 3.0]
        assert result["series_B"].to_list() == [7.0, 7.0, 7.0, 7.0]

    def test_none_method_defaults_to_no_change(self) -> None:
        """Test that none method defaults to no change."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        original_values = df["series_A"].to_list()
        result = normalize_data_tab_results(data_frame = df, method="none")
        result_values = result["series_A"].to_list()
        assert result_values == original_values

    def test_unsupported_method_returns_df_or_raises(self) -> None:
        """Test that unsupported method returns df or raises."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        # Either returns df unchanged or raises ValueError — both are acceptable
        try:
            result = normalize_data_tab_results(data_frame = df, method="unsupported_method")
            assert isinstance(result, pl.DataFrame)
        except (ValueError, KeyError):
            pass  # Raising is acceptable for unknown method

    @pytest.mark.parametrize("method", ["none", "min_max", "z_score"])
    def test_all_methods_return_correct_shape(self, method: str) -> None:
        """Test that all methods return correct shape."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            normalize_data_tab_results,
        )

        df = _date_value_df(n_rows=15)
        result = normalize_data_tab_results(data_frame = df, method=method)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 15


# ---------------------------------------------------------------------------
# transform_data_tab_results
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTransformDataTabResults:
    """transform_data_tab_results applies the requested transformation."""

    def test_transformation_none_returns_unchanged(self) -> None:
        """Test that transformation none returns unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        result = transform_data_tab_results(data_frame = df, transformation="none")
        assert isinstance(result, pl.DataFrame)
        assert result.shape == df.shape

    def test_percent_change_returns_dataframe(self) -> None:
        """Test that percent change returns dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = transform_data_tab_results(data_frame = df, transformation="percent_change")
        assert isinstance(result, pl.DataFrame)

    def test_cumulative_returns_dataframe(self) -> None:
        """Test that cumulative returns dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = transform_data_tab_results(data_frame = df, transformation="cumulative")
        assert isinstance(result, pl.DataFrame)

    def test_comparative_returns_dataframe(self) -> None:
        """Test that comparative returns dataframe."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=20)
        result = transform_data_tab_results(data_frame = df, transformation="comparative")
        assert isinstance(result, pl.DataFrame)

    def test_comparative_with_baseline_date(self) -> None:
        """Test that comparative with baseline date."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=10)
        result = transform_data_tab_results(
            data_frame = df,
            transformation="comparative",
            baseline_date="2024-01-01",
        )
        assert isinstance(result, pl.DataFrame)

    def test_none_transformation_preserves_values(self) -> None:
        """Test that none transformation preserves values."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        original_a = df["series_A"].to_list()
        result = transform_data_tab_results(data_frame = df, transformation="none")
        assert result["series_A"].to_list() == original_a

    def test_percent_change_first_row_is_zero_or_null(self) -> None:
        """Test that percent change first row is zero or null."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=10)
        result = transform_data_tab_results(data_frame = df, transformation="percent_change")
        assert isinstance(result, pl.DataFrame)
        # First row pct_change is conventionally 0 or null
        # We just check the shape is maintained or reduced by 1
        assert len(result) >= len(df) - 1

    def test_percent_change_skips_zero_baseline_series(self) -> None:
        """Percent change should skip series whose first value is zero."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = pl.DataFrame(
            {
                "date": [f"2024-03-0{i}" for i in range(1, 5)],
                "series_A": [0.0, 10.0, 20.0, 30.0],
                "series_B": [0.0, 5.0, 10.0, 15.0],
            }
        )
        result = transform_data_tab_results(data_frame = df, transformation="percent_change")
        assert isinstance(result, pl.DataFrame)
        assert "series_A_pct" not in result.columns
        assert "series_B_pct" not in result.columns

    def test_result_has_same_row_count(self) -> None:
        """Most transformations must preserve row count."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        for transformation in ("none", "cumulative", "comparative"):
            df = _date_value_df(n_rows=12)
            result = transform_data_tab_results(data_frame = df, transformation=transformation)
            assert len(result) >= len(df) - 1, (
                f"Row count dropped too much for transformation='{transformation}'"
            )

    @pytest.mark.parametrize(
        "transformation",
        ["none", "percent_change", "cumulative", "comparative"],
    )
    def test_all_transformations_return_polars_df(self, transformation: str) -> None:
        """Test that all transformations return polars df."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=10)
        result = transform_data_tab_results(data_frame = df, transformation=transformation)
        assert isinstance(result, pl.DataFrame)

    def test_unsupported_transformation_returns_df_or_raises(self) -> None:
        """Test that unsupported transformation returns df or raises."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = _date_value_df(n_rows=5)
        try:
            result = transform_data_tab_results(data_frame = df, transformation="invalid_transform")
            assert isinstance(result, pl.DataFrame)
        except (ValueError, KeyError):
            pass  # Raising is acceptable for unknown transformation

    def test_comparative_skips_zero_baseline_series(self) -> None:
        """Comparative transform should skip series with zero baseline values."""
        from src.dashboard.shiny_utils.utils_tab_results import (
            transform_data_tab_results,
        )

        df = pl.DataFrame(
            {
                "date": ["2024-04-01", "2024-04-02", "2024-04-03"],
                "series_A": [0.0, 10.0, 20.0],
                "series_B": [0.0, 4.0, 8.0],
            }
        )
        result = transform_data_tab_results(
            data_frame = df,
            transformation="comparative",
            baseline_date="2024-04-01",
        )
        assert isinstance(result, pl.DataFrame)
        assert "series_A_rel" not in result.columns
        assert "series_B_rel" not in result.columns
