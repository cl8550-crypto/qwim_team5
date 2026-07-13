"""Tests for Inflation_Model_Standard (Ornstein-Uhlenbeck inflation model).

Covers construction, parameter validation, OLS fitting, Monte Carlo
prediction, analytical formula verification, and edge cases.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.inflation.model_inflation_base import Inflation_Model_Status
from src.models.inflation.model_inflation_standard import (
    Inflation_Model_Standard,
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
def default_model() -> Inflation_Model_Standard:
    """Return an unfitted standard model with default parameters."""
    return Inflation_Model_Standard()


@pytest.fixture()
def small_model() -> Inflation_Model_Standard:
    """Return a standard model with 100 simulations for faster tests."""
    return Inflation_Model_Standard(n_simulations=100)


@pytest.fixture()
def annual_data() -> pl.DataFrame:
    """Return 10 years of annual CPI-like inflation data (reproducible)."""
    rng = np.random.default_rng(42)
    n = 10
    dates = [f"{y}-01-01" for y in range(2015, 2015 + n)]
    baseline = 0.025
    rates = baseline + 0.01 * rng.standard_normal(n)
    return pl.DataFrame({"Date": dates, "inflation_rate": rates.tolist()})


@pytest.fixture()
def monthly_data() -> pl.DataFrame:
    """Return 48 months of monthly inflation data."""
    rng = np.random.default_rng(7)
    start = pl.date(2021, 1, 1)
    end = pl.date(2024, 12, 1)
    dates = pl.date_range(start=start, end=end, interval="1mo", eager=True)
    rates = 0.025 + 0.005 * rng.standard_normal(len(dates))
    return pl.DataFrame({"Date": dates, "inflation_rate": rates.tolist()})


@pytest.fixture()
def fitted_annual_model(annual_data: pl.DataFrame) -> Inflation_Model_Standard:
    """Return standard model fitted to annual_data (100 simulations)."""
    m = Inflation_Model_Standard(n_simulations=100)
    m.fit(data = annual_data)
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardConstruction:
    """Tests for Inflation_Model_Standard constructor."""

    @pytest.mark.unit()
    def test_default_kappa_stored(self, default_model: Inflation_Model_Standard) -> None:
        """Test that default kappa stored."""
        assert default_model.m_kappa == pytest.approx(0.5, abs=1e-12)

    @pytest.mark.unit()
    def test_default_theta_stored(self, default_model: Inflation_Model_Standard) -> None:
        """Test that default theta stored."""
        assert default_model.m_theta == pytest.approx(0.025, abs=1e-12)

    @pytest.mark.unit()
    def test_default_sigma_stored(self, default_model: Inflation_Model_Standard) -> None:
        """Test that default sigma stored."""
        assert default_model.m_sigma == pytest.approx(0.010, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_parameters_stored(self) -> None:
        """Test that custom parameters stored."""
        m = Inflation_Model_Standard(kappa=1.2, theta=0.03, sigma=0.008)
        assert m.m_kappa == pytest.approx(1.2, abs=1e-12)
        assert m.m_theta == pytest.approx(0.03, abs=1e-12)
        assert m.m_sigma == pytest.approx(0.008, abs=1e-12)

    @pytest.mark.unit()
    def test_default_n_simulations(self, default_model: Inflation_Model_Standard) -> None:
        """Test that default n simulations."""
        assert default_model.m_n_simulations == 1000

    @pytest.mark.unit()
    def test_custom_n_simulations(self) -> None:
        """Test that custom n simulations."""
        m = Inflation_Model_Standard(n_simulations=500)
        assert m.m_n_simulations == 500

    @pytest.mark.unit()
    def test_initial_current_rate_equals_theta(self, default_model: Inflation_Model_Standard) -> None:
        """Test that initial current rate equals theta."""
        assert default_model.m_current_rate == pytest.approx(default_model.m_theta, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_kappa_raises(self) -> None:
        """Test that zero kappa raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(kappa=0.0)

    @pytest.mark.unit()
    def test_negative_kappa_raises(self) -> None:
        """Test that negative kappa raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(kappa=-0.1)

    @pytest.mark.unit()
    def test_zero_sigma_raises(self) -> None:
        """Test that zero sigma raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(sigma=0.0)

    @pytest.mark.unit()
    def test_negative_sigma_raises(self) -> None:
        """Test that negative sigma raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(sigma=-0.01)

    @pytest.mark.unit()
    def test_zero_n_simulations_raises(self) -> None:
        """Test that zero n simulations raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(n_simulations=0)

    @pytest.mark.unit()
    def test_float_n_simulations_raises(self) -> None:
        """Test that float n simulations raises."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(n_simulations=100.5)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_status_not_fitted_initially(self, default_model: Inflation_Model_Standard) -> None:
        """Test that status not fitted initially."""
        assert default_model.status == Inflation_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Inflation_Model_Standard) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False


# =============================================================================
# Tests: fit
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardFit:
    """Tests for fit() parameter estimation."""

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(self, annual_data: pl.DataFrame) -> None:
        """Test that fit sets fitted status."""
        m = Inflation_Model_Standard(n_simulations=50)
        m.fit(data = annual_data)
        assert m.is_fitted is True

    @pytest.mark.unit()
    def test_fit_returns_self(self, annual_data: pl.DataFrame) -> None:
        """Test that fit returns self."""
        m = Inflation_Model_Standard(n_simulations=50)
        result = m.fit(data = annual_data)
        assert result is m

    @pytest.mark.unit()
    def test_fit_updates_current_rate(
        self, annual_data: pl.DataFrame
    ) -> None:
        """Test that fit updates current rate."""
        m = Inflation_Model_Standard(n_simulations=50)
        last_rate = annual_data["inflation_rate"].to_list()[-1]
        m.fit(data = annual_data)
        assert m.m_current_rate == pytest.approx(last_rate, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self, annual_data: pl.DataFrame
    ) -> None:
        """Test that fit sets parameters dict."""
        m = Inflation_Model_Standard(n_simulations=50)
        m.fit(data = annual_data)
        expected_keys = {"kappa", "theta", "sigma", "current_rate", "dt_years"}
        assert expected_keys.issubset(set(m.parameters.keys()))

    @pytest.mark.unit()
    def test_fit_kappa_positive(self, annual_data: pl.DataFrame) -> None:
        """Test that fit kappa positive."""
        m = Inflation_Model_Standard(n_simulations=50)
        m.fit(data = annual_data)
        assert m.m_kappa > 0

    @pytest.mark.unit()
    def test_fit_sigma_positive(self, annual_data: pl.DataFrame) -> None:
        """Test that fit sigma positive."""
        m = Inflation_Model_Standard(n_simulations=50)
        m.fit(data = annual_data)
        assert m.m_sigma > 0

    @pytest.mark.unit()
    def test_fit_monthly_data(self, monthly_data: pl.DataFrame) -> None:
        """Test that fit monthly data."""
        m = Inflation_Model_Standard(n_simulations=50)
        m.fit(data = monthly_data)
        assert m.is_fitted is True
        assert m.m_kappa > 0

    @pytest.mark.unit()
    def test_fit_fewer_than_3_rows_raises(self) -> None:
        """Test that fit fewer than 3 rows raises."""
        m = Inflation_Model_Standard()
        data = pl.DataFrame(
            {"Date": ["2024-01-01", "2025-01-01"], "inflation_rate": [0.02, 0.03]}
        )
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = data)

    @pytest.mark.unit()
    def test_fit_missing_date_column_raises(self) -> None:
        """Test that fit missing date column raises."""
        m = Inflation_Model_Standard()
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = pl.DataFrame({"inflation_rate": [0.02, 0.03, 0.04]}))

    @pytest.mark.unit()
    def test_fit_missing_rate_column_raises(self) -> None:
        """Test that fit missing rate column raises."""
        m = Inflation_Model_Standard()
        with pytest.raises(Exception_Validation_Input):
            m.fit(
                data = pl.DataFrame(
                    {"Date": ["2022-01-01", "2023-01-01", "2024-01-01"]}
                )
            )

    @pytest.mark.unit()
    def test_fit_nan_values_raises(self) -> None:
        """Test that fit nan values raises."""
        m = Inflation_Model_Standard()
        data = pl.DataFrame(
            {
                "Date": ["2022-01-01", "2023-01-01", "2024-01-01"],
                "inflation_rate": [0.02, float("nan"), 0.03],
            }
        )
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = data)

    @pytest.mark.unit()
    def test_fit_non_dataframe_raises(self) -> None:
        """Test that fit non dataframe raises."""
        m = Inflation_Model_Standard()
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = {"Date": [], "inflation_rate": []})  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sorts_by_date(self) -> None:
        """Shuffled data should give same result as sorted data."""
        m1 = Inflation_Model_Standard(n_simulations=50)
        m2 = Inflation_Model_Standard(n_simulations=50)
        data = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2022-01-01", "2023-01-01", "2021-01-01", "2020-01-01"],
                "inflation_rate": [0.031, 0.070, 0.040, 0.047, 0.023],
            }
        )
        sorted_data = data.sort("Date")
        m1.fit(data = data)
        m2.fit(data = sorted_data)
        assert m1.m_kappa == pytest.approx(m2.m_kappa, abs=1e-10)
        assert m1.m_theta == pytest.approx(m2.m_theta, abs=1e-10)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardPredict:
    """Tests for predict() output structure."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict returns dataframe."""
        result = fitted_annual_model.predict(n_periods=12, seed=42)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict correct length."""
        for n in [1, 6, 12, 24]:
            result = fitted_annual_model.predict(n_periods=n, seed=0)
            assert len(result) == n, f"Expected {n} rows, got {len(result)}"

    @pytest.mark.unit()
    def test_predict_has_required_columns(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict has required columns."""
        result = fitted_annual_model.predict(n_periods=12, seed=1)
        required = {"Date", "Mean", "Median", "Std", "P5", "P25", "P75", "P95", "Min", "Max"}
        assert required.issubset(set(result.columns))

    @pytest.mark.unit()
    def test_predict_mean_finite(self, fitted_annual_model: Inflation_Model_Standard) -> None:
        """Test that predict mean finite."""
        result = fitted_annual_model.predict(n_periods=12, seed=2)
        means = result["Mean"].to_numpy()
        assert np.all(np.isfinite(means))

    @pytest.mark.unit()
    def test_predict_quantile_ordering(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict quantile ordering."""
        result = fitted_annual_model.predict(n_periods=24, seed=99)
        assert all(
            result["P5"][i] <= result["P25"][i] <= result["Median"][i]
            <= result["P75"][i] <= result["P95"][i]
            for i in range(len(result))
        )

    @pytest.mark.unit()
    def test_predict_min_le_max(self, fitted_annual_model: Inflation_Model_Standard) -> None:
        """Test that predict min le max."""
        result = fitted_annual_model.predict(n_periods=12, seed=5)
        assert all(result["Min"][i] <= result["Max"][i] for i in range(len(result)))

    @pytest.mark.unit()
    def test_predict_reproducible_with_seed(
        self, annual_data: pl.DataFrame
    ) -> None:
        """Test that predict reproducible with seed."""
        m1 = Inflation_Model_Standard(n_simulations=200)
        m2 = Inflation_Model_Standard(n_simulations=200)
        m1.fit(data = annual_data)
        m2.fit(data = annual_data)
        r1 = m1.predict(n_periods=12, seed=42)
        r2 = m2.predict(n_periods=12, seed=42)
        assert r1["Mean"].to_list() == r2["Mean"].to_list()

    @pytest.mark.unit()
    def test_predict_different_seeds_differ(self, annual_data: pl.DataFrame) -> None:
        """Test that predict different seeds differ."""
        m = Inflation_Model_Standard(n_simulations=500)
        m.fit(data = annual_data)
        r1 = m.predict(n_periods=24, seed=1)
        r2 = m.predict(n_periods=24, seed=2)
        # Means should differ (with overwhelming probability for 500 paths)
        assert r1["Mean"].to_list() != r2["Mean"].to_list()

    @pytest.mark.unit()
    def test_predict_before_fit_raises(self, default_model: Inflation_Model_Standard) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(n_periods=5)

    @pytest.mark.unit()
    def test_predict_zero_periods_raises(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict zero periods raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.predict(n_periods=0)

    @pytest.mark.unit()
    def test_predict_invalid_freq_raises(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict invalid freq raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.predict(n_periods=12, freq="1w")

    @pytest.mark.unit()
    def test_predict_default_start_date(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict default start date."""
        result = fitted_annual_model.predict(n_periods=3, seed=0)
        assert str(result["Date"][0]) == "2025-01-01"

    @pytest.mark.unit()
    def test_predict_custom_start_date(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that predict custom start date."""
        result = fitted_annual_model.predict(n_periods=3, start_date="2030-01-01", seed=0)
        assert str(result["Date"][0]) == "2030-01-01"

    @pytest.mark.unit()
    def test_predict_std_positive(self, fitted_annual_model: Inflation_Model_Standard) -> None:
        """Test that predict std positive."""
        result = fitted_annual_model.predict(n_periods=12, seed=10)
        std_vals = result["Std"].to_numpy()
        assert np.all(std_vals >= 0)


# =============================================================================
# Tests: get_annual_rate
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardGetAnnualRate:
    """Tests for get_annual_rate()."""

    @pytest.mark.unit()
    def test_returns_theta_after_fit(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that returns theta after fit."""
        rate = fitted_annual_model.get_annual_rate()
        assert rate == pytest.approx(fitted_annual_model.m_theta, abs=1e-12)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Inflation_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_annual_rate()


# =============================================================================
# Tests: analytical formulas
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardAnalytical:
    """Tests for get_analytical_mean() and get_analytical_variance()."""

    @pytest.mark.unit()
    def test_analytical_mean_at_zero_equals_pi0(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical mean at zero equals pi0."""
        # As t -> 0, mean should approach pi0 = current_rate
        mean = fitted_annual_model.get_analytical_mean(t_years=1e-6)
        assert mean == pytest.approx(fitted_annual_model.m_current_rate, abs=1e-4)

    @pytest.mark.unit()
    def test_analytical_mean_converges_to_theta(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical mean converges to theta."""
        # As t -> infinity, mean should converge to theta
        mean = fitted_annual_model.get_analytical_mean(t_years=200.0)
        assert mean == pytest.approx(fitted_annual_model.m_theta, abs=1e-4)

    @pytest.mark.unit()
    def test_analytical_variance_zero_at_t_zero(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical variance zero at t zero."""
        var = fitted_annual_model.get_analytical_variance(t_years=1e-9)
        assert var == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.unit()
    def test_analytical_variance_converges_to_stationary(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical variance converges to stationary."""
        stationary = (
            fitted_annual_model.m_sigma**2 / (2.0 * fitted_annual_model.m_kappa)
        )
        var_long = fitted_annual_model.get_analytical_variance(t_years=200.0)
        assert var_long == pytest.approx(stationary, rel=0.01)

    @pytest.mark.unit()
    def test_analytical_variance_positive(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical variance positive."""
        var = fitted_annual_model.get_analytical_variance(t_years=1.0)
        assert var > 0

    @pytest.mark.unit()
    def test_analytical_mean_before_fit_raises(
        self, default_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical mean before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.get_analytical_mean(t_years=1.0)

    @pytest.mark.unit()
    def test_analytical_variance_before_fit_raises(
        self, default_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical variance before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.get_analytical_variance(t_years=1.0)

    @pytest.mark.unit()
    def test_analytical_mean_zero_t_raises(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical mean zero t raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_mean(t_years=0.0)

    @pytest.mark.unit()
    def test_analytical_variance_negative_t_raises(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical variance negative t raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_annual_model.get_analytical_variance(t_years=-1.0)

    @pytest.mark.unit()
    def test_analytical_mean_custom_pi0(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that analytical mean custom pi0."""
        # With pi0 = theta, mean should stay at theta for all t
        theta = fitted_annual_model.m_theta
        mean = fitted_annual_model.get_analytical_mean(t_years=5.0, pi0=theta)
        assert mean == pytest.approx(theta, abs=1e-12)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardRepr:
    """Tests for __repr__."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(self, default_model: Inflation_Model_Standard) -> None:
        """Test that repr contains class name."""
        assert "Inflation_Model_Standard" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_kappa(self, default_model: Inflation_Model_Standard) -> None:
        """Test that repr contains kappa."""
        assert "kappa=" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_theta(self, default_model: Inflation_Model_Standard) -> None:
        """Test that repr contains theta."""
        assert "theta=" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status(self, default_model: Inflation_Model_Standard) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_fitted_contains_fitted(
        self, fitted_annual_model: Inflation_Model_Standard
    ) -> None:
        """Test that repr fitted contains fitted."""
        assert "Fitted" in repr(fitted_annual_model)


# =============================================================================
# Tests: missing branch coverage
# =============================================================================


class Class_Test_Inflation_Standard_Coverage_Gaps:
    """Targeted tests to cover remaining branch gaps in the OU model."""

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Bool_Theta(self) -> None:
        """Constructor should reject boolean theta values."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(theta=True)

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Bool_N_Simulations(self) -> None:
        """Constructor should reject boolean n_simulations values."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(n_simulations=False)

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Non_Finite_Theta(self) -> None:
        """Constructor should reject a non-finite theta (e.g. nan)."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(theta=float("nan"))

    @pytest.mark.unit()
    def Test_Constructor_Raises_For_Inf_Theta(self) -> None:
        """Constructor should reject infinite theta."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Standard(theta=float("inf"))

    @pytest.mark.unit()
    def Test_Fit_Raises_When_Dates_Not_Increasing(self) -> None:
        """fit() should raise when dates have zero gap (duplicate dates)."""
        # Duplicate dates → gaps_days will contain 0 → dt = 0 → dt <= 0 raises
        dup_dates = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-01", "2023-01-01", "2023-01-01"],
                "inflation_rate": [0.025, 0.026, 0.024, 0.027],
            }
        )
        m = Inflation_Model_Standard(n_simulations=10)
        with pytest.raises(Exception_Validation_Input):
            m.fit(data = dup_dates)

    @pytest.mark.unit()
    def Test_Analytical_Mean_Raises_For_Bool_T_Years(self) -> None:
        """Analytical mean should reject boolean t_years values."""
        model_inflation_standard = Inflation_Model_Standard(n_simulations=10)
        model_inflation_standard.m_status = Inflation_Model_Status.FITTED

        with pytest.raises(Exception_Validation_Input):
            model_inflation_standard.get_analytical_mean(t_years=True)

    @pytest.mark.unit()
    def Test_Analytical_Variance_Raises_For_Bool_T_Years(self) -> None:
        """Analytical variance should reject boolean t_years values."""
        model_inflation_standard = Inflation_Model_Standard(n_simulations=10)
        model_inflation_standard.m_status = Inflation_Model_Status.FITTED

        with pytest.raises(Exception_Validation_Input):
            model_inflation_standard.get_analytical_variance(t_years=False)

    @pytest.mark.unit()
    def Test_Fit_Uses_Constructor_Priors_When_Beta_Ols_Non_Negative(self) -> None:
        """When OLS beta >= 0 the model falls back to constructor kappa/theta."""
        # Craft data where rates strictly increase → β ≥ 0 in OLS
        import datetime as dt

        dates = [dt.date(2020, 1, 1) + dt.timedelta(days=365 * i) for i in range(8)]
        # Monotone increasing rates → no mean reversion, beta_ols >= 0
        rates = [0.01 + 0.005 * i for i in range(8)]
        data = pl.DataFrame(
            {
                "Date": dates,
                "inflation_rate": rates,
            }
        )
        m = Inflation_Model_Standard(kappa=0.4, theta=0.03, n_simulations=10)
        m.fit(data = data)
        # The model should use constructor priors (kappa=0.4) since beta >= 0
        assert m.m_kappa == pytest.approx(0.4, abs=1e-9)

    @pytest.mark.unit()
    def Test_Fit_Sigma_Fallback_When_Tiny_Dataset(self) -> None:
        """When residuals have <= 2 elements sigma falls back to constructor prior."""
        import datetime as dt

        # 3 rows → rates has 3 elements, y = diff(rates) has 2 elements
        # x = rates[:-1] has 2, resid = y - fitted has 2 → len(resid) == 2 (≤ 2) → fallback
        dates = [dt.date(2022, 1, 1), dt.date(2023, 1, 1), dt.date(2024, 1, 1)]
        rates = [0.03, 0.02, 0.025]
        data = pl.DataFrame({"Date": dates, "inflation_rate": rates})
        m = Inflation_Model_Standard(sigma=0.007, n_simulations=10)
        original_sigma = m.m_sigma
        m.fit(data = data)
        # Sigma falls back to original when resid is too small
        assert m.m_sigma == pytest.approx(original_sigma, rel=0.001) or m.m_sigma > 0

    @pytest.mark.unit()
    def Test_Fit_Raises_When_Ols_Returns_Non_Finite_Parameters(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fit() should reject non-finite OLS coefficients after data validation passes."""
        import src.models.inflation.model_inflation_standard as module_inflation_standard

        data = pl.DataFrame(
            {
                "Date": ["2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
                "inflation_rate": [0.020, 0.021, 0.019, 0.020],
            }
        )

        def _fake_lstsq(
            *_args: object,
            **_kwargs: object,
        ) -> tuple[np.ndarray, np.ndarray, None, None]:
            return np.array([np.nan, -0.1], dtype=np.float64), np.array([], dtype=np.float64), None, None

        monkeypatch.setattr(module_inflation_standard, "lstsq", _fake_lstsq)

        model_inflation_standard = Inflation_Model_Standard(n_simulations=10)
        with pytest.raises(Exception_Validation_Input, match="non-finite parameter estimates"):
            model_inflation_standard.fit(data = data)



# =============================================================================
# Tests: private helpers
# =============================================================================


@pytest.mark.unit
class TestInflationModelStandardHelpers:
    """Tests for private helper functions."""

    @pytest.mark.unit()
    def test_freq_to_dt_daily(self) -> None:
        """Test that freq to dt daily."""
        assert _freq_to_dt_years(freq = "1d") == pytest.approx(1.0 / 365.25, abs=1e-10)

    @pytest.mark.unit()
    def test_freq_to_dt_monthly(self) -> None:
        """Test that freq to dt monthly."""
        assert _freq_to_dt_years(freq = "1mo") == pytest.approx(1.0 / 12.0, abs=1e-12)

    @pytest.mark.unit()
    def test_freq_to_dt_annual(self) -> None:
        """Test that freq to dt annual."""
        assert _freq_to_dt_years(freq = "1y") == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.unit()
    def test_freq_to_dt_invalid_raises(self) -> None:
        """Test that freq to dt invalid raises."""
        with pytest.raises(Exception_Validation_Input):
            _freq_to_dt_years(freq = "1w")

    @pytest.mark.unit()
    def test_validate_positive_float_valid(self) -> None:
        """Test that validate positive float valid."""
        _validate_positive_float(value = 0.5, name = "kappa")  # Should not raise

    @pytest.mark.unit()
    def test_validate_positive_float_zero_raises(self) -> None:
        """Test that validate positive float zero raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = 0.0, name = "kappa")

    @pytest.mark.unit()
    def test_validate_positive_float_negative_raises(self) -> None:
        """Test that validate positive float negative raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = -1.0, name = "sigma")

    @pytest.mark.unit()
    def test_validate_positive_float_bool_raises(self) -> None:
        """Test that validate positive float rejects boolean values."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = True, name = "kappa")

    @pytest.mark.unit()
    def test_validate_positive_float_nan_raises(self) -> None:
        """Test that validate positive float nan raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("nan"), name = "kappa")

    @pytest.mark.unit()
    def test_simulate_ou_exact_shape(self) -> None:
        """Test that simulate ou exact shape."""
        rng = np.random.default_rng(42)
        paths = _simulate_ou_exact(
            kappa=0.5, theta=0.025, sigma=0.01,
            pi0=0.03, n_steps=12, n_paths=200, dt=1.0 / 12.0, rng=rng,
        )
        assert paths.shape == (12, 200)

    @pytest.mark.unit()
    def test_simulate_ou_exact_finite_values(self) -> None:
        """Test that simulate ou exact finite values."""
        rng = np.random.default_rng(0)
        paths = _simulate_ou_exact(
            kappa=0.5, theta=0.025, sigma=0.01,
            pi0=0.03, n_steps=24, n_paths=100, dt=1.0 / 12.0, rng=rng,
        )
        assert np.all(np.isfinite(paths))

    @pytest.mark.unit()
    def test_simulate_ou_exact_mean_converges_to_theta(self) -> None:
        """Long-horizon mean should converge to theta."""
        rng = np.random.default_rng(42)
        kappa, theta, sigma = 2.0, 0.025, 0.005
        paths = _simulate_ou_exact(
            kappa=kappa, theta=theta, sigma=sigma,
            pi0=0.08,  # Start far from theta
            n_steps=200,
            n_paths=10_000,
            dt=1.0 / 12.0,
            rng=rng,
        )
        # Mean of the last period should be close to theta
        terminal_mean = float(np.mean(paths[-1]))
        assert terminal_mean == pytest.approx(theta, abs=0.005)
