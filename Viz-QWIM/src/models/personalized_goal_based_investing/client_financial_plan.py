"""Adapter from Clients Dashboard values to staged goal-model cash flows.

The adapter deliberately keeps a client's reported assets, contributions,
guaranteed income, and recurring retirement spending separate.  It does not
turn annual spending into a one-time goal amount or silently apply taxes,
longevity, or inflation assumptions.
"""

from __future__ import annotations

import math

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.models.personalized_goal_based_investing.model_goal_postponement import (
    Portfolio_Specification,
    Priority_Spending_Specification,
)
from src.models.personalized_goal_based_investing.risk_portfolio_policy import normalize_risk_profile


if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.models.personalized_goal_based_investing.risk_portfolio_policy import Predefined_Portfolio_Policy


@dataclass(frozen=True, slots=True)
class Client_Financial_Plan:  # noqa: N801
    """Normalized client inputs for an annual or periodic goal-model horizon."""

    risk_profile: str
    initial_wealth: float
    retirement_stage: int
    contribution_by_stage: Mapping[int, float]
    income_by_stage: Mapping[int, float]
    income_by_source_stage: Mapping[str, Mapping[int, float]]
    spending_by_stage: Mapping[int, float]
    spending_by_priority_stage: Mapping[str, Mapping[int, float]]
    annual_spending_by_priority: Mapping[str, float]
    annual_guaranteed_income: float

    @property
    def annual_retirement_gap(self) -> float:
        """Annual recurring need not covered by the listed guaranteed income."""
        return max(0.0, sum(self.annual_spending_by_priority.values()) - self.annual_guaranteed_income)


@dataclass(frozen=True, slots=True)
class Income_Source_Specification:  # noqa: N801
    """Timing and nominal growth assumptions for one guaranteed income source.

    ``annual_amount`` is the amount at ``start_age``.  A finite ``end_age``
    means the source ends after that age's scheduled payment; ``None`` means
    it continues through the model horizon.  This deliberately represents an
    input contract only: the current Clients dashboard still supplies a
    single shared income-start age, so the adapter creates equivalent default
    specifications until source-level fields are available.
    """

    annual_amount: float
    start_age: int
    end_age: int | None = None
    annual_growth_rate: float = 0.0

    def __post_init__(self) -> None:
        _non_negative_amount(self.annual_amount, "annual_amount")
        if not isinstance(self.start_age, int) or self.start_age < 0:
            raise ValueError("start_age must be a non-negative integer")
        if self.end_age is not None and (not isinstance(self.end_age, int) or self.end_age < self.start_age):
            raise ValueError("end_age must be None or an integer no earlier than start_age")
        if not math.isfinite(self.annual_growth_rate) or self.annual_growth_rate <= -1:
            raise ValueError("annual_growth_rate must be finite and greater than -1")


