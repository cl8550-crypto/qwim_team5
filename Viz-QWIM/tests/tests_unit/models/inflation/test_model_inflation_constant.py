"""Tests for Inflation_Model_Constant (constant-rate inflation model).

Covers construction, fit() with and without historical data, predict(),
get_annual_rate(), and edge-case validation.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.inflation.model_inflation_base import Inflation_Model_Status
from src.models.inflation.model_inflation_constant import (
    Inflation_Model_Constant,
    _make_date_range,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def default_model() -> Inflation_Model_Constant:
    """Return an unfitted constant model with default rate (2.5 %)."""
    return Inflation_Model_Constant()


@pytest.fixture()
def fitted_default_model() -> Inflation_Model_Constant:
    """Return a constant model fitted without historical data."""
    m = Inflation_Model_Constant()
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def historical_data() -> pl.DataFrame:
    """Return five years of annual inflation data."""
    return pl.DataFrame(
        {
            "Date": [
                "2020-01-01",
                "2021-01-01",
                "2022-01-01",
                "2023-01-01",
                "2024-01-01",
            ],
            "inflation_rate": [0.023, 0.047, 0.080, 0.034, 0.032],
        }
    )


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantConstruction:
    """Tests for Inflation_Model_Constant constructor."""

    @pytest.mark.unit()
    def test_default_rate_stored(self, default_model: Inflation_Model_Constant) -> None:
        """Test that default rate stored."""
        assert default_model.m_annual_rate == pytest.approx(0.025, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_rate_stored(self) -> None:
        """Test that custom rate stored."""
        m = Inflation_Model_Constant(annual_rate=0.04)
        assert m.m_annual_rate == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_rate_accepted(self) -> None:
        """Test that zero rate accepted."""
        m = Inflation_Model_Constant(annual_rate=0.0)
        assert m.m_annual_rate == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_negative_rate_within_bounds_accepted(self) -> None:
        """Test that negative rate within bounds accepted."""
        m = Inflation_Model_Constant(annual_rate=-0.01)
        assert m.m_annual_rate == pytest.approx(-0.01, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_at_maximum_boundary_accepted(self) -> None:
        """Test that rate at maximum boundary accepted."""
        m = Inflation_Model_Constant(annual_rate=1.0)
        assert m.m_annual_rate == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_below_lower_bound_raises(self) -> None:
        """Test that rate below lower bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=-0.6)

    @pytest.mark.unit()
    def test_rate_above_upper_bound_raises(self) -> None:
        """Test that rate above upper bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=1.5)

    @pytest.mark.unit()
    def test_nan_rate_raises(self) -> None:
        """Test that nan rate raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=float("nan"))

    @pytest.mark.unit()
    def test_inf_rate_raises(self) -> None:
        """Test that inf rate raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=float("inf"))

    @pytest.mark.unit()
    def Test_Reject_Bool_Rate(self) -> None:
        """Test that reject bool rate."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_default_status_not_fitted(self, default_model: Inflation_Model_Constant) -> None:
        """Test that default status not fitted."""
        assert default_model.status == Inflation_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Inflation_Model_Constant) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Inflation_Model_Constant(name_model="My CPI Model")
        assert m.name_model == "My CPI Model"


