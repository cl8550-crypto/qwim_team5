"""Tests for Longevity_Model_Constant (constant-mortality model).

Covers construction, fit() with and without historical data, predict(),
get_life_expectancy(), and survival_probability().
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.longevity.model_longevity_base import Longevity_Model_Status
from src.models.longevity.model_longevity_constant import Longevity_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def default_model() -> Longevity_Model_Constant:
    """Return an unfitted constant model with default qx (1 %)."""
    return Longevity_Model_Constant()


@pytest.fixture()
def fitted_default_model() -> Longevity_Model_Constant:
    """Return a constant model fitted without historical data."""
    m = Longevity_Model_Constant()
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def life_table_data() -> pl.DataFrame:
    """Return a small historical mortality life-table DataFrame."""
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
class TestLongevityModelConstantConstruction:
    """Tests for Longevity_Model_Constant constructor."""

    @pytest.mark.unit()
    def test_default_qx_stored(self, default_model: Longevity_Model_Constant) -> None:
        """Test that default qx stored."""
        assert default_model.m_qx == pytest.approx(0.01, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_qx_stored(self) -> None:
        """Test that custom qx stored."""
        m = Longevity_Model_Constant(qx=0.02)
        assert m.m_qx == pytest.approx(0.02, abs=1e-12)

    @pytest.mark.unit()
    def test_qx_at_minimum_boundary_accepted(self) -> None:
        """Test that qx at minimum boundary accepted."""
        m = Longevity_Model_Constant(qx=1e-6)
        assert m.m_qx == pytest.approx(1e-6, rel=1e-6)

    @pytest.mark.unit()
    def test_qx_at_maximum_boundary_accepted(self) -> None:
        """Test that qx at maximum boundary accepted."""
        m = Longevity_Model_Constant(qx=0.5)
        assert m.m_qx == pytest.approx(0.5, abs=1e-12)

    @pytest.mark.unit()
    def test_qx_below_minimum_raises(self) -> None:
        """Test that qx below minimum raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=0.0)  # exactly zero is below _QX_MIN

    @pytest.mark.unit()
    def test_qx_above_maximum_raises(self) -> None:
        """Test that qx above maximum raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=0.6)

    @pytest.mark.unit()
    def test_qx_negative_raises(self) -> None:
        """Test that qx negative raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=-0.01)

    @pytest.mark.unit()
    def test_nan_qx_raises(self) -> None:
        """Test that nan qx raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=float("nan"))

    @pytest.mark.unit()
    def Test_Reject_Bool_Qx(self) -> None:
        """Test that reject bool qx."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_inf_qx_raises(self) -> None:
        """Test that inf qx raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=float("inf"))

    @pytest.mark.unit()
    def test_default_status_not_fitted(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that default status not fitted."""
        assert default_model.status == Longevity_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Longevity_Model_Constant) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Longevity_Model_Constant(name_model="SSA 2019 Baseline")
        assert m.name_model == "SSA 2019 Baseline"


