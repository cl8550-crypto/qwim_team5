"""Tests for the Longevity_Model_Base abstract base class.

Covers construction guards, shared validation helpers, and the
``get_summary_statistics`` utility via a concrete stub subclass.
"""

from __future__ import annotations

import polars as pl
import pytest

from src.models.longevity.model_longevity_base import (
    LONGEVITY_MODEL_STATUS_FITTED,
    Longevity_Model_Base,
    Longevity_Model_Status,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Concrete stub used throughout all base-class tests
# =============================================================================


class _ConcreteLongevityModel(Longevity_Model_Base):
    """Minimal concrete subclass for testing the abstract base."""

    def fit(self, data: pl.DataFrame) -> _ConcreteLongevityModel:
        """Fit."""
        self.m_status = LONGEVITY_MODEL_STATUS_FITTED
        self.m_parameters = {"qx": 0.01}
        return self

    def predict(self, n_ages: int, start_age: int = 0) -> pl.DataFrame:
        """Predict."""
        self._check_is_fitted()
        self._validate_n_ages(n_ages = n_ages)
        self._validate_age(age = start_age)
        ages = list(range(start_age, start_age + n_ages))
        return pl.DataFrame(
            {
                "Age": ages,
                "qx": [0.01] * n_ages,
            },
        )

    def get_life_expectancy(self, current_age: int = 0) -> float:
        """Get life expectancy."""
        self._check_is_fitted()
        self._validate_age(age = current_age)
        return 99.0  # stub

    def survival_probability(self, current_age: int, t_years: float) -> float:
        """Survival probability."""
        self._check_is_fitted()
        self._validate_age(age = current_age)
        return 0.99**t_years  # stub


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def stub_model() -> _ConcreteLongevityModel:
    """Return a concrete stub model in NOT_FITTED state."""
    return _ConcreteLongevityModel(name_model="Test Model")


@pytest.fixture()
def fitted_stub_model() -> _ConcreteLongevityModel:
    """Return a concrete stub model in FITTED state."""
    m = _ConcreteLongevityModel(name_model="Fitted Model")
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def valid_mortality_data() -> pl.DataFrame:
    """Return a small valid historical mortality DataFrame."""
    return pl.DataFrame(
        {
            "Age": [60, 65, 70, 75],
            "qx": [0.010, 0.014, 0.021, 0.032],
        },
    )


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelBaseConstruction:
    """Tests for abstract base class construction validation."""

    @pytest.mark.unit()
    def test_valid_name_accepted(self) -> None:
        """Test that valid name accepted."""
        model = _ConcreteLongevityModel(name_model="My Longevity Model")
        assert model.name_model == "My Longevity Model"

    @pytest.mark.unit()
    def test_name_stripped(self) -> None:
        """Test that name stripped."""
        model = _ConcreteLongevityModel(name_model="  Padded Name  ")
        assert model.name_model == "Padded Name"

    @pytest.mark.unit()
    def test_default_status_not_fitted(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that default status not fitted."""
        assert stub_model.status == Longevity_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_default_parameters_empty(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that default parameters empty."""
        assert stub_model.parameters == {}

    @pytest.mark.unit()
    def test_invalid_name_empty_string_raises(self) -> None:
        """Test that invalid name empty string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteLongevityModel(name_model="")

    @pytest.mark.unit()
    def test_invalid_name_whitespace_raises(self) -> None:
        """Test that invalid name whitespace raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteLongevityModel(name_model="   ")

    @pytest.mark.unit()
    def test_invalid_name_non_string_raises(self) -> None:
        """Test that invalid name non string raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteLongevityModel(name_model=123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_abstract_class_not_instantiable_directly(self) -> None:
        """Test that abstract class not instantiable directly."""
        with pytest.raises(TypeError):
            Longevity_Model_Base()  # type: ignore[abstract]


# =============================================================================
# Tests: properties
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelBaseProperties:
    """Tests for abstract base class properties."""

    @pytest.mark.unit()
    def test_is_fitted_false_before_fit(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that is fitted false before fit."""
        assert stub_model.is_fitted is False

    @pytest.mark.unit()
    def test_is_fitted_true_after_fit(
        self,
        fitted_stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that is fitted true after fit."""
        assert fitted_stub_model.is_fitted is True

    @pytest.mark.unit()
    def test_status_fitted_after_fit(
        self,
        fitted_stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that status fitted after fit."""
        assert fitted_stub_model.status == Longevity_Model_Status.FITTED

    @pytest.mark.unit()
    def test_parameters_copy_returned(
        self,
        fitted_stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that parameters copy returned."""
        params = fitted_stub_model.parameters
        params["injected"] = 99.0
        assert "injected" not in fitted_stub_model.parameters

    @pytest.mark.unit()
    def test_name_model_unchanged(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that name model unchanged."""
        assert stub_model.name_model == "Test Model"


# =============================================================================
# Tests: validation helpers
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelBaseValidation:
    """Tests for shared validation helpers."""

    @pytest.mark.unit()
    def test_validate_n_ages_valid(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate n ages valid."""
        stub_model._validate_n_ages(n_ages = 1)
        stub_model._validate_n_ages(n_ages = 120)

    @pytest.mark.unit()
    def test_validate_n_ages_zero_raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate n ages zero raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_ages(n_ages = 0)

    @pytest.mark.unit()
    def test_validate_n_ages_negative_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate n ages negative raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_ages(n_ages = -5)

    @pytest.mark.unit()
    def test_validate_n_ages_float_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate n ages float raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_ages(n_ages = 3.5)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Validate_N_Ages_Bool_Raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate n ages bool raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_n_ages(n_ages = True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_validate_age_valid_zero(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate age valid zero."""
        stub_model._validate_age(age = 0)  # should not raise

    @pytest.mark.unit()
    def test_validate_age_valid_positive(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate age valid positive."""
        stub_model._validate_age(age = 65)  # should not raise

    @pytest.mark.unit()
    def test_validate_age_negative_raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate age negative raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_age(age = -1)

    @pytest.mark.unit()
    def test_validate_age_float_raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate age float raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_age(age = 65.5)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Validate_Age_Bool_Raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that validate age bool raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_age(age = True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_validate_mortality_data_valid(
        self,
        stub_model: _ConcreteLongevityModel,
        valid_mortality_data: pl.DataFrame,
    ) -> None:
        """Test that validate mortality data valid."""
        stub_model._validate_mortality_data(data = valid_mortality_data)  # should not raise

    @pytest.mark.unit()
    def test_validate_mortality_data_not_dataframe_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate mortality data not dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_mortality_data(data = {"Age": [], "qx": []})  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_validate_mortality_data_empty_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate mortality data empty raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_mortality_data(data = pl.DataFrame())

    @pytest.mark.unit()
    def test_validate_mortality_data_missing_age_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate mortality data missing age raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_mortality_data(data = pl.DataFrame({"qx": [0.01]}))

    @pytest.mark.unit()
    def test_validate_mortality_data_missing_qx_raises(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that validate mortality data missing qx raises."""
        with pytest.raises(Exception_Validation_Input):
            stub_model._validate_mortality_data(data = pl.DataFrame({"Age": [65]}))

    @pytest.mark.unit()
    def test_check_is_fitted_raises_when_not_fitted(
        self,
        stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that check is fitted raises when not fitted."""
        with pytest.raises(Exception_Calculation):
            stub_model._check_is_fitted()

    @pytest.mark.unit()
    def test_check_is_fitted_passes_when_fitted(
        self,
        fitted_stub_model: _ConcreteLongevityModel,
    ) -> None:
        """Test that check is fitted passes when fitted."""
        fitted_stub_model._check_is_fitted()  # should not raise


# =============================================================================
# Tests: get_summary_statistics
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelBaseSummaryStatistics:
    """Tests for the shared get_summary_statistics utility."""

    @pytest.mark.unit()
    def test_returns_dataframe(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that returns dataframe."""
        df_pred = pl.DataFrame(
            {"Age": [65, 66], "qx": [0.01, 0.012]},
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert isinstance(result, pl.DataFrame)

    @pytest.mark.unit()
    def test_output_has_required_columns(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that output has required columns."""
        df_pred = pl.DataFrame(
            {
                "Age": [65, 66, 67],
                "qx": [0.010, 0.012, 0.014],
            },
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        expected_cols = {"Mean", "Median", "Std", "Min", "Max", "P5", "P95"}
        assert expected_cols.issubset(set(result.columns))

    @pytest.mark.unit()
    def test_single_row_output(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that single row output."""
        df_pred = pl.DataFrame(
            {"Age": [65, 66], "qx": [0.01, 0.02]},
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert len(result) == 1

    @pytest.mark.unit()
    def test_mean_correct(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that mean correct."""
        df_pred = pl.DataFrame(
            {
                "Age": [65, 66, 67],
                "qx": [0.01, 0.02, 0.03],
            },
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Mean"][0] == pytest.approx(0.02, abs=1e-10)

    @pytest.mark.unit()
    def test_constant_qx_zero_std(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that constant qx zero std."""
        df_pred = pl.DataFrame(
            {
                "Age": [65, 66, 67],
                "qx": [0.01, 0.01, 0.01],
            },
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Std"][0] == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_min_max_correct(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that min max correct."""
        df_pred = pl.DataFrame(
            {
                "Age": [65, 66, 67],
                "qx": [0.01, 0.05, 0.12],
            },
        )
        result = stub_model.get_summary_statistics(df_predict = df_pred)
        assert result["Min"][0] == pytest.approx(0.01, abs=1e-10)
        assert result["Max"][0] == pytest.approx(0.12, abs=1e-10)

    @pytest.mark.unit()
    def test_missing_qx_column_raises(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that missing qx column raises."""
        df_pred = pl.DataFrame({"Age": [65], "other_col": [0.01]})
        with pytest.raises(Exception_Validation_Input):
            stub_model.get_summary_statistics(df_predict = df_pred)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelBaseRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_name(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that repr contains name."""
        assert "Test Model" in repr(stub_model)

    @pytest.mark.unit()
    def test_repr_contains_status(self, stub_model: _ConcreteLongevityModel) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(stub_model)

    @pytest.mark.unit()
    def test_repr_fitted_status(self, fitted_stub_model: _ConcreteLongevityModel) -> None:
        """Test that repr fitted status."""
        assert "Fitted" in repr(fitted_stub_model)
