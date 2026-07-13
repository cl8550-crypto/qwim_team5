"""Conftest for insurance regression tests — provides baseline helpers.

Baselines stored at:
    tests/tests_regression/_baselines/products/insurance/
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest


BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "products"
    / "insurance"
)


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet baseline; skip test if it does not exist yet."""
    path = BASELINES_DIR / filename
    if not path.exists():
        pytest.skip(f"Baseline not found: {path}")
    return pl.read_parquet(path)


def save_baseline(filename: str, df: pl.DataFrame) -> None:
    """Persist a Parquet baseline, creating directories as needed."""
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASELINES_DIR / filename)
