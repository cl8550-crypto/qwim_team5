"""Tests for Interest_Rate_Model_Constant (constant short-rate model).

Covers construction, fit() with and without historical data, predict(),
get_annual_rate(), and the _make_date_range helper.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.interest_rate.model_interest_rate_base import Interest_Rate_Model_Status
from src.models.interest_rate.model_interest_rate_constant import (
    Interest_Rate_Model_Constant,
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
def default_model() -> Interest_Rate_Model_Constant:
    """Return an unfitted constant model with default rate (4 %)."""
    return Interest_Rate_Model_Constant()


@pytest.fixture()
def fitted_default_model() -> Interest_Rate_Model_Constant:
    """Return a constant model fitted without historical data."""
    m = Interest_Rate_Model_Constant()
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def historical_data() -> pl.DataFrame:
    """Return four years of annual short-rate data."""
    return pl.DataFrame(
        {
            "Date": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"],
            "short_rate": [0.025, 0.050, 0.053, 0.045],
        },
    )


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantConstruction:
    """Tests for Interest_Rate_Model_Constant constructor."""

    @pytest.mark.unit()
    def test_default_rate_stored(self, default_model: Interest_Rate_Model_Constant) -> None:
        """Test that default rate stored."""
        assert default_model.m_annual_rate == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_rate_stored(self) -> None:
        """Test that custom rate stored."""
        m = Interest_Rate_Model_Constant(annual_rate=0.05)
        assert m.m_annual_rate == pytest.approx(0.05, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_rate_accepted(self) -> None:
        """Test that zero rate accepted."""
        m = Interest_Rate_Model_Constant(annual_rate=0.0)
        assert m.m_annual_rate == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_negative_rate_within_bounds_accepted(self) -> None:
        """Test that negative rate within bounds accepted."""
        m = Interest_Rate_Model_Constant(annual_rate=-0.005)
        assert m.m_annual_rate == pytest.approx(-0.005, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_at_maximum_boundary_accepted(self) -> None:
        """Test that rate at maximum boundary accepted."""
        m = Interest_Rate_Model_Constant(annual_rate=0.50)
        assert m.m_annual_rate == pytest.approx(0.50, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_below_lower_bound_raises(self) -> None:
        """Test that rate below lower bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Constant(annual_rate=-0.20)

    @pytest.mark.unit()
    def test_rate_above_upper_bound_raises(self) -> None:
        """Test that rate above upper bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Constant(annual_rate=0.60)

    @pytest.mark.unit()
    def test_nan_rate_raises(self) -> None:
        """Test that nan rate raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Constant(annual_rate=float("nan"))

    @pytest.mark.unit()
    def test_inf_rate_raises(self) -> None:
        """Test that inf rate raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Constant(annual_rate=float("inf"))

    @pytest.mark.unit()
    def test_default_status_not_fitted(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that default status not fitted."""
        assert default_model.status == Interest_Rate_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Interest_Rate_Model_Constant(name_model="Fed Funds Model")
        assert m.name_model == "Fed Funds Model"


