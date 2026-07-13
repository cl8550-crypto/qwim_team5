"""Behave step definitions for risks_metrics.utils_risks.

Tests cover:
    - Risk_Measure_Type enum member access
    - Category classmethod retrieval (variance, VaR-family, drawdown,
      higher-moment, coherent, convex)
    - Membership checks: specific members in their expected categories
    - Subset relationship: coherent ⊆ convex

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path — step files live 4 levels below the root:
#   tests/tests_behave/features/steps/<this file>
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.risks_metrics.risks.utils_risks import Risk_Measure_Type
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when required imports are unavailable."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"risks_metrics.utils_risks not importable: {_import_error_message}"
        )


# ===========================================================================
# When — member access
# ===========================================================================


@when(u'I access the Risk_Measure_Type member "{member_name}"')
def step_access_member(context, member_name: str) -> None:
    """Look up an enum member by name and store on context."""
    _require_imports()
    context.member = Risk_Measure_Type[member_name]


# ===========================================================================
# When — category retrieval
# ===========================================================================


@when(u"I retrieve the variance-based measures")
def step_retrieve_variance_based(context) -> None:
    """Store variance-based category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_variance_based_measures()


@when(u"I retrieve the VaR-family measures")
def step_retrieve_var_family(context) -> None:
    """Store VaR-family category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_var_family_measures()


@when(u"I retrieve the drawdown measures")
def step_retrieve_drawdown(context) -> None:
    """Store drawdown category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_drawdown_measures()


@when(u"I retrieve the higher-moment measures")
def step_retrieve_higher_moment(context) -> None:
    """Store higher-moment category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_higher_moment_measures()


@when(u"I retrieve the coherent measures")
def step_retrieve_coherent(context) -> None:
    """Store coherent category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_coherent_measures()


@when(u"I also retrieve the convex measures")
def step_also_retrieve_convex(context) -> None:
    """Store convex category list alongside existing coherent list."""
    _require_imports()
    context.convex_list = Risk_Measure_Type.get_convex_measures()


@when(u"I retrieve the convex measures")
def step_retrieve_convex(context) -> None:
    """Store convex category list on context."""
    _require_imports()
    context.category_list = Risk_Measure_Type.get_convex_measures()


# ===========================================================================
# Then — assertions
# ===========================================================================


@then(u'the member name should be "{expected_name}"')
def step_assert_member_name(context, expected_name: str) -> None:
    """Assert the stored member's name equals expected_name."""
    assert context.member.name == expected_name, (
        f"Expected member name '{expected_name}', got '{context.member.name}'"
    )


@then(u"the category list should be non-empty")
def step_assert_category_nonempty(context) -> None:
    """Assert the stored category list is not empty."""
    assert len(context.category_list) > 0, "Category list should not be empty"


@then(u'"{member_name}" should be in the category list')
def step_assert_member_in_category(context, member_name: str) -> None:
    """Assert the named member appears in the stored category list."""
    member = Risk_Measure_Type[member_name]
    assert member in context.category_list, (
        f"Expected {member_name} to be in category list, "
        f"but list is {[m.name for m in context.category_list]}"
    )


@then(u"the coherent set should be a subset of the convex set")
def step_assert_coherent_subset_convex(context) -> None:
    """Assert the coherent category list is a subset of the convex category list."""
    coherent_set = set(context.category_list)
    convex_set = set(context.convex_list)
    assert coherent_set.issubset(convex_set), (
        f"Coherent members not in convex: "
        f"{[m.name for m in coherent_set - convex_set]}"
    )
