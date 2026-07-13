"""Hypothesis (property-based) tests for Yield_Curve_Model_Constant.

Tests cover:
- Constructor flat_rate validation (range [-0.10, 0.30])
- m_flat_rate stored correctly after construction
- fit() with empty DataFrame keeps constructor rate
- fit() with valid data updates m_flat_rate to mean of Yield column
- predict() returns Maturity + Yield columns
- predict() Yield column is all equal to m_flat_rate
- get_par_yield() equals m_flat_rate for all maturities
- get_forward_rate() equals m_flat_rate for all maturities
"""

from __future__ import annotations

import math

import polars as pl
import pytest

from hypothesis import given, HealthCheck, settings
from hypothesis import strategies as st

from src.models.yield_curve.model_yield_curve_constant import Yield_Curve_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FLAT_RATE = st.floats(
    min_value=-0.10, max_value=0.30, allow_nan=False, allow_infinity=False
)
_MATURITY = st.floats(
    min_value=0.1, max_value=30.0, allow_nan=False, allow_infinity=False
)


def _fitted_model(flat_rate: float = 0.03) -> Yield_Curve_Model_Constant:
    """Return a Yield_Curve_Model_Constant fitted on empty data."""
    model = Yield_Curve_Model_Constant(flat_rate=flat_rate)
    model.fit(data = pl.DataFrame())
    return model


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Yield_Curve_Constant_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Yield_Curve_Constant_Construction:
    """Tests for Yield_Curve_Model_Constant constructor."""

    @pytest.mark.unit()
    @given(flat_rate=_FLAT_RATE)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_flat_rate_stored_correctly(self, flat_rate: float) -> None:
        """m_flat_rate stores the constructor value exactly."""
        model = Yield_Curve_Model_Constant(flat_rate=flat_rate)
        assert math.isclose(model.m_flat_rate, flat_rate)

    @pytest.mark.unit()
    @given(
        out_of_range=st.one_of(
            st.floats(min_value=0.31, max_value=10.0, allow_nan=False, allow_infinity=False),
            st.floats(min_value=-10.0, max_value=-0.11, allow_nan=False, allow_infinity=False),
        )
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_out_of_range_rate_raises(self, out_of_range: float) -> None:
        """flat_rate outside [-0.10, 0.30] raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=out_of_range)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Yield_Curve_Constant_Fit
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Yield_Curve_Constant_Fit:
    """Tests for fit() behaviour."""

    @pytest.mark.unit()
    @given(flat_rate=_FLAT_RATE)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_empty_keeps_constructor_rate(self, flat_rate: float) -> None:
        """fit(empty DataFrame) leaves m_flat_rate unchanged."""
        model = Yield_Curve_Model_Constant(flat_rate=flat_rate)
        model.fit(data = pl.DataFrame())
        assert math.isclose(model.m_flat_rate, flat_rate)

    @pytest.mark.unit()
    @given(
        yields=st.lists(
            st.floats(min_value=-0.05, max_value=0.15, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20,
        )
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_data_sets_mean_yield(self, yields: list[float]) -> None:
        """fit() updates m_flat_rate to the mean of the Yield column."""
        maturities = [float(idx_m + 1) for idx_m in range(len(yields))]
        data = pl.DataFrame({"Maturity": maturities, "Yield": yields})
        model = Yield_Curve_Model_Constant()
        model.fit(data = data)
        expected_mean = sum(yields) / len(yields)
        assert math.isclose(model.m_flat_rate, expected_mean, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Yield_Curve_Constant_Predict
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Yield_Curve_Constant_Predict:
    """Tests for predict() structural invariants."""

    @pytest.mark.unit()
    @given(
        flat_rate=_FLAT_RATE,
        n_points=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_has_maturity_and_yield_columns(
        self,
        flat_rate: float,
        n_points: int,
    ) -> None:
        """predict() returns DataFrame with Maturity and Yield columns."""
        model = _fitted_model(flat_rate=flat_rate)
        df = model.predict(n_points=n_points)
        assert "Maturity" in df.columns
        assert "Yield" in df.columns

    @pytest.mark.unit()
    @given(
        flat_rate=_FLAT_RATE,
        n_points=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_correct_row_count(
        self,
        flat_rate: float,
        n_points: int,
    ) -> None:
        """predict() returns exactly n_points rows."""
        model = _fitted_model(flat_rate=flat_rate)
        df = model.predict(n_points=n_points)
        assert len(df) == n_points

    @pytest.mark.unit()
    @given(
        flat_rate=_FLAT_RATE,
        n_points=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_all_yields_equal_flat_rate(
        self,
        flat_rate: float,
        n_points: int,
    ) -> None:
        """Every Yield value equals m_flat_rate (flat curve invariant)."""
        model = _fitted_model(flat_rate=flat_rate)
        df = model.predict(n_points=n_points)
        for item_y in df["Yield"].to_list():
            assert math.isclose(item_y, flat_rate, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        flat_rate=_FLAT_RATE,
        n_points=st.integers(min_value=2, max_value=50),
        max_mat=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_maturities_positive(
        self,
        flat_rate: float,
        n_points: int,
        max_mat: float,
    ) -> None:
        """All Maturity values are strictly positive."""
        model = _fitted_model(flat_rate=flat_rate)
        df = model.predict(n_points=n_points, max_maturity=max_mat)
        for item_m in df["Maturity"].to_list():
            assert item_m > 0


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Yield_Curve_Constant_Par_And_Forward
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Yield_Curve_Constant_Par_And_Forward:
    """Tests for get_par_yield() and get_forward_rate() invariants."""

    @pytest.mark.unit()
    @given(flat_rate=_FLAT_RATE, maturity=_MATURITY)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_par_yield_equals_flat_rate(
        self,
        flat_rate: float,
        maturity: float,
    ) -> None:
        """get_par_yield() returns m_flat_rate for all maturities."""
        model = _fitted_model(flat_rate=flat_rate)
        assert math.isclose(model.get_par_yield(maturity=maturity), flat_rate)

    @pytest.mark.unit()
    @given(flat_rate=_FLAT_RATE, maturity=_MATURITY)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_forward_rate_equals_flat_rate(
        self,
        flat_rate: float,
        maturity: float,
    ) -> None:
        """get_forward_rate() returns m_flat_rate for all maturities."""
        model = _fitted_model(flat_rate=flat_rate)
        assert math.isclose(model.get_forward_rate(maturity=maturity), flat_rate)

    @pytest.mark.unit()
    @given(flat_rate=_FLAT_RATE, maturity=_MATURITY)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_par_yield_equals_forward_rate(
        self,
        flat_rate: float,
        maturity: float,
    ) -> None:
        """par_yield equals forward_rate for all maturities on flat curve."""
        model = _fitted_model(flat_rate=flat_rate)
        par = model.get_par_yield(maturity=maturity)
        fwd = model.get_forward_rate(maturity=maturity)
        assert math.isclose(par, fwd)
