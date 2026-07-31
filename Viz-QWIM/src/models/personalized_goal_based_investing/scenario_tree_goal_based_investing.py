"""QWIM data adapter and historical-bootstrap scenario-tree generator."""

from __future__ import annotations

import os

from pathlib import Path

import numpy as np
import pandas as pd

from .model_goal_postponement import Scenario_Node, Scenario_Tree


_ETF_FOLDERS = ("sectors", "bonds", "commodities", "rates")


def find_cleaned_data_dir(start: Path | None = None) -> Path:
    """Locate QWIM's repository-level cleaned market-data directory."""
    environment_path = os.environ.get("QWIM_CLEANED_DATA_DIR")
    if environment_path and Path(environment_path).is_dir():
        return Path(environment_path)
    current = (start or Path(__file__)).resolve()
    for parent in (current, *current.parents):
        candidate = parent / "cleaned_data"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("cleaned_data folder not found; set QWIM_CLEANED_DATA_DIR to its location")


def load_monthly_market_panel(cleaned_data_root: str | Path, *, cash_ticker: str = "BIL") -> pd.DataFrame:
    """Load monthly simple returns, lagged CPI, and VIX shocks from cleaned data."""
    root = Path(cleaned_data_root)
    returns: dict[str, pd.Series] = {}
    for folder in _ETF_FOLDERS:
        for csv_file in (root / folder).glob("*.csv"):
            frame = pd.read_csv(csv_file, parse_dates=["Date"]).sort_values("Date").set_index("Date")
            ticker = csv_file.stem.split("_")[0]
            log_returns = frame["Log_Return"] if "Log_Return" in frame else np.log(frame["Close"] / frame["Close"].shift())
            returns[ticker] = log_returns.rename(ticker)
    if cash_ticker not in returns:
        raise KeyError(f"{cash_ticker!r} is unavailable; found {sorted(returns)}")
    panel = np.expm1(pd.concat(returns.values(), axis=1).sort_index().resample("ME").sum(min_count=1))
    vix = pd.read_csv(root / "volatility" / "VIX_VIX_Index.csv", parse_dates=["Date"]).set_index("Date")
    cpi = pd.read_csv(root / "macro" / "CPI_Monthly_CPIAUCSL.csv", parse_dates=["Date"]).set_index("Date")
    vix_shock = vix["Delta_Log_VIX"] if "Delta_Log_VIX" in vix else np.log(vix["Close"]).diff()
    inflation = cpi["YoY_Inflation"] if "YoY_Inflation" in cpi else np.log(cpi["CPIAUCSL"] / cpi["CPIAUCSL"].shift(12))
    panel["vix_shock"] = vix_shock.resample("ME").last()
    panel["yoy_inflation"] = inflation.resample("ME").last().shift(1)
    return panel.dropna().sort_index()


def historical_bootstrap_tree(panel: pd.DataFrame, *, assets: tuple[str, ...], return_periods: int, branches: int = 2, seed: int = 7) -> Scenario_Tree:
    """Sample whole monthly return vectors, preserving cross-asset dependence."""
    if return_periods < 1 or branches < 2:
        raise ValueError("return_periods must be >= 1 and branches must be >= 2")
    source = panel.loc[:, list(assets)].dropna()
    if len(source) < branches:
        raise ValueError("Not enough complete return vectors for unique siblings")
    rng = np.random.default_rng(seed)
    root = Scenario_Node("root", 1, None, 1.0, {})
    nodes, frontier = [root], [root]
    for stage in range(2, return_periods + 2):
        next_frontier: list[Scenario_Node] = []
        for parent in frontier:
            for branch, row_number in enumerate(rng.choice(len(source), size=branches, replace=False)):
                row = source.iloc[int(row_number)]
                child = Scenario_Node(f"n{stage}_{parent.identifier}_{branch}", stage, parent.identifier, parent.probability / branches, {asset: float(1 + row[asset]) for asset in assets})
                nodes.append(child)
                next_frontier.append(child)
        frontier = next_frontier
    tree = Scenario_Tree(tuple(nodes))
    tree.validate(assets=assets, branches=branches)
    return tree
