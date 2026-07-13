"""Tests for Interest_Rate_Model_Standard (Vasicek short-rate model).

Covers construction, parameter validation, OLS fitting, Monte Carlo
prediction, analytical formula verification, and edge cases.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.interest_rate.model_interest_rate_base import Interest_Rate_Model_Status
from src.models.interest_rate.model_interest_rate_standard import (
    Interest_Rate_Model_Standard,
    _freq_to_dt_years,
    _simulate_ou_exact,
    _validate_positive_float,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def default_model() -> Interest_Rate_Model_Standard:
    """Return an unfitted standard model with default parameters."""
    return Interest_Rate_Model_Standard()


@pytest.fixture()
def small_model() -> Interest_Rate_Model_Standard:
    """Return a standard model with 100 simulations for faster tests."""
    return Interest_Rate_Model_Standard(n_simulations=100)


@pytest.fixture()
def annual_data() -> pl.DataFrame:
    """Return 10 years of annual short-rate data (reproducible)."""
    rng = np.random.default_rng(0)
    n = 10
    dates = [f"{y}-01-01" for y in range(2015, 2015 + n)]
    baseline = 0.04
    rates = baseline + 0.01 * rng.standard_normal(n)
    return pl.DataFrame({"Date": dates, "short_rate": rates.tolist()})


@pytest.fixture()
def monthly_data() -> pl.DataFrame:
    """Return 48 months of monthly short-rate data."""
    rng = np.random.default_rng(7)
    start = pl.date(2021, 1, 1)
    end = pl.date(2024, 12, 1)
    dates = pl.date_range(start=start, end=end, interval="1mo", eager=True)
    rates = 0.04 + 0.005 * rng.standard_normal(len(dates))
    return pl.DataFrame({"Date": dates, "short_rate": rates.tolist()})


@pytest.fixture()
def fitted_annual_model(annual_data: pl.DataFrame) -> Interest_Rate_Model_Standard:
    """Return standard model fitted to annual_data (100 simulations)."""
    m = Interest_Rate_Model_Standard(n_simulations=100)
    m.fit(data = annual_data)
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardConstruction:
    """Tests for Interest_Rate_Model_Standard constructor."""

    @pytest.mark.unit()
    def test_default_kappa_stored(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that default kappa stored."""
        assert default_model.m_kappa == pytest.approx(0.3, abs=1e-12)

    @pytest.mark.unit()
    def test_default_theta_stored(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that default theta stored."""
        assert default_model.m_theta == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_default_sigma_stored(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that default sigma stored."""
        assert default_model.m_sigma == pytest.approx(0.015, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_parameters_stored(self) -> None:
        """Test that custom parameters stored."""
        m = Interest_Rate_Model_Standard(kappa=1.0, theta=0.035, sigma=0.012)
        assert m.m_kappa == pytest.approx(1.0, abs=1e-12)
        assert m.m_theta == pytest.approx(0.035, abs=1e-12)
        assert m.m_sigma == pytest.approx(0.012, abs=1e-12)

    @pytest.mark.unit()
    def test_default_n_simulations(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that default n simulations."""
        assert default_model.m_n_simulations == 1000

    @pytest.mark.unit()
    def test_custom_n_simulations(self) -> None:
        """Test that custom n simulations."""
        m = Interest_Rate_Model_Standard(n_simulations=500)
        assert m.m_n_simulations == 500

    @pytest.mark.unit()
    def test_initial_current_rate_equals_theta(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that initial current rate equals theta."""
        assert default_model.m_current_rate == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_kappa_raises(self) -> None:
        """Test that zero kappa raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(kappa=0.0)

    @pytest.mark.unit()
    def test_negative_kappa_raises(self) -> None:
        """Test that negative kappa raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(kappa=-0.5)

    @pytest.mark.unit()
    def test_zero_sigma_raises(self) -> None:
        """Test that zero sigma raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(sigma=0.0)

    @pytest.mark.unit()
    def test_negative_sigma_raises(self) -> None:
        """Test that negative sigma raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(sigma=-0.01)

    @pytest.mark.unit()
    def test_zero_n_simulations_raises(self) -> None:
        """Test that zero n simulations raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(n_simulations=0)

    @pytest.mark.unit()
    def test_float_n_simulations_raises(self) -> None:
        """Test that float n simulations raises."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(n_simulations=100.0)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_status_not_fitted_initially(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that status not fitted initially."""
        assert default_model.status == Interest_Rate_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False


# =============================================================================
# Tests: fit
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardFit:
    """Tests for fit() against historical short-rate data."""

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        small_model.fit(data = annual_data)
        assert small_model.status == Interest_Rate_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = small_model.fit(data = annual_data)
        assert result is small_model

    @pytest.mark.unit()
    def test_fit_updates_current_rate(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit updates current rate."""
        small_model.fit(data = annual_data)
        last_rate = float(annual_data.sort("Date")["short_rate"][-1])
        assert small_model.m_current_rate == pytest.approx(last_rate, abs=1e-10)

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets parameters dict."""
        small_model.fit(data = annual_data)
        params = small_model.parameters
        assert "kappa" in params
        assert "theta" in params
        assert "sigma" in params
        assert "current_rate" in params

    @pytest.mark.unit()
    def test_fit_kappa_positive(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit kappa positive."""
        small_model.fit(data = annual_data)
        assert small_model.m_kappa > 0

    @pytest.mark.unit()
    def test_fit_sigma_positive(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
    ) -> None:
        """Test that fit sigma positive."""
        small_model.fit(data = annual_data)
        assert small_model.m_sigma > 0

    @pytest.mark.unit()
    def test_fit_monthly_data(
        self,
        small_model: Interest_Rate_Model_Standard,
        monthly_data: pl.DataFrame,
    ) -> None:
        """Test that fit monthly data."""
        small_model.fit(data = monthly_data)
        assert small_model.is_fitted
        assert small_model.m_kappa > 0
        assert small_model.m_sigma > 0

    @pytest.mark.unit()
    def test_fit_fewer_than_3_rows_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit fewer than 3 rows raises."""
        too_small = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2024-01-01"],
                "short_rate": [0.04, 0.05],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            small_model.fit(data = too_small)

    @pytest.mark.unit()
    def test_fit_missing_date_column_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit missing date column raises."""
        bad = pl.DataFrame(
            {"short_rate": [0.04, 0.05, 0.045, 0.053]},
        )
        with pytest.raises(Exception_Validation_Input):
            small_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_missing_rate_column_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit missing rate column raises."""
        bad = pl.DataFrame(
            {"Date": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"]},
        )
        with pytest.raises(Exception_Validation_Input):
            small_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_nan_values_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit nan values raises."""
        bad = pl.DataFrame(
            {
                "Date": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"],
                "short_rate": [0.04, float("nan"), 0.05, 0.045],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            small_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_non_dataframe_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit non dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            small_model.fit(data = [0.04, 0.05, 0.045])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sorts_by_date(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that fit sorts by date."""
        unsorted = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2021-01-01", "2022-01-01", "2023-01-01"],
                "short_rate": [0.045, 0.025, 0.030, 0.050],
            },
        )
        # Should not raise; order is handled internally
        small_model.fit(data = unsorted)
        assert small_model.is_fitted

    @pytest.mark.unit()
    def test_fit_exactly_3_rows_falls_back_to_prior_sigma(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """With exactly 3 data rows len(resid)==2 so sigma uses the constructor prior."""
        three_row_data = pl.DataFrame(
            {
                "Date": ["2022-01-01", "2023-01-01", "2024-01-01"],
                "short_rate": [0.06, 0.05, 0.04],
            },
        )
        prior_sigma = small_model.m_sigma
        small_model.fit(data = three_row_data)
        assert small_model.is_fitted
        assert small_model.m_sigma == prior_sigma

    @pytest.mark.unit()
    def test_fit_ols_non_finite_result_raises(
        self,
        small_model: Interest_Rate_Model_Standard,
        annual_data: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fit() raises when OLS produces a non-finite parameter (inf alpha → inf theta)."""
        import src.models.interest_rate.model_interest_rate_standard as ir_module

        monkeypatch.setattr(
            ir_module,
            "lstsq",
            lambda *args, **kwargs: (np.array([float("inf"), -0.1]), None, None, None),
        )
        with pytest.raises(Exception_Validation_Input), pytest.warns(RuntimeWarning):
            small_model.fit(data = annual_data)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardPredict:
    """Tests for the Monte Carlo predict() method."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_annual_model.predict(n_periods=12, seed=0)
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict correct length."""
        df = fitted_annual_model.predict(n_periods=24, seed=0)
        assert len(df) == 24

    @pytest.mark.unit()
    def test_predict_has_required_columns(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict has required columns."""
        df = fitted_annual_model.predict(n_periods=6, seed=0)
        required = {"Date", "Mean", "Median", "Std", "P5", "P25", "P75", "P95", "Min", "Max"}
        assert required.issubset(set(df.columns))

    @pytest.mark.unit()
    def test_predict_mean_finite(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict mean finite."""
        df = fitted_annual_model.predict(n_periods=12, seed=0)
        assert np.all(np.isfinite(df["Mean"].to_numpy()))

    @pytest.mark.unit()
    def test_predict_quantile_ordering(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict quantile ordering."""
        df = fitted_annual_model.predict(n_periods=12, seed=42)
        assert (df["P5"].to_numpy() <= df["P25"].to_numpy()).all()
        assert (df["P25"].to_numpy() <= df["Median"].to_numpy()).all()
        assert (df["Median"].to_numpy() <= df["P75"].to_numpy()).all()
        assert (df["P75"].to_numpy() <= df["P95"].to_numpy()).all()

    @pytest.mark.unit()
    def test_predict_min_le_max(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict min le max."""
        df = fitted_annual_model.predict(n_periods=12, seed=0)
        assert (df["Min"].to_numpy() <= df["Max"].to_numpy()).all()

    @pytest.mark.unit()
    def test_predict_reproducible_with_seed(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict reproducible with seed."""
        df1 = fitted_annual_model.predict(n_periods=12, seed=99)
        df2 = fitted_annual_model.predict(n_periods=12, seed=99)
        assert df1["Mean"].to_list() == df2["Mean"].to_list()

    @pytest.mark.unit()
    def test_predict_different_seeds_differ(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict different seeds differ."""
        df1 = fitted_annual_model.predict(n_periods=24, seed=1)
        df2 = fitted_annual_model.predict(n_periods=24, seed=2)
        assert df1["Mean"].to_list() != df2["Mean"].to_list()

    @pytest.mark.unit()
    def test_predict_before_fit_raises(
        self, small_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            small_model.predict(n_periods=6)

    @pytest.mark.unit()
    def test_predict_zero_periods_raises(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict zero periods raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.predict(n_periods=0)

    @pytest.mark.unit()
    def test_predict_invalid_freq_raises(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.predict(n_periods=6, freq="1w")

    @pytest.mark.unit()
    def test_predict_default_start_date(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict default start date."""
        df = fitted_annual_model.predict(n_periods=3, seed=0)
        first_date = str(df["Date"][0])
        assert first_date.startswith("2025")

    @pytest.mark.unit()
    def test_predict_custom_start_date(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict custom start date."""
        df = fitted_annual_model.predict(n_periods=3, start_date="2027-01-01", seed=0)
        first_date = str(df["Date"][0])
        assert first_date.startswith("2027")

    @pytest.mark.unit()
    def test_predict_std_positive(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that predict std positive."""
        # With sigma > 0 and multiple simulations, std should be > 0
        df = fitted_annual_model.predict(n_periods=12, seed=0)
        assert np.all(df["Std"].to_numpy() >= 0)
        # At least some steps should have positive std
        assert np.any(df["Std"].to_numpy() > 0)


# =============================================================================
# Tests: get_annual_rate
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardGetAnnualRate:
    """Tests for get_annual_rate()."""

    @pytest.mark.unit()
    def test_returns_theta_after_fit(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that returns theta after fit."""
        assert fitted_annual_model.get_annual_rate() == pytest.approx(
            fitted_annual_model.m_theta, abs=1e-12,
        )

    @pytest.mark.unit()
    def test_raises_before_fit(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_annual_rate()


# =============================================================================
# Tests: analytical formulae
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardAnalytical:
    """Tests for the closed-form analytical helpers."""

    @pytest.mark.unit()
    def test_analytical_mean_at_zero_equals_r0(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical mean at zero equals r0."""
        # At t -> 0+, mean should be close to r0
        r0 = 0.04
        mean_small_t = fitted_annual_model.get_analytical_mean(t_years=1e-6, r0=r0)
        assert mean_small_t == pytest.approx(r0, abs=1e-4)

    @pytest.mark.unit()
    def test_analytical_mean_converges_to_theta(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical mean converges to theta."""
        # As t -> inf, mean should converge to theta
        mean_long = fitted_annual_model.get_analytical_mean(t_years=100.0)
        assert mean_long == pytest.approx(fitted_annual_model.m_theta, abs=1e-4)

    @pytest.mark.unit()
    def test_analytical_variance_zero_at_t_zero(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical variance zero at t zero."""
        var = fitted_annual_model.get_analytical_variance(t_years=1e-6)
        assert var == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.unit()
    def test_analytical_variance_converges_to_stationary(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical variance converges to stationary."""
        # Stationary variance = sigma^2 / (2*kappa)
        stationary_var = (fitted_annual_model.m_sigma**2) / (2.0 * fitted_annual_model.m_kappa)
        var_long = fitted_annual_model.get_analytical_variance(t_years=100.0)
        assert var_long == pytest.approx(stationary_var, rel=1e-4)

    @pytest.mark.unit()
    def test_analytical_variance_positive(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical variance positive."""
        var = fitted_annual_model.get_analytical_variance(t_years=1.0)
        assert var > 0

    @pytest.mark.unit()
    def test_analytical_mean_before_fit_raises(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical mean before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.get_analytical_mean(t_years=1.0)

    @pytest.mark.unit()
    def test_analytical_variance_before_fit_raises(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical variance before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.get_analytical_variance(t_years=1.0)

    @pytest.mark.unit()
    def test_analytical_mean_zero_t_raises(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical mean zero t raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_mean(t_years=0.0)

    @pytest.mark.unit()
    def test_analytical_variance_negative_t_raises(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical variance negative t raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_variance(t_years=-1.0)

    @pytest.mark.unit()
    def test_analytical_mean_custom_r0(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that analytical mean custom r0."""
        # Starting at theta, mean stays at theta
        theta = fitted_annual_model.m_theta
        mean_t = fitted_annual_model.get_analytical_mean(t_years=5.0, r0=theta)
        assert mean_t == pytest.approx(theta, abs=1e-10)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that repr contains class name."""
        assert "Interest_Rate_Model_Standard" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_kappa(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that repr contains kappa."""
        assert "kappa" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_theta(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that repr contains theta."""
        assert "theta" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status(
        self, default_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_fitted_contains_fitted(
        self, fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Test that repr fitted contains fitted."""
        assert "Fitted" in repr(fitted_annual_model)


# =============================================================================
# Tests: private helpers
# =============================================================================


@pytest.mark.unit()
class TestInterestRateModelStandardHelpers:
    """Tests for private helper functions."""

    @pytest.mark.unit()
    def test_freq_to_dt_daily(self) -> None:
        """Test that freq to dt daily."""
        assert _freq_to_dt_years(freq = "1d") == pytest.approx(1.0 / 365.25, rel=1e-9)

    @pytest.mark.unit()
    def test_freq_to_dt_monthly(self) -> None:
        """Test that freq to dt monthly."""
        assert _freq_to_dt_years(freq = "1mo") == pytest.approx(1.0 / 12.0, rel=1e-9)

    @pytest.mark.unit()
    def test_freq_to_dt_annual(self) -> None:
        """Test that freq to dt annual."""
        assert _freq_to_dt_years(freq = "1y") == pytest.approx(1.0, rel=1e-9)

    @pytest.mark.unit()
    def test_freq_to_dt_invalid_raises(self) -> None:
        """Test that freq to dt invalid raises."""
        with pytest.raises(Exception_Validation_Input):
            _freq_to_dt_years(freq = "1w")

    @pytest.mark.unit()
    def test_validate_positive_float_valid(self) -> None:
        """Test that validate positive float valid."""
        _validate_positive_float(value = 0.5, name = "test_param")  # Should not raise

    @pytest.mark.unit()
    def test_validate_positive_float_zero_raises(self) -> None:
        """Test that validate positive float zero raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = 0.0, name = "test_param")

    @pytest.mark.unit()
    def test_validate_positive_float_negative_raises(self) -> None:
        """Test that validate positive float negative raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = -1.0, name = "test_param")

    @pytest.mark.unit()
    def test_validate_positive_float_nan_raises(self) -> None:
        """Test that validate positive float nan raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("nan"), name = "test_param")

    @pytest.mark.unit()
    def test_validate_positive_float_bool_raises(self) -> None:
        """Test that validate positive float rejects boolean values."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = True, name = "test_param")

    @pytest.mark.unit()
    def test_simulate_ou_exact_shape(self) -> None:
        """Test that simulate ou exact shape."""
        rng = np.random.default_rng(42)
        paths = _simulate_ou_exact(
            kappa=0.3,
            theta=0.04,
            sigma=0.015,
            r0=0.04,
            n_steps=12,
            n_paths=50,
            dt=1.0 / 12.0,
            rng=rng,
        )
        assert paths.shape == (12, 50)

    @pytest.mark.unit()
    def test_simulate_ou_exact_finite_values(self) -> None:
        """Test that simulate ou exact finite values."""
        rng = np.random.default_rng(0)
        paths = _simulate_ou_exact(
            kappa=0.3,
            theta=0.04,
            sigma=0.015,
            r0=0.04,
            n_steps=24,
            n_paths=100,
            dt=1.0 / 12.0,
            rng=rng,
        )
        assert np.all(np.isfinite(paths))

    @pytest.mark.unit()
    def test_simulate_ou_exact_mean_converges_to_theta(self) -> None:
        """Test that simulate ou exact mean converges to theta."""
        # With high kappa and many paths, long-horizon mean should be near theta
        rng = np.random.default_rng(42)
        theta = 0.04
        paths = _simulate_ou_exact(
            kappa=2.0,
            theta=theta,
            sigma=0.01,
            r0=0.04,
            n_steps=120,
            n_paths=10_000,
            dt=1.0 / 12.0,
            rng=rng,
        )
        # Check the final step mean converges to theta
        final_mean = float(np.mean(paths[-1]))
        assert final_mean == pytest.approx(theta, abs=0.005)


# =============================================================================
# Tests: missing branch coverage
# =============================================================================


class Class_Test_Interest_Rate_Standard_Coverage_Gaps:
    """Targeted tests to close remaining branch gaps in the OU short-rate model."""

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Bool_Theta(self) -> None:
        """Constructor should reject boolean theta values."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(theta=True)

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Bool_N_Simulations(self) -> None:
        """Constructor should reject boolean n_simulations values."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(n_simulations=False)

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Non_Finite_Theta(self) -> None:
        """Constructor should reject a non-finite theta."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(theta=float("nan"))

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Inf_Theta(self) -> None:
        """Constructor should reject infinite theta."""
        with pytest.raises(Exception_Validation_Input):
            Interest_Rate_Model_Standard(theta=float("inf"))

    @pytest.mark.unit()
    def Test_Fit_Raises_When_Dates_Have_Zero_Gap(self) -> None:
        """fit() should raise when dates have zero gap (duplicate dates → dt ≤ 0)."""
        dup_data = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01", "2023-01-01", "2023-01-01"],
                "short_rate": [0.04, 0.041, 0.039, 0.040],
            }
        )
        m = Interest_Rate_Model_Standard(n_simulations=10)
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = dup_data)

    @pytest.mark.unit()
    def Test_Analytical_Mean_Raises_For_Bool_T_Years(
        self,
        fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Analytical mean should reject boolean t_years values."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_mean(t_years=True)

    @pytest.mark.unit()
    def Test_Analytical_Variance_Raises_For_Bool_T_Years(
        self,
        fitted_annual_model: Interest_Rate_Model_Standard,
    ) -> None:
        """Analytical variance should reject boolean t_years values."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_variance(t_years=False)

    @pytest.mark.unit()
    def Test_Fit_Uses_Constructor_Priors_When_Beta_Ols_Non_Negative(self) -> None:
        """When OLS beta >= 0 the model should fall back to constructor kappa/theta."""
        import datetime as dt

        dates = [dt.date(2018, 1, 1) + dt.timedelta(days=365 * i) for i in range(8)]
        # Monotone increasing rates → OLS slope beta >= 0 → non-mean-reverting
        rates = [0.01 + 0.005 * i for i in range(8)]
        data = pl.DataFrame({"Date": dates, "short_rate": rates})
        m = Interest_Rate_Model_Standard(kappa=0.5, theta=0.04, n_simulations=10)
        m.fit(data = data)
        assert m.m_kappa == pytest.approx(0.5, abs=1e-9)

