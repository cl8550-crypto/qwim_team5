"""
Registered Index-Linked Annuity (RILA) class.

===============================

A Registered Index-Linked Annuity (also known as a *buffered annuity*
or *structured annuity*) is an SEC-registered product that sits
between a Fixed Indexed Annuity (FIA) and a Variable Annuity (VA) on
the risk spectrum.  The contract holder assumes limited downside
market risk in exchange for higher upside potential than an FIA.

Key characteristics of RILAs:

- **Index-linked crediting**: returns are tied to a market index
  (e.g. S&P 500, Russell 2000, MSCI EAFE) over a defined term.
- **Buffer protection**: the insurer absorbs the first *B* % of index
  losses; the contract holder bears losses beyond the buffer.
- **Floor protection**: (alternative to buffer) the maximum loss is
  capped at the floor level; the contract holder bears losses up to
  the floor with the insurer absorbing the rest.
- **Cap rate**: the maximum return credited per term.
- **Performance trigger**: (alternative crediting strategy) if the
  index return is non-negative, a fixed rate is credited regardless
  of the magnitude of the gain.
- **Term / segment duration**: crediting is evaluated at the end of
  each term (typically 1, 2, 3, or 6 years).  Investors may hold
  multiple overlapping segments.
- **Interim value**: a market-value-adjusted account value calculated
  during a term (before maturity) that reflects current index
  performance and a discount factor.
- **Surrender charges**: declining schedule of early withdrawal
  penalties similar to FIA/VA products.
- **Income analysis**: annual payout, monthly payout, and nominal/real
    withdrawal-rate projections can be derived once income begins.
- **Outcome analysis**: deterministic worst-case and best-case account-value
    projections are available for scenario framing.
- **No guaranteed minimum accumulation**: unlike an FIA, the account
  value can decline (up to the buffer/floor limit).  RILA contracts
  are SEC-registered securities.

Author
------
QWIM Team

Version
-------
0.5.1 (2026-05-30)
"""

from __future__ import annotations

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from .annuity_base import Annuity_Base, Annuity_Type
from ._annuity_RILA_enums import Crediting_Strategy, Protection_Type
from ._annuity_RILA_core_calcs_mixin import _RILA_Core_Calcs_Mixin
from ._annuity_RILA_payout_calcs_mixin import _RILA_Payout_Calcs_Mixin


_logger = get_logger(name = __name__)


# Re-export enumerations so existing imports from this module remain valid.
__all__ = [
    "Annuity_RILA",
    "Crediting_Strategy",
    "Protection_Type",
]


# ======================================================================
# Annuity_RILA class
# ======================================================================


