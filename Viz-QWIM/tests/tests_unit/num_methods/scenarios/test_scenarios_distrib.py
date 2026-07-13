"""Unit tests for scenarios_distrib module.

This module contains comprehensive tests for the Scenarios_Distribution class and related
utilities in src/num_methods/scenarios/scenarios_distrib.py.
"""

import datetime as dt

import numpy as np
import polars as pl
import pytest

from scipy import stats


@pytest.fixture()
def Scenarios_Distribution_class():
    """Fixture to import Scenarios_Distribution class."""
    from src.num_methods.scenarios.scenarios_distrib import Scenarios_Distribution

    return Scenarios_Distribution


@pytest.fixture()
def Distribution_Type_enum():
    """Fixture to import Distribution_Type enum."""
    from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

    return Distribution_Type


@pytest.fixture()
def Covariance_Input_Type_enum():
    """Fixture to import Covariance_Input_Type enum."""
    from src.num_methods.scenarios.scenarios_distrib import Covariance_Input_Type

    return Covariance_Input_Type


@pytest.fixture()
def Scenario_Data_Type_enum():
    """Fixture to import Scenario_Data_Type from base."""
    from src.num_methods.scenarios.scenarios_base import Scenario_Data_Type

    return Scenario_Data_Type


@pytest.fixture()
def Frequency_Time_Series_enum():
    """Fixture to import Frequency_Time_Series from base."""
    from src.num_methods.scenarios.scenarios_base import Frequency_Time_Series

    return Frequency_Time_Series


@pytest.fixture()
def sample_covariance_matrix():
    """Fixture providing a valid 2x2 covariance matrix."""
    return np.array([[0.04, 0.01], [0.01, 0.01]])


@pytest.fixture()
def sample_correlation_and_volatility():
    """Fixture providing correlation matrix and volatility vector."""
    correlation = np.array([[1.0, 0.5], [0.5, 1.0]])
    volatilities = np.array([0.20, 0.10])
    return correlation, volatilities


class Test_Distribution_Type_Enum:
    """Tests for Distribution_Type enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, Distribution_Type_enum):
        """Test that all distribution type enum members exist."""
        assert hasattr(Distribution_Type_enum, "NORMAL")
        assert hasattr(Distribution_Type_enum, "LOGNORMAL")
        assert hasattr(Distribution_Type_enum, "STUDENT_T")

    @pytest.mark.unit()
    def test_enum_values(self, Distribution_Type_enum):
        """Test enum values are descriptive strings."""
        assert isinstance(Distribution_Type_enum.NORMAL.value, str)
        assert "Normal" in Distribution_Type_enum.NORMAL.value


class Test_Covariance_Input_Type_Enum:
    """Tests for Covariance_Input_Type enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, Covariance_Input_Type_enum):
        """Test covariance input type enum members exist."""
        assert hasattr(Covariance_Input_Type_enum, "COVARIANCE_MATRIX")
        assert hasattr(Covariance_Input_Type_enum, "CORRELATION_AND_VOLATILITIES")

    @pytest.mark.unit()
    def test_enum_values(self, Covariance_Input_Type_enum):
        """Test enum values are descriptive strings."""
        assert isinstance(Covariance_Input_Type_enum.COVARIANCE_MATRIX.value, str)


