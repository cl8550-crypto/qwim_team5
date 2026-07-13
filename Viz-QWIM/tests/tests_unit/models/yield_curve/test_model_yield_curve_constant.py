"""Tests for Yield_Curve_Model_Constant (flat / constant yield curve model).

Covers construction, fit() with and without data, predict(),
get_par_yield(), get_forward_rate(), and repr.
"""

from __future__ import annotations

import polars as pl
import pytest

from src.models.yield_curve.model_yield_curve_base import Yield_Curve_Model_Status
from src.models.yield_curve.model_yield_curve_constant import Yield_Curve_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def default_model() -> Yield_Curve_Model_Constant:
    """Return an unfitted flat-curve model with default parameters."""
    return Yield_Curve_Model_Constant()


@pytest.fixture()
def fitted_default_model() -> Yield_Curve_Model_Constant:
    """Return a flat-curve model fitted with empty data (uses 3 % default)."""
    m = Yield_Curve_Model_Constant()
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def market_data() -> pl.DataFrame:
    """Simple four-point yield curve (upward-sloping)."""
    return pl.DataFrame(
        {
            "Maturity": [1.0, 2.0, 5.0, 10.0],
            "Yield": [0.030, 0.032, 0.036, 0.038],
        },
    )


@pytest.fixture()
def fitted_market_model(market_data: pl.DataFrame) -> Yield_Curve_Model_Constant:
    """Return flat-curve model fitted to market_data fixture."""
    m = Yield_Curve_Model_Constant()
    m.fit(data = market_data)
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantConstruction:
    """Tests for Yield_Curve_Model_Constant constructor."""

    @pytest.mark.unit()
    def test_default_flat_rate_stored(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that default flat rate stored."""
        assert default_model.m_flat_rate == pytest.approx(0.03, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_flat_rate_stored(self) -> None:
        """Test that custom flat rate stored."""
        m = Yield_Curve_Model_Constant(flat_rate=0.05)
        assert m.m_flat_rate == pytest.approx(0.05, abs=1e-12)

    @pytest.mark.unit()
    def test_negative_rate_accepted(self) -> None:
        """Test that negative rate accepted."""
        # Japan / European-style negative yields
        m = Yield_Curve_Model_Constant(flat_rate=-0.005)
        assert m.m_flat_rate == pytest.approx(-0.005, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_at_lower_boundary_accepted(self) -> None:
        """Test that rate at lower boundary accepted."""
        m = Yield_Curve_Model_Constant(flat_rate=-0.10)
        assert m.m_flat_rate == pytest.approx(-0.10, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_at_upper_boundary_accepted(self) -> None:
        """Test that rate at upper boundary accepted."""
        m = Yield_Curve_Model_Constant(flat_rate=0.30)
        assert m.m_flat_rate == pytest.approx(0.30, abs=1e-12)

    @pytest.mark.unit()
    def test_rate_below_lower_bound_raises(self) -> None:
        """Test that rate below lower bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=-0.11)

    @pytest.mark.unit()
    def test_rate_above_upper_bound_raises(self) -> None:
        """Test that rate above upper bound raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=0.31)

    @pytest.mark.unit()
    def test_nan_raises(self) -> None:
        """Test that nan raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=float("nan"))

    @pytest.mark.unit()
    def test_inf_raises(self) -> None:
        """Test that inf raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=float("inf"))

    @pytest.mark.unit()
    def test_bool_raises(self) -> None:
        """Test that bool raises."""
        with pytest.raises(Exception_Validation_Input):
            Yield_Curve_Model_Constant(flat_rate=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_default_status_not_fitted(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that default status not fitted."""
        assert default_model.status == Yield_Curve_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Yield_Curve_Model_Constant(name_model="Floor Rate")
        assert m.name_model == "Floor Rate"


