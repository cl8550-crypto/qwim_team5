"""Convex portfolio optimization wrappers using optimalportfolios.

Provides minimum variance, maximum quadratic utility, and budgeted risk
contribution (risk parity) portfolios.

Author: QWIM Team
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import polars as pl

from optimalportfolios import (
    Constraints,
    PortfolioObjective,
    cvx_quadratic_optimisation,
    opt_risk_budgeting,
)

from src.portfolios.portfolio_QWIM import Portfolio_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._optport_builders import _build_constraints, _extract_weights_to_portfolio_qwim
from ._optport_validators import (
    _compute_covar_and_means,
    _convert_polars_to_numpy_returns,
    _validate_risk_budgets,
    _validate_returns_data,
    _validate_scalar_positive_finite,
)


_logger = get_logger(name = __name__)


def calc_optimalportfolios_minimum_variance(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate minimum variance portfolio using optimalportfolios package.

    The minimum variance portfolio minimizes portfolio variance subject to
    the constraint that weights sum to one. This is the leftmost point on
    the efficient frontier.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
        Returns should be in decimal form (e.g. 0.01 for 1 % return).
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Min Variance Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative (no short selling).
        Default is ``True``.

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
        portfolio_name = "Min Variance Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    covar, _ = _compute_covar_and_means(returns_array = returns_array)
    constraints = _build_constraints(asset_names = asset_names, is_long_only=is_long_only)

    _logger.info(
        "Calculating minimum variance portfolio",
        extra={"num_assets": len(asset_names), "is_long_only": is_long_only},
    )

    try:
        weights = cvx_quadratic_optimisation(
            portfolio_objective=PortfolioObjective.MIN_VARIANCE,
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
        _logger.error("Minimum variance optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e


def calc_optimalportfolios_maximum_quadratic_utility(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, risk_aversion: float = 1.0, is_long_only: bool = True) -> Portfolio_QWIM:
    r"""Calculate maximum quadratic utility portfolio using optimalportfolios package.

    Maximizes expected utility with quadratic utility function, balancing expected
    return against portfolio variance scaled by risk aversion.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Max Quadratic Utility"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    risk_aversion : float, optional
        Risk aversion coefficient. Default is ``1.0``.
    is_long_only : bool, optional
        If ``True``, constrains weights to be non-negative. Default is ``True``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If ``returns_data`` is invalid, ``risk_aversion`` is not a positive
        finite numeric value, or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    risk_aversion = _validate_scalar_positive_finite(
        value_input = risk_aversion,
        field_name="risk_aversion",
    )

    if portfolio_name is None:
        portfolio_name = "Max Quadratic Utility Portfolio"

    asset_names = [col for col in returns_data.columns if col != "Date"]
    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    covar, means = _compute_covar_and_means(returns_array = returns_array)
    constraints = _build_constraints(asset_names = asset_names, is_long_only=is_long_only)

    _logger.info(
        "Calculating maximum quadratic utility portfolio",
        extra={
            "num_assets": len(asset_names),
            "risk_aversion": risk_aversion,
            "is_long_only": is_long_only,
        },
    )

    try:
        weights = cvx_quadratic_optimisation(
            portfolio_objective=PortfolioObjective.QUADRATIC_UTILITY,
            covar=covar,
            constraints=constraints,
            means=means,
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
        _logger.error("Maximum quadratic utility optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e


def calc_optimalportfolios_budgeted_risk_contribution(
    *, returns_data: pl.DataFrame, portfolio_name: str | None = None, optimization_date: str | datetime | None = None, risk_budgets: np.ndarray | dict[str, float] | None = None) -> Portfolio_QWIM:
    r"""Calculate budgeted risk contribution portfolio (risk parity) using optimalportfolios.

    Allocates portfolio risk according to specified risk budgets.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` column and asset return columns.
    portfolio_name : str | None, optional
        Name for the resulting portfolio. Defaults to ``"Risk Parity Portfolio"``.
    optimization_date : str | datetime | None, optional
        Date for the portfolio weights. Defaults to current date.
    risk_budgets : np.ndarray | dict[str, float] | None, optional
        Array-like or asset-keyed dict of non-negative risk budget allocations
        for each asset. Values must sum to 1.0. If ``None``, uses equal budgets
        (risk parity). Default is ``None``.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object containing optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If ``returns_data`` is invalid, budgets are inconsistent, or the solver fails.
    """
    is_valid, error_msg = _validate_returns_data(returns_data = returns_data)
    if not is_valid:
        _logger.error("Invalid returns_data: %s", error_msg)
        raise Exception_Validation_Input(error_msg)

    asset_names = [col for col in returns_data.columns if col != "Date"]
    n_assets = len(asset_names)
    risk_budgets = _validate_risk_budgets(risk_budgets_input = risk_budgets, asset_names = asset_names)

    if portfolio_name is None:
        portfolio_name = (
            "Risk Parity Portfolio" if risk_budgets is None else "Risk Budget Portfolio"
        )

    returns_array = _convert_polars_to_numpy_returns(returns_data = returns_data)
    covar, _ = _compute_covar_and_means(returns_array = returns_array)
    constraints = _build_constraints(asset_names = asset_names, is_long_only=True)

    _logger.info(
        "Calculating budgeted risk contribution portfolio",
        extra={
            "num_assets": n_assets,
            "equal_risk_contribution": risk_budgets is None,
        },
    )

    try:
        if risk_budgets is not None:
            weights = opt_risk_budgeting(
                covar=covar,
                constraints=constraints,
                risk_budget=risk_budgets,
            )
        else:
            weights = opt_risk_budgeting(
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
        _logger.error("Budgeted risk contribution optimization failed: %s", str(e))
        raise Exception_Validation_Input(f"Optimization failed: {e!s}") from e
