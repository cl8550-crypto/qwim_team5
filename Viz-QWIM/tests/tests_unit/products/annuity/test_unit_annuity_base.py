"""Unit tests for Annuity_Base abstract class.

Tests cover base-class validation paths and fallback method implementations
that are not exercised by any concrete subclass (all concrete implementations
override ``get_annuity_as_string``).

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-27)
"""

from __future__ import annotations

import polars as pl
import pytest

from src.products.annuity.annuity_base import Annuity_Base, Annuity_Type, Withdrawal_Rates
from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_Validation_Input


# ---------------------------------------------------------------------------
# Minimal concrete stub (does NOT override get_annuity_as_string)
# ---------------------------------------------------------------------------


class _ConcreteAnnuityStub(Annuity_Base):
    """Minimal Annuity_Base subclass used only for base-class unit tests.

    Accepts ``annuity_type`` as a constructor parameter so that the invalid-
    type validation path in ``Annuity_Base.__init__`` can be reached.
    Does **not** override ``get_annuity_as_string``, allowing the base-class
    fallback implementation to be executed.
    """

    def __init__(
        self,
        client_age: int,
        annuity_payout_rate: float,
        annuity_type: Annuity_Type,
        annuity_income_starting_age: int | None = None,
    ) -> None:
        super().__init__(
            client_age,
            annuity_payout_rate,
            annuity_type,  # type: ignore[arg-type]
            annuity_income_starting_age=annuity_income_starting_age,
        )

    def calc_annuity_payout(
        self,
        amount_principal: float,
        obj_scenarios: pl.DataFrame | None = None,
        obj_inflation: pl.DataFrame | None = None,
    ) -> float:
        return amount_principal * self.m_annuity_payout_rate

    def calc_withdrawal_rates(
        self,
        amount_principal: float,
        desired_WR: float | None = None,
        obj_scenarios: pl.DataFrame | None = None,
        obj_inflation: pl.DataFrame | None = None,
    ) -> Withdrawal_Rates:
        rate = desired_WR if desired_WR is not None else self.m_annuity_payout_rate
        return Withdrawal_Rates(nominal_WR=rate, real_WR=rate)


# ======================================================================
# Tests: Annuity_Base.__init__ — annuity_type validation
# ======================================================================


@pytest.mark.unit()
class Test_Annuity_Base_Invalid_Type:
    """Test that Annuity_Base raises on an invalid annuity_type argument."""

    @pytest.mark.unit()
    def test_invalid_annuity_type_raises(self) -> None:
        """Non-Annuity_Type value should raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteAnnuityStub(
                client_age=65,
                annuity_payout_rate=0.05,
                annuity_type="INVALID",  # type: ignore[arg-type]
            )


# ======================================================================
# Tests: Annuity_Base.get_annuity_as_string — base fallback
# ======================================================================


@pytest.mark.unit()
class Test_Annuity_Base_String_Representation:
    """Test the base-class fallback ``get_annuity_as_string`` method.

    All production subclasses override this method, so coverage requires a
    stub that does not override it.
    """

    @pytest.mark.unit()
    def test_base_get_annuity_as_string_contains_payout_rate(self) -> None:
        """Base get_annuity_as_string should include the formatted payout rate."""
        stub = _ConcreteAnnuityStub(
            client_age=60,
            annuity_payout_rate=0.04,
            annuity_type=Annuity_Type.ANNUITY_DIA,
        )
        result = stub.get_annuity_as_string()
        assert isinstance(result, str)
        assert "4.00%" in result
        assert "60" in result
