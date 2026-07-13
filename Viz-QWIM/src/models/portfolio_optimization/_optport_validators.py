"""Pure validation and conversion helpers for the optimalportfolios wrapper.

These functions have no external solver dependencies and can be tested
without access to the ``optimalportfolios`` package.

Author: QWIM Team
"""

from __future__ import annotations

import numpy as np
import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def _validate_returns_data(*, returns_data: pl.DataFrame) -> tuple[bool, str]:
    """Validate returns DataFrame structure and content.

    Defensive validation following project standards with early returns.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame to validate.

    Returns
    -------
    tuple[bool, str]
        ``(True, "")`` when valid; ``(False, error_description)`` otherwise.
    """
    if returns_data is None:
        return False, "returns_data cannot be None"

    if not isinstance(returns_data, pl.DataFrame):
        return False, f"returns_data must be Polars DataFrame, got {type(returns_data)}"

    if len(returns_data) == 0:
        return False, "returns_data cannot be empty"

    if "Date" not in returns_data.columns:
        return False, "returns_data must have 'Date' column"

    if returns_data.get_column("Date").null_count() > 0:
        return False, "returns_data 'Date' column cannot contain null values"

    asset_columns = [col for col in returns_data.columns if col != "Date"]
    if len(asset_columns) == 0:
        return False, "returns_data must have at least one asset column besides 'Date'"

    for col in asset_columns:
        series_asset = returns_data.get_column(col)
        if series_asset.dtype not in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]:
            return False, f"Asset column '{col}' must be numeric, got {series_asset.dtype}"

        if series_asset.null_count() > 0:
            return False, f"Asset column '{col}' cannot contain null values"

        if not series_asset.cast(pl.Float64).is_finite().all():
            return False, f"Asset column '{col}' must contain only finite numeric values"

    return True, ""


def _convert_polars_to_numpy_returns(*, returns_data: pl.DataFrame) -> np.ndarray:
    """Convert Polars DataFrame to NumPy array for the optimalportfolios package.

    Parameters
    ----------
    returns_data : pl.DataFrame
        Polars DataFrame with ``'Date'`` and asset return columns.

    Returns
    -------
    np.ndarray
        Returns array of shape ``(n_samples, n_assets)``.
    """
    asset_columns = [col for col in returns_data.columns if col != "Date"]
    return returns_data.select(asset_columns).to_numpy().astype(np.float64)


