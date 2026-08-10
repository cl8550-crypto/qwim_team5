"""Goal Parity model (Roadmap Secs 1-5; Cron & Golts 2022, Golts & Jones 2023).

Six-step pipeline: investor profiling -> cash-flow EPV -> skew-adjusted vols
-> option-based 4x4 decomposition -> strategic optimization -> signal-priority
tactical rebalancing. Public entry points re-exported here.
"""

from __future__ import annotations

from src.models.goal_parity._goalparity_backtest import (
    BacktestFold,
    BacktestResult,
    run_walk_forward,
)
from src.models.goal_parity._goalparity_calibration import CalibrationSuite
from src.models.goal_parity._goalparity_cashflow import CashFlowEstimator, CashFlowProfile
from src.models.goal_parity._goalparity_data import AssetStats, AssetUniverse, load_default_universe
from src.models.goal_parity._goalparity_decomposition import (
    GoalDecomposer,
    GoalShares,
    first_passage_probability,
)
from src.models.goal_parity._goalparity_asset_map import asset_map_coordinates
from src.models.goal_parity._goalparity_optimization import (
    OptimizationResult,
    StrategicOptimizer,
    tilted_theta,
)
from src.models.goal_parity._goalparity_profiling import InvestorProfile
from src.models.goal_parity._goalparity_rebalancing import (
    RebalanceResult,
    SignalPriorityRebalancer,
    Trade,
)
from src.models.goal_parity._goalparity_volatility import AdjustedVolatility, VolatilityAdjuster
from src.models.goal_parity.utils_goal_parity import (
    GOALS,
    RISK_PROFILE_TO_ETA,
    THETA_BALANCED,
    eta_to_barrier,
    normalize_risk_profile,
)

__all__ = [
    "GOALS",
    "RISK_PROFILE_TO_ETA",
    "THETA_BALANCED",
    "AdjustedVolatility",
    "BacktestFold",
    "BacktestResult",
    "AssetStats",
    "AssetUniverse",
    "CalibrationSuite",
    "CashFlowEstimator",
    "CashFlowProfile",
    "GoalDecomposer",
    "GoalShares",
    "InvestorProfile",
    "OptimizationResult",
    "RebalanceResult",
    "SignalPriorityRebalancer",
    "StrategicOptimizer",
    "Trade",
    "VolatilityAdjuster",
    "asset_map_coordinates",
    "eta_to_barrier",
    "first_passage_probability",
    "load_default_universe",
    "normalize_risk_profile",
    "run_walk_forward",
    "tilted_theta",
]
