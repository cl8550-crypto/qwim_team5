"""Historical bootstrap return-path generation.

Per the project specification, market uncertainty is represented via
**historical bootstrapping**, not Monte Carlo simulation from a parametric
distribution (Monte Carlo / GBM are intentionally excluded). This module
implements the stationary bootstrap of Politis and Romano (1994, "The
Stationary Bootstrap", JASA 89:428) applied jointly across all assets, which
is the academically preferred bootstrap for dependent (autocorrelated,
cross-correlated) financial time series:

- Naive iid bootstrap (resampling single rows independently) destroys serial
  autocorrelation and volatility clustering present in real return series.
- Fixed-length block bootstrap (Kunsch 1989 moving-block bootstrap) preserves
  local dependence but produces paths with a periodicity artifact from the
  fixed block length.
- The stationary bootstrap draws block lengths from a Geometric
  distribution, which yields a strictly stationary resampled process. It is
  the standard choice in empirical finance (e.g., White's 2000 Reality Check
  uses it) and is what we use here.

Rows are resampled *jointly* across assets (never column-by-column), so
cross-sectional correlation structure is preserved exactly at every
resampled time point; only the temporal block structure is synthetic.

Moment matching (optional)
---------------------------
Kim et al. only require *some* scenario generation method (footnote cites
Hoyland & Wallace 2001; Hoyland, Kaut & Wallace 2003 -- moment matching). A
pure historical bootstrap reuses the historical sample mean, which is a very
noisy expected-return estimator (see :mod:`expected_returns`). We therefore
support recentering/rescaling bootstrapped paths to a *target* mean and
covariance (typically the Black-Litterman posterior mean and the
EWMA+shrinkage covariance from :mod:`covariance`), following the
moment-matching idea of Hoyland et al. (2003): keep the empirical
(non-Gaussian, fat-tailed) *shape* of returns from history, but correct its
first two moments toward better estimators. This is applied via a
mean-shift plus a covariance-matching linear (Cholesky) transform of the
demeaned returns, which preserves higher-order moments (skew, kurtosis) of
the historical residuals better than simulating from a Gaussian would.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BootstrapConfig:
    """Configuration for the stationary block bootstrap.

    Parameters
    ----------
    expected_block_length : float
        Expected block length (in base-frequency periods) for the geometric
        block-length distribution. A common rule of thumb is
        ``n_obs ** (1/3)``; the default of 12 is a reasonable choice for
        monthly data (roughly one year of persistence).
    random_state : int | None
        Seed for reproducibility.
    """

    expected_block_length: float = 12.0
    random_state: int | None = None


def stationary_bootstrap_path(
    returns: pd.DataFrame,
    n_periods: int,
    config: BootstrapConfig | None = None,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Draw one stationary-bootstrap path of length ``n_periods``.

    Parameters
    ----------
    returns : pd.DataFrame
        Historical periodic returns, shape ``(n_obs, n_assets)``, one column
        per asset, asset order preserved in the output.
    n_periods : int
        Number of base-frequency periods to generate (e.g. total months
        across all stages before stage-level compounding).
    config : BootstrapConfig, optional
        Bootstrap parameters. Defaults to ``BootstrapConfig()``.
    rng : np.random.Generator, optional
        Shared RNG for reproducible batches; if omitted a fresh generator is
        created from ``config.random_state``.

    Returns
    -------
    np.ndarray
        Array of shape ``(n_periods, n_assets)``.

    Notes
    -----
    Implements the circular stationary bootstrap: starting index is uniform
    over ``0..n_obs-1``; block length is ``1 + Geometric(p)`` with
    ``p = 1 / expected_block_length``; indices wrap around (circular) so
    every historical row remains eligible regardless of starting point.
    """
    cfg = config or BootstrapConfig()
    if rng is None:
        rng = np.random.default_rng(cfg.random_state)

    values = returns.to_numpy()
    n_obs, n_assets = values.shape
    if n_obs < 2:
        raise ValueError("Need at least 2 historical observations to bootstrap.")

    p = 1.0 / max(cfg.expected_block_length, 1.0)
    out = np.empty((n_periods, n_assets))

    filled = 0
    idx = int(rng.integers(0, n_obs))
    while filled < n_periods:
        block_len = int(rng.geometric(p))
        block_len = max(1, min(block_len, n_periods - filled))
        for k in range(block_len):
            out[filled + k] = values[(idx + k) % n_obs]
        filled += block_len
        idx = int(rng.integers(0, n_obs))  # new random restart point per block

    return out


