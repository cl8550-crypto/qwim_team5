"""Unit tests for utils_portfolio_optimization module.

Tests cover:
    - portfolio_optimization_type enum members, values, and classmethods
    - portfolio_optimization_feature_type enum members, values, and classmethods
    - Regression: enum.Enum used (not aenum.Enum) so all standard Enum behaviour works
    - All classmethods return correct types/counts after the aenum→enum migration fix
"""

from __future__ import annotations

from enum import Enum

import pytest

from src.models.portfolio_optimization.utils_portfolio_optimization import (
    portfolio_optimization_feature_type,
    portfolio_optimization_type,
)


# =============================================================================
# portfolio_optimization_type — enum membership
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Type_Members:
    """Verify every expected member exists on portfolio_optimization_type."""

    # Basic
    @pytest.mark.unit()
    def test_member_basic_equal_weighted(self) -> None:
        """Test that member basic equal weighted."""
        assert portfolio_optimization_type.BASIC_EQUAL_WEIGHTED is not None

    @pytest.mark.unit()
    def test_member_basic_inverse_volatility(self) -> None:
        """Test that member basic inverse volatility."""
        assert portfolio_optimization_type.BASIC_INVERSE_VOLATILITY is not None

    @pytest.mark.unit()
    def test_member_basic_random_dirichlet(self) -> None:
        """Test that member basic random dirichlet."""
        assert portfolio_optimization_type.BASIC_RANDOM_DIRICHLET is not None

    # Convex
    @pytest.mark.unit()
    def test_member_convex_mean_risk(self) -> None:
        """Test that member convex mean risk."""
        assert portfolio_optimization_type.CONVEX_MEAN_RISK is not None

    @pytest.mark.unit()
    def test_member_convex_risk_budgeting(self) -> None:
        """Test that member convex risk budgeting."""
        assert portfolio_optimization_type.CONVEX_RISK_BUDGETING is not None

    @pytest.mark.unit()
    def test_member_convex_maximum_diversification(self) -> None:
        """Test that member convex maximum diversification."""
        assert portfolio_optimization_type.CONVEX_MAXIMUM_DIVERSIFICATION is not None

    @pytest.mark.unit()
    def test_member_convex_distributionally_robust_cvar(self) -> None:
        """Test that member convex distributionally robust cvar."""
        assert portfolio_optimization_type.CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR is not None

    @pytest.mark.unit()
    def test_member_convex_benchmark_tracking(self) -> None:
        """Test that member convex benchmark tracking."""
        assert portfolio_optimization_type.CONVEX_BENCHMARK_TRACKING is not None

    # Clustering
    @pytest.mark.unit()
    def test_member_clustering_hierarchical_risk_parity(self) -> None:
        """Test that member clustering hierarchical risk parity."""
        assert portfolio_optimization_type.CLUSTERING_HIERARCHICAL_RISK_PARITY is not None

    @pytest.mark.unit()
    def test_member_clustering_herc(self) -> None:
        """Test that member clustering herc."""
        assert (
            portfolio_optimization_type.CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION
            is not None
        )

    @pytest.mark.unit()
    def test_member_clustering_schur(self) -> None:
        """Test that member clustering schur."""
        assert portfolio_optimization_type.CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION is not None

    @pytest.mark.unit()
    def test_member_clustering_nested(self) -> None:
        """Test that member clustering nested."""
        assert portfolio_optimization_type.CLUSTERING_NESTED is not None

    # Ensemble
    @pytest.mark.unit()
    def test_member_ensemble_stacking(self) -> None:
        """Test that member ensemble stacking."""
        assert portfolio_optimization_type.ENSEMBLE_STACKING is not None

    @pytest.mark.unit()
    def test_total_member_count(self) -> None:
        """Enum must have exactly 13 members."""
        assert len(portfolio_optimization_type) == 13


# =============================================================================
# portfolio_optimization_type — values
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Type_Values:
    """Verify enum values equal the member name strings."""

    @pytest.mark.parametrize(
        "member",
        list(portfolio_optimization_type),
    )
    @pytest.mark.unit()
    def test_value_equals_name(self, member: portfolio_optimization_type) -> None:
        """Each enum value must equal its name (self-documenting convention)."""
        assert member.value == member.name


