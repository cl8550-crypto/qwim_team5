"""Behave step definitions for Inflation_Model_Constant.

Tests cover:
    - Construction with valid/invalid annual rates
    - fit() with empty data (uses constructor rate)
    - fit() from historical rates (mean estimation)
    - predict() row count, column names, value equality

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
    from src.models.inflation.model_inflation_constant import (
        Inflation_Model_Constant,
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


@when("I construct an Inflation_Model_Constant with annual_rate {rate:f}")
def step_construct_inflation_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.inflation_model = Inflation_Model_Constant(annual_rate=rate)
    context.inflation_exception = None


@when("I attempt to construct an Inflation_Model_Constant with annual_rate {rate:f}")
def step_attempt_construct_inflation_model(context, rate: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.inflation_exception = None
    try:
        Inflation_Model_Constant(annual_rate=rate)
    except Exception as exc:  # noqa: BLE001
        context.inflation_exception = exc


@when("I fit the inflation model with empty data")
def step_fit_inflation_empty(context) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.inflation_model.fit(data = pl.DataFrame())


@when("I fit the inflation model from historical rates {r1:f} {r2:f} {r3:f}")
def step_fit_inflation_historical(context, r1: float, r2: float, r3: float) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    hist = pl.DataFrame(
        {
            "Date": ["2022-01-01", "2023-01-01", "2024-01-01"],
            "inflation_rate": [r1, r2, r3],
        }
    )
    context.inflation_model.fit(data = hist)


@when("I predict {n:d} inflation periods from start_date {start_str}")
def step_predict_inflation(context, n: int, start_str: str) -> None:  # noqa: ANN001
    _skip_if_unavailable(context)
    context.inflation_prediction = context.inflation_model.predict(
        n_periods=n,
        start_date=start_str,
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then("the inflation model annual_rate should be {expected:f}")
def step_check_inflation_annual_rate(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.inflation_model.m_annual_rate - expected) < 1e-12


@then("an inflation validation exception should be raised")
def step_check_inflation_exception(context) -> None:  # noqa: ANN001
    assert context.inflation_exception is not None
    assert isinstance(context.inflation_exception, Exception_Validation_Input)


@then("the inflation prediction has {n:d} rows")
def step_check_inflation_row_count(context, n: int) -> None:  # noqa: ANN001
    assert len(context.inflation_prediction) == n


@then("the inflation prediction all rates equal {rate:f}")
def step_check_inflation_all_rates_equal(context, rate: float) -> None:  # noqa: ANN001
    for val in context.inflation_prediction["inflation_rate"].to_list():
        assert abs(val - rate) < 1e-12


@then("the fitted inflation annual_rate should be approximately {expected:f}")
def step_check_fitted_annual_rate(context, expected: float) -> None:  # noqa: ANN001
    assert abs(context.inflation_model.m_annual_rate - expected) < 1e-5


@then("the inflation prediction contains column {col_name}")
def step_check_inflation_column_exists(context, col_name: str) -> None:  # noqa: ANN001
    assert col_name in context.inflation_prediction.columns
