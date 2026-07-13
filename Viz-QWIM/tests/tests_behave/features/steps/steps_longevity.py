"""Behave step definitions for Longevity_Model_Constant.

Tests cover:
    - Construction with valid/invalid qx values
    - fit() with empty data and life table data
    - predict() row count, column names, constant qx values

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
    import polars as pl
    from src.models.longevity.model_longevity_constant import (
        Longevity_Model_Constant,
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


@when("I construct a Longevity_Model_Constant with qx {qx_val:f}")
def step_construct_longevity_model(context, qx_val: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.longevity_model = Longevity_Model_Constant(qx=qx_val)
    context.longevity_exception = None


@when("I attempt to construct a Longevity_Model_Constant with qx {qx_val:f}")
def step_attempt_construct_longevity_model(context, qx_val: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.longevity_exception = None
    try:
        Longevity_Model_Constant(qx=qx_val)
    except Exception as exc:  # noqa: BLE001
        context.longevity_exception = exc


@when("I fit the longevity model with empty data")
def step_fit_longevity_empty(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.longevity_model.fit(data = pl.DataFrame())


@when(
    "I fit the longevity model from life table qx values {v1:f} {v2:f} {v3:f} {v4:f}"
)
def step_fit_longevity_life_table(
    context, v1: float, v2: float, v3: float, v4: float
) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    life_table = pl.DataFrame(
        {
            "Age": [60, 65, 70, 75],
            "qx": [v1, v2, v3, v4],
        }
    )
    context.longevity_model.fit(data = life_table)


@when("I predict longevity for {n:d} ages from start_age {start_age:d}")
def step_predict_longevity(context, n: int, start_age: int) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.longevity_prediction = context.longevity_model.predict(
        n_ages=n,
        start_age=start_age,
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then("the longevity model qx should be {expected:f}")
def step_check_longevity_qx(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.longevity_model.m_qx - expected) < 1e-12


@then("a longevity validation exception should be raised")
def step_check_longevity_exception(context) -> None:  # noqa: ANN001
    assert context.longevity_exception is not None
    assert isinstance(context.longevity_exception, Exception_Validation_Input)


@then("the longevity prediction has {n:d} rows")
def step_check_longevity_row_count(context, n: int) -> None:  # noqa: ANN001
    assert len(context.longevity_prediction) == n


@then("the longevity prediction all qx values equal {expected:f}")
def step_check_longevity_all_qx_equal(context, expected: float) -> None:  # noqa: ANN001
    for val in context.longevity_prediction["qx"].to_list():
        assert abs(val - expected) < 1e-12


@then("the fitted longevity qx should be approximately {expected:f}")
def step_check_fitted_longevity_qx(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.longevity_model.m_qx - expected) < 1e-4


@then("the longevity prediction contains column {col_name}")
def step_check_longevity_column_exists(context, col_name: str) -> None:  # noqa: ANN001
    assert col_name in context.longevity_prediction.columns
