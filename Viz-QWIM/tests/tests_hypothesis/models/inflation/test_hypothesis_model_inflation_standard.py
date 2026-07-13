"""Hypothesis (property-based) tests for Inflation_Model_Standard.

Tests cover:
- Constructor parameter validation (kappa > 0, sigma > 0, n_simulations > 0)
- Constructor stores parameters correctly
- get_analytical_mean() converges to theta as t → ∞
- get_analytical_variance() is non-negative and bounded by sigma²/(2*kappa)
- predict() returns correct shape and expected column names
- predict() Mean column is finite for all rows
"""

from __future__ import annotations

import math

import polars as pl
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.inflation.model_inflation_base import Inflation_Model_Status
from src.models.inflation.model_inflation_standard import Inflation_Model_Standard
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KAPPA = st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False)
_THETA = st.floats(min_value=-0.05, max_value=0.20, allow_nan=False, allow_infinity=False)
_SIGMA = st.floats(min_value=0.001, max_value=0.10, allow_nan=False, allow_infinity=False)

_PREDICT_COLS = {"Date", "Mean", "Median", "Std", "P5", "P25", "P75", "P95", "Min", "Max"}


def _fitted_model(
    kappa: float = 0.5,
    theta: float = 0.025,
    sigma: float = 0.010,
) -> Inflation_Model_Standard:
    """Return a pre-fitted Inflation_Model_Standard using synthetic data."""
    model = Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=sigma, n_simulations=50)
    import datetime

    dates = [datetime.date(2000 + idx_yr, 1, 1) for idx_yr in range(10)]
    rates = [theta + 0.005 * ((-1) ** idx_yr) for idx_yr in range(10)]
    data = pl.DataFrame({"Date": dates, "inflation_rate": rates})
    model.fit(data = data)
    return model


