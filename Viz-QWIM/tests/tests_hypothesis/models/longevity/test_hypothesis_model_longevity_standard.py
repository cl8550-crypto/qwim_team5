"""Hypothesis (property-based) tests for Longevity_Model_Standard.

Tests cover:
- Constructor parameter validation (B > 0, b > 0)
- predict() shape, column names, and structural invariants
- survival column starts at 1.0 and is non-increasing
- qx values lie in (0, 1)
- get_life_expectancy() returns positive finite float
- Life expectancy monotonically decreases with starting age (over a range)
"""

from __future__ import annotations

import math

import polars as pl
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.longevity.model_longevity_standard import Longevity_Model_Standard
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PARAM_B = st.floats(min_value=1e-7, max_value=1e-2, allow_nan=False, allow_infinity=False)
_PARAM_b = st.floats(min_value=0.01, max_value=0.30, allow_nan=False, allow_infinity=False)


def _fitted_model(B: float = 5e-5, b: float = 0.09) -> Longevity_Model_Standard:
    """Return a model fitted from a synthetic life table."""
    model = Longevity_Model_Standard(B=B, b=b)
    ages = list(range(50, 90))
    qx_vals = [
        min(1.0 - math.exp(-B / b * math.exp(b * a) * (math.exp(b) - 1.0)), 0.99)
        for a in ages
    ]
    data = pl.DataFrame({"Age": ages, "qx": qx_vals})
    model.fit(data = data)
    return model


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Longevity_Standard_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Standard_Construction:
    """Tests for Longevity_Model_Standard constructor."""

    @pytest.mark.unit()
    @given(B_val=_PARAM_B, b_val=_PARAM_b)
    @settings(max_examples=200)
    def Test_valid_parameters_stored(self, B_val: float, b_val: float) -> None:
        """m_B and m_b store the constructor values."""
        model = Longevity_Model_Standard(B=B_val, b=b_val)
        assert math.isclose(model.m_B, B_val)
        assert math.isclose(model.m_b, b_val)

    @pytest.mark.unit()
    @given(b_val=_PARAM_b)
    @settings(max_examples=200)
    def Test_invalid_B_zero_raises(self, b_val: float) -> None:
        """B=0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=0.0, b=b_val)

    @pytest.mark.unit()
    @given(invalid_B=st.booleans(), b_val=_PARAM_b)
    @settings(max_examples=20)
    def Test_invalid_B_bool_raises(self, invalid_B: bool, b_val: float) -> None:
        """Boolean B values raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=invalid_B, b=b_val)

    @pytest.mark.unit()
    @given(B_val=_PARAM_B)
    @settings(max_examples=200)
    def Test_invalid_b_zero_raises(self, B_val: float) -> None:
        """b=0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=B_val, b=0.0)

    @pytest.mark.unit()
    @given(B_val=_PARAM_B, invalid_b=st.booleans())
    @settings(max_examples=20)
    def Test_invalid_b_bool_raises(self, B_val: float, invalid_b: bool) -> None:
        """Boolean b values raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=B_val, b=invalid_b)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Longevity_Standard_Predict
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Standard_Predict:
    """Tests for predict() structural invariants."""

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=1, max_value=50),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_output_has_correct_row_count(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """predict() returns exactly n_ages rows."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        assert len(df) == n_ages

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=1, max_value=30),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_output_columns_correct(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """predict() returns DataFrame with Age, qx, survival columns."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        assert "Age" in df.columns
        assert "qx" in df.columns
        assert "survival" in df.columns

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=2, max_value=30),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_survival_starts_at_one(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """survival[0] equals 1.0 for any start_age."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        assert math.isclose(df["survival"][0], 1.0, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=2, max_value=30),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_survival_is_non_increasing(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """survival column is non-increasing."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        survival = df["survival"].to_list()
        for idx_i in range(1, len(survival)):
            assert survival[idx_i] <= survival[idx_i - 1] + 1e-12

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=1, max_value=30),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_qx_values_in_unit_interval(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """All qx values lie in (0, 1)."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        for item_q in df["qx"].to_list():
            assert 0.0 < item_q < 1.0

    @pytest.mark.unit()
    @given(
        n_ages=st.integers(min_value=1, max_value=30),
        start_age=st.integers(min_value=0, max_value=80),
    )
    @settings(max_examples=200)
    def Test_age_column_is_sequential(
        self,
        n_ages: int,
        start_age: int,
    ) -> None:
        """Age column equals [start_age, start_age+1, ..., start_age+n_ages-1]."""
        model = _fitted_model()
        df = model.predict(n_ages=n_ages, start_age=start_age)
        ages = df["Age"].to_list()
        expected = list(range(start_age, start_age + n_ages))
        assert ages == expected


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Longevity_Standard_Life_Expectancy
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Standard_Life_Expectancy:
    """Tests for get_life_expectancy() invariants."""

    @pytest.mark.unit()
    @given(current_age=st.integers(min_value=0, max_value=100))
    @settings(max_examples=200)
    def Test_life_expectancy_positive_finite(self, current_age: int) -> None:
        """get_life_expectancy() always returns a positive finite float."""
        model = _fitted_model()
        ex = model.get_life_expectancy(current_age=current_age)
        assert math.isfinite(ex)
        assert ex > 0

    @pytest.mark.unit()
    @given(
        age_a=st.integers(min_value=0, max_value=60),
        age_b=st.integers(min_value=61, max_value=90),
    )
    @settings(max_examples=200)
    def Test_life_expectancy_decreases_with_age(
        self,
        age_a: int,
        age_b: int,
    ) -> None:
        """Younger age should have higher life expectancy than older age."""
        model = _fitted_model()
        ex_a = model.get_life_expectancy(current_age=age_a)
        ex_b = model.get_life_expectancy(current_age=age_b)
        assert ex_a > ex_b


class Class_Test_Hypothesis_Longevity_Standard_Analytical_Guards:
    """Tests for boolean rejection on analytical helper inputs."""

    @pytest.mark.unit()
    @given(invalid_t_years=st.booleans())
    @settings(max_examples=2)
    def Test_survival_probability_bool_t_years_raises(
        self,
        invalid_t_years: bool,
    ) -> None:
        """Boolean t_years values raise Exception_Validation_Input."""
        model = _fitted_model()

        with pytest.raises(Exception_Validation_Input):
            model.survival_probability(current_age=65, t_years=invalid_t_years)

    @pytest.mark.unit()
    @given(invalid_age=st.booleans())
    @settings(max_examples=2)
    def Test_force_of_mortality_bool_age_raises(
        self,
        invalid_age: bool,
    ) -> None:
        """Boolean age values raise Exception_Validation_Input."""
        model = _fitted_model()

        with pytest.raises(Exception_Validation_Input):
            model.get_force_of_mortality(age = invalid_age)
