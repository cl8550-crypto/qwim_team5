"""Hypothesis property-based tests for Risk_Measure_Type.

Property tests verify structural invariants of ``Risk_Measure_Type``:

- Every member is a valid ``Risk_Measure_Type`` instance.
- ``get_coherent_measures()`` is always a subset of ``get_convex_measures()``.
- Variance-based, VaR-family, drawdown, and higher-moment categories are
  pairwise disjoint.
- All six classmethod category lists are non-empty.
- Random members accessed by index are valid enum instances.

Author: QWIM Development Team
Version: 0.1.0
Last Modified: 2026-05-28
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.risks_metrics.risks.utils_risks import Risk_Measure_Type


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_strategy_any_member = st.sampled_from(list(Risk_Measure_Type))
_all_members = list(Risk_Measure_Type)


# ---------------------------------------------------------------------------
# Member invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Risk_Measure_Type_Members:
    """Property tests for enum member validity."""

    @pytest.mark.unit()
    @given(member=_strategy_any_member)
    @settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_every_sampled_member_is_instance(self, member: Risk_Measure_Type) -> None:
        """Every member drawn by hypothesis is a ``Risk_Measure_Type`` instance."""
        assert isinstance(member, Risk_Measure_Type)

    @pytest.mark.unit()
    @given(member=_strategy_any_member)
    @settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_member_name_equals_value(self, member: Risk_Measure_Type) -> None:
        """For every member, ``member.name == member.value``."""
        assert member.name == member.value

    @pytest.mark.unit()
    @given(index=st.integers(min_value=0, max_value=len(_all_members) - 1))
    @settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_member_accessible_by_index(self, index: int) -> None:
        """Members are accessible by integer index from the full list."""
        member = _all_members[index]
        assert isinstance(member, Risk_Measure_Type)


# ---------------------------------------------------------------------------
# Category invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Risk_Measure_Type_Categories:
    """Property tests for category classmethod invariants."""

    @pytest.mark.unit()
    def Test_all_category_lists_nonempty(self) -> None:
        """All six category classmethods return non-empty lists."""
        assert len(Risk_Measure_Type.get_variance_based_measures()) > 0
        assert len(Risk_Measure_Type.get_var_family_measures()) > 0
        assert len(Risk_Measure_Type.get_drawdown_measures()) > 0
        assert len(Risk_Measure_Type.get_higher_moment_measures()) > 0
        assert len(Risk_Measure_Type.get_coherent_measures()) > 0
        assert len(Risk_Measure_Type.get_convex_measures()) > 0

    @pytest.mark.unit()
    def Test_coherent_is_subset_of_convex(self) -> None:
        """``get_coherent_measures()`` is always a subset of ``get_convex_measures()``."""
        coherent = set(Risk_Measure_Type.get_coherent_measures())
        convex = set(Risk_Measure_Type.get_convex_measures())
        assert coherent.issubset(convex)

    @pytest.mark.unit()
    def Test_variance_var_drawdown_highermom_pairwise_disjoint(self) -> None:
        """Variance-based, VaR-family, drawdown, higher-moment categories are pairwise disjoint."""
        variance = set(Risk_Measure_Type.get_variance_based_measures())
        var_family = set(Risk_Measure_Type.get_var_family_measures())
        drawdown = set(Risk_Measure_Type.get_drawdown_measures())
        higher_mom = set(Risk_Measure_Type.get_higher_moment_measures())

        assert variance.isdisjoint(var_family)
        assert variance.isdisjoint(drawdown)
        assert variance.isdisjoint(higher_mom)
        assert var_family.isdisjoint(drawdown)
        assert var_family.isdisjoint(higher_mom)
        assert drawdown.isdisjoint(higher_mom)

    @pytest.mark.unit()
    @given(member=_strategy_any_member)
    @settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_coherent_member_also_in_convex(self, member: Risk_Measure_Type) -> None:
        """Any member in coherent must also appear in convex."""
        coherent = Risk_Measure_Type.get_coherent_measures()
        convex = Risk_Measure_Type.get_convex_measures()
        if member in coherent:
            assert member in convex

    @pytest.mark.unit()
    @given(member=_strategy_any_member)
    @settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_category_items_are_valid_enum_members(self, member: Risk_Measure_Type) -> None:
        """All items returned by any category classmethod are ``Risk_Measure_Type`` instances."""
        all_items = (
            Risk_Measure_Type.get_variance_based_measures()
            + Risk_Measure_Type.get_var_family_measures()
            + Risk_Measure_Type.get_drawdown_measures()
            + Risk_Measure_Type.get_higher_moment_measures()
        )
        for item in all_items:
            assert isinstance(item, Risk_Measure_Type)
