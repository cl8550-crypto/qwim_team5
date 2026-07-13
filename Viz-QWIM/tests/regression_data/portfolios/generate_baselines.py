"""Generate regression baseline data for portfolio tests.

Run this script once (or whenever intentional behaviour changes) to
produce the parquet files that the regression test suite compares against.

Usage
-----
From the project root::

    python tests/regression_data/portfolios/generate_baselines.py

The script writes the following files next to itself:

* ``baseline_portfolio_values.parquet``  — daily portfolio values (100 rows)
* ``baseline_benchmark_values.parquet``  — corresponding benchmark series
* ``baseline_weights.parquet``           — single–date equal–weight row
* ``baseline_metadata.json``             — scalar KPIs for numerical assertions
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap – allow running the script from the project root or from
# inside the tests/regression_data/portfolios/ directory.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Import after sys.path is fixed
from src.portfolios.portfolio_QWIM import Portfolio_QWIM  # noqa: E402
from src.portfolios import utils_portfolio  # noqa: E402

# Inject the real portfolio class (avoids relative-import fallback)
utils_portfolio.Portfolio_QWIM_class = Portfolio_QWIM

from src.portfolios.utils_portfolio import (  # noqa: E402
    calculate_portfolio_values,
    create_benchmark_portfolio_values,
)

import polars as pl  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixed synthetic dataset — intentionally deterministic
# ---------------------------------------------------------------------------
_COMPONENTS = ["VTI", "AGG", "VNQ", "VXUS", "BND"]
_N_ROWS = 100
_START_DATE = "2023-01-02"
_INITIAL_VALUE = 100.0
_WEIGHTS = {c: round(1.0 / len(_COMPONENTS), 10) for c in _COMPONENTS}


def _build_price_data() -> pl.DataFrame:
    """Return a deterministic 100-row ETF price DataFrame."""
    # Tiny pseudo-random walk seeded with fixed values so the baseline is
    # completely reproducible without touching random state in production code.
    import random  # noqa: PLC0415
    from datetime import date as _date, timedelta  # noqa: PLC0415

    rng = random.Random(42)
    start = _date(2023, 1, 2)
    date_list = [start + timedelta(days=i) for i in range(_N_ROWS)]

    prices: dict[str, list] = {"Date": date_list}
    for comp in _COMPONENTS:
        price = 100.0
        series: list[float] = []
        for _ in range(_N_ROWS):
            price *= 1.0 + rng.uniform(-0.01, 0.01)
            series.append(round(price, 6))
        prices[comp] = series

    return pl.DataFrame(prices).with_columns(pl.col("Date").cast(pl.Date))


def _build_weights_df() -> pl.DataFrame:
    """Return a single-date equal-weight DataFrame."""
    from datetime import date as _date  # noqa: PLC0415

    row: dict[str, object] = {"Date": [_date(2023, 1, 2)]}
    for comp in _COMPONENTS:
        row[comp] = [_WEIGHTS[comp]]
    return pl.DataFrame(row).with_columns(pl.col("Date").cast(pl.Date))


def generate() -> None:
    """Build and persist all baseline artefacts."""
    out_dir = _SCRIPT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Building synthetic price data (%d rows, %d components)…", _N_ROWS, len(_COMPONENTS))
    price_data = _build_price_data()

    weights_df = _build_weights_df()
    logger.info("Creating portfolio_QWIM object…")
    port = Portfolio_QWIM(
        name_portfolio="Regression Baseline Portfolio",
        portfolio_weights=weights_df,
    )

    logger.info("Calculating portfolio values…")
    portfolio_values = calculate_portfolio_values(
        portfolio_obj=port,
        price_data=price_data,
        initial_value=_INITIAL_VALUE,
    )

    logger.info("Creating benchmark values…")
    benchmark_values = create_benchmark_portfolio_values(portfolio_values = portfolio_values)

    # -----------------------------------------------------------------------
    # Persist artefacts
    # -----------------------------------------------------------------------
    pv_path = out_dir / "baseline_portfolio_values.parquet"
    bv_path = out_dir / "baseline_benchmark_values.parquet"
    w_path  = out_dir / "baseline_weights.parquet"
    md_path = out_dir / "baseline_metadata.json"

    portfolio_values.write_parquet(pv_path)
    logger.info("Written: %s", pv_path)

    benchmark_values.write_parquet(bv_path)
    logger.info("Written: %s", bv_path)

    weights_df.write_parquet(w_path)
    logger.info("Written: %s", w_path)

    # Scalar KPIs
    pv_col = "Portfolio_Value"
    first_val = float(portfolio_values[pv_col][0])
    last_val  = float(portfolio_values[pv_col][-1])
    min_val   = float(portfolio_values[pv_col].min())  # type: ignore[arg-type]
    max_val   = float(portfolio_values[pv_col].max())  # type: ignore[arg-type]
    n_rows    = len(portfolio_values)

    bv_col    = "Value"
    bench_first = float(benchmark_values[bv_col][0])
    bench_last  = float(benchmark_values[bv_col][-1])

    metadata = {
        "components": _COMPONENTS,
        "n_rows": n_rows,
        "initial_value": _INITIAL_VALUE,
        "portfolio_values": {
            "column": pv_col,
            "first": first_val,
            "last": last_val,
            "min": min_val,
            "max": max_val,
        },
        "benchmark_values": {
            "column": bv_col,
            "first": bench_first,
            "last": bench_last,
        },
        "weights": {c: _WEIGHTS[c] for c in _COMPONENTS},
    }

    with md_path.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    logger.info("Written: %s", md_path)

    logger.info("All baseline artefacts generated successfully.")


if __name__ == "__main__":
    generate()
