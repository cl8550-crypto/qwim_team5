"""Hierarchical and advanced portfolio optimization wrappers using optimalportfolios.

Provides maximum diversification, maximum Sharpe ratio, maximum CARA
under Gaussian mixture, and tracking error minimization portfolios.

Author: QWIM Team
"""

from __future__ import annotations

import warnings
from datetime import datetime
from typing import cast

import cvxpy as cp
import numpy as np
import polars as pl

from cvxpy.constraints.constraint import Constraint

from optimalportfolios import (
    cvx_maximize_portfolio_sharpe,
    fit_gaussian_mixture,
    opt_maximise_diversification,
    opt_maximize_cara_mixture,
)

from src.portfolios.portfolio_QWIM import Portfolio_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._optport_builders import _build_constraints, _extract_weights_to_portfolio_qwim
from ._optport_validators import (
    _validate_boolean_flag,
    _compute_covar_and_means,
    _convert_polars_to_numpy_returns,
    _validate_positive_integer,
    _validate_returns_data,
    _validate_scalar_finite_numeric,
    _validate_scalar_positive_finite,
)


_logger = get_logger(name = __name__)


def calc_optimalportfolios_maximum_diversification(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate maximum diversification portfolio using optimalportfolios package.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Max Diversification Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative. Default is ``True``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If ``returns_data`` is invalid or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    if portfolio_name is None:
        portfolio_name = "Max Diversification Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    covar, _ = _compute_covar_and_means(returns_array = returns_array)
    constraints = _build_constraints(asset_names = asset_names, is_long_only=is_long_only)

    _logger.info(
        "Calculating maximum diversification portfolio",
        extra={"num_assets": len(asset_names), "is_long_only": is_long_only},
    )

    try:
        weights = opt_maximise_diversification(
            covar=covar,
            constraints=constraints,
        )

        _logger.info(
            "Optimization complete",
            extra={
                "portfolio_name": portfolio_name,
                "weights_sum": float(np.sum(weights)),
            },
        )

        return _extract_weights_to_portfolio_qwim(
            weights=weights,
            asset_names=asset_names,
            portfolio_name=portfolio_name,
            optimization_date=optimization_date,
        )

    except Exception as e:
        _logger.error("Maximum diversification optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e


def calc_optimalportfolios_maximum_sharpe_ratio(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, risk_free_rate: float = 0.0, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate maximum Sharpe ratio portfolio using optimalportfolios package.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Max Sharpe Ratio Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    risk_free_rate : float, optional
        Risk-free rate for calculating excess returns. Default is ``0.0``.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative. Default is ``True``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If ``returns_data`` is invalid, ``risk_free_rate`` is not a finite
        numeric value, or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    risk_free_rate = _validate_scalar_finite_numeric(
        value_input = risk_free_rate,
        field_name="risk_free_rate",
    )

    if portfolio_name is None:
        portfolio_name = "Max Sharpe Ratio Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    covar, means = _compute_covar_and_means(returns_array = returns_array)
    excess_means = means - risk_free_rate
    constraints = _build_constraints(asset_names = asset_names, is_long_only=is_long_only)

    _logger.info(
        "Calculating maximum Sharpe ratio portfolio",
        extra={
            "num_assets": len(asset_names),
            "risk_free_rate": risk_free_rate,
            "is_long_only": is_long_only,
        },
    )

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Solution may be inaccurate",
                category=UserWarning,
                module="optimalportfolios",
            )
            weights = cvx_maximize_portfolio_sharpe(
                covar=covar,
                means=excess_means,
                constraints=constraints,
            )

        _logger.info(
            "Optimization complete",
            extra={
                "portfolio_name": portfolio_name,
                "weights_sum": float(np.sum(weights)),
            },
        )

        return _extract_weights_to_portfolio_qwim(
            weights=weights,
            asset_names=asset_names,
            portfolio_name=portfolio_name,
            optimization_date=optimization_date,
        )

    except Exception as e:
        _logger.error("Maximum Sharpe ratio optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e


def calc_optimalportfolios_maximum_cara_gaussian_mixture(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, risk_aversion: float = 1.0, n_components: int = 2, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate maximum CARA utility portfolio under Gaussian mixture model.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Max CARA GMM Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    risk_aversion : float, optional
        Risk aversion coefficient. Default is ``1.0``.
    n_components : int, optional
        Number of Gaussian mixture components. Default is ``2``.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative. Default is ``True``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If inputs are invalid, including a non-positive or non-finite
        ``risk_aversion`` value, a non-positive-integer ``n_components``
        value, or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    risk_aversion = _validate_scalar_positive_finite(
        value_input = risk_aversion,
        field_name="risk_aversion",
    )

    n_components = _validate_positive_integer(
        value_input = n_components,
        field_name="n_components",
    )

    if portfolio_name is None:
        portfolio_name = "Max CARA GMM Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    constraints = _build_constraints(asset_names = asset_names, is_long_only=is_long_only)

    _logger.info(
        "Calculating maximum CARA utility (GMM) portfolio",
        extra={
            "num_assets": len(asset_names),
            "risk_aversion": risk_aversion,
            "n_components": n_components,
            "is_long_only": is_long_only,
        },
    )

    try:
        gmm_params = fit_gaussian_mixture(x=returns_array, n_components=n_components)

        weights = opt_maximize_cara_mixture(
            means=gmm_params.means,
            covars=gmm_params.covars,
            probs=gmm_params.probs,
            constraints=constraints,
            carra=risk_aversion,
        )

        _logger.info(
            "Optimization complete",
            extra={
                "portfolio_name": portfolio_name,
                "weights_sum": float(np.sum(weights)),
            },
        )

        return _extract_weights_to_portfolio_qwim(
            weights=weights,
            asset_names=asset_names,
            portfolio_name=portfolio_name,
            optimization_date=optimization_date,
        )

    except Exception as e:
        _logger.error("Maximum CARA GMM optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e


def calc_optimalportfolios_tracking_error_minimization(
    *, returns_data: pl.DataFrame, benchmark_returns: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate tracking error minimization portfolio using optimalportfolios package.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    benchmark_returns : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and a single benchmark return column.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Tracking Error Min Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative. Default is ``True``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If inputs are invalid, including a non-boolean ``is_long_only``
        value, non-matching benchmark ``Date`` values, or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    is_long_only = _validate_boolean_flag(
        value_input = is_long_only,
        field_name="is_long_only",
    )

    is_valid_bench, error_msg_bench = _validate_returns_data(returns_data = benchmark_returns)
    if not is_valid_bench:
        _logger.error("Invalid benchmark_returns: %s", error_msg_bench)
        raise Exception_Validation_Input(f"Invalid benchmark_returns: {error_msg_bench}")

    benchmark_columns = [col for col in benchmark_returns.columns if col != "Date"]
    if len(benchmark_columns) != 1:
        msg = (
            f"benchmark_returns must have exactly one asset column,"
            f" got {len(benchmark_columns)}"
        )
        _logger.error(msg)
        raise Exception_Validation_Input(msg)

    if len(returns_data) != len(benchmark_returns):
        msg = (
            f"returns_data ({len(returns_data)} rows) and benchmark_returns "
            f"({len(benchmark_returns)} rows) must have the same length"
        )
        _logger.error(msg)
        raise Exception_Validation_Input(msg)

    returns_data = returns_data.sort("Date")
    benchmark_returns = benchmark_returns.sort("Date")
    if not returns_data.get_column("Date").equals(benchmark_returns.get_column("Date")):
        msg = "returns_data and benchmark_returns must contain matching Date values"
        _logger.error(msg)
        raise Exception_Validation_Input(msg)

    if portfolio_name is None:
        portfolio_name = "Tracking Error Min Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    n_assets = len(asset_names)
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    benchmark_array = benchmark_returns.select(benchmark_columns[0]).to_numpy().flatten()

    _logger.info(
        "Calculating tracking error minimization portfolio (cvxpy)",
        extra={
            "num_assets": n_assets,
            "benchmark_col": benchmark_columns[0],
            "is_long_only": is_long_only,
        },
    )

    try:
        covar, _ = _compute_covar_and_means(returns_array = returns_array)
        cov_combined = np.cov(returns_array.T, benchmark_array)
        cov_with_benchmark = cov_combined[:n_assets, -1]

        w_var = cp.Variable(n_assets)
        objective = cp.Minimize(
            cp.quad_form(w_var, covar) - 2.0 * cov_with_benchmark @ w_var
        )
        cvx_constraints: list[Constraint] = [
            cast(Constraint, cp.sum(w_var) == 1.0),
        ]
        if is_long_only:
            cvx_constraints.append(cast(Constraint, w_var >= 0))

        prob = cp.Problem(objective, cvx_constraints)
        prob.solve(solver=cp.ECOS)

        if prob.status not in ("optimal", "optimal_inaccurate"):
            raise Exception_Calculation(
                f"cvxpy solver failed with status: {prob.status}"
            )

        weights = np.asarray(w_var.value, dtype=np.float64)

        _logger.info(
            "Optimization complete",
            extra={
                "portfolio_name": portfolio_name,
                "weights_sum": float(np.sum(weights)),
            },
        )

        return _extract_weights_to_portfolio_qwim(
            weights=weights,
            asset_names=asset_names,
            portfolio_name=portfolio_name,
            optimization_date=optimization_date,
        )

    except Exception as e:
        _logger.error("Tracking error minimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e