# =============================================================================
# Tests: fit — no historical data
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantFitNoData:
    """Tests for fit() with empty DataFrame."""

    @pytest.mark.unit()
    def test_fit_empty_data_returns_self(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit empty data returns self."""
        result = default_model.fit(data = pl.DataFrame())
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_empty_data_sets_fitted(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit empty data sets fitted."""
        default_model.fit(data = pl.DataFrame())
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_empty_data_preserves_qx(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit empty data preserves qx."""
        original_qx = default_model.m_qx
        default_model.fit(data = pl.DataFrame())
        assert default_model.m_qx == pytest.approx(original_qx, abs=1e-12)

    @pytest.mark.unit()
    def test_fit_invalid_type_raises(self, default_model: Longevity_Model_Constant) -> None:
        """Test that fit invalid type raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = [0.01, 0.02])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit sets parameters dict."""
        params = fitted_default_model.parameters
        assert "qx" in params
        assert params["qx"] == pytest.approx(0.01, abs=1e-12)


# =============================================================================
# Tests: fit — with historical data
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantFitWithData:
    """Tests for fit() with a historical mortality DataFrame."""

    @pytest.mark.unit()
    def test_fit_estimates_mean(
        self,
        default_model: Longevity_Model_Constant,
        life_table_data: pl.DataFrame,
    ) -> None:
        """Test that fit estimates mean."""
        default_model.fit(data = life_table_data)
        expected_mean = float(np.mean([0.010, 0.014, 0.021, 0.032]))
        assert default_model.m_qx == pytest.approx(expected_mean, abs=1e-10)

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        default_model: Longevity_Model_Constant,
        life_table_data: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = default_model.fit(data = life_table_data)
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        default_model: Longevity_Model_Constant,
        life_table_data: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        default_model.fit(data = life_table_data)
        assert default_model.status == Longevity_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_missing_age_column_raises(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit missing age column raises."""
        bad_data = pl.DataFrame({"qx": [0.01, 0.02]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_missing_qx_column_raises(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that fit missing qx column raises."""
        bad_data = pl.DataFrame({"Age": [65, 70]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_nan_values_raises(self, default_model: Longevity_Model_Constant) -> None:
        """Test that fit nan values raises."""
        bad_data = pl.DataFrame(
            {
                "Age": [65, 70],
                "qx": [0.01, float("nan")],
            },
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_single_observation(self, default_model: Longevity_Model_Constant) -> None:
        """Test that fit single observation."""
        single = pl.DataFrame({"Age": [65], "qx": [0.02]})
        default_model.fit(data = single)
        assert default_model.m_qx == pytest.approx(0.02, abs=1e-10)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantPredict:
    """Tests for the predict() method."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_default_model.predict(n_ages=6)
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict correct length."""
        df = fitted_default_model.predict(n_ages=20)
        assert len(df) == 20

    @pytest.mark.unit()
    def test_predict_has_age_column(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict has age column."""
        df = fitted_default_model.predict(n_ages=3)
        assert "Age" in df.columns

    @pytest.mark.unit()
    def test_predict_has_qx_column(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict has qx column."""
        df = fitted_default_model.predict(n_ages=3)
        assert "qx" in df.columns

    @pytest.mark.unit()
    def test_predict_constant_values(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict constant values."""
        df = fitted_default_model.predict(n_ages=5)
        qx_vals = df["qx"].to_list()
        assert all(q == pytest.approx(0.01, abs=1e-12) for q in qx_vals)

    @pytest.mark.unit()
    def test_predict_ages_start_at_zero_by_default(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict ages start at zero by default."""
        df = fitted_default_model.predict(n_ages=5)
        assert df["Age"][0] == 0

    @pytest.mark.unit()
    def test_predict_ages_correct_range(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict ages correct range."""
        df = fitted_default_model.predict(n_ages=5, start_age=65)
        assert df["Age"].to_list() == [65, 66, 67, 68, 69]

    @pytest.mark.unit()
    def test_predict_custom_start_age(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict custom start age."""
        df = fitted_default_model.predict(n_ages=3, start_age=80)
        assert df["Age"][0] == 80

    @pytest.mark.unit()
    def test_predict_before_fit_raises(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(n_ages=6)

    @pytest.mark.unit()
    def test_predict_zero_ages_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict zero ages raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_ages=0)

    @pytest.mark.unit()
    def test_predict_negative_start_age_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that predict negative start age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.predict(n_ages=5, start_age=-1)

    @pytest.mark.unit()
    def test_predict_with_custom_qx(self) -> None:
        """Test that predict with custom qx."""
        m = Longevity_Model_Constant(qx=0.03)
        m.fit(data = pl.DataFrame())
        df = m.predict(n_ages=4)
        assert all(q == pytest.approx(0.03, abs=1e-12) for q in df["qx"].to_list())


# =============================================================================
# Tests: get_life_expectancy
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantLifeExpectancy:
    """Tests for get_life_expectancy()."""

    @pytest.mark.unit()
    def test_returns_positive_value(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that returns positive value."""
        ex = fitted_default_model.get_life_expectancy()
        assert ex > 0

    @pytest.mark.unit()
    def test_exact_geometric_series_formula(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that exact geometric series formula."""
        # e_x = (1 - qx) / qx for constant qx (geometric series)
        qx = fitted_default_model.m_qx
        expected = (1.0 - qx) / qx
        assert fitted_default_model.get_life_expectancy() == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit()
    def test_age_independent(self, fitted_default_model: Longevity_Model_Constant) -> None:
        """Test that age independent."""
        # Under constant mortality, life expectancy is age-independent
        e0 = fitted_default_model.get_life_expectancy(current_age=0)
        e65 = fitted_default_model.get_life_expectancy(current_age=65)
        assert e0 == pytest.approx(e65, abs=1e-10)

    @pytest.mark.unit()
    def test_higher_qx_lower_expectancy(self) -> None:
        """Test that higher qx lower expectancy."""
        low_q = Longevity_Model_Constant(qx=0.01)
        high_q = Longevity_Model_Constant(qx=0.05)
        for m in (low_q, high_q):
            m.fit(data = pl.DataFrame())
        assert low_q.get_life_expectancy() > high_q.get_life_expectancy()

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Longevity_Model_Constant) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_life_expectancy()

    @pytest.mark.unit()
    def test_negative_age_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that negative age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.get_life_expectancy(current_age=-1)


# =============================================================================
# Tests: survival_probability
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantSurvivalProbability:
    """Tests for survival_probability()."""

    @pytest.mark.unit()
    def test_one_year_survival(self, fitted_default_model: Longevity_Model_Constant) -> None:
        """Test that one year survival."""
        # P(survive 1 year) = 1 - qx = 0.99
        prob = fitted_default_model.survival_probability(current_age=65, t_years=1.0)
        assert prob == pytest.approx(0.99, abs=1e-10)

    @pytest.mark.unit()
    def test_zero_years_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that zero years raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.survival_probability(current_age=65, t_years=0.0)

    @pytest.mark.unit()
    def test_negative_years_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that negative years raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.survival_probability(current_age=65, t_years=-1.0)

    @pytest.mark.unit()
    def test_exponential_decay_formula(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that exponential decay formula."""
        # P(survive t years) = (1 - qx)^t
        qx = fitted_default_model.m_qx
        for t in [1.0, 5.0, 10.0, 20.0]:
            expected = (1.0 - qx) ** t
            actual = fitted_default_model.survival_probability(current_age=0, t_years=t)
            assert actual == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit()
    def test_probability_declines_with_time(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that probability declines with time."""
        probs = [
            fitted_default_model.survival_probability(current_age=65, t_years=float(t))
            for t in [1, 5, 10, 20]
        ]
        assert probs == sorted(probs, reverse=True)

    @pytest.mark.unit()
    def test_probability_in_unit_interval(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that probability in unit interval."""
        prob = fitted_default_model.survival_probability(current_age=65, t_years=10.0)
        assert 0.0 <= prob <= 1.0

    @pytest.mark.unit()
    def test_age_independent_for_constant_model(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that age independent for constant model."""
        # Under constant mortality, survival probability is age-independent
        p0 = fitted_default_model.survival_probability(current_age=0, t_years=10.0)
        p60 = fitted_default_model.survival_probability(current_age=60, t_years=10.0)
        assert p0 == pytest.approx(p60, abs=1e-10)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Longevity_Model_Constant) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.survival_probability(current_age=65, t_years=10.0)

    @pytest.mark.unit()
    def test_negative_age_raises(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that negative age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_default_model.survival_probability(current_age=-1, t_years=10.0)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelConstantRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(
        self,
        default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that repr contains class name."""
        assert "Longevity_Model_Constant" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_qx(self, default_model: Longevity_Model_Constant) -> None:
        """Test that repr contains qx."""
        assert "0.010000" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_status(self, default_model: Longevity_Model_Constant) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_fitted_contains_fitted(
        self,
        fitted_default_model: Longevity_Model_Constant,
    ) -> None:
        """Test that repr fitted contains fitted."""
        assert "Fitted" in repr(fitted_default_model)
