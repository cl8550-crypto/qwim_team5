"""AssetUniverse: market data layer for the Goal Parity model (Roadmap Sec 1).

Loads the team's cleaned ETF data from the repo-level ``cleaned_data/`` folder
(qwim_team5/cleaned_data — bonds, commodities, rates, sectors, volatility) and
computes the per-asset statistics the pipeline needs: annualized expected
return ``a``, volatility ``sigma``, skewness ``gamma`` (Roadmap Sec 2), plus a
return-on-capital ("income") fraction used by the Step 2 RC/RN split.

Prices are total-return adjusted (dividends reinvested via yfinance
auto_adjust), so Log_Return already includes income; the RC/RN split is a
configurable per-asset-class fraction (see INCOME_FRACTION_BY_CLASS).
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats as sp_stats


#: Trading days per year, used to annualize daily log-return statistics.
TRADING_DAYS: int = 252
TRADING_DAYS_PER_MONTH: float = TRADING_DAYS / 12

#: Golts & Jones (2023), "Data and Methodology": volatility is an
#: exponentially weighted average (420-month half-life) over a trailing
#: 120-month window; skewness uses returns Winsorized at +/-1 sigma over an
#: expanding window, with the resulting skewness estimate itself clipped to
#: +/-1. The paper's data is monthly (1970-2022); ours is daily and shorter
#: (ETF-inception-limited), so the window/half-life are converted to
#: daily-equivalent counts via TRADING_DAYS_PER_MONTH, and "expanding window"
#: collapses to "all available history" since this is a point-in-time
#: snapshot tool, not a walk-forward backtest.
EWMA_VOL_HALF_LIFE_DAYS: float = 420 * TRADING_DAYS_PER_MONTH
EWMA_VOL_WINDOW_DAYS: int = round(120 * TRADING_DAYS_PER_MONTH)
SKEW_WINSORIZE_SIGMA: float = 1.0
SKEW_CLIP: float = 1.0

#: Fraction of total return attributed to "return ON capital" (RN_t: coupons,
#: dividends, carry) per asset class — Step 2 RC/RN split (Roadmap Sec 3.2).
#: Configurable defaults; prices are total-return so income is embedded.
INCOME_FRACTION_BY_CLASS: dict[str, float] = {
    "sectors": 0.25,
    "bonds": 0.85,
    "commodities": 0.0,
    "rates": 0.95,
    "volatility": 0.0,
}

#: Files in cleaned_data that are context series, not investable assets.
NON_INVESTABLE_FILES: frozenset[str] = frozenset({"VIX_VIX_Index.csv"})

#: Ticker used as the risk-free / cash proxy (r_f, Roadmap Sec 2).
CASH_TICKER: str = "BIL"


@dataclass(frozen=True)
class AssetStats:
    """Per-asset inputs to the pipeline (Roadmap Sec 2 asset-specific params)."""

    ticker: str
    name: str
    asset_class: str
    a: float  # annualized expected (log) return
    sigma: float  # annualized volatility
    gamma: float  # skewness of daily log returns (Fisher-Pearson)
    income_fraction: float  # RN share of total return (Step 2 split)


def find_cleaned_data_dir(start: Path | None = None) -> Path:
    """Locate the repo-level cleaned_data folder.

    Honors the GOAL_PARITY_DATA_DIR env var, then walks up from this file
    (Viz-QWIM lives one level below the qwim_team5 repo root).
    """
    env_dir = os.environ.get("GOAL_PARITY_DATA_DIR")
    if env_dir:
        path = Path(env_dir)
        if path.is_dir():
            return path
    current = (start or Path(__file__)).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / "cleaned_data"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "cleaned_data folder not found; clone qwim_team5 so that Viz-QWIM sits "
        "inside it, or set GOAL_PARITY_DATA_DIR"
    )


def _ewma_annualized_volatility(returns: np.ndarray) -> float:
    """Annualized EWMA volatility over a trailing window (Appendix, "Data and
    Methodology"): most-recent `EWMA_VOL_WINDOW_DAYS` observations, weighted
    by exponential decay with half-life `EWMA_VOL_HALF_LIFE_DAYS` (recency
    tilt only, since the half-life is much longer than the window)."""
    windowed = returns[-EWMA_VOL_WINDOW_DAYS:]
    ages = np.arange(windowed.size - 1, -1, -1)  # 0 = most recent
    weights = 0.5 ** (ages / EWMA_VOL_HALF_LIFE_DAYS)
    weights /= weights.sum()
    weighted_mean = float(np.sum(weights * windowed))
    weighted_var = float(np.sum(weights * (windowed - weighted_mean) ** 2))
    return float(np.sqrt(weighted_var * TRADING_DAYS))


def _winsorized_expanding_skew(returns: np.ndarray) -> float:
    """Skewness on returns Winsorized at +/-1 sigma, over the full available
    (expanding-to-today) history, itself clipped to +/-1 (Appendix, "Data and
    Methodology")."""
    std = float(np.std(returns, ddof=1))
    if std == 0.0:
        return 0.0
    mean = float(np.mean(returns))
    winsorized = np.clip(returns, mean - SKEW_WINSORIZE_SIGMA * std, mean + SKEW_WINSORIZE_SIGMA * std)
    gamma = float(sp_stats.skew(winsorized, bias=False))
    return float(np.clip(gamma, -SKEW_CLIP, SKEW_CLIP))


def _parse_asset_file(path: Path) -> tuple[str, str, pl.DataFrame]:
    """Read one cleaned ETF CSV -> (ticker, human name, Date/Log_Return frame)."""
    ticker, _, rest = path.stem.partition("_")
    name = rest.replace("_", " ") or ticker
    frame = (
        pl.read_csv(path, try_parse_dates=True, infer_schema_length=10000)
        .select("Date", "Log_Return")
        .drop_nulls()
    )
    return ticker, name, frame


@dataclass
class AssetUniverse:
    """User-selectable multi-asset universe backed by cleaned_data (Roadmap Sec 1)."""

    data_dir: Path
    frames: dict[str, pl.DataFrame] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)
    classes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, data_dir: Path | None = None, tickers: list[str] | None = None) -> "AssetUniverse":
        """Load every investable cleaned ETF (optionally restricted to ``tickers``)."""
        root = data_dir or find_cleaned_data_dir()
        universe = cls(data_dir=root)
        for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            asset_class = class_dir.name
            if asset_class == "macro":
                continue
            for csv_path in sorted(class_dir.glob("*.csv")):
                if csv_path.name in NON_INVESTABLE_FILES:
                    continue
                ticker, name, frame = _parse_asset_file(csv_path)
                if tickers is not None and ticker not in tickers:
                    continue
                universe.frames[ticker] = frame
                universe.names[ticker] = name
                universe.classes[ticker] = asset_class
        if not universe.frames:
            raise ValueError(f"No assets loaded from {root} (tickers={tickers})")
        return universe

    @property
    def tickers(self) -> list[str]:
        return sorted(self.frames)

    def common_start_date(self):
        """Latest first-observation date across selected assets (Roadmap Sec 1)."""
        return max(frame["Date"].min() for frame in self.frames.values())

    def aligned_returns(self, tickers: list[str] | None = None) -> pl.DataFrame:
        """Daily log returns joined on Date from the common start date onward."""
        selected = tickers or self.tickers
        start = max(self.frames[t]["Date"].min() for t in selected)
        out: pl.DataFrame | None = None
        for ticker in selected:
            frame = (
                self.frames[ticker]
                .filter(pl.col("Date") >= start)
                .rename({"Log_Return": ticker})
            )
            out = frame if out is None else out.join(frame, on="Date", how="inner")
        assert out is not None
        return out.sort("Date")

    def stats(self, ticker: str) -> AssetStats:
        """Annualized a / sigma / gamma for one asset (Roadmap Sec 2, Sec 5).
        sigma and gamma follow the paper's Appendix ("Data and Methodology"):
        EWMA-weighted trailing-window volatility and Winsorized
        expanding-window skewness (see `_ewma_annualized_volatility` /
        `_winsorized_expanding_skew`)."""
        returns = self.frames[ticker]["Log_Return"].to_numpy()
        a = float(np.mean(returns) * TRADING_DAYS)
        sigma = _ewma_annualized_volatility(returns)
        gamma = _winsorized_expanding_skew(returns)
        asset_class = self.classes[ticker]
        return AssetStats(
            ticker=ticker,
            name=self.names[ticker],
            asset_class=asset_class,
            a=a,
            sigma=sigma,
            gamma=gamma,
            income_fraction=INCOME_FRACTION_BY_CLASS.get(asset_class, 0.25),
        )

    def all_stats(self, tickers: list[str] | None = None) -> list[AssetStats]:
        return [self.stats(t) for t in (tickers or self.tickers)]

    def risk_free_rate(self) -> float:
        """Annualized r_f from the 1-3M T-bill proxy (BIL), Roadmap Sec 5."""
        if CASH_TICKER not in self.frames:
            return 0.0
        returns = self.frames[CASH_TICKER]["Log_Return"].to_numpy()
        recent = returns[-TRADING_DAYS:] if returns.size > TRADING_DAYS else returns
        return float(np.mean(recent) * TRADING_DAYS)

    def cash_tickers(self) -> list[str]:
        """Cash-like assets (rates class) used for the Sec 3.6 cash floor."""
        return [t for t in self.tickers if self.classes[t] == "rates"]


@functools.lru_cache(maxsize=1)
def load_default_universe() -> AssetUniverse:
    """Cached full universe for dashboard use (loads 18 CSVs once per process)."""
    return AssetUniverse.load()
