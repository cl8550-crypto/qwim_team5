r"""Scenarios from statistical distributions.

=============================================

Provides :class:`Scenarios_Distribution`, a concrete subclass of
:class:`Scenarios_Base` that generates daily financial time-series
scenarios by sampling from multivariate statistical distributions.

Supported distributions
-----------------------

1. **Multivariate Normal**
   $\mathbf{X} \sim \mathcal{N}(\boldsymbol{\mu},\, \Sigma)$
   with mean vector $\boldsymbol{\mu}$ and covariance $\Sigma$.

2. **Multivariate Lognormal**
   $\mathbf{X} = \exp(\mathbf{Y})$ where
   $\mathbf{Y} \sim \mathcal{N}(\boldsymbol{\mu}_{\ln},\, \Sigma_{\ln})$.
   The underlying normal parameters are derived from the requested
   arithmetic mean and covariance via the standard mapping.

3. **Multivariate Student-*t***
   $\mathbf{X} \sim t_{\nu}(\boldsymbol{\mu},\, \Sigma)$
   with degrees of freedom $\nu > 2$.  Heavier tails capture crash
   scenarios better than the normal distribution.

All generators accept a covariance (or correlation + volatility) matrix
and use Cholesky decomposition to produce correlated samples.

Author
------
QWIM Team

Version
-------
0.6.0 (2026-03-01)
"""

from __future__ import annotations

import attrs

import datetime as dt

from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from aenum import Enum


if TYPE_CHECKING:
    from collections.abc import Sequence

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._scenario_rng import (
    create_scenario_rng_QWIM,
    spawn_scenario_rng_streams_QWIM,
)
from .scenarios_base import (
    Frequency_Time_Series,
    Scenario_Data_Type,
    Scenarios_Base,
)


_logger = get_logger(name = __name__)


# ======================================================================
# Enums
# ======================================================================


class Distribution_Type(Enum):
    """Statistical distribution used for scenario generation.

    Attributes
    ----------
    NORMAL : str
        Multivariate normal (Gaussian).
    LOGNORMAL : str
        Multivariate lognormal.
    STUDENT_T : str
        Multivariate Student-*t*.
    """

    NORMAL = "Normal"
    LOGNORMAL = "Lognormal"
    STUDENT_T = "Student-t"


class Covariance_Input_Type(Enum):
    """How the covariance structure is supplied.

    Attributes
    ----------
    COVARIANCE_MATRIX : str
        Full covariance matrix provided directly.
    CORRELATION_AND_VOLATILITIES : str
        Correlation matrix + volatility vector provided separately.
    """

    COVARIANCE_MATRIX = "Covariance Matrix"
    CORRELATION_AND_VOLATILITIES = "Correlation + Volatilities"


# ======================================================================
# Helper: ensure positive semi-definite
# ======================================================================


