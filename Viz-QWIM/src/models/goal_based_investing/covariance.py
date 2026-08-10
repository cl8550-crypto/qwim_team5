"""Covariance estimation: EWMA + linear shrinkage.

Why not the plain sample covariance
------------------------------------
The sample covariance matrix is the maximum-likelihood estimator under iid
Gaussian returns, but it has two well-documented problems for portfolio
construction:

1. **Equal-weighting of stale data.** The plain sample covariance weights an
   observation from 20 years ago the same as last month, even though
   volatility and correlation regimes drift over time (volatility
   clustering; Engle 1982, Bollerslev 1986). An exponentially weighted
   moving average (EWMA) instead applies geometrically decaying weights, so
   recent data dominates the estimate -- the RiskMetrics (1996) approach,
   :math:`\\Sigma_t = \\lambda \\Sigma_{t-1} + (1-\\lambda) r_t r_t^\\top`.

2. **Estimation error in high dimensions.** With ``n`` assets, the sample
   covariance has ``n(n+1)/2`` free parameters estimated from a finite
   window, so extreme eigenvalues are systematically over/under-estimated
   (Marchenko-Pastur). Mean-variance optimizers then load up on the
   "luckiest" historical correlations, producing unstable, extreme weights
   (Michaud 1989, "The Markowitz Optimization Enigma"). Ledoit and Wolf
   (2004, "Honey, I Shrunk the Sample Covariance Matrix", J. Portfolio
   Management) show that shrinking the sample covariance toward a
   low-variance structured target (e.g. the constant-correlation matrix)
   strictly dominates the sample covariance in expected quadratic loss, with
   a shrinkage intensity that can be estimated analytically or via
   cross-validation.

We combine both fixes: compute an EWMA covariance to address (1), then apply
linear shrinkage of that EWMA matrix toward the constant-correlation target
to address (2). This is a standard combination in the risk-management
literature and remains a proper positive semi-definite covariance matrix
usable directly by the CVaR and variance constraints in
:mod:`stochastic_optimizer`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CovarianceConfig:
    """Configuration for the EWMA + shrinkage covariance estimator.

    Parameters
    ----------
    ewma_lambda : float
        Decay factor in ``(0, 1)``. RiskMetrics recommends 0.94 for daily
        data and 0.97 for monthly data. Higher = slower-moving, more stable
        estimate; lower = more reactive to recent volatility.
    shrinkage_intensity : float | None
        Shrinkage weight in ``[0, 1]`` applied to the constant-correlation
        target. If ``None`` (default), estimated analytically via the
        Ledoit-Wolf formula for the constant-correlation target.
    annualization_factor : int
        Periods per year, used only to annualize the final covariance for
        reporting/optimization inputs expressed in annual terms.
    """

    ewma_lambda: float = 0.97
    shrinkage_intensity: float | None = None
    annualization_factor: int = 12


def ewma_covariance(returns: pd.DataFrame, ewma_lambda: float = 0.97) -> np.ndarray:
    """Compute the RiskMetrics-style EWMA covariance matrix.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic returns, shape ``(n_obs, n_assets)``, chronologically
        ordered (oldest first).
    ewma_lambda : float
        Decay factor; see :class:`CovarianceConfig`.

    Returns
    -------
    np.ndarray
        Shape ``(n_assets, n_assets)``, per-period (not annualized) EWMA
        covariance as of the last observation.
    """
    values = returns.to_numpy()
    n_obs, n_assets = values.shape
    if n_obs < 2:
        raise ValueError("Need at least 2 observations for EWMA covariance.")

    demeaned = values - values.mean(axis=0)
    cov = np.outer(demeaned[0], demeaned[0])
    for t in range(1, n_obs):
        cov = ewma_lambda * cov + (1 - ewma_lambda) * np.outer(demeaned[t], demeaned[t])
    return cov


def constant_correlation_target(cov: np.ndarray) -> np.ndarray:
    """Build the Ledoit-Wolf constant-correlation shrinkage target.

    Every pairwise correlation is replaced by the average off-diagonal
    correlation, while each asset keeps its own variance -- this is the
    structured, low-parameter target recommended in Ledoit & Wolf (2004).

    Parameters
    ----------
    cov : np.ndarray
        Sample (or EWMA) covariance matrix, ``(n_assets, n_assets)``.

    Returns
    -------
    np.ndarray
        Constant-correlation covariance matrix, same shape.
    """
    std = np.sqrt(np.diag(cov))
    n = cov.shape[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = cov / np.outer(std, std)
    corr = np.nan_to_num(corr, nan=0.0)
    off_diag_mask = ~np.eye(n, dtype=bool)
    avg_corr = corr[off_diag_mask].mean() if n > 1 else 0.0

    target_corr = np.full((n, n), avg_corr)
    np.fill_diagonal(target_corr, 1.0)
    return target_corr * np.outer(std, std)


def ledoit_wolf_shrinkage_intensity(returns: pd.DataFrame, sample_cov: np.ndarray) -> float:
    """Analytic Ledoit-Wolf shrinkage intensity toward the constant-correlation target.

    Implements the consistent estimator of the optimal shrinkage constant
    from Ledoit & Wolf (2004), Section 3: intensity = (sum of asymptotic
    variances of sample covariance entries, penalized for the target's own
    covariance with the sample) / (squared Frobenius distance between sample
    and target), clipped to ``[0, 1]``.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic returns used to estimate the sample covariance (used here
        to compute the higher-moment terms needed for the optimal
        intensity).
    sample_cov : np.ndarray
        The covariance matrix being shrunk (may be EWMA rather than plain
        sample covariance; the formula is applied identically).

    Returns
    -------
    float
        Shrinkage intensity in ``[0, 1]``.
    """
    values = returns.to_numpy()
    n_obs, n_assets = values.shape
    demeaned = values - values.mean(axis=0)
    target = constant_correlation_target(sample_cov)

    # Pi: sum of asymptotic variances of each entry of the sample covariance.
    pi_mat = np.zeros((n_assets, n_assets))
    for t in range(n_obs):
        outer_t = np.outer(demeaned[t], demeaned[t])
        pi_mat += (outer_t - sample_cov) ** 2
    pi_mat /= n_obs
    pi_hat = pi_mat.sum()

    # Gamma: squared Frobenius norm of (target - sample), the misspecification term.
    gamma_hat = np.sum((target - sample_cov) ** 2)

    if gamma_hat <= 1e-16:
        return 0.0

    kappa_hat = pi_hat / gamma_hat
    intensity = max(0.0, min(1.0, kappa_hat / n_obs))
    return intensity


def ewma_shrinkage_covariance(
    returns: pd.DataFrame, config: CovarianceConfig | None = None
) -> tuple[np.ndarray, float]:
    """Full pipeline: EWMA covariance, shrunk toward the constant-correlation target.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic returns, ``(n_obs, n_assets)``.
    config : CovarianceConfig, optional
        Estimator configuration.

    Returns
    -------
    tuple[np.ndarray, float]
        ``(annualized_covariance, shrinkage_intensity_used)``.
    """
    cfg = config or CovarianceConfig()
    ewma_cov = ewma_covariance(returns, cfg.ewma_lambda)

    intensity = cfg.shrinkage_intensity
    if intensity is None:
        intensity = ledoit_wolf_shrinkage_intensity(returns, ewma_cov)

    target = constant_correlation_target(ewma_cov)
    shrunk = intensity * target + (1 - intensity) * ewma_cov
    shrunk = _nearest_psd(shrunk)

    annualized = shrunk * cfg.annualization_factor
    return annualized, intensity


def _nearest_psd(matrix: np.ndarray) -> np.ndarray:
    """Clip small negative eigenvalues from floating-point noise."""
    sym = (matrix + matrix.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals_clipped = np.clip(eigvals, 1e-12, None)
    return eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T