class Annuity_RILA(_RILA_Core_Calcs_Mixin, _RILA_Payout_Calcs_Mixin, Annuity_Base):
    r"""Registered Index-Linked Annuity (RILA).

    A RILA provides index-linked returns over defined terms with limited
    downside exposure controlled by a **buffer** or **floor** mechanism.
    The public interface also includes surrender-value, death-benefit,
    income-payout, withdrawal-rate, and outcome-analysis helpers supplied
    by the payout mixin.

    **Credited return per term (cap strategy)**:

    With buffer protection:

    $$
    r_{\text{credited}} = \begin{cases}
        \min(R_{\text{index}},\; c)
            & \text{if } R_{\text{index}} \ge 0 \\[4pt]
        0
            & \text{if } -b \le R_{\text{index}} < 0 \\[4pt]
        R_{\text{index}} + b
            & \text{if } R_{\text{index}} < -b
    \end{cases}
    $$

    With floor protection:

    $$
    r_{\text{credited}} = \begin{cases}
        \min(R_{\text{index}},\; c)
            & \text{if } R_{\text{index}} \ge 0 \\[4pt]
        \max(R_{\text{index}},\; f)
            & \text{if } R_{\text{index}} < 0
    \end{cases}
    $$

    **Performance trigger strategy**:

    $$
    r_{\text{credited}} = \begin{cases}
        r_{\text{trigger}}
            & \text{if } R_{\text{index}} \ge 0 \\[4pt]
        \text{downside}(R_{\text{index}})
            & \text{if } R_{\text{index}} < 0
    \end{cases}
    $$

    **Interim value** (market-value-adjusted mid-term):

    $$
    IV = P \times (1 + r_{\text{credited, partial}})
        \times \frac{1}{(1 + d)^{T - t}}
    $$

    Where $d$ = discount rate, $T$ = term length, and $t$ = elapsed years.

    Attributes
    ----------
    m_client_age : int
        The current age of the client (inherited).
    m_annuity_payout_rate : float
        The payout rate of the annuity (inherited).
    m_annuity_type : Annuity_Type
        Set to ``ANNUITY_RILA`` (inherited).
    m_age_income_start : int
        The age at which income payments begin.
    m_term_years : int
        Duration of each crediting term / segment (years).
    m_protection_type : Protection_Type
        Type of downside protection (BUFFER or FLOOR).
    m_buffer_rate : float
        Buffer percentage absorbed by the insurer (e.g. 0.10 for 10 %).
        Only meaningful when ``m_protection_type`` is ``BUFFER``.
    m_floor_rate : float
        Floor / maximum loss percentage for the contract holder (e.g.
        -0.10 for -10 %).  Only meaningful when ``m_protection_type``
        is ``FLOOR``.
    m_crediting_strategy : Crediting_Strategy
        Crediting strategy applied to the index return.
    m_cap_rate : float
        Maximum return credited per term (used with CAP or
        PARTICIPATION_RATE strategies).
    m_participation_rate : float
        Fraction of the index return credited (used with
        PARTICIPATION_RATE strategy).
    m_performance_trigger_rate : float
        Fixed rate credited when the index return >= 0 (used with
        PERFORMANCE_TRIGGER strategy).
    m_rate_rider_charge : float
        Annual rider charge for optional benefits (as a decimal).
    m_rate_surrender_charge_initial : float
        Initial surrender charge rate (year 0).
    m_surrender_charge_schedule_years : int
        Years over which the surrender charge declines to zero.
    m_pct_free_withdrawal : float
        Annual free-withdrawal percentage.
    m_rate_interim_discount : float
        Discount rate used in interim-value calculation.
    m_has_GMDB : bool
        Whether the contract includes a Guaranteed Minimum Death Benefit.
    m_has_return_of_premium_death_benefit : bool
        Whether the death benefit guarantees at least the premium paid.
    m_payment_frequency : int
        Number of payments per year.
    m_financial_index : str
        Name of the financial index column in ``obj_scenarios``.
    """

    def __init__(
        self,
        client_age: int,
        annuity_payout_rate: float,
        age_income_start: int,
        term_years: int = 6,
        protection_type: Protection_Type = Protection_Type.BUFFER,
        buffer_rate: float = 0.10,
        floor_rate: float = -0.10,
        crediting_strategy: Crediting_Strategy = Crediting_Strategy.CAP,
        cap_rate: float = 0.15,
        participation_rate: float = 1.0,
        performance_trigger_rate: float = 0.0,
        rate_rider_charge: float = 0.0,
        rate_surrender_charge_initial: float = 0.06,
        surrender_charge_schedule_years: int = 6,
        pct_free_withdrawal: float = 0.10,
        rate_interim_discount: float = 0.02,
        has_GMDB: bool = False,
        has_return_of_premium_death_benefit: bool = True,
        payment_frequency: int = 12,
        financial_index: str = "S&P 500",
        annuity_income_starting_age: int | None = None,
    ) -> None:
        """Initialize a Registered Index-Linked Annuity object.

        Parameters
        ----------
        client_age : int
            The current age of the client.
        annuity_payout_rate : float
            The annual payout rate of the annuity (as a decimal).
        age_income_start : int
            The age at which income payments begin.
        term_years : int, optional
            Duration of each crediting term in years (default 6).
        protection_type : Protection_Type, optional
            Downside protection mechanism (default ``BUFFER``).
        buffer_rate : float, optional
            Buffer percentage absorbed by insurer (default 0.10 = 10 %).
        floor_rate : float, optional
            Floor / maximum loss percentage; should be negative or zero
            (default -0.10 = -10 %).
        crediting_strategy : Crediting_Strategy, optional
            Index-return crediting strategy (default ``CAP``).
        cap_rate : float, optional
            Maximum return credited per term (default 0.15 = 15 %).
        participation_rate : float, optional
            Fraction of index return credited (default 1.0 = 100 %).
        performance_trigger_rate : float, optional
            Fixed rate credited when index return >= 0 (default 0.0).
        rate_rider_charge : float, optional
            Annual rider charge for optional benefits (default 0.0).
        rate_surrender_charge_initial : float, optional
            Initial surrender charge rate (default 0.06 = 6 %).
        surrender_charge_schedule_years : int, optional
            Years for surrender charge to decline to zero (default 6).
        pct_free_withdrawal : float, optional
            Annual free-withdrawal percentage (default 0.10 = 10 %).
        rate_interim_discount : float, optional
            Discount rate for interim-value calculation (default 0.02).
        has_GMDB : bool, optional
            Include Guaranteed Minimum Death Benefit (default ``False``).
        has_return_of_premium_death_benefit : bool, optional
            Death benefit guarantees at least the premium (default ``True``).
        payment_frequency : int, optional
            Number of payments per year (default 12 = monthly).
        financial_index : str, optional
            Name of the column in ``obj_scenarios`` containing index returns.
            Defaults to ``"S&P 500"``.
        annuity_income_starting_age : int | None, optional
            The age when the client will start receiving income from this
            annuity.  Must be ``>= client_age`` when provided.  Defaults
            to ``client_age`` when ``None``.

        Raises
        ------
        Exception_Validation_Input
            If any input fails validation.
        """
        super().__init__(
            client_age,
            annuity_payout_rate,
            Annuity_Type.ANNUITY_RILA,
            annuity_income_starting_age=annuity_income_starting_age,
        )

        # --- Input validation ---
        if not isinstance(age_income_start, int) or age_income_start <= client_age:
            raise Exception_Validation_Input(
                "age_income_start must be an integer greater than client_age",
                field_name="age_income_start",
                expected_type=int,
                actual_value=age_income_start,
            )

        if isinstance(term_years, bool) or not isinstance(term_years, int) or term_years <= 0:
            raise Exception_Validation_Input(
                "term_years must be a positive integer",
                field_name="term_years",
                expected_type=int,
                actual_value=term_years,
            )

        if not isinstance(protection_type, Protection_Type):
            raise Exception_Validation_Input(
                "protection_type must be a valid Protection_Type enum",
                field_name="protection_type",
                expected_type=Protection_Type,
                actual_value=protection_type,
            )

        if (
            isinstance(buffer_rate, bool)
            or not isinstance(buffer_rate, (int, float))
            or buffer_rate < 0
            or buffer_rate > 1
        ):
            raise Exception_Validation_Input(
                "buffer_rate must be between 0 and 1",
                field_name="buffer_rate",
                expected_type=float,
                actual_value=buffer_rate,
            )

        if isinstance(floor_rate, bool) or not isinstance(floor_rate, (int, float)) or floor_rate > 0:
            raise Exception_Validation_Input(
                "floor_rate must be a non-positive number (e.g. -0.10)",
                field_name="floor_rate",
                expected_type=float,
                actual_value=floor_rate,
            )

        if not isinstance(crediting_strategy, Crediting_Strategy):
            raise Exception_Validation_Input(
                "crediting_strategy must be a valid Crediting_Strategy enum",
                field_name="crediting_strategy",
                expected_type=Crediting_Strategy,
                actual_value=crediting_strategy,
            )

        if isinstance(cap_rate, bool) or not isinstance(cap_rate, (int, float)) or cap_rate < 0:
            raise Exception_Validation_Input(
                "cap_rate must be a non-negative number",
                field_name="cap_rate",
                expected_type=float,
                actual_value=cap_rate,
            )

        if (
            isinstance(participation_rate, bool)
            or not isinstance(participation_rate, (int, float))
            or participation_rate < 0
            or participation_rate > 3.0
        ):
            raise Exception_Validation_Input(
                "participation_rate must be between 0 and 3.0",
                field_name="participation_rate",
                expected_type=float,
                actual_value=participation_rate,
            )

        if (
            isinstance(performance_trigger_rate, bool)
            or not isinstance(performance_trigger_rate, (int, float))
            or performance_trigger_rate < 0
        ):
            raise Exception_Validation_Input(
                "performance_trigger_rate must be a non-negative number",
                field_name="performance_trigger_rate",
                expected_type=float,
                actual_value=performance_trigger_rate,
            )

        if isinstance(rate_rider_charge, bool) or not isinstance(rate_rider_charge, (int, float)) or rate_rider_charge < 0:
            raise Exception_Validation_Input(
                "rate_rider_charge must be a non-negative number",
                field_name="rate_rider_charge",
                expected_type=float,
                actual_value=rate_rider_charge,
            )

        if (
            isinstance(rate_surrender_charge_initial, bool)
            or not isinstance(rate_surrender_charge_initial, (int, float))
            or rate_surrender_charge_initial < 0
        ):
            raise Exception_Validation_Input(
                "rate_surrender_charge_initial must be non-negative",
                field_name="rate_surrender_charge_initial",
                expected_type=float,
                actual_value=rate_surrender_charge_initial,
            )

        if (
            isinstance(surrender_charge_schedule_years, bool)
            or not isinstance(surrender_charge_schedule_years, int)
            or surrender_charge_schedule_years < 0
        ):
            raise Exception_Validation_Input(
                "surrender_charge_schedule_years must be a non-negative integer",
                field_name="surrender_charge_schedule_years",
                expected_type=int,
                actual_value=surrender_charge_schedule_years,
            )

        if isinstance(pct_free_withdrawal, bool):
            raise Exception_Validation_Input(
                "pct_free_withdrawal must be numeric",
                field_name="pct_free_withdrawal",
                expected_type=float,
                actual_value=pct_free_withdrawal,
            )

        if isinstance(rate_interim_discount, bool) or not isinstance(rate_interim_discount, (int, float)) or rate_interim_discount < 0:
            raise Exception_Validation_Input(
                "rate_interim_discount must be a non-negative number",
                field_name="rate_interim_discount",
                expected_type=float,
                actual_value=rate_interim_discount,
            )

        if isinstance(payment_frequency, bool) or not isinstance(payment_frequency, int) or payment_frequency <= 0:
            raise Exception_Validation_Input(
                "payment_frequency must be a positive integer",
                field_name="payment_frequency",
                expected_type=int,
                actual_value=payment_frequency,
            )

        if not isinstance(financial_index, str) or not financial_index.strip():
            raise Exception_Validation_Input(
                "financial_index must be a non-empty string",
                field_name="financial_index",
                expected_type=str,
                actual_value=financial_index,
            )

        # --- Set member variables ---
        self.m_age_income_start: int = age_income_start
        self.m_term_years: int = term_years
        self.m_protection_type: Protection_Type = protection_type
        self.m_buffer_rate: float = float(buffer_rate)
        self.m_floor_rate: float = float(floor_rate)
        self.m_crediting_strategy: Crediting_Strategy = crediting_strategy
        self.m_cap_rate: float = float(cap_rate)
        self.m_participation_rate: float = float(participation_rate)
        self.m_performance_trigger_rate: float = float(performance_trigger_rate)
        self.m_rate_rider_charge: float = float(rate_rider_charge)
        self.m_rate_surrender_charge_initial: float = float(rate_surrender_charge_initial)
        self.m_surrender_charge_schedule_years: int = surrender_charge_schedule_years
        self.m_pct_free_withdrawal: float = float(pct_free_withdrawal)
        self.m_rate_interim_discount: float = float(rate_interim_discount)
        self.m_has_GMDB: bool = has_GMDB
        self.m_has_return_of_premium_death_benefit: bool = has_return_of_premium_death_benefit
        self.m_payment_frequency: int = payment_frequency
        self.m_financial_index: str = financial_index

        _logger.info(
            f"Created RILA with payout rate {annuity_payout_rate:.2%}, "
            f"income at age {age_income_start}, "
            f"term: {term_years}yr, "
            f"protection: {protection_type.value} "
            f"(buffer={buffer_rate:.0%}, floor={floor_rate:.0%}), "
            f"crediting: {crediting_strategy.value} "
            f"(cap={cap_rate:.0%}, participation={participation_rate:.0%}, "
            f"trigger={performance_trigger_rate:.0%}), "
            f"surrender: {rate_surrender_charge_initial:.1%}/"
            f"{surrender_charge_schedule_years}yr, "
            f"index: {financial_index!r}",
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def income_start_age(self) -> int:
        """Int : The age at which income payments begin."""
        return self.m_age_income_start

    @property
    def term_years(self) -> int:
        """Int : Duration of each crediting term in years."""
        return self.m_term_years

    @property
    def protection_type(self) -> Protection_Type:
        """Protection_Type : The downside protection mechanism."""
        return self.m_protection_type

    @property
    def buffer_rate(self) -> float:
        """Float : Buffer percentage absorbed by the insurer."""
        return self.m_buffer_rate

    @property
    def floor_rate(self) -> float:
        """Float : Floor / maximum loss percentage (negative or zero)."""
        return self.m_floor_rate

    @property
    def crediting_strategy(self) -> Crediting_Strategy:
        """Crediting_Strategy : The index-return crediting strategy."""
        return self.m_crediting_strategy

    @property
    def cap_rate(self) -> float:
        """Float : Maximum return credited per term."""
        return self.m_cap_rate

    @property
    def participation_rate(self) -> float:
        """Float : Fraction of the index return credited."""
        return self.m_participation_rate

    @property
    def performance_trigger_rate(self) -> float:
        """Float : Fixed rate credited when the index return >= 0."""
        return self.m_performance_trigger_rate

    @property
    def rate_rider_charge(self) -> float:
        """Float : Annual rider charge for optional benefits."""
        return self.m_rate_rider_charge

    @property
    def pct_free_withdrawal(self) -> float:
        """Float : Annual free-withdrawal percentage."""
        return self.m_pct_free_withdrawal

    @property
    def rate_interim_discount(self) -> float:
        """Float : Discount rate used in interim-value calculation."""
        return self.m_rate_interim_discount

    @property
    def has_GMDB(self) -> bool:
        """Bool : Whether the contract includes a GMDB."""
        return self.m_has_GMDB

    @property
    def has_return_of_premium_death_benefit(self) -> bool:
        """Bool : Whether the death benefit guarantees at least the premium."""
        return self.m_has_return_of_premium_death_benefit

    @property
    def payment_frequency(self) -> int:
        """Int : Number of payments per year."""
        return self.m_payment_frequency

    @property
    def financial_index(self) -> str:
        """Str : Name of the financial index column used in scenario data."""
        return self.m_financial_index

    @property
    def deferral_years(self) -> int:
        """Int : Number of years until income payments begin."""
        return self.m_age_income_start - self.m_client_age


    def get_annuity_as_string(self) -> str:
        """Return a human-readable string representation of the RILA.

        Returns
        -------
        str
            String representation of the Registered Index-Linked Annuity.
        """
        protection_detail = (
            f"Buffer {self.m_buffer_rate:.0%}"
            if self.m_protection_type == Protection_Type.BUFFER
            else f"Floor {self.m_floor_rate:.0%}"
        )

        crediting_detail = f"{self.m_crediting_strategy.value}"
        if self.m_crediting_strategy == Crediting_Strategy.CAP:
            crediting_detail += f" {self.m_cap_rate:.0%}"
        elif self.m_crediting_strategy == Crediting_Strategy.PERFORMANCE_TRIGGER:
            crediting_detail += f" {self.m_performance_trigger_rate:.0%}"
        elif self.m_crediting_strategy == Crediting_Strategy.PARTICIPATION_RATE:
            crediting_detail += f" {self.m_participation_rate:.0%} (cap {self.m_cap_rate:.0%})"

        riders = []
        if self.m_has_GMDB:
            riders.append("GMDB")
        if self.m_has_return_of_premium_death_benefit:
            riders.append("ROP-DB")
        rider_text = ", ".join(riders) if riders else "None"

        return (
            f"RILA: Age {self.m_client_age}, "
            f"Income at {self.m_age_income_start}, "
            f"Term {self.m_term_years}yr, "
            f"Protection: {protection_detail}, "
            f"Crediting: {crediting_detail}, "
            f"Riders: {rider_text}, "
            f"Index: {self.m_financial_index}, "
            f"Payout {self.m_annuity_payout_rate:.2%}, "
            f"Surrender {self.m_rate_surrender_charge_initial:.1%}/"
            f"{self.m_surrender_charge_schedule_years}yr, "
            f"Frequency {self.m_payment_frequency}/year"
        )