def _nearest_PSD(*, matrix: np.ndarray) -> np.ndarray:
    """Return the nearest positive semi-definite matrix.

    Uses eigenvalue clipping: any negative eigenvalue is replaced by a
    small positive epsilon.

    Parameters
    ----------
    matrix : np.ndarray
        Symmetric matrix to repair.

    Returns
    -------
    np.ndarray
        PSD-corrected matrix.
    """
    eigvals, eigvecs = np.linalg.eigh(matrix)
    eigvals = np.maximum(eigvals, 1e-10)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def _calc_lognormal_normal_parameters(
    *, mean_returns: np.ndarray, covariance_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calculate the underlying normal parameters for lognormal sampling.

    Parameters
    ----------
    mean_returns : np.ndarray
        Strictly positive arithmetic means of the target lognormal
        distribution.
    covariance_matrix : np.ndarray
        Covariance matrix of the target lognormal distribution.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Pair ``(mu_ln, sigma_ln)`` containing the underlying normal
        mean vector and covariance matrix.

    Raises
    ------
    Exception_Validation_Input
        Raised when any requested arithmetic mean is non-positive.
    Exception_Calculation
        Raised when the covariance-to-lognormal mapping is invalid for
        at least one component pair.

    Notes
    -----
    This helper is intentionally pure and vectorized so the expensive
    covariance-to-lognormal mapping stays in NumPy rather than Python
    nested loops.
    """
    if np.any(mean_returns <= 0):
        raise Exception_Validation_Input(
            "Lognormal requires strictly positive mean returns "
            "(interpret as price levels or 1 + return)",
            field_name="mean_returns",
            expected_type="> 0",
            actual_value=mean_returns[mean_returns <= 0].tolist(),
        )

    denominator_matrix = np.outer(mean_returns, mean_returns)
    ratio_matrix = covariance_matrix / denominator_matrix
    invalid_ratio_mask = 1.0 + ratio_matrix <= 0.0

    if np.any(invalid_ratio_mask):
        idx_invalid = np.argwhere(invalid_ratio_mask)[0]
        idx_row = int(idx_invalid[0])
        idx_col = int(idx_invalid[1])
        raise Exception_Calculation(
            "Lognormal parameter mapping failed for "
            f"components ({idx_row}, {idx_col}): 1 + Cov/(mu_i*mu_j) "
            f"= {1.0 + ratio_matrix[idx_row, idx_col]:.6e} <= 0",
        )

    sigma_ln = np.log1p(ratio_matrix)
    mu_ln = np.log(mean_returns) - 0.5 * np.diag(sigma_ln)
    return mu_ln, sigma_ln


# ======================================================================
# Scenarios_Distribution
# ======================================================================


class Scenarios_Distribution(Scenarios_Base):
    r"""Scenarios generated from multivariate statistical distributions.

    Parameters
    ----------
    names_components : Sequence[str]
        Component (asset) names.
    distribution_type : Distribution_Type
        Which distribution to sample from.
    mean_returns : np.ndarray
        Mean return vector, shape ``(K,)``.  For lognormal this is
        the desired *arithmetic* mean of the output, **not** the
        underlying normal mean.
    covariance_matrix : np.ndarray | None
        ``(K, K)`` covariance matrix.  Either this **or**
        *correlation_matrix + volatilities* must be supplied.
    correlation_matrix : np.ndarray | None
        ``(K, K)`` correlation matrix (ignored if *covariance_matrix*
        is provided).
    volatilities : np.ndarray | None
        ``(K,)`` volatility vector (ignored if *covariance_matrix* is
        provided).
    degrees_of_freedom : float
        Degrees of freedom $\nu$ for Student-*t* (must be > 2).
        Ignored for other distributions.
    dates : Sequence[dt.date] | None
        Pre-defined dates (if *None*, generated from *start_date* /
        *num_days*).
    start_date : dt.date | None
        First business day when *dates* is *None*.
    num_days : int
        Number of trading days to generate (default 252).
    num_scenarios : int
        Number of independent scenario paths.
    data_type : Scenario_Data_Type
        Type of generated data.
    frequency : Frequency
        Observation frequency.
    name_scenarios : str
        Human-readable label.
    random_seed : int | None
        RNG seed for reproducibility.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        names_components: Sequence[str],
        distribution_type: Distribution_Type = Distribution_Type.NORMAL,
        mean_returns: np.ndarray | None = None,
        covariance_matrix: np.ndarray | None = None,
        correlation_matrix: np.ndarray | None = None,
        volatilities: np.ndarray | None = None,
        degrees_of_freedom: float = 5.0,
        dates: Sequence[dt.date] | None = None,
        start_date: dt.date | None = None,
        num_days: int = 252,
        num_scenarios: int = 1,
        data_type: Scenario_Data_Type = Scenario_Data_Type.RETURN_ARITHMETIC,
        frequency: Frequency_Time_Series = Frequency_Time_Series.DAILY,
        name_scenarios: str = "Distribution Scenario",
        random_seed: int | None = None,
    ) -> None:
        """Initialize the distribution scenario set with statistical parameters for return generation."""
        K = len(names_components)

        # --- distribution type ---
        if not isinstance(distribution_type, Distribution_Type):
            raise Exception_Validation_Input(
                f"distribution_type must be Distribution_Type enum, "
                f"got {type(distribution_type).__name__}",
                field_name="distribution_type",
                expected_type="Distribution_Type",
                actual_value=distribution_type,
            )

        # --- mean returns ---
        if mean_returns is None:
            mean_returns = np.zeros(K, dtype=np.float64)
        else:
            mean_returns = np.asarray(mean_returns, dtype=np.float64)

        if mean_returns.shape != (K,):
            raise Exception_Validation_Input(
                f"mean_returns shape must be ({K},), got {mean_returns.shape}",
                field_name="mean_returns",
                expected_type=f"({K},)",
                actual_value=mean_returns.shape,
            )

        # --- covariance matrix ---
        if covariance_matrix is not None:
            covariance_matrix = np.asarray(
                covariance_matrix,
                dtype=np.float64,
            )
            if covariance_matrix.shape != (K, K):
                raise Exception_Validation_Input(
                    f"covariance_matrix shape must be ({K}, {K}), got {covariance_matrix.shape}",
                    field_name="covariance_matrix",
                    expected_type=f"({K}, {K})",
                    actual_value=covariance_matrix.shape,
                )
            cov_input_type = Covariance_Input_Type.COVARIANCE_MATRIX

        elif correlation_matrix is not None and volatilities is not None:
            correlation_matrix = np.asarray(
                correlation_matrix,
                dtype=np.float64,
            )
            volatilities = np.asarray(volatilities, dtype=np.float64)

            if correlation_matrix.shape != (K, K):
                raise Exception_Validation_Input(
                    f"correlation_matrix shape must be ({K}, {K}), got {correlation_matrix.shape}",
                    field_name="correlation_matrix",
                    expected_type=f"({K}, {K})",
                    actual_value=correlation_matrix.shape,
                )
            if volatilities.shape != (K,):
                raise Exception_Validation_Input(
                    f"volatilities shape must be ({K},), got {volatilities.shape}",
                    field_name="volatilities",
                    expected_type=f"({K},)",
                    actual_value=volatilities.shape,
                )

            # Build covariance: Cov = diag(sigma) @ Corr @ diag(sigma)
            mat_D = np.diag(volatilities)
            covariance_matrix = mat_D @ correlation_matrix @ mat_D
            cov_input_type = Covariance_Input_Type.CORRELATION_AND_VOLATILITIES

        else:
            # Default: identity covariance (independent, unit variance)
            covariance_matrix = np.eye(K, dtype=np.float64)
            cov_input_type = Covariance_Input_Type.COVARIANCE_MATRIX

        # --- validate symmetry ---
        if not np.allclose(covariance_matrix, covariance_matrix.T, atol=1e-8):
            raise Exception_Validation_Input(
                "Covariance matrix must be symmetric",
                field_name="covariance_matrix",
                expected_type="symmetric",
                actual_value="asymmetric",
            )

        if (
            isinstance(degrees_of_freedom, bool)
            or not isinstance(degrees_of_freedom, float | int)
            or not np.isfinite(degrees_of_freedom)
        ):
            raise Exception_Validation_Input(
                "degrees_of_freedom must be a finite real number",
                field_name="degrees_of_freedom",
                expected_type=float,
                actual_value=degrees_of_freedom,
            )

        if isinstance(num_days, bool) or not isinstance(num_days, int) or num_days < 1:
            raise Exception_Validation_Input(
                "num_days must be a positive integer (> 0)",
                field_name="num_days",
                expected_type=int,
                actual_value=num_days,
            )

        if random_seed is not None and (
            isinstance(random_seed, bool)
            or not isinstance(random_seed, int)
            or random_seed < 0
        ):
            raise Exception_Validation_Input(
                "random_seed must be a non-negative integer or None",
                field_name="random_seed",
                expected_type=int,
                actual_value=random_seed,
            )

        if start_date is not None and not isinstance(start_date, dt.date):
            raise Exception_Validation_Input(
                "start_date must be a date instance or None",
                field_name="start_date",
                expected_type=dt.date,
                actual_value=start_date,
            )

        # --- Student-t validation ---
        if distribution_type == Distribution_Type.STUDENT_T and degrees_of_freedom <= 2.0:
            raise Exception_Validation_Input(
                "degrees_of_freedom must be > 2 for Student-t (variance is undefined for nu <= 2)",
                field_name="degrees_of_freedom",
                expected_type="> 2.0",
                actual_value=degrees_of_freedom,
            )

        # --- determine dates ---
        if dates is None and start_date is None:
            start_date = dt.datetime.now(tz=dt.UTC).date()
        if dates is None:
            dates = self._generate_business_dates(start_date = start_date, num_days = num_days)

        # --- base init ---
        super().__init__(
            names_components=list(names_components),
            dates=dates,
            data_type=data_type,
            frequency=frequency,
            num_scenarios=num_scenarios,
            name_scenarios=name_scenarios,
        )

        # --- distribution-specific members ---
        self.m_distribution_type: Distribution_Type = distribution_type
        self.m_mean_returns: np.ndarray = mean_returns
        self.m_covariance_matrix: np.ndarray = covariance_matrix
        self.m_covariance_input_type: Covariance_Input_Type = cov_input_type
        self.m_degrees_of_freedom: float = float(degrees_of_freedom)
        self.m_random_seed: int | None = random_seed
        self.m_num_days: int = num_days

        # Derive correlation matrix & volatilities from covariance
        vols = np.sqrt(np.diag(covariance_matrix))
        vols_safe = np.where(vols == 0, 1.0, vols)
        D_inv = np.diag(1.0 / vols_safe)
        self.m_volatilities: np.ndarray = vols
        self.m_correlation_matrix: np.ndarray = D_inv @ covariance_matrix @ D_inv

        _logger.info(
            "Scenarios_Distribution created",
            extra={
                "event_type": "scenarios_distribution_created",
                "name_scenarios": self.m_name_scenarios,
                "distribution_type": self.m_distribution_type.value,
                "num_components": self.m_num_components,
                "num_dates": self.m_num_dates,
            },
        )

    # ------------------------------------------------------------------
    # Properties (distribution-specific)
    # ------------------------------------------------------------------

    @property
    def distribution_type(self) -> Distribution_Type:
        """Distribution_Type : Distribution used for generation."""
        return self.m_distribution_type

    @property
    def mean_returns(self) -> np.ndarray:
        """np.ndarray : Mean return vector (copy)."""
        return self.m_mean_returns.copy()

    @property
    def covariance_matrix_input(self) -> np.ndarray:
        """np.ndarray : Covariance matrix (copy)."""
        return self.m_covariance_matrix.copy()

    @property
    def covariance_input_type(self) -> Covariance_Input_Type:
        """Covariance_Input_Type : How covariance was supplied."""
        return self.m_covariance_input_type

    @property
    def volatilities(self) -> np.ndarray:
        """np.ndarray : Volatilities derived from covariance (copy)."""
        return self.m_volatilities.copy()

    @property
    def correlation_matrix_derived(self) -> np.ndarray:
        """np.ndarray : Correlation matrix derived from covariance."""
        return self.m_correlation_matrix.copy()

    @property
    def degrees_of_freedom(self) -> float:
        """Float : Degrees of freedom for Student-*t*."""
        return self.m_degrees_of_freedom

    @property
    def random_seed(self) -> int | None:
        """Int | None : RNG seed for reproducibility."""
        return self.m_random_seed

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def generate(self) -> pl.DataFrame:
        r"""Generate daily scenarios from the configured distribution.

        Dispatches to one of:

        * :meth:`_generate_normal`
        * :meth:`_generate_lognormal`
        * :meth:`_generate_student_t`

        Returns
        -------
        pl.DataFrame
            DataFrame with ``Date`` column and one column per
            component.
        """
        generators = {
            Distribution_Type.NORMAL: self._generate_normal,
            Distribution_Type.LOGNORMAL: self._generate_lognormal,
            Distribution_Type.STUDENT_T: self._generate_student_t,
        }

        generator = generators[self.m_distribution_type]
        return generator()

    # ------------------------------------------------------------------
    # Private generators
    # ------------------------------------------------------------------

    def _cholesky_safe(self, *, matrix: np.ndarray) -> np.ndarray:
        """Compute Cholesky with PSD fallback.

        Parameters
        ----------
        matrix : np.ndarray
            Symmetric matrix.

        Returns
        -------
        np.ndarray
            Lower-triangular Cholesky factor ``L`` such that
            ``L @ L.T ≈ matrix``.
        """
        try:
            return np.linalg.cholesky(matrix)
        except np.linalg.LinAlgError:
            _logger.warning(
                "Matrix not positive-definite; applying eigenvalue clipping to nearest PSD matrix",
            )
            return np.linalg.cholesky(_nearest_PSD(matrix = matrix))

    def _build_dataframe(self, *, samples: np.ndarray) -> pl.DataFrame:
        """Convert a ``(T, K)`` numpy array into a Polars DataFrame.

        Parameters
        ----------
        samples : np.ndarray
            Array of shape ``(T, K)`` where ``T`` is the number of
            dates and ``K`` the number of components.

        Returns
        -------
        pl.DataFrame
            With ``Date`` column and one Float64 column per component.
        """
        data: dict[str, list] = {"Date": self.m_dates}
        for idx_j, item_name in enumerate(self.m_names_components):
            data[item_name] = samples[:, idx_j].tolist()

        temp_df = pl.DataFrame(data).with_columns(
            pl.col("Date").cast(pl.Date),
        )
        df = temp_df.with_columns(
            [
                pl.col(item_name).cast(pl.Float64, strict=False)
                for item_name in self.m_names_components
            ],
        )

        self.m_df_scenarios = df
        return self.m_df_scenarios

    def _generate_normal(self) -> pl.DataFrame:
        r"""Sample from multivariate normal.

        $$
        \mathbf{X}_t = \boldsymbol{\mu} + L \, \mathbf{Z}_t,
        \quad \mathbf{Z}_t \sim \mathcal{N}(\mathbf{0}, I)
        $$

        where $L$ is the lower Cholesky factor of $\Sigma$.

        Returns
        -------
        pl.DataFrame
        """
        rng = create_scenario_rng_QWIM(seed = self.m_random_seed)
        temp_dates = self.m_num_dates
        temp_num_components = self.m_num_components

        if temp_dates == 0:
            raise Exception_Calculation(
                "Cannot generate: no dates available",
            )

        mat_chol = self._cholesky_safe(matrix = self.m_covariance_matrix)
        temp_RNG_normal = rng.standard_normal((temp_dates, temp_num_components))
        samples = temp_RNG_normal @ mat_chol.T + self.m_mean_returns

        _logger.info(
            "Generated normal samples",
            extra={
                "event_type": "generation_normal",
                "num_dates": temp_dates,
                "num_components": temp_num_components,
                "random_seed": self.m_random_seed,
            },
        )
        return self._build_dataframe(samples = samples)

    def _generate_lognormal(self) -> pl.DataFrame:
        r"""Sample from multivariate lognormal.

        We want $\mathbf{X}$ such that
        $E[\mathbf{X}] = \boldsymbol{\mu}$ and the covariance of
        $\mathbf{X}$ matches the input.  The underlying normal
        parameters are:

        $$
        \mu_{\ln,i}
          = \ln\!\bigl(\mu_i\bigr)
            - \tfrac{1}{2}\,\sigma_{\ln,ii}
        $$
        $$
        \sigma_{\ln,ij}
          = \ln\!\Bigl(1 + \frac{\Sigma_{ij}}{\mu_i \mu_j}\Bigr)
        $$

        Then $\mathbf{X} = \exp(\mathbf{Y})$, where
        $\mathbf{Y} \sim \mathcal{N}(\boldsymbol{\mu}_{\ln},
        \Sigma_{\ln})$.

        Returns
        -------
        pl.DataFrame
        """
        rng = create_scenario_rng_QWIM(seed = self.m_random_seed)
        temp_dates = self.m_num_dates
        temp_num_components = self.m_num_components

        if temp_dates == 0:
            raise Exception_Calculation(
                "Cannot generate: no dates available",
            )

        mu_ln, sigma_ln = _calc_lognormal_normal_parameters(
            mean_returns=self.m_mean_returns,
            covariance_matrix=self.m_covariance_matrix,
        )

        mat_chol = self._cholesky_safe(matrix = sigma_ln)
        temp_RNG_normal = rng.standard_normal((temp_dates, temp_num_components))
        temp_RNG = temp_RNG_normal @ mat_chol.T + mu_ln
        samples = np.exp(temp_RNG)

        _logger.info(
            "Generated lognormal samples",
            extra={
                "event_type": "generation_lognormal",
                "num_dates": temp_dates,
                "num_components": temp_num_components,
                "random_seed": self.m_random_seed,
            },
        )
        return self._build_dataframe(samples = samples)

    def _generate_student_t(self) -> pl.DataFrame:
        r"""Sample from multivariate Student-*t*.

        For $\nu > 2$ degrees of freedom:

        $$
        \mathbf{X}_t = \boldsymbol{\mu}
          + L \, \frac{\mathbf{Z}_t}{\sqrt{W_t / \nu}}
        $$

        where $\mathbf{Z}_t \sim \mathcal{N}(\mathbf{0}, I)$ and
        $W_t \sim \chi^2(\nu)$ are independent, and $L$ is the
        Cholesky factor of the *scale* matrix

        $$
        \Psi = \frac{\nu - 2}{\nu}\,\Sigma
        $$

        so that $\operatorname{Cov}(\mathbf{X}) = \Sigma$.

        Returns
        -------
        pl.DataFrame
        """
        rng_normal, rng_chi_square = spawn_scenario_rng_streams_QWIM(
            seed = self.m_random_seed,
            num_streams = 2,
        )
        temp_dates = self.m_num_dates
        temp_num_components = self.m_num_components
        nu = self.m_degrees_of_freedom

        if temp_dates == 0:
            raise Exception_Calculation(
                "Cannot generate: no dates available",
            )

        # Scale matrix so that Cov(X) = Sigma
        scale_matrix = (nu - 2.0) / nu * self.m_covariance_matrix

        mat_chol = self._cholesky_safe(matrix = scale_matrix)
        temp_RNG_normal = rng_normal.standard_normal((temp_dates, temp_num_components))
        temp_chi_square = rng_chi_square.chisquare(df=nu, size=temp_dates)

        # X = mu + L @ Z / sqrt(W / nu)
        scaling = np.sqrt(temp_chi_square / nu)[:, np.newaxis]  # (temp_dates, 1)
        samples = self.m_mean_returns + (temp_RNG_normal @ mat_chol.T) / scaling

        _logger.info(
            "Generated Student-t samples",
            extra={
                "event_type": "generation_student_t",
                "num_dates": temp_dates,
                "num_components": temp_num_components,
                "degrees_of_freedom": nu,
                "random_seed": self.m_random_seed,
            },
        )
        return self._build_dataframe(samples = samples)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_correlation_and_volatilities(
        cls, *, names_components: Sequence[str], correlation_matrix: np.ndarray, volatilities: np.ndarray, distribution_type: Distribution_Type = Distribution_Type.NORMAL, mean_returns: np.ndarray | None = None, degrees_of_freedom: float = 5.0, dates: Sequence[dt.date] | None = None, start_date: dt.date | None = None, num_days: int = 252, num_scenarios: int = 1, data_type: Scenario_Data_Type = Scenario_Data_Type.RETURN_ARITHMETIC, frequency: Frequency_Time_Series = Frequency_Time_Series.DAILY, name_scenarios: str = "Distribution Scenario", random_seed: int | None = None) -> Scenarios_Distribution:
        """Construct from correlation matrix + volatilities.

        This is a convenience wrapper that converts to a covariance
        matrix and delegates to the standard constructor.

        Parameters
        ----------
        names_components : Sequence[str]
            Component names.
        correlation_matrix : np.ndarray
            ``(K, K)`` correlation matrix.
        volatilities : np.ndarray
            ``(K,)`` volatilities (standard deviations).
        distribution_type, mean_returns, degrees_of_freedom, dates,
        start_date, num_days, num_scenarios, data_type, frequency,
        name_scenarios, random_seed
            Forwarded to the constructor.

        Returns
        -------
        Scenarios_Distribution
        """
        return cls(
            names_components=names_components,
            distribution_type=distribution_type,
            mean_returns=mean_returns,
            correlation_matrix=correlation_matrix,
            volatilities=volatilities,
            degrees_of_freedom=degrees_of_freedom,
            dates=dates,
            start_date=start_date,
            num_days=num_days,
            num_scenarios=num_scenarios,
            data_type=data_type,
            frequency=frequency,
            name_scenarios=name_scenarios,
            random_seed=random_seed,
        )

    # ------------------------------------------------------------------
    # Dunder overrides
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return a string representation of this instance."""
        return (
            f"Scenarios_Distribution("
            f"name='{self.m_name_scenarios}', "
            f"distribution={self.m_distribution_type.value}, "
            f"components={self.m_num_components}, "
            f"dates={self.m_num_dates})"
        )
