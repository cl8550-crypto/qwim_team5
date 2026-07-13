"""Numerical methods for covariance and correlation matrix estimation.

This module provides numerical methods for estimating covariance and
correlation matrices using various statistical estimators from the
``skfolio`` library.  It also defines enumerations for distance-based
measures commonly used in hierarchical clustering.
"""

from __future__ import annotations

import attrs
import numpy as np
import polars as pl

from aenum import Enum
from skfolio.moments.covariance import (
    OAS,
    DenoiseCovariance,
    DetoneCovariance,
    EmpiricalCovariance,
    EWCovariance,
    GerberCovariance,
    GraphicalLassoCV,
    ImpliedCovariance,
    LedoitWolf,
    ShrunkCovariance,
)

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


class Covariance_Estimator(Enum):  # pyright: ignore[reportGeneralTypeIssues]
    """Enumeration of covariance matrix estimator types.

    This enum defines various methods for estimating covariance matrices
    used in portfolio optimization and risk analysis.

    Attributes
    ----------
    EMPIRICAL : str
        Sample covariance matrix estimator
    GERBER : str
        Gerber statistic-based covariance estimator
    DENOISING : str
        Random matrix theory-based denoising estimator
    DETONING : str
        Market mode removal (detoning) estimator
    EXPONENTIALLY_WEIGHTED : str
        Exponentially weighted moving average (EWMA) covariance
    LEDOIT_WOLF : str
        Ledoit-Wolf shrinkage estimator
    ORACLE_APPROXIMATING_SHRINKAGE : str
        Oracle Approximating Shrinkage (OAS) estimator
    SHRUNK_COVARIANCE : str
        Basic shrinkage covariance estimator
    GRAPHICAL_LASSO_CV : str
        Graphical Lasso with cross-validation
    IMPLIED_COVARIANCE : str
        Market-implied covariance from option prices

    Examples
    --------
    >>> from src.num_methods.covariance.cov_corr import Covariance_Estimator
    >>> estimator = Covariance_Estimator.LEDOIT_WOLF
    >>> print(estimator.value)
    'Ledoit-Wolf'

    Notes
    -----
    - EMPIRICAL: Standard sample covariance (1/n * X^T * X)
    - GERBER: Robust estimator using Gerber statistic for co-movement
    - DENOISING: Removes noise eigenvalues using Marchenko-Pastur distribution
    - DETONING: Removes market-wide systematic component
    - EXPONENTIALLY_WEIGHTED: Gives more weight to recent observations
    - LEDOIT_WOLF: Optimal shrinkage toward identity matrix
    - ORACLE_APPROXIMATING_SHRINKAGE: Improved Ledoit-Wolf with better finite sample properties
    - SHRUNK_COVARIANCE: Basic linear shrinkage estimator
    - GRAPHICAL_LASSO_CV: Sparse inverse covariance via L1 regularization
    - IMPLIED_COVARIANCE: Extracted from market option prices

    References
    ----------
    - Ledoit, O., & Wolf, M. (2004). "A well-conditioned estimator for large-dimensional covariance matrices"
    - Chen, Y., Wiesel, A., Eldar, Y. C., & Hero, A. O. (2010). "Shrinkage algorithms for MMSE covariance estimation"
    - Friedman, J., Hastie, T., & Tibshirani, R. (2008). "Sparse inverse covariance estimation with the graphical lasso"
    """

    EMPIRICAL = "Empirical"
    GERBER = "Gerber"
    DENOISING = "Denoising"
    DETONING = "Detoning"
    EXPONENTIALLY_WEIGHTED = "Exponentially Weighted"
    LEDOIT_WOLF = "Ledoit-Wolf"
    ORACLE_APPROXIMATING_SHRINKAGE = "Oracle Approximating Shrinkage"
    SHRUNK_COVARIANCE = "Shrunk Covariance"
    GRAPHICAL_LASSO_CV = "Graphical Lasso CV"
    IMPLIED_COVARIANCE = "Implied Covariance"