# =============================================================================
# portfolio_optimization_type — standard Enum contract (regression: aenum→enum)
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Type_Enum_Contract:
    """Regression tests confirming standard enum.Enum behaviour after the aenum fix."""

    @pytest.mark.unit()
    def test_is_standard_enum_subclass(self) -> None:
        """portfolio_optimization_type must be a subclass of stdlib Enum."""
        assert issubclass(portfolio_optimization_type, Enum)

    @pytest.mark.unit()
    def test_subscript_by_name(self) -> None:
        """portfolio_optimization_type['BASIC_EQUAL_WEIGHTED'] must work (stdlib Enum)."""
        member = portfolio_optimization_type["BASIC_EQUAL_WEIGHTED"]
        assert member is portfolio_optimization_type.BASIC_EQUAL_WEIGHTED

    @pytest.mark.unit()
    def test_subscript_by_value(self) -> None:
        """portfolio_optimization_type('CONVEX_MEAN_RISK') must work."""
        member = portfolio_optimization_type("CONVEX_MEAN_RISK")
        assert member is portfolio_optimization_type.CONVEX_MEAN_RISK

    @pytest.mark.unit()
    def test_iteration(self) -> None:
        """Iterating over the enum must yield all 13 members."""
        members = list(portfolio_optimization_type)
        assert len(members) == 13

    @pytest.mark.unit()
    def test_membership_test(self) -> None:
        """in-operator check must work."""
        assert portfolio_optimization_type.ENSEMBLE_STACKING in portfolio_optimization_type

    @pytest.mark.unit()
    def test_identity_equality(self) -> None:
        """Two accesses to same member must return identical object."""
        assert (
            portfolio_optimization_type.BASIC_EQUAL_WEIGHTED
            is portfolio_optimization_type.BASIC_EQUAL_WEIGHTED
        )

    @pytest.mark.unit()
    def test_name_attribute(self) -> None:
        """Each member must expose a .name string attribute."""
        assert isinstance(portfolio_optimization_type.CONVEX_RISK_BUDGETING.name, str)

    @pytest.mark.unit()
    def test_value_attribute(self) -> None:
        """Each member must expose a .value attribute."""
        assert isinstance(portfolio_optimization_type.CLUSTERING_NESTED.value, str)


