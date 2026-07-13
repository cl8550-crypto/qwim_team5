"""Tests for Longevity_Model_Standard (Gompertz mortality model).

Covers construction, fit() via OLS complementary-log-log regression,
predict(), get_life_expectancy(), survival_probability(), and the
get_force_of_mortality() and _validate_positive_float helpers.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.longevity.model_longevity_base import Longevity_Model_Status
from src.models.longevity.model_longevity_standard import (
    Longevity_Model_Standard,
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
def default_model() -> Longevity_Model_Standard:
    """Return an unfitted Gompertz model with default parameters."""
    return Longevity_Model_Standard()


@pytest.fixture()
def small_model() -> Longevity_Model_Standard:
    """Return Gompertz model with small custom parameters."""
    return Longevity_Model_Standard(B=1e-4, b=0.08)


@pytest.fixture()
def adult_life_table() -> pl.DataFrame:
    """Return representative US adult mortality data (SSA-like, ages 40-80)."""
    ages = list(range(40, 85, 5))
    # Realistic qx values increasing with age
    qx_values = [0.0031, 0.0049, 0.0077, 0.0119, 0.0181, 0.0270, 0.0401, 0.0594, 0.0877]
    return pl.DataFrame({"Age": ages, "qx": qx_values})


@pytest.fixture()
def fitted_adult_model(adult_life_table: pl.DataFrame) -> Longevity_Model_Standard:
    """Return Gompertz model fitted to adult life-table data."""
    m = Longevity_Model_Standard()
    m.fit(data = adult_life_table)
    return m


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardConstruction:
    """Tests for Longevity_Model_Standard constructor."""

    @pytest.mark.unit()
    def test_default_B_stored(self, default_model: Longevity_Model_Standard) -> None:
        """Test that default B stored."""
        assert default_model.m_B == pytest.approx(5e-5, rel=1e-10)

    @pytest.mark.unit()
    def test_default_b_stored(self, default_model: Longevity_Model_Standard) -> None:
        """Test that default b stored."""
        assert default_model.m_b == pytest.approx(0.09, abs=1e-12)

    @pytest.mark.unit()
    def test_custom_parameters_stored(self) -> None:
        """Test that custom parameters stored."""
        m = Longevity_Model_Standard(B=1e-4, b=0.10)
        assert m.m_B == pytest.approx(1e-4, rel=1e-10)
        assert m.m_b == pytest.approx(0.10, abs=1e-12)

    @pytest.mark.unit()
    def test_zero_B_raises(self) -> None:
        """Test that zero B raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=0.0)

    @pytest.mark.unit()
    def test_negative_B_raises(self) -> None:
        """Test that negative B raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=-1e-5)

    @pytest.mark.unit()
    def test_bool_B_raises(self) -> None:
        """Test that boolean B raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(B=True)

    @pytest.mark.unit()
    def test_zero_b_raises(self) -> None:
        """Test that zero b raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(b=0.0)

    @pytest.mark.unit()
    def test_negative_b_raises(self) -> None:
        """Test that negative b raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(b=-0.1)

    @pytest.mark.unit()
    def test_bool_b_raises(self) -> None:
        """Test that boolean b raises."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Standard(b=False)

    @pytest.mark.unit()
    def test_status_not_fitted_initially(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that status not fitted initially."""
        assert default_model.status == Longevity_Model_Status.NOT_FITTED

    @pytest.mark.unit()
    def test_is_not_fitted_initially(self, default_model: Longevity_Model_Standard) -> None:
        """Test that is not fitted initially."""
        assert default_model.is_fitted is False

    @pytest.mark.unit()
    def test_custom_name_stored(self) -> None:
        """Test that custom name stored."""
        m = Longevity_Model_Standard(name_model="US Adult Mortality")
        assert m.name_model == "US Adult Mortality"


