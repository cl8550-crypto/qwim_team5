"""
Robot Framework keyword library for Discounting_Model_Constant.
=============================================================

Tests cover:
    - Construction with valid discount rates
    - Construction with rate <= -1 raises Exception_Validation_Input
    - calc_discount_factor: zero time, one year at 5%, higher rate comparison
    - calc_present_value: single cash flow
    - calc_present_value_stream: multi-cash-flow positivity
    - All four day-count conventions give finite positive factors

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import datetime
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
    from src.models.discounting.model_discounting_constant import (
        Discounting_Model_Constant,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
    from src.utils.dates_times_utils.daycount import Daycount_Convention
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


class Keywords_Discounting:
    """Robot Framework keyword library for discounting model tests."""

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def check_module_available(self) -> None:
        """Fail if the discounting module could not be imported."""
        if not MODULE_IMPORT_AVAILABLE:
            raise AssertionError(
                f"Discounting module import failed: {_import_error_message}"
            )

    # ------------------------------------------------------------------
    # Construction keywords
    # ------------------------------------------------------------------

    def construct_constant_model(self, discount_rate: float) -> Discounting_Model_Constant:
        """Create and return a ``Discounting_Model_Constant``.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate (decimal, e.g. 0.05 for 5 %).

        Returns
        -------
        Discounting_Model_Constant
            The constructed model.
        """
        self.check_module_available()
        return Discounting_Model_Constant(discount_rate=float(discount_rate))

    def construct_constant_model_raises_for_invalid_rate(
        self, discount_rate: float
    ) -> None:
        """Assert that construction with rate <= -1 raises a validation error.

        Parameters
        ----------
        discount_rate : float
            Rate expected to be invalid (must be <= -1).
        """
        self.check_module_available()
        try:
            Discounting_Model_Constant(discount_rate=float(discount_rate))
        except Exception_Validation_Input:
            return
        raise AssertionError(
            f"Expected Exception_Validation_Input for rate={discount_rate}"
        )

    # ------------------------------------------------------------------
    # Discount factor keywords
    # ------------------------------------------------------------------

    def discount_factor_zero_time_equals_one(
        self, discount_rate: float, date_str: str
    ) -> None:
        """Assert that discount factor is 1 when start == end.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate.
        date_str : str
            ISO date string used as both start and end.
        """
        self.check_module_available()
        model = Discounting_Model_Constant(discount_rate=float(discount_rate))
        d = datetime.date.fromisoformat(date_str)
        factor = model.calc_discount_factor(end_date=d, start_date=d)
        if abs(factor - 1.0) > 1e-12:
            raise AssertionError(
                f"Expected 1.0 for zero time, got {factor}"
            )

    def discount_factor_one_year_approx(
        self,
        discount_rate: float,
        start_str: str,
        end_str: str,
        expected: float,
        tol: float = 1e-4,
    ) -> None:
        """Assert discount factor is approximately equal to expected value.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate.
        start_str : str
            ISO start date.
        end_str : str
            ISO end date.
        expected : float
            Expected discount factor.
        tol : float
            Absolute tolerance (default 1e-4).
        """
        self.check_module_available()
        model = Discounting_Model_Constant(discount_rate=float(discount_rate))
        start_date = datetime.date.fromisoformat(start_str)
        end_date = datetime.date.fromisoformat(end_str)
        factor = model.calc_discount_factor(end_date=end_date, start_date=start_date)
        if abs(factor - float(expected)) > float(tol):
            raise AssertionError(
                f"Discount factor {factor} not within {tol} of {expected}"
            )

    def discount_factor_monotone_in_rate(
        self,
        low_rate: float,
        high_rate: float,
        start_str: str,
        end_str: str,
    ) -> None:
        """Assert higher rate produces smaller discount factor.

        Parameters
        ----------
        low_rate : float
            Lower discount rate.
        high_rate : float
            Higher discount rate.
        start_str : str
            ISO start date.
        end_str : str
            ISO end date.
        """
        self.check_module_available()
        start_date = datetime.date.fromisoformat(start_str)
        end_date = datetime.date.fromisoformat(end_str)
        model_low = Discounting_Model_Constant(discount_rate=float(low_rate))
        model_high = Discounting_Model_Constant(discount_rate=float(high_rate))
        factor_low = model_low.calc_discount_factor(end_date=end_date, start_date=start_date)
        factor_high = model_high.calc_discount_factor(end_date=end_date, start_date=start_date)
        if not (factor_high < factor_low):
            raise AssertionError(
                f"Expected factor_high({factor_high}) < factor_low({factor_low})"
            )

    def all_conventions_give_finite_positive_factor(
        self, discount_rate: float, start_str: str, end_str: str
    ) -> None:
        """Assert all daycount conventions give a finite, positive factor.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate.
        start_str : str
            ISO start date.
        end_str : str
            ISO end date.
        """
        self.check_module_available()
        start_date = datetime.date.fromisoformat(start_str)
        end_date = datetime.date.fromisoformat(end_str)
        model = Discounting_Model_Constant(discount_rate=float(discount_rate))
        for conv in Daycount_Convention:
            factor = model.calc_discount_factor(
                end_date=end_date, start_date=start_date, daycount_convention=conv
            )
            import math
            if not (math.isfinite(factor) and factor > 0):
                raise AssertionError(
                    f"Convention {conv.name}: expected finite positive, got {factor}"
                )

    # ------------------------------------------------------------------
    # Present value keywords
    # ------------------------------------------------------------------

    def present_value_approx(
        self,
        discount_rate: float,
        cash_flow: float,
        start_str: str,
        end_str: str,
        expected: float,
        tol: float = 0.01,
    ) -> None:
        """Assert present value is approximately equal to expected.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate.
        cash_flow : float
            Future cash flow amount.
        start_str : str
            ISO valuation date.
        end_str : str
            ISO payment date.
        expected : float
            Expected present value.
        tol : float
            Absolute tolerance (default 0.01).
        """
        self.check_module_available()
        model = Discounting_Model_Constant(discount_rate=float(discount_rate))
        pv = model.calc_present_value(
            cash_flow=float(cash_flow),
            end_date=datetime.date.fromisoformat(end_str),
            start_date=datetime.date.fromisoformat(start_str),
        )
        if abs(pv - float(expected)) > float(tol):
            raise AssertionError(
                f"PV {pv} not within {tol} of {expected}"
            )

    def present_value_stream_is_positive(
        self,
        discount_rate: float,
        cash_flows: list,
        start_str: str,
        end_dates: list,
    ) -> None:
        """Assert total PV of a cash flow stream is positive.

        Parameters
        ----------
        discount_rate : float
            Annual discount rate.
        cash_flows : list
            List of future cash flows (floats).
        start_str : str
            ISO valuation date.
        end_dates : list
            List of ISO end date strings.
        """
        self.check_module_available()
        model = Discounting_Model_Constant(discount_rate=float(discount_rate))
        total_pv = model.calc_present_value_stream(
            cash_flows=[float(cf) for cf in cash_flows],
            end_dates=[datetime.date.fromisoformat(d) for d in end_dates],
            start_date=datetime.date.fromisoformat(start_str),
        )
        if not (total_pv > 0):
            raise AssertionError(f"Expected positive total PV, got {total_pv}")
