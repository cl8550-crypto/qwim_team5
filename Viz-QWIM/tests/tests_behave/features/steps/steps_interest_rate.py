"""Behave step definitions for Interest_Rate_Model_Constant.

Tests cover:
    - Construction with valid/invalid annual rates
    - fit() with empty data and historical rates
    - predict() row count, column names, constant rate values

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
    from src.models.interest_rate.model_interest_rate_constant import (
        Interest_Rate_Model_Constant,
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


@when("I construct an Interest_Rate_Model_Constant with annual_rate {rate:f}")
def step_construct_interest_rate_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.interest_rate_model = Interest_Rate_Model_Constant(annual_rate=rate)
    context.interest_rate_exception = None


@when("I attempt to construct an Interest_Rate_Model_Constant with annual_rate {rate:f}")
def step_attempt_construct_interest_rate_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.interest_rate_exception = None
    try:
        Interest_Rate_Model_Constant(annual_rate=rate)
    except Exception as exc:  # noqa: BLE001
        context.interest_rate_exception = exc


@when("I fit the interest rate model with empty data")
def step_fit_interest_rate_empty(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.interest_rate_model.fit(data = pl.DataFrame())


@when("I fit the interest rate model from historical rates {r1:f} {r2:f} {r3:f} {r4:f}")
def step_fit_interest_rate_historical_four(
    context, r1: float, r2: float, r3: float, r4: float
) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    hist = pl.DataFrame(
        {
            "Date": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"],
            "short_rate": [r1, r2, r3, r4],
        }
    )
    context.interest_rate_model.fit(data = hist)


@when("I predict {n:d} interest rate periods from start_date {start_str}")
def step_predict_interest_rate(context, n: int, start_str: str) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.interest_rate_prediction = context.interest_rate_model.predict(
        n_periods=n,
        start_date=start_str,
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then("the interest rate model annual_rate should be {expected:f}")
def step_check_interest_rate_annual_rate(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.interest_rate_model.m_annual_rate - expected) < 1e-12


@then("an interest rate validation exception should be raised")
def step_check_interest_rate_exception(context) -> None:  # noqa: ANN001
    assert context.interest_rate_exception is not None
    assert isinstance(context.interest_rate_exception, Exception_Validation_Input)


@then("the interest rate prediction has {n:d} rows")
def step_check_interest_rate_row_count(context, n: int) -> None:  # noqa: ANN001
    assert len(context.interest_rate_prediction) == n


@then("the interest rate prediction all rates equal {rate:f}")
def step_check_interest_rate_all_equal(context, rate: float) -> None:  # noqa: ANN001
    for val in context.interest_rate_prediction["short_rate"].to_list():
        assert abs(val - rate) < 1e-12


@then("the fitted interest rate annual_rate should be approximately {expected:f}")
def step_check_fitted_interest_rate(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.interest_rate_model.m_annual_rate - expected) < 1e-4


@then("the interest rate prediction contains column {col_name}")
def step_check_interest_rate_column_exists(context, col_name: str) -> None:  # noqa: ANN001
    assert col_name in context.interest_rate_prediction.columns