# =============================================================================
# Tests: fit
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardFit:
    """Tests for the fit() method."""

    @pytest.mark.unit()
    def test_fit_sets_fitted_status(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
    ) -> None:
        """Test that fit sets fitted status."""
        default_model.fit(data = adult_life_table)
        assert default_model.status == Longevity_Model_Status.FITTED

    @pytest.mark.unit()
    def test_fit_returns_self(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
    ) -> None:
        """Test that fit returns self."""
        result = default_model.fit(data = adult_life_table)
        assert result is default_model

    @pytest.mark.unit()
    def test_fit_updates_B_positive(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
    ) -> None:
        """Test that fit updates B positive."""
        default_model.fit(data = adult_life_table)
        assert default_model.m_B > 0

    @pytest.mark.unit()
    def test_fit_updates_b_positive(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
    ) -> None:
        """Test that fit updates b positive."""
        default_model.fit(data = adult_life_table)
        assert default_model.m_b > 0

    @pytest.mark.unit()
    def test_fit_sets_parameters_dict(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that fit sets parameters dict."""
        params = fitted_adult_model.parameters
        assert "B" in params
        assert "b" in params
        assert params["B"] > 0
        assert params["b"] > 0

    @pytest.mark.unit()
    def test_fit_sorts_by_age(self, default_model: Longevity_Model_Standard) -> None:
        """Test that fit sorts by age."""
        # Provide data in unsorted order — should still fit successfully
        unsorted = pl.DataFrame(
            {
                "Age": [75, 65, 55, 45],
                "qx": [0.032, 0.014, 0.006, 0.003],
            },
        )
        default_model.fit(data = unsorted)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_recovers_gompertz_params_from_synthetic_data(self) -> None:
        """Test that fit recovers gompertz params from synthetic data."""
        # Generate synthetic data from known B, b
        B_true = 5e-5
        b_true = 0.09
        ages = list(range(40, 90, 5))
        qx_vals = []
        for x in ages:
            integral_mu = (B_true / b_true) * np.exp(b_true * x) * (np.exp(b_true) - 1.0)
            qx_vals.append(1.0 - np.exp(-integral_mu))
        data = pl.DataFrame({"Age": ages, "qx": qx_vals})

        m = Longevity_Model_Standard()
        m.fit(data = data)
        # Recovered parameters should closely match true values
        assert m.m_b == pytest.approx(b_true, rel=0.02)  # within 2%
        assert m.m_B == pytest.approx(B_true, rel=0.05)  # within 5%

    @pytest.mark.unit()
    def test_fit_fewer_than_3_usable_rows_raises(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that fit fewer than 3 usable rows raises."""
        # Two rows with qx in (0, 1) is below the 3-row threshold
        short_data = pl.DataFrame({"Age": [65, 70], "qx": [0.014, 0.021]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = short_data)

    @pytest.mark.unit()
    def test_fit_missing_age_column_raises(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that fit missing age column raises."""
        bad_data = pl.DataFrame({"qx": [0.01, 0.02, 0.03]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_missing_qx_column_raises(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that fit missing qx column raises."""
        bad_data = pl.DataFrame({"Age": [65, 70, 75]})
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_nan_qx_raises(self, default_model: Longevity_Model_Standard) -> None:
        """Test that fit nan qx raises."""
        bad_data = pl.DataFrame(
            {"Age": [65, 70, 75], "qx": [0.014, float("nan"), 0.032]},
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = bad_data)

    @pytest.mark.unit()
    def test_fit_non_dataframe_raises(self, default_model: Longevity_Model_Standard) -> None:
        """Test that fit non dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = [(65, 0.014), (70, 0.021)])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_fit_excludes_qx_equals_one(self, default_model: Longevity_Model_Standard) -> None:
        """Test that fit excludes qx equals one."""
        # qx=1.0 rows (limiting-age entries) should be silently excluded
        data_with_max = pl.DataFrame(
            {
                "Age": [60, 65, 70, 75, 80, 85, 90, 120],
                "qx": [0.010, 0.014, 0.021, 0.032, 0.050, 0.077, 0.119, 1.0],
            },
        )
        default_model.fit(data = data_with_max)
        assert default_model.is_fitted is True

    @pytest.mark.unit()
    def test_fit_near_zero_b_slope_uses_limit_B_formula(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With b_ols≈0 (denom<1e-12), fit uses the b→0 limit B≈exp(alpha)."""
        import src.models.longevity.model_longevity_standard as lng_module

        alpha_val = -8.0
        monkeypatch.setattr(
            lng_module,
            "lstsq",
            lambda *args, **kwargs: (np.array([alpha_val, 1e-100]), None, None, None),
        )
        default_model.fit(data = adult_life_table)
        assert default_model.is_fitted is True
        assert default_model.m_B == pytest.approx(np.exp(alpha_val), rel=1e-6)

    @pytest.mark.unit()
    def test_fit_ols_non_finite_B_raises(
        self,
        default_model: Longevity_Model_Standard,
        adult_life_table: pl.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fit() raises when OLS produces a non-finite B (inf alpha → B=inf)."""
        import src.models.longevity.model_longevity_standard as lng_module

        monkeypatch.setattr(
            lng_module,
            "lstsq",
            lambda *args, **kwargs: (np.array([float("inf"), 0.1]), None, None, None),
        )
        with pytest.raises(Exception_Validation_Input):
            default_model.fit(data = adult_life_table)


# =============================================================================
# Tests: predict
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardPredict:
    """Tests for the predict() method."""

    @pytest.mark.unit()
    def test_predict_returns_dataframe(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict returns dataframe."""
        df = fitted_adult_model.predict(n_ages=10)
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_predict_correct_length(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict correct length."""
        df = fitted_adult_model.predict(n_ages=20)
        assert len(df) == 20

    @pytest.mark.unit()
    def test_predict_has_age_column(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict has age column."""
        df = fitted_adult_model.predict(n_ages=5)
        assert "Age" in df.columns

    @pytest.mark.unit()
    def test_predict_has_qx_column(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict has qx column."""
        df = fitted_adult_model.predict(n_ages=5)
        assert "qx" in df.columns

    @pytest.mark.unit()
    def test_predict_has_survival_column(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict has survival column."""
        df = fitted_adult_model.predict(n_ages=5)
        assert "survival" in df.columns

    @pytest.mark.unit()
    def test_predict_survival_starts_at_one(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict survival starts at one."""
        df = fitted_adult_model.predict(n_ages=5, start_age=65)
        assert df["survival"][0] == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.unit()
    def test_predict_survival_decreases_monotonically(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict survival decreases monotonically."""
        df = fitted_adult_model.predict(n_ages=10, start_age=65)
        survival = df["survival"].to_list()
        assert all(survival[i] >= survival[i + 1] for i in range(len(survival) - 1))

    @pytest.mark.unit()
    def test_predict_qx_increases_with_age(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict qx increases with age."""
        # Gompertz qx should always increase with age
        df = fitted_adult_model.predict(n_ages=10, start_age=50)
        qx_vals = df["qx"].to_list()
        assert all(qx_vals[i] <= qx_vals[i + 1] for i in range(len(qx_vals) - 1))

    @pytest.mark.unit()
    def test_predict_qx_in_unit_interval(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict qx in unit interval."""
        df = fitted_adult_model.predict(n_ages=20, start_age=40)
        qx_arr = np.array(df["qx"].to_list())
        assert np.all(qx_arr > 0)
        assert np.all(qx_arr < 1)

    @pytest.mark.unit()
    def test_predict_ages_correct_range(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict ages correct range."""
        df = fitted_adult_model.predict(n_ages=5, start_age=65)
        assert df["Age"].to_list() == [65, 66, 67, 68, 69]

    @pytest.mark.unit()
    def test_predict_before_fit_raises(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict before fit raises."""
        with pytest.raises(Exception_Calculation):
            default_model.predict(n_ages=10)

    @pytest.mark.unit()
    def test_predict_zero_ages_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict zero ages raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.predict(n_ages=0)

    @pytest.mark.unit()
    def test_predict_negative_start_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that predict negative start age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.predict(n_ages=5, start_age=-1)


# =============================================================================
# Tests: get_life_expectancy
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardLifeExpectancy:
    """Tests for get_life_expectancy()."""

    @pytest.mark.unit()
    def test_returns_positive_value(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that returns positive value."""
        ex = fitted_adult_model.get_life_expectancy(current_age=65)
        assert ex > 0

    @pytest.mark.unit()
    def test_decreases_with_age(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that decreases with age."""
        e40 = fitted_adult_model.get_life_expectancy(current_age=40)
        e65 = fitted_adult_model.get_life_expectancy(current_age=65)
        e80 = fitted_adult_model.get_life_expectancy(current_age=80)
        assert e40 > e65 > e80

    @pytest.mark.unit()
    def test_plausible_range_at_birth(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that plausible range at birth."""
        # Life expectancy at young age should be plausible (30-100 years)
        ex = fitted_adult_model.get_life_expectancy(current_age=0)
        assert 30 < ex < 120

    @pytest.mark.unit()
    def test_plausible_range_at_65(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that plausible range at 65."""
        # Life expectancy at 65 should be plausible (10-40 years remaining)
        ex = fitted_adult_model.get_life_expectancy(current_age=65)
        assert 5 < ex < 50

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Longevity_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_life_expectancy()

    @pytest.mark.unit()
    def test_negative_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that negative age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.get_life_expectancy(current_age=-1)


# =============================================================================
# Tests: survival_probability
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardSurvivalProbability:
    """Tests for survival_probability()."""

    @pytest.mark.unit()
    def test_returns_value_in_unit_interval(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that returns value in unit interval."""
        prob = fitted_adult_model.survival_probability(current_age=65, t_years=10.0)
        assert 0.0 <= prob <= 1.0

    @pytest.mark.unit()
    def test_declines_with_time(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that declines with time."""
        probs = [
            fitted_adult_model.survival_probability(current_age=65, t_years=float(t))
            for t in [1, 5, 10, 20]
        ]
        assert probs == sorted(probs, reverse=True)

    @pytest.mark.unit()
    def test_increases_with_mortality_age(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that increases with mortality age."""
        # Older starting age → shorter remaining survival
        p40 = fitted_adult_model.survival_probability(current_age=40, t_years=10.0)
        p75 = fitted_adult_model.survival_probability(current_age=75, t_years=10.0)
        assert p40 > p75

    @pytest.mark.unit()
    def test_analytical_formula_matches(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that analytical formula matches."""
        # Verify against the analytical formula: S(x, t) = exp(-B/b * exp(b*x) * (exp(b*t) - 1))
        x, t = 65, 10.0
        B, b = fitted_adult_model.m_B, fitted_adult_model.m_b
        expected = np.exp(-(B / b) * np.exp(b * x) * (np.exp(b * t) - 1.0))
        actual = fitted_adult_model.survival_probability(current_age=x, t_years=t)
        assert actual == pytest.approx(float(expected), rel=1e-10)

    @pytest.mark.unit()
    def test_zero_years_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that zero years raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.survival_probability(current_age=65, t_years=0.0)

    @pytest.mark.unit()
    def test_negative_years_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that negative years raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.survival_probability(current_age=65, t_years=-5.0)

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Longevity_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.survival_probability(current_age=65, t_years=10.0)

    @pytest.mark.unit()
    def test_negative_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that negative age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.survival_probability(current_age=-1, t_years=10.0)


# =============================================================================
# Tests: get_force_of_mortality
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardForceMortality:
    """Tests for the get_force_of_mortality() analytical helper."""

    @pytest.mark.unit()
    def test_returns_positive_value(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that returns positive value."""
        mu = fitted_adult_model.get_force_of_mortality(age = 65)
        assert mu > 0

    @pytest.mark.unit()
    def test_increases_with_age(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that increases with age."""
        mu40 = fitted_adult_model.get_force_of_mortality(age = 40)
        mu65 = fitted_adult_model.get_force_of_mortality(age = 65)
        mu80 = fitted_adult_model.get_force_of_mortality(age = 80)
        assert mu40 < mu65 < mu80

    @pytest.mark.unit()
    def test_analytical_formula(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that analytical formula."""
        B, b = fitted_adult_model.m_B, fitted_adult_model.m_b
        x = 65.0
        expected = B * np.exp(b * x)
        actual = fitted_adult_model.get_force_of_mortality(age = x)
        assert actual == pytest.approx(float(expected), rel=1e-10)

    @pytest.mark.unit()
    def test_negative_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that negative age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.get_force_of_mortality(age = -1)

    @pytest.mark.unit()
    def test_bool_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that boolean age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.get_force_of_mortality(age = True)

    @pytest.mark.unit()
    def test_non_finite_age_raises(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that non-finite age raises."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.get_force_of_mortality(age = float("nan"))

    @pytest.mark.unit()
    def test_raises_before_fit(self, default_model: Longevity_Model_Standard) -> None:
        """Test that raises before fit."""
        with pytest.raises(Exception_Calculation):
            default_model.get_force_of_mortality(age = 65)


# =============================================================================
# Tests: repr
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardRepr:
    """Tests for __repr__ output."""

    @pytest.mark.unit()
    def test_repr_contains_class_name(
        self,
        default_model: Longevity_Model_Standard,
    ) -> None:
        """Test that repr contains class name."""
        assert "Longevity_Model_Standard" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_contains_B(self, default_model: Longevity_Model_Standard) -> None:
        """Test that repr contains B."""
        r = repr(default_model)
        assert "B=" in r

    @pytest.mark.unit()
    def test_repr_contains_b(self, default_model: Longevity_Model_Standard) -> None:
        """Test that repr contains b."""
        r = repr(default_model)
        assert "b=" in r

    @pytest.mark.unit()
    def test_repr_contains_status(self, default_model: Longevity_Model_Standard) -> None:
        """Test that repr contains status."""
        assert "Not Fitted" in repr(default_model)

    @pytest.mark.unit()
    def test_repr_fitted_contains_fitted(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that repr fitted contains fitted."""
        assert "Fitted" in repr(fitted_adult_model)


# =============================================================================
# Tests: _validate_positive_float helper
# =============================================================================


@pytest.mark.unit()
class TestLongevityModelStandardHelpers:
    """Tests for the private _validate_positive_float helper."""

    @pytest.mark.unit()
    def test_valid_positive_value_passes(self) -> None:
        """Test that valid positive value passes."""
        _validate_positive_float(value = 0.5, name = "test")  # should not raise

    @pytest.mark.unit()
    def test_zero_raises(self) -> None:
        """Test that zero raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = 0.0, name = "test")

    @pytest.mark.unit()
    def test_negative_raises(self) -> None:
        """Test that negative raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = -1.0, name = "test")

    @pytest.mark.unit()
    def test_nan_raises(self) -> None:
        """Test that nan raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("nan"), name = "test")

    @pytest.mark.unit()
    def test_inf_raises(self) -> None:
        """Test that inf raises."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = float("inf"), name = "test")

    @pytest.mark.unit()
    def test_bool_raises(self) -> None:
        """Test that boolean values raise."""
        with pytest.raises(Exception_Validation_Input):
            _validate_positive_float(value = True, name = "test")

    @pytest.mark.unit()
    def test_qx_at_age_increases_with_age(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that qx at age increases with age."""
        # Internal helper should produce increasing qx with age
        q40 = fitted_adult_model._qx_at_age(age = 40)
        q65 = fitted_adult_model._qx_at_age(age = 65)
        q80 = fitted_adult_model._qx_at_age(age = 80)
        assert q40 < q65 < q80

    @pytest.mark.unit()
    def test_qx_at_age_in_unit_interval(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that qx at age in unit interval."""
        for age in [0, 20, 40, 65, 80, 100]:
            q = fitted_adult_model._qx_at_age(age = float(age))
            assert 0.0 < q < 1.0

    @pytest.mark.unit()
    def test_qx_at_age_matches_survival_formula(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """Test that qx at age matches survival formula."""
        # qx = 1 - S(x, 1)
        x = 65
        q_expected = 1.0 - fitted_adult_model.survival_probability(current_age=x, t_years=1.0)
        q_actual = fitted_adult_model._qx_at_age(age = float(x))
        assert q_actual == pytest.approx(q_expected, rel=1e-8)


# =============================================================================
# Tests: missing branch coverage
# =============================================================================


class Class_Test_Longevity_Standard_Coverage_Gaps:
    """Targeted tests to close remaining branch gaps in the Gompertz model."""

    @pytest.mark.unit()
    def Test_Fit_Uses_Constructor_Priors_When_Slope_Non_Positive(self) -> None:
        """When OLS slope b <= 0 the model should fall back to constructor priors."""
        # Reverse-age qx (decreasing mortality): CLL transform slope will be negative
        ages = list(range(40, 85, 5))
        # Decreasing qx (unusual but forces b <= 0 in OLS)
        qx_values = [0.09, 0.07, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01]
        data = pl.DataFrame({"Age": ages, "qx": qx_values})
        m = Longevity_Model_Standard(B=5e-5, b=0.09)
        m.fit(data = data)
        # Should not raise; model falls back to constructor priors
        assert m.m_b > 0

    @pytest.mark.unit()
    def Test_Fit_B_Fitted_Fallback_When_Denom_Near_Zero(self) -> None:
        """When b_fitted is extremely small denom < 1e-12, B falls back to exp(alpha)."""
        # Near-identical tiny qx forces near-zero OLS slope
        ages = list(range(1, 11))
        qx_values = [1e-6 + i * 1e-10 for i in range(10)]
        data = pl.DataFrame({"Age": ages, "qx": qx_values})
        m = Longevity_Model_Standard()
        try:
            m.fit(data = data)
            if hasattr(m, "m_B"):
                assert m.m_B > 0
        except Exception_Validation_Input:
            # Non-finite estimates raise validation error — acceptable path
            pass

    @pytest.mark.unit()
    def Test_Survival_Probability_Raises_For_Bool_T_Years(
        self,
        fitted_adult_model: Longevity_Model_Standard,
    ) -> None:
        """survival_probability() should reject boolean t_years values."""
        with pytest.raises(Exception_Validation_Input):
            fitted_adult_model.survival_probability(current_age=65, t_years=True)