class Distance_Estimator_Type(Enum):  # pyright: ignore[reportGeneralTypeIssues]
    r"""Enumeration of distance estimator types for correlation-based distances.

    This enum defines various methods for computing distances between assets
    based on correlation, covariance, or information-theoretic measures.
    These distances are commonly used in hierarchical clustering for portfolio
    optimization (e.g., Hierarchical Risk Parity).

    **Correlation-Based Distances**: Convert correlation to distance
        - Pearson, Kendall, Spearman correlations transformed to distances

    **Covariance-Based Distances**: Use covariance structure directly
        - Pearson, Kendall, Spearman covariances transformed to distances

    **Information-Theoretic**: Mutual information-based measures
        - Variation of Information for clustering comparison

    Attributes
    ----------
    DISTANCE_PEARSON : str
        Distance derived from Pearson correlation coefficient.
        $d_{ij} = \\sqrt{\\frac{1}{2}(1 - \\rho_{ij})}$ where $\\rho$ is Pearson correlation.
    DISTANCE_KENDALL : str
        Distance derived from Kendall's tau rank correlation.
        More robust to outliers than Pearson-based distance.
    DISTANCE_SPEARMAN : str
        Distance derived from Spearman's rank correlation coefficient.
        Captures monotonic relationships, robust to non-linearity.
    DISTANCE_COV_PEARSON : str
        Distance derived from Pearson covariance matrix.
        Accounts for scale differences between assets.
    DISTANCE_COV_KENDALL : str
        Distance derived from Kendall-based covariance estimate.
        Robust covariance with rank-based correlation.
    DISTANCE_COV_SPEARMAN : str
        Distance derived from Spearman-based covariance estimate.
        Combines rank correlation with variance scaling.
    VARIATION_OF_INFORMATION : str
        Information-theoretic distance based on mutual information.
        $VI(X,Y) = H(X) + H(Y) - 2I(X;Y)$ where $H$ is entropy and $I$ is mutual information.

    Notes
    -----
    Distance metrics must satisfy:
    - Non-negativity: $d(x,y) \\geq 0$
    - Identity: $d(x,x) = 0$
    - Symmetry: $d(x,y) = d(y,x)$
    - Triangle inequality: $d(x,z) \\leq d(x,y) + d(y,z)$

    The standard correlation-to-distance transformation is:

    $$
    d_{ij} = \\sqrt{\\frac{1}{2}(1 - \\rho_{ij})}
    $$

    This ensures $d \\in [0, 1]$ for $\\rho \\in [-1, 1]$.

    Examples
    --------
    >>> from src.num_methods.covariance.cov_corr import Distance_Estimator_Type
    >>> dist_type = Distance_Estimator_Type.DISTANCE_PEARSON
    >>> print(dist_type.value)
    'Distance_Pearson'

    >>> # Get correlation-based distances for HRP
    >>> corr_distances = Distance_Estimator_Type.get_correlation_based()
    >>> print([d.name for d in corr_distances])
    ['DISTANCE_PEARSON', 'DISTANCE_KENDALL', 'DISTANCE_SPEARMAN']

    References
    ----------
    - López de Prado, M. (2016). "Building Diversified Portfolios that Outperform
      Out-of-Sample". Journal of Portfolio Management.
    - Meilă, M. (2007). "Comparing clusterings—an information based distance".
      Journal of Multivariate Analysis.
    - Székely, G. J., & Rizzo, M. L. (2009). "Brownian distance covariance".
      Annals of Applied Statistics.
    """

    # Correlation-Based Distances
    DISTANCE_PEARSON = "Distance_Pearson"
    DISTANCE_KENDALL = "Distance_Kendall"
    DISTANCE_SPEARMAN = "Distance_Spearman"

    # Covariance-Based Distances
    DISTANCE_COV_PEARSON = "Distance_Cov_Pearson"
    DISTANCE_COV_KENDALL = "Distance_Cov_Kendall"
    DISTANCE_COV_SPEARMAN = "Distance_Cov_Spearman"

    # Information-Theoretic Distances
    VARIATION_OF_INFORMATION = "Variation_of_Information"

    @classmethod
    def get_correlation_based(cls) -> list[Distance_Estimator_Type]:
        """Return all correlation-based distance estimators.

        Returns
        -------
        list[Distance_Estimator_Type]
            List of distance estimators derived from correlation coefficients.
        """
        return [  # type: ignore[invalid-return-type]  # pyright: ignore[reportReturnType]
            cls.DISTANCE_PEARSON,
            cls.DISTANCE_KENDALL,
            cls.DISTANCE_SPEARMAN,
        ]

    @classmethod
    def get_covariance_based(cls) -> list[Distance_Estimator_Type]:
        """Return all covariance-based distance estimators.

        Returns
        -------
        list[Distance_Estimator_Type]
            List of distance estimators derived from covariance matrices.
        """
        return [  # type: ignore[invalid-return-type]  # pyright: ignore[reportReturnType]
            cls.DISTANCE_COV_PEARSON,
            cls.DISTANCE_COV_KENDALL,
            cls.DISTANCE_COV_SPEARMAN,
        ]

    @classmethod
    def get_rank_based(cls) -> list[Distance_Estimator_Type]:
        """Return all rank-based (non-parametric) distance estimators.

        These estimators are robust to outliers and non-linear relationships.

        Returns
        -------
        list[Distance_Estimator_Type]
            List of rank-based distance estimators (Kendall, Spearman variants).
        """
        return [  # type: ignore[invalid-return-type]  # pyright: ignore[reportReturnType]
            cls.DISTANCE_KENDALL,
            cls.DISTANCE_SPEARMAN,
            cls.DISTANCE_COV_KENDALL,
            cls.DISTANCE_COV_SPEARMAN,
        ]

    @classmethod
    def get_information_theoretic(cls) -> list[Distance_Estimator_Type]:
        """Return all information-theoretic distance estimators.

        Returns
        -------
        list[Distance_Estimator_Type]
            List of information-theoretic distance estimators.
        """
        return [  # type: ignore[invalid-return-type]  # pyright: ignore[reportReturnType]
            cls.VARIATION_OF_INFORMATION,  # pyright: ignore[reportReturnType]
        ]


