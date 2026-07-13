"""
Robot Framework keyword library for Longevity_Model_Constant.
=============================================================

Tests cover:
    - Construction with valid/invalid qx values
    - fit() with empty data and life table data
    - predict() row count, column names, constant qx values

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
    from src.models.longevity.model_longevity_constant import (
        Longevity_Model_Constant,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


class Keywords_Longevity:
    """Robot Framework keyword library for longevity model tests."""

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def check_module_available(self) -> None:
        """Fail if the longevity module could not be imported."""
        if not MODULE_IMPORT_AVAILABLE:
            raise AssertionError(
                f"Longevity module import failed: {_import_error_message}"
            )

    # ------------------------------------------------------------------
    # Construction keywords
    # ------------------------------------------------------------------

    def construct_constant_longevity_model(self, qx: float) -> Longevity_Model_Constant:
        """Create and return a ``Longevity_Model_Constant``.

        Parameters
        ----------
        qx : float
            Annual probability of death (decimal, e.g. 0.02 for 2 %).

        Returns
        -------
        Longevity_Model_Constant
            The constructed model.
        """
        self.check_module_available()
        return Longevity_Model_Constant(qx=float(qx))

    def construct_longevity_model_raises_for_invalid_qx(self, qx: float) -> None:
        """Assert that construction with an out-of-range qx raises a validation error.

        Parameters
        ----------
        qx : float
            Value expected to be invalid (> 0.50).
        """
        self.check_module_available()
        try:
            Longevity_Model_Constant(qx=float(qx))
        except Exception_Validation_Input:
            return
        raise AssertionError(
            f"Expected Exception_Validation_Input for qx={qx}"
        )

    # ------------------------------------------------------------------
    # Fit keywords
    # ------------------------------------------------------------------

    def fit_with_empty_data(self, model: Longevity_Model_Constant) -> None:
        """Fit a longevity model with an empty DataFrame.

        Parameters
        ----------
        model : Longevity_Model_Constant
            The model to fit.
        """
        self.check_module_available()
        model.fit(data = pl.DataFrame())

    def fit_from_life_table(
        self,
        model: Longevity_Model_Constant,
        qx_values: list,
    ) -> None:
        """Fit a longevity model from a list of qx values.

        Parameters
        ----------
        model : Longevity_Model_Constant
            The model to fit.
        qx_values : list
            List of annual death probability values.
        """
        self.check_module_available()
        n = len(qx_values)
        ages = list(range(60, 60 + n * 5, 5))
        life_table = pl.DataFrame(
            {
                "Age": ages[:n],
                "qx": [float(q) for q in qx_values],
            }
        )
        model.fit(data = life_table)

    # ------------------------------------------------------------------
    # Predict keywords
    # ------------------------------------------------------------------

    def predict_n_ages(
        self,
        model: Longevity_Model_Constant,
        n_ages: int,
        start_age: int = 65,
    ) -> "pl.DataFrame":
        """Call predict() and return the resulting DataFrame.

        Parameters
        ----------
        model : Longevity_Model_Constant
            A fitted model.
        n_ages : int
            Number of age steps.
        start_age : int
            Starting age.

        Returns
        -------
        pl.DataFrame
            The prediction DataFrame.
        """
        self.check_module_available()
        return model.predict(n_ages=int(n_ages), start_age=int(start_age))

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

    def prediction_all_qx_equal(
        self, df: "pl.DataFrame", expected_qx: float, tol: float = 1e-12
    ) -> None:
        """Assert all qx values equal expected_qx.

        Parameters
        ----------
        df : pl.DataFrame
            Prediction result.
        expected_qx : float
            Expected constant qx value.
        tol : float
            Absolute tolerance.
        """
        for val in df["qx"].to_list():
            if abs(val - float(expected_qx)) > float(tol):
                raise AssertionError(
                    f"qx {val} not within {tol} of {expected_qx}"
                )

    def prediction_contains_columns(self, df: "pl.DataFrame") -> None:
        """Assert DataFrame contains both Age and qx columns.

        Parameters
        ----------
        df : pl.DataFrame
            Prediction result.
        """
        for col in ("Age", "qx"):
            if col not in df.columns:
                raise AssertionError(f"Missing column: {col}")
