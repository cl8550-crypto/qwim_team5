"""Behave step definitions for Portfolio_Rebalancing_Standard.

Tests cover:
    - Construction with valid/invalid parameters
    - configure() with valid weights and asset names
    - should_rebalance() threshold trigger
    - rebalance() output structure and drift values

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
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
    import numpy as np
    import polars as pl
    from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
        Portfolio_Rebalancing_Standard,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _skip_if_unavailable(context) -> None:  # noqa: ANN001
    if not MODULE_IMPORT_AVAILABLE:
        context.scenario.skip(f"Import unavailable: {_import_error_message}")


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when("I construct a Portfolio_Rebalancing_Standard with default parameters")
def step_construct_default(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.rebalancing_strategy = Portfolio_Rebalancing_Standard()
    context.rebalancing_exception = None
    context.rebalancing_result = None


@when("I attempt to construct a Portfolio_Rebalancing_Standard with tolerance_abs {tol:f}")
def step_attempt_construct_bad_tolerance(context, tol: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.rebalancing_exception = None
    try:
        Portfolio_Rebalancing_Standard(tolerance_abs=tol)
    except Exception as exc:  # noqa: BLE001
        context.rebalancing_exception = exc


@when("I configure the rebalancing strategy with equal weights for {n:d} assets")
def step_configure_equal(context, n: int) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    target = np.ones(n) / n
    names = [f"Asset{i + 1}" for i in range(n)]
    context.rebalancing_strategy.configure(target_weights = target, names_assets = names)


@when("I check should_rebalance with weights {w0:f} {w1:f}")
def step_should_rebalance_two_assets(context, w0: float, w1: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    current = np.array([w0, w1])
    context.should_rebalance_result = context.rebalancing_strategy.should_rebalance(current_weights = current)


@when("I perform a rebalance with weights {w0:f} {w1:f} and portfolio_value {pv:f}")
def step_rebalance_two_assets(context, w0: float, w1: float, pv: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    current = np.array([w0, w1])
    context.rebalancing_result = context.rebalancing_strategy.rebalance(
        current_weights = current, portfolio_value=pv
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then("the rebalancing strategy tolerance_abs should be {expected:f}")
def step_check_tolerance(context, expected: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    assert abs(context.rebalancing_strategy.tolerance_abs - expected) < 1e-9, (
        f"Expected tolerance_abs={expected}, got {context.rebalancing_strategy.tolerance_abs}"
    )


@then("the rebalancing strategy status should be {expected}")
def step_check_status(context, expected: str) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    actual = context.rebalancing_strategy.m_status.value
    assert actual == expected, f"Expected status='{expected}', got '{actual}'"


@then("a rebalancing validation exception should be raised")
def step_check_validation_exception(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    assert context.rebalancing_exception is not None, (
        "Expected a validation exception but none was raised"
    )
    assert isinstance(context.rebalancing_exception, Exception_Validation_Input), (
        f"Expected Exception_Validation_Input, got {type(context.rebalancing_exception)}"
    )


@then("the rebalancing strategy n_assets should be {n:d}")
def step_check_n_assets(context, n: int) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    assert context.rebalancing_strategy.n_assets == n, (
        f"Expected n_assets={n}, got {context.rebalancing_strategy.n_assets}"
    )


@then("should_rebalance should return True")
def step_should_rebalance_true(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    assert context.should_rebalance_result is True, (
        f"Expected True but got {context.should_rebalance_result}"
    )


@then("should_rebalance should return False")
def step_should_rebalance_false(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    assert context.should_rebalance_result is False, (
        f"Expected False but got {context.should_rebalance_result}"
    )


@then("the rebalancing result should have {n:d} columns")
def step_result_columns(context, n: int) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    actual = len(context.rebalancing_result.columns)
    assert actual == n, f"Expected {n} columns, got {actual}"


@then("the rebalancing result should have {n:d} rows")
def step_result_rows(context, n: int) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    actual = len(context.rebalancing_result)
    assert actual == n, f"Expected {n} rows, got {actual}"


@then("the rebalancing result Drift for asset {idx:d} should be approximately {expected:f}")
def step_result_drift(context, idx: int, expected: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    drift_value = context.rebalancing_result["Drift"][idx]
    assert abs(drift_value - expected) < 1e-6, (
        f"Expected Drift[{idx}]={expected}, got {drift_value}"
    )
