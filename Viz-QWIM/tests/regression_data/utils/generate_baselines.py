"""Generate Parquet baseline files for get_data_ETFs regression tests.

Run this script whenever an **intentional** change is made to the
get_data_ETFs module.  Commit the updated Parquet files together
with the corresponding code change so that regression tests continue to
pass.

Usage
-----
    python tests/regression_data/utils/generate_baselines.py

Baselines written
-----------------
* ``get_data_ETFs__sample_output.parquet``

Author
------
QWIM Team
"""

from __future__ import annotations

import sys

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import polars as pl


# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.data_utils.get_data_ETFs import get_etf_data  # noqa: E402


# ---------------------------------------------------------------------------
# Path where Parquet baselines are stored
# ---------------------------------------------------------------------------
BASELINES_DIR = Path(__file__).resolve().parent
BASELINES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Canonical parameters (MUST NOT change without regenerating)
# ---------------------------------------------------------------------------
DEFAULT_ETF_TICKERS: list[str] = [
    "IVV",
    "IJH",
    "IWM",
    "EFA",
    "EEM",
    "AGG",
    "SPTL",
    "HYG",
    "SPBO",
    "IYR",
    "DBC",
    "GLD",
]
START_DATE: str = "2024-01-02"
END_DATE: str = "2024-01-05"


# ---------------------------------------------------------------------------
# Mock data builder
# ---------------------------------------------------------------------------


def _make_bulk_download_frame(*, tickers: list[str]) -> pd.DataFrame:
    """Build a MultiIndex pandas DataFrame matching the yfinance bulk shape.

    Parameters
    ----------
    tickers : list[str]
        ETF ticker symbols to include as columns.

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with ``(Ticker, 'Close')`` columns and
        deterministic price values over three business days.
    """
    index = pd.date_range(START_DATE, periods=3, freq="B")
    data: dict[tuple[str, str], list[float]] = {}
    for idx_ticker, ticker in enumerate(tickers):
        data[(ticker, "Close")] = [
            100.0 + idx_ticker * 10 + idx_row for idx_row in range(3)
        ]
    frame = pd.DataFrame(data, index=index)
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)
    return frame


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate the get_data_ETFs sample output Parquet baseline.

    Mocks ``yfinance.download`` to produce deterministic price data,
    calls ``get_etf_data()``, and writes the resulting DataFrame to
    ``get_data_ETFs__sample_output.parquet`` in the same directory.
    """
    output_path = BASELINES_DIR / "get_data_ETFs__sample_output.parquet"

    with patch(
        "yfinance.download",
        return_value=_make_bulk_download_frame(tickers=DEFAULT_ETF_TICKERS),
    ):
        result = get_etf_data(
            tickers=DEFAULT_ETF_TICKERS,
            start_date=START_DATE,
            end_date=END_DATE,
        )

    result.write_parquet(output_path)
    print(f"Wrote baseline: {output_path}")


if __name__ == "__main__":
    main()

