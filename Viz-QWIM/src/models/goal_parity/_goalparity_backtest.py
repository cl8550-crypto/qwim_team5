"""Walk-forward historical backtest for the Goal Parity model.

Rolls a train/test/step window over the aligned daily returns: at each
rebalance date, every model input (expected returns, EWMA vols, Winsorized
skew, the gamma0 calibration, the Steps 2-4 goal decomposition) is
re-estimated from the training window ONLY — no look-ahead — then the Step 5
strategic weights are held over the next step while realized returns
accumulate. A 60/40-style benchmark (equal-weight sectors / equal-weight
bonds) is tracked over the same span for comparison.

Window semantics: the *step* drives the contiguous out-of-sample equity
curve (each fold's weights are held for one step, then re-estimated); the
*test window* is a per-fold reporting horizon (fold returns are measured
over it and may overlap the next fold when test > step).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from src.models.goal_parity._goalparity_calibration import CalibrationSuite
from src.models.goal_parity._goalparity_cashflow import CashFlowEstimator
from src.models.goal_parity._goalparity_data import (
    INCOME_FRACTION_BY_CLASS,
    TRADING_DAYS,
    AssetStats,
    AssetUniverse,
    _ewma_annualized_volatility,
    _winsorized_expanding_skew,
)
from src.models.goal_parity._goalparity_decomposition import GoalDecomposer
from src.models.goal_parity._goalparity_optimization import StrategicOptimizer
from src.models.goal_parity._goalparity_profiling import InvestorProfile
from src.models.goal_parity._goalparity_volatility import VolatilityAdjuster


#: Trading days per calendar month, for month-denominated windows.
TRADING_DAYS_PER_MONTH: int = 21

#: Below this many training days, skew / first-passage estimates get noisy
#: enough that results should carry a warning (~2.5 years).
MIN_COMFORTABLE_TRAIN_DAYS: int = round(2.5 * TRADING_DAYS)

#: Benchmark sleeve weights: 60% equities (sectors) / 40% bonds.
BENCHMARK_EQUITY_SHARE: float = 0.60


@dataclass(frozen=True)
class BacktestFold:
    """One walk-forward fold: trained on [train_start, train_end), held/tested after."""

    train_start: date
    train_end: date
    test_start: date
    test_end: date
    weights: dict[str, float]
    solver_success: bool
    portfolio_test_return: float  # simple return over the test window
    benchmark_test_return: float


@dataclass(frozen=True)
class BacktestResult:
    """Contiguous out-of-sample equity curves plus per-fold detail."""

    dates: list[date]  # out-of-sample dates (one per NAV point)
    portfolio_nav: np.ndarray  # starts at 1.0
    benchmark_nav: np.ndarray
    folds: list[BacktestFold]
    summary: dict[str, dict[str, float]]  # {"Goal Parity": {...}, "Benchmark": {...}}
    benchmark_description: str
    warnings: list[str]


def _simple_daily_returns(log_returns: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Daily portfolio log returns for fixed weights rebalanced daily."""
    growth = np.expm1(log_returns) @ weights  # simple portfolio return per day
    return np.log1p(growth)


def _performance_summary(daily_log: np.ndarray, nav: np.ndarray) -> dict[str, float]:
    """Annualized performance stats over the out-of-sample span (rf = 0)."""
    ann_log = float(np.mean(daily_log) * TRADING_DAYS)
    ann_vol = float(np.std(daily_log, ddof=1) * np.sqrt(TRADING_DAYS))
    running_max = np.maximum.accumulate(nav)
    max_drawdown = float(np.min(nav / running_max) - 1.0)
    return {
        "total_return": float(nav[-1] / nav[0] - 1.0),
        "annualized_return": float(np.expm1(ann_log)),
        "annualized_volatility": ann_vol,
        "sharpe_ratio": ann_log / ann_vol if ann_vol > 0 else 0.0,
        "max_drawdown": max_drawdown,
    }


