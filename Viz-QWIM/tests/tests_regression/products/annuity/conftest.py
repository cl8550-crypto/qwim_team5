"""Shared fixtures for annuity regression tests.

Baselines capture snapshots of key calculation outputs for each annuity type
at fixed, deterministic parameters.  Tests compare current output against the
stored Parquet baselines to detect unintended behavioural changes.

Baseline Regeneration
---------------------
If intentional code changes alter numerical outputs, regenerate baselines with::

    REGENERATE_BASELINES=1 python -m pytest tests/tests_regression/products/annuity/ -q

Or run::

    python -c "
    import os; os.environ['REGENERATE_BASELINES'] = '1'
    import pytest; pytest.main(['tests/tests_regression/products/annuity/', '-q'])
    "

Then commit both the code changes and the updated Parquet files together.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[3]
    / "_baselines"
    / "products"
    / "annuity"
)


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet baseline by filename.

    Parameters
    ----------
    filename :
        Parquet filename (not full path) within BASELINES_DIR.

    Returns
    -------
    pl.DataFrame
    """
    path = BASELINES_DIR / filename
    if not path.exists():
        pytest.skip(f"Baseline not found: {path}. Run with REGENERATE_BASELINES=1 first.")
    return pl.read_parquet(path)


def save_baseline(filename: str, df: pl.DataFrame) -> None:
    """Persist a Parquet baseline.

    Parameters
    ----------
    filename :
        Parquet filename (not full path) within BASELINES_DIR.
    df :
        DataFrame to persist.
    """
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    path = BASELINES_DIR / filename
    df.write_parquet(path)