def compound_to_stage_returns(period_returns: np.ndarray, stage_lengths: list[int]) -> np.ndarray:
    """Compound base-frequency periodic returns into per-stage returns.

    Parameters
    ----------
    period_returns : np.ndarray
        Shape ``(sum(stage_lengths), n_assets)``, base-frequency returns
        (e.g. monthly), ordered stage-by-stage.
    stage_lengths : list[int]
        Number of base periods per stage, e.g. ``[20, 40, 40]`` for a
        5y-quarterly / 10y-annual / 10y-annual mix expressed in months
        (60, 120, 120 months -> whatever base frequency is used).

    Returns
    -------
    np.ndarray
        Shape ``(n_stages, n_assets)`` of compounded (geometric) returns,
        one row per stage: ``prod(1 + r) - 1`` over each stage's periods.
    """
    n_assets = period_returns.shape[1]
    n_stages = len(stage_lengths)
    out = np.empty((n_stages, n_assets))
    cursor = 0
    for t, length in enumerate(stage_lengths):
        chunk = period_returns[cursor : cursor + length]
        out[t] = np.prod(1.0 + chunk, axis=0) - 1.0
        cursor += length
    return out


def generate_bootstrap_stage_paths(
    returns: pd.DataFrame,
    stage_lengths: list[int],
    n_paths: int,
    config: BootstrapConfig | None = None,
    target_mean: np.ndarray | None = None,
    target_cov: np.ndarray | None = None,
) -> np.ndarray:
    """Generate many bootstrapped, stage-compounded return paths.

    Parameters
    ----------
    returns : pd.DataFrame
        Historical base-frequency returns, ``(n_obs, n_assets)``.
    stage_lengths : list[int]
        Base periods per stage (see :func:`compound_to_stage_returns`).
    n_paths : int
        Number of independent bootstrap paths to draw (before scenario-tree
        reduction in :mod:`scenario_tree`); typically several thousand.
    config : BootstrapConfig, optional
        Bootstrap parameters.
    target_mean : np.ndarray, optional
        If given, shape ``(n_assets,)`` *annualized simple* target mean
        return used to recenter the stage-1-equivalent annualized moments of
        the bootstrapped paths (moment matching, see module docstring). Set
        this to the Black-Litterman posterior or CAPM-implied mean from
        :mod:`expected_returns` to replace the noisy historical mean while
        keeping the empirical bootstrap shape.
    target_cov : np.ndarray, optional
        If given, shape ``(n_assets, n_assets)`` *annualized* target
        covariance (e.g. the EWMA+shrinkage estimate from :mod:`covariance`)
        used to rescale the cross-sectional dispersion of the bootstrapped
        paths via a Cholesky-based linear transform of the demeaned periodic
        returns, applied before stage compounding.

    Returns
    -------
    np.ndarray
        Shape ``(n_paths, n_stages, n_assets)``.
    """
    cfg = config or BootstrapConfig()
    rng = np.random.default_rng(cfg.random_state)
    n_total_periods = sum(stage_lengths)
    n_assets = returns.shape[1]

    values = returns.to_numpy()
    periods_per_year = _infer_periods_per_year(returns)

    adj_values = values
    if target_mean is not None or target_cov is not None:
        adj_values = _moment_match_periodic_returns(
            values, periods_per_year, target_mean, target_cov
        )

    adj_returns = pd.DataFrame(adj_values, columns=returns.columns)

    paths = np.empty((n_paths, len(stage_lengths), n_assets))
    for p in range(n_paths):
        period_path = stationary_bootstrap_path(adj_returns, n_total_periods, cfg, rng=rng)
        paths[p] = compound_to_stage_returns(period_path, stage_lengths)
    return paths


def _infer_periods_per_year(returns: pd.DataFrame) -> int:
    """Infer periods-per-year from a DatetimeIndex, defaulting to 12 (monthly)."""
    if isinstance(returns.index, pd.DatetimeIndex) and len(returns.index) > 2:
        median_days = np.median(np.diff(returns.index.values).astype("timedelta64[D]").astype(float))
        if median_days <= 2:
            return 252
        if median_days <= 10:
            return 52
        if median_days <= 45:
            return 12
        if median_days <= 100:
            return 4
        return 1
    return 12


