"""Shared (non-reactive) pipeline helpers for the Goal Parity dashboard tab.

Pure functions over the model layer so every subtab can recompute cheaply and
the logic stays unit-testable outside Shiny. The asset universe is loaded once
per process from the repo-level cleaned_data folder (see the model data layer).
"""

from __future__ import annotations

import functools

from dataclasses import dataclass

import numpy as np

from src.models.goal_parity import (
    CalibrationSuite,
    CashFlowEstimator,
    GoalDecomposer,
    InvestorProfile,
    OptimizationResult,
    RebalanceResult,
    SignalPriorityRebalancer,
    StrategicOptimizer,
    VolatilityAdjuster,
    asset_map_coordinates,
    load_default_universe,
)
from src.models.goal_parity.utils_goal_parity import GOALS


@functools.lru_cache(maxsize=1)
def calibrated_volatility_adjuster() -> VolatilityAdjuster:
    """VolatilityAdjuster with gamma0 fitted from the full universe's pooled
    daily returns (Golts & Jones 2023, Appendix A: a single gamma0 fitted
    across the whole universe, not per-asset), replacing the paper's
    illustrative default of 1.6. Cached: refitting on every reactive trigger
    would be wasteful, and the fitted value only depends on the (static)
    cleaned_data history, not on any per-request investor input."""
    universe = load_default_universe()
    returns_by_ticker = {t: universe.frames[t]["Log_Return"].to_numpy() for t in universe.tickers}
    gamma0 = CalibrationSuite.fit_gamma0_for_universe(returns_by_ticker)
    return VolatilityAdjuster(gamma0=gamma0)


@dataclass(frozen=True)
class PipelineOutput:
    """Steps 2-4 applied to the selected universe for one investor."""

    tickers: list[str]
    rows: list[dict]  # one display row per asset
    shares_by_ticker: dict[str, dict[str, float]]
    exp_returns: np.ndarray
    cash_tickers: list[str]


#: Below this max single-asset goal share, no asset in the universe -- and
#: therefore no portfolio built from it, even at 100% weight -- can power the
#: goal much past this level. Distinguishes "structurally scarce in this data"
#: from "the optimizer under-shot." Chosen with headroom below the Income
#: goal's ~0.44 max share (the next-lowest of the four in the 18-asset
#: universe), well above Preservation's observed ~0.11.
SCARCE_GOAL_MAX_SHARE_THRESHOLD: float = 0.20


def scarce_goals(pipeline: PipelineOutput) -> list[str]:
    """Goals with no meaningfully-scoring asset in the selected universe.

    Cheap proxy for "what's the max achievable power at 100% tilt": the max
    per-asset goal share, read directly off `shares_by_ticker`, needs no
    optimizer solve and empirically tracks the expensive full-tilt result
    (e.g. Preservation: ~0.11 max share vs. ~0.10 max achieved tilted power).
    """
    scarce = []
    for goal in GOALS:
        max_share = max(
            (pipeline.shares_by_ticker[t][goal] for t in pipeline.tickers),
            default=0.0,
        )
        if max_share < SCARCE_GOAL_MAX_SHARE_THRESHOLD:
            scarce.append(goal)
    return scarce


def available_assets() -> dict[str, str]:
    """ticker -> display label for the dashboard checkbox group."""
    universe = load_default_universe()
    return {t: f"{t} — {universe.names[t]} ({universe.classes[t]})" for t in universe.tickers}


def decompose_universe(profile: InvestorProfile, tickers: list[str] | None = None) -> PipelineOutput:
    """Run Steps 2-4 for the selected assets under the given investor profile."""
    universe = load_default_universe()
    selected = [t for t in (tickers or universe.tickers) if t in universe.frames]
    if not selected:
        selected = universe.tickers
    cashflow = CashFlowEstimator()
    volatility = calibrated_volatility_adjuster()
    decomposer = GoalDecomposer()

    rows: list[dict] = []
    shares_by_ticker: dict[str, dict[str, float]] = {}
    exp_returns: list[float] = []
    for stats in universe.all_stats(selected):
        cf_profile = cashflow.profile(stats, profile.T)
        adjusted = volatility.adjust(stats)
        goal_shares = decomposer.decompose(
            stats.ticker,
            cf_profile.epv,
            adjusted.sigma_d,
            adjusted.sigma_l,
            profile.T,
            profile.tau_years,
            profile.b,
        )
        x, y = asset_map_coordinates(goal_shares)
        shares_by_ticker[stats.ticker] = goal_shares.shares
        exp_returns.append(stats.a)
        rows.append(
            {
                "Ticker": stats.ticker,
                "Name": stats.name,
                "Class": stats.asset_class,
                "a": stats.a,
                "sigma": stats.sigma,
                "gamma": stats.gamma,
                "EPV": goal_shares.epv,
                "WAM": cf_profile.wam,
                "pi_default": goal_shares.pi_default,
                "pi_liquidity": goal_shares.pi_liquidity,
                **{goal: goal_shares.shares[goal] for goal in GOALS},
                "map_x": x,
                "map_y": y,
            }
        )
    return PipelineOutput(
        tickers=selected,
        rows=rows,
        shares_by_ticker=shares_by_ticker,
        exp_returns=np.array(exp_returns),
        cash_tickers=[t for t in universe.cash_tickers() if t in selected],
    )


def run_strategic(
    pipeline: PipelineOutput,
    mode: str = "balanced",
    tilt_goal: str = "Growth",
    tilt_strength: float = 1.0,
) -> OptimizationResult:
    """Step 5 on a decomposed universe (Sec 3.5). ``tilt_strength`` in [0, 1]
    interpolates between Balanced (0.0) and a maximal tilt (1.0), per the
    paper's own partial-tilt example (Golts & Jones 2023, p.12)."""
    optimizer = StrategicOptimizer()
    if mode == "balanced":
        return optimizer.solve_balanced(
            pipeline.tickers, pipeline.exp_returns, pipeline.shares_by_ticker
        )
    return optimizer.solve_tilted(
        pipeline.tickers,
        pipeline.exp_returns,
        pipeline.shares_by_ticker,
        tilt_goal,
        tilt_strength=tilt_strength,
    )


def run_rebalance_demo(
    pipeline: PipelineOutput,
    strategic: OptimizationResult,
    drift_scale: float = 0.25,
    seed: int = 5,
) -> RebalanceResult:
    """Step 6 demo (Sec 3.6/4.2): drift the strategic weights with a seeded
    shock, then re-align toward the strategic portfolio's achieved goal powers
    ("re-aligning with strategic goal powers", Roadmap Sec 1)."""
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0.0, drift_scale, len(strategic.weights)).clip(-0.9, 0.9)
    drifted = np.clip(strategic.weights * (1.0 + shocks), 0.0, None)
    total = drifted.sum()
    drifted = drifted / total if total > 0 else strategic.weights
    rebalancer = SignalPriorityRebalancer(cash_min=0.02)
    return rebalancer.rebalance(
        pipeline.tickers,
        drifted,
        pipeline.shares_by_ticker,
        strategic.goal_powers,
        cash_tickers=pipeline.cash_tickers,
    )
