"""
Robot Framework keyword library for Yield Curve models.
========================================================

Tests cover:
    - Construction of constant and Nelson-Siegel models
    - fit() with market data and empty DataFrame
    - predict() output shape and columns
    - get_par_yield() and get_forward_rate() return values
    - Validation error handling

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Robot Framework / stderr patch
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")

# ---------------------------------------------------------------------------
# Conditional imports
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    import polars as pl
    from src.models.yield_curve.model_yield_curve_base import Yield_Curve_Model_Status
    from src.models.yield_curve.model_yield_curve_constant import Yield_Curve_Model_Constant
    from src.models.yield_curve.model_yield_curve_standard import Yield_Curve_Model_Standard
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


# ---------------------------------------------------------------------------
# Market data constant
# ---------------------------------------------------------------------------

_MARKET_DATA = pl.DataFrame(
    {
        "Maturity": [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
        "Yield": [0.020, 0.025, 0.030, 0.035, 0.040, 0.045, 0.048, 0.050],
    }
)


class Keywords_Yield_Curve:
    """Robot Framework keyword library for yield curve model tests."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def construct_constant_model_default(self) -> Yield_Curve_Model_Constant:
        """Construct a Yield_Curve_Model_Constant with default flat rate.

        Returns the unfitted model instance.
        """
        return Yield_Curve_Model_Constant()

    def construct_constant_model_with_rate(self, rate: float) -> Yield_Curve_Model_Constant:
        """Construct a Yield_Curve_Model_Constant with a given flat rate."""
        return Yield_Curve_Model_Constant(flat_rate=float(rate))

    def construct_standard_model(self) -> Yield_Curve_Model_Standard:
        """Construct a Yield_Curve_Model_Standard with default parameters."""
        return Yield_Curve_Model_Standard()

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit_model_to_market_data(self, model) -> None:
        """Fit *model* to the built-in market yield data (in-place)."""
        model.fit(data = _MARKET_DATA)

    def fit_model_to_empty_data(self, model) -> None:
        """Fit *model* to an empty DataFrame (no-op for constant model)."""
        model.fit(data = pl.DataFrame())

    # ------------------------------------------------------------------
    # Status checks
    # ------------------------------------------------------------------

    def model_is_fitted(self, model) -> bool:
        """Return True if *model* has been fitted."""
        return model.m_status == Yield_Curve_Model_Status.FITTED

    def model_name_is(self, model, expected_name: str) -> bool:
        """Return True if model name matches *expected_name*."""
        return model.m_name_model == expected_name

    # ------------------------------------------------------------------
    # Predict helpers
    # ------------------------------------------------------------------

    def predict_at_standard_maturities(self, model) -> pl.DataFrame:
        """Predict yields at [1.0, 5.0, 10.0, 30.0] maturities."""
        return model.predict(maturities=[1.0, 5.0, 10.0, 30.0])

    def predicted_df_has_column(self, df: pl.DataFrame, col: str) -> bool:
        """Return True if *df* has the specified column."""
        return col in df.columns

    def predicted_df_row_count(self, df: pl.DataFrame) -> int:
        """Return number of rows in *df*."""
        return len(df)

    def all_yields_equal(self, df: pl.DataFrame, expected_rate: float) -> bool:
        """Return True if all Yield values in *df* equal *expected_rate*."""
        tol = 1e-12
        return all(abs(y - float(expected_rate)) < tol for y in df["Yield"].to_list())

    # ------------------------------------------------------------------
    # Par yield / forward rate
    # ------------------------------------------------------------------

    def get_par_yield_at_maturity(self, model, maturity: float) -> float:
        """Return get_par_yield(*maturity*) for the fitted *model*."""
        return model.get_par_yield(maturity = float(maturity))

    def get_forward_rate_at_maturity(self, model, maturity: float) -> float:
        """Return get_forward_rate(*maturity*) for the fitted *model*."""
        return model.get_forward_rate(maturity = float(maturity))

    def par_yield_equals_flat_rate(self, model, maturity: float) -> bool:
        """Return True if par yield at *maturity* equals the flat rate."""
        return abs(model.get_par_yield(maturity = float(maturity)) - model.m_flat_rate) < 1e-12

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def constructing_constant_with_invalid_rate_raises(self, rate: float) -> bool:
        """Return True if constructing with *rate* raises Exception_Validation_Input."""
        try:
            Yield_Curve_Model_Constant(flat_rate=float(rate))
            return False
        except Exception_Validation_Input:
            return True

    def constructing_standard_with_invalid_lambda_raises(self, lam: float) -> bool:
        """Return True if constructing NS model with *lam* raises Exception_Validation_Input."""
        try:
            Yield_Curve_Model_Standard(lambda_=float(lam))
            return False
        except Exception_Validation_Input:
            return True
