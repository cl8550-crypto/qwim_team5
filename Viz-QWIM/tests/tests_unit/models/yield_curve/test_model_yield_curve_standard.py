"""Tests for Yield_Curve_Model_Standard (Nelson-Siegel yield curve model).

Covers construction, fit() via OLS grid-search, predict(), get_par_yield(),
get_forward_rate(), get_slope(), get_curvature(), and the module-level
helpers _validate_positive_float, _validate_finite_float, _ns_loadings,
_ns_yield, _ns_forward.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.yield_curve import model_yield_curve_standard as ns_standard_module
from src.models.yield_curve.model_yield_curve_base import Yield_Curve_Model_Status
from src.models.yield_curve.model_yield_curve_standard import (
    Yield_Curve_Model_Standard,
    _design_matrix,
    _ns_forward,
    _ns_loadings,
    _ns_yield,
    _validate_finite_float,
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
def default_model() -> Yield_Curve_Model_Standard:
    """Return an unfitted Nelson-Siegel model with default parameters."""
    return Yield_Curve_Model_Standard()


@pytest.fixture()
def upward_sloping_data() -> pl.DataFrame:
    """Standard upward-sloping US-Treasury-like yield curve (8 points)."""
    return pl.DataFrame(
        {
            "Maturity": [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
            "Yield": [0.020, 0.025, 0.030, 0.035, 0.040, 0.045, 0.048, 0.050],
        },
    )


@pytest.fixture()
def inverted_data() -> pl.DataFrame:
    """Inverted yield curve (short > long end)."""
    return pl.DataFrame(
        {
            "Maturity": [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            "Yield": [0.055, 0.053, 0.050, 0.047, 0.043, 0.040, 0.038],
        },
    )


@pytest.fixture()
def humped_data() -> pl.DataFrame:
    """Humped yield curve (medium-maturity peak)."""
    return pl.DataFrame(
        {
            "Maturity": [0.25, 1.0, 2.0, 5.0, 7.0, 10.0, 20.0, 30.0],
            "Yield": [0.030, 0.038, 0.045, 0.050, 0.048, 0.044, 0.040, 0.038],
        },
    )


@pytest.fixture()
def fitted_upward_model(upward_sloping_data: pl.DataFrame) -> Yield_Curve_Model_Standard:
    """Return Nelson-Siegel model fitted to upward-sloping curve."""
    m = Yield_Curve_Model_Standard()
    m.fit(data = upward_sloping_data)
    return m


@pytest.fixture()
def fitted_ns_from_known_params() -> Yield_Curve_Model_Standard:
    """Return a model manually set to known NS parameters and marked fitted."""
    m = Yield_Curve_Model_Standard(beta0=0.06, beta1=-0.02, beta2=0.01, lambda_=2.0)
    # Fit with synthetically generated data so the OLS recovers similar params
    taus = np.array([0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0])
    yields = np.array([_ns_yield(tau = float(t), beta0 = 0.06, beta1 = -0.02, beta2 = 0.01, lam = 2.0) for t in taus])
    data = pl.DataFrame({"Maturity": taus.tolist(), "Yield": yields.tolist()})
    m.fit(data = data)
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardConstruction:
    """Tests for Yield_Curve_Model_Standard constructor."""

    @pytest.mark.unit()
    def test_default_beta0_stored(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that default beta0 stored."""
        assert default_model.m_beta0 == pytest.approx(0.05, abs=1e-12)

    @pytest.mark.unit()
    def test_default_beta1_stored(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that default beta1 stored."""
        assert default_model.m_beta1 == pytest.approx(-0.01, abs=1e-12)

    @pytest.mark.unit()
    def test_default_beta2_stored(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that default beta2 stored."""
        assert default_model.m_beta2 == pytest.approx(0.01, abs=1e-12)

    @pytest.mark.unit()
    def test_default_lambda_stored(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that default lambda stored."""
        assert default_model.m_lambda == pytest.approx(2.0, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_parameters_stored(self) -> None:
        """Test that custom parameters stored."""
        m = Yield_Curve_Model_Standard(beta0=0.06, beta1=-0.03, beta2=0.02, lambda_=3.0)
        assert m.m_beta0 == pytest.approx(0.06, abs=1e-12)
        assert m.m_beta1 == pytest.approx(-0.03, abs=1e-12)
        assert m.m_beta2 == pytest.approx(0.02, abs=1e-12)
        assert m.m_lambda == pytest.approx(3.0, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_lambda_raises(self) -> None:
        """Test that zero lambda raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Standard(lambda_=0.0)

    @pytest.mark.unit()
    def test_negative_lambda_raises(self) -> None:
        """Test that negative lambda raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Standard(lambda_=-1.0)

    @pytest.mark.unit()
    def test_nan_lambda_raises(self) -> None:
        """Test that nan lambda raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Standard(lambda_=float("nan"))

    @pytest.mark.unit()
    def test_nan_beta0_raises(self) -> None:
        """Test that nan beta0 raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Standard(beta0=float("nan"))

    @pytest.mark.unit()
    def test_inf_beta1_raises(self) -> None:
        """Test that inf beta1 raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Standard(beta1=float("inf"))

    @pytest.mark.unit()
    def test_negative_beta0_accepted(self) -> None:
        """Test that negative beta0 accepted."""
        # Negative long-run yield is financially valid in some environments
        m = Yield_Curve_Model_Standard(beta0=-0.01)
        assert m.m_beta0 == pytest.approx(-0.01, abs=1e-12)

    @pytest.mark.unit()
    def test_status_not_fitted_initially(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that status not fitted initially."""
        assert default_model.status == Yield_Curve_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Yield_Curve_Model_Standard(name_model="US Treasury NS")
        assert m.name_model == "US Treasury NS"


# =============================================================================
# Tests: fit
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardFit:
    """Tests for the fit() method."""

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        default_model: Yield_Curve_Model_Standard,
        upward_sloping_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        default_model.fit(data = upward_sloping_data)
        assert default_model.status == Yield_Curve_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        default_model: Yield_Curve_Model_Standard,
        upward_sloping_data: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = default_model.fit(data = upward_sloping_data)
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_empty_data_uses_priors(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit empty data uses priors."""
        beta0_before = default_model.m_beta0
        lambda_before = default_model.m_lambda
        default_model.fit(data = pl.DataFrame())
        assert default_model.m_beta0 == pytest.approx(beta0_before, abs=1e-12)
        assert default_model.m_lambda == pytest.approx(lambda_before, abs=1e-12)
        assert default_model.status == Yield_Curve_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_stores_parameters_dict(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that fit stores parameters dict."""
        params = fitted_upward_model.parameters
        for key in ("beta0", "beta1", "beta2", "lambda"):
            assert key in params

    @pytest.mark.unit()
    def test_fit_lambda_positive_after_fit(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that fit lambda positive after fit."""
        assert fitted_upward_model.m_lambda > 0

    @pytest.mark.unit()
    def test_fit_betas_finite_after_fit(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that fit betas finite after fit."""
        assert np.isfinite(fitted_upward_model.m_beta0)
        assert np.isfinite(fitted_upward_model.m_beta1)
        assert np.isfinite(fitted_upward_model.m_beta2)

    @pytest.mark.unit()
    def test_fit_sorts_by_maturity(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit sorts by maturity."""
        # Unsorted input should still fit correctly
        unsorted = pl.DataFrame(
            {
                "Maturity": [30.0, 5.0, 1.0, 0.5],
                "Yield": [0.050, 0.040, 0.030, 0.025],
            },
        )
        default_model.fit(data = unsorted)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_recovers_ns_params_from_synthetic_data(
        self,
        fitted_ns_from_known_params: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that fit recovers ns params from synthetic data."""
        # When data is generated exactly from NS, OLS should recover params closely
        m = fitted_ns_from_known_params
        # beta0 (long-run level) should be close to 6%
        assert m.m_beta0 == pytest.approx(0.06, abs=5e-3)

    @pytest.mark.unit()
    def test_fit_inverted_curve(
        self,
        default_model: Yield_Curve_Model_Standard,
        inverted_data: pl.DataFrame,
    ) -> None:
        """Test that fit inverted curve."""
        default_model.fit(data = inverted_data)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_humped_curve(
        self,
        default_model: Yield_Curve_Model_Standard,
        humped_data: pl.DataFrame,
    ) -> None:
        """Test that fit humped curve."""
        default_model.fit(data = humped_data)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_too_few_rows_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit too few rows raises."""
        short = pl.DataFrame({"Maturity": [1.0, 5.0], "Yield": [0.03, 0.04]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = short)

    @pytest.mark.unit()
    def test_fit_missing_maturity_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit missing maturity raises."""
        bad = pl.DataFrame({"Yield": [0.03, 0.04, 0.05]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_missing_yield_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit missing yield raises."""
        bad = pl.DataFrame({"Maturity": [1.0, 5.0, 10.0]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_nan_yield_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit nan yield raises."""
        bad = pl.DataFrame(
            {
                "Maturity": [1.0, 5.0, 10.0],
                "Yield": [0.03, float("nan"), 0.05],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_infinite_yield_raises(
        self,
        default_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that fit rejects infinite yields after DataFrame validation."""
        bad = pl.DataFrame(
            {
                "Maturity": [1.0, 5.0, 10.0],
                "Yield": [0.03, float("inf"), 0.05],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_non_dataframe_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that fit non dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = [(1.0, 0.03), (5.0, 0.04)])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_lstsq_errors_fall_back_to_priors(
        self,
        upward_sloping_data: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that OLS failures for all lambda candidates preserve priors."""
        model = Yield_Curve_Model_Standard(beta0=0.06, beta1=-0.03, beta2=0.02, lambda_=3.0)

        def raise_linalg_error(*args: object, **kwargs: object) -> tuple[object, ...]:
            raise np.linalg.LinAlgError("forced failure")

        monkeypatch.setattr(ns_standard_module, "lstsq", raise_linalg_error)

        model.fit(data = upward_sloping_data)

        assert model.status == Yield_Curve_Model_Status.FITTED
        assert model.m_beta0 == pytest.approx(0.06, abs=1e-12)
        assert model.m_beta1 == pytest.approx(-0.03, abs=1e-12)
        assert model.m_beta2 == pytest.approx(0.02, abs=1e-12)
        assert model.m_lambda == pytest.approx(3.0, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_rank_deficient_ols_falls_back_to_priors(
        self,
        upward_sloping_data: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that rank-deficient OLS results are skipped for all lambdas."""
        model = Yield_Curve_Model_Standard(beta0=0.04, beta1=-0.01, beta2=0.02, lambda_=1.5)

        def return_rank_deficient(*args: object, **kwargs: object) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
            return np.zeros(3), np.array([]), 2, np.array([])

        monkeypatch.setattr(ns_standard_module, "lstsq", return_rank_deficient)

        model.fit(data = upward_sloping_data)

        assert model.status == Yield_Curve_Model_Status.FITTED
        assert model.m_beta0 == pytest.approx(0.04, abs=1e-12)
        assert model.m_beta1 == pytest.approx(-0.01, abs=1e-12)
        assert model.m_beta2 == pytest.approx(0.02, abs=1e-12)
        assert model.m_lambda == pytest.approx(1.5, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_non_finite_betas_fall_back_to_priors(
        self,
        upward_sloping_data: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that non-finite OLS coefficients do not overwrite priors."""
        model = Yield_Curve_Model_Standard(beta0=0.055, beta1=-0.015, beta2=0.01, lambda_=2.5)

        def return_non_finite_betas(*args: object, **kwargs: object) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
            return np.array([np.inf, 0.0, 0.0]), np.array([]), 3, np.array([])

        monkeypatch.setattr(ns_standard_module, "lstsq", return_non_finite_betas)
        monkeypatch.setattr(ns_standard_module.np, "sum", lambda values: 0.0)

        model.fit(data = upward_sloping_data)

        assert model.status == Yield_Curve_Model_Status.FITTED
        assert model.m_beta0 == pytest.approx(0.055, abs=1e-12)
        assert model.m_beta1 == pytest.approx(-0.015, abs=1e-12)
        assert model.m_beta2 == pytest.approx(0.01, abs=1e-12)
        assert model.m_lambda == pytest.approx(2.5, abs=1e-12)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardPredict:
    """Tests for predict()."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_upward_model.predict(maturities=[1.0, 5.0, 10.0])
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that predict correct length."""
        df = fitted_upward_model.predict(maturities=[1.0, 2.0, 5.0, 10.0, 30.0])
        assert len(df) == 5

    @pytest.mark.unit()
    def test_predict_has_maturity_column(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict has maturity column."""
        df = fitted_upward_model.predict(maturities=[5.0])
        assert "Maturity" in df.columns

    @pytest.mark.unit()
    def test_predict_has_yield_column(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict has yield column."""
        df = fitted_upward_model.predict(maturities=[5.0])
        assert "Yield" in df.columns

    @pytest.mark.unit()
    def test_predict_has_forward_rate_column(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict has forward rate column."""
        df = fitted_upward_model.predict(maturities=[5.0])
        assert "forward_rate" in df.columns

    @pytest.mark.unit()
    def test_predict_maturities_match_input(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict maturities match input."""
        taus = [0.5, 2.0, 10.0, 30.0]
        df = fitted_upward_model.predict(maturities=taus)
        assert df["Maturity"].to_list() == pytest.approx(taus)

    @pytest.mark.unit()
    def test_predict_yields_finite(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that predict yields finite."""
        df = fitted_upward_model.predict(maturities=[0.5, 1.0, 5.0, 10.0, 30.0])
        assert all(np.isfinite(v) for v in df["Yield"].to_list())

    @pytest.mark.unit()
    def test_predict_forward_rates_finite(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict forward rates finite."""
        df = fitted_upward_model.predict(maturities=[1.0, 5.0, 30.0])
        assert all(np.isfinite(v) for v in df["forward_rate"].to_list())

    @pytest.mark.unit()
    def test_predict_none_generates_grid(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict none generates grid."""
        df = fitted_upward_model.predict(n_points=40)
        assert len(df) == 40

    @pytest.mark.unit()
    def test_predict_before_fit_raises(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(maturities=[5.0])

    @pytest.mark.unit()
    def test_predict_zero_n_points_raises(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict zero n points raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_upward_model.predict(n_points=0)

    @pytest.mark.unit()
    def test_predict_negative_maturity_raises(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that predict negative maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_upward_model.predict(maturities=[-1.0, 5.0])


# =============================================================================
# Tests: get_par_yield
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardParYield:
    """Tests for get_par_yield()."""

    @pytest.mark.unit()
    def test_returns_finite_value(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that returns finite value."""
        y = fitted_upward_model.get_par_yield(maturity = 5.0)
        assert np.isfinite(y)

    @pytest.mark.unit()
    def test_matches_ns_formula(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that matches ns formula."""
        tau = 10.0
        expected = _ns_yield(
            tau = tau,
            beta0 = fitted_upward_model.m_beta0,
            beta1 = fitted_upward_model.m_beta1,
            beta2 = fitted_upward_model.m_beta2,
            lam = fitted_upward_model.m_lambda,
        )
        assert fitted_upward_model.get_par_yield(maturity = tau) == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit()
    def test_matches_predict_output(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that matches predict output."""
        tau = 5.0
        df = fitted_upward_model.predict(maturities=[tau])
        assert fitted_upward_model.get_par_yield(maturity = tau) == pytest.approx(df["Yield"][0], rel=1e-10)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_par_yield(maturity = 5.0)

    @pytest.mark.unit()
    def test_zero_maturity_raises(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that zero maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_upward_model.get_par_yield(maturity = 0.0)

    @pytest.mark.unit()
    def test_negative_maturity_raises(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that negative maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_upward_model.get_par_yield(maturity = -1.0)


# =============================================================================
# Tests: get_forward_rate
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardForwardRate:
    """Tests for get_forward_rate()."""

    @pytest.mark.unit()
    def test_returns_finite_value(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that returns finite value."""
        f = fitted_upward_model.get_forward_rate(maturity = 5.0)
        assert np.isfinite(f)

    @pytest.mark.unit()
    def test_matches_ns_formula(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that matches ns formula."""
        tau = 10.0
        expected = _ns_forward(
            tau = tau,
            beta0 = fitted_upward_model.m_beta0,
            beta1 = fitted_upward_model.m_beta1,
            beta2 = fitted_upward_model.m_beta2,
            lam = fitted_upward_model.m_lambda,
        )
        assert fitted_upward_model.get_forward_rate(maturity = tau) == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit()
    def test_matches_predict_column(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that matches predict column."""
        tau = 10.0
        df = fitted_upward_model.predict(maturities=[tau])
        assert fitted_upward_model.get_forward_rate(maturity = tau) == pytest.approx(
            df["forward_rate"][0], rel=1e-10,
        )

    @pytest.mark.unit()
    def test_converges_to_beta0_at_long_end(
        self, fitted_ns_from_known_params: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that converges to beta0 at long end."""
        # For NS, f(tau) -> beta0 as tau -> inf
        f_long = fitted_ns_from_known_params.get_forward_rate(maturity = 100.0)
        assert f_long == pytest.approx(fitted_ns_from_known_params.m_beta0, abs=1e-4)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_forward_rate(maturity = 5.0)

    @pytest.mark.unit()
    def test_zero_maturity_raises(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that zero maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_upward_model.get_forward_rate(maturity = 0.0)


# =============================================================================
# Tests: get_slope and get_curvature
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardShapeDiagnostics:
    """Tests for get_slope() and get_curvature()."""

    @pytest.mark.unit()
    def test_slope_returns_beta1(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that slope returns beta1."""
        assert fitted_upward_model.get_slope() == pytest.approx(
            fitted_upward_model.m_beta1, abs=1e-12,
        )

    @pytest.mark.unit()
    def test_curvature_returns_beta2(self, fitted_upward_model: Yield_Curve_Model_Standard) -> None:
        """Test that curvature returns beta2."""
        assert fitted_upward_model.get_curvature() == pytest.approx(
            fitted_upward_model.m_beta2, abs=1e-12,
        )

    @pytest.mark.unit()
    def test_slope_raises_before_fit(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that slope raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_slope()

    @pytest.mark.unit()
    def test_curvature_raises_before_fit(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that curvature raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_curvature()


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that repr contains class name."""
        assert "Yield_Curve_Model_Standard" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_beta0(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that repr contains beta0."""
        assert "beta0=" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_lambda(self, default_model: Yield_Curve_Model_Standard) -> None:
        """Test that repr contains lambda."""
        assert "lambda=" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status_not_fitted(
        self, default_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that repr contains status not fitted."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_fitted_status(
        self, fitted_upward_model: Yield_Curve_Model_Standard,
    ) -> None:
        """Test that repr contains fitted status."""
        assert "Fitted" in repr(fitted_upward_model)


# =============================================================================
# Tests: module-level helpers
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelStandardHelpers:
    """Tests for module-level helper functions."""

    # --- _validate_positive_float ---

    @pytest.mark.unit()
    def test_validate_positive_float_valid(self) -> None:
        """Test that validate positive float valid."""
        _validate_positive_float(value = 0.5, name = "test")  # should not raise

    @pytest.mark.unit()
    def test_validate_positive_float_zero_raises(self) -> None:
        """Test that validate positive float zero raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = 0.0, name = "test")

    @pytest.mark.unit()
    def test_validate_positive_float_negative_raises(self) -> None:
        """Test that validate positive float negative raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = -1.0, name = "test")

    @pytest.mark.unit()
    def test_validate_positive_float_nan_raises(self) -> None:
        """Test that validate positive float nan raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("nan"), name = "test")

    @pytest.mark.unit()
    def test_validate_positive_float_inf_raises(self) -> None:
        """Test that validate positive float inf raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("inf"), name = "test")

    @pytest.mark.unit()
    def test_validate_positive_float_bool_raises(self) -> None:
        """Test that validate positive float bool raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = True, name = "test")  # type: ignore[arg-type]  # noqa: FBT003

    # --- _validate_finite_float ---

    @pytest.mark.unit()
    def test_validate_finite_float_positive_valid(self) -> None:
        """Test that validate finite float positive valid."""
        _validate_finite_float(value = 1.5, name = "test")

    @pytest.mark.unit()
    def test_validate_finite_float_negative_valid(self) -> None:
        """Test that validate finite float negative valid."""
        _validate_finite_float(value = -0.01, name = "test")

    @pytest.mark.unit()
    def test_validate_finite_float_zero_valid(self) -> None:
        """Test that validate finite float zero valid."""
        _validate_finite_float(value = 0.0, name = "test")

    @pytest.mark.unit()
    def test_validate_finite_float_nan_raises(self) -> None:
        """Test that validate finite float nan raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_finite_float(value = float("nan"), name = "test")

    @pytest.mark.unit()
    def test_validate_finite_float_inf_raises(self) -> None:
        """Test that validate finite float inf raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_finite_float(value = float("inf"), name = "test")

    @pytest.mark.unit()
    def test_validate_finite_float_bool_raises(self) -> None:
        """Test that validate finite float rejects booleans."""
        with pytest.raises(Exception_Validation_Input):
            _validate_finite_float(value = False, name = "test")  # type: ignore[arg-type]  # noqa: FBT003

    # --- _ns_loadings ---

    @pytest.mark.unit()
    def test_ns_loadings_l1_always_one(self) -> None:
        """Test that ns loadings l1 always one."""
        l1, _, _ = _ns_loadings(tau = 5.0, lam = 2.0)
        assert l1 == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.unit()
    def test_ns_loadings_l2_near_one_short_maturity(self) -> None:
        """Test that ns loadings l2 near one short maturity."""
        # At very short maturity L2 -> 1 (L'Hopital)
        _, l2, _ = _ns_loadings(tau = 1e-9, lam = 2.0)
        assert l2 == pytest.approx(1.0, abs=1e-6)

    @pytest.mark.unit()
    def test_ns_loadings_l2_decays_with_maturity(self) -> None:
        """Test that ns loadings l2 decays with maturity."""
        _, l2_short, _ = _ns_loadings(tau = 1.0, lam = 2.0)
        _, l2_long, _ = _ns_loadings(tau = 30.0, lam = 2.0)
        assert l2_short > l2_long

    @pytest.mark.unit()
    def test_ns_loadings_l3_zero_at_short_maturity(self) -> None:
        """Test that ns loadings l3 zero at short maturity."""
        # l3 = l2 - exp(-x); at very short maturity both terms -> 1 -> l3 -> 0
        _, _l2, l3 = _ns_loadings(tau = 1e-9, lam = 2.0)
        assert l3 == pytest.approx(0.0, abs=1e-4)

    # --- _ns_yield ---

    @pytest.mark.unit()
    def test_ns_yield_converges_to_beta0_long(self) -> None:
        """Test that ns yield converges to beta0 long."""
        # y(tau) -> beta0 as tau -> inf
        y_long = _ns_yield(tau = 1000.0, beta0 = 0.06, beta1 = -0.02, beta2 = 0.01, lam = 2.0)
        assert y_long == pytest.approx(0.06, abs=1e-4)

    @pytest.mark.unit()
    def test_ns_yield_at_zero_equals_beta0_plus_beta1(self) -> None:
        """Test that ns yield at zero equals beta0 plus beta1."""
        # y(0+) = beta0 + beta1 (L2(0+) = 1, L3(0+) = 0)
        y_short = _ns_yield(tau = 1e-9, beta0 = 0.06, beta1 = -0.02, beta2 = 0.01, lam = 2.0)
        assert y_short == pytest.approx(0.06 + (-0.02), abs=1e-4)

    # --- _ns_forward ---

    @pytest.mark.unit()
    def test_ns_forward_converges_to_beta0_long(self) -> None:
        """Test that ns forward converges to beta0 long."""
        # f(tau) -> beta0 as tau -> inf
        f_long = _ns_forward(tau = 1000.0, beta0 = 0.06, beta1 = -0.02, beta2 = 0.01, lam = 2.0)
        assert f_long == pytest.approx(0.06, abs=1e-4)

    @pytest.mark.unit()
    def test_ns_forward_at_zero_equals_beta0_plus_beta1(self) -> None:
        """Test that ns forward at zero equals beta0 plus beta1."""
        # f(0+) = beta0 + beta1 (exp(-x) -> 1, x*exp(-x) -> 0)
        f_short = _ns_forward(tau = 1e-9, beta0 = 0.06, beta1 = -0.02, beta2 = 0.01, lam = 2.0)
        assert f_short == pytest.approx(0.06 + (-0.02), abs=1e-4)

    @pytest.mark.unit()
    def test_ns_forward_equals_spot_when_flat(self) -> None:
        """Test that ns forward equals spot when flat."""
        # If beta1 = beta2 = 0, forward == spot == beta0 for all tau
        for tau in [0.5, 2.0, 10.0, 30.0]:
            y = _ns_yield(tau = tau, beta0 = 0.05, beta1 = 0.0, beta2 = 0.0, lam = 2.0)
            f = _ns_forward(tau = tau, beta0 = 0.05, beta1 = 0.0, beta2 = 0.0, lam = 2.0)
            assert y == pytest.approx(0.05, abs=1e-10)
            assert f == pytest.approx(0.05, abs=1e-10)

    # --- _design_matrix ---

    @pytest.mark.unit()
    def test_design_matrix_shape(self) -> None:
        """Test that design matrix shape."""
        taus = np.array([1.0, 5.0, 10.0])
        mat = _design_matrix(taus = taus, lam = 2.0)
        assert mat.shape == (3, 3)

    @pytest.mark.unit()
    def test_design_matrix_first_column_is_ones(self) -> None:
        """Test that design matrix first column is ones."""
        taus = np.array([1.0, 5.0, 10.0])
        mat = _design_matrix(taus = taus, lam = 2.0)
        assert mat[:, 0].tolist() == pytest.approx([1.0, 1.0, 1.0])

    @pytest.mark.unit()
    def test_design_matrix_all_finite(self) -> None:
        """Test that design matrix all finite."""
        taus = np.linspace(0.25, 30.0, 20)
        mat = _design_matrix(taus = taus, lam = 2.0)
        assert np.all(np.isfinite(mat))
