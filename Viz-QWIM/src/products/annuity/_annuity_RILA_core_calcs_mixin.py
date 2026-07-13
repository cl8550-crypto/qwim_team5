"""Core index-linked calculation mixin for Annuity_RILA.

This private mixin provides the fundamental per-term crediting and
account-value methods for ``Annuity_RILA``.  It is not intended to be
used independently — it relies on instance attributes set by
``Annuity_RILA.__init__``.

Methods provided
----------------
- ``calc_downside_return`` — apply buffer or floor downside protection.
- ``calc_credited_rate`` — apply the selected crediting strategy.
- ``calc_annualised_credited_rate`` — annualise a term credited rate.
- ``calc_account_value_at_term_end`` — account value after one term.
- ``calc_interim_value`` — market-value-adjusted mid-term value.
- ``calc_account_values_multi_term`` — account values across many terms.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-28)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._annuity_RILA_enums import Crediting_Strategy, Protection_Type


if TYPE_CHECKING:
    class _RILA_Core_Calc_State(Protocol):
        m_protection_type: Protection_Type
        m_buffer_rate: float
        m_floor_rate: float
        m_crediting_strategy: Crediting_Strategy
        m_cap_rate: float
        m_participation_rate: float
        m_performance_trigger_rate: float
        m_term_years: int
        m_rate_interim_discount: float
        m_rate_rider_charge: float

        def calc_downside_return(self, *, index_return: float) -> float: ...
        def calc_credited_rate(self, *, index_return: float) -> float: ...


_logger = get_logger(name = __name__)


class _RILA_Core_Calcs_Mixin:
    """Mixin providing core per-term crediting and account-value calculations.

    Relies on the following instance attributes being set by
    ``Annuity_RILA.__init__``:

    - ``m_protection_type`` : Protection_Type
    - ``m_buffer_rate``     : float
    - ``m_floor_rate``      : float
    - ``m_crediting_strategy`` : Crediting_Strategy
    - ``m_cap_rate``        : float
    - ``m_participation_rate`` : float
    - ``m_performance_trigger_rate`` : float
    - ``m_rate_rider_charge`` : float
    - ``m_rate_interim_discount`` : float
    - ``m_term_years``      : int
    """

    # ------------------------------------------------------------------
    # Downside protection calculations
    # ------------------------------------------------------------------

    def calc_downside_return(
        self: _RILA_Core_Calc_State, *, index_return: float) -> float:
        r"""Calculate the return after applying downside protection.

        **Buffer protection** (insurer absorbs first *b* % of loss):

        $$
        r_{\text{down}} = \begin{cases}
            0 & \text{if } -b \le R < 0 \\
            R + b & \text{if } R < -b
        \end{cases}
        $$

        **Floor protection** (maximum loss = *f*):

        $$
        r_{\text{down}} = \max(R,\; f)
        $$

        Parameters
        ----------
        index_return : float
            The raw index return for the term (as a decimal).

        Returns
        -------
        float
            The return after downside protection is applied.
            Always ``<= 0`` (or ``0`` if the index did not decline).

        Raises
        ------
        Exception_Validation_Input
            If ``index_return`` is not a number.
        """
        if not isinstance(index_return, (int, float)):
            raise Exception_Validation_Input(
                "index_return must be a number",
                field_name="index_return",
                expected_type=float,
                actual_value=index_return,
            )

        if index_return >= 0:
            return 0.0

        if self.m_protection_type == Protection_Type.BUFFER:
            # Insurer absorbs the first buffer_rate of losses
            if abs(index_return) <= self.m_buffer_rate:
                return 0.0
            return index_return + self.m_buffer_rate

        # Floor protection: loss capped at floor_rate
        return max(index_return, self.m_floor_rate)

    # ------------------------------------------------------------------
    # Credited-rate calculations
    # ------------------------------------------------------------------

    def calc_credited_rate(
        self: _RILA_Core_Calc_State, *, index_return: float) -> float:
        r"""Calculate the credited rate for a single term.

        Applies the selected crediting strategy and downside protection.

        **Cap strategy**:

        $$
        r_{\text{credited}} = \begin{cases}
            \min(R_{\text{index}},\; c)
                & \text{if } R_{\text{index}} \ge 0 \\[4pt]
            \text{downside}(R_{\text{index}})
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

        **Participation rate strategy**:

        $$
        r_{\text{credited}} = \begin{cases}
            \min(R_{\text{index}} \times p,\; c)
                & \text{if } R_{\text{index}} \ge 0 \\[4pt]
            \text{downside}(R_{\text{index}})
                & \text{if } R_{\text{index}} < 0
        \end{cases}
        $$

        Parameters
        ----------
        index_return : float
            The raw index return for the term (as a decimal).

        Returns
        -------
        float
            The credited rate after applying the crediting strategy
            and downside protection.

        Raises
        ------
        Exception_Validation_Input
            If ``index_return`` is not a number.
        Exception_Calculation
            If the crediting strategy is unrecognised.
        """
        if not isinstance(index_return, (int, float)):
            raise Exception_Validation_Input(
                "index_return must be a number",
                field_name="index_return",
                expected_type=float,
                actual_value=index_return,
            )

        # --- Negative index return: apply downside protection ---
        if index_return < 0:
            return self.calc_downside_return(index_return = index_return)

        # --- Non-negative index return: apply crediting strategy ---
        if self.m_crediting_strategy == Crediting_Strategy.CAP:
            return min(index_return, self.m_cap_rate)

        if self.m_crediting_strategy == Crediting_Strategy.PERFORMANCE_TRIGGER:
            return self.m_performance_trigger_rate

        if self.m_crediting_strategy == Crediting_Strategy.PARTICIPATION_RATE:
            participated = index_return * self.m_participation_rate
            return min(participated, self.m_cap_rate)

        raise Exception_Calculation(
            f"Unrecognised crediting strategy: {self.m_crediting_strategy}",
        )

    def calc_annualised_credited_rate(
        self: _RILA_Core_Calc_State, *, index_return: float, term_years: int | None = None) -> float:
        r"""Annualise the term credited rate.

        $$
        r_{\text{annual}} = (1 + r_{\text{term}})^{1/T} - 1
        $$

        Parameters
        ----------
        index_return : float
            The raw index return for the term.
        term_years : int | None, optional
            Term length to annualise over (default: :attr:`term_years`).

        Returns
        -------
        float
            The annualised credited rate.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if term_years is None:
            term_years = self.m_term_years

        if not isinstance(term_years, int) or term_years <= 0:
            raise Exception_Validation_Input(
                "term_years must be a positive integer",
                field_name="term_years",
                expected_type=int,
                actual_value=term_years,
            )

        credited = self.calc_credited_rate(index_return = index_return)
        growth_factor = 1.0 + credited
        # Guard: if total return makes growth non-positive, return total loss
        if growth_factor <= 0.0:
            return -1.0
        return growth_factor ** (1.0 / term_years) - 1.0

    # ------------------------------------------------------------------
    # Account value and interim value
    # ------------------------------------------------------------------

    def calc_account_value_at_term_end(
        self: _RILA_Core_Calc_State, *, amount_principal: float, index_return: float) -> float:
        r"""Calculate the account value at the end of one crediting term.

        $$
        V = P \times (1 + r_{\text{credited}})
        $$

        Parameters
        ----------
        amount_principal : float
            The principal invested at the start of the term.
        index_return : float
            The cumulative index return over the term.

        Returns
        -------
        float
            The account value at term end.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        credited = self.calc_credited_rate(index_return = index_return)
        return amount_principal * (1 + credited)

    def calc_interim_value(
        self: _RILA_Core_Calc_State, *, amount_principal: float, current_index_return: float, years_elapsed: int) -> float:
        r"""Calculate the market-value-adjusted interim value mid-term.

        The interim value reflects the current index performance and
        applies a discount for the remaining term:

        $$
        IV = P \times (1 + r_{\text{credited, partial}})
            \times \frac{1}{(1 + d)^{T - t}}
        $$

        Where $d$ = ``rate_interim_discount``, $T$ = total term, and
        $t$ = years elapsed.

        Parameters
        ----------
        amount_principal : float
            The principal invested at the start of the term.
        current_index_return : float
            The index return so far within the term.
        years_elapsed : int
            Number of years elapsed within the current term.

        Returns
        -------
        float
            The interim account value.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        if not isinstance(years_elapsed, int) or years_elapsed < 0:
            raise Exception_Validation_Input(
                "years_elapsed must be a non-negative integer",
                field_name="years_elapsed",
                expected_type=int,
                actual_value=years_elapsed,
            )

        if years_elapsed > self.m_term_years:
            raise Exception_Validation_Input(
                "years_elapsed cannot exceed term_years",
                field_name="years_elapsed",
                expected_type=int,
                actual_value=years_elapsed,
            )

        # Apply crediting rules to the partial-term index return
        credited_partial = self.calc_credited_rate(index_return = current_index_return)

        remaining_years = self.m_term_years - years_elapsed
        discount_factor = 1.0 / ((1 + self.m_rate_interim_discount) ** remaining_years)

        return amount_principal * (1 + credited_partial) * discount_factor

    def calc_account_values_multi_term(
        self: _RILA_Core_Calc_State, *, amount_principal: float, term_index_returns: list[float]) -> list[float]:
        r"""Simulate account value across multiple consecutive terms.

        For each term *i* the account value at the end is:

        $$
        V_i = V_{i-1} \times (1 + r_{\text{credited}, i})
        $$

        Annual rider charges are deducted from the account value once
        per term (compounded over the term length):

        $$
        V_i = V_i \times (1 - c_{\text{rider}})^{T}
        $$

        Parameters
        ----------
        amount_principal : float
            The initial premium invested.
        term_index_returns : list[float]
            A list of cumulative index returns, one per term.

        Returns
        -------
        list[float]
            Account values at the end of each term, starting with the
            initial value at index 0.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        if not isinstance(term_index_returns, list):
            raise Exception_Validation_Input(
                "term_index_returns must be a list of numbers",
                field_name="term_index_returns",
                expected_type=list,
                actual_value=term_index_returns,
            )

        values: list[float] = [float(amount_principal)]
        current_value = float(amount_principal)

        charge_factor = (1 - self.m_rate_rider_charge) ** self.m_term_years

        for term_return in term_index_returns:
            credited = self.calc_credited_rate(index_return = term_return)
            current_value *= 1 + credited
            # Deduct rider charges accumulated over the term
            current_value *= charge_factor
            current_value = max(current_value, 0.0)
            values.append(current_value)

        return values
