"""Constraint builder and portfolio weight extractor for the optimalportfolios wrapper.

These helpers depend on ``optimalportfolios.Constraints`` and
``Portfolio_QWIM`` and therefore cannot be tested without those packages.

Author: QWIM Team
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypedDict

# pandas-boundary: optimalportfolios Constraints expects pd.Series bounds.
import pandas as pd
import polars as pl

from optimalportfolios import Constraints

from src.portfolios.portfolio_QWIM import Portfolio_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


if TYPE_CHECKING:
    import numpy as np


_logger = get_logger(name = __name__)


class _ConstraintsKwargs(TypedDict, total=False):
    """Typed kwargs for constructing ``optimalportfolios.Constraints``."""

    is_long_only: bool
    min_weights: pd.Series
    max_weights: pd.Series


def _build_constraints(
    *, asset_names: list[str], is_long_only: bool = True, min_w_scalar: float | None = None, max_w_scalar: float | None = None) -> Constraints:
    """Build an ``optimalportfolios`` Constraints object.

    Parameters
    ----------
    asset_names : list[str]
        List of asset names (used as index for ``pd.Series`` weight bounds).
    is_long_only : bool
        If ``True``, enforce non-negative weights. Default is ``True``.
    min_w_scalar : float | None
        Scalar minimum weight applied uniformly to all assets. Default is ``None``.
    max_w_scalar : float | None
        Scalar maximum weight applied uniformly to all assets. Default is ``None``.

    Returns
    -------
    Constraints
        Configured ``Constraints`` object for optimalportfolios.

    Raises
    ------
    Exception_Validation_Input
        If ``is_long_only`` is not a boolean value.
    """
    if not isinstance(is_long_only, bool):
        raise Exception_Validation_Input(
            "is_long_only must be a boolean value",
            field_name="is_long_only",
            expected_type=bool,
            actual_value=is_long_only,
        )

    min_weights: pd.Series | None = None
    max_weights: pd.Series | None = None

    if min_w_scalar is not None:
        min_weights = pd.Series([min_w_scalar] * len(asset_names), index=asset_names)

    if max_w_scalar is not None:
        max_weights = pd.Series([max_w_scalar] * len(asset_names), index=asset_names)

    constraints_kwargs: _ConstraintsKwargs = {"is_long_only": is_long_only}
    if min_weights is not None:
        constraints_kwargs["min_weights"] = min_weights
    if max_weights is not None:
        constraints_kwargs["max_weights"] = max_weights

    return Constraints(**constraints_kwargs)


def _extract_weights_to_portfolio_qwim(
    *, weights: np.ndarray, asset_names: list[str], portfolio_name: str, optimization_date: str | datetime | None = None) -> Portfolio_QWIM:
    """Extract weights from numpy array and create a ``Portfolio_QWIM`` object.

    Parameters
    ----------
    weights : np.ndarray
        NumPy array of portfolio weights with shape ``(n_assets,)``.
    asset_names : list[str]
        List of asset names corresponding to weights.
    portfolio_name : str
        Name for the portfolio.
    optimization_date : str | datetime | None
        Date for the portfolio weights. Defaults to current UTC date.

    Returns
    -------
    Portfolio_QWIM
        Portfolio object with the optimized weights.

    Raises
    ------
    Exception_Validation_Input
        If ``weights`` and ``asset_names`` do not have the same length.
    """
    if len(weights) != len(asset_names):
        raise Exception_Validation_Input(
            "weights and asset_names must have the same length",
            field_name="weights / asset_names",
            expected_type=list,
            actual_value=f"len(weights)={len(weights)}, len(asset_names)={len(asset_names)}",
        )

    if optimization_date is None:
        opt_date = datetime.now(UTC).strftime("%Y-%m-%d")
    elif isinstance(optimization_date, datetime):
        opt_date = optimization_date.strftime("%Y-%m-%d")
    else:
        opt_date = str(optimization_date)

    weights_dict: dict[str, list[object]] = {"Date": [opt_date]}
    for asset_name, weight in zip(asset_names, weights, strict=False):
        weights_dict[asset_name] = [float(weight)]

    weights_df = pl.DataFrame(weights_dict)

    port = Portfolio_QWIM(
        name_portfolio=portfolio_name,
        names_components=asset_names,
        date_portfolio=opt_date,
    )
    port.m_portfolio_weights = weights_df

    return port
