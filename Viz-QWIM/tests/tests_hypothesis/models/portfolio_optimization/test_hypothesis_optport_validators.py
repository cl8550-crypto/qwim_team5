"""Hypothesis-based tests for portfolio optimization validator helpers.

Tests cover:
- _validate_returns_data
- _convert_polars_to_numpy_returns
- _compute_covar_and_means
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.models.portfolio_optimization._optport_validators import (
    _compute_covar_and_means,
    _convert_polars_to_numpy_returns,
    _validate_returns_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_df(n_rows: int = 5, n_assets: int = 2) -> pl.DataFrame:
    """Return a minimal valid returns DataFrame."""
    rng = np.random.default_rng(42)
    data: dict[str, object] = {"Date": [f"2024-01-{i+1:02d}" for i in range(n_rows)]}
    for j in range(n_assets):
        data[f"Asset{j+1}"] = rng.normal(0.0, 0.01, n_rows).tolist()
    return pl.DataFrame(data)


# ---------------------------------------------------------------------------
# Tests for _validate_returns_data
# ---------------------------------------------------------------------------


class Class_Test_Validate_Returns_Data:
    """Tests for _validate_returns_data."""

    @pytest.mark.unit()
    def Test_None_Input_Returns_Invalid(self) -> None:
        """None input should return (False, non-empty message)."""
        is_valid, msg = _validate_returns_data(returns_data = None)  # type: ignore[arg-type]
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_Non_DataFrame_Returns_Invalid(self) -> None:
        """A plain dict should return invalid."""
        is_valid, msg = _validate_returns_data(returns_data = {"Date": [], "A": []})  # type: ignore[arg-type]
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_Empty_DataFrame_Returns_Invalid(self) -> None:
        """Zero-row DataFrame should return invalid."""
        df = pl.DataFrame({"Date": [], "A": []})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_Missing_Date_Column_Returns_Invalid(self) -> None:
        """DataFrame without 'Date' column should return invalid."""
        df = pl.DataFrame({"A": [0.01, 0.02], "B": [0.01, -0.01]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_No_Asset_Columns_Returns_Invalid(self) -> None:
        """DataFrame with only 'Date' column should return invalid."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_Non_Numeric_Asset_Column_Returns_Invalid(self) -> None:
        """String asset column should return invalid."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"], "A": ["x", "y"]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert len(msg) > 0

    @pytest.mark.unit()
    def Test_Valid_DataFrame_Returns_Valid(self) -> None:
        """A well-formed returns DataFrame should return (True, '')."""
        df = _make_valid_df(n_rows=10, n_assets=3)
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=2, max_value=50),
        n_assets=st.integers(min_value=1, max_value=8),
    )
    @settings(max_examples=200)
    def Test_Valid_DataFrames_Always_Pass(self, n_rows: int, n_assets: int) -> None:
        """Randomly-sized valid DataFrames should always return valid."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        is_valid, _ = _validate_returns_data(returns_data = df)
        assert is_valid is True


# ---------------------------------------------------------------------------
# Tests for _convert_polars_to_numpy_returns
# ---------------------------------------------------------------------------


class Class_Test_Convert_Polars_To_Numpy_Returns:
    """Tests for _convert_polars_to_numpy_returns."""

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=2, max_value=50),
        n_assets=st.integers(min_value=1, max_value=8),
    )
    @settings(max_examples=200)
    def Test_Output_Shape_Matches_Input(self, n_rows: int, n_assets: int) -> None:
        """Output shape should be (n_rows, n_assets)."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        assert arr.shape == (n_rows, n_assets)

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=2, max_value=50),
        n_assets=st.integers(min_value=1, max_value=8),
    )
    @settings(max_examples=200)
    def Test_Output_Dtype_Is_Float64(self, n_rows: int, n_assets: int) -> None:
        """Output dtype should be float64."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        assert arr.dtype == np.float64

    @pytest.mark.unit()
    def Test_Single_Asset_Returns_2d(self) -> None:
        """Single-asset input should still return 2-D array."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"], "A": [0.01, -0.01]})
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        assert arr.ndim == 2
        assert arr.shape == (2, 1)


# ---------------------------------------------------------------------------
# Tests for _compute_covar_and_means
# ---------------------------------------------------------------------------


class Class_Test_Compute_Covar_And_Means:
    """Tests for _compute_covar_and_means."""

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=3, max_value=50),
        n_assets=st.integers(min_value=1, max_value=8),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.too_slow],
        deadline=None,
    )
    def Test_Covar_Shape_Is_N_By_N(self, n_rows: int, n_assets: int) -> None:
        """Covariance matrix should have shape (n_assets, n_assets)."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        covar, _ = _compute_covar_and_means(returns_array = arr)
        assert covar.shape == (n_assets, n_assets)

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=3, max_value=50),
        n_assets=st.integers(min_value=1, max_value=8),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.too_slow],
        deadline=None,
    )
    def Test_Means_Shape_Is_N(self, n_rows: int, n_assets: int) -> None:
        """Means vector should have shape (n_assets,)."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        _, means = _compute_covar_and_means(returns_array = arr)
        assert means.shape == (n_assets,)

    @pytest.mark.unit()
    def Test_Single_Asset_Scalar_Handled(self) -> None:
        """Single-asset covar should be a 2-D (1, 1) array, not scalar."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02", "2024-01-03"], "A": [0.01, -0.01, 0.005]})
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        covar, means = _compute_covar_and_means(returns_array = arr)
        assert covar.shape == (1, 1)
        assert means.shape == (1,)

    @pytest.mark.unit()
    @given(
        n_rows=st.integers(min_value=3, max_value=50),
        n_assets=st.integers(min_value=2, max_value=8),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.too_slow],
        deadline=None,
    )
    def Test_Covar_Is_Symmetric(self, n_rows: int, n_assets: int) -> None:
        """Covariance matrix should be symmetric."""
        df = _make_valid_df(n_rows=n_rows, n_assets=n_assets)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        covar, _ = _compute_covar_and_means(returns_array = arr)
        assert np.allclose(covar, covar.T, atol=1e-12)