# =============================================================================
# Tests: fit — no historical data
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantFitNoData:
    """Tests for fit() with empty DataFrame."""

    @pytest.mark.unit()
    def test_fit_empty_data_returns_self(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit empty data returns self."""
        result = default_model.fit(data = pl.DataFrame())
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_empty_data_sets_fitted(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit empty data sets fitted."""
        default_model.fit(data = pl.DataFrame())
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_empty_data_preserves_rate(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit empty data preserves rate."""
        original_rate = default_model.m_annual_rate
        default_model.fit(data = pl.DataFrame())
        assert default_model.m_annual_rate == pytest.approx(original_rate, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_invalid_type_raises(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit invalid type raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = [0.04, 0.05])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit sets parameters dict."""
        params = fitted_default_model.parameters
        assert "annual_rate" in params
        assert params["annual_rate"] == pytest.approx(0.04, abs=1e-12)


# =============================================================================
# Tests: fit — with historical data
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantFitWithData:
    """Tests for fit() with a historical short-rate DataFrame."""

    @pytest.mark.unit()
    def test_fit_estimates_mean(
        self,
        default_model: Interest_Rate_Model_Constant,
        historical_data: pl.DataFrame,
    ) -> None:
        """Test that fit estimates mean."""
        default_model.fit(data = historical_data)
        expected_mean = float(np.mean([0.025, 0.050, 0.053, 0.045]))
        assert default_model.m_annual_rate == pytest.approx(expected_mean, abs=1e-10)

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        default_model: Interest_Rate_Model_Constant,
        historical_data: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = default_model.fit(data = historical_data)
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        default_model: Interest_Rate_Model_Constant,
        historical_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        default_model.fit(data = historical_data)
        assert default_model.status == Interest_Rate_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_missing_date_column_raises(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit missing date column raises."""
        bad_data = pl.DataFrame({"short_rate": [0.04, 0.05]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_missing_rate_column_raises(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit missing rate column raises."""
        bad_data = pl.DataFrame({"Date": ["2024-01-01", "2025-01-01"]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_nan_values_raises(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit nan values raises."""
        bad_data = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2025-01-01"],
                "short_rate": [0.04, float("nan")],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_single_observation(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that fit single observation."""
        single = pl.DataFrame({"Date": ["2024-01-01"], "short_rate": [0.05]})
        default_model.fit(data = single)
        assert default_model.m_annual_rate == pytest.approx(0.05, abs=1e-10)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantPredict:
    """Tests for the predict() method."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_default_model.predict(n_periods=6)
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict correct length."""
        df = fitted_default_model.predict(n_periods=12)
        assert len(df) == 12

    @pytest.mark.unit()
    def test_predict_has_date_column(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict has date column."""
        df = fitted_default_model.predict(n_periods=3)
        assert "Date" in df.columns

    @pytest.mark.unit()
    def test_predict_has_short_rate_column(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict has short rate column."""
        df = fitted_default_model.predict(n_periods=3)
        assert "short_rate" in df.columns

    @pytest.mark.unit()
    def test_predict_constant_values(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict constant values."""
        df = fitted_default_model.predict(n_periods=5)
        rates = df["short_rate"].to_list()
        assert all(r == pytest.approx(0.04, abs=1e-12) for r in rates)

    @pytest.mark.unit()
    def test_predict_with_custom_rate(self) -> None:
        """Test that predict with custom rate."""
        m = Interest_Rate_Model_Constant(annual_rate=0.06)
        m.fit(data = pl.DataFrame())
        df = m.predict(n_periods=4)
        assert all(r == pytest.approx(0.06, abs=1e-12) for r in df["short_rate"].to_list())

    @pytest.mark.unit()
    def test_predict_monthly_freq(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict monthly freq."""
        df = fitted_default_model.predict(n_periods=12, freq="1mo")
        assert len(df) == 12

    @pytest.mark.unit()
    def test_predict_daily_freq(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict daily freq."""
        df = fitted_default_model.predict(n_periods=30, freq="1d")
        assert len(df) == 30

    @pytest.mark.unit()
    def test_predict_annual_freq(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict annual freq."""
        df = fitted_default_model.predict(n_periods=5, freq="1y")
        assert len(df) == 5

    @pytest.mark.unit()
    def test_predict_default_start_date(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict default start date."""
        df = fitted_default_model.predict(n_periods=3)
        # Default start date is 2025-01-01
        first_date = str(df["Date"][0])
        assert first_date.startswith("2025")

    @pytest.mark.unit()
    def test_predict_custom_start_date(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict custom start date."""
        df = fitted_default_model.predict(n_periods=3, start_date="2026-01-01")
        first_date = str(df["Date"][0])
        assert first_date.startswith("2026")

    @pytest.mark.unit()
    def test_predict_before_fit_raises(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(n_periods=6)

    @pytest.mark.unit()
    def test_predict_zero_periods_raises(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict zero periods raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_periods=0)

    @pytest.mark.unit()
    def test_predict_invalid_freq_raises(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that predict invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_periods=6, freq="1w")


# =============================================================================
# Tests: get_annual_rate
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantGetAnnualRate:
    """Tests for get_annual_rate()."""

    @pytest.mark.unit()
    def test_returns_correct_rate_after_fit(
        self, fitted_default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that returns correct rate after fit."""
        assert fitted_default_model.get_annual_rate() == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_raises_before_fit(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_annual_rate()

    @pytest.mark.unit()
    def test_returns_estimated_rate_after_fit_with_data(
        self,
        default_model: Interest_Rate_Model_Constant,
        historical_data: pl.DataFrame,
    ) -> None:
        """Test that returns estimated rate after fit with data."""
        default_model.fit(data = historical_data)
        expected = float(np.mean([0.025, 0.050, 0.053, 0.045]))
        assert default_model.get_annual_rate() == pytest.approx(expected, abs=1e-10)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelConstantRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that repr contains class name."""
        assert "Interest_Rate_Model_Constant" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_rate(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that repr contains rate."""
        assert "0.040000" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status(
        self, default_model: Interest_Rate_Model_Constant,
    ) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)


# =============================================================================
# Tests: _make_date_range helper
# =============================================================================


@pytest.mark.unit()
class TestMakeDateRange:
    """Tests for the private _make_date_range helper."""

    @pytest.mark.unit()
    def test_monthly_correct_length(self) -> None:
        """Test that monthly correct length."""
        result = _make_date_range(start_date = "2025-01-01", n_periods = 12, freq = "1mo")
        assert len(result) == 12

    @pytest.mark.unit()
    def test_daily_correct_length(self) -> None:
        """Test that daily correct length."""
        result = _make_date_range(start_date = "2025-01-01", n_periods = 30, freq = "1d")
        assert len(result) == 30

    @pytest.mark.unit()
    def test_annual_correct_length(self) -> None:
        """Test that annual correct length."""
        result = _make_date_range(start_date = "2025-01-01", n_periods = 5, freq = "1y")
        assert len(result) == 5

    @pytest.mark.unit()
    def test_monthly_starts_on_start_date(self) -> None:
        """Test that monthly starts on start date."""
        result = _make_date_range(start_date = "2025-03-01", n_periods = 6, freq = "1mo")
        assert str(result[0]) == "2025-03-01"

    @pytest.mark.unit()
    def test_invalid_freq_raises(self) -> None:
        """Test that invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            _make_date_range(start_date = "2025-01-01", n_periods = 6, freq = "1w")
