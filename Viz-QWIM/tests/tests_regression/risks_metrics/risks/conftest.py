"""Shared fixtures for risks_metrics.utils_risks regression tests.

The baselines here are canonical snapshots of the Risk_Measure_Type
category classmethods.  Do NOT change them without regenerating the
Parquet baseline files first.

Baseline Regeneration
---------------------
If an intentional change to the enum membership is made, re-run::

    python -c "
    import polars as pl; from pathlib import Path
    from src.risks_metrics.risks.utils_risks import Risk_Measure_Type
    bd = Path('tests/tests_regression/_baselines/risks_metrics/risks')
    for name, fn in {
        'variance_based': Risk_Measure_Type.get_variance_based_measures,
        'var_family': Risk_Measure_Type.get_var_family_measures,
        'drawdown': Risk_Measure_Type.get_drawdown_measures,
        'higher_moment': Risk_Measure_Type.get_higher_moment_measures,
        'coherent': Risk_Measure_Type.get_coherent_measures,
        'convex': Risk_Measure_Type.get_convex_measures,
    }.items():
        pl.DataFrame({'member_name': [m.name for m in fn()],
                      'member_value': [m.value for m in fn()]
                     }).write_parquet(bd / f'category_{name}.parquet')
    "

Then commit both the code changes and the updated Parquet files together.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "risks_metrics"
    / "risks"
)


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet baseline by filename."""
    path = BASELINES_DIR / filename
    assert path.exists(), f"Baseline not found: {path}"
    return pl.read_parquet(path)