def build_client_financial_plan(
    *,
    risk_profile: str,
    confirmed_plan_assets: float,
    current_age: int,
    retirement_age: int,
    income_start_age: int,
    annual_contribution: float,
    annual_goals: Mapping[str, float],
    annual_income: Mapping[str, float],
    horizon_periods: int,
    periods_per_year: int = 1,
    income_sources: Mapping[str, Income_Source_Specification] | None = None,
) -> Client_Financial_Plan:
    """Map Clients values to recurring schedules for the research model.

    ``annual_goals`` must use the existing ``essential``, ``important``, and
    ``aspirational`` keys.  The current Clients tab supplies only annual
    amounts, so all listed income sources are conservatively scheduled from
    ``income_start_age`` and all spending begins at retirement.  Callers with
    source-level start/end ages and nominal growth assumptions can pass
    ``income_sources`` without changing the output contract.
    """
    if not isinstance(horizon_periods, int) or horizon_periods < 1:
        raise ValueError("horizon_periods must be a positive integer")
    if not isinstance(periods_per_year, int) or periods_per_year < 1:
        raise ValueError("periods_per_year must be a positive integer")
    for name, age in {
        "current_age": current_age,
        "retirement_age": retirement_age,
        "income_start_age": income_start_age,
    }.items():
        if not isinstance(age, int) or age < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if retirement_age < current_age:
        raise ValueError("retirement_age must be at least current_age")
    if income_start_age < current_age:
        raise ValueError("income_start_age must be at least current_age")
    wealth = _non_negative_amount(confirmed_plan_assets, "confirmed_plan_assets")
    contribution = _non_negative_amount(annual_contribution, "annual_contribution")
    spending = _priority_amounts(annual_goals)
    guaranteed_income = _source_amounts(annual_income)

    final_stage = horizon_periods + 1
    retirement_stage = min(
        final_stage,
        2 + (retirement_age - current_age) * periods_per_year,
    )
    periodic_contribution = contribution / periods_per_year
    periodic_spending = sum(spending.values()) / periods_per_year
    scheduled_sources = _income_sources_or_default(
        amounts=guaranteed_income,
        income_start_age=income_start_age,
        income_sources=income_sources,
    )
    income_by_source_stage = {
        source: _schedule_income_source(
            specification=specification,
            current_age=current_age,
            final_stage=final_stage,
            periods_per_year=periods_per_year,
        )
        for source, specification in scheduled_sources.items()
    }
    income_by_stage = {
        stage: amount
        for stage in range(2, final_stage + 1)
        if (amount := sum(schedule.get(stage, 0.0) for schedule in income_by_source_stage.values())) > 0
    }
    if not income_by_stage:
        income_by_stage = {min(final_stage, 2 + (income_start_age - current_age) * periods_per_year): 0.0}
    spending_by_priority_stage = {
        priority: dict.fromkeys(
            range(retirement_stage, final_stage + 1),
            amount / periods_per_year,
        )
        for priority, amount in spending.items()
    }

    return Client_Financial_Plan(
        risk_profile=normalize_risk_profile(risk_profile),
        initial_wealth=wealth,
        retirement_stage=retirement_stage,
        contribution_by_stage=dict.fromkeys(range(2, retirement_stage), periodic_contribution),
        income_by_stage=income_by_stage,
        income_by_source_stage=income_by_source_stage,
        spending_by_stage=dict.fromkeys(range(retirement_stage, final_stage + 1), periodic_spending),
        spending_by_priority_stage=spending_by_priority_stage,
        annual_spending_by_priority=spending,
        annual_guaranteed_income=sum(
            schedule.get(retirement_stage, 0.0) * periods_per_year
            for schedule in income_by_source_stage.values()
        ),
    )


