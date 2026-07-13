"""
Robot Framework keyword library for Inflation_Model_Constant.
=============================================================

Tests cover:
    - Construction with valid/invalid annual rates
    - fit() with empty data and historical data
    - predict() row count, column names, constant rate values

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
    from src.models.inflation.model_inflation_constant import (
        Inflation_Model_Constant,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


class Keywords_Inflation:
    """Robot Framework keyword library for inflation model tests."""

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def check_module_available(self) -> None:
        """Fail if the inflation module could not be imported."""
        if not MODULE_IMPORT_AVAILABLE:
            raise AssertionError(
                f"Inflation module import failed: {_import_error_message}"
            )

    # ------------------------------------------------------------------
    # Construction keywords
    # ------------------------------------------------------------------

    def construct_constant_inflation_model(
        self, annual_rate: float
    ) -> Inflation_Model_Constant:
        """Create and return an ``Inflation_Model_Constant``.

        Parameters
        ----------
        annual_rate : float
            Annual inflation rate (decimal).

        Returns
        -------
        Inflation_Model_Constant
            The constructed model.
        """
        self.check_module_available()
        return Inflation_Model_Constant(annual_rate=float(annual_rate))

    def construct_inflation_model_raises_for_invalid_rate(
        self, annual_rate: float
    ) -> None:
        """Assert that construction with an out-of-range rate raises a validation error.

        Parameters
        ----------
        annual_rate : float
            Rate expected to be invalid (> 1.0 or < -0.5).
        """
        self.check_module_available()
        try:
            Inflation_Model_Constant(annual_rate=float(annual_rate))
        except Exception_Validation_Input:
            return
        raise AssertionError(
            f"Expected Exception_Validation_Input for annual_rate={annual_rate}"
        )

    # ------------------------------------------------------------------
    # Fit keywords
    # ------------------------------------------------------------------

    def fit_with_empty_data(self, model: Inflation_Model_Constant) -> None:
        """Fit an inflation model with an empty DataFrame.

        Parameters
        ----------
        model : Inflation_Model_Constant
            The model to fit.
        """
        self.check_module_available()
        model.fit(data = pl.DataFrame())

    def fit_from_historical_rates(
        self,
        model: Inflation_Model_Constant,
        rates: list,
    ) -> None:
        """Fit an inflation model from a list of historical annual rates.

        Parameters
        ----------
        model : Inflation_Model_Constant
            The model to fit.
        rates : list
            List of historical annual inflation rates (floats).
        """
        self.check_module_available()
        n = len(rates)
        import datetime
        dates = [
            (datetime.date(2020 + i, 1, 1)).isoformat() for i in range(n)
        ]
        hist = pl.DataFrame(
            {
                "Date": dates,
                "inflation_rate": [float(r) for r in rates],
            }
        )
        model.fit(data = hist)

    # ------------------------------------------------------------------
    # Predict keywords
    # ------------------------------------------------------------------

    def predict_n_periods(
        self,
        model: Inflation_Model_Constant,
        n_periods: int,
        start_date: str = "2025-01-01",
    ) -> "pl.DataFrame":
        """Call predict() and return the resulting DataFrame.

        Parameters
        ----------
        model : Inflation_Model_Constant
            A fitted model.
        n_periods : int
            Number of periods to project.
        start_date : str
            ISO start date string.

        Returns
        -------
        pl.DataFrame
            The prediction DataFrame.
        """
        self.check_module_available()
        return model.predict(n_periods=int(n_periods), start_date=start_date)

    def prediction_has_n_rows(self, df: "pl.DataFrame", expected_rows: int) -> None:
        """Assert DataFrame has exactly expected_rows rows.

        Parameters
        ----------
        df : pl.DataFrame
            Prediction result.
        expected_rows : int
            Expected number of rows.
        """
        actual = len(df)
        if actual != int(expected_rows):
            raise AssertionError(
                f"Expected {expected_rows} rows, got {actual}"
            )

    def prediction_all_rates_equal(
        self, df: "pl.DataFrame", expected_rate: float, tol: float = 1e-12
    ) -> None:
        """Assert all inflation_rate values equal expected_rate.

        Parameters
        ----------
        df : pl.DataFrame
            Prediction result.
        expected_rate : float
            Expected constant inflation rate.
        tol : float
            Absolute tolerance.
        """
        for val in df["inflation_rate"].to_list():
            if abs(val - float(expected_rate)) > float(tol):
                raise AssertionError(
                    f"Rate {val} not within {tol} of {expected_rate}"
                )

    def prediction_contains_columns(self, df: "pl.DataFrame") -> None:
        """Assert DataFrame contains both Date and inflation_rate columns.

        Parameters
        ----------
        df : pl.DataFrame
            Prediction result.
        """
        for col in ("Date", "inflation_rate"):
            if col not in df.columns:
                raise AssertionError(f"Missing column: {col}")
