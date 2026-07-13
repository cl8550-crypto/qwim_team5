"""ETF data retrieval module for fetching historical prices from Yahoo Finance.

This module retrieves historical price data for a selection of ETFs from Yahoo Finance
and saves it to a CSV file in a wide-table format.

Pandas is imported intentionally here -- this is an approved quarantine seam.
All downstream code receives ``polars.DataFrame``; ``pandas`` is used only to
interact with the ``yfinance`` API which returns pandas objects internally.
Do **not** propagate ``pd.DataFrame`` objects outside this module.
See ``[tool.pandas_quarantine].allowed_files`` in ``pyproject.toml``.

The script fetches daily closing prices for the following ETFs:

- IVV: iShares Core S&P 500 ETF
- IJH: iShares Core S&P Mid-Cap ETF
- IWM: iShares Russell 2000 ETF
- EFA: iShares MSCI EAFE ETF
- EEM: iShares MSCI Emerging Markets ETF
- AGG: iShares Core U.S. Aggregate Bond ETF
- SPTL: SPDR Portfolio Long Term Treasury ETF
- HYG: iShares iBoxx $ High Yield Corporate Bond ETF
- SPBO: SPDR Portfolio Corporate Bond ETF
- IYR: iShares U.S. Real Estate ETF
- DBC: Invesco DB Commodity Index Tracking Fund
- GLD: SPDR Gold Shares

Functions
---------
get_etf_data
    Retrieves historical ETF price data from Yahoo Finance.
main
    Main execution function that retrieves data and saves to CSV.

Examples
--------
To fetch ETF data and save to CSV:

.. code-block:: python

    from src.utils.data_utils.get_data_ETFs import main

    main()
"""

from __future__ import annotations

import time

from datetime import datetime
from pathlib import Path

# pandas-quarantine: allowed -- yfinance adapter seam; convert to polars immediately.
import pandas as pd
import polars as pl
import yfinance as yf

from cachetools import TTLCache

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


# Configure module logger
_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# In-memory TTL cache: keyed on (tickers_tuple, start_date, end_date).
# Preserve caller ticker order because the returned DataFrame column order is
# part of the public contract.
# ---------------------------------------------------------------------------
_ETF_CACHE: TTLCache = TTLCache(maxsize=32, ttl=3600)


def _resolve_project_root() -> Path:
    """Resolve the repository root for generated ETF data files.

    Prefer a directory that exposes repository markers so tests can monkeypatch
    ``__file__`` without having to mirror the full production path depth.

    Returns
    -------
    Path
        Absolute path to the project root directory.
    """
    resolved_file = Path(__file__).resolve()

    for candidate in resolved_file.parents:
        if (candidate / "pyproject.toml").is_file() or (candidate / "pytest.ini").is_file():
            return candidate

    # Fallback for shallow temp-path test fixtures.
    return resolved_file.parent.parent.parent


def _download_etf_pandas(
    *, tickers: list[str], start_date: str | None, end_date: str | None) -> pd.DataFrame:
    """Download raw price data from Yahoo Finance as a pandas DataFrame.

    This is the *only* function that is allowed to touch ``pandas`` in this
    module.  All callers must convert the result to polars before returning
    to external code.

    Parameters
    ----------
    tickers : list[str]
        ETF ticker symbols to download.
    start_date : str | None
        Start date in YYYY-MM-DD format, or None for all history.
    end_date : str | None
        End date in YYYY-MM-DD format, or None for today.

    Returns
    -------
    pd.DataFrame
        DataFrame with a DatetimeIndex and one column per ticker.
        Returns an empty DataFrame if all download attempts fail.
    """
    _logger.info(
        "Retrieving data for %d ETFs from %s to %s...",
        len(tickers),
        start_date,
        end_date or "present",
    )

    all_data = pd.DataFrame()

    # --- Bulk download attempt ---
    try:
        data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )

        if isinstance(data, pd.DataFrame) and not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                prices = pd.DataFrame()
                for ticker in tickers:
                    if ticker in data.columns.get_level_values(0):
                        try:
                            prices[ticker] = data[(ticker, "Close")]
                            _logger.debug("Bulk: extracted %s", ticker)
                        except (KeyError, ValueError) as exc:
                            _logger.warning("Could not extract Close for %s: %s", ticker, exc)
                if not prices.empty:
                    _logger.info(
                        "Bulk download OK: %d rows x %d tickers",
                        len(prices),
                        len(prices.columns),
                    )
                    return prices
            elif "Close" in data.columns:
                prices = data[["Close"]].copy()
                prices.columns = [tickers[0]]
                _logger.info("Single-ticker bulk OK: %d rows", len(prices))
                return prices
    except Exception as exc:
        _logger.warning("Bulk download failed (%s) -- falling back to individual", exc)

    # --- Individual-ticker fallback ---
    _logger.info("Downloading each ticker individually...")
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(
                start=start_date,
                end=end_date,
                auto_adjust=True,
            )
            if not history.empty and "Close" in history.columns:
                all_data[ticker] = history["Close"]
                _logger.debug("Individual: %s -- %d rows", ticker, len(history))
            else:
                _logger.warning("No data for %s", ticker)
            time.sleep(0.5)  # honour rate limits
        except Exception as exc:
            _logger.error("Error downloading %s: %s", ticker, exc)

    if not all_data.empty:
        _logger.info(
            "Individual downloads OK: %d rows x %d tickers",
            len(all_data),
            len(all_data.columns),
        )
    else:
        _logger.warning("No data retrieved from Yahoo Finance")

    return all_data


