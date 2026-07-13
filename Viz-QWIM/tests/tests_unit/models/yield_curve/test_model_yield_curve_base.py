"""Tests for Yield_Curve_Model_Base abstract base class.

Covers construction, properties, shared validators, the
_resolve_maturities helper, and get_summary_statistics, using a
minimal concrete stub that supplies the four abstract methods.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.yield_curve.model_yield_curve_base import (
    Yield_Curve_Model_Base,
    Yield_Curve_Model_Status,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Minimal concrete stub
# =============================================================================


class _ConcreteYieldCurveModel(Yield_Curve_Model_Base):
    """Minimal concrete subclass for testing the base-class API."""

    def fit(self, data: pl.DataFrame) -> _ConcreteYieldCurveModel:
        """Fit."""
        self.m_status = Yield_Curve_Model_Status.FITTED  # type: ignore[reportAttributeAccessIssue]
        return self

    def predict(
        self,
        maturities: list[float] | np.ndarray | None = None,
        *,
        n_points: int = 50,
        max_maturity: float = 30.0,
    ) -> pl.DataFrame:
        """Predict."""
        self._check_is_fitted()
        taus = self._resolve_maturities(maturities = maturities, n_points = n_points, max_maturity = max_maturity)
        return pl.DataFrame({"Maturity": taus.tolist(), "Yield": [0.04] * len(taus)})

    def get_par_yield(self, maturity: float) -> float:
        """Get par yield."""
        self._check_is_fitted()
        self._validate_maturity(maturity = maturity)
        return 0.04

    def get_forward_rate(self, maturity: float) -> float:
        """Get forward rate."""
        self._check_is_fitted()
        self._validate_maturity(maturity = maturity)
        return 0.04


@pytest.fixture()
def model() -> _ConcreteYieldCurveModel:
    """Model."""
    return _ConcreteYieldCurveModel()


@pytest.fixture()
def fitted_model() -> _ConcreteYieldCurveModel:
    """Fitted model."""
    m = _ConcreteYieldCurveModel()
    m.fit(data = pl.DataFrame())
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseConstruction:
    """Tests for Yield_Curve_Model_Base constructor."""

    @pytest.mark.unit()
    def test_valid_name_accepted(self) -> None:
        """Test that valid name accepted."""
        m = _ConcreteYieldCurveModel(name_model="My Curve")
        assert m.name_model == "My Curve"

    @pytest.mark.unit()
    def test_name_stripped(self) -> None:
        """Test that name stripped."""
        m = _ConcreteYieldCurveModel(name_model="  Curve  ")
        assert m.name_model == "Curve"

    @pytest.mark.unit()
    def test_default_status_not_fitted(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that default status not fitted."""
        assert model.status == Yield_Curve_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_default_parameters_empty(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that default parameters empty."""
        assert model.parameters == {}

    @pytest.mark.unit()
    def test_invalid_name_empty_string_raises(self) -> None:
        """Test that invalid name empty string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteYieldCurveModel(name_model="")

    @pytest.mark.unit()
    def test_invalid_name_whitespace_raises(self) -> None:
        """Test that invalid name whitespace raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteYieldCurveModel(name_model="   ")

    @pytest.mark.unit()
    def test_invalid_name_non_string_raises(self) -> None:
        """Test that invalid name non string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteYieldCurveModel(name_model=123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_abstract_class_not_instantiable_directly(self) -> None:
        """Test that abstract class not instantiable directly."""
        with pytest.raises(TypeError):
            Yield_Curve_Model_Base()  # type: ignore[abstract]


# =============================================================================
# Tests: properties
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseProperties:
    """Tests for Yield_Curve_Model_Base properties."""

    @pytest.mark.unit()
    def test_is_fitted_false_before_fit(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that is fitted false before fit."""
        assert model.is_fitted is False

    @pytest.mark.unit()
    def test_is_fitted_true_after_fit(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that is fitted true after fit."""
        assert fitted_model.is_fitted is True

    @pytest.mark.unit()
    def test_status_fitted_after_fit(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that status fitted after fit."""
        assert fitted_model.status == Yield_Curve_Model_Status.FITTED

    @pytest.mark.unit()
    def test_parameters_copy_returned(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that parameters copy returned."""
        params = fitted_model.parameters
        params["extra"] = 99.0
        assert "extra" not in fitted_model.parameters

    @pytest.mark.unit()
    def test_name_model_unchanged(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that name model unchanged."""
        assert model.name_model == "Yield Curve Model"


# =============================================================================
# Tests: _validate_maturity
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseValidateMaturity:
    """Tests for the _validate_maturity helper."""

    @pytest.mark.unit()
    def test_positive_float_valid(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that positive float valid."""
        model._validate_maturity(maturity = 1.0)  # should not raise

    @pytest.mark.unit()
    def test_positive_integer_valid(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that positive integer valid."""
        model._validate_maturity(maturity = 10)  # int also accepted

    @pytest.mark.unit()
    def test_zero_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that zero raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = 0.0)

    @pytest.mark.unit()
    def test_negative_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that negative raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = -1.0)

    @pytest.mark.unit()
    def test_nan_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that nan raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = float("nan"))

    @pytest.mark.unit()
    def test_inf_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that inf raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = float("inf"))

    @pytest.mark.unit()
    def test_bool_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that bool raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = True)  # type: ignore[arg-type]  # noqa: FBT003

    @pytest.mark.unit()
    def test_string_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that string raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_maturity(maturity = "5")  # type: ignore[arg-type]


# =============================================================================
# Tests: _validate_yield_curve_data
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseValidateData:
    """Tests for the _validate_yield_curve_data helper."""

    @pytest.mark.unit()
    def test_valid_dataframe_passes(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that valid dataframe passes."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0], "Yield": [0.03, 0.04]})
        model._validate_yield_curve_data(data = df)  # should not raise

    @pytest.mark.unit()
    def test_not_dataframe_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that not dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = [(1.0, 0.03)])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_empty_dataframe_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that empty dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = pl.DataFrame())

    @pytest.mark.unit()
    def test_missing_maturity_column_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that missing maturity column raises."""
        df = pl.DataFrame({"Yield": [0.03, 0.04]})
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = df)

    @pytest.mark.unit()
    def test_missing_yield_column_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that missing yield column raises."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0]})
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = df)

    @pytest.mark.unit()
    def test_nan_maturity_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that nan maturity raises."""
        df = pl.DataFrame({"Maturity": [1.0, float("nan")], "Yield": [0.03, 0.04]})
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = df)

    @pytest.mark.unit()
    def test_nan_yield_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that nan yield raises."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0], "Yield": [0.03, float("nan")]})
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = df)

    @pytest.mark.unit()
    def test_non_positive_maturity_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that non positive maturity raises."""
        df = pl.DataFrame({"Maturity": [0.0, 5.0], "Yield": [0.03, 0.04]})
        with pytest.raises(Exception_Validation_Input):
            model._validate_yield_curve_data(data = df)

    @pytest.mark.unit()
    def test_negative_yield_permitted(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that negative yield permitted."""
        # Negative yields are financially valid (Japan, Europe)
        df = pl.DataFrame({"Maturity": [1.0, 5.0], "Yield": [-0.005, -0.002]})
        model._validate_yield_curve_data(data = df)  # should not raise


# =============================================================================
# Tests: _check_is_fitted
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseCheckFitted:
    """Tests for the _check_is_fitted helper."""

    @pytest.mark.unit()
    def test_raises_when_not_fitted(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that raises when not fitted."""
        with pytest.raises(Exception_Calculation):
            model._check_is_fitted()

    @pytest.mark.unit()
    def test_passes_when_fitted(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that passes when fitted."""
        fitted_model._check_is_fitted()  # should not raise


# =============================================================================
# Tests: _resolve_maturities
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseResolveMaturities:
    """Tests for the _resolve_maturities helper."""

    @pytest.mark.unit()
    def test_explicit_list_returned_as_array(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that explicit list returned as array."""
        taus = model._resolve_maturities(maturities = [1.0, 5.0, 10.0], n_points = 50, max_maturity = 30.0)
        assert list(taus) == pytest.approx([1.0, 5.0, 10.0])

    @pytest.mark.unit()
    def test_explicit_array_accepted(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that explicit array accepted."""
        arr = np.array([2.0, 7.0])
        taus = model._resolve_maturities(maturities = arr, n_points = 50, max_maturity = 30.0)
        assert len(taus) == 2

    @pytest.mark.unit()
    def test_none_generates_grid(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that none generates grid."""
        taus = model._resolve_maturities(maturities = None, n_points = 20, max_maturity = 30.0)
        assert len(taus) == 20

    @pytest.mark.unit()
    def test_grid_starts_at_quarter_year(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that grid starts at quarter year."""
        taus = model._resolve_maturities(maturities = None, n_points = 50, max_maturity = 30.0)
        assert taus[0] == pytest.approx(0.25, rel=1e-6)

    @pytest.mark.unit()
    def test_grid_ends_at_max_maturity(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that grid ends at max maturity."""
        taus = model._resolve_maturities(maturities = None, n_points = 50, max_maturity = 30.0)
        assert taus[-1] == pytest.approx(30.0, rel=1e-6)

    @pytest.mark.unit()
    def test_grid_log_spaced_monotone(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that grid log spaced monotone."""
        taus = model._resolve_maturities(maturities = None, n_points = 20, max_maturity = 30.0)
        assert all(taus[i] < taus[i + 1] for i in range(len(taus) - 1))

    @pytest.mark.unit()
    def test_zero_n_points_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that zero n points raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = None, n_points = 0, max_maturity = 30.0)

    @pytest.mark.unit()
    def test_negative_n_points_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that negative n points raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = None, n_points = -5, max_maturity = 30.0)

    @pytest.mark.unit()
    def test_zero_max_maturity_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that zero max maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = None, n_points = 50, max_maturity = 0.0)

    @pytest.mark.unit()
    def test_negative_max_maturity_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that negative max maturity raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = None, n_points = 50, max_maturity = -10.0)

    @pytest.mark.unit()
    def Test_Max_Maturity_Below_Quarter_Year_Raises(
        self,
        model: _ConcreteYieldCurveModel,
    ) -> None:
        """Generated grids must not accept an upper bound below 0.25 years."""
        with pytest.raises(Exception_Validation_Input, match="0.25"):
            model._resolve_maturities(maturities = None, n_points = 50, max_maturity = 0.10)

    @pytest.mark.unit()
    def test_maturities_with_zero_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that maturities with zero raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = [0.0, 1.0, 5.0], n_points = 50, max_maturity = 30.0)

    @pytest.mark.unit()
    def test_maturities_with_nan_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that maturities with nan raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = [1.0, float("nan")], n_points = 50, max_maturity = 30.0)

    @pytest.mark.unit()
    def test_empty_list_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that empty list raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = [], n_points = 50, max_maturity = 30.0)

    @pytest.mark.unit()
    def test_non_convertible_maturities_raises(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that maturities with non-float-convertible values raises."""
        with pytest.raises(Exception_Validation_Input):
            model._resolve_maturities(maturities = ["not_a_float", "also_bad"], n_points = 50, max_maturity = 30.0)


# =============================================================================
# Tests: get_summary_statistics
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseSummaryStatistics:
    """Tests for get_summary_statistics utility method."""

    @pytest.mark.unit()
    def test_returns_dataframe(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that returns dataframe."""
        df = fitted_model.predict(maturities=[1.0, 5.0, 10.0])
        stats = fitted_model.get_summary_statistics(df_predict = df)
        assert isinstance(stats, pl.DataFrame)

    @pytest.mark.unit()
    def test_single_row_output(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that single row output."""
        df = fitted_model.predict(maturities=[1.0, 5.0, 10.0])
        stats = fitted_model.get_summary_statistics(df_predict = df)
        assert len(stats) == 1

    @pytest.mark.unit()
    def test_output_has_required_columns(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that output has required columns."""
        df = fitted_model.predict(maturities=[1.0, 5.0, 10.0])
        stats = fitted_model.get_summary_statistics(df_predict = df)
        for col in ("Mean", "Median", "Std", "Min", "Max", "P5", "P95"):
            assert col in stats.columns

    @pytest.mark.unit()
    def test_constant_yield_zero_std(self) -> None:
        """Test that constant yield zero std."""
        # All yields equal -> std should be 0
        df = pl.DataFrame({"Maturity": [1.0, 5.0, 10.0], "Yield": [0.04, 0.04, 0.04]})
        m = _ConcreteYieldCurveModel()
        stats = m.get_summary_statistics(df_predict = df)
        assert stats["Std"][0] == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_mean_correct(self) -> None:
        """Test that mean correct."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0], "Yield": [0.02, 0.06]})
        m = _ConcreteYieldCurveModel()
        stats = m.get_summary_statistics(df_predict = df)
        assert stats["Mean"][0] == pytest.approx(0.04, abs=1e-12)

    @pytest.mark.unit()
    def test_min_max_correct(self) -> None:
        """Test that min max correct."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0, 10.0], "Yield": [0.01, 0.04, 0.07]})
        m = _ConcreteYieldCurveModel()
        stats = m.get_summary_statistics(df_predict = df)
        assert stats["Min"][0] == pytest.approx(0.01)
        assert stats["Max"][0] == pytest.approx(0.07)

    @pytest.mark.unit()
    def test_missing_yield_column_raises(self) -> None:
        """Test that missing yield column raises."""
        df = pl.DataFrame({"Maturity": [1.0, 5.0]})
        m = _ConcreteYieldCurveModel()
        with pytest.raises(Exception_Validation_Input):
            m.get_summary_statistics(df_predict = df)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestYieldCurveModelBaseRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_name(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that repr contains name."""
        assert "Yield Curve Model" in repr(model)

    @pytest.mark.unit()
    def test_repr_contains_status(self, model: _ConcreteYieldCurveModel) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(model)

    @pytest.mark.unit()
    def test_repr_fitted_status(self, fitted_model: _ConcreteYieldCurveModel) -> None:
        """Test that repr fitted status."""
        assert "Fitted" in repr(fitted_model)