def _analytical_model(
    kappa: float = 0.5,
    theta: float = 0.025,
    sigma: float = 0.010,
) -> Inflation_Model_Standard:
    """Return a fitted-status model for analytical helper tests.

    The analytical mean and variance methods only depend on fitted status and
    the model parameters. They do not require an expensive OLS fit on every
    Hypothesis example.
    """
    model = Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=sigma, n_simulations=50)
    model.m_status = Inflation_Model_Status.FITTED
    model.m_current_rate = float(theta)
    return model


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Inflation_Standard_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Standard_Construction:
    """Tests for Inflation_Model_Standard constructor."""

    @pytest.mark.unit()
    @given(kappa=_KAPPA, theta=_THETA, sigma=_SIGMA)
    @settings(max_examples=200)
    def Test_parameters_stored_correctly(
        self,
        kappa: float,
        theta: float,
        sigma: float,
    ) -> None:
        """m_kappa, m_theta, m_sigma store constructor values."""
        model = Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=sigma)
        assert math.isclose(model.m_kappa, kappa)
        assert math.isclose(model.m_theta, theta)
        assert math.isclose(model.m_sigma, sigma)

    @pytest.mark.unit()
    @given(theta=_THETA, sigma=_SIGMA)
    @settings(max_examples=200)
    def Test_invalid_kappa_zero_raises(self, theta: float, sigma: float) -> None:
        """kappa=0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(kappa=0.0, theta=theta, sigma=sigma)

    @pytest.mark.unit()
    @given(kappa=_KAPPA, theta=_THETA)
    @settings(max_examples=200)
    def Test_invalid_sigma_zero_raises(self, kappa: float, theta: float) -> None:
        """sigma=0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=0.0)

    @pytest.mark.unit()
    @given(kappa=_KAPPA, theta=_THETA, sigma=_SIGMA)
    @settings(max_examples=200)
    def Test_invalid_n_simulations_zero_raises(
        self,
        kappa: float,
        theta: float,
        sigma: float,
    ) -> None:
        """n_simulations=0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=sigma, n_simulations=0)

    @pytest.mark.unit()
    @given(kappa=_KAPPA, theta=_THETA, sigma=_SIGMA, invalid_n_simulations=st.booleans())
    @settings(max_examples=20)
    def Test_invalid_n_simulations_bool_raises(
        self,
        kappa: float,
        theta: float,
        sigma: float,
        invalid_n_simulations: bool,
    ) -> None:
        """Boolean n_simulations values raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(
                kappa=kappa,
                theta=theta,
                sigma=sigma,
                n_simulations=invalid_n_simulations,
            )

    @pytest.mark.unit()
    @given(kappa=_KAPPA, theta=_THETA, sigma=_SIGMA)
    @settings(max_examples=200)
    def Test_initial_current_rate_equals_theta(
        self,
        kappa: float,
        theta: float,
        sigma: float,
    ) -> None:
        """m_current_rate is initialized to theta before fitting."""
        model = Inflation_Model_Standard(kappa=kappa, theta=theta, sigma=sigma)
        assert math.isclose(model.m_current_rate, theta)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Inflation_Standard_Analytical_Mean
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Standard_Analytical_Mean:
    """Tests for get_analytical_mean() invariants."""

    @pytest.mark.unit()
    @given(invalid_t_years=st.booleans())
    @settings(max_examples=2)
    def Test_invalid_bool_t_years_raises(
        self,
        invalid_t_years: bool,
    ) -> None:
        """Boolean t_years values raise Exception_Validation_Input."""
        model = _analytical_model()

        with pytest.raises(Exception_Validation_Input):
            model.get_analytical_mean(t_years=invalid_t_years)

    @pytest.mark.unit()
    @given(
        kappa=_KAPPA,
        theta=_THETA,
        sigma=_SIGMA,
        t_years=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False),
        pi0=st.floats(min_value=-0.05, max_value=0.15, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_mean_finite(
        self,
        kappa: float,
        theta: float,
        sigma: float,
        t_years: float,
        pi0: float,
    ) -> None:
        """get_analytical_mean() always returns a finite float."""
        model = _analytical_model(kappa=kappa, theta=theta, sigma=sigma)
        result = model.get_analytical_mean(t_years=t_years, pi0=pi0)
        assert math.isfinite(result)

    @pytest.mark.unit()
    @given(
        kappa=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        theta=_THETA,
        sigma=_SIGMA,
        pi0=st.floats(min_value=-0.05, max_value=0.15, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_mean_converges_to_theta_for_large_t(
        self,
        kappa: float,
        theta: float,
        sigma: float,
        pi0: float,
    ) -> None:
        """For large kappa and t=20, mean should be close to theta."""
        model = _analytical_model(kappa=kappa, theta=theta, sigma=sigma)
        result = model.get_analytical_mean(t_years=20.0, pi0=pi0)
        assert math.isclose(result, theta, abs_tol=0.01)

    @pytest.mark.unit()
    @given(
        kappa=_KAPPA,
        theta=_THETA,
        sigma=_SIGMA,
    )
    @settings(max_examples=200)
    def Test_mean_at_t_zero_approaches_current_rate(
        self,
        kappa: float,
        theta: float,
        sigma: float,
    ) -> None:
        """For t→0, mean should approach pi0 (current_rate)."""
        model = _analytical_model(kappa=kappa, theta=theta, sigma=sigma)
        pi0 = model.m_current_rate
        result = model.get_analytical_mean(t_years=0.001, pi0=pi0)
        assert math.isclose(result, pi0, abs_tol=0.01)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Inflation_Standard_Analytical_Variance
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Standard_Analytical_Variance:
    """Tests for get_analytical_variance() invariants."""

    @pytest.mark.unit()
    @given(
        kappa=_KAPPA,
        theta=_THETA,
        sigma=_SIGMA,
        t_years=st.floats(min_value=0.01, max_value=30.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_variance_non_negative(
        self,
        kappa: float,
        theta: float,
        sigma: float,
        t_years: float,
    ) -> None:
        """Analytical variance is always non-negative."""
        model = _analytical_model(kappa=kappa, theta=theta, sigma=sigma)
        var = model.get_analytical_variance(t_years=t_years)
        assert var >= 0.0

    @pytest.mark.unit()
    @given(
        kappa=_KAPPA,
        theta=_THETA,
        sigma=_SIGMA,
        t_years=st.floats(min_value=0.1, max_value=30.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def Test_variance_bounded_by_stationary_variance(
        self,
        kappa: float,
        theta: float,
        sigma: float,
        t_years: float,
    ) -> None:
        """Variance <= sigma²/(2*kappa) (stationary variance bound)."""
        model = _analytical_model(kappa=kappa, theta=theta, sigma=sigma)
        var = model.get_analytical_variance(t_years=t_years)
        stationary_var = sigma**2 / (2.0 * kappa)
        assert var <= stationary_var + 1e-10


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Inflation_Standard_Predict
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Standard_Predict:
    """Tests for predict() structural invariants."""

    @pytest.mark.unit()
    @given(n_periods=st.integers(min_value=1, max_value=24))
    @settings(max_examples=200)
    def Test_predict_returns_correct_row_count(self, n_periods: int) -> None:
        """predict() returns exactly n_periods rows."""
        model = _fitted_model()
        df = model.predict(n_periods=n_periods, start_date="2025-01-01", seed=42)
        assert len(df) == n_periods

    @pytest.mark.unit()
    @given(n_periods=st.integers(min_value=1, max_value=24))
    @settings(max_examples=200)
    def Test_predict_has_required_columns(self, n_periods: int) -> None:
        """predict() returns DataFrame containing all required columns."""
        model = _fitted_model()
        df = model.predict(n_periods=n_periods, start_date="2025-01-01", seed=42)
        for item_col in _PREDICT_COLS:
            assert item_col in df.columns

    @pytest.mark.unit()
    @given(n_periods=st.integers(min_value=1, max_value=24))
    @settings(max_examples=200)
    def Test_predict_mean_column_all_finite(self, n_periods: int) -> None:
        """All values in the Mean column are finite."""
        model = _fitted_model()
        df = model.predict(n_periods=n_periods, start_date="2025-01-01", seed=42)
        for item_val in df["Mean"].to_list():
            assert math.isfinite(item_val)