def _compute_covar_and_means(
    *, returns_array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute covariance matrix and mean returns from a returns array.

    Parameters
    ----------
    returns_array : np.ndarray
        Returns array with shape ``(n_samples, n_assets)``.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(covariance_matrix, mean_returns)`` where ``covariance_matrix`` has
        shape ``(n_assets, n_assets)`` and ``mean_returns`` has shape ``(n_assets,)``.

    Raises
    ------
    Exception_Validation_Input
        If ``returns_array`` is not a 2-D array with at least two observations.
    """
    if not isinstance(returns_array, np.ndarray):
        raise Exception_Validation_Input(
            "returns_array must be a NumPy array",
            field_name="returns_array",
            expected_type=np.ndarray,
            actual_value=type(returns_array).__name__,
        )

    if returns_array.ndim != 2:
        raise Exception_Validation_Input(
            "returns_array must be a 2-D NumPy array",
            field_name="returns_array",
            expected_type=np.ndarray,
            actual_value=f"ndim={returns_array.ndim}",
        )

    if returns_array.shape[0] < 2 or returns_array.shape[1] < 1:
        raise Exception_Validation_Input(
            "returns_array must have at least 2 observations and 1 asset",
            field_name="returns_array",
            expected_type=np.ndarray,
            actual_value=f"shape={returns_array.shape}",
        )

    covar = np.cov(returns_array.T)
    means = np.mean(returns_array, axis=0)
    if covar.ndim == 0:
        covar = np.array([[float(covar)]])
    return covar, means


def _validate_scalar_positive_finite(
    *, value_input: object, field_name: str) -> float:
    """Validate positive finite scalar optimizer inputs.

    Parameters
    ----------
    value_input : object
        Candidate scalar value supplied to a public optimizer wrapper.
    field_name : str
        Parameter name used in the validation error context.

    Returns
    -------
    float
        Validated positive finite scalar converted to ``float``.

    Raises
    ------
    Exception_Validation_Input
        If the value is boolean, non-numeric, non-finite, or not strictly positive.
    """
    if isinstance(value_input, bool | np.bool_) or not isinstance(
        value_input,
        float | int | np.floating | np.integer,
    ):
        raise Exception_Validation_Input(
            f"{field_name} must be a positive finite numeric value, got {value_input}",
            field_name=field_name,
            expected_type=float,
            actual_value=value_input,
        )

    if not np.isfinite(value_input):
        raise Exception_Validation_Input(
            f"{field_name} must be a positive finite numeric value, got {value_input}",
            field_name=field_name,
            expected_type=float,
            actual_value=value_input,
        )

    value_float = float(value_input)
    if value_float <= 0:
        raise Exception_Validation_Input(
            f"{field_name} must be positive, got {value_input}",
            field_name=field_name,
            expected_type=float,
            actual_value=value_input,
        )

    return value_float


def _validate_scalar_finite_numeric(
    *, value_input: object, field_name: str) -> float:
    """Validate finite numeric scalar inputs that may be negative or zero.

    Parameters
    ----------
    value_input : object
        Candidate scalar value supplied to a public optimizer wrapper.
    field_name : str
        Parameter name used in the validation error context.

    Returns
    -------
    float
        Validated finite numeric scalar converted to ``float``.

    Raises
    ------
    Exception_Validation_Input
        If the value is boolean, non-numeric, or non-finite.
    """
    if isinstance(value_input, bool | np.bool_) or not isinstance(
        value_input,
        float | int | np.floating | np.integer,
    ):
        raise Exception_Validation_Input(
            f"{field_name} must be a finite numeric value, got {value_input}",
            field_name=field_name,
            expected_type=float,
            actual_value=value_input,
        )

    if not np.isfinite(value_input):
        raise Exception_Validation_Input(
            f"{field_name} must be a finite numeric value, got {value_input}",
            field_name=field_name,
            expected_type=float,
            actual_value=value_input,
        )

    return float(value_input)


def _validate_positive_integer(
    *, value_input: object, field_name: str) -> int:
    """Validate strictly positive integer optimizer inputs.

    Parameters
    ----------
    value_input : object
        Candidate scalar value supplied to a public optimizer wrapper.
    field_name : str
        Parameter name used in the validation error context.

    Returns
    -------
    int
        Validated positive integer.

    Raises
    ------
    Exception_Validation_Input
        If the value is boolean, non-integer, or less than one.
    """
    if isinstance(value_input, bool | np.bool_) or not isinstance(
        value_input,
        int | np.integer,
    ):
        raise Exception_Validation_Input(
            f"{field_name} must be a positive integer, got {value_input}",
            field_name=field_name,
            expected_type=int,
            actual_value=value_input,
        )

    value_int = int(value_input)
    if value_int < 1:
        raise Exception_Validation_Input(
            f"{field_name} must be at least 1, got {value_input}",
            field_name=field_name,
            expected_type=int,
            actual_value=value_input,
        )

    return value_int


def _validate_boolean_flag(
    *, value_input: object, field_name: str) -> bool:
    """Validate boolean optimizer flags at public wrapper boundaries.

    Parameters
    ----------
    value_input : object
        Candidate boolean-like value supplied to a public optimizer wrapper.
    field_name : str
        Parameter name used in the validation error context.

    Returns
    -------
    bool
        Validated boolean value.

    Raises
    ------
    Exception_Validation_Input
        If the value is not a real boolean.
    """
    if not isinstance(value_input, bool | np.bool_):
        raise Exception_Validation_Input(
            f"{field_name} must be a boolean value, got {value_input}",
            field_name=field_name,
            expected_type=bool,
            actual_value=value_input,
        )

    return bool(value_input)


def _validate_risk_budgets(
    *, risk_budgets_input: object, asset_names: list[str]) -> np.ndarray | None:
    """Validate risk-budget inputs for budgeted-risk-contribution optimization.

    Parameters
    ----------
    risk_budgets_input : object
        Optional dict or one-dimensional array-like input with one budget per asset.
    asset_names : list[str]
        Asset names used to validate length and dict keys.

    Returns
    -------
    np.ndarray | None
        Validated floating-point risk budgets aligned to ``asset_names``, or
        ``None`` when equal-risk budgeting should be used.

    Raises
    ------
    Exception_Validation_Input
        If keys are missing, the input is not one-dimensional, contains invalid
        values, has the wrong length, includes negative budgets, or does not sum
        to one.
    """
    if risk_budgets_input is None:
        return None

    if isinstance(risk_budgets_input, dict):
        missing = [asset_name for asset_name in asset_names if asset_name not in risk_budgets_input]
        if missing:
            msg = f"risk_budgets dict missing keys for assets: {missing}"
            _logger.error(msg)
            raise Exception_Validation_Input(msg)

        unexpected = [
            budget_name
            for budget_name in risk_budgets_input
            if budget_name not in asset_names
        ]
        if unexpected:
            msg = f"risk_budgets dict contains unexpected assets: {unexpected}"
            _logger.error(msg)
            raise Exception_Validation_Input(msg)

        raw_budget_values: object = [risk_budgets_input[asset_name] for asset_name in asset_names]
    else:
        raw_budget_values = risk_budgets_input

    budgets_object = np.asarray(raw_budget_values, dtype=object)
    if budgets_object.ndim != 1:
        raise Exception_Validation_Input(
            "risk_budgets must be a 1-D array-like input",
            field_name="risk_budgets",
            expected_type=np.ndarray,
            actual_value=risk_budgets_input,
        )

    if len(budgets_object) != len(asset_names):
        msg = (
            f"risk_budgets length ({len(budgets_object)}) must match"
            f" n_assets ({len(asset_names)})"
        )
        _logger.error(msg)
        raise Exception_Validation_Input(msg)

    budgets_array = np.array(
        [
            _validate_scalar_finite_numeric(
                value_input = budget_value,
                field_name=f"risk_budgets[{index}]",
            )
            for index, budget_value in enumerate(budgets_object.tolist())
        ],
        dtype=float,
    )

    if np.any(budgets_array < 0):
        raise Exception_Validation_Input(
            "risk_budgets must contain non-negative values",
            field_name="risk_budgets",
            expected_type=np.ndarray,
            actual_value=risk_budgets_input,
        )

    budget_sum = float(np.sum(budgets_array))
    if not np.isclose(budget_sum, 1.0, atol=1e-6):
        msg = f"risk_budgets must sum to 1.0, got {budget_sum}"
        _logger.error(msg)
        raise Exception_Validation_Input(msg)

    return budgets_array
