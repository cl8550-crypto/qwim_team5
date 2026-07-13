"""Shared fixtures for yield_curve regression tests.

These fixtures reproduce the exact parameter sets used to generate the
Parquet baselines.  Do NOT change them without regenerating the baselines
(set REGENERATE_BASELINES=1).

Usage
-----
    pytest tests/tests_regression/models/yield_curve/ -v -m regression
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl
import pytest

from src.models.yield_curve.model_yield_curve_constant import Yield_Curve_Model_Constant
from src.models.yield_curve.model_yield_curve_standard import Yield_Curve_Model_Standard


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "models"
    / "yield_curve"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet regression baseline."""
    return pl.read_parquet(BASELINES_DIR / filename)


def save_baseline(df: pl.DataFrame, filename: str) -> None:
    """Save a DataFrame as a Parquet regression baseline."""
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASELINES_DIR / filename)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MARKET_DATA = pl.DataFrame(
    {
        "Maturity": [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
        "Yield": [0.020, 0.025, 0.030, 0.035, 0.040, 0.045, 0.048, 0.050],
    }
)

MATURITIES_PREDICT = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0]

FLAT_RATE = 0.03


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def constant_model_fitted() -> Yield_Curve_Model_Constant:
    """Flat yield-curve model fitted to MARKET_DATA."""
    m = Yield_Curve_Model_Constant(flat_rate=FLAT_RATE)
    m.fit(data = MARKET_DATA)
    return m


@pytest.fixture()
def constant_model_hardcoded() -> Yield_Curve_Model_Constant:
    """Flat yield-curve model with hard-coded rate (empty data fit)."""
    m = Yield_Curve_Model_Constant(flat_rate=FLAT_RATE)
    m.fit(data = pl.DataFrame())
    return m


@pytest.fixture()
def standard_model_fitted() -> Yield_Curve_Model_Standard:
    """Nelson-Siegel model fitted to MARKET_DATA."""
    m = Yield_Curve_Model_Standard()
    m.fit(data = MARKET_DATA)
    return m