def get_etf_data(
    *, tickers: list[str], start_date: str | None = None, end_date: str | None = None) -> pl.DataFrame:
    """Retrieve historical ETF data from Yahoo Finance.

    Results are cached in memory for one hour (TTLCache, up to 32 entries)
    keyed on ``(tuple(tickers), start_date, end_date)``.

    The function downloads closing price data for the specified ETF tickers.
    It attempts a bulk download first and falls back to individual ticker
    downloads if needed.  All data is returned as a polars DataFrame -- pandas
    is used only at the yfinance adapter seam and converted immediately.

    Parameters
    ----------
    tickers : list[str]
        List of ETF ticker symbols to retrieve.
    start_date : str | None
        Start date in YYYY-MM-DD format; None for all available data.
    end_date : str | None
        End date in YYYY-MM-DD format; None for today.

    Returns
    -------
    pl.DataFrame
        DataFrame with a ``Date`` column (``pl.Date``) and one
        ``Float64`` column per ticker.  Returns an empty DataFrame if no
        data could be retrieved.

    Examples
    --------
    >>> tickers = ["SPY", "QQQ"]
    >>> df = get_etf_data(tickers=tickers, start_date="2023-01-01", end_date="2023-12-31")
    >>> df.shape[1]  # Date + 2 ticker columns
    3
    """
    cache_key = (tuple(tickers), start_date, end_date)
    if cache_key in _ETF_CACHE:
        _logger.debug("Cache hit for key %s", cache_key)
        return _ETF_CACHE[cache_key]  # type: ignore[return-value]

    pd_df = _download_etf_pandas(tickers = tickers, start_date = start_date, end_date = end_date)

    if pd_df.empty:
        result = pl.DataFrame(schema={"Date": pl.Date, **dict.fromkeys(tickers, pl.Float64)})
        _ETF_CACHE[cache_key] = result
        return result

    # ----- Quarantine boundary: pandas -> polars -----
    pd_df = pd_df.reset_index(drop=False)  # move DatetimeIndex -> column
    # Normalise the date column name
    date_col = pd_df.columns[0]
    pd_df = pd_df.rename(columns={date_col: "Date"})
    # Drop timezone info so polars can infer Date dtype
    if hasattr(pd_df["Date"], "dt") and pd_df["Date"].dt.tz is not None:
        pd_df["Date"] = pd_df["Date"].dt.tz_localize(None)

    result = pl.from_pandas(pd_df).with_columns(pl.col("Date").cast(pl.Date)).sort("Date")
    # Ensure Float64 for all ticker columns
    ticker_cols = [c for c in result.columns if c != "Date"]
    result = result.with_columns(
        [pl.col(c).cast(pl.Float64) for c in ticker_cols],
    )
    # ----- End quarantine boundary -----

    _ETF_CACHE[cache_key] = result
    return result


def main() -> None:
    """Retrieve ETF data and save to CSV.

    Retrieves historical price data for a set of ETFs, processes the data
    into a wide-table format, and saves it to a CSV file.

    Returns
    -------
    None

    Notes
    -----
    The output file is saved at ``PROJECT_ROOT/inputs/raw/data_ETFs.csv``.
    The function creates directories if they do not exist.
    Data spans from 2012-01-01 to the present; prices are adjusted for
    splits and dividends.

    Examples
    --------
    >>> from src.utils.data_utils.get_data_ETFs import main
    >>> main()  # Downloads data and saves to CSV
    """
    etf_tickers = [
        "IVV",  # iShares Core S&P 500 ETF
        "IJH",  # iShares Core S&P Mid-Cap ETF
        "IWM",  # iShares Russell 2000 ETF
        "EFA",  # iShares MSCI EAFE ETF
        "EEM",  # iShares MSCI Emerging Markets ETF
        "AGG",  # iShares Core U.S. Aggregate Bond ETF
        "SPTL",  # SPDR Portfolio Long Term Treasury ETF
        "HYG",  # iShares iBoxx $ High Yield Corporate Bond ETF
        "SPBO",  # SPDR Portfolio Corporate Bond ETF
        "IYR",  # iShares U.S. Real Estate ETF
        "DBC",  # Invesco DB Commodity Index Tracking Fund
        "GLD",  # SPDR Gold Shares
    ]
    start_date = "2012-01-01"

    try:
        project_dir = _resolve_project_root()
        raw_data_dir = project_dir / "inputs" / "raw"
        output_file = raw_data_dir / "data_ETFs.csv"

        _logger.info("Project directory: %s", project_dir.absolute())
        _logger.info("Output file:       %s", output_file.absolute())

        raw_data_dir.mkdir(parents=True, exist_ok=True)

        df = get_etf_data(tickers=etf_tickers, start_date=start_date)

        if df.is_empty():
            _logger.error("No data was retrieved from Yahoo Finance.")
            return

        # polars write_csv -- no pandas needed here
        df.write_csv(output_file)

        _logger.info(
            "Saved %d rows (%s to %s) -> %s",
            len(df),
            df["Date"].min(),
            df["Date"].max(),
            output_file.absolute(),
        )
        _logger.info("Columns: %s", ", ".join(df.columns))
        _logger.info("Download completed at: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    except Exception as exc:
        _logger.exception("Error occurred: %s", exc)


if __name__ == "__main__":
    main()