# =============================================================================
# Tests: fit — no historical data
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantFitNoData:
    """Tests for fit() when called with an empty DataFrame."""

    @pytest.mark.unit()
    def test_fit_empty_data_returns_self(self, default_model: Inflation_Model_Constant) -> None:
        """Test that fit empty data returns self."""
        result = default_model.fit(data = pl.DataFrame())
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_empty_data_sets_fitted(self, default_model: Inflation_Model_Constant) -> None:
        """Test that fit empty data sets fitted."""
        default_model.fit(data = pl.DataFrame())
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_empty_data_preserves_rate(self, default_model: Inflation_Model_Constant) -> None:
        """Test that fit empty data preserves rate."""
        original_rate = default_model.m_annual_rate
        default_model.fit(data = pl.DataFrame())
        assert default_model.m_annual_rate == pytest.approx(original_rate, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_invalid_type_raises(self, default_model: Inflation_Model_Constant) -> None:
        """Test that fit invalid type raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = {"Date": [], "inflation_rate": []})  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that fit sets parameters dict."""
        assert "annual_rate" in fitted_default_model.parameters
        assert fitted_default_model.parameters["annual_rate"] == pytest.approx(0.025, abs=1e-12)


# =============================================================================
# Tests: fit — with historical data
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantFitWithData:
    """Tests for fit() with historical inflation data."""

    @pytest.mark.unit()
    def test_fit_estimates_mean(self, historical_data: pl.DataFrame) -> None:
        """Test that fit estimates mean."""
        m = Inflation_Model_Constant()
        m.fit(data = historical_data)
        expected_mean = np.mean([0.023, 0.047, 0.080, 0.034, 0.032])
        assert m.m_annual_rate == pytest.approx(expected_mean, abs=1e-10)

    @pytest.mark.unit()
    def test_fit_returns_self(self, historical_data: pl.DataFrame) -> None:
        """Test that fit returns self."""
        m = Inflation_Model_Constant()
        result = m.fit(data = historical_data)
        assert result is m

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(self, historical_data: pl.DataFrame) -> None:
        """Test that fit sets fitted status."""
        m = Inflation_Model_Constant()
        m.fit(data = historical_data)
        assert m.is_fitted is True

    @pytest.mark.unit()
    def test_fit_missing_date_column_raises(self) -> None:
        """Test that fit missing date column raises."""
        m = Inflation_Model_Constant()
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = pl.DataFrame({"inflation_rate": [0.02, 0.03]}))

    @pytest.mark.unit()
    def test_fit_missing_rate_column_raises(self) -> None:
        """Test that fit missing rate column raises."""
        m = Inflation_Model_Constant()
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = pl.DataFrame({"Date": ["2024-01-01", "2025-01-01"]}))

    @pytest.mark.unit()
    def test_fit_nan_values_raises(self) -> None:
        """Test that fit nan values raises."""
        m = Inflation_Model_Constant()
        data = pl.DataFrame(
            {"Date": ["2024-01-01", "2025-01-01"], "inflation_rate": [0.02, float("nan")]}
        )
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = data)

    @pytest.mark.unit()
    def test_fit_single_observation(self) -> None:
        """Test that fit single observation."""
        m = Inflation_Model_Constant()
        data = pl.DataFrame({"Date": ["2024-01-01"], "inflation_rate": [0.035]})
        m.fit(data = data)
        assert m.m_annual_rate == pytest.approx(0.035, abs=1e-12)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantPredict:
    """Tests for predict() output shape, types, and values."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict returns dataframe."""
        result = fitted_default_model.predict(n_periods=6)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict correct length."""
        for n in [1, 6, 12, 24]:
            result = fitted_default_model.predict(n_periods=n)
            assert len(result) == n, f"Expected {n} rows, got {len(result)}"

    @pytest.mark.unit()
    def test_predict_has_date_column(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict has date column."""
        result = fitted_default_model.predict(n_periods=3)
        assert "Date" in result.columns

    @pytest.mark.unit()
    def test_predict_has_inflation_rate_column(
        self, fitted_default_model: Inflation_Model_Constant
    ) -> None:
        """Test that predict has inflation rate column."""
        result = fitted_default_model.predict(n_periods=3)
        assert "inflation_rate" in result.columns

    @pytest.mark.unit()
    def test_predict_constant_values(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict constant values."""
        result = fitted_default_model.predict(n_periods=12)
        rates = result["inflation_rate"].to_list()
        assert all(r == pytest.approx(0.025, abs=1e-12) for r in rates)

    @pytest.mark.unit()
    def test_predict_with_custom_rate(self) -> None:
        """Test that predict with custom rate."""
        m = Inflation_Model_Constant(annual_rate=0.04)
        m.fit(data = pl.DataFrame())
        result = m.predict(n_periods=6)
        rates = result["inflation_rate"].to_list()
        assert all(r == pytest.approx(0.04, abs=1e-12) for r in rates)

    @pytest.mark.unit()
    def test_predict_monthly_freq(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict monthly freq."""
        result = fitted_default_model.predict(n_periods=6, freq="1mo")
        assert len(result) == 6

    @pytest.mark.unit()
    def test_predict_daily_freq(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict daily freq."""
        result = fitted_default_model.predict(n_periods=30, freq="1d")
        assert len(result) == 30

    @pytest.mark.unit()
    def test_predict_annual_freq(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict annual freq."""
        result = fitted_default_model.predict(n_periods=5, freq="1y")
        assert len(result) == 5

    @pytest.mark.unit()
    def test_predict_default_start_date(
        self, fitted_default_model: Inflation_Model_Constant
    ) -> None:
        """Test that predict default start date."""
        result = fitted_default_model.predict(n_periods=3)
        first_date = str(result["Date"][0])
        assert first_date == "2025-01-01"

    @pytest.mark.unit()
    def test_predict_custom_start_date(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that predict custom start date."""
        result = fitted_default_model.predict(n_periods=3, start_date="2030-06-01")
        first_date = str(result["Date"][0])
        assert first_date == "2030-06-01"

    @pytest.mark.unit()
    def test_predict_before_fit_raises(self, default_model: Inflation_Model_Constant) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(n_periods=5)

    @pytest.mark.unit()
    def test_predict_zero_periods_raises(
        self, fitted_default_model: Inflation_Model_Constant
    ) -> None:
        """Test that predict zero periods raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_periods=0)

    @pytest.mark.unit()
    def test_predict_invalid_freq_raises(
        self, fitted_default_model: Inflation_Model_Constant
    ) -> None:
        """Test that predict invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_periods=5, freq="1w")


# =============================================================================
# Tests: get_annual_rate
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantGetAnnualRate:
    """Tests for get_annual_rate()."""

    @pytest.mark.unit()
    def test_returns_correct_rate_after_fit(
        self, fitted_default_model: Inflation_Model_Constant
    ) -> None:
        """Test that returns correct rate after fit."""
        rate = fitted_default_model.get_annual_rate()
        assert rate == pytest.approx(0.025, abs=1e-12)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Inflation_Model_Constant) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_annual_rate()

    @pytest.mark.unit()
    def test_returns_estimated_rate_after_fit_with_data(
        self, historical_data: pl.DataFrame
    ) -> None:
        """Test that returns estimated rate after fit with data."""
        m = Inflation_Model_Constant()
        m.fit(data = historical_data)
        expected_mean = np.mean([0.023, 0.047, 0.080, 0.034, 0.032])
        assert m.get_annual_rate() == pytest.approx(expected_mean, abs=1e-10)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit
class TestInflationModelConstantRepr:
    """Tests for __repr__."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(self, default_model: Inflation_Model_Constant) -> None:
        """Test that repr contains class name."""
        assert "Inflation_Model_Constant" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_rate(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that repr contains rate."""
        r = repr(fitted_default_model)
        assert "0.025000" in r

    @pytest.mark.unit()
    def test_repr_contains_status(self, fitted_default_model: Inflation_Model_Constant) -> None:
        """Test that repr contains status."""
        r = repr(fitted_default_model)
        assert "Fitted" in r


# =============================================================================
# Tests: _make_date_range helper
# =============================================================================


@pytest.mark.unit
class TestMakeDateRange:
    """Tests for the private _make_date_range helper."""

    @pytest.mark.unit()
    def test_monthly_correct_length(self) -> None:
        """Test that monthly correct length."""
        series = _make_date_range(start_date = "2025-01-01", n_periods = 12, freq = "1mo")
        assert len(series) == 12

    @pytest.mark.unit()
    def test_daily_correct_length(self) -> None:
        """Test that daily correct length."""
        series = _make_date_range(start_date = "2025-01-01", n_periods = 30, freq = "1d")
        assert len(series) == 30

    @pytest.mark.unit()
    def test_annual_correct_length(self) -> None:
        """Test that annual correct length."""
        series = _make_date_range(start_date = "2025-01-01", n_periods = 5, freq = "1y")
        assert len(series) == 5

    @pytest.mark.unit()
    def test_monthly_starts_on_start_date(self) -> None:
        """Test that monthly starts on start date."""
        series = _make_date_range(start_date = "2025-06-01", n_periods = 3, freq = "1mo")
        assert str(series[0]) == "2025-06-01"

    @pytest.mark.unit()
    def test_invalid_freq_raises(self) -> None:
        """Test that invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            _make_date_range(start_date = "2025-01-01", n_periods = 5, freq = "1w")