# =============================================================================
# portfolio_optimization_type — classmethods
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Type_Classmethods:
    """Test the four grouping classmethods."""

    @pytest.mark.unit()
    def test_get_basic_methods_count(self) -> None:
        """Test that get basic methods count."""
        methods = portfolio_optimization_type.get_basic_methods()
        assert len(methods) == 3

    @pytest.mark.unit()
    def test_get_basic_methods_returns_list(self) -> None:
        """Test that get basic methods returns list."""
        methods = portfolio_optimization_type.get_basic_methods()
        assert isinstance(methods, list)

    @pytest.mark.unit()
    def test_get_basic_methods_all_basic(self) -> None:
        """Test that get basic methods all basic."""
        methods = portfolio_optimization_type.get_basic_methods()
        assert all(m.name.startswith("BASIC") for m in methods)

    @pytest.mark.unit()
    def test_get_basic_methods_members(self) -> None:
        """Test that get basic methods members."""
        methods = portfolio_optimization_type.get_basic_methods()
        expected = {
            portfolio_optimization_type.BASIC_EQUAL_WEIGHTED,
            portfolio_optimization_type.BASIC_INVERSE_VOLATILITY,
            portfolio_optimization_type.BASIC_RANDOM_DIRICHLET,
        }
        assert set(methods) == expected

    @pytest.mark.unit()
    def test_get_convex_methods_count(self) -> None:
        """Test that get convex methods count."""
        methods = portfolio_optimization_type.get_convex_methods()
        assert len(methods) == 5

    @pytest.mark.unit()
    def test_get_convex_methods_all_convex(self) -> None:
        """Test that get convex methods all convex."""
        methods = portfolio_optimization_type.get_convex_methods()
        assert all(m.name.startswith("CONVEX") for m in methods)

    @pytest.mark.unit()
    def test_get_convex_methods_members(self) -> None:
        """Test that get convex methods members."""
        methods = portfolio_optimization_type.get_convex_methods()
        expected = {
            portfolio_optimization_type.CONVEX_MEAN_RISK,
            portfolio_optimization_type.CONVEX_RISK_BUDGETING,
            portfolio_optimization_type.CONVEX_MAXIMUM_DIVERSIFICATION,
            portfolio_optimization_type.CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR,
            portfolio_optimization_type.CONVEX_BENCHMARK_TRACKING,
        }
        assert set(methods) == expected

    @pytest.mark.unit()
    def test_get_clustering_methods_count(self) -> None:
        """Test that get clustering methods count."""
        methods = portfolio_optimization_type.get_clustering_methods()
        assert len(methods) == 4

    @pytest.mark.unit()
    def test_get_clustering_methods_all_clustering(self) -> None:
        """Test that get clustering methods all clustering."""
        methods = portfolio_optimization_type.get_clustering_methods()
        assert all(m.name.startswith("CLUSTERING") for m in methods)

    @pytest.mark.unit()
    def test_get_clustering_methods_members(self) -> None:
        """Test that get clustering methods members."""
        methods = portfolio_optimization_type.get_clustering_methods()
        expected = {
            portfolio_optimization_type.CLUSTERING_HIERARCHICAL_RISK_PARITY,
            portfolio_optimization_type.CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION,
            portfolio_optimization_type.CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION,
            portfolio_optimization_type.CLUSTERING_NESTED,
        }
        assert set(methods) == expected

    @pytest.mark.unit()
    def test_get_ensemble_methods_count(self) -> None:
        """Test that get ensemble methods count."""
        methods = portfolio_optimization_type.get_ensemble_methods()
        assert len(methods) == 1

    @pytest.mark.unit()
    def test_get_ensemble_methods_all_ensemble(self) -> None:
        """Test that get ensemble methods all ensemble."""
        methods = portfolio_optimization_type.get_ensemble_methods()
        assert all(m.name.startswith("ENSEMBLE") for m in methods)

    @pytest.mark.unit()
    def test_get_ensemble_methods_members(self) -> None:
        """Test that get ensemble methods members."""
        methods = portfolio_optimization_type.get_ensemble_methods()
        assert portfolio_optimization_type.ENSEMBLE_STACKING in methods

    @pytest.mark.unit()
    def test_classmethod_groups_cover_all_members(self) -> None:
        """Union of all four method groups must equal the full member set."""
        all_via_groups = (
            portfolio_optimization_type.get_basic_methods()
            + portfolio_optimization_type.get_convex_methods()
            + portfolio_optimization_type.get_clustering_methods()
            + portfolio_optimization_type.get_ensemble_methods()
        )
        assert set(all_via_groups) == set(portfolio_optimization_type)

    @pytest.mark.unit()
    def test_classmethod_groups_are_disjoint(self) -> None:
        """Each method group must contain unique members (no overlap)."""
        basic = set(portfolio_optimization_type.get_basic_methods())
        convex = set(portfolio_optimization_type.get_convex_methods())
        clustering = set(portfolio_optimization_type.get_clustering_methods())
        ensemble = set(portfolio_optimization_type.get_ensemble_methods())

        assert basic.isdisjoint(convex)
        assert basic.isdisjoint(clustering)
        assert basic.isdisjoint(ensemble)
        assert convex.isdisjoint(clustering)
        assert convex.isdisjoint(ensemble)
        assert clustering.isdisjoint(ensemble)

    @pytest.mark.unit()
    def test_classmethods_return_type_instances(self) -> None:
        """All items in each classmethod result must be portfolio_optimization_type instances."""
        for method_list in [
            portfolio_optimization_type.get_basic_methods(),
            portfolio_optimization_type.get_convex_methods(),
            portfolio_optimization_type.get_clustering_methods(),
            portfolio_optimization_type.get_ensemble_methods(),
        ]:
            for item in method_list:
                assert isinstance(item, portfolio_optimization_type)