# =============================================================================
# Tests: fit (no data)
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantFitNoData:
    """Tests for fit() called with an empty DataFrame."""

    @pytest.mark.unit()
    def test_fit_empty_data_returns_self(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit empty data returns self."""
        result = default_model.fit(data = pl.DataFrame())
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_empty_data_sets_fitted(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit empty data sets fitted."""
        default_model.fit(data = pl.DataFrame())
        assert default_model.status == Yield_Curve_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_empty_data_preserves_rate(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit empty data preserves rate."""
        rate_before = default_model.m_flat_rate
        default_model.fit(data = pl.DataFrame())
        assert default_model.m_flat_rate == pytest.approx(rate_before, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_invalid_type_raises(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit invalid type raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = [(1.0, 0.03)])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that fit sets parameters dict."""
        assert "flat_rate" in fitted_default_model.parameters
        assert fitted_default_model.parameters["flat_rate"] == pytest.approx(
            fitted_default_model.m_flat_rate,
        )


# =============================================================================
# Tests: fit (with data)
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantFitWithData:
    """Tests for fit() called with market yield data."""

    @pytest.mark.unit()
    def test_fit_estimates_mean(
        self,
        default_model: Yield_Curve_Model_Constant,
        market_data: pl.DataFrame,
    ) -> None:
        """Test that fit estimates mean."""
        default_model.fit(data = market_data)
        expected_mean = float(
            market_data["Yield"].mean(),  # type: ignore[arg-type]
        )
        assert default_model.m_flat_rate == pytest.approx(expected_mean, rel=1e-10)

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        default_model: Yield_Curve_Model_Constant,
        market_data: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = default_model.fit(data = market_data)
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        default_model: Yield_Curve_Model_Constant,
        market_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        default_model.fit(data = market_data)
        assert default_model.status == Yield_Curve_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_missing_maturity_column_raises(
        self, default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that fit missing maturity column raises."""
        bad = pl.DataFrame({"Yield": [0.03, 0.04]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_missing_yield_column_raises(
        self, default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that fit missing yield column raises."""
        bad = pl.DataFrame({"Maturity": [1.0, 5.0]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_negative_yields_accepted(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit negative yields accepted."""
        neg = pl.DataFrame({"Maturity": [1.0, 2.0, 5.0], "Yield": [-0.002, -0.001, 0.0]})
        default_model.fit(data = neg)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_non_finite_yield_raises(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit rejects non-finite yield values."""
        bad = pl.DataFrame({"Maturity": [1.0, 2.0], "Yield": [0.03, float("inf")]})

        with pytest.raises(Exception_Validation_Input, match="non-finite"):
            default_model.fit(data = bad)

    @pytest.mark.unit()
    def test_fit_single_observation(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that fit single observation."""
        single = pl.DataFrame({"Maturity": [10.0], "Yield": [0.045]})
        default_model.fit(data = single)
        assert default_model.m_flat_rate == pytest.approx(0.045, abs=1e-12)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantPredict:
    """Tests for predict()."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_default_model.predict(maturities=[1.0, 5.0, 10.0])
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that predict correct length."""
        df = fitted_default_model.predict(maturities=[1.0, 2.0, 5.0, 10.0, 20.0])
        assert len(df) == 5

    @pytest.mark.unit()
    def test_predict_has_maturity_column(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict has maturity column."""
        df = fitted_default_model.predict(maturities=[1.0, 5.0])
        assert "Maturity" in df.columns

    @pytest.mark.unit()
    def test_predict_has_yield_column(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict has yield column."""
        df = fitted_default_model.predict(maturities=[1.0, 5.0])
        assert "Yield" in df.columns

    @pytest.mark.unit()
    def test_predict_constant_values(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict constant values."""
        df = fitted_default_model.predict(maturities=[1.0, 2.0, 5.0, 10.0, 30.0])
        assert all(
            v == pytest.approx(fitted_default_model.m_flat_rate, abs=1e-12)
            for v in df["Yield"].to_list()
        )

    @pytest.mark.unit()
    def test_predict_maturities_match_input(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict maturities match input."""
        taus = [0.5, 2.0, 10.0]
        df = fitted_default_model.predict(maturities=taus)
        assert df["Maturity"].to_list() == pytest.approx(taus)

    @pytest.mark.unit()
    def test_predict_none_generates_grid(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict none generates grid."""
        df = fitted_default_model.predict(n_points=30)
        assert len(df) == 30

    @pytest.mark.unit()
    def test_predict_custom_max_maturity(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict custom max maturity."""
        df = fitted_default_model.predict(n_points=10, max_maturity=10.0)
        assert df["Maturity"].max() == pytest.approx(10.0, rel=1e-6)

    @pytest.mark.unit()
    def test_predict_before_fit_raises(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(maturities=[1.0, 5.0])

    @pytest.mark.unit()
    def test_predict_zero_n_points_raises(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict zero n points raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_points=0)

    @pytest.mark.unit()
    def test_predict_zero_max_maturity_raises(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that predict zero max maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(max_maturity=0.0)

    @pytest.mark.unit()
    def Test_Predict_Max_Maturity_Below_Quarter_Year_Raises(
        self,
        fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Generated prediction grids require max_maturity >= 0.25 years."""
        with pytest.raises(Exception_Validation_Input, match="0.25"):
            fitted_default_model.predict(max_maturity=0.10)


# =============================================================================
# Tests: get_par_yield
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantParYield:
    """Tests for get_par_yield()."""

    @pytest.mark.unit()
    def test_returns_flat_rate(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that returns flat rate."""
        yield_val = fitted_default_model.get_par_yield(maturity = 5.0)
        assert yield_val == pytest.approx(fitted_default_model.m_flat_rate, abs=1e-12)

    @pytest.mark.unit()
    def test_maturity_independent(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that maturity independent."""
        for tau in [0.25, 1.0, 5.0, 10.0, 30.0]:
            assert fitted_default_model.get_par_yield(maturity = tau) == pytest.approx(
                fitted_default_model.m_flat_rate, abs=1e-12,
            )

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_par_yield(maturity = 5.0)

    @pytest.mark.unit()
    def test_zero_maturity_raises(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that zero maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.get_par_yield(maturity = 0.0)

    @pytest.mark.unit()
    def test_negative_maturity_raises(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that negative maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.get_par_yield(maturity = -1.0)


# =============================================================================
# Tests: get_forward_rate
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantForwardRate:
    """Tests for get_forward_rate()."""

    @pytest.mark.unit()
    def test_returns_flat_rate(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that returns flat rate."""
        fwd = fitted_default_model.get_forward_rate(maturity = 5.0)
        assert fwd == pytest.approx(fitted_default_model.m_flat_rate, abs=1e-12)

    @pytest.mark.unit()
    def test_equals_spot_yield(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that equals spot yield."""
        # For a flat curve forward == spot at every maturity
        for tau in [1.0, 5.0, 10.0]:
            assert fitted_default_model.get_forward_rate(maturity = tau) == pytest.approx(
                fitted_default_model.get_par_yield(maturity = tau), abs=1e-12,
            )

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_forward_rate(maturity = 5.0)

    @pytest.mark.unit()
    def test_zero_maturity_raises(self, fitted_default_model: Yield_Curve_Model_Constant) -> None:
        """Test that zero maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.get_forward_rate(maturity = 0.0)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelConstantRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that repr contains class name."""
        assert "Yield_Curve_Model_Constant" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_flat_rate(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that repr contains flat rate."""
        assert "flat_rate=" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status(self, default_model: Yield_Curve_Model_Constant) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_fitted_contains_fitted(
        self, fitted_default_model: Yield_Curve_Model_Constant,
    ) -> None:
        """Test that repr fitted contains fitted."""
        assert "Fitted" in repr(fitted_default_model)
