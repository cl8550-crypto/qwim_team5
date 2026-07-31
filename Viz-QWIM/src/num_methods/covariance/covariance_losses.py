"""Loss functions for evaluating covariance-matrix estimates."""

from __future__ import annotations

import numpy as np # type: ignore

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


def _validate_covariance_pair(
    *,
    estimated_covariance: np.ndarray,
    realized_covariance: np.ndarray,
) -> None:
    """Validate two covariance matrices before calculating loss.

    Parameters
    ----------
    estimated_covariance
        Covariance matrix estimated from the training window.
    realized_covariance
        Covariance matrix observed during the test window.

    Raises
    ------
    Exception_Validation_Input
        Raised when the matrices are invalid or incompatible.
    """
    if estimated_covariance.ndim != 2 or realized_covariance.ndim != 2:
        raise Exception_Validation_Input(
            message="Covariance matrices must be two-dimensional."
        )

    if estimated_covariance.shape != realized_covariance.shape:
        raise Exception_Validation_Input(
            message=(
                "Estimated and realized covariance matrices must have "
                "the same dimensions."
            )
        )

    if estimated_covariance.shape[0] != estimated_covariance.shape[1]:
        raise Exception_Validation_Input(
            message="Covariance matrices must be square."
        )

    if not np.all(np.isfinite(estimated_covariance)):
        raise Exception_Validation_Input(
            message="Estimated covariance contains NaN or infinite values."
        )

    if not np.all(np.isfinite(realized_covariance)):
        raise Exception_Validation_Input(
            message="Realized covariance contains NaN or infinite values."
        )


def calculate_frobenius_loss(
    *,
    estimated_covariance: np.ndarray,
    realized_covariance: np.ndarray,
) -> float:
    r"""Calculate squared Frobenius loss.

    The squared Frobenius loss measures the total squared element-wise
    difference between the estimated and realized covariance matrices.

    .. math::

        L_F = \|\hat{\Sigma} - \Sigma\|_F^2

    Returns
    -------
    float
        Squared Frobenius loss.
    """
    _validate_covariance_pair(
        estimated_covariance=estimated_covariance,
        realized_covariance=realized_covariance,
    )

    difference_matrix = estimated_covariance - realized_covariance

    return float(np.sum(np.square(difference_matrix)))


def calculate_relative_frobenius_loss(
    *,
    estimated_covariance: np.ndarray,
    realized_covariance: np.ndarray,
) -> float:
    r"""Calculate Frobenius loss relative to realized covariance magnitude.

    .. math::

        L_{RF} =
        \frac{\|\hat{\Sigma} - \Sigma\|_F}
        {\|\Sigma\|_F}

    Returns
    -------
    float
        Relative Frobenius loss.

    Raises
    ------
    Exception_Validation_Input
        Raised when the realized covariance norm is effectively zero.
    """
    _validate_covariance_pair(
        estimated_covariance=estimated_covariance,
        realized_covariance=realized_covariance,
    )

    realized_norm = np.linalg.norm(realized_covariance, ord="fro")

    if np.isclose(realized_norm, 0.0):
        raise Exception_Validation_Input(
            message="Realized covariance norm cannot be zero."
        )

    estimation_error = np.linalg.norm(
        estimated_covariance - realized_covariance,
        ord="fro",
    )

    return float(estimation_error / realized_norm)


def calculate_portfolio_variance_loss(
    *,
    estimated_covariance: np.ndarray,
    realized_covariance: np.ndarray,
    portfolio_weights: np.ndarray,
) -> float:
    r"""Calculate squared portfolio-variance forecast error.

    .. math::

        L_V =
        \left(
        w^\top\hat{\Sigma}w -
        w^\top\Sigma w
        \right)^2

    Parameters
    ----------
    estimated_covariance
        Covariance matrix estimated from the training window.
    realized_covariance
        Covariance matrix observed during the test window.
    portfolio_weights
        One-dimensional vector of portfolio weights.

    Returns
    -------
    float
        Squared variance forecast error.
    """
    _validate_covariance_pair(
        estimated_covariance=estimated_covariance,
        realized_covariance=realized_covariance,
    )

    number_of_assets = estimated_covariance.shape[0]

    if portfolio_weights.ndim != 1:
        raise Exception_Validation_Input(
            message="Portfolio weights must be one-dimensional."
        )

    if portfolio_weights.shape[0] != number_of_assets:
        raise Exception_Validation_Input(
            message="Portfolio weights must match the covariance dimensions."
        )

    if not np.all(np.isfinite(portfolio_weights)):
        raise Exception_Validation_Input(
            message="Portfolio weights contain NaN or infinite values."
        )

    estimated_variance = float(
        portfolio_weights.T @ estimated_covariance @ portfolio_weights
    )
    realized_variance = float(
        portfolio_weights.T @ realized_covariance @ portfolio_weights
    )

    return float(np.square(estimated_variance - realized_variance))


def calculate_gaussian_log_likelihood_loss(
    *,
    estimated_covariance: np.ndarray,
    realized_covariance: np.ndarray,
    regularization: float = 1e-10,
) -> float:
    r"""Calculate Gaussian covariance loss.

    This loss penalizes both poor covariance fit and unstable covariance
    matrices.

    .. math::

        L_G =
        \log|\hat{\Sigma}| +
        \operatorname{tr}
        \left(
        \hat{\Sigma}^{-1}\Sigma
        \right)

    Parameters
    ----------
    estimated_covariance
        Estimated covariance matrix.
    realized_covariance
        Realized covariance matrix.
    regularization
        Small diagonal adjustment used to improve numerical stability.

    Returns
    -------
    float
        Gaussian log-likelihood loss.
    """
    _validate_covariance_pair(
        estimated_covariance=estimated_covariance,
        realized_covariance=realized_covariance,
    )

    if regularization <= 0.0:
        raise Exception_Validation_Input(
            message="Regularization must be positive."
        )

    number_of_assets = estimated_covariance.shape[0]
    regularized_covariance = estimated_covariance + (
        regularization * np.eye(number_of_assets)
    )

    sign, log_determinant = np.linalg.slogdet(regularized_covariance)

    if sign <= 0:
        raise Exception_Validation_Input(
            message="Estimated covariance must have a positive determinant."
        )

    precision_matrix = np.linalg.pinv(regularized_covariance)
    trace_term = np.trace(precision_matrix @ realized_covariance)

    return float(log_determinant + trace_term)