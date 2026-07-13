"""Unit tests for the utils_risks module.

This module contains comprehensive tests for the risk_measure_type enumeration,
covering all enum members, their string values, and every class-method accessor
that returns subsets of risk measures (variance-based, VaR family, drawdown,
higher moment, coherent, and convex).

Test Classes
------------
- Test_Risk_Measure_Type_Members
    Verifies that the expected enum members exist with correct string values.
- Test_Risk_Measure_Type_Get_Variance_Based
    Tests the get_variance_based_measures() class method.
- Test_Risk_Measure_Type_Get_Var_Family
    Tests the get_var_family_measures() class method.
- Test_Risk_Measure_Type_Get_Drawdown
    Tests the get_drawdown_measures() class method.
- Test_Risk_Measure_Type_Get_Higher_Moment
    Tests the get_higher_moment_measures() class method.
- Test_Risk_Measure_Type_Get_Coherent
    Tests the get_coherent_measures() class method.
- Test_Risk_Measure_Type_Get_Convex
    Tests the get_convex_measures() class method.
- Test_Risk_Measure_Type_Category_Exclusivity
    Tests cross-category properties (disjoint sets, coverage, subset relationships).
- Test_Risk_Measure_Type_Parametrized
    Parametrized regression checks on known member-category assignments.
"""

from __future__ import annotations

import pytest

from src.risks_metrics.risks.utils_risks import Risk_Measure_Type


# ==============================================================================
# Tests: Enum member existence and values
# ==============================================================================


class Test_Risk_Measure_Type_Members:
    """Verify enum members exist with the expected string values."""

    # ---- Variance-Based ----

    @pytest.mark.unit()
    def test_variance_member_exists(self):
        """risk_measure_type.VARIANCE exists."""
        assert Risk_Measure_Type.VARIANCE

    @pytest.mark.unit()
    def test_variance_value(self):
        """VARIANCE value is 'VARIANCE'."""
        assert Risk_Measure_Type.VARIANCE.value == "VARIANCE"

    @pytest.mark.unit()
    def test_semi_variance_member_exists(self):
        """SEMI_VARIANCE member exists."""
        assert Risk_Measure_Type.SEMI_VARIANCE

    @pytest.mark.unit()
    def test_mean_absolute_deviation_member_exists(self):
        """MEAN_ABSOLUTE_DEVIATION member exists."""
        assert Risk_Measure_Type.MEAN_ABSOLUTE_DEVIATION

    @pytest.mark.unit()
    def test_first_lower_partial_moment_member_exists(self):
        """FIRST_LOWER_PARTIAL_MOMENT member exists."""
        assert Risk_Measure_Type.FIRST_LOWER_PARTIAL_MOMENT

    # ---- VaR Family ----

    @pytest.mark.unit()
    def test_value_at_risk_member_exists(self):
        """VALUE_AT_RISK member exists."""
        assert Risk_Measure_Type.VALUE_AT_RISK

    @pytest.mark.unit()
    def test_cvar_member_exists(self):
        """CONDITIONAL_VALUE_AT_RISK member exists."""
        assert Risk_Measure_Type.CONDITIONAL_VALUE_AT_RISK

    @pytest.mark.unit()
    def test_evar_member_exists(self):
        """ENTROPIC_VALUE_AT_RISK member exists."""
        assert Risk_Measure_Type.ENTROPIC_VALUE_AT_RISK

    @pytest.mark.unit()
    def test_worst_realization_member_exists(self):
        """WORST_REALIZATION member exists."""
        assert Risk_Measure_Type.WORST_REALIZATION

    # ---- Drawdown ----

    @pytest.mark.unit()
    def test_maximum_drawdown_member_exists(self):
        """MAXIMUM_DRAWDOWN member exists."""
        assert Risk_Measure_Type.MAXIMUM_DRAWDOWN

    @pytest.mark.unit()
    def test_average_drawdown_member_exists(self):
        """AVERAGE_DRAWDOWN member exists."""
        assert Risk_Measure_Type.AVERAGE_DRAWDOWN

    @pytest.mark.unit()
    def test_cdar_member_exists(self):
        """CONDITIONAL_DRAWDOWN_AT_RISK member exists."""
        assert Risk_Measure_Type.CONDITIONAL_DRAWDOWN_AT_RISK

    @pytest.mark.unit()
    def test_dar_member_exists(self):
        """DRAWDOWN_AT_RISK member exists."""
        assert Risk_Measure_Type.DRAWDOWN_AT_RISK

    @pytest.mark.unit()
    def test_edar_member_exists(self):
        """ENTROPIC_DRAWDOWN_AT_RISK member exists."""
        assert Risk_Measure_Type.ENTROPIC_DRAWDOWN_AT_RISK

    @pytest.mark.unit()
    def test_ulcer_index_member_exists(self):
        """ULCER_INDEX member exists."""
        assert Risk_Measure_Type.ULCER_INDEX

    # ---- Higher Moment ----

    @pytest.mark.unit()
    def test_fourth_central_moment_member_exists(self):
        """FOURTH_CENTRAL_MOMENT member exists."""
        assert Risk_Measure_Type.FOURTH_CENTRAL_MOMENT

    @pytest.mark.unit()
    def test_fourth_lower_partial_moment_member_exists(self):
        """FOURTH_LOWER_PARTIAL_MOMENT member exists."""
        assert Risk_Measure_Type.FOURTH_LOWER_PARTIAL_MOMENT

    @pytest.mark.unit()
    def test_skew_member_exists(self):
        """SKEW member exists."""
        assert Risk_Measure_Type.SKEW

    @pytest.mark.unit()
    def test_kurtosis_member_exists(self):
        """KURTOSIS member exists."""
        assert Risk_Measure_Type.KURTOSIS

    # ---- Other ----

    @pytest.mark.unit()
    def test_gini_mean_difference_member_exists(self):
        """GINI_MEAN_DIFFERENCE member exists."""
        assert Risk_Measure_Type.GINI_MEAN_DIFFERENCE

    @pytest.mark.unit()
    def test_entropic_risk_measure_member_exists(self):
        """ENTROPIC_RISK_MEASURE member exists."""
        assert Risk_Measure_Type.ENTROPIC_RISK_MEASURE

    @pytest.mark.unit()
    def test_total_member_count(self):
        """Enum has exactly 20 members."""
        assert len(list(Risk_Measure_Type)) == 20


# ==============================================================================
# Tests: get_variance_based_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Variance_Based:
    """Tests for get_variance_based_measures() class method."""

    @pytest.fixture()
    def variance_measures(self):
        """Variance measures."""
        return Risk_Measure_Type.get_variance_based_measures()

    @pytest.mark.unit()
    def test_returns_list(self, variance_measures):
        """Return value is a list."""
        assert isinstance(variance_measures, list)

    @pytest.mark.unit()
    def test_returns_four_measures(self, variance_measures):
        """Exactly 4 variance-based measures are defined."""
        assert len(variance_measures) == 4

    @pytest.mark.unit()
    def test_variance_in_result(self, variance_measures):
        """VARIANCE is in the variance-based list."""
        assert Risk_Measure_Type.VARIANCE in variance_measures

    @pytest.mark.unit()
    def test_semi_variance_in_result(self, variance_measures):
        """SEMI_VARIANCE is in the variance-based list."""
        assert Risk_Measure_Type.SEMI_VARIANCE in variance_measures

    @pytest.mark.unit()
    def test_mad_in_result(self, variance_measures):
        """MEAN_ABSOLUTE_DEVIATION is in the variance-based list."""
        assert Risk_Measure_Type.MEAN_ABSOLUTE_DEVIATION in variance_measures

    @pytest.mark.unit()
    def test_first_lpm_in_result(self, variance_measures):
        """FIRST_LOWER_PARTIAL_MOMENT is in the variance-based list."""
        assert Risk_Measure_Type.FIRST_LOWER_PARTIAL_MOMENT in variance_measures

    @pytest.mark.unit()
    def test_cvar_not_in_result(self, variance_measures):
        """CONDITIONAL_VALUE_AT_RISK is NOT in the variance-based list."""
        assert Risk_Measure_Type.CONDITIONAL_VALUE_AT_RISK not in variance_measures

    @pytest.mark.unit()
    def test_all_elements_are_risk_measure_type(self, variance_measures):
        """All returned elements are risk_measure_type instances."""
        assert all(isinstance(m, Risk_Measure_Type) for m in variance_measures)


# ==============================================================================
# Tests: get_var_family_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Var_Family:
    """Tests for get_var_family_measures() class method."""

    @pytest.fixture()
    def var_measures(self):
        """Var measures."""
        return Risk_Measure_Type.get_var_family_measures()

    @pytest.mark.unit()
    def test_returns_list(self, var_measures):
        """Return value is a list."""
        assert isinstance(var_measures, list)

    @pytest.mark.unit()
    def test_returns_four_measures(self, var_measures):
        """Exactly 4 VaR-family measures are defined."""
        assert len(var_measures) == 4

    @pytest.mark.unit()
    def test_var_in_result(self, var_measures):
        """VALUE_AT_RISK is in the VaR-family list."""
        assert Risk_Measure_Type.VALUE_AT_RISK in var_measures

    @pytest.mark.unit()
    def test_cvar_in_result(self, var_measures):
        """CONDITIONAL_VALUE_AT_RISK is in the VaR-family list."""
        assert Risk_Measure_Type.CONDITIONAL_VALUE_AT_RISK in var_measures

    @pytest.mark.unit()
    def test_evar_in_result(self, var_measures):
        """ENTROPIC_VALUE_AT_RISK is in the VaR-family list."""
        assert Risk_Measure_Type.ENTROPIC_VALUE_AT_RISK in var_measures

    @pytest.mark.unit()
    def test_worst_realization_in_result(self, var_measures):
        """WORST_REALIZATION is in the VaR-family list."""
        assert Risk_Measure_Type.WORST_REALIZATION in var_measures

    @pytest.mark.unit()
    def test_maximum_drawdown_not_in_result(self, var_measures):
        """MAXIMUM_DRAWDOWN is NOT in the VaR-family list."""
        assert Risk_Measure_Type.MAXIMUM_DRAWDOWN not in var_measures


# ==============================================================================
# Tests: get_drawdown_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Drawdown:
    """Tests for get_drawdown_measures() class method."""

    @pytest.fixture()
    def drawdown_measures(self):
        """Drawdown measures."""
        return Risk_Measure_Type.get_drawdown_measures()

    @pytest.mark.unit()
    def test_returns_list(self, drawdown_measures):
        """Return value is a list."""
        assert isinstance(drawdown_measures, list)

    @pytest.mark.unit()
    def test_returns_six_measures(self, drawdown_measures):
        """Exactly 6 drawdown measures are defined."""
        assert len(drawdown_measures) == 6

    @pytest.mark.unit()
    def test_maximum_drawdown_in_result(self, drawdown_measures):
        """MAXIMUM_DRAWDOWN is in the drawdown list."""
        assert Risk_Measure_Type.MAXIMUM_DRAWDOWN in drawdown_measures

    @pytest.mark.unit()
    def test_average_drawdown_in_result(self, drawdown_measures):
        """AVERAGE_DRAWDOWN is in the drawdown list."""
        assert Risk_Measure_Type.AVERAGE_DRAWDOWN in drawdown_measures

    @pytest.mark.unit()
    def test_cdar_in_result(self, drawdown_measures):
        """CONDITIONAL_DRAWDOWN_AT_RISK is in the drawdown list."""
        assert Risk_Measure_Type.CONDITIONAL_DRAWDOWN_AT_RISK in drawdown_measures

    @pytest.mark.unit()
    def test_dar_in_result(self, drawdown_measures):
        """DRAWDOWN_AT_RISK is in the drawdown list."""
        assert Risk_Measure_Type.DRAWDOWN_AT_RISK in drawdown_measures

    @pytest.mark.unit()
    def test_edar_in_result(self, drawdown_measures):
        """ENTROPIC_DRAWDOWN_AT_RISK is in the drawdown list."""
        assert Risk_Measure_Type.ENTROPIC_DRAWDOWN_AT_RISK in drawdown_measures

    @pytest.mark.unit()
    def test_ulcer_index_in_result(self, drawdown_measures):
        """ULCER_INDEX is in the drawdown list."""
        assert Risk_Measure_Type.ULCER_INDEX in drawdown_measures

    @pytest.mark.unit()
    def test_variance_not_in_result(self, drawdown_measures):
        """VARIANCE is NOT in the drawdown list."""
        assert Risk_Measure_Type.VARIANCE not in drawdown_measures


