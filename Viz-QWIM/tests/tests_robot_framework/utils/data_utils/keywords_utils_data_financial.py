"""Robot Framework keyword library for utils_data_financial tests.

Tests cover
-----------
Keyword wrappers for expected_returns_estimator_type,
prior_estimator_type, and distribution_estimator_type enum inspection:
member counts, classmethod group returns, disjointness, and full coverage
checks (every member in at least one group).

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-03-01
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so that "src." imports resolve correctly
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard following project coding standards
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.data_utils.utils_data_financial import (
        Distribution_Estimator_Type,
        Expected_Returns_Estimator_Type,
        Prior_Estimator_Type,
    )
    import logging as _logging
    _logger = _logging.getLogger(__name__)
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"utils_data_financial source modules could not be imported: {_import_error_message}"
        )


# ===========================================================================
# expected_returns_estimator_type keywords
# ===========================================================================


def get_expected_returns_member_count() -> int:
    """Return the number of members in expected_returns_estimator_type.

    Returns
    -------
    int
        Number of enum members.
    """
    _require_imports()
    return len(list(Expected_Returns_Estimator_Type))


def get_expected_returns_historical_methods() -> list:
    """Call get_historical_methods on expected_returns_estimator_type.

    Returns
    -------
    list
        List of enum members from the historical group.
    """
    _require_imports()
    return Expected_Returns_Estimator_Type.get_historical_methods()


def get_expected_returns_model_based_methods() -> list:
    """Call get_model_based_methods on expected_returns_estimator_type.

    Returns
    -------
    list
        List of enum members from the model-based group.
    """
    _require_imports()
    return Expected_Returns_Estimator_Type.get_model_based_methods()


def expected_returns_all_members_are_covered() -> bool:
    """Check every expected_returns_estimator_type member appears in at least one group.

    Returns
    -------
    bool
        True if all members are covered.
    """
    _require_imports()
    union: set = set()
    union.update(Expected_Returns_Estimator_Type.get_historical_methods())
    union.update(Expected_Returns_Estimator_Type.get_model_based_methods())
    union.update(Expected_Returns_Estimator_Type.get_distribution_based_methods())
    return all(m in union for m in Expected_Returns_Estimator_Type)


# ===========================================================================
# prior_estimator_type keywords
# ===========================================================================


def get_prior_member_count() -> int:
    """Return the number of members in prior_estimator_type.

    Returns
    -------
    int
        Number of enum members.
    """
    _require_imports()
    return len(list(Prior_Estimator_Type))


def get_prior_data_driven() -> list:
    """Call get_data_driven on prior_estimator_type.

    Returns
    -------
    list
        List of enum members in the data-driven group.
    """
    _require_imports()
    return Prior_Estimator_Type.get_data_driven()


def get_prior_equilibrium_based() -> list:
    """Call get_equilibrium_based on prior_estimator_type.

    Returns
    -------
    list
        List of enum members in the equilibrium-based group.
    """
    _require_imports()
    return Prior_Estimator_Type.get_equilibrium_based()


def prior_all_members_are_covered() -> bool:
    """Check every prior_estimator_type member appears in at least one group.

    Returns
    -------
    bool
        True if all members are covered.
    """
    _require_imports()
    union: set = set()
    for group_fn in [
        Prior_Estimator_Type.get_data_driven,
        Prior_Estimator_Type.get_equilibrium_based,
        Prior_Estimator_Type.get_factor_based,
        Prior_Estimator_Type.get_scenario_based,
        Prior_Estimator_Type.get_probabilistic,
        Prior_Estimator_Type.get_bayesian_methods,
        Prior_Estimator_Type.get_view_incorporation_methods,
    ]:
        union.update(group_fn())
    return all(m in union for m in Prior_Estimator_Type)


# ===========================================================================
# distribution_estimator_type keywords
# ===========================================================================


def get_distribution_member_count() -> int:
    """Return the number of members in distribution_estimator_type.

    Returns
    -------
    int
        Number of enum members.
    """
    _require_imports()
    return len(list(Distribution_Estimator_Type))


def get_distribution_univariate() -> list:
    """Call get_univariate on distribution_estimator_type.

    Returns
    -------
    list
        List of enum members in the univariate group.
    """
    _require_imports()
    return Distribution_Estimator_Type.get_univariate()


def get_distribution_fat_tailed() -> list:
    """Call get_fat_tailed_distributions on distribution_estimator_type.

    Returns
    -------
    list
        List of enum members in the fat-tailed group.
    """
    _require_imports()
    return Distribution_Estimator_Type.get_fat_tailed_distributions()


def get_distribution_simulation_ready() -> list:
    """Call get_simulation_ready on distribution_estimator_type.

    Returns
    -------
    list
        List of enum members considered simulation-ready.
    """
    _require_imports()
    return Distribution_Estimator_Type.get_simulation_ready()


def distribution_all_members_are_covered() -> bool:
    """Check every distribution_estimator_type member appears in at least one group.

    Returns
    -------
    bool
        True if all members are covered.
    """
    _require_imports()
    union: set = set()
    for group_fn in [
        Distribution_Estimator_Type.get_univariate,
        Distribution_Estimator_Type.get_bivariate_copulas,
        Distribution_Estimator_Type.get_multivariate_copulas,
        Distribution_Estimator_Type.get_fat_tailed_distributions,
        Distribution_Estimator_Type.get_flexible_distributions,
    ]:
        union.update(group_fn())
    return all(m in union for m in Distribution_Estimator_Type)


# ===========================================================================
# Shared assertion helpers
# ===========================================================================


def list_should_be_non_empty(lst: list) -> None:
    """Assert that *lst* contains at least one element.

    Parameters
    ----------
    lst : list
        List to check.

    Raises
    ------
    AssertionError
        If *lst* is empty.
    """
    assert len(lst) > 0, f"Expected non-empty list but got: {lst!r}"


def integer_should_equal(actual: int, expected: int) -> None:
    """Assert that two integers are equal.

    Parameters
    ----------
    actual : int
        Observed value.
    expected : int
        Expected value.

    Raises
    ------
    AssertionError
        If values differ.
    """
    assert int(actual) == int(expected), (
        f"Expected {expected}, got {actual}"
    )


def lists_should_be_disjoint(list_a: list, list_b: list) -> None:
    """Assert that two lists share no common elements.

    Parameters
    ----------
    list_a : list
        First list.
    list_b : list
        Second list.

    Raises
    ------
    AssertionError
        If any element appears in both lists.
    """
    common = set(list_a) & set(list_b)
    assert len(common) == 0, (
        f"Expected disjoint lists but found common elements: {common}"
    )


def bool_should_be_true(value: bool) -> None:
    """Assert that *value* is True.

    Parameters
    ----------
    value : bool
        Value to check.

    Raises
    ------
    AssertionError
        If *value* is not True.
    """
    assert value is True, f"Expected True but got {value!r}"
