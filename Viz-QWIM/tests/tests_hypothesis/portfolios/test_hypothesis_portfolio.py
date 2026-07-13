"""Hypothesis property-based tests for portfolio_QWIM.

Property tests verify structural invariants of the ``portfolio_QWIM`` class:

- Constructor from names_components creates equal weights summing to ~1.
- Number of components matches len(names_components).
- Portfolio name is stored correctly.
- Component names are unique and non-empty.
- get_portfolio_components, get_portfolio_name, get_num_components properties
  return consistent values.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.portfolios.portfolio_QWIM import Portfolio_QWIM


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_strategy_component_name = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=20,
)

_strategy_portfolio_name = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=60,
)


def _strategy_unique_components(min_size: int = 1, max_size: int = 10):
    """Strategy producing lists of unique, non-empty component names."""
    return st.lists(
        _strategy_component_name,
        min_size=min_size,
        max_size=max_size,
        unique=True,
    ).filter(lambda lst: all(len(n.strip()) > 0 for n in lst))


# ---------------------------------------------------------------------------
# Construction from names_components
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Portfolio_QWIM_From_Names:
    """Property tests for ``portfolio_QWIM`` constructed from component names."""

    @pytest.mark.unit()
    @given(
        name_portfolio=_strategy_portfolio_name,
        names_components=_strategy_unique_components(min_size=1, max_size=8),
    )
    @settings(max_examples=200)
    def Test_portfolio_name_stored_correctly(
        self,
        name_portfolio: str,
        names_components: list[str],
    ) -> None:
        """Portfolio name is stored (stripped) correctly."""
        assume(len(name_portfolio.strip()) > 0)
        portfolio_obj = Portfolio_QWIM(
            name_portfolio=name_portfolio,
            names_components=names_components,
        )
        assert portfolio_obj.get_portfolio_name == name_portfolio.strip()

    @pytest.mark.unit()
    @given(
        name_portfolio=_strategy_portfolio_name,
        names_components=_strategy_unique_components(min_size=1, max_size=8),
    )
    @settings(max_examples=200)
    def Test_num_components_matches_input(
        self,
        name_portfolio: str,
        names_components: list[str],
    ) -> None:
        """Number of components equals len(names_components)."""
        assume(len(name_portfolio.strip()) > 0)
        portfolio_obj = Portfolio_QWIM(
            name_portfolio=name_portfolio,
            names_components=names_components,
        )
        assert portfolio_obj.get_num_components == len(names_components)

    @pytest.mark.unit()
    @given(
        name_portfolio=_strategy_portfolio_name,
        names_components=_strategy_unique_components(min_size=1, max_size=8),
    )
    @settings(max_examples=200)
    def Test_equal_weights_sum_to_one(
        self,
        name_portfolio: str,
        names_components: list[str],
    ) -> None:
        """Initial equal weights sum to approximately 1.0."""
        assume(len(name_portfolio.strip()) > 0)
        portfolio_obj = Portfolio_QWIM(
            name_portfolio=name_portfolio,
            names_components=names_components,
        )
        df = portfolio_obj.get_portfolio_weights()
        # sum weights across all component columns for the single row
        weight_sum = sum(
            df[item_col][0] for item_col in portfolio_obj.get_portfolio_components
        )
        assert math.isclose(weight_sum, 1.0, rel_tol=1e-9, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(
        name_portfolio=_strategy_portfolio_name,
        names_components=_strategy_unique_components(min_size=2, max_size=8),
    )
    @settings(max_examples=200)
    def Test_each_weight_equals_one_over_n(
        self,
        name_portfolio: str,
        names_components: list[str],
    ) -> None:
        """Each initial weight equals 1/n_components."""
        assume(len(name_portfolio.strip()) > 0)
        portfolio_obj = Portfolio_QWIM(
            name_portfolio=name_portfolio,
            names_components=names_components,
        )
        df = portfolio_obj.get_portfolio_weights()
        n_comp = len(names_components)
        expected_weight = 1.0 / n_comp
        for item_comp in portfolio_obj.get_portfolio_components:
            assert math.isclose(df[item_comp][0], expected_weight, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        name_portfolio=_strategy_portfolio_name,
        names_components=_strategy_unique_components(min_size=1, max_size=8),
    )
    @settings(max_examples=200)
    def Test_component_names_match_input(
        self,
        name_portfolio: str,
        names_components: list[str],
    ) -> None:
        """Stored component names equal the (stripped) input names."""
        assume(len(name_portfolio.strip()) > 0)
        portfolio_obj = Portfolio_QWIM(
            name_portfolio=name_portfolio,
            names_components=names_components,
        )
        stored = portfolio_obj.get_portfolio_components
        stripped_input = [n.strip() for n in names_components]
        assert stored == stripped_input
