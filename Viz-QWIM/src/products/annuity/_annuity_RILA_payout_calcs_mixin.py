"""Payout and cashflow calculation mixin for Annuity_RILA.

This private mixin provides surrender, death-benefit, payout, and
scenario-analysis methods for ``Annuity_RILA``.  It is not intended
to be used independently — it relies on instance attributes set by
``Annuity_RILA.__init__`` and on methods provided by
``_RILA_Core_Calcs_Mixin``.

Methods provided
----------------
- ``calc_surrender_charge_rate`` — linearly declining surrender charge.
- ``calc_surrender_value`` — net surrender value after charges.
- ``calc_death_benefit`` — death benefit with optional ROP or GMDB.
- ``calc_annuity_payout`` — annual payout from benefit base.
- ``calc_withdrawal_rates`` — nominal and real withdrawal rates.
- ``calc_monthly_payout`` — monthly equivalent of the annual payout.
- ``calc_worst_case_account_value`` — account value with maximum losses.
- ``calc_best_case_account_value`` — account value with maximum gains.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-30)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._annuity_RILA_enums import Crediting_Strategy, Protection_Type
from .annuity_base import Withdrawal_Rates


if TYPE_CHECKING:
    import polars as pl

    class _RILA_Surrender_State(Protocol):
        """Structural state required by surrender calculations."""

        m_surrender_charge_schedule_years: int
        m_rate_surrender_charge_initial: float
        m_pct_free_withdrawal: float

        def calc_surrender_charge_rate(self, *, year: int) -> float: ...

    class _RILA_Death_Benefit_State(Protocol):
        """Structural state required by death-benefit calculations."""

        m_has_return_of_premium_death_benefit: bool
        m_has_GMDB: bool

    class _RILA_Payout_State(Protocol):
        """Structural state required by payout calculations."""

        m_client_age: int
        m_age_income_start: int
        m_financial_index: str
        m_annuity_payout_rate: float

        def calc_account_values_multi_term(
            self, *, amount_principal: float, term_index_returns: list[float]) -> list[float]: ...

    class _RILA_Withdrawal_State(Protocol):
        """Structural state required by withdrawal and monthly payout calculations."""

        m_annuity_payout_rate: float

        def calc_annuity_payout(
            self, *, amount_principal: float, obj_scenarios: pl.DataFrame | None = None, obj_inflation: pl.DataFrame | None = None) -> float: ...

    class _RILA_Outcome_State(Protocol):
        """Structural state required by worst-case and best-case outcome analysis."""

        m_protection_type: Protection_Type
        m_floor_rate: float
        m_rate_rider_charge: float
        m_term_years: int
        m_crediting_strategy: Crediting_Strategy
        m_performance_trigger_rate: float
        m_participation_rate: float
        m_cap_rate: float

        def calc_credited_rate(self, *, index_return: float) -> float: ...


_logger = get_logger(name = __name__)


class _RILA_Payout_Calcs_Mixin:
    """Mixin providing payout, surrender, death-benefit, and scenario calculations.

    Relies on the following instance attributes being set by
    ``Annuity_RILA.__init__``:

    - ``m_client_age``                    : int
    - ``m_age_income_start``              : int
    - ``m_annuity_payout_rate``           : float
    - ``m_pct_free_withdrawal``           : float
    - ``m_rate_surrender_charge_initial`` : float
    - ``m_surrender_charge_schedule_years`` : int
    - ``m_has_return_of_premium_death_benefit`` : bool
    - ``m_has_GMDB``                      : bool
    - ``m_financial_index``               : str
    - ``m_cap_rate``                      : float
    - ``m_participation_rate``            : float
    - ``m_performance_trigger_rate``      : float
    - ``m_crediting_strategy``            : Crediting_Strategy
    - ``m_protection_type``               : Protection_Type
    - ``m_floor_rate``                    : float
    - ``m_rate_rider_charge``             : float
    - ``m_term_years``                    : int

    Also relies on ``calc_account_values_multi_term`` and
    ``calc_credited_rate`` supplied by ``_RILA_Core_Calcs_Mixin``.
    """

    # ------------------------------------------------------------------
    # Surrender calculations
    # ------------------------------------------------------------------

    def calc_surrender_charge_rate(
        self: _RILA_Surrender_State, *, year: int) -> float:
        r"""Calculate the surrender charge rate for a given contract year.

        Uses a linearly declining schedule:

        $$
        SC(t) = \max\!\Bigl(0,\; SC_0 \times \bigl(1 - \tfrac{t}{T}\bigr)\Bigr)
        $$

        Where $SC_0$ = initial surrender charge, $T$ = schedule duration.

        Parameters
        ----------
        year : int
            The contract year (0-indexed; year 0 = purchase year).

        Returns
        -------
        float
            The surrender charge rate as a decimal.  Returns 0.0 if the
            surrender period has expired.
        """
        if isinstance(year, bool) or not isinstance(year, int) or year < 0:
            return 0.0

        if self.m_surrender_charge_schedule_years <= 0:
            return 0.0

        if year >= self.m_surrender_charge_schedule_years:
            return 0.0

        return self.m_rate_surrender_charge_initial * (
            1 - year / self.m_surrender_charge_schedule_years
        )

    def calc_surrender_value(
        self: _RILA_Surrender_State, *, account_value: float, year: int) -> float:
        """Calculate the surrender (cash-out) value.

        The free-withdrawal portion is exempt from surrender charges.

        Parameters
        ----------
        account_value : float
            The current account value.
        year : int
            The contract year (0-indexed).

        Returns
        -------
        float
            The net surrender value after charges.

        Raises
        ------
        Exception_Validation_Input
            If ``account_value`` is not a positive number.
        """
        if isinstance(account_value, bool) or not isinstance(account_value, (int, float)) or account_value <= 0:
            raise Exception_Validation_Input(
                "account_value must be a positive number",
                field_name="account_value",
                expected_type=float,
                actual_value=account_value,
            )

        charge_rate = self.calc_surrender_charge_rate(year = year)
        free_amount = account_value * self.m_pct_free_withdrawal
        excess_amount = max(account_value - free_amount, 0.0)
        surrender_charge = excess_amount * charge_rate
        return account_value - surrender_charge

    # ------------------------------------------------------------------
    # Death benefit
    # ------------------------------------------------------------------

    def calc_death_benefit(
        self: _RILA_Death_Benefit_State, *, amount_principal: float, account_value: float) -> float:
        r"""Calculate the death benefit.

        If the return-of-premium death benefit is elected:

        $$
        DB = \max(V_{\text{account}},\; A)
        $$

        Otherwise:

        $$
        DB = V_{\text{account}}
        $$

        Parameters
        ----------
        amount_principal : float
            The initial premium invested.
        account_value : float
            The current account value.

        Returns
        -------
        float
            The death benefit amount.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if isinstance(amount_principal, bool) or not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        if isinstance(account_value, bool) or not isinstance(account_value, (int, float)) or account_value < 0:
            raise Exception_Validation_Input(
                "account_value must be a non-negative number",
                field_name="account_value",
                expected_type=float,
                actual_value=account_value,
            )

        if self.m_has_return_of_premium_death_benefit:
            return max(account_value, amount_principal)

        if self.m_has_GMDB:
            return max(account_value, amount_principal)

        return account_value

    # ------------------------------------------------------------------
    # Payout calculations
    # ------------------------------------------------------------------

    def calc_annuity_payout(
        self: _RILA_Payout_State, *, amount_principal: float, obj_scenarios: pl.DataFrame | None = None, obj_inflation: pl.DataFrame | None = None) -> float:
        """Calculate the RILA annual payout.

        The payout depends on:

        1. Whether the client has reached the income start age.
        2. The account value after crediting across terms (via scenario
           data if available, otherwise the principal is used directly).
        3. The payout rate applied to the account value or benefit base.

        Parameters
        ----------
        amount_principal : float
            The principal amount invested.
        obj_scenarios : pl.DataFrame | None, optional
            Polars DataFrame containing scenario market data.  The first column
            must be ``Date``; the column named ``self.m_financial_index`` must
            contain index returns per crediting term.
        obj_inflation : pl.DataFrame | None, optional
            Polars DataFrame with pre-calculated inflation factors (unused
            for RILA; kept for interface compatibility).

        Returns
        -------
        float
            The calculated annual payout.  Returns ``0.0`` while in
            deferral.

        Raises
        ------
        Exception_Validation_Input
            If ``amount_principal`` is not a positive number or if
            ``obj_scenarios`` is missing required columns.
        """
        import polars as pl  # noqa: PLC0415

        if isinstance(amount_principal, bool) or not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        # Still in deferral period
        if self.m_client_age < self.m_age_income_start:
            return 0.0

        benefit_base: float = float(amount_principal)

        if obj_scenarios is not None:
            required_cols = {"Date", self.m_financial_index}
            if not required_cols.issubset(set(obj_scenarios.columns)):
                missing = required_cols - set(obj_scenarios.columns)
                raise Exception_Validation_Input(
                    f"obj_scenarios is missing required columns: {missing}",
                    field_name="obj_scenarios",
                    expected_type=pl.DataFrame,
                    actual_value=obj_scenarios.columns,
                )
            term_returns = obj_scenarios[self.m_financial_index].to_list()
            account_values = self.calc_account_values_multi_term(
                amount_principal = amount_principal,
                term_index_returns = term_returns,
            )
            benefit_base = account_values[-1] if account_values else amount_principal
            _logger.info("RILA benefit base after index crediting: %.2f", benefit_base)
        else:
            _logger.info("RILA benefit base from principal: %.2f", benefit_base)

        annual_payout: float = benefit_base * self.m_annuity_payout_rate
        _logger.info("RILA annual payout: %.2f", annual_payout)

        return annual_payout

    def calc_withdrawal_rates(
        self: _RILA_Withdrawal_State, *, amount_principal: float, desired_WR: float | None = None, obj_scenarios: pl.DataFrame | None = None, obj_inflation: pl.DataFrame | None = None) -> Withdrawal_Rates:
        r"""Calculate nominal and real withdrawal rates for this RILA.

        The nominal withdrawal rate is the ratio of the RILA payout
        (account-value driven, index-credited across terms if scenarios
        are supplied) to the invested principal.  The real withdrawal rate
        deflates the nominal rate by the cumulative inverse inflation factor:

        $$
        WR_{\text{nominal}} = \frac{P_{\text{annual}}}{A}
        $$

        $$
        WR_{\text{real}} = WR_{\text{nominal}} \times IF^{-1}
        $$

        Parameters
        ----------
        amount_principal : float
            The principal amount invested.
        desired_WR : float | None, optional
            The desired withdrawal rate (as a decimal, e.g. 0.04 for 4 %).
        obj_scenarios : pl.DataFrame | None, optional
            Polars DataFrame containing scenario market data.
        obj_inflation : pl.DataFrame | None, optional
            Polars DataFrame with pre-calculated inflation factors.

        Returns
        -------
        Withdrawal_Rates
            Struct with ``nominal_WR`` and ``real_WR``.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if isinstance(amount_principal, bool) or not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        effective_desired_WR: float = (
            desired_WR if desired_WR is not None else self.m_annuity_payout_rate
        )
        if isinstance(effective_desired_WR, bool) or not isinstance(effective_desired_WR, (int, float)) or effective_desired_WR <= 0:
            raise Exception_Validation_Input(
                "desired_WR must be a positive number",
                field_name="desired_WR",
                expected_type=float,
                actual_value=effective_desired_WR,
            )

        # Nominal payout: inflation is not applied inside RILA calc_annuity_payout
        nominal_payout: float = self.calc_annuity_payout(
            amount_principal = amount_principal,
            obj_scenarios = obj_scenarios,
            obj_inflation = None,
        )
        nominal_WR: float = nominal_payout / amount_principal

        # Inverse inflation factor — defaults to 1.0 when no inflation data supplied
        inverse_inflation_factor: float = 1.0
        if obj_inflation is not None:
            required_cols = {
                "Start Date",
                "End Date",
                "Inflation Factor",
                "Inverse Inflation Factor",
            }
            if not required_cols.issubset(set(obj_inflation.columns)):
                missing = required_cols - set(obj_inflation.columns)
                raise Exception_Validation_Input(
                    f"obj_inflation is missing required columns: {missing}",
                    field_name="obj_inflation",
                    expected_type=type(obj_inflation),
                    actual_value=obj_inflation.columns,
                )
            inverse_inflation_factor = obj_inflation["Inverse Inflation Factor"].product()

        real_WR: float = nominal_WR * inverse_inflation_factor

        _logger.info(
            f"RILA withdrawal rates — desired={effective_desired_WR:.2%}, "
            f"nominal={nominal_WR:.4%}, real={real_WR:.4%}, "
            f"inverse_inflation_factor={inverse_inflation_factor:.6f}",
        )

        return Withdrawal_Rates(nominal_WR=nominal_WR, real_WR=real_WR)

    def calc_monthly_payout(
        self: _RILA_Withdrawal_State, *, amount_principal: float, obj_scenarios: pl.DataFrame | None = None, obj_inflation: pl.DataFrame | None = None) -> float:
        """Calculate the monthly equivalent of the annual payout.

        Parameters
        ----------
        amount_principal : float
            The principal amount invested.
        obj_scenarios : pl.DataFrame | None, optional
            Scenario data for payout calculations.
        obj_inflation : pl.DataFrame | None, optional
            Polars DataFrame with pre-calculated inflation factors (unused
            for RILA; kept for interface compatibility).

        Returns
        -------
        float
            The monthly equivalent payout amount.
        """
        annual_payout = self.calc_annuity_payout(
            amount_principal = amount_principal,
            obj_scenarios = obj_scenarios,
            obj_inflation = obj_inflation,
        )
        return annual_payout / 12

    # ------------------------------------------------------------------
    # Worst-case and best-case outcome analysis
    # ------------------------------------------------------------------

    def calc_worst_case_account_value(
        self: _RILA_Outcome_State, *, amount_principal: float, num_terms: int = 1) -> float:
        r"""Calculate the worst-case account value assuming maximum loss each term.

        For buffer protection:

        $$
        V_{\text{worst}} = P \times (1 - (1 - b))^{n}
        $$

        For floor protection:

        $$
        V_{\text{worst}} = P \times (1 + f)^{n}
        $$

        Parameters
        ----------
        amount_principal : float
            The initial premium invested.
        num_terms : int, optional
            Number of consecutive worst-case terms (default 1).

        Returns
        -------
        float
            The worst-case account value.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if isinstance(amount_principal, bool) or not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        if isinstance(num_terms, bool) or not isinstance(num_terms, int) or num_terms <= 0:
            raise Exception_Validation_Input(
                "num_terms must be a positive integer",
                field_name="num_terms",
                expected_type=int,
                actual_value=num_terms,
            )

        if self.m_protection_type == Protection_Type.BUFFER:
            # Worst case: index drops beyond buffer (theoretically -100 %)
            # Maximum per-term loss = 1 - buffer_rate (i.e. -90 % for 10 % buffer)
            worst_term_return = -1.0  # Total index wipeout
            worst_credited = self.calc_credited_rate(index_return = worst_term_return)
        else:
            # Floor protection: worst-case credited = floor_rate
            worst_credited = self.m_floor_rate

        charge_factor = (1 - self.m_rate_rider_charge) ** self.m_term_years
        value = float(amount_principal)
        for _ in range(num_terms):
            value *= (1 + worst_credited) * charge_factor
            value = max(value, 0.0)

        return value

    def calc_best_case_account_value(
        self: _RILA_Outcome_State, *, amount_principal: float, num_terms: int = 1) -> float:
        r"""Calculate the best-case account value assuming maximum gain each term.

        $$
        V_{\text{best}} = P \times (1 + c)^{n}
        $$

        Parameters
        ----------
        amount_principal : float
            The initial premium invested.
        num_terms : int, optional
            Number of consecutive best-case terms (default 1).

        Returns
        -------
        float
            The best-case account value.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid.
        """
        if isinstance(amount_principal, bool) or not isinstance(amount_principal, (int, float)) or amount_principal <= 0:
            raise Exception_Validation_Input(
                "amount_principal must be a positive number",
                field_name="amount_principal",
                expected_type=float,
                actual_value=amount_principal,
            )

        if isinstance(num_terms, bool) or not isinstance(num_terms, int) or num_terms <= 0:
            raise Exception_Validation_Input(
                "num_terms must be a positive integer",
                field_name="num_terms",
                expected_type=int,
                actual_value=num_terms,
            )

        if self.m_crediting_strategy == Crediting_Strategy.PERFORMANCE_TRIGGER:
            best_credited = self.m_performance_trigger_rate
        elif self.m_crediting_strategy == Crediting_Strategy.PARTICIPATION_RATE:
            best_credited = min(
                self.m_participation_rate * 1.0,  # assume 100 % index gain
                self.m_cap_rate,
            )
        else:
            best_credited = self.m_cap_rate

        charge_factor = (1 - self.m_rate_rider_charge) ** self.m_term_years
        value = float(amount_principal)
        for _ in range(num_terms):
            value *= (1 + best_credited) * charge_factor

        return value