# =============================================================================
# portfolio_optimization_feature_type — enum membership
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Feature_Type_Members:
    """Verify every expected member exists on portfolio_optimization_feature_type."""

    # Objectives
    @pytest.mark.unit()
    def test_member_minimize_risk(self) -> None:
        """Test that member minimize risk."""
        assert portfolio_optimization_feature_type.MINIMIZE_RISK is not None

    @pytest.mark.unit()
    def test_member_maximize_returns(self) -> None:
        """Test that member maximize returns."""
        assert portfolio_optimization_feature_type.MAXIMIZE_RETURNS is not None

    @pytest.mark.unit()
    def test_member_maximize_utility(self) -> None:
        """Test that member maximize utility."""
        assert portfolio_optimization_feature_type.MAXIMIZE_UTILITY is not None

    @pytest.mark.unit()
    def test_member_maximize_ratio(self) -> None:
        """Test that member maximize ratio."""
        assert portfolio_optimization_feature_type.MAXIMIZE_RATIO is not None

    # Costs
    @pytest.mark.unit()
    def test_member_costs_transaction(self) -> None:
        """Test that member costs transaction."""
        assert portfolio_optimization_feature_type.COSTS_TRANSACTION is not None

    @pytest.mark.unit()
    def test_member_fees_management(self) -> None:
        """Test that member fees management."""
        assert portfolio_optimization_feature_type.FEES_MANAGEMENT is not None

    # Regularization
    @pytest.mark.unit()
    def test_member_regularization_l1(self) -> None:
        """Test that member regularization l1."""
        assert portfolio_optimization_feature_type.REGULARIZATION_L1 is not None

    @pytest.mark.unit()
    def test_member_regularization_l2(self) -> None:
        """Test that member regularization l2."""
        assert portfolio_optimization_feature_type.REGULARIZATION_L2 is not None

    # Weight constraints
    @pytest.mark.unit()
    def test_member_constraints_weight(self) -> None:
        """Test that member constraints weight."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_WEIGHT is not None

    @pytest.mark.unit()
    def test_member_constraints_group(self) -> None:
        """Test that member constraints group."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_GROUP is not None

    @pytest.mark.unit()
    def test_member_constraints_budget(self) -> None:
        """Test that member constraints budget."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_BUDGET is not None

    @pytest.mark.unit()
    def test_member_constraints_threshold_long(self) -> None:
        """Test that member constraints threshold long."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_LONG is not None

    @pytest.mark.unit()
    def test_member_constraints_threshold_short(self) -> None:
        """Test that member constraints threshold short."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_SHORT is not None

    # Portfolio constraints
    @pytest.mark.unit()
    def test_member_constraints_tracking_error(self) -> None:
        """Test that member constraints tracking error."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_TRACKING_ERROR is not None

    @pytest.mark.unit()
    def test_member_constraints_turnover(self) -> None:
        """Test that member constraints turnover."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_TURNOVER is not None

    @pytest.mark.unit()
    def test_member_constraints_cardinality(self) -> None:
        """Test that member constraints cardinality."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY is not None

    @pytest.mark.unit()
    def test_member_constraints_cardinality_group(self) -> None:
        """Test that member constraints cardinality group."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY_GROUP is not None

    @pytest.mark.unit()
    def test_member_constraints_risk_measure(self) -> None:
        """Test that member constraints risk measure."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_RISK_MEASURE is not None

    @pytest.mark.unit()
    def test_member_constraints_expected_return(self) -> None:
        """Test that member constraints expected return."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_EXPECTED_RETURN is not None

    # Advanced / Custom
    @pytest.mark.unit()
    def test_member_constraints_custom(self) -> None:
        """Test that member constraints custom."""
        assert portfolio_optimization_feature_type.CONSTRAINTS_CUSTOM is not None

    # Robust optimization
    @pytest.mark.unit()
    def test_member_uncertainty_set_expected_returns(self) -> None:
        """Test that member uncertainty set expected returns."""
        assert (
            portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_EXPECTED_RETURNS is not None
        )

    @pytest.mark.unit()
    def test_member_uncertainty_set_covariance(self) -> None:
        """Test that member uncertainty set covariance."""
        assert portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_COVARIANCE is not None

    # Custom features
    @pytest.mark.unit()
    def test_member_objective_custom(self) -> None:
        """Test that member objective custom."""
        assert portfolio_optimization_feature_type.OBJECTIVE_CUSTOM is not None

    @pytest.mark.unit()
    def test_member_estimator_prior(self) -> None:
        """Test that member estimator prior."""
        assert portfolio_optimization_feature_type.ESTIMATOR_PRIOR is not None

    @pytest.mark.unit()
    def test_total_member_count(self) -> None:
        """Enum must have exactly 24 members."""
        assert len(portfolio_optimization_feature_type) == 24


# =============================================================================
# portfolio_optimization_feature_type — values
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Feature_Type_Values:
    """Verify enum values equal the member name strings."""

    @pytest.mark.parametrize(
        "member",
        list(portfolio_optimization_feature_type),
    )
    @pytest.mark.unit()
    def test_value_equals_name(self, member: portfolio_optimization_feature_type) -> None:
        """Test that value equals name."""
        assert member.value == member.name


# =============================================================================
# portfolio_optimization_feature_type — standard Enum contract (regression)
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Feature_Type_Enum_Contract:
    """Regression: standard stdlib Enum behaviour after aenum→enum migration."""

    @pytest.mark.unit()
    def test_is_standard_enum_subclass(self) -> None:
        """Test that is standard enum subclass."""
        assert issubclass(portfolio_optimization_feature_type, Enum)

    @pytest.mark.unit()
    def test_subscript_by_name(self) -> None:
        """Test that subscript by name."""
        member = portfolio_optimization_feature_type["MINIMIZE_RISK"]
        assert member is portfolio_optimization_feature_type.MINIMIZE_RISK

    @pytest.mark.unit()
    def test_subscript_by_value(self) -> None:
        """Test that subscript by value."""
        member = portfolio_optimization_feature_type("MAXIMIZE_UTILITY")
        assert member is portfolio_optimization_feature_type.MAXIMIZE_UTILITY

    @pytest.mark.unit()
    def test_iteration_count(self) -> None:
        """Test that iteration count."""
        assert len(list(portfolio_optimization_feature_type)) == 24

    @pytest.mark.unit()
    def test_membership_test(self) -> None:
        """Test that membership test."""
        assert (
            portfolio_optimization_feature_type.REGULARIZATION_L1
            in portfolio_optimization_feature_type
        )

    @pytest.mark.unit()
    def test_identity_equality(self) -> None:
        """Test that identity equality."""
        assert (
            portfolio_optimization_feature_type.CONSTRAINTS_BUDGET
            is portfolio_optimization_feature_type.CONSTRAINTS_BUDGET
        )


# =============================================================================
# portfolio_optimization_feature_type — classmethods
# =============================================================================


@pytest.mark.unit()
class Test_Portfolio_Optimization_Feature_Type_Classmethods:
    """Test all ten grouping classmethods."""

    # --- get_objectives ---

    @pytest.mark.unit()
    def test_get_objectives_count(self) -> None:
        """Test that get objectives count."""
        assert len(portfolio_optimization_feature_type.get_objectives()) == 4

    @pytest.mark.unit()
    def test_get_objectives_members(self) -> None:
        """Test that get objectives members."""
        objs = set(portfolio_optimization_feature_type.get_objectives())
        expected = {
            portfolio_optimization_feature_type.MINIMIZE_RISK,
            portfolio_optimization_feature_type.MAXIMIZE_RETURNS,
            portfolio_optimization_feature_type.MAXIMIZE_UTILITY,
            portfolio_optimization_feature_type.MAXIMIZE_RATIO,
        }
        assert objs == expected

    @pytest.mark.unit()
    def test_get_objectives_returns_list(self) -> None:
        """Test that get objectives returns list."""
        assert isinstance(portfolio_optimization_feature_type.get_objectives(), list)

    # --- get_costs ---

    @pytest.mark.unit()
    def test_get_costs_count(self) -> None:
        """Test that get costs count."""
        assert len(portfolio_optimization_feature_type.get_costs()) == 2

    @pytest.mark.unit()
    def test_get_costs_members(self) -> None:
        """Test that get costs members."""
        costs = set(portfolio_optimization_feature_type.get_costs())
        expected = {
            portfolio_optimization_feature_type.COSTS_TRANSACTION,
            portfolio_optimization_feature_type.FEES_MANAGEMENT,
        }
        assert costs == expected

    # --- get_regularization ---

    @pytest.mark.unit()
    def test_get_regularization_count(self) -> None:
        """Test that get regularization count."""
        assert len(portfolio_optimization_feature_type.get_regularization()) == 2

    @pytest.mark.unit()
    def test_get_regularization_members(self) -> None:
        """Test that get regularization members."""
        regs = set(portfolio_optimization_feature_type.get_regularization())
        expected = {
            portfolio_optimization_feature_type.REGULARIZATION_L1,
            portfolio_optimization_feature_type.REGULARIZATION_L2,
        }
        assert regs == expected

    # --- get_weight_constraints ---

    @pytest.mark.unit()
    def test_get_weight_constraints_count(self) -> None:
        """Test that get weight constraints count."""
        assert len(portfolio_optimization_feature_type.get_weight_constraints()) == 5

    @pytest.mark.unit()
    def test_get_weight_constraints_members(self) -> None:
        """Test that get weight constraints members."""
        wc = set(portfolio_optimization_feature_type.get_weight_constraints())
        expected = {
            portfolio_optimization_feature_type.CONSTRAINTS_WEIGHT,
            portfolio_optimization_feature_type.CONSTRAINTS_GROUP,
            portfolio_optimization_feature_type.CONSTRAINTS_BUDGET,
            portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_LONG,
            portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_SHORT,
        }
        assert wc == expected

    # --- get_portfolio_constraints ---

    @pytest.mark.unit()
    def test_get_portfolio_constraints_count(self) -> None:
        """Test that get portfolio constraints count."""
        assert len(portfolio_optimization_feature_type.get_portfolio_constraints()) == 6

    @pytest.mark.unit()
    def test_get_portfolio_constraints_members(self) -> None:
        """Test that get portfolio constraints members."""
        pc = set(portfolio_optimization_feature_type.get_portfolio_constraints())
        expected = {
            portfolio_optimization_feature_type.CONSTRAINTS_TRACKING_ERROR,
            portfolio_optimization_feature_type.CONSTRAINTS_TURNOVER,
            portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY,
            portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY_GROUP,
            portfolio_optimization_feature_type.CONSTRAINTS_RISK_MEASURE,
            portfolio_optimization_feature_type.CONSTRAINTS_EXPECTED_RETURN,
        }
        assert pc == expected

    # --- get_all_constraints ---

    @pytest.mark.unit()
    def test_get_all_constraints_count(self) -> None:
        """get_all_constraints = weight (5) + portfolio (6) + custom (1) = 12."""
        assert len(portfolio_optimization_feature_type.get_all_constraints()) == 12

    @pytest.mark.unit()
    def test_get_all_constraints_contains_custom(self) -> None:
        """Test that get all constraints contains custom."""
        all_c = portfolio_optimization_feature_type.get_all_constraints()
        assert portfolio_optimization_feature_type.CONSTRAINTS_CUSTOM in all_c

    @pytest.mark.unit()
    def test_get_all_constraints_contains_weight_constraints(self) -> None:
        """Test that get all constraints contains weight constraints."""
        all_c = set(portfolio_optimization_feature_type.get_all_constraints())
        weight_c = set(portfolio_optimization_feature_type.get_weight_constraints())
        assert weight_c.issubset(all_c)

    @pytest.mark.unit()
    def test_get_all_constraints_contains_portfolio_constraints(self) -> None:
        """Test that get all constraints contains portfolio constraints."""
        all_c = set(portfolio_optimization_feature_type.get_all_constraints())
        port_c = set(portfolio_optimization_feature_type.get_portfolio_constraints())
        assert port_c.issubset(all_c)

    # --- get_robust_optimization_features ---

    @pytest.mark.unit()
    def test_get_robust_optimization_features_count(self) -> None:
        """Test that get robust optimization features count."""
        assert len(portfolio_optimization_feature_type.get_robust_optimization_features()) == 2

    @pytest.mark.unit()
    def test_get_robust_optimization_features_members(self) -> None:
        """Test that get robust optimization features members."""
        rob = set(portfolio_optimization_feature_type.get_robust_optimization_features())
        expected = {
            portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_EXPECTED_RETURNS,
            portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_COVARIANCE,
        }
        assert rob == expected

    # --- get_custom_features ---

    @pytest.mark.unit()
    def test_get_custom_features_count(self) -> None:
        """Test that get custom features count."""
        assert len(portfolio_optimization_feature_type.get_custom_features()) == 3

    @pytest.mark.unit()
    def test_get_custom_features_members(self) -> None:
        """Test that get custom features members."""
        custom = set(portfolio_optimization_feature_type.get_custom_features())
        expected = {
            portfolio_optimization_feature_type.OBJECTIVE_CUSTOM,
            portfolio_optimization_feature_type.CONSTRAINTS_CUSTOM,
            portfolio_optimization_feature_type.ESTIMATOR_PRIOR,
        }
        assert custom == expected

    # --- get_integer_features ---

    @pytest.mark.unit()
    def test_get_integer_features_count(self) -> None:
        """Test that get integer features count."""
        assert len(portfolio_optimization_feature_type.get_integer_features()) == 4

    @pytest.mark.unit()
    def test_get_integer_features_members(self) -> None:
        """Test that get integer features members."""
        ints = set(portfolio_optimization_feature_type.get_integer_features())
        expected = {
            portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY,
            portfolio_optimization_feature_type.CONSTRAINTS_CARDINALITY_GROUP,
            portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_LONG,
            portfolio_optimization_feature_type.CONSTRAINTS_THRESHOLD_SHORT,
        }
        assert ints == expected

    @pytest.mark.unit()
    def test_integer_features_not_in_convex_features(self) -> None:
        """Integer/combinatorial features must NOT be in the convex-features list."""
        integer_f = set(portfolio_optimization_feature_type.get_integer_features())
        convex_f = set(portfolio_optimization_feature_type.get_convex_features())
        # No integer feature should appear in convex (they break convexity)
        assert integer_f.isdisjoint(convex_f)

    # --- get_convex_features ---

    @pytest.mark.unit()
    def test_get_convex_features_count(self) -> None:
        """Test that get convex features count."""
        assert len(portfolio_optimization_feature_type.get_convex_features()) == 13

    @pytest.mark.unit()
    def test_get_convex_features_objectives_included(self) -> None:
        """MINIMIZE_RISK, MAXIMIZE_RETURNS, MAXIMIZE_UTILITY must be convex."""
        convex = set(portfolio_optimization_feature_type.get_convex_features())
        assert portfolio_optimization_feature_type.MINIMIZE_RISK in convex
        assert portfolio_optimization_feature_type.MAXIMIZE_RETURNS in convex
        assert portfolio_optimization_feature_type.MAXIMIZE_UTILITY in convex

    @pytest.mark.unit()
    def test_get_convex_features_robust_included(self) -> None:
        """Robust uncertainty sets must be present in convex features."""
        convex = set(portfolio_optimization_feature_type.get_convex_features())
        assert portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_EXPECTED_RETURNS in convex
        assert portfolio_optimization_feature_type.UNCERTAINTY_SET_ON_COVARIANCE in convex

    # --- return types ---

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_objectives",
            "get_costs",
            "get_regularization",
            "get_weight_constraints",
            "get_portfolio_constraints",
            "get_all_constraints",
            "get_robust_optimization_features",
            "get_custom_features",
            "get_integer_features",
            "get_convex_features",
        ],
    )
    @pytest.mark.unit()
    def test_classmethod_returns_list_of_feature_type(self, method_name: str) -> None:
        """Each classmethod must return a list of portfolio_optimization_feature_type."""
        method = getattr(portfolio_optimization_feature_type, method_name)
        result = method()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, portfolio_optimization_feature_type)
