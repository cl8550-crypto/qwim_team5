"""Offline CVaR policy construction for the five QWIM risk profiles.

The policies are intentionally produced *offline*.  A client record selects one
of the stored policies; it does not trigger portfolio optimisation in the
Dashboard.  Each profile controls the permitted equity exposure, while the
optimiser minimises historical Expected Shortfall (CVaR) inside that band.
"""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cvxpy as cp
import numpy as np


if TYPE_CHECKING:
    from collections.abc import Mapping

    import pandas as pd


@dataclass(frozen=True, slots=True)
class Risk_Profile_Band:  # noqa: N801
    """Permitted equity allocation for one client risk-tolerance category."""

    profile: str
    minimum_equity_weight: float
    maximum_equity_weight: float

    def __post_init__(self) -> None:
        if not self.profile:
            raise ValueError("profile must not be empty")
        if not 0 <= self.minimum_equity_weight <= self.maximum_equity_weight <= 1:
            raise ValueError("equity weights must satisfy 0 <= minimum <= maximum <= 1")


@dataclass(frozen=True, slots=True)
class Predefined_Portfolio_Policy:  # noqa: N801
    """A stored long-only policy selected by a client's risk profile."""

    profile: str
    weights: Mapping[str, float]
    expected_shortfall: float
    confidence_level: float
    equity_band: Risk_Profile_Band

    def dollar_allocations(self, investable_wealth: float) -> dict[str, float]:
        """Scale policy weights to the wealth explicitly allocated to this plan."""
        if not np.isfinite(investable_wealth) or investable_wealth < 0:
            raise ValueError("investable_wealth must be finite and non-negative")
        return {asset: investable_wealth * weight for asset, weight in self.weights.items()}


# The labels deliberately match the current Dashboard/PDF client-data contract.
DEFAULT_RISK_PROFILE_BANDS: tuple[Risk_Profile_Band, ...] = (
    Risk_Profile_Band("Conservative", 0.05, 0.25),
    Risk_Profile_Band("Moderate Conservative", 0.25, 0.40),
    Risk_Profile_Band("Moderate", 0.40, 0.55),
    Risk_Profile_Band("Moderate Aggressive", 0.55, 0.70),
    Risk_Profile_Band("Aggressive", 0.70, 0.85),
)

PREDEFINED_POLICY_VERSION = "cvar-v1-2026-07"


def normalize_risk_profile(label: str) -> str:
    """Validate a risk-tolerance label from the client-data contract."""
    cleaned = " ".join(str(label).strip().split())
    profiles = {band.profile for band in DEFAULT_RISK_PROFILE_BANDS}
    if cleaned not in profiles:
        raise ValueError(f"Unknown risk profile {label!r}; expected one of {sorted(profiles)}")
    return cleaned


