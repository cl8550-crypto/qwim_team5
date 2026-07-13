"""Behave step definitions for Discounting_Model_Constant.

Tests cover:
    - Construction with valid/invalid discount rates
    - calc_discount_factor: zero time, one year, higher rate comparison
    - calc_present_value: single cash flow, stream of cash flows

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest
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
    from src.models.discounting.model_discounting_constant import (
        Discounting_Model_Constant,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
    from src.utils.dates_times_utils.daycount import Daycount_Convention
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
# Given / When
# ---------------------------------------------------------------------------


@when("I construct a Discounting_Model_Constant with discount_rate {rate:f}")
def step_construct_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.discounting_model = Discounting_Model_Constant(discount_rate=rate)
    context.construction_exception = None


@when("I attempt to construct a Discounting_Model_Constant with discount_rate {rate:f}")
def step_attempt_construct_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.construction_exception = None
    try:
        Discounting_Model_Constant(discount_rate=rate)
    except Exception as exc:  # noqa: BLE001
        context.construction_exception = exc


@when("I calculate the discount factor from {start_str} to {end_str}")
def step_calc_discount_factor(context, start_str: str, end_str: str) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    start_date = datetime.date.fromisoformat(start_str)
    end_date = datetime.date.fromisoformat(end_str)
    context.discount_factor = context.discounting_model.calc_discount_factor(
        end_date=end_date,
        start_date=start_date,
    )


@when(
    "I calculate the present value of {cash_flow:f} at end_date {end_str}"
    " from start_date {start_str}"
)
def step_calc_present_value(
    context, cash_flow: float, end_str: str, start_str: str
) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    end_date = datetime.date.fromisoformat(end_str)
    start_date = datetime.date.fromisoformat(start_str)
    context.present_value = context.discounting_model.calc_present_value(
        cash_flow=cash_flow,
        end_date=end_date,
        start_date=start_date,
    )


@when(
    "I calculate the present value stream for cash flows {cf1:f} {cf2:f}"
    " at end_dates {end1} {end2} from start_date {start_str}"
)
def step_calc_pv_stream(
    context,
    cf1: float,
    cf2: float,
    end1: str,
    end2: str,
    start_str: str,
) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.stream_pv = context.discounting_model.calc_present_value_stream(
        cash_flows=[cf1, cf2],
        end_dates=[
            datetime.date.fromisoformat(end1),
            datetime.date.fromisoformat(end2),
        ],
        start_date=datetime.date.fromisoformat(start_str),
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then("the model discount_rate should be {expected:f}")
def step_check_discount_rate(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.discounting_model.discount_rate - expected) < 1e-12


@then("a validation exception should be raised")
def step_check_validation_exception(context) -> None:  # noqa: ANN001
    assert context.construction_exception is not None
    assert isinstance(context.construction_exception, Exception_Validation_Input)


@then("the discount factor should be approximately {expected:f}")
def step_check_discount_factor_approx(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.discount_factor - expected) < 1e-4


@then("the discount factor should be exactly 1.0")
def step_check_discount_factor_one(context) -> None:  # noqa: ANN001
    assert abs(context.discount_factor - 1.0) < 1e-12


@then("the discount factor should be less than {bound:f}")
def step_check_discount_factor_less_than(context, bound: float) -> None:  # noqa: ANN001
    assert context.discount_factor < bound


@then("the present value should be approximately {expected:f}")
def step_check_present_value_approx(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.present_value - expected) < 0.01


@then("the stream present value should be positive")
def step_check_stream_pv_positive(context) -> None:  # noqa: ANN001
    assert context.stream_pv > 0.0