def build_portfolio_specification_from_plan(
    *,
    financial_plan: Client_Financial_Plan,
    policy: Predefined_Portfolio_Policy,
    cash_asset: str = "BIL",
    equity_assets: tuple[str, ...] = ("XLK", "XLP"),
    transaction_cost: float = 0.0,
    asset_weight_tolerance: float = 0.10,
    shortfall_penalties: Mapping[str, float] | None = None,
) -> Portfolio_Specification:
    """Translate a client plan and selected CVaR policy into MSMIP inputs.

    The policy continues to be selected by the client's risk tolerance.  Its
    equity band becomes a hard multi-stage risky-weight constraint, while each
    non-cash policy allocation receives a transparent cap of policy weight
    plus ``asset_weight_tolerance``.  The three recurring spending tiers are
    retained as soft constraints with ordered funding penalties.
    """
    if policy.profile != financial_plan.risk_profile:
        raise ValueError("policy profile must match the financial plan risk profile")
    if cash_asset not in policy.weights:
        raise ValueError(f"selected policy must contain cash asset {cash_asset!r}")
    if not math.isfinite(transaction_cost) or not 0 <= transaction_cost < 1:
        raise ValueError("transaction_cost must lie in [0, 1)")
    if not math.isfinite(asset_weight_tolerance) or not 0 <= asset_weight_tolerance <= 1:
        raise ValueError("asset_weight_tolerance must lie in [0, 1]")
    assets = (cash_asset, *(asset for asset in policy.weights if asset != cash_asset))
    risky_assets = tuple(asset for asset in equity_assets if asset in assets)
    if not risky_assets:
        raise ValueError("selected policy must contain at least one configured equity asset")
    penalties = {"essential": 1_000.0, "important": 100.0, "aspirational": 10.0}
    if shortfall_penalties is not None:
        if set(shortfall_penalties) != set(penalties):
            raise ValueError("shortfall_penalties must cover essential, important, and aspirational")
        penalties = {priority: float(value) for priority, value in shortfall_penalties.items()}
    return Portfolio_Specification(
        assets=assets,
        cash_asset=cash_asset,
        initial_wealth=financial_plan.initial_wealth,
        transaction_cost=dict.fromkeys(assets[1:], transaction_cost),
        max_weight={
            asset: min(1.0, policy.weights[asset] + asset_weight_tolerance)
            for asset in assets[1:]
        },
        income_by_stage=financial_plan.income_by_stage,
        contribution_by_stage=financial_plan.contribution_by_stage,
        risky_assets=risky_assets,
        minimum_risky_weight=policy.equity_band.minimum_equity_weight,
        maximum_risky_weight=policy.equity_band.maximum_equity_weight,
        priority_spending=tuple(
            Priority_Spending_Specification(
                priority=priority,
                amount_by_stage=financial_plan.spending_by_priority_stage[priority],
                shortfall_penalty=penalties[priority],
            )
            for priority in ("essential", "important", "aspirational")
        ),
    )


def _non_negative_amount(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite non-negative number")
    amount = float(value)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return amount


def _income_sources_or_default(
    *,
    amounts: Mapping[str, float],
    income_start_age: int,
    income_sources: Mapping[str, Income_Source_Specification] | None,
) -> Mapping[str, Income_Source_Specification]:
    """Return explicit source schedules, retaining current-dashboard defaults."""
    if income_sources is None:
        return {
            source: Income_Source_Specification(amount, start_age=income_start_age)
            for source, amount in amounts.items()
        }
    if set(income_sources) != set(amounts):
        raise ValueError("income_sources must contain exactly the annual_income source names")
    for source, specification in income_sources.items():
        if not math.isclose(specification.annual_amount, amounts[source], abs_tol=1e-9):
            raise ValueError(f"income_sources[{source!r}].annual_amount must match annual_income")
    return income_sources


def _schedule_income_source(
    *,
    specification: Income_Source_Specification,
    current_age: int,
    final_stage: int,
    periods_per_year: int,
) -> dict[int, float]:
    """Create one source's periodic nominal cash-flow schedule."""
    start_stage = max(2, 2 + (specification.start_age - current_age) * periods_per_year)
    end_stage = final_stage
    if specification.end_age is not None:
        end_stage = min(end_stage, 2 + (specification.end_age - current_age) * periods_per_year)
    if start_stage > end_stage:
        return {}
    return {
        stage: specification.annual_amount
        / periods_per_year
        * (1 + specification.annual_growth_rate) ** ((stage - start_stage) / periods_per_year)
        for stage in range(start_stage, end_stage + 1)
    }


def _priority_amounts(values: Mapping[str, float]) -> dict[str, float]:
    required = {"essential", "important", "aspirational"}
    if set(values) != required:
        raise ValueError(f"annual_goals must contain exactly {sorted(required)}")
    return {priority: _non_negative_amount(value, f"annual_goals[{priority!r}]") for priority, value in values.items()}


def _source_amounts(values: Mapping[str, float]) -> dict[str, float]:
    required = {"social_security", "pension", "annuity_existing", "other"}
    if set(values) != required:
        raise ValueError(f"annual_income must contain exactly {sorted(required)}")
    return {source: _non_negative_amount(value, f"annual_income[{source!r}]") for source, value in values.items()}
