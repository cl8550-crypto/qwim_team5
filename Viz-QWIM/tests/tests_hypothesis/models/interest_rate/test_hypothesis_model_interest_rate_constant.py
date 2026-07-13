"""Hypothesis (property-based) tests for Interest_Rate_Model_Constant.

Tests cover:
- Valid construction across the allowed rate range [-0.10, 0.50]
- ``fit()`` on empty DataFrame keeps constructor rate
- ``fit()`` on non-empty DataFrame estimates arithmetic mean of short_rate
- ``predict()`` returns constant-rate DataFrame with expected shape and values
- ``get_annual_rate()`` round-trip after fit
"""

from __future__ import annotations

import polars as pl
import pytest

from hypothesis import given, HealthCheck, settings
from hypothesis import strategies as st

from src.models.interest_rate.model_interest_rate_constant import Interest_Rate_Model_Constant


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Interest_Rate_Constant_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Interest_Rate_Constant_Construction:
    """Tests for valid construction of Interest_Rate_Model_Constant."""

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=-0.10, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_valid_rate_stores_correctly(
        self,
        annual_rate: float,
    ) -> None:
        """Constructor stores any valid rate in [-0.10, 0.50] correctly."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        assert model.m_annual_rate == annual_rate

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=-0.10, max_value=0.50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_valid_rate_name_model_stored(
        self,
        annual_rate: float,
    ) -> None:
        """Custom name_model is stored in m_name_model."""
        model = Interest_Rate_Model_Constant(
            annual_rate=annual_rate,
            name_model="Test IR Model",
        )
        assert model.name_model == "Test IR Model"

    @pytest.mark.unit()
    @given(
        annual_rate=st.one_of(
            st.floats(max_value=-0.101, allow_nan=False, allow_infinity=False),
            st.floats(min_value=0.501, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_out_of_range_rate_raises(
        self,
        annual_rate: float,
    ) -> None:
        """Rate outside [-0.10, 0.50] raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Constant(annual_rate=annual_rate)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Interest_Rate_Constant_Fit_Empty
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Interest_Rate_Constant_Fit_Empty:
    """Tests for fit() with an empty DataFrame (no-op)."""

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=-0.09, max_value=0.49, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_empty_preserves_constructor_rate(
        self,
        annual_rate: float,
    ) -> None:
        """fit(empty DataFrame) leaves the constructor rate unchanged."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        result = model.fit(data = pl.DataFrame())
        assert result.m_annual_rate == annual_rate

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=-0.09, max_value=0.49, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_returns_self(
        self,
        annual_rate: float,
    ) -> None:
        """fit() returns the same model instance (method chaining)."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        result = model.fit(data = pl.DataFrame())
        assert result is model


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Interest_Rate_Constant_Fit_Data
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Interest_Rate_Constant_Fit_Data:
    """Tests for fit() with non-empty historical rate data."""

    @pytest.mark.unit()
    @given(
        rates=st.lists(
            st.floats(min_value=-0.05, max_value=0.30, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20,
        ),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_estimates_mean_of_short_rate(
        self,
        rates: list[float],
    ) -> None:
        """fit() sets m_annual_rate to the arithmetic mean of short_rate column."""
        import math

        hist = pl.DataFrame(
            {
                "Date": [f"202{i % 10}-01-01" for i in range(len(rates))],
                "short_rate": rates,
            }
        )
        model = Interest_Rate_Model_Constant()
        model.fit(data = hist)
        expected_mean = sum(rates) / len(rates)
        assert math.isclose(model.m_annual_rate, expected_mean, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        rate_val=st.floats(min_value=0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
        n_obs=st.integers(min_value=2, max_value=30),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_fit_constant_data_returns_same_rate(
        self,
        rate_val: float,
        n_obs: int,
    ) -> None:
        """fit() on constant short_rate data returns exactly that rate."""
        import math

        hist = pl.DataFrame(
            {
                "Date": [f"2020-{(i % 12) + 1:02d}-01" for i in range(n_obs)],
                "short_rate": [rate_val] * n_obs,
            }
        )
        model = Interest_Rate_Model_Constant()
        model.fit(data = hist)
        assert math.isclose(model.m_annual_rate, rate_val, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Interest_Rate_Constant_Predict
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Interest_Rate_Constant_Predict:
    """Tests for predict() output shape, type, and value invariants."""

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
        n_periods=st.integers(min_value=1, max_value=24),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_returns_correct_row_count(
        self,
        annual_rate: float,
        n_periods: int,
    ) -> None:
        """predict(n_periods) DataFrame has exactly n_periods rows."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        model.fit(data = pl.DataFrame())
        df_result = model.predict(n_periods=n_periods, start_date="2025-01-01")
        assert len(df_result) == n_periods

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
        n_periods=st.integers(min_value=1, max_value=24),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_all_rates_equal_annual_rate(
        self,
        annual_rate: float,
        n_periods: int,
    ) -> None:
        """All short_rate values in predict() output equal the fitted rate."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        model.fit(data = pl.DataFrame())
        df_result = model.predict(n_periods=n_periods, start_date="2025-01-01")
        rates = df_result["short_rate"].to_list()
        assert all(r == annual_rate for r_val in rates for r in [r_val])

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
        n_periods=st.integers(min_value=1, max_value=24),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_predict_has_date_and_short_rate_columns(
        self,
        annual_rate: float,
        n_periods: int,
    ) -> None:
        """predict() DataFrame always has columns Date and short_rate."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        model.fit(data = pl.DataFrame())
        df_result = model.predict(n_periods=n_periods, start_date="2025-01-01")
        assert "Date" in df_result.columns
        assert "short_rate" in df_result.columns

    @pytest.mark.unit()
    @given(
        annual_rate=st.floats(min_value=0.0, max_value=0.20, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_get_annual_rate_matches_fitted_rate(
        self,
        annual_rate: float,
    ) -> None:
        """get_annual_rate() returns the same value as m_annual_rate after fit."""
        model = Interest_Rate_Model_Constant(annual_rate=annual_rate)
        model.fit(data = pl.DataFrame())
        assert model.get_annual_rate() == model.m_annual_rate