# ==============================================================================
# Tests: get_higher_moment_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Higher_Moment:
    """Tests for get_higher_moment_measures() class method."""

    @pytest.fixture()
    def hm_measures(self):
        """Hm measures."""
        return Risk_Measure_Type.get_higher_moment_measures()

    @pytest.mark.unit()
    def test_returns_list(self, hm_measures):
        """Return value is a list."""
        assert isinstance(hm_measures, list)

    @pytest.mark.unit()
    def test_returns_four_measures(self, hm_measures):
        """Exactly 4 higher-moment measures are defined."""
        assert len(hm_measures) == 4

    @pytest.mark.unit()
    def test_fourth_central_moment_in_result(self, hm_measures):
        """FOURTH_CENTRAL_MOMENT is in the higher-moment list."""
        assert Risk_Measure_Type.FOURTH_CENTRAL_MOMENT in hm_measures

    @pytest.mark.unit()
    def test_fourth_lpm_in_result(self, hm_measures):
        """FOURTH_LOWER_PARTIAL_MOMENT is in the higher-moment list."""
        assert Risk_Measure_Type.FOURTH_LOWER_PARTIAL_MOMENT in hm_measures

    @pytest.mark.unit()
    def test_skew_in_result(self, hm_measures):
        """SKEW is in the higher-moment list."""
        assert Risk_Measure_Type.SKEW in hm_measures

    @pytest.mark.unit()
    def test_kurtosis_in_result(self, hm_measures):
        """KURTOSIS is in the higher-moment list."""
        assert Risk_Measure_Type.KURTOSIS in hm_measures

    @pytest.mark.unit()
    def test_variance_not_in_result(self, hm_measures):
        """VARIANCE is NOT in the higher-moment list."""
        assert Risk_Measure_Type.VARIANCE not in hm_measures


# ==============================================================================
# Tests: get_coherent_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Coherent:
    """Tests for get_coherent_measures() class method."""

    @pytest.fixture()
    def coherent_measures(self):
        """Coherent measures."""
        return Risk_Measure_Type.get_coherent_measures()

    @pytest.mark.unit()
    def test_returns_list(self, coherent_measures):
        """Return value is a list."""
        assert isinstance(coherent_measures, list)

    @pytest.mark.unit()
    def test_has_at_least_one_measure(self, coherent_measures):
        """Coherent list is non-empty."""
        assert len(coherent_measures) >= 1

    @pytest.mark.unit()
    def test_cvar_is_coherent(self, coherent_measures):
        """CONDITIONAL_VALUE_AT_RISK is a coherent risk measure."""
        assert Risk_Measure_Type.CONDITIONAL_VALUE_AT_RISK in coherent_measures

    @pytest.mark.unit()
    def test_evar_is_coherent(self, coherent_measures):
        """ENTROPIC_VALUE_AT_RISK is a coherent risk measure."""
        assert Risk_Measure_Type.ENTROPIC_VALUE_AT_RISK in coherent_measures

    @pytest.mark.unit()
    def test_worst_realization_is_coherent(self, coherent_measures):
        """WORST_REALIZATION is a coherent risk measure."""
        assert Risk_Measure_Type.WORST_REALIZATION in coherent_measures

    @pytest.mark.unit()
    def test_cdar_is_coherent(self, coherent_measures):
        """CONDITIONAL_DRAWDOWN_AT_RISK is a coherent risk measure."""
        assert Risk_Measure_Type.CONDITIONAL_DRAWDOWN_AT_RISK in coherent_measures

    @pytest.mark.unit()
    def test_variance_is_not_coherent(self, coherent_measures):
        """VARIANCE is NOT a coherent risk measure."""
        assert Risk_Measure_Type.VARIANCE not in coherent_measures

    @pytest.mark.unit()
    def test_value_at_risk_is_not_coherent(self, coherent_measures):
        """VALUE_AT_RISK is NOT a coherent risk measure."""
        assert Risk_Measure_Type.VALUE_AT_RISK not in coherent_measures

    @pytest.mark.unit()
    def test_all_elements_are_risk_measure_type(self, coherent_measures):
        """Every element in the coherent list is a risk_measure_type."""
        assert all(isinstance(m, Risk_Measure_Type) for m in coherent_measures)