def _benchmark_weights(
    universe: AssetUniverse, tickers: list[str]
) -> tuple[np.ndarray, str]:
    """60/40 equal-weight sectors/bonds over the selected tickers (bonds
    falls back to the rates class if no bond ETF is selected)."""
    classes = [universe.classes[t] for t in tickers]
    equity_idx = [i for i, c in enumerate(classes) if c == "sectors"]
    bond_idx = [i for i, c in enumerate(classes) if c == "bonds"]
    if not bond_idx:
        bond_idx = [i for i, c in enumerate(classes) if c == "rates"]
    weights = np.zeros(len(tickers))
    if equity_idx and bond_idx:
        weights[equity_idx] = BENCHMARK_EQUITY_SHARE / len(equity_idx)
        weights[bond_idx] = (1.0 - BENCHMARK_EQUITY_SHARE) / len(bond_idx)
        description = "60% sectors / 40% bonds, equal-weight within each sleeve"
    elif equity_idx or bond_idx:
        idx = equity_idx or bond_idx
        weights[idx] = 1.0 / len(idx)
        description = "equal-weight (only one benchmark sleeve available)"
    else:
        weights[:] = 1.0 / len(tickers)
        description = "equal-weight all selected assets (no sectors/bonds selected)"
    return weights, description


def _point_in_time_stats(
    universe: AssetUniverse, ticker: str, train_returns: np.ndarray
) -> AssetStats:
    """AssetStats estimated from the training window only (no look-ahead),
    using the same estimators as the live pipeline."""
    asset_class = universe.classes[ticker]
    return AssetStats(
        ticker=ticker,
        name=universe.names[ticker],
        asset_class=asset_class,
        a=float(np.mean(train_returns) * TRADING_DAYS),
        sigma=_ewma_annualized_volatility(train_returns),
        gamma=_winsorized_expanding_skew(train_returns),
        income_fraction=INCOME_FRACTION_BY_CLASS.get(asset_class, 0.25),
    )


def _solve_fold_weights(
    universe: AssetUniverse,
    profile: InvestorProfile,
    tickers: list[str],
    train_matrix: np.ndarray,  # (train_days x n_assets) log returns
    mode: str,
    tilt_goal: str,
    tilt_strength: float,
):
    """Steps 2-5 on training data only: per-fold gamma0 fit, goal
    decomposition, and strategic optimization."""
    gamma0 = CalibrationSuite.fit_gamma0_for_universe(
        {t: train_matrix[:, i] for i, t in enumerate(tickers)}
    )
    cashflow = CashFlowEstimator()
    volatility = VolatilityAdjuster(gamma0=gamma0)
    decomposer = GoalDecomposer()

    shares_by_ticker: dict[str, dict[str, float]] = {}
    exp_returns: list[float] = []
    for i, ticker in enumerate(tickers):
        stats = _point_in_time_stats(universe, ticker, train_matrix[:, i])
        cf_profile = cashflow.profile(stats, profile.T)
        adjusted = volatility.adjust(stats)
        goal_shares = decomposer.decompose(
            ticker,
            cf_profile.epv,
            adjusted.sigma_d,
            adjusted.sigma_l,
            profile.T,
            profile.tau_years,
            profile.b,
        )
        shares_by_ticker[ticker] = goal_shares.shares
        exp_returns.append(stats.a)

    optimizer = StrategicOptimizer()
    if mode == "balanced":
        return optimizer.solve_balanced(tickers, np.array(exp_returns), shares_by_ticker)
    return optimizer.solve_tilted(
        tickers, np.array(exp_returns), shares_by_ticker, tilt_goal, tilt_strength=tilt_strength
    )


