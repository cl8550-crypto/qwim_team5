"""Behave step definitions for yield_curve models.

Tests cover:
    - Construction of constant and Nelson-Siegel models
    - fit() with market data and empty DataFrame
    - predict() output columns and values
    - Validation errors

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
    from src.models.yield_curve.model_yield_curve_constant import Yield_Curve_Model_Constant
    from src.models.yield_curve.model_yield_curve_standard import Yield_Curve_Model_Standard
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


# ---------------------------------------------------------------------------
# Market data used across scenarios
# ---------------------------------------------------------------------------

_MARKET_DATA = pl.DataFrame(
    {
        "Maturity": [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
        "Yield": [0.020, 0.025, 0.030, 0.035, 0.040, 0.045, 0.048, 0.050],
    }
)


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------


@given("market yield data is available")
def step_market_data_available(context) -> None:
    """Store market data in context."""
    context.market_data = _MARKET_DATA
    context.model = None
    context.predicted_df = None
    context.raised_exception = None


# ---------------------------------------------------------------------------
# Construction steps
# ---------------------------------------------------------------------------


@when("I construct a constant yield curve model with default parameters")
def step_construct_constant_default(context) -> None:
    """Construct a Yield_Curve_Model_Constant with defaults."""
    context.model = Yield_Curve_Model_Constant()


@when("I construct a constant yield curve model with flat rate {rate:f}")
def step_construct_constant_with_rate(context, rate: float) -> None:
    """Construct a Yield_Curve_Model_Constant with a specific flat rate."""
    context.model = Yield_Curve_Model_Constant(flat_rate=rate)


@when("I construct a Nelson-Siegel yield curve model")
def step_construct_standard(context) -> None:
    """Construct a Yield_Curve_Model_Standard with defaults."""
    context.model = Yield_Curve_Model_Standard()


@when("I attempt to construct a constant model with flat rate {rate:f}")
def step_attempt_construct_constant_invalid(context, rate: float) -> None:
    """Attempt to construct a constant model with an invalid flat rate."""
    try:
        context.model = Yield_Curve_Model_Constant(flat_rate=rate)
    except Exception as exc:
        context.raised_exception = exc


@when("I attempt to construct a Nelson-Siegel model with lambda {lam:f}")
def step_attempt_construct_standard_invalid_lambda(context, lam: float) -> None:
    """Attempt to construct an NS model with an invalid lambda."""
    try:
        context.model = Yield_Curve_Model_Standard(lambda_=lam)
    except Exception as exc:
        context.raised_exception = exc


# ---------------------------------------------------------------------------
# Fit steps
# ---------------------------------------------------------------------------


@when("I fit the model to market data")
def step_fit_market_data(context) -> None:
    """Fit the model to market data stored in context."""
    context.model.fit(data = context.market_data)


@when("I fit the model to an empty DataFrame")
def step_fit_empty_df(context) -> None:
    """Fit the model to an empty DataFrame (no-op for constant model)."""
    context.model.fit(data = pl.DataFrame())


# ---------------------------------------------------------------------------
# Predict steps
# ---------------------------------------------------------------------------


@when("I predict yields at maturities {m1:f} {m2:f} {m3:f}")
def step_predict_three_maturities(context, m1: float, m2: float, m3: float) -> None:
    """Predict yields at three maturities."""
    context.predicted_df = context.model.predict(maturities=[m1, m2, m3])


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then('the model name should be "{name}"')
def step_check_model_name(context, name: str) -> None:
    """Assert model name attribute."""
    assert context.model.m_name_model == name, (
        f"Expected '{name}', got '{context.model.m_name_model}'"
    )


@then("the model should not be fitted")
def step_model_not_fitted(context) -> None:
    """Assert the model has not been fitted."""
    from src.models.yield_curve.model_yield_curve_base import Yield_Curve_Model_Status
    assert context.model.m_status != Yield_Curve_Model_Status.FITTED


@then("the model should be fitted")
def step_model_fitted(context) -> None:
    """Assert the model has been fitted."""
    from src.models.yield_curve.model_yield_curve_base import Yield_Curve_Model_Status
    assert context.model.m_status == Yield_Curve_Model_Status.FITTED


@then("the flat rate should be the mean of market yields")
def step_flat_rate_is_mean(context) -> None:
    """Assert flat rate equals the mean of the market yield column."""
    import numpy as np
    expected_mean = float(
        context.market_data["Yield"].to_numpy().mean()
    )
    assert abs(context.model.m_flat_rate - expected_mean) < 1e-9, (
        f"Expected flat_rate={expected_mean}, got {context.model.m_flat_rate}"
    )


@then("all predicted yields should equal {rate:f}")
def step_all_yields_equal(context, rate: float) -> None:
    """Assert all predicted Yield values equal the given rate."""
    for y in context.predicted_df["Yield"].to_list():
        assert abs(y - rate) < 1e-12, f"Expected {rate}, got {y}"


@then("the Nelson-Siegel model parameters should include beta0")
def step_ns_has_beta0(context) -> None:
    """Assert the NS model has the m_beta0 attribute after fitting."""
    assert hasattr(context.model, "m_beta0"), "Model missing m_beta0"
    assert isinstance(context.model.m_beta0, float)


@then('the predicted DataFrame should contain column "{col}"')
def step_df_has_column(context, col: str) -> None:
    """Assert the predicted DataFrame has the specified column."""
    assert col in context.predicted_df.columns, (
        f"Column '{col}' not found in {context.predicted_df.columns}"
    )


@then("an Exception_Validation_Input should be raised")
def step_exception_raised(context) -> None:
    """Assert an Exception_Validation_Input was raised."""
    assert isinstance(context.raised_exception, Exception_Validation_Input), (
        f"Expected Exception_Validation_Input, got {type(context.raised_exception)}"
    )