# ==============================================================================
# Tests: get_convex_measures
# ==============================================================================


class Test_Risk_Measure_Type_Get_Convex:
    """Tests for get_convex_measures() class method."""

    @pytest.fixture()
    def convex_measures(self):
        """Convex measures."""
        return Risk_Measure_Type.get_convex_measures()

    @pytest.mark.unit()
    def test_returns_list(self, convex_measures):
        """Return value is a list."""
        assert isinstance(convex_measures, list)

    @pytest.mark.unit()
    def test_coherent_is_subset_of_convex(self, convex_measures):
        """Every coherent measure is also convex (coherent ⊆ convex)."""
        coherent = Risk_Measure_Type.get_coherent_measures()
        for m in coherent:
            assert m in convex_measures

    @pytest.mark.unit()
    def test_variance_is_convex(self, convex_measures):
        """VARIANCE is a convex (but not coherent) risk measure."""
        assert Risk_Measure_Type.VARIANCE in convex_measures

    @pytest.mark.unit()
    def test_entropic_risk_measure_is_convex(self, convex_measures):
        """ENTROPIC_RISK_MEASURE is in the convex list."""
        assert Risk_Measure_Type.ENTROPIC_RISK_MEASURE in convex_measures

    @pytest.mark.unit()
    def test_var_is_convex(self, convex_measures):
        """VALUE_AT_RISK is in the convex list."""
        assert Risk_Measure_Type.VALUE_AT_RISK in convex_measures

    @pytest.mark.unit()
    def test_convex_is_larger_than_coherent(self, convex_measures):
        """Convex set is strictly larger than the coherent set."""
        coherent = Risk_Measure_Type.get_coherent_measures()
        assert len(convex_measures) > len(coherent)

    @pytest.mark.unit()
    def test_all_elements_are_risk_measure_type(self, convex_measures):
        """Every element in the convex list is a risk_measure_type."""
        assert all(isinstance(m, Risk_Measure_Type) for m in convex_measures)


# ==============================================================================
# Tests: Cross-category properties
# ==============================================================================


class Test_Risk_Measure_Type_Category_Exclusivity:
    """Test structural properties across categories."""

    @pytest.mark.unit()
    def test_variance_and_drawdown_are_disjoint(self):
        """Variance-based and drawdown categories share no members."""
        variance = set(Risk_Measure_Type.get_variance_based_measures())
        drawdown = set(Risk_Measure_Type.get_drawdown_measures())
        assert variance.isdisjoint(drawdown)

    @pytest.mark.unit()
    def test_var_family_and_drawdown_are_disjoint(self):
        """VaR-family and drawdown categories share no members."""
        var_fam = set(Risk_Measure_Type.get_var_family_measures())
        drawdown = set(Risk_Measure_Type.get_drawdown_measures())
        assert var_fam.isdisjoint(drawdown)

    @pytest.mark.unit()
    def test_higher_moment_and_drawdown_are_disjoint(self):
        """Higher-moment and drawdown categories share no members."""
        hm = set(Risk_Measure_Type.get_higher_moment_measures())
        drawdown = set(Risk_Measure_Type.get_drawdown_measures())
        assert hm.isdisjoint(drawdown)

    @pytest.mark.unit()
    def test_all_members_appear_in_at_least_one_named_category(self):
        """Every enum member is covered by at least one named category list."""
        all_categorized = (
            set(Risk_Measure_Type.get_variance_based_measures())
            | set(Risk_Measure_Type.get_var_family_measures())
            | set(Risk_Measure_Type.get_drawdown_measures())
            | set(Risk_Measure_Type.get_higher_moment_measures())
            | {Risk_Measure_Type.GINI_MEAN_DIFFERENCE, Risk_Measure_Type.ENTROPIC_RISK_MEASURE}
        )
        for member in Risk_Measure_Type:
            assert member in all_categorized, f"{member} not in any category"

    @pytest.mark.unit()
    def test_coherent_measures_all_exist_as_enum_members(self):
        """Every value returned by get_coherent_measures() is an enum member."""
        for m in Risk_Measure_Type.get_coherent_measures():
            assert m in list(Risk_Measure_Type)