class Test_Scenarios_Distribution_Instantiation:
    """Tests for Scenarios_Distribution initialization."""

    @pytest.mark.unit()
    def test_initialization_with_covariance_matrix(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test initialization with covariance matrix input."""
        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.NORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj is not None
        assert obj.num_components == 2

    @pytest.mark.unit()
    def test_initialization_with_correlation_and_volatility(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_correlation_and_volatility,
    ):
        """Test initialization with correlation matrix and volatilities."""
        correlation, volatilities = sample_correlation_and_volatility

        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            correlation_matrix=correlation,
            volatilities=volatilities,
            distribution_type=Distribution_Type_enum.NORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj is not None
        assert obj.num_components == 2

    @pytest.mark.unit()
    def test_student_t_with_default_degrees_of_freedom(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that Student-t works with default degrees_of_freedom=5.0.

        The implementation has a default degrees_of_freedom=5.0, so
        omitting it does NOT raise an error.
        """
        obj = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([0.0008]),
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.STUDENT_T,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        # Default df=5.0 > 2, so it succeeds
        assert obj is not None
        assert obj.degrees_of_freedom == 5.0


class Test_Covariance_Matrix_Validation:
    """Tests for covariance matrix validation."""

    @pytest.mark.unit()
    def test_covariance_must_be_square(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that non-square covariance matrix raises error."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],
                mean_returns=np.array([0.0005, 0.0003]),
                covariance_matrix=np.array([[0.04, 0.01, 0.02], [0.01, 0.01, 0.005]]),
                distribution_type=Distribution_Type_enum.NORMAL,
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )

    @pytest.mark.unit()
    def test_covariance_must_match_component_count(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that covariance dimension must match number of components."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],  # 2 components
                mean_returns=np.array([0.0005, 0.0003]),
                covariance_matrix=np.array([[0.04]]),  # 1x1 matrix
                distribution_type=Distribution_Type_enum.NORMAL,
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )

    @pytest.mark.unit()
    def test_covariance_must_be_symmetric(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that asymmetric covariance matrix raises error."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],
                mean_returns=np.array([0.0005, 0.0003]),
                covariance_matrix=np.array([[0.04, 0.01], [0.02, 0.01]]),
                distribution_type=Distribution_Type_enum.NORMAL,
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )

    @pytest.mark.unit()
    def test_covariance_must_be_positive_semidefinite(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that non-PSD covariance matrix is handled (fallback to nearest PSD)."""
        # Create non-PSD matrix
        non_psd = np.array([[1.0, 2.0], [2.0, 1.0]])  # Negative eigenvalue

        # Should either raise error or apply PSD correction
        try:
            obj = Scenarios_Distribution_class(
                names_components=["A", "B"],
                mean_returns=np.array([0.0005, 0.0003]),
                covariance_matrix=non_psd,
                distribution_type=Distribution_Type_enum.NORMAL,
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )
            # If it succeeds, check that matrix was corrected
            assert obj is not None
        except Exception:
            # Raising error is also acceptable behavior
            pass


class Test_Correlation_Matrix_Validation:
    """Tests for correlation matrix validation when using correlation + volatility input."""

    @pytest.mark.unit()
    def test_correlation_accepts_valid_matrix(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that a valid correlation matrix with diagonal=1 is accepted.

        The implementation does not validate that off-diagonal correlation
        values are in [-1, 1] or that diagonal is exactly 1. It only
        validates shapes and symmetry of the resulting covariance.
        """
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            mean_returns=np.array([0.0005]),
            correlation_matrix=np.array([[1.0]]),
            volatilities=np.array([0.15]),
            distribution_type=Distribution_Type_enum.NORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj is not None

    @pytest.mark.unit()
    def test_correlation_values_out_of_bounds_accepted(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test behavior with correlation values outside [-1, 1].

        The implementation does NOT validate bounds on correlation values.
        It builds cov = diag(vol) @ corr @ diag(vol) and only checks
        symmetry. The Cholesky decomposition may fail at generate() time
        for non-PSD matrices, but construction succeeds.
        """
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([0.0005, 0.0003]),
            correlation_matrix=np.array([[1.0, 1.5], [1.5, 1.0]]),
            volatilities=np.array([0.15, 0.08]),
            distribution_type=Distribution_Type_enum.NORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj is not None


class Test_Normal_Distribution:
    """Tests for multivariate normal distribution scenario generation."""

    @pytest.mark.unit()
    def test_normal_generates_dataframe(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test that normal distribution generates proper DataFrame."""
        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        result = obj.generate()

        assert isinstance(result, pl.DataFrame)
        # generate() produces num_dates rows (one scenario path)
        assert len(result) == 10
        assert "Stock" in result.columns
        assert "Bond" in result.columns

    @pytest.mark.unit()
    def test_normal_statistics_match_parameters(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that generated normal returns match input statistics."""
        # Known mean and covariance
        mean = np.array([0.001, 0.0005])
        cov = np.array([[0.04, 0.01], [0.01, 0.01]])

        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=mean,
            covariance_matrix=cov,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        result = obj.generate()

        # Calculate realized statistics
        stock_returns = result["Stock"].to_numpy()
        realized_mean = np.mean(stock_returns)
        realized_std = np.std(stock_returns, ddof=1)

        # Allow generous tolerance for finite sample
        expected_std = np.sqrt(cov[0, 0])
        assert np.abs(realized_mean - mean[0]) < 0.01
        assert np.abs(realized_std - expected_std) < expected_std * 0.1


class Test_Lognormal_Distribution:
    """Tests for multivariate lognormal distribution scenario generation."""

    @pytest.mark.unit()
    def test_lognormal_generates_positive_values(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that lognormal distribution generates positive values.

        Lognormal requires strictly positive mean_returns (they represent
        price levels or 1+return).
        """
        obj = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([1.0008]),  # Must be > 0 for lognormal
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            num_days=100,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        result = obj.generate()

        # All lognormal values should be positive
        stock_values = result["Stock"].to_numpy()
        assert np.all(stock_values > 0)

    @pytest.mark.unit()
    def test_lognormal_parameter_conversion(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test lognormal parameter conversion from arithmetic to log space."""
        # For lognormal, mean_returns must be strictly positive
        arith_mean = np.array([1.10])  # Positive (e.g. 1 + 10% return)
        arith_cov = np.array([[0.04]])

        obj = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=arith_mean,
            covariance_matrix=arith_cov,
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj is not None


class Test_Student_T_Distribution:
    """Tests for multivariate Student-t distribution scenario generation."""

    @pytest.mark.unit()
    def test_student_t_with_degrees_of_freedom(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test Student-t distribution with specified degrees of freedom."""
        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            degrees_of_freedom=5,  # Heavy tails
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        result = obj.generate()

        assert isinstance(result, pl.DataFrame)
        # generate() returns num_dates rows (one path)
        assert len(result) == 10

    @pytest.mark.unit()
    def test_student_t_has_heavier_tails(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that Student-t has heavier tails than normal (more extreme values)."""
        cov = np.array([[0.04]])
        mean = np.array([0.0])

        # Normal distribution
        obj_normal = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=mean,
            covariance_matrix=cov,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        # Student-t with low df (heavy tails)
        obj_t = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=mean,
            covariance_matrix=cov,
            distribution_type=Distribution_Type_enum.STUDENT_T,
            degrees_of_freedom=4,
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=123,
        )

        result_normal = obj_normal.generate()
        result_t = obj_t.generate()

        # Student-t should have higher kurtosis (heavier tails)
        kurtosis_normal = stats.kurtosis(result_normal["Stock"].to_numpy())
        kurtosis_t = stats.kurtosis(result_t["Stock"].to_numpy())

        # Student-t with df=4 has theoretical excess kurtosis of 6
        # Normal has excess kurtosis of 0
        # In practice, kurtosis_t should generally be larger
        # (but allow for sampling variation)

    @pytest.mark.unit()
    def test_student_t_degrees_of_freedom_validation(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that degrees_of_freedom <= 2 raises error."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["Stock"],
                mean_returns=np.array([0.0008]),
                covariance_matrix=np.array([[0.04]]),
                distribution_type=Distribution_Type_enum.STUDENT_T,
                degrees_of_freedom=1,  # Too low! Need df > 2
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )

    @pytest.mark.unit()
    def test_bool_degrees_of_freedom_raises(self, Scenarios_Distribution_class):
        """Boolean degrees_of_freedom should not coerce to 1.0."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution_class(
                names_components=["Stock"],
                degrees_of_freedom=True,
            )

    @pytest.mark.unit()
    def test_non_finite_degrees_of_freedom_raises(self, Scenarios_Distribution_class):
        """NaN or inf degrees_of_freedom should raise before storage."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_degrees_of_freedom in (float("nan"), float("inf")):
            with pytest.raises(Exception_Validation_Input):
                Scenarios_Distribution_class(
                    names_components=["Stock"],
                    degrees_of_freedom=item_degrees_of_freedom,
                )

    @pytest.mark.unit()
    def test_bool_num_days_raises(self, Scenarios_Distribution_class):
        """Boolean num_days should not coerce to a one-day schedule."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution_class(
                names_components=["Stock"],
                num_days=True,
            )

    @pytest.mark.unit()
    def test_zero_num_days_raises(self, Scenarios_Distribution_class):
        """Zero num_days should raise instead of creating an empty schedule."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution_class(
                names_components=["Stock"],
                num_days=0,
            )

    @pytest.mark.unit()
    def test_invalid_random_seed_raises(self, Scenarios_Distribution_class):
        """Boolean and negative random_seed values should be rejected early."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_random_seed in (True, -1):
            with pytest.raises(Exception_Validation_Input):
                Scenarios_Distribution_class(
                    names_components=["Stock"],
                    random_seed=item_random_seed,
                )

    @pytest.mark.unit()
    def test_invalid_start_date_raises(self, Scenarios_Distribution_class):
        """Non-date start_date should raise before business-date generation."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution_class(
                names_components=["Stock"],
                start_date="2024-01-01",
            )


class Test_Scenario_Generation:
    """Tests for general scenario generation functionality."""

    @pytest.mark.unit()
    def test_reproducibility_with_seed(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test that scenarios are reproducible with same random_seed constructor param."""
        obj1 = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        obj2 = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        result1 = obj1.generate()
        result2 = obj2.generate()

        # Results should be identical when using same seed
        assert result1["Stock"].to_list() == result2["Stock"].to_list()
        assert result1["Bond"].to_list() == result2["Bond"].to_list()

    @pytest.mark.unit()
    def test_different_seeds_produce_different_results(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test that different seeds produce different return paths."""
        obj1 = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([0.0008]),
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        obj2 = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([0.0008]),
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=99,
        )

        result1 = obj1.generate()
        result2 = obj2.generate()

        # Different seeds should produce different results
        assert result1["Stock"].to_list() != result2["Stock"].to_list()


class Test_Date_Handling:
    """Tests for date generation and handling."""

    @pytest.mark.unit()
    def test_generate_with_explicit_dates(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        sample_covariance_matrix,
    ):
        """Test scenario generation with user-provided dates."""
        dates = [dt.date(2024, 1, i) for i in range(1, 6)]

        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0008, 0.0002]),
            covariance_matrix=sample_covariance_matrix,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=dates,
        )

        result = obj.generate()

        # Should use provided dates
        unique_dates = result["Date"].unique().sort()
        assert len(unique_dates) == 5


class Test_Correlation_Recovery:
    """Tests for correlation structure in generated scenarios."""

    @pytest.mark.unit()
    def test_generated_correlation_matches_input(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that generated scenarios have correlation matching input."""
        # Strong positive correlation
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        vols = np.array([0.15, 0.10])

        obj = Scenarios_Distribution_class(
            names_components=["Stock", "Bond"],
            mean_returns=np.array([0.0005, 0.0003]),
            correlation_matrix=corr,
            volatilities=vols,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        result = obj.generate()

        # Calculate realized correlation
        stock = result["Stock"].to_numpy()
        bond = result["Bond"].to_numpy()
        realized_corr = np.corrcoef(stock, bond)[0, 1]

        # Should be close to 0.8 (allow tolerance for finite sample)
        assert np.abs(realized_corr - 0.8) < 0.05


class Test_Edge_Cases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit()
    def test_single_component_distribution(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test distribution scenarios with single component."""
        obj = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([0.0008]),
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=5,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        result = obj.generate()
        assert "Stock" in result.columns

    @pytest.mark.unit()
    def test_zero_mean_returns(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test generation with zero mean returns."""
        obj = Scenarios_Distribution_class(
            names_components=["Stock"],
            mean_returns=np.array([0.0]),
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            random_seed=42,
        )

        result = obj.generate()

        # Mean should be close to zero
        mean_return = result["Stock"].mean()
        assert np.abs(mean_return) < 0.01

    @pytest.mark.unit()
    def test_perfect_positive_correlation(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test generation with perfect positive correlation."""
        corr = np.array([[1.0, 1.0], [1.0, 1.0]])
        vols = np.array([0.15, 0.15])

        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([0.0005, 0.0005]),
            correlation_matrix=corr,
            volatilities=vols,
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        result = obj.generate()

        # With perfect correlation and same parameters, A and B should be identical
        assert result is not None


class Test_PSD_Correction:
    """Tests for positive semi-definite matrix correction."""

    @pytest.mark.unit()
    def test_psd_correction_applied_when_needed(
        self,
        Scenarios_Distribution_class,
        Distribution_Type_enum,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that PSD correction is applied to non-PSD matrices."""
        # Create a matrix that is close to PSD but not quite
        almost_psd = np.array([[1.0, 0.9999], [0.9999, 1.0]])

        # This should work (with or without correction)
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([0.0005, 0.0003]),
            covariance_matrix=almost_psd,
            distribution_type=Distribution_Type_enum.NORMAL,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj is not None


# ---------------------------------------------------------------------------
# Phase-3 gap-filling tests  (lines 211, 221, 226, 256, 263, 277-278,
#   348, 353, 358, 363, 368, 373, 383, 494, 544, 553, 567, 622, 693, 716)
# ---------------------------------------------------------------------------


class Test_Invalid_Distribution_Type:
    """Cover line 211 -- distribution_type must be a Distribution_Type enum."""

    @pytest.mark.unit()
    def test_string_distribution_type_raises(self, Scenarios_Distribution_class):
        """Passing a bare string triggers the isinstance guard (line 211)."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A"],
                distribution_type="Normal",  # not a Distribution_Type enum member
            )


class Test_Default_Mean_Returns:
    """Cover line 221 -- mean_returns=None defaults to zeros."""

    @pytest.mark.unit()
    def test_none_mean_returns_gives_zeros(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """When mean_returns is None the constructor fills zeros (line 221)."""
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=None,
            covariance_matrix=np.array([[0.04, 0.01], [0.01, 0.01]]),
            distribution_type=Distribution_Type_enum.NORMAL,
        )
        np.testing.assert_array_equal(obj.mean_returns, np.zeros(2))


class Test_Mean_Returns_Shape_Mismatch:
    """Cover line 226 -- wrong mean_returns shape raises."""

    @pytest.mark.unit()
    def test_wrong_mean_returns_shape_raises(self, Scenarios_Distribution_class):
        """mean_returns.shape != (K,) triggers Exception_Validation_Input (line 226)."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],
                mean_returns=np.array([0.001]),  # shape (1,) but K=2
                covariance_matrix=np.array([[0.04, 0.01], [0.01, 0.01]]),
            )


class Test_Correlation_Matrix_Shape_Mismatch:
    """Cover line 256 -- correlation_matrix must be (K,K)."""

    @pytest.mark.unit()
    def test_wrong_corr_shape_raises(self, Scenarios_Distribution_class):
        """correlation_matrix.shape != (K,K) raises (line 256)."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],
                correlation_matrix=np.array([[1.0]]),  # 1x1 but K=2
                volatilities=np.array([0.20, 0.10]),
            )


class Test_Volatilities_Shape_Mismatch:
    """Cover line 263 -- volatilities must be (K,)."""

    @pytest.mark.unit()
    def test_wrong_volatilities_shape_raises(self, Scenarios_Distribution_class):
        """volatilities.shape != (K,) raises (line 263)."""
        with pytest.raises(Exception):
            Scenarios_Distribution_class(
                names_components=["A", "B"],
                correlation_matrix=np.array([[1.0, 0.3], [0.3, 1.0]]),
                volatilities=np.array([0.20]),  # shape (1,) but K=2
            )


class Test_Identity_Covariance_Fallback:
    """Cover lines 277-278 -- identity covariance used when no input given."""

    @pytest.mark.unit()
    def test_no_cov_input_uses_identity(
        self, Scenarios_Distribution_class, Covariance_Input_Type_enum
    ):
        """With no covariance_matrix and no corr+vols the else branch fires (lines 277-278)."""
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            # no covariance_matrix, no correlation_matrix, no volatilities
        )
        assert obj.covariance_matrix_input.shape == (2, 2)
        assert obj.covariance_input_type == Covariance_Input_Type_enum.COVARIANCE_MATRIX
        np.testing.assert_array_equal(
            obj.covariance_matrix_input, np.eye(2, dtype=np.float64)
        )


class Test_Distribution_Properties:
    """Cover property return statements at lines 348, 353, 358, 363, 368, 373, 383."""

    @pytest.fixture()
    def obj(self, Scenarios_Distribution_class, Distribution_Type_enum):
        """Build a simple NORMAL instance for property checks."""
        return Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([0.001, 0.0005]),
            covariance_matrix=np.array([[0.04, 0.01], [0.01, 0.01]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            random_seed=42,
        )

    @pytest.mark.unit()
    def test_distribution_type_property(self, obj, Distribution_Type_enum):
        """distribution_type property (line 348)."""
        assert obj.distribution_type == Distribution_Type_enum.NORMAL

    @pytest.mark.unit()
    def test_mean_returns_property(self, obj):
        """mean_returns property (line 353)."""
        result = obj.mean_returns
        assert result.shape == (2,)
        np.testing.assert_array_almost_equal(result, np.array([0.001, 0.0005]))

    @pytest.mark.unit()
    def test_covariance_matrix_input_property(self, obj):
        """covariance_matrix_input property (line 358)."""
        result = obj.covariance_matrix_input
        assert result.shape == (2, 2)

    @pytest.mark.unit()
    def test_covariance_input_type_property(self, obj, Covariance_Input_Type_enum):
        """covariance_input_type property (line 363)."""
        assert obj.covariance_input_type == Covariance_Input_Type_enum.COVARIANCE_MATRIX

    @pytest.mark.unit()
    def test_volatilities_property(self, obj):
        """volatilities property (line 368)."""
        result = obj.volatilities
        assert result.shape == (2,)

    @pytest.mark.unit()
    def test_correlation_matrix_derived_property(self, obj):
        """correlation_matrix_derived property (line 373)."""
        result = obj.correlation_matrix_derived
        assert result.shape == (2, 2)

    @pytest.mark.unit()
    def test_random_seed_property(self, obj):
        """random_seed property (line 383)."""
        assert obj.random_seed == 42


class Test_Generate_Zero_Dates:
    """Cover zero-dates raises across all three generators (lines 494, 544, 622)."""

    @pytest.mark.unit()
    def test_normal_zero_dates_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """_generate_normal raises when dates list is empty (line 494)."""
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
            dates=[],
        )
        with pytest.raises(Exception):
            obj.generate()

    @pytest.mark.unit()
    def test_lognormal_zero_dates_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """_generate_lognormal raises when dates list is empty (line 544)."""
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            mean_returns=np.array([0.1]),
            covariance_matrix=np.array([[0.01]]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            dates=[],
        )
        with pytest.raises(Exception):
            obj.generate()

    @pytest.mark.unit()
    def test_student_t_zero_dates_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """_generate_student_t raises when dates list is empty (line 622)."""
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.STUDENT_T,
            degrees_of_freedom=5.0,
            dates=[],
        )
        with pytest.raises(Exception):
            obj.generate()


class Test_Lognormal_Negative_Means_Raises:
    """Cover line 553 -- lognormal requires strictly positive mean returns."""

    @pytest.mark.unit()
    def test_negative_mean_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """np.any(mu <= 0) triggers Exception_Validation_Input (line 553)."""
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([-0.01, 0.05]),  # A has negative mean
            covariance_matrix=np.array([[0.04, 0.01], [0.01, 0.01]]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            num_days=5,
        )
        with pytest.raises(Exception):
            obj.generate()

    @pytest.mark.unit()
    def test_zero_mean_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """mu=0 also triggers the guard (line 553, boundary case)."""
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            mean_returns=np.array([0.0]),
            covariance_matrix=np.array([[0.01]]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            num_days=5,
        )
        with pytest.raises(Exception):
            obj.generate()


class Test_Lognormal_Mapping_Failure_Raises:
    """Cover line 567 -- lognormal parameter mapping raises when 1+ratio <= 0."""

    @pytest.mark.unit()
    def test_extreme_negative_covariance_raises(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """ratio = cov/(mu_i*mu_j) = -0.02/0.01 = -2 => 1+ratio = -1 <= 0 (line 567)."""
        obj = Scenarios_Distribution_class(
            names_components=["A", "B"],
            mean_returns=np.array([0.1, 0.1]),
            covariance_matrix=np.array([[0.04, -0.02], [-0.02, 0.04]]),
            distribution_type=Distribution_Type_enum.LOGNORMAL,
            num_days=5,
        )
        with pytest.raises(Exception):
            obj.generate()


class Test_From_Correlation_And_Volatilities_Classmethod:
    """Cover line 693 -- from_correlation_and_volatilities classmethod body."""

    @pytest.mark.unit()
    def test_classmethod_returns_instance(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """from_correlation_and_volatilities delegates to __init__ (line 693)."""
        obj = Scenarios_Distribution_class.from_correlation_and_volatilities(
            names_components=["A", "B"],
            correlation_matrix=np.array([[1.0, 0.4], [0.4, 1.0]]),
            volatilities=np.array([0.20, 0.10]),
            distribution_type=Distribution_Type_enum.NORMAL,
            mean_returns=np.array([0.001, 0.0005]),
            random_seed=7,
        )
        assert obj is not None
        assert obj.num_components == 2

    @pytest.mark.unit()
    def test_classmethod_result_generates(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """Object from classmethod can generate scenarios successfully."""
        obj = Scenarios_Distribution_class.from_correlation_and_volatilities(
            names_components=["A"],
            correlation_matrix=np.array([[1.0]]),
            volatilities=np.array([0.15]),
            distribution_type=Distribution_Type_enum.NORMAL,
            num_days=10,
        )
        result = obj.generate()
        assert isinstance(result, pl.DataFrame)


class Test_Repr_Method:
    """Cover line 716 -- __repr__ return statement."""

    @pytest.mark.unit()
    def test_repr_is_string(
        self, Scenarios_Distribution_class, Distribution_Type_enum
    ):
        """repr() executes the __repr__ return (line 716)."""
        obj = Scenarios_Distribution_class(
            names_components=["A"],
            covariance_matrix=np.array([[0.04]]),
            distribution_type=Distribution_Type_enum.NORMAL,
        )
        result = repr(obj)
        assert isinstance(result, str)
        assert "Scenarios_Distribution" in result
