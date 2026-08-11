"""Solve and pickle goal-based investing plans for the dashboard.

Run this offline (not from within Shiny) whenever a client's goals or the
underlying market data changes. It writes one ``.pkl`` per client to
``inputs/processed/personalized_goal_based_investing/``, which ``utils_data.py``'s
``get_personalized_goal_based_investing_results()`` loads at dashboard startup.

Usage
-----
    python3 scripts/solve_and_pickle_goal_plans.py

Run from the repository root (so the relative ``inputs/`` path resolves and
so ``src.models.personalized_goal_based_investing`` imports correctly -- see the
import-path warning in ``utils_data.py``'s docstring for why this matters).

This script currently defines its client list and market-data source
inline in ``CLIENTS`` and ``load_market_returns()`` below -- replace those
with a real query against your client database / cleaned_data folder once
one exists. It is a template, not a production data pipeline.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas_contract import result

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# IMPORTANT: this import path must exactly match what utils_data.py uses to
# unpickle -- both must say "src.models.personalized_goal_based_investing", not a bare
# "personalized_goal_based_investing" import, or ModuleNotFoundError will surface later
# at dashboard load time instead of here.
from src.models.personalized_goal_based_investing import (
    CovarianceConfig,
    Goal,
    GoalSet,
    MSGPConfig,
    MSGPOptimizer,
    BootstrapConfig,
    build_scenario_tree,
    estimate_expected_returns,
    ewma_shrinkage_covariance,
    generate_bootstrap_stage_paths_with_inflation,
)

from src.models.personalized_goal_based_investing.stochastic_optimizer import (
    EfficientFrontierContext,
)

OUTPUT_DIR = PROJECT_ROOT / "inputs" / "processed" / "personalized_goal_based_investing"


#: cleaned_data/ lives next to Viz-QWIM, not inside it -- two levels above this
#: script's own project root (which points at Viz-QWIM/).
CLEANED_DATA_DIR = PROJECT_ROOT.parent / "cleaned_data"

#: Cash proxy: 1-3 month T-Bill ETF, used as asset index 0 per the model's
#: convention that the first asset is cash/cash-equivalent.
CASH_FILE = CLEANED_DATA_DIR / "rates" / "BIL_Risk_Free_Rate_1_3M_TBill.csv"

BOND_FILES = {
    "Bonds_Aggregate": CLEANED_DATA_DIR / "bonds" / "AGG_US_Aggregate_Bonds.csv",
    "Bonds_TIPS": CLEANED_DATA_DIR / "bonds" / "TIP_TIPS.csv",
}
COMMODITY_FILES = {
    "Commodities_Broad": CLEANED_DATA_DIR / "commodities" / "DBC_Commodities_Broad.csv",
    "Gold": CLEANED_DATA_DIR / "commodities" / "GLD_Gold.csv",
}
#: XLC (Communication Services, inception 2018-06) and XLRE (Real Estate,
#: inception 2015-10) are deliberately excluded from the default universe:
#: including them forces the inner-join (needed so the bootstrap preserves
#: true cross-asset correlation) to truncate ALL assets to mid-2018 onward,
#: losing the 2008 crisis, the 2013 taper tantrum, and most of the
#: post-2008 rate cycle -- a thin, single-regime sample for a 25-45 year
#: retirement bootstrap. Set INCLUDE_LATE_INCEPTION_SECTORS = True to
#: include them anyway (e.g. if you deliberately want a shorter, more
#: recent-regime sample, or plan to handle the two ETFs' shorter history
#: with a different alignment approach than a simple inner join).
INCLUDE_LATE_INCEPTION_SECTORS = False

SECTOR_FILES = {
    "Sector_Materials": CLEANED_DATA_DIR / "sectors" / "XLB_Materials.csv",
    "Sector_Energy": CLEANED_DATA_DIR / "sectors" / "XLE_Energy.csv",
    "Sector_Financials": CLEANED_DATA_DIR / "sectors" / "XLF_Financials.csv",
    "Sector_Industrials": CLEANED_DATA_DIR / "sectors" / "XLI_Industrials.csv",
    "Sector_Technology": CLEANED_DATA_DIR / "sectors" / "XLK_Technology.csv",
    "Sector_Consumer_Staples": CLEANED_DATA_DIR / "sectors" / "XLP_Consumer_Staples.csv",
    "Sector_Utilities": CLEANED_DATA_DIR / "sectors" / "XLU_Utilities.csv",
    "Sector_Health_Care": CLEANED_DATA_DIR / "sectors" / "XLV_Health_Care.csv",
    "Sector_Consumer_Discretionary": CLEANED_DATA_DIR / "sectors" / "XLY_Consumer_Discretionary.csv",
}
if INCLUDE_LATE_INCEPTION_SECTORS:
    SECTOR_FILES["Sector_Communication_Services"] = CLEANED_DATA_DIR / "sectors" / "XLC_Communication_Services.csv"
    SECTOR_FILES["Sector_Real_Estate"] = CLEANED_DATA_DIR / "sectors" / "XLRE_Real_Estate.csv"

INFLATION_FILE = CLEANED_DATA_DIR / "macro" / "CPI_Monthly_CPIAUCSL.csv"


def _load_log_return_series(path: Path, label: str) -> pd.Series:
    """Read one cleaned_data CSV and return its daily simple-return series.

    The files store ``Log_Return`` (already computed, first row NaN). We
    convert to simple returns (``exp(log_return) - 1``) because the
    personalized_goal_based_investing package compounds returns multiplicatively via
    ``prod(1 + r) - 1`` throughout (stage compounding, wealth evolution),
    which assumes simple, not log, returns.
    """
    if not path.exists():
        raise FileNotFoundError(f"Expected data file for '{label}' not found: {path}")
    df = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    if "Log_Return" not in df.columns:
        raise ValueError(f"'{label}' file has no Log_Return column: {path}")
    simple_return = np.expm1(df["Log_Return"])
    simple_return.name = label
    return simple_return.dropna()


def load_market_returns() -> pd.DataFrame:
    """Load and align the historical monthly return series for the asset universe.

    Reads each asset's daily ``Log_Return`` column, converts to simple
    returns, inner-joins all series on common trading dates (required so the
    bootstrap draws simultaneous, correlation-preserving observations), then
    compounds daily returns up to monthly. Column 0 is always the cash proxy
    (BIL), matching the model's convention that the first asset is cash.

    Returns
    -------
    pd.DataFrame
        Monthly simple returns, DatetimeIndex (month-end), one column per
        asset, cash first.
    """
    all_files = {"Cash": CASH_FILE, **BOND_FILES, **COMMODITY_FILES, **SECTOR_FILES}

    daily_series = [_load_log_return_series(path, label) for label, path in all_files.items()]
    daily_returns = pd.concat(daily_series, axis=1, join="inner")

    if daily_returns.empty:
        raise ValueError(
            "No overlapping dates across the asset universe after inner join -- "
            "check CLEANED_DATA_DIR and file paths are correct."
        )
    print(
        f"Joint daily history: {daily_returns.index.min().date()} to "
        f"{daily_returns.index.max().date()} ({len(daily_returns)} trading days, "
        f"{daily_returns.shape[1]} assets)"
    )

    monthly_returns = daily_returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    # Cash must stay column 0 -- resample/concat above preserves dict insertion
    # order via pd.concat, but assert it explicitly since the model's
    # stage-0 cash convention silently breaks if this ever isn't true.
    assert monthly_returns.columns[0] == "Cash", "Cash must be asset column 0."
    return monthly_returns


def load_inflation_series(aligned_index: pd.DatetimeIndex) -> pd.Series:
    """Load month-over-month CPI inflation, aligned to the asset return dates.

    Parameters
    ----------
    aligned_index : pd.DatetimeIndex
        The (monthly) index of ``load_market_returns()``'s output; the
        inflation series is reindexed/forward-filled to match it exactly, so
        it can be jointly bootstrapped with asset returns.

    Returns
    -------
    pd.Series
        Month-over-month inflation rate, same index as ``aligned_index``.
    """
    if not INFLATION_FILE.exists():
        raise FileNotFoundError(f"Inflation data file not found: {INFLATION_FILE}")
    raw = pd.read_csv(INFLATION_FILE, parse_dates=["Date"]).set_index("Date").sort_index()

    value_col = next(
        (c for c in raw.columns if c.lower() in ("cpiaucsl", "value", "close", "cpi")), None
    )
    if value_col is None:
        raise ValueError(
            f"Could not find a CPI level column in {INFLATION_FILE}; "
            f"columns present: {list(raw.columns)}. Update `value_col` detection above."
        )

    monthly_level = raw[value_col].resample("ME").last()
    inflation_rate = monthly_level.pct_change().dropna()
    inflation_rate.name = "inflation"

    aligned = inflation_rate.reindex(aligned_index, method="ffill")
    if aligned.isna().any():
        raise ValueError(
            "Inflation series could not be fully aligned to the asset return dates "
            "(gaps after forward-fill) -- check date ranges overlap."
        )
    return aligned


#: Client goal definitions. Replace with a real per-client data source.
CLIENTS: dict[str, GoalSet] = {
    "jane_doe_retirement": GoalSet([
        Goal(
            name="Retirement",
            target_wealth=800_000,
            horizon_stage=3,
            priority=1,
            current_wealth=150_000,
            contribution_schedule={1: 40_000, 2: 50_000},
            cvar_alpha=0.90,
            cvar_shortfall_ratio=0.5,
        ),
        Goal(name="Children's Education", target_wealth=120_000, horizon_stage=2, priority=2),
    ]),
}

#: Stage structure shared across clients in this example (5y/10y/10y in months).
STAGE_LENGTHS_MONTHS = [60, 120, 120]
BRANCHING = [4, 3, 3]
STAGE_YEARS = [0, 5, 15, 25]


def solve_one_client(goal_set: GoalSet, returns: pd.DataFrame, inflation: pd.Series) -> "MSGPResult":  # noqa: F821
    """Run the full estimation -> bootstrap -> tree -> MSGP pipeline for one client."""
    cov_ann, _ = ewma_shrinkage_covariance(returns, CovarianceConfig(ewma_lambda=0.97, annualization_factor=12))
    mkt_weights = np.full(returns.shape[1], 1.0 / returns.shape[1])  # placeholder: use real benchmark weights
    mu_ann = estimate_expected_returns(
        "black_litterman", returns, cov_ann, market_weights=mkt_weights,
        risk_free_rate=0.03, market_risk_premium=0.045,
    )

    paths, inflation_paths = generate_bootstrap_stage_paths_with_inflation(
        returns, inflation, STAGE_LENGTHS_MONTHS, n_paths=3000,
        config=BootstrapConfig(expected_block_length=12, random_state=42),
        target_mean=mu_ann, target_cov=cov_ann,
    )
    tree = build_scenario_tree(
        paths, BRANCHING, list(returns.columns), inflation_paths=inflation_paths, random_state=42
    )

    cfg = MSGPConfig(
        stage_years=STAGE_YEARS, discount_rate=0.03, max_weight=0.45,
        turnover_limit=1.8, txn_cost_buy=0.001, txn_cost_sell=0.001,
    )
    result = MSGPOptimizer(tree, goal_set, cfg).solve()

    result.efficient_frontier_context = EfficientFrontierContext(
        expected_returns=mu_ann,
        covariance=cov_ann,
        assets=list(returns.columns),
    )

    return result
    # Store the inputs used to construct the efficient frontier.
    result.stage0_expected_returns = mu_ann
    result.stage0_covariance = cov_ann

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    returns = load_market_returns()
    inflation = load_inflation_series(returns.index)

    for client_id, goal_set in CLIENTS.items():
        print(f"Solving {client_id} ...")
        result = solve_one_client(goal_set, returns, inflation)

        out_path = OUTPUT_DIR / f"{client_id}.pkl"
        with out_path.open("wb") as f:
            pickle.dump(result, f)
        print(f"  wrote {out_path} (status: {result.final.solver_status})")


if __name__ == "__main__":
    main()