# ==============================================================================
# Tests: Parametrized membership checks
# ==============================================================================


class Test_Risk_Measure_Type_Parametrized:
    """Parametrized regression tests for known category memberships."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "member",
        [
            Risk_Measure_Type.VARIANCE,
            Risk_Measure_Type.SEMI_VARIANCE,
            Risk_Measure_Type.MEAN_ABSOLUTE_DEVIATION,
            Risk_Measure_Type.FIRST_LOWER_PARTIAL_MOMENT,
        ],
    )
    def test_variance_based_membership(self, member):
        """Each member is listed in get_variance_based_measures()."""
        assert member in Risk_Measure_Type.get_variance_based_measures()

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "member",
        [
            Risk_Measure_Type.MAXIMUM_DRAWDOWN,
            Risk_Measure_Type.AVERAGE_DRAWDOWN,
            Risk_Measure_Type.CONDITIONAL_DRAWDOWN_AT_RISK,
            Risk_Measure_Type.DRAWDOWN_AT_RISK,
            Risk_Measure_Type.ENTROPIC_DRAWDOWN_AT_RISK,
            Risk_Measure_Type.ULCER_INDEX,
        ],
    )
    def test_drawdown_membership(self, member):
        """Each member is listed in get_drawdown_measures()."""
        assert member in Risk_Measure_Type.get_drawdown_measures()

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "member",
        [
            Risk_Measure_Type.FOURTH_CENTRAL_MOMENT,
            Risk_Measure_Type.FOURTH_LOWER_PARTIAL_MOMENT,
            Risk_Measure_Type.SKEW,
            Risk_Measure_Type.KURTOSIS,
        ],
    )
    def test_higher_moment_membership(self, member):
        """Each member is listed in get_higher_moment_measures()."""
        assert member in Risk_Measure_Type.get_higher_moment_measures()

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "member",
        [
            Risk_Measure_Type.VALUE_AT_RISK,
            Risk_Measure_Type.CONDITIONAL_VALUE_AT_RISK,
            Risk_Measure_Type.ENTROPIC_VALUE_AT_RISK,
            Risk_Measure_Type.WORST_REALIZATION,
        ],
    )
    def test_var_family_membership(self, member):
        """Each member is listed in get_var_family_measures()."""
        assert member in Risk_Measure_Type.get_var_family_measures()

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "expected_value",
        [
            "VARIANCE",
            "SEMI_VARIANCE",
            "MEAN_ABSOLUTE_DEVIATION",
            "FIRST_LOWER_PARTIAL_MOMENT",
            "VALUE_AT_RISK",
            "CONDITIONAL_VALUE_AT_RISK",
            "ENTROPIC_VALUE_AT_RISK",
            "WORST_REALIZATION",
            "MAXIMUM_DRAWDOWN",
            "AVERAGE_DRAWDOWN",
            "CONDITIONAL_DRAWDOWN_AT_RISK",
            "DRAWDOWN_AT_RISK",
            "ENTROPIC_DRAWDOWN_AT_RISK",
            "ULCER_INDEX",
            "FOURTH_CENTRAL_MOMENT",
            "FOURTH_LOWER_PARTIAL_MOMENT",
            "SKEW",
            "KURTOSIS",
            "GINI_MEAN_DIFFERENCE",
            "ENTROPIC_RISK_MEASURE",
        ],
    )
    def test_all_member_values_are_uppercase_strings(self, expected_value):
        """Every enum member's .value is an uppercase string matching its name."""
        member = Risk_Measure_Type[expected_value]
        assert member.value == expected_value
