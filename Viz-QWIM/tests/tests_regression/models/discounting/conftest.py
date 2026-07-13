"""Shared fixtures for discounting model regression tests.

The fixtures here are **canonical** — they reproduce the exact parameter
sets used to generate the Parquet baselines.  Do NOT change them without
regenerating the baselines first (set REGENERATE_BASELINES=1).

Usage
-----
    pytest tests/tests_regression/models/discounting/ -v -m regression
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl
import pytest

from src.models.discounting.model_discounting_constant import (
    Discounting_Model_Constant,
)
from src.utils.dates_times_utils.daycount import Daycount_Convention


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "models"
    / "discounting"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet baseline fixture.

    Parameters
    ----------
    filename : str
        Parquet file name (relative to ``BASELINES_DIR``).

    Returns
    -------
    pl.DataFrame
        The loaded DataFrame.
    """
    return pl.read_parquet(BASELINES_DIR / filename)


def save_baseline(filename: str, df: pl.DataFrame) -> None:
    """Save a DataFrame as a Parquet baseline fixture.

    Parameters
    ----------
    filename : str
        Target file name inside ``BASELINES_DIR``.
    df : pl.DataFrame
        The DataFrame to persist.
    """
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASELINES_DIR / filename)


# ---------------------------------------------------------------------------
# Fixed constants
# ---------------------------------------------------------------------------
DISCOUNT_RATE_LOW: float = 0.03
DISCOUNT_RATE_MID: float = 0.05
DISCOUNT_RATE_HIGH: float = 0.10

VALUATION_DATE_STR: str = "2024-01-01"

CASH_FLOWS: list[float] = [1_000.0, 2_000.0, 3_000.0, 5_000.0]
END_DATES_STR: list[str] = [
    "2025-01-01",
    "2026-01-01",
    "2027-01-01",
    "2029-01-01",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fixture_model_low() -> Discounting_Model_Constant:
    """Discounting model with 3 % rate."""
    return Discounting_Model_Constant(discount_rate=DISCOUNT_RATE_LOW)


@pytest.fixture(scope="session")
def fixture_model_mid() -> Discounting_Model_Constant:
    """Discounting model with 5 % rate."""
    return Discounting_Model_Constant(discount_rate=DISCOUNT_RATE_MID)


@pytest.fixture(scope="session")
def fixture_model_high() -> Discounting_Model_Constant:
    """Discounting model with 10 % rate."""
    return Discounting_Model_Constant(discount_rate=DISCOUNT_RATE_HIGH)
