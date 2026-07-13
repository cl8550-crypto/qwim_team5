"""Shared fixtures for portfolio_rebalancing regression tests.

These fixtures reproduce the exact parameter sets used to generate the
Parquet baselines.  Do NOT change them without regenerating the baselines
(set REGENERATE_BASELINES=1).

Usage
-----
    pytest tests/tests_regression/models/portfolio_rebalancing/ -v -m regression
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
    Portfolio_Rebalancing_Standard,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "models"
    / "portfolio_rebalancing"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet regression baseline.

    Parameters
    ----------
    filename : str
        Parquet file name relative to ``BASELINES_DIR``.

    Returns
    -------
    pl.DataFrame
        Baseline DataFrame.
    """
    return pl.read_parquet(BASELINES_DIR / filename)


def save_baseline(df: pl.DataFrame, filename: str) -> None:
    """Save a DataFrame as a Parquet regression baseline.

    Parameters
    ----------
    df : pl.DataFrame
        DataFrame to persist.
    filename : str
        Parquet file name relative to ``BASELINES_DIR``.
    """
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASELINES_DIR / filename)


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

#: Three-asset portfolio used for all regression fixtures
NAMES_3: list[str] = ["Equities", "Bonds", "Cash"]

#: Equal weights target
TARGET_EQUAL: np.ndarray = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

#: 60/30/10 target
TARGET_60_30_10: np.ndarray = np.array([0.60, 0.30, 0.10])

#: Drifted current weights for threshold scenario (Equities drifted +10%)
CURRENT_DRIFTED: np.ndarray = np.array([0.43, 0.30, 0.27])  # equal target, drifted

#: At-target current weights (no rebalance expected)
CURRENT_AT_TARGET: np.ndarray = TARGET_EQUAL.copy()

#: Portfolio value used in all regression scenarios
PORTFOLIO_VALUE: float = 1_000_000.0

#: Cost rate used in all regression scenarios (basis points)
COST_BPS: float = 10.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def strategy_equal() -> Portfolio_Rebalancing_Standard:
    """Threshold strategy configured with equal weights (1/3 each)."""
    s = Portfolio_Rebalancing_Standard(
        tolerance_abs=0.05,
        rebalancing_frequency_days=0,
        transaction_cost_bps=COST_BPS,
    )
    s.configure(target_weights = TARGET_EQUAL, names_assets = NAMES_3)
    return s


@pytest.fixture()
def strategy_60_30_10() -> Portfolio_Rebalancing_Standard:
    """Threshold strategy configured with 60/30/10 weights."""
    s = Portfolio_Rebalancing_Standard(
        tolerance_abs=0.05,
        rebalancing_frequency_days=0,
        transaction_cost_bps=COST_BPS,
    )
    s.configure(target_weights = TARGET_60_30_10, names_assets = NAMES_3)
    return s
