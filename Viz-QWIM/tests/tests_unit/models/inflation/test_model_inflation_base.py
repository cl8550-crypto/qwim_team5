"""Tests for the Inflation_Model_Base abstract base class.

Covers construction guards, shared validation helpers, and the
`get_summary_statistics` utility via a concrete stub subclass.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.inflation.model_inflation_base import (
    Inflation_Model_Base,
    INFLATION_MODEL_STATUS_FITTED,
    Inflation_Model_Status,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Concrete stub used throughout all base-class tests
# =============================================================================


class _ConcreteInflationModel(Inflation_Model_Base):
    """Minimal concrete subclass for testing the abstract base."""

    def fit(self, data: pl.DataFrame) -> "_ConcreteInflationModel":
        """Fit."""
        self.m_status = INFLATION_MODEL_STATUS_FITTED
        self.m_parameters = {"rate": 0.025}
        return self

    def predict(
        self,
        n_periods: int,
        start_date: str | None = None,
        freq: str = "1mo",
    ) -> pl.DataFrame:
        """Predict."""
        self._check_is_fitted()
        self._validate_n_periods(n_periods = n_periods)
        return pl.DataFrame({"Date": ["2025-01-01"] * n_periods, "inflation_rate": [0.025] * n_periods})

    def get_annual_rate(self) -> float:
        """Get annual rate."""
        self._check_is_fitted()
        return 0.025


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def stub_model() -> _ConcreteInflationModel:
    """Return a concrete stub model in NOT_FITTED state."""
    return _ConcreteInflationModel(name_model="Test Model")


@pytest.fixture()
def fitted_stub_model() -> _ConcreteInflationModel:
    """Return a concrete stub model in FITTED state."""
    m = _ConcreteInflationModel(name_model="Fitted Model")
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def valid_inflation_data() -> pl.DataFrame:
    """Return a small valid historical inflation DataFrame."""
    return pl.DataFrame(
        {
            "Date": ["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"],
            "inflation_rate": [0.023, 0.024, 0.070, 0.040],
        }
    )


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit
class TestInflationModelBaseConstruction:
    """Tests for abstract base class construction validation."""

    @pytest.mark.unit()
    def test_valid_name_accepted(self) -> None:
        """Test that valid name accepted."""
        model = _ConcreteInflationModel(name_model="My Model")
        assert model.name_model == "My Model"

    @pytest.mark.unit()
    def test_name_stripped(self) -> None:
        """Test that name stripped."""
        model = _ConcreteInflationModel(name_model="  Padded Name  ")
        assert model.name_model == "Padded Name"

    @pytest.mark.unit()
    def test_default_status_not_fitted(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that default status not fitted."""
        assert stub_model.status == Inflation_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_default_parameters_empty(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that default parameters empty."""
        assert stub_model.parameters == {}

    @pytest.mark.unit()
    def test_invalid_name_empty_string_raises(self) -> None:
        """Test that invalid name empty string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteInflationModel(name_model="")

    @pytest.mark.unit()
    def test_invalid_name_whitespace_raises(self) -> None:
        """Test that invalid name whitespace raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteInflationModel(name_model="   ")

    @pytest.mark.unit()
    def test_invalid_name_non_string_raises(self) -> None:
        """Test that invalid name non string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteInflationModel(name_model=123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_abstract_class_not_instantiable_directly(self) -> None:
        """Test that abstract class not instantiable directly."""
        with pytest.raises(TypeError):
            Inflation_Model_Base()  # type: ignore[abstract]


# =============================================================================
# Tests: properties
# =============================================================================


@pytest.mark.unit
class TestInflationModelBaseProperties:
    """Tests for abstract base class properties."""

    @pytest.mark.unit()
    def test_is_fitted_false_before_fit(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that is fitted false before fit."""
        assert stub_model.is_fitted is False

    @pytest.mark.unit()
    def test_is_fitted_true_after_fit(self, fitted_stub_model: _ConcreteInflationModel) -> None:
        """Test that is fitted true after fit."""
        assert fitted_stub_model.is_fitted is True

    @pytest.mark.unit()
    def test_status_fitted_after_fit(self, fitted_stub_model: _ConcreteInflationModel) -> None:
        """Test that status fitted after fit."""
        assert fitted_stub_model.status == Inflation_Model_Status.FITTED

    @pytest.mark.unit()
    def test_parameters_copy_returned(self, fitted_stub_model: _ConcreteInflationModel) -> None:
        """Test that parameters copy returned."""
        params = fitted_stub_model.parameters
        params["injected"] = 99.0
        assert "injected" not in fitted_stub_model.parameters

    @pytest.mark.unit()
    def test_name_model_unchanged(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that name model unchanged."""
        assert stub_model.name_model == "Test Model"


# =============================================================================
# Tests: validation helpers
# =============================================================================


@pytest.mark.unit
class TestInflationModelBaseValidation:
    """Tests for shared validation helpers."""

    @pytest.mark.unit()
    def test_validate_n_periods_valid(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that validate n periods valid."""
        stub_model._validate_n_periods(n_periods = 1)
        stub_model._validate_n_periods(n_periods = 100)

    @pytest.mark.unit()
    def test_validate_n_periods_zero_raises(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that validate n periods zero raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_periods(n_periods = 0)

    @pytest.mark.unit()
    def test_validate_n_periods_negative_raises(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that validate n periods negative raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_periods(n_periods = -5)

    @pytest.mark.unit()
    def test_validate_n_periods_float_raises(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that validate n periods float raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_periods(n_periods = 3.5)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Validate_N_Periods_Bool_Raises(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that validate n periods bool raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_periods(n_periods = True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_validate_inflation_data_valid(
        self,
        stub_model: _ConcreteInflationModel,
        valid_inflation_data: pl.DataFrame,
    ) -> None:
        """Test that validate inflation data valid."""
        # Should not raise
        stub_model._validate_inflation_data(data = valid_inflation_data)

    @pytest.mark.unit()
    def test_validate_inflation_data_not_dataframe_raises(
        self, stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that validate inflation data not dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_inflation_data(data = {"Date": [], "inflation_rate": []})  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_validate_inflation_data_empty_raises(
        self, stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that validate inflation data empty raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_inflation_data(data = pl.DataFrame())

    @pytest.mark.unit()
    def test_validate_inflation_data_missing_date_raises(
        self, stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that validate inflation data missing date raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_inflation_data(data = pl.DataFrame({"inflation_rate": [0.025]}))

    @pytest.mark.unit()
    def test_validate_inflation_data_missing_rate_raises(
        self, stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that validate inflation data missing rate raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_inflation_data(data = pl.DataFrame({"Date": ["2024-01-01"]}))

    @pytest.mark.unit()
    def test_check_is_fitted_raises_when_not_fitted(
        self, stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that check is fitted raises when not fitted."""
        with pytest.raises(Exception_Calculation):
            stub_model._check_is_fitted()

    @pytest.mark.unit()
    def test_check_is_fitted_passes_when_fitted(
        self, fitted_stub_model: _ConcreteInflationModel
    ) -> None:
        """Test that check is fitted passes when fitted."""
        # Should not raise
        fitted_stub_model._check_is_fitted()


# =============================================================================
# Tests: get_summary_statistics
# =============================================================================


@pytest.mark.unit
class TestInflationModelBaseSummaryStatistics:
    """Tests for the shared get_summary_statistics utility."""

    @pytest.mark.unit()
    def test_returns_dataframe(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that returns dataframe."""
        df_pred = pl.DataFrame({"Date": ["2025-01-01", "2025-02-01"], "inflation_rate": [0.02, 0.03]})
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_output_has_required_columns(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that output has required columns."""
        df_pred = pl.DataFrame(
            {"Date": ["2025-01-01", "2025-02-01", "2025-03-01"], "inflation_rate": [0.02, 0.03, 0.025]}
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        expected_cols = {"Mean", "Median", "Std", "Min", "Max", "P5", "P95"}
        assert expected_cols.issubset(set(result.columns))

    @pytest.mark.unit()
    def test_single_row_output(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that single row output."""
        df_pred = pl.DataFrame({"Date": ["2025-01-01", "2025-02-01"], "inflation_rate": [0.02, 0.04]})
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert len(result) == 1

    @pytest.mark.unit()
    def test_mean_correct(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that mean correct."""
        df_pred = pl.DataFrame(
            {"Date": ["2025-01-01", "2025-02-01", "2025-03-01"], "inflation_rate": [0.02, 0.04, 0.03]}
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Mean"][0] == pytest.approx(0.03, abs=1e-10)

    @pytest.mark.unit()
    def test_constant_rates_zero_std(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that constant rates zero std."""
        df_pred = pl.DataFrame(
            {
                "Date": ["2025-01-01", "2025-02-01", "2025-03-01"],
                "inflation_rate": [0.025, 0.025, 0.025],
            }
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Std"][0] == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_min_max_correct(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that min max correct."""
        df_pred = pl.DataFrame(
            {
                "Date": ["2025-01-01", "2025-02-01", "2025-03-01"],
                "inflation_rate": [0.01, 0.05, 0.03],
            }
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Min"][0] == pytest.approx(0.01, abs=1e-12)
        assert result["Max"][0] == pytest.approx(0.05, abs=1e-12)

    @pytest.mark.unit()
    def test_missing_inflation_rate_column_raises(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that missing inflation rate column raises."""
        df_invalid = pl.DataFrame({"Date": ["2025-01-01"], "other_col": [0.025]})
        with pytest.raises(Exception_Validation_Input):
            stub_model.get_summary_statistics(df_predict = df_invalid)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit
class TestInflationModelBaseRepr:
    """Tests for __repr__ string formatting."""

    @pytest.mark.unit()
    def test_repr_contains_name(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that repr contains name."""
        r = repr(stub_model)
        assert "Test Model" in r

    @pytest.mark.unit()
    def test_repr_contains_status(self, stub_model: _ConcreteInflationModel) -> None:
        """Test that repr contains status."""
        r = repr(stub_model)
        assert "Not Fitted" in r

    @pytest.mark.unit()
    def test_repr_fitted_status(self, fitted_stub_model: _ConcreteInflationModel) -> None:
        """Test that repr fitted status."""
        r = repr(fitted_stub_model)
        assert "Fitted" in r
