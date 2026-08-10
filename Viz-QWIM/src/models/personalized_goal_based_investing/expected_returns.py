"""Expected return estimation: historical mean, CAPM, and Black-Litterman.

Choosing an expected-return model matters more than the covariance choice
for mean-variance-style optimizers, because portfolio weights are far more
sensitive to errors in the mean than to errors in the covariance (Chopra &
Ziemba 1993 estimate roughly an order of magnitude more sensitivity). This
module implements three estimators and documents the tradeoffs so a caller
can pick deliberately rather than by default.

Historical mean
    ``mu_hat_i = mean(r_i)`` over some lookback window.
    + Simple, transparent, no extra assumptions.
    - Extremely noisy: the standard error of a sample mean shrinks only at
      rate ``1/sqrt(T)``, so with e.g. 20 years of monthly data the
      confidence interval on annual expected equity return is often wider
      than +/- 5-8%. Historical means also "look backward" and over/under-
      weight whichever regime dominated the sample window.

CAPM (implied / equilibrium) returns
    ``mu_i = r_f + beta_i * (mu_m - r_f)``, or the reverse-optimization form
    ``Pi = delta * Sigma * w_mkt`` (Sharpe 1964; the reverse-optimization
    form is also the standard Black-Litterman prior, He & Litterman 1999).
    + Returns are internally consistent with market-cap weights and a single
      risk-aversion parameter -- by construction, the market-cap weighted
      portfolio is mean-variance optimal under these returns, which removes
      the estimation noise of using raw historical means directly in an
      optimizer.
    - Assumes markets are (roughly) priced efficiently and that the supplied
      benchmark weights are a sensible proxy for the "market" of the given
      asset universe; provides no channel for the investor's own views.

Black-Litterman
    Combines the CAPM equilibrium prior with investor views ``P, Q, Omega``
    via Bayesian updating (Black & Litterman 1992; He & Litterman 1999).
    + Addresses both problems above: the estimate is anchored at the
      low-error equilibrium prior, and shifts only as far as the investor's
      *confidently stated* views justify, avoiding the extreme, corner-
      solution portfolios that raw historical means produce in mean-
      variance optimization (Idzorek 2005 gives a practical view-confidence
      calibration).
    - Requires a market-cap benchmark and a risk-aversion parameter (or view
      confidences) that must be chosen or estimated; with zero views it
      reduces exactly to the CAPM prior above.

**Recommendation used by this project**: Black-Litterman when a benchmark
and (optionally) views are available; it dominates the historical mean on
theoretical and empirical grounds and is the academically strongest of the
three for feeding a stochastic optimizer. Historical mean is retained only
as a diagnostic baseline / fallback when no benchmark weights exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def historical_mean_returns(returns: pd.DataFrame, annualization_factor: int = 12) -> np.ndarray:
    """Simple annualized historical mean return per asset.

    Parameters
    ----------
    returns : pd.DataFrame
        Periodic returns, ``(n_obs, n_assets)``.
    annualization_factor : int
        Periods per year (12 = monthly, 4 = quarterly, 252 = daily).

    Returns
    -------
    np.ndarray
        Shape ``(n_assets,)``.
    """
    return returns.to_numpy().mean(axis=0) * annualization_factor


def capm_implied_returns(
    cov: np.ndarray,
    market_weights: np.ndarray,
    risk_free_rate: float,
    risk_aversion: float | None = None,
    market_risk_premium: float | None = None,
) -> np.ndarray:
    """Reverse-optimization (equilibrium) expected returns.

    Implements :math:`\\Pi = \\delta \\Sigma w_{mkt} + r_f`, the standard
    CAPM/He-Litterman equilibrium prior. Either supply ``risk_aversion``
    directly, or ``market_risk_premium`` (``E[r_m] - r_f``) from which
    ``delta = market_risk_premium / (w_mkt' Sigma w_mkt)`` is derived.

    Parameters
    ----------
    cov : np.ndarray
        Annualized covariance matrix, ``(n_assets, n_assets)``.
    market_weights : np.ndarray
        Benchmark / market-cap weights, ``(n_assets,)``, summing to 1.
    risk_free_rate : float
        Annualized risk-free rate.
    risk_aversion : float, optional
        Market risk-aversion coefficient ``delta``. Typical values 2.0-3.5.
    market_risk_premium : float, optional
        Alternative way to pin down ``delta``; used only if
        ``risk_aversion`` is not supplied.

    Returns
    -------
    np.ndarray
        Shape ``(n_assets,)`` annualized implied excess+risk-free returns.
    """
    w = np.asarray(market_weights, dtype=float)
    market_var = float(w @ cov @ w)
    if risk_aversion is None:
        if market_risk_premium is None:
            raise ValueError("Supply either risk_aversion or market_risk_premium.")
        if market_var <= 0:
            raise ValueError("Market variance must be positive to derive risk aversion.")
        risk_aversion = market_risk_premium / market_var
    pi = risk_aversion * (cov @ w) + risk_free_rate
    return pi


@dataclass
class BlackLittermanViews:
    """Investor views for the Black-Litterman posterior.

    Parameters
    ----------
    P : np.ndarray
        View "pick" matrix, shape ``(n_views, n_assets)``. Each row selects
        the assets involved in a relative or absolute view.
    Q : np.ndarray
        View outcomes, shape ``(n_views,)``, e.g. "asset A will outperform
        asset B by 2%/yr" -> row of ``P`` with +1/-1, ``Q`` entry 0.02.
    confidence : np.ndarray, optional
        Per-view confidence in ``(0, 1]``, used to scale the corresponding
        diagonal entry of ``Omega`` via Idzorek's (2005) method: higher
        confidence -> smaller view variance -> the posterior moves further
        toward that view. Defaults to a moderate 0.5 for all views if
        omitted, i.e. no black-box variance formula is silently assumed.
    """

    P: np.ndarray
    Q: np.ndarray
    confidence: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self) -> None:
        self.P = np.atleast_2d(np.asarray(self.P, dtype=float))
        self.Q = np.asarray(self.Q, dtype=float).reshape(-1)
        if self.P.shape[0] != self.Q.shape[0]:
            raise ValueError("P and Q must have the same number of views (rows).")
        if self.confidence.size == 0:
            self.confidence = np.full(self.Q.shape[0], 0.5)
        elif self.confidence.shape[0] != self.Q.shape[0]:
            raise ValueError("confidence must have one entry per view.")


def black_litterman_posterior(
    cov: np.ndarray,
    equilibrium_returns: np.ndarray,
    tau: float = 0.05,
    views: BlackLittermanViews | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Black-Litterman posterior mean and covariance.

    Implements the standard Bayesian update (Black & Litterman 1992):

    .. math::

        \\mu_{BL} = \\left[(\\tau\\Sigma)^{-1} + P^\\top \\Omega^{-1} P\\right]^{-1}
                    \\left[(\\tau\\Sigma)^{-1}\\Pi + P^\\top \\Omega^{-1} Q\\right]

    With no views, this returns ``(equilibrium_returns, tau * cov)`` exactly,
    matching the module's documented "reduces to CAPM prior" behavior.

    Parameters
    ----------
    cov : np.ndarray
        Annualized covariance, ``(n_assets, n_assets)``.
    equilibrium_returns : np.ndarray
        The prior mean ``Pi``, typically from :func:`capm_implied_returns`.
    tau : float
        Scalar controlling prior uncertainty, conventionally small (0.01-0.1;
        Black-Litterman 1992 use 0.05 as a default reflecting uncertainty in
        the mean relative to the return distribution itself).
    views : BlackLittermanViews, optional
        Investor views; omit for a pure equilibrium (CAPM) estimate.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(posterior_mean, posterior_covariance_of_the_mean)``. The
        posterior covariance of returns to feed a downstream optimizer is
        ``cov + posterior_covariance_of_the_mean`` (Black-Litterman 1992
        adds back the estimation-uncertainty term); we return the two parts
        separately so callers can choose.
    """
    n = cov.shape[0]
    prior_cov = tau * cov

    if views is None or views.Q.size == 0:
        return equilibrium_returns.copy(), prior_cov

    P, Q = views.P, views.Q
    # Idzorek (2005): view variance inversely related to stated confidence,
    # scaled by the view's own variance under the prior (P tau Sigma P').
    view_prior_var = np.diag(P @ prior_cov @ P.T)
    conf = np.clip(views.confidence, 1e-6, 1.0)
    omega_diag = view_prior_var * (1.0 - conf) / conf
    omega = np.diag(np.maximum(omega_diag, 1e-12))

    prior_precision = np.linalg.inv(prior_cov)
    omega_inv = np.linalg.inv(omega)

    posterior_precision = prior_precision + P.T @ omega_inv @ P
    posterior_cov = np.linalg.inv(posterior_precision)
    posterior_mean = posterior_cov @ (
        prior_precision @ equilibrium_returns + P.T @ omega_inv @ Q
    )
    return posterior_mean, posterior_cov


def estimate_expected_returns(
    method: str,
    returns: pd.DataFrame,
    cov: np.ndarray,
    annualization_factor: int = 12,
    risk_free_rate: float = 0.0,
    market_weights: np.ndarray | None = None,
    risk_aversion: float | None = None,
    market_risk_premium: float | None = None,
    bl_tau: float = 0.05,
    bl_views: BlackLittermanViews | None = None,
) -> np.ndarray:
    """Single dispatch entry point for the three supported estimators.

    Parameters
    ----------
    method : {"historical_mean", "capm", "black_litterman"}
        Estimator to use.
    returns : pd.DataFrame
        Periodic historical returns (used by ``"historical_mean"``).
    cov : np.ndarray
        Annualized covariance (used by ``"capm"`` and ``"black_litterman"``).
    annualization_factor : int
        Periods per year for ``"historical_mean"``.
    risk_free_rate, market_weights, risk_aversion, market_risk_premium
        See :func:`capm_implied_returns`.
    bl_tau, bl_views
        See :func:`black_litterman_posterior`.

    Returns
    -------
    np.ndarray
        Shape ``(n_assets,)`` annualized expected returns.
    """
    if method == "historical_mean":
        return historical_mean_returns(returns, annualization_factor)

    if market_weights is None:
        raise ValueError(f"method='{method}' requires market_weights (benchmark).")
    pi = capm_implied_returns(cov, market_weights, risk_free_rate, risk_aversion, market_risk_premium)

    if method == "capm":
        return pi
    if method == "black_litterman":
        mu, _ = black_litterman_posterior(cov, pi, tau=bl_tau, views=bl_views)
        return mu

    raise ValueError(f"Unknown method '{method}'. Use 'historical_mean', 'capm', or 'black_litterman'.")