@attrs.define(kw_only=True)
class Covariance_Matrix:
    """Covariance matrix estimator using various methods from skfolio.

    This class estimates covariance matrices from return data using different
    statistical methods, with built-in sanity checks to ensure matrix validity.

    Attributes
    ----------
    m_cov_matrix : np.ndarray
        Covariance matrix of shape (m_num_components, m_num_components)
    m_num_components : int
        Number of components (assets) in the covariance matrix
    m_component_names : list[str]
        Names of the components
    m_estimator_type : Covariance_Estimator
        Type of estimator used
    m_num_observations : int
        Number of observations used in estimation

    Examples
    --------
    >>> import polars as pl
    >>> from src.num_methods.covariance.utils_cov_corr import Covariance_Estimator, Covariance_Matrix
    >>> # Create sample returns data
    >>> returns_df = pl.DataFrame(
    ...     {
    ...         "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
    ...         "AAPL": [0.01, -0.02, 0.015],
    ...         "MSFT": [0.02, -0.01, 0.01],
    ...         "GOOG": [0.015, -0.015, 0.02],
    ...     }
    ... )
    >>> # Create covariance matrix with Ledoit-Wolf estimator
    >>> cov_mat = Covariance_Matrix(data_returns=returns_df, estimator=Covariance_Estimator.LEDOIT_WOLF)
    >>> print(cov_mat.m_cov_matrix.shape)
    (3, 3)

    Notes
    -----
    The class performs comprehensive sanity checks:
    - Matrix symmetry
    - Positive semi-definiteness
    - No NaN or infinite values
    - Diagonal elements are positive
    - Correlation values in [-1, 1] range

    The skfolio estimators are mapped as follows:
    - EMPIRICAL -> EmpiricalPrior
    - GERBER -> GerberPrior
    - DENOISING -> DenoiseCovariance
    - DETONING -> DetoneCovariance
    - EXPONENTIALLY_WEIGHTED -> EWCovariance
    - LEDOIT_WOLF -> LedoitWolf
    - ORACLE_APPROXIMATING_SHRINKAGE -> OAS
    - SHRUNK_COVARIANCE -> ShrunkCovariance
    - GRAPHICAL_LASSO_CV -> GraphicalLassoCV
    - IMPLIED_COVARIANCE -> ImpliedCovariance
    """

    # ------------------------------------------------------------------
    # attrs fields — keyword-only, mutable (frozen=False)
    # ------------------------------------------------------------------

    data_returns: pl.DataFrame = attrs.field()
    estimator: Covariance_Estimator = attrs.field()

    m_component_names: list[str] = attrs.field(init=False, default=attrs.Factory(list))
    m_num_components: int = attrs.field(init=False, default=0)
    m_num_observations: int = attrs.field(init=False, default=0)
    m_estimator_type: Covariance_Estimator = attrs.field(init=False, default=Covariance_Estimator.EMPIRICAL)
    m_cov_matrix: np.ndarray = attrs.field(init=False, default=attrs.Factory(lambda: np.empty((0, 0))))

    def __attrs_post_init__(self) -> None:
        """Validate and initialize covariance matrix after attrs construction."""
        # Input validation with early returns
        _logger.info("Initializing Covariance_Matrix")

        # Validate data_returns type
        if not isinstance(self.data_returns, pl.DataFrame):
            error_msg = f"data_returns must be polars DataFrame, got {type(self.data_returns).__name__}"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Validate estimator type
        if not isinstance(self.estimator, Covariance_Estimator):
            error_msg = (
                f"estimator must be Covariance_Estimator enum, got {type(self.estimator).__name__}"
            )
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Configuration validation
        if self.data_returns.is_empty():
            error_msg = "data_returns DataFrame cannot be empty"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        if "Date" not in self.data_returns.columns:
            error_msg = "data_returns must have 'Date' column"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Extract component names (all columns except Date)
        component_names = [col for col in self.data_returns.columns if col != "Date"]

        if len(component_names) < 2:
            error_msg = f"Need at least 2 components, got {len(component_names)}"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Business logic validation - check for sufficient observations
        num_observations = len(self.data_returns)
        num_components = len(component_names)

        if num_observations < num_components:
            error_msg = f"Insufficient observations: {num_observations} observations for {num_components} components"
            _logger.warning(error_msg)

        if num_observations < 3:
            error_msg = f"Need at least 3 observations, got {num_observations}"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Store metadata
        self.m_component_names = component_names
        self.m_num_components = num_components
        self.m_num_observations = num_observations
        self.m_estimator_type = self.estimator

        _logger.info(
            "Processing %s components with %s observations",
            num_components,
            num_observations,
        )
        _logger.info("Using estimator: %s", self.estimator.value)

        # Convert Polars DataFrame to numpy array for skfolio
        # Select only component columns (exclude Date)
        returns_data = self.data_returns.select(component_names)

        # Check for NaN or infinite values in returns
        for col in component_names:
            if returns_data[col].is_null().any():
                error_msg = f"NaN values found in column '{col}'"
                _logger.error(error_msg)
                raise Exception_Validation_Input(error_msg)

            # Convert to numpy to check for infinity
            col_values = returns_data[col].to_numpy()
            if not np.all(np.isfinite(col_values)):
                error_msg = f"Infinite values found in column '{col}'"
                _logger.error(error_msg)
                raise Exception_Validation_Input(error_msg)

        # Convert to numpy array (observations x components)
        returns_numpy = returns_data.to_numpy()

        _logger.debug("Returns array shape: %s", returns_numpy.shape)

        # Estimate covariance matrix using skfolio
        try:
            cov_matrix = self._estimate_covariance(returns=returns_numpy, estimator=self.estimator)
        except Exception as estimation_error:
            error_msg = f"Covariance estimation failed: {estimation_error!s}"
            _logger.error(error_msg)
            raise Exception_Calculation(error_msg) from estimation_error

        # Store covariance matrix
        self.m_cov_matrix = cov_matrix

        _logger.info("Covariance matrix estimated with shape: %s", self.m_cov_matrix.shape)

        # Run sanity checks
        try:
            self.validate_covariance_matrix()
            _logger.info("All sanity checks passed")
        except Exception_Validation_Input as validation_error:
            error_msg = f"Covariance matrix failed sanity checks: {validation_error!s}"
            _logger.error(error_msg)
            raise Exception_Calculation(error_msg) from validation_error

    def _estimate_covariance(
        self, *, returns: np.ndarray, estimator: Covariance_Estimator) -> np.ndarray:
        """Estimate covariance matrix using skfolio estimators.

        Parameters
        ----------
        returns : np.ndarray
            Returns data of shape (n_observations, n_components)
        estimator : Covariance_Estimator
            Type of estimator to use

        Returns
        -------
        np.ndarray
            Estimated covariance matrix of shape (n_components, n_components)

        Raises
        ------
        Exception_Validation_Input
            If estimator type is not recognized
        Exception_Calculation
            If estimation fails
        """
        # Map estimator enum to skfolio class
        estimator_map = {
            Covariance_Estimator.EMPIRICAL: EmpiricalCovariance,
            Covariance_Estimator.GERBER: GerberCovariance,
            Covariance_Estimator.DENOISING: DenoiseCovariance,
            Covariance_Estimator.DETONING: DetoneCovariance,
            Covariance_Estimator.EXPONENTIALLY_WEIGHTED: EWCovariance,
            Covariance_Estimator.LEDOIT_WOLF: LedoitWolf,
            Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE: OAS,
            Covariance_Estimator.SHRUNK_COVARIANCE: ShrunkCovariance,
            Covariance_Estimator.GRAPHICAL_LASSO_CV: GraphicalLassoCV,
            Covariance_Estimator.IMPLIED_COVARIANCE: ImpliedCovariance,
        }

        if estimator not in estimator_map:
            error_msg = f"Unknown estimator type: {estimator.value}"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        # Create estimator instance
        estimator_class = estimator_map[estimator]
        estimator_instance = estimator_class()

        _logger.debug("Created estimator instance: %s", estimator_class.__name__)

        # Fit estimator and get covariance matrix
        try:
            estimator_instance.fit(returns)
            cov_matrix = estimator_instance.covariance_

            _logger.debug("Estimated covariance shape: %s", cov_matrix.shape)

            return cov_matrix

        except Exception as e:  # pragma: no cover
            error_msg = f"Estimator {estimator.value} failed: {e!s}"
            _logger.error(error_msg)
            raise Exception_Calculation(error_msg) from e

    def validate_covariance_matrix(self) -> None:
        """Run comprehensive sanity checks on covariance matrix.

        Raises
        ------
        Exception_Validation_Input
            If any sanity check fails

        Notes
        -----
        Performs the following checks:
        1. Matrix shape is (n, n)
        2. No NaN values
        3. No infinite values
        4. Matrix is symmetric
        5. Diagonal elements are positive
        6. Matrix is positive semi-definite
        7. Implied correlations are in [-1, 1]
        """
        _logger.debug("Running sanity checks on covariance matrix")

        # Check 1: Shape validation
        self._check_matrix_shape()

        # Check 2: No NaN values
        self._check_no_nan()

        # Check 3: No infinite values
        self._check_no_infinite()

        # Check 4: Symmetry
        self._check_symmetry()

        # Check 5: Positive diagonal
        self._check_positive_diagonal()

        # Check 6: Positive semi-definite
        self._check_positive_semidefinite()

        # Check 7: Valid correlations
        self._check_valid_correlations()

        _logger.debug("All sanity checks passed")

    def _check_matrix_shape(self) -> None:
        """Check that covariance matrix has correct shape.

        Raises
        ------
        Exception_Validation_Input
            If matrix shape is incorrect
        """
        expected_shape = (self.m_num_components, self.m_num_components)

        if self.m_cov_matrix.shape != expected_shape:
            error_msg = (
                f"Covariance matrix shape mismatch: "
                f"expected {expected_shape}, got {self.m_cov_matrix.shape}"
            )
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        _logger.debug("Shape check passed: %s", self.m_cov_matrix.shape)

    def _check_no_nan(self) -> None:
        """Check that covariance matrix contains no NaN values.

        Raises
        ------
        Exception_Validation_Input
            If NaN values are found
        """
        if np.any(np.isnan(self.m_cov_matrix)):
            error_msg = "Covariance matrix contains NaN values"
            _logger.error(error_msg)

            # Find location of NaN values for debugging
            nan_locations = np.argwhere(np.isnan(self.m_cov_matrix))
            _logger.error("NaN locations: %s", nan_locations.tolist())

            raise Exception_Validation_Input(error_msg)

        _logger.debug("NaN check passed")

    def _check_no_infinite(self) -> None:
        """Check that covariance matrix contains no infinite values.

        Raises
        ------
        Exception_Validation_Input
            If infinite values are found
        """
        if not np.all(np.isfinite(self.m_cov_matrix)):
            error_msg = "Covariance matrix contains infinite values"
            _logger.error(error_msg)

            # Find location of infinite values for debugging
            inf_locations = np.argwhere(~np.isfinite(self.m_cov_matrix))
            _logger.error("Infinite value locations: %s", inf_locations.tolist())

            raise Exception_Validation_Input(error_msg)

        _logger.debug("Infinity check passed")

    def _check_symmetry(self) -> None:
        """Check that covariance matrix is symmetric.

        Raises
        ------
        Exception_Validation_Input
            If matrix is not symmetric within tolerance

        Notes
        -----
        Uses tolerance of 1e-8 for numerical comparison
        """
        tolerance = 1e-8

        if not np.allclose(self.m_cov_matrix, self.m_cov_matrix.T, atol=tolerance):
            error_msg = "Covariance matrix is not symmetric"
            _logger.error(error_msg)

            # Calculate max asymmetry for debugging
            max_asymmetry = np.max(np.abs(self.m_cov_matrix - self.m_cov_matrix.T))
            _logger.error("Maximum asymmetry: %s", max_asymmetry)

            raise Exception_Validation_Input(error_msg)

        _logger.debug("Symmetry check passed")

    def _check_positive_diagonal(self) -> None:
        """Check that all diagonal elements (variances) are positive.

        Raises
        ------
        Exception_Validation_Input
            If any diagonal element is non-positive
        """
        diagonal = np.diag(self.m_cov_matrix)

        if not np.all(diagonal > 0):
            error_msg = "Covariance matrix has non-positive diagonal elements"
            _logger.error(error_msg)

            # Find which components have non-positive variance
            non_positive_idx = np.where(diagonal <= 0)[0]
            problematic_components = [self.m_component_names[idx] for idx in non_positive_idx]
            _logger.error("Components with non-positive variance: %s", problematic_components)
            _logger.error("Their variances: %s", diagonal[non_positive_idx].tolist())

            raise Exception_Validation_Input(error_msg)

        _logger.debug("Positive diagonal check passed, min variance: %.6e", np.min(diagonal))

    def _check_positive_semidefinite(self) -> None:
        """Check that covariance matrix is positive semi-definite.

        Raises
        ------
        Exception_Validation_Input
            If matrix has negative eigenvalues beyond numerical tolerance

        Notes
        -----
        A matrix is positive semi-definite if all eigenvalues are >= 0.
        Uses tolerance of -1e-8 to account for numerical errors.
        """
        tolerance = -1e-8

        try:
            eigenvalues = np.linalg.eigvals(self.m_cov_matrix)
        except np.linalg.LinAlgError as e:  # pragma: no cover
            error_msg = f"Failed to compute eigenvalues: {e!s}"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg) from e

        min_eigenvalue = np.min(eigenvalues)

        if min_eigenvalue < tolerance:
            error_msg = (
                f"Covariance matrix is not positive semi-definite. "
                f"Minimum eigenvalue: {min_eigenvalue:.6e}"
            )
            _logger.error(error_msg)

            # Count negative eigenvalues
            negative_eigenvalues = eigenvalues[eigenvalues < tolerance]
            _logger.error("Number of negative eigenvalues: %s", len(negative_eigenvalues))
            _logger.error("Negative eigenvalues: %s", negative_eigenvalues.tolist())

            raise Exception_Validation_Input(error_msg)

        _logger.debug("Positive semi-definite check passed, min eigenvalue: %.6e", min_eigenvalue)

    def _check_valid_correlations(self) -> None:
        """Check that implied correlation values are in valid range [-1, 1].

        Raises
        ------
        Exception_Validation_Input
            If any correlation is outside [-1, 1] range

        Notes
        -----
        Computes correlation matrix from covariance matrix:
        corr[i,j] = cov[i,j] / sqrt(cov[i,i] * cov[j,j])
        """
        # Extract standard deviations
        std_dev = np.sqrt(np.diag(self.m_cov_matrix))

        # Compute correlation matrix
        outer_product = np.outer(std_dev, std_dev)
        correlation_matrix = self.m_cov_matrix / outer_product

        # Check diagonal is 1.0
        diagonal = np.diag(correlation_matrix)
        if not np.allclose(diagonal, 1.0, atol=1e-6):  # pragma: no cover
            error_msg = "Correlation matrix diagonal elements are not 1.0"
            _logger.error(error_msg)
            _logger.error("Diagonal values: %s", diagonal.tolist())
            raise Exception_Validation_Input(error_msg)

        # Check all correlations in [-1, 1]
        min_corr = np.min(correlation_matrix)
        max_corr = np.max(correlation_matrix)

        tolerance = 1e-6

        if min_corr < -1.0 - tolerance or max_corr > 1.0 + tolerance:  # pragma: no cover
            error_msg = (
                f"Correlation values outside valid range [-1, 1]: "
                f"min={min_corr:.6f}, max={max_corr:.6f}"
            )
            _logger.error(error_msg)

            # Find problematic correlations
            invalid_mask = (correlation_matrix < -1.0 - tolerance) | (
                correlation_matrix > 1.0 + tolerance
            )
            invalid_locations = np.argwhere(invalid_mask)
            _logger.error("Invalid correlation locations: %s", invalid_locations.tolist())

            raise Exception_Validation_Input(error_msg)

        _logger.debug("Valid correlations check passed, range: [%.6f, %.6f]", min_corr, max_corr)

    def get_covariance_matrix(self) -> np.ndarray:
        """Get a copy of the covariance matrix.

        Returns
        -------
        np.ndarray
            Copy of covariance matrix

        Notes
        -----
        Returns a copy to prevent unintended modifications to internal state
        """
        return self.m_cov_matrix.copy()

    def get_correlation_matrix(self) -> np.ndarray:
        """Compute and return correlation matrix.

        Returns
        -------
        np.ndarray
            Correlation matrix derived from covariance matrix

        Notes
        -----
        Correlation matrix is computed as:
        corr[i,j] = cov[i,j] / sqrt(cov[i,i] * cov[j,j])
        """
        std_dev = np.sqrt(np.diag(self.m_cov_matrix))
        outer_product = np.outer(std_dev, std_dev)

        return self.m_cov_matrix / outer_product

    def get_component_variance(
        self, *, component_name: str) -> float:
        """Get variance for a specific component.

        Parameters
        ----------
        component_name : str
            Name of component

        Returns
        -------
        float
            Variance of the component

        Raises
        ------
        Exception_Validation_Input
            If component name is not found
        """
        if component_name not in self.m_component_names:
            error_msg = (
                f"Component '{component_name}' not found. Available: {self.m_component_names}"
            )
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        idx = self.m_component_names.index(component_name)

        return float(self.m_cov_matrix[idx, idx])

    def get_component_covariance(
        self, *, component_name_1: str, component_name_2: str) -> float:
        """Get covariance between two components.

        Parameters
        ----------
        component_name_1 : str
            Name of first component
        component_name_2 : str
            Name of second component

        Returns
        -------
        float
            Covariance between the two components

        Raises
        ------
        Exception_Validation_Input
            If either component name is not found
        """
        if component_name_1 not in self.m_component_names:
            error_msg = f"Component '{component_name_1}' not found"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        if component_name_2 not in self.m_component_names:
            error_msg = f"Component '{component_name_2}' not found"
            _logger.error(error_msg)
            raise Exception_Validation_Input(error_msg)

        idx_1 = self.m_component_names.index(component_name_1)
        idx_2 = self.m_component_names.index(component_name_2)

        return float(self.m_cov_matrix[idx_1, idx_2])

    def to_polars(self) -> pl.DataFrame:
        """Return the covariance matrix as a labelled ``pl.DataFrame``.

        The first column is named ``"component"`` and contains the component
        names.  Remaining columns are named after each component and contain
        the covariance values for that row.

        Returns
        -------
        pl.DataFrame
            Wide-format covariance matrix with shape
            ``(n_components, n_components + 1)``.

        Examples
        --------
        >>> cov = Covariance_Matrix()
        >>> cov.estimate(data, component_names, Covariance_Estimator.EMPIRICAL)
        >>> df = cov.to_polars()
        >>> df.shape  # (n, n + 1)
        (12, 13)
        """
        cov = self.m_cov_matrix
        names = self.m_component_names
        data: dict[str, list] = {"component": names}
        for j, col_name in enumerate(names):
            data[col_name] = cov[:, j].tolist()
        return pl.DataFrame(data)

    def __str__(self) -> str:
        """Return string representation of covariance matrix.

        Returns
        -------
        str
            String representation
        """
        return (
            f"Covariance_Matrix(estimator={self.m_estimator_type.value}, "
            f"components={self.m_num_components}, "
            f"observations={self.m_num_observations})"
        )

    def __repr__(self) -> str:
        """Return detailed string representation.

        Returns
        -------
        str
            Detailed representation
        """
        return (
            f"Covariance_Matrix(estimator={self.m_estimator_type.value}, "
            f"components={self.m_component_names}, "
            f"observations={self.m_num_observations}, "
            f"shape={self.m_cov_matrix.shape})"
        )