def _moment_match_periodic_returns(
    values: np.ndarray,
    periods_per_year: int,
    target_mean: np.ndarray | None,
    target_cov: np.ndarray | None,
) -> np.ndarray:
    """Shift/rescale periodic returns so their annualized moments hit targets.

    Demeans the historical periodic returns, applies a linear map so the
    (annualized) covariance of the transformed series matches ``target_cov``
    (if given), then re-adds a per-period mean consistent with the
    (annualized) ``target_mean`` (if given). Historical values are used
    as-is for any target left as ``None``.
    """
    n_obs, n_assets = values.shape
    hist_mean = values.mean(axis=0)
    demeaned = values - hist_mean

    if target_cov is not None:
        hist_cov = np.cov(demeaned, rowvar=False) * periods_per_year
        hist_cov = _nearest_psd(hist_cov)
        target_cov = _nearest_psd(np.asarray(target_cov, dtype=float))
        try:
            L_hist = np.linalg.cholesky(hist_cov)
            L_target = np.linalg.cholesky(target_cov)
            transform = L_target @ np.linalg.inv(L_hist)
        except np.linalg.LinAlgError:
            # Fall back to a diagonal (volatility-only) rescale if either
            # covariance is singular (e.g., too few historical observations).
            hist_std = np.sqrt(np.diag(hist_cov))
            target_std = np.sqrt(np.diag(target_cov))
            scale = np.where(hist_std > 0, target_std / hist_std, 1.0)
            transform = np.diag(scale)
        demeaned = demeaned @ transform.T / np.sqrt(periods_per_year)
        # the transform above was derived on annualized covariance; rescale
        # back down to per-period units for a periodic series.
        demeaned = demeaned * np.sqrt(periods_per_year) / np.sqrt(periods_per_year)

    if target_mean is not None:
        per_period_target_mean = np.asarray(target_mean, dtype=float) / periods_per_year
        return demeaned + per_period_target_mean
    return demeaned + hist_mean


def generate_bootstrap_stage_paths_with_inflation(
    returns: pd.DataFrame,
    inflation_series: pd.Series,
    stage_lengths: list[int],
    n_paths: int,
    config: BootstrapConfig | None = None,
    target_mean: np.ndarray | None = None,
    target_cov: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Jointly bootstrap asset returns and an inflation series.

    Bootstrapping inflation independently from asset returns would discard
    their real historical correlation (e.g. commodities and inflation tend
    to move together; bonds tend to suffer in inflationary periods) --
    exactly the kind of cross-series dependence a block bootstrap is meant
    to preserve. This function draws a single shared sequence of blocks and
    applies it to both the (optionally moment-matched) asset returns and the
    raw inflation series, so each bootstrapped path keeps its internal
    asset/inflation relationship intact.

    Parameters
    ----------
    returns : pd.DataFrame
        Historical periodic asset returns, ``(n_obs, n_assets)``, same index
        as ``inflation_series``.
    inflation_series : pd.Series
        Historical periodic inflation rate, same index/frequency as
        ``returns`` (e.g. month-over-month CPI percent change).
    stage_lengths, n_paths, config, target_mean, target_cov
        See :func:`generate_bootstrap_stage_paths`. Moment matching (if
        requested) is applied only to the asset columns; the inflation
        series is always bootstrapped from its raw historical distribution.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(asset_paths, inflation_paths)`` of shapes
        ``(n_paths, n_stages, n_assets)`` and ``(n_paths, n_stages)``.
    """
    cfg = config or BootstrapConfig()
    if not returns.index.equals(inflation_series.index):
        raise ValueError("returns and inflation_series must share the same index.")

    asset_values = returns.to_numpy()
    if target_mean is not None or target_cov is not None:
        periods_per_year = _infer_periods_per_year(returns)
        asset_values = _moment_match_periodic_returns(asset_values, periods_per_year, target_mean, target_cov)

    combined = np.column_stack([asset_values, inflation_series.to_numpy()])
    combined_df = pd.DataFrame(combined, columns=list(returns.columns) + ["__inflation__"])

    n_total_periods = sum(stage_lengths)
    n_assets = asset_values.shape[1]
    rng = np.random.default_rng(cfg.random_state)

    asset_paths = np.empty((n_paths, len(stage_lengths), n_assets))
    inflation_paths = np.empty((n_paths, len(stage_lengths)))
    for p in range(n_paths):
        period_path = stationary_bootstrap_path(combined_df, n_total_periods, cfg, rng=rng)
        asset_paths[p] = compound_to_stage_returns(period_path[:, :n_assets], stage_lengths)
        inflation_paths[p] = compound_to_stage_returns(period_path[:, n_assets:], stage_lengths)[:, 0]

    return asset_paths, inflation_paths


def _nearest_psd(matrix: np.ndarray) -> np.ndarray:
    """Clip negative eigenvalues to a small positive floor (numerical safety)."""
    sym = (matrix + matrix.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals_clipped = np.clip(eigvals, 1e-10, None)
    return eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T