def run_walk_forward(
    universe: AssetUniverse,
    profile: InvestorProfile,
    tickers: list[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    train_years: float = 3.0,
    test_months: int = 6,
    step_months: int | None = None,
    mode: str = "balanced",
    tilt_goal: str = "Growth",
    tilt_strength: float = 1.0,
) -> BacktestResult:
    """Walk-forward backtest over [start_date, end_date].

    ``step_months`` defaults to the profile's rebalancing frequency tau so the
    walk-forward steps at the same cadence the client's portfolio would
    actually be reviewed.
    """
    if train_years < 1.0:
        raise ValueError("Training window must be at least 1 year")
    if test_months < 1:
        raise ValueError("Test window must be at least 1 month")
    step = int(step_months) if step_months else profile.tau_months
    if step < 1:
        raise ValueError("Step size must be at least 1 month")

    selected = [t for t in (tickers or universe.tickers) if t in universe.frames]
    if not selected:
        selected = universe.tickers
    aligned = universe.aligned_returns(selected)
    if start_date is not None:
        aligned = aligned.filter(aligned["Date"] >= start_date)
    if end_date is not None:
        aligned = aligned.filter(aligned["Date"] <= end_date)

    dates_all = aligned["Date"].to_list()
    returns_all = aligned.select(selected).to_numpy()
    n = len(dates_all)

    train_days = round(train_years * TRADING_DAYS)
    step_days = step * TRADING_DAYS_PER_MONTH
    test_days = test_months * TRADING_DAYS_PER_MONTH
    if n < train_days + step_days:
        raise ValueError(
            f"Not enough data for one fold: need {train_days + step_days} trading days "
            f"(train {train_years:g}y + step {step}m) but the selected date range has {n}."
        )

    warnings: list[str] = []
    if train_days < MIN_COMFORTABLE_TRAIN_DAYS:
        warnings.append(
            f"Training window of {train_years:g} years is short — skew and "
            "first-passage estimates get noisy below ~2.5 years, so read the "
            "results as indicative only."
        )

    bench_weights, bench_desc = _benchmark_weights(universe, selected)

    folds: list[BacktestFold] = []
    oos_daily_log: list[np.ndarray] = []
    bench_daily_log: list[np.ndarray] = []
    for i in range(train_days, n, step_days):
        train_matrix = returns_all[max(0, i - train_days) : i]
        result = _solve_fold_weights(
            universe, profile, selected, train_matrix, mode, tilt_goal, tilt_strength
        )
        if not result.success:
            warnings.append(
                f"Fold starting {dates_all[i]} did not fully converge; its weights "
                "are a best effort."
            )

        hold_end = min(i + step_days, n)
        hold_returns = returns_all[i:hold_end]
        oos_daily_log.append(_simple_daily_returns(hold_returns, result.weights))
        bench_daily_log.append(_simple_daily_returns(hold_returns, bench_weights))

        test_end_idx = min(i + test_days, n)
        test_returns = returns_all[i:test_end_idx]
        gp_test = float(np.expm1(np.sum(_simple_daily_returns(test_returns, result.weights))))
        bench_test = float(np.expm1(np.sum(_simple_daily_returns(test_returns, bench_weights))))
        folds.append(
            BacktestFold(
                train_start=dates_all[max(0, i - train_days)],
                train_end=dates_all[i - 1],
                test_start=dates_all[i],
                test_end=dates_all[test_end_idx - 1],
                weights={t: float(w) for t, w in zip(selected, result.weights)},
                solver_success=bool(result.success),
                portfolio_test_return=gp_test,
                benchmark_test_return=bench_test,
            )
        )

    gp_log = np.concatenate(oos_daily_log)
    bench_log = np.concatenate(bench_daily_log)
    gp_nav = np.exp(np.concatenate([[0.0], np.cumsum(gp_log)]))[1:]
    bench_nav = np.exp(np.concatenate([[0.0], np.cumsum(bench_log)]))[1:]
    oos_dates = dates_all[train_days : train_days + len(gp_log)]

    return BacktestResult(
        dates=oos_dates,
        portfolio_nav=gp_nav,
        benchmark_nav=bench_nav,
        folds=folds,
        summary={
            "Goal Parity": _performance_summary(gp_log, gp_nav),
            "Benchmark": _performance_summary(bench_log, bench_nav),
        },
        benchmark_description=bench_desc,
        warnings=warnings,
    )