def load_predefined_cvar_policies() -> dict[str, Predefined_Portfolio_Policy]:
    """Load the versioned, offline-calibrated policy table used by Dashboard."""
    policy_file = Path(__file__).with_name("data") / "cvar_policy_v1.json"
    with policy_file.open(encoding="utf-8") as file_handle:
        document = json.load(file_handle)
    if document.get("version") != PREDEFINED_POLICY_VERSION:
        raise ValueError(f"Unexpected predefined policy version in {policy_file.name}")
    bands = {band.profile: band for band in DEFAULT_RISK_PROFILE_BANDS}
    policies: dict[str, Predefined_Portfolio_Policy] = {}
    for item in document["policies"]:
        profile = normalize_risk_profile(item["profile"])
        if profile in policies:
            raise ValueError(f"Duplicate predefined policy for {profile!r}")
        weights = {asset: float(weight) for asset, weight in item["weights"].items()}
        if not weights or any(weight < 0 for weight in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
            raise ValueError(f"Invalid weights for predefined policy {profile!r}")
        policies[profile] = Predefined_Portfolio_Policy(
            profile=profile,
            weights=weights,
            expected_shortfall=float(item["expected_shortfall_95"]),
            confidence_level=float(document["confidence_level"]),
            equity_band=bands[profile],
        )
    if set(policies) != set(bands):
        raise ValueError("Predefined policy table must contain every risk profile exactly once")
    return policies


def build_cvar_policies(
    monthly_returns: pd.DataFrame,
    *,
    equity_assets: tuple[str, ...],
    confidence_level: float = 0.95,
    max_weight: Mapping[str, float] | None = None,
    bands: tuple[Risk_Profile_Band, ...] = DEFAULT_RISK_PROFILE_BANDS,
) -> dict[str, Predefined_Portfolio_Policy]:
    """Build five long-only minimum-Expected-Shortfall policies offline.

    ``monthly_returns`` contains simple returns, one asset per column.  For
    each risk band the model minimises historical CVaR at ``confidence_level``
    subject to full investment, long-only holdings, asset caps, and a required
    equity-exposure interval.  The lower equity bound is deliberate: without
    it, all five risk profiles could select the same lowest-CVaR portfolio.
    """
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie strictly between 0 and 1")
    if monthly_returns.empty:
        raise ValueError("monthly_returns must not be empty")
    if monthly_returns.columns.has_duplicates:
        raise ValueError("monthly_returns columns must be unique asset names")
    if not equity_assets or len(set(equity_assets)) != len(equity_assets):
        raise ValueError("equity_assets must be non-empty and unique")
    missing_equity_assets = set(equity_assets).difference(monthly_returns.columns)
    if missing_equity_assets:
        raise ValueError(f"equity_assets are absent from monthly_returns: {sorted(missing_equity_assets)}")
    if not bands or len({band.profile for band in bands}) != len(bands):
        raise ValueError("bands must contain unique profiles")

    returns = monthly_returns.astype(float).dropna()
    if len(returns) < 2 or not np.isfinite(returns.to_numpy()).all():
        raise ValueError("monthly_returns requires at least two complete finite rows")
    assets = tuple(str(asset) for asset in returns.columns)
    caps = dict.fromkeys(assets, 1.0)
    if max_weight is not None:
        unknown_assets = set(max_weight).difference(assets)
        if unknown_assets:
            raise ValueError(f"max_weight contains unknown assets: {sorted(unknown_assets)}")
        caps.update(max_weight)
    if any(not np.isfinite(cap) or not 0 <= cap <= 1 for cap in caps.values()):
        raise ValueError("max_weight values must lie in [0, 1]")
    if sum(caps.values()) < 1 - 1e-9:
        raise ValueError("max_weight caps cannot fund a fully invested portfolio")

    matrix = returns.to_numpy()
    weights = cp.Variable(len(assets), nonneg=True)
    value_at_risk = cp.Variable()
    excess_loss = cp.Variable(len(returns), nonneg=True)
    losses = -matrix @ weights
    equity_indices = [assets.index(asset) for asset in equity_assets]
    base_constraints = [
        cp.sum(weights) == 1,
        weights <= np.array([caps[asset] for asset in assets]),
        excess_loss >= losses - value_at_risk,
    ]
    tail_probability = 1 - confidence_level
    objective = cp.Minimize(value_at_risk + cp.sum(excess_loss) / (tail_probability * len(returns)))

    policies: dict[str, Predefined_Portfolio_Policy] = {}
    for band in bands:
        problem = cp.Problem(
            objective,
            [
                *base_constraints,
                cp.sum(weights[equity_indices]) >= band.minimum_equity_weight,
                cp.sum(weights[equity_indices]) <= band.maximum_equity_weight,
            ],
        )
        problem.solve(solver=cp.CLARABEL)
        if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE} or weights.value is None:
            raise ValueError(f"No feasible CVaR policy for {band.profile!r}: {problem.status}")
        solved_weights = np.maximum(np.asarray(weights.value, dtype=float).reshape(-1), 0.0)
        solved_weights /= solved_weights.sum()
        portfolio_losses = -matrix @ solved_weights
        expected_shortfall = _historical_expected_shortfall(portfolio_losses, confidence_level)
        policies[band.profile] = Predefined_Portfolio_Policy(
            profile=band.profile,
            weights=dict(zip(assets, solved_weights, strict=True)),
            expected_shortfall=expected_shortfall,
            confidence_level=confidence_level,
            equity_band=band,
        )
    return policies


def _historical_expected_shortfall(losses: np.ndarray, confidence_level: float) -> float:
    """Mean loss in the worst tail, reported as a non-negative loss fraction."""
    ordered_losses = np.sort(np.asarray(losses, dtype=float))
    observations = max(1, int(np.ceil((1 - confidence_level) * len(ordered_losses))))
    return float(max(0.0, ordered_losses[-observations:].mean()))
