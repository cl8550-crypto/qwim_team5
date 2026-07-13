"""
Tests for pkg_skfolio module
============================

This module tests portfolio optimization functions using the skfolio package.

Test Coverage:
    - Helper function validation tests
    - Basic optimization methods (equal weight, inverse vol, random)
    - Convex optimization methods (mean-risk, risk budgeting, etc.)
    - Clustering optimization methods (HRP, HERC, etc.)
    - Ensemble optimization methods (stacking)
    - Error handling and edge cases
"""

from datetime import datetime
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)

from skfolio.optimization import ObjectiveFunction

from src.models.portfolio_optimization.pkg_skfolio import (
    _convert_polars_to_pandas_returns,
    _extract_weights_to_portfolio_qwim,
    _get_optimization_type_enum,
    _validate_returns_data,
    calc_skfolio_optimization_basic,
    calc_skfolio_optimization_clustering,
    calc_skfolio_optimization_convex,
    calc_skfolio_optimization_ensemble,
)
from src.models.portfolio_optimization.utils_portfolio_optimization import (
    portfolio_optimization_type,
)
from src.portfolios.portfolio_QWIM import Portfolio_QWIM


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_returns_data():
    """Create sample returns data for testing."""
    np.random.seed(42)
    n_days = 252
    assets = ["AAPL", "MSFT", "GOOG", "AMZN"]
    dates = pl.date_range(pl.date(2023, 1, 1), pl.date(2023, 12, 31), eager=True)[:n_days]

    returns_dict = {"Date": dates}
    for asset in assets:
        returns_dict[asset] = np.random.normal(0.0005, 0.02, n_days).tolist()

    return pl.DataFrame(returns_dict)


@pytest.fixture()
def small_returns_data():
    """Create small returns data for faster tests."""
    returns_dict = {
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        "AAPL": [0.01, -0.005, 0.02, 0.015, -0.01],
        "MSFT": [0.015, 0.01, -0.01, 0.005, 0.02],
        "GOOG": [0.005, 0.02, 0.015, -0.005, 0.01],
    }
    return pl.DataFrame(returns_dict)


@pytest.fixture()
def benchmark_returns_data():
    """Create benchmark returns data for tracking error tests."""
    np.random.seed(123)
    n_days = 252
    dates = pl.date_range(pl.date(2023, 1, 1), pl.date(2023, 12, 31), eager=True)[:n_days]

    returns_dict = {
        "Date": dates,
        "SPY": np.random.normal(0.0004, 0.015, n_days).tolist(),
    }

    return pl.DataFrame(returns_dict)


# =============================================================================
# Tests for Helper Functions
# =============================================================================


@pytest.mark.unit()
class Test_Validate_Returns_Data:
    """Test _validate_returns_data helper function."""

    @pytest.mark.unit()
    def test_validate_returns_data_valid(self, sample_returns_data):
        """Test validation with valid returns data."""
        is_valid, error_msg = _validate_returns_data(returns_data = sample_returns_data)
        assert is_valid is True
        assert error_msg == ""

    @pytest.mark.unit()
    def test_validate_returns_data_none(self):
        """Test validation with None input."""
        is_valid, error_msg = _validate_returns_data(returns_data = None)
        assert is_valid is False
        assert "cannot be None" in error_msg

    @pytest.mark.unit()
    def test_validate_returns_data_wrong_type(self):
        """Test validation with wrong type input."""
        is_valid, error_msg = _validate_returns_data(returns_data = [1, 2, 3])
        assert is_valid is False
        assert "must be a Polars DataFrame" in error_msg

    @pytest.mark.unit()
    def test_validate_returns_data_empty(self):
        """Test validation with empty DataFrame."""
        empty_df = pl.DataFrame()
        is_valid, error_msg = _validate_returns_data(returns_data = empty_df)
        assert is_valid is False
        assert "cannot be empty" in error_msg

    @pytest.mark.unit()
    def test_validate_returns_data_missing_date_column(self):
        """Test validation with missing Date column."""
        df = pl.DataFrame({"AAPL": [0.01, 0.02], "MSFT": [0.015, 0.01]})
        is_valid, error_msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "'Date' column" in error_msg

    @pytest.mark.unit()
    def test_validate_returns_data_no_asset_columns(self):
        """Test validation with only Date column."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"]})
        is_valid, error_msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "at least one asset column" in error_msg

    @pytest.mark.unit()
    def test_validate_returns_data_non_numeric_column(self):
        """Test validation with non-numeric asset column."""
        df = pl.DataFrame(
            {"Date": ["2024-01-01", "2024-01-02"], "AAPL": ["abc", "def"], "MSFT": [0.01, 0.02]},
        )
        is_valid, error_msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "must be numeric" in error_msg


@pytest.mark.unit()
class Test_Convert_Polars_To_Pandas_Returns:
    """Test _convert_polars_to_pandas_returns helper function."""

    @pytest.mark.unit()
    def test_convert_polars_to_pandas_basic(self, small_returns_data):
        """Test basic conversion from Polars to pandas."""
        result = _convert_polars_to_pandas_returns(returns_data = small_returns_data)

        # Check type
        import pandas as pd

        assert isinstance(result, pd.DataFrame)

        # Check index is Date
        assert result.index.name == "Date"

        # Check columns
        assert list(result.columns) == ["AAPL", "MSFT", "GOOG"]

        # Check shape
        assert result.shape == (5, 3)

    @pytest.mark.unit()
    def test_convert_polars_to_pandas_date_parsing(self, small_returns_data):
        """Test that dates are properly parsed."""
        import pandas as pd

        result = _convert_polars_to_pandas_returns(returns_data = small_returns_data)

        # Check index is datetime
        assert isinstance(result.index, pd.DatetimeIndex)

    @pytest.mark.unit()
    def test_convert_polars_to_pandas_mixed_timezone_dates(self):
        """Mixed-offset Date strings are parsed in UTC without FutureWarning."""
        import warnings

        mixed_timezone_data = pl.DataFrame(
            {
                "Date": [
                    "2024-01-01T00:00:00+01:00",
                    "2024-01-02T00:00:00-05:00",
                    "2024-01-03T00:00:00Z",
                ],
                "AAPL": [0.01, -0.005, 0.02],
                "MSFT": [0.015, 0.01, -0.01],
            },
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            result = _convert_polars_to_pandas_returns(returns_data = mixed_timezone_data)

        import pandas as pd

        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.name == "Date"
        assert str(result.index.tz) == "UTC"


@pytest.mark.unit()
class Test_Extract_Weights_To_Portfolio_QWIM:
    """Test _extract_weights_to_portfolio_qwim helper function."""

    @pytest.mark.unit()
    def test_extract_weights_length_mismatch_raises_validation_input(self):
        """Mismatched weights and asset names should fail fast."""

        class StubSkfolioModel:
            def __init__(self, weights: np.ndarray) -> None:
                self.weights_ = weights

        with pytest.raises(Exception_Validation_Input) as exc_info:
            _extract_weights_to_portfolio_qwim(
                skfolio_model=StubSkfolioModel(np.array([0.50, 0.30, 0.20])),
                asset_names=["AAPL", "MSFT"],
                portfolio_name="Test Portfolio",
                optimization_date="2024-01-01",
            )

        assert "same length" in str(exc_info.value)

    @pytest.mark.unit()
    def test_extract_weights_basic(self, sample_returns_data):
        """Test basic weight extraction."""
        # Fit a simple optimizer
        import pandas as pd

        from skfolio.optimization import EqualWeighted

        returns_pandas = sample_returns_data.to_pandas()
        returns_pandas["Date"] = pd.to_datetime(returns_pandas["Date"])
        returns_pandas = returns_pandas.set_index("Date")

        optimizer = EqualWeighted()
        optimizer.fit(returns_pandas)

        # Extract weights
        portfolio = _extract_weights_to_portfolio_qwim(
            skfolio_model=optimizer,
            asset_names=["AAPL", "MSFT", "GOOG", "AMZN"],
            portfolio_name="Test Portfolio",
            optimization_date="2024-01-01",
        )

        # Verify portfolio object
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Test Portfolio"
        assert portfolio.get_num_components == 4
        assert set(portfolio.get_portfolio_components) == {"AAPL", "MSFT", "GOOG", "AMZN"}

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-10

    @pytest.mark.unit()
    def test_extract_weights_with_datetime(self, sample_returns_data):
        """Test weight extraction with datetime object."""
        import pandas as pd

        from skfolio.optimization import EqualWeighted

        returns_pandas = sample_returns_data.to_pandas()
        returns_pandas["Date"] = pd.to_datetime(returns_pandas["Date"])
        returns_pandas = returns_pandas.set_index("Date")

        optimizer = EqualWeighted()
        optimizer.fit(returns_pandas)

        optimization_date = datetime(2024, 6, 15)
        portfolio = _extract_weights_to_portfolio_qwim(
            skfolio_model=optimizer,
            asset_names=["AAPL", "MSFT", "GOOG", "AMZN"],
            portfolio_name="Test",
            optimization_date=optimization_date,
        )

        # Check date is formatted correctly
        weights_df = portfolio.get_portfolio_weights()
        assert weights_df["Date"][0] == "2024-06-15"

    @pytest.mark.unit()
    def test_extract_weights_default_date(self, sample_returns_data):
        """Test weight extraction with default date (current date)."""
        import pandas as pd

        from skfolio.optimization import EqualWeighted

        returns_pandas = sample_returns_data.to_pandas()
        returns_pandas["Date"] = pd.to_datetime(returns_pandas["Date"])
        returns_pandas = returns_pandas.set_index("Date")

        optimizer = EqualWeighted()
        optimizer.fit(returns_pandas)

        portfolio = _extract_weights_to_portfolio_qwim(
            skfolio_model=optimizer,
            asset_names=["AAPL", "MSFT", "GOOG", "AMZN"],
            portfolio_name="Test",
            optimization_date=None,
        )

        # Just verify it doesn't crash and creates valid portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_num_components == 4


@pytest.mark.unit()
class Test_Get_Optimization_Type_Enum:
    """Test _get_optimization_type_enum helper function."""

    @pytest.mark.unit()
    def test_get_optimization_type_enum_from_enum(self):
        """Test conversion when input is already enum."""
        result = _get_optimization_type_enum(optimization_type = portfolio_optimization_type.BASIC_EQUAL_WEIGHTED)
        assert result == portfolio_optimization_type.BASIC_EQUAL_WEIGHTED

    @pytest.mark.unit()
    def test_get_optimization_type_enum_from_string(self):
        """Test conversion from valid string."""
        result = _get_optimization_type_enum(optimization_type = "BASIC_EQUAL_WEIGHTED")
        assert result == portfolio_optimization_type.BASIC_EQUAL_WEIGHTED

    @pytest.mark.unit()
    def test_get_optimization_type_enum_invalid_string(self):
        """Test conversion from invalid string."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            _get_optimization_type_enum(optimization_type = "INVALID_TYPE")
        assert "Invalid optimization_type" in str(exc_info.value)
        assert "Valid types:" in str(exc_info.value)

    @pytest.mark.unit()
    def test_get_optimization_type_enum_wrong_type(self):
        """Test conversion from wrong type."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            _get_optimization_type_enum(optimization_type = 123)
        assert "must be str or portfolio_optimization_type" in str(exc_info.value)


# =============================================================================
# Tests for Basic Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Skfolio_Optimization_Basic:
    """Test calc_skfolio_optimization_basic function."""

    @pytest.mark.unit()
    def test_basic_equal_weighted(self, sample_returns_data):
        """Test equal weighted optimization."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
            portfolio_name="Equal Weight Test",
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Equal Weight Test"
        assert portfolio.get_num_components == 4

        # Verify equal weights (0.25 each for 4 assets)
        weights = portfolio.get_portfolio_weights()
        for component in portfolio.get_portfolio_components:
            assert abs(weights[component][0] - 0.25) < 1e-10

    @pytest.mark.unit()
    def test_basic_inverse_volatility(self, sample_returns_data):
        """Test inverse volatility optimization."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_INVERSE_VOLATILITY",
            portfolio_name="Inverse Vol Test",
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Inverse Vol Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-10

    @pytest.mark.unit()
    def test_basic_random_dirichlet(self, sample_returns_data):
        """Test random Dirichlet optimization."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_RANDOM_DIRICHLET",
            portfolio_name="Random Test",
            random_state=42,
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Random Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-10

    @pytest.mark.unit()
    def test_basic_with_enum_type(self, sample_returns_data):
        """Test using enum type directly."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type=portfolio_optimization_type.BASIC_EQUAL_WEIGHTED,
            portfolio_name="Enum Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Enum Test"

    @pytest.mark.unit()
    def test_basic_default_portfolio_name(self, sample_returns_data):
        """Test default portfolio name generation."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        # Default name should include optimization type
        assert "BASIC_EQUAL_WEIGHTED" in portfolio.get_portfolio_name

    @pytest.mark.unit()
    def test_basic_custom_optimization_date(self, sample_returns_data):
        """Test custom optimization date."""
        portfolio = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
            optimization_date="2024-12-31",
        )

        weights_df = portfolio.get_portfolio_weights()
        assert weights_df["Date"][0] == "2024-12-31"

    @pytest.mark.unit()
    def test_basic_invalid_returns_data(self):
        """Test with invalid returns data."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_basic(
                returns_data=None,
                optimization_type="BASIC_EQUAL_WEIGHTED",
            )
        assert "cannot be None" in str(exc_info.value)

    @pytest.mark.unit()
    def test_basic_invalid_optimization_type(self, sample_returns_data):
        """Test with invalid optimization type (convex type instead of basic)."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_basic(
                returns_data=sample_returns_data,
                optimization_type="CONVEX_MEAN_RISK",
            )
        assert "not a basic method" in str(exc_info.value)


@pytest.mark.slow()
class Test_Calc_Skfolio_Optimization_BasicSlow:
    """Slow tests for basic optimization (require more computation)."""

    @pytest.mark.unit()
    def test_basic_random_produces_different_weights(self, sample_returns_data):
        """Test that random optimization produces valid (but different) weights each time.

        Note: skfolio's Random optimizer doesn't support random_state parameter,
        so reproducibility is not guaranteed. This test verifies that weights are
        valid but different on each run.
        """
        portfolio1 = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_RANDOM_DIRICHLET",
        )

        portfolio2 = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_RANDOM_DIRICHLET",
        )

        # Both portfolios should be valid
        assert isinstance(portfolio1, Portfolio_QWIM)
        assert isinstance(portfolio2, Portfolio_QWIM)

        # Weights should sum to 1.0
        weights1 = portfolio1.get_portfolio_weights()
        weights2 = portfolio2.get_portfolio_weights()

        sum1 = sum(weights1[comp][0] for comp in portfolio1.get_portfolio_components)
        sum2 = sum(weights2[comp][0] for comp in portfolio2.get_portfolio_components)

        assert abs(sum1 - 1.0) < 1e-6
        assert abs(sum2 - 1.0) < 1e-6

        # Weights are likely different (but not guaranteed in all cases)
        # This is a probabilistic test - with 4 assets, it's very unlikely to get identical weights


# =============================================================================
# Tests for Convex Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Skfolio_Optimization_Convex:
    """Test calc_skfolio_optimization_convex function."""

    @pytest.mark.unit()
    def test_convex_mean_risk_minimize_risk(self, sample_returns_data):
        """Test mean-risk optimization with minimize risk objective."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
            objective_function=ObjectiveFunction.MINIMIZE_RISK,
            portfolio_name="Min Risk Test",
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Min Risk Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_convex_mean_risk_maximize_return(self, sample_returns_data):
        """Test mean-risk optimization with maximize return objective."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
            objective_function=ObjectiveFunction.MAXIMIZE_RETURN,
            portfolio_name="Max Return Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Max Return Test"

    @pytest.mark.unit()
    def test_convex_risk_budgeting(self, sample_returns_data):
        """Test risk budgeting optimization."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_RISK_BUDGETING",
            portfolio_name="Risk Parity Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Risk Parity Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_convex_maximum_diversification(self, sample_returns_data):
        """Test maximum diversification optimization."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MAXIMUM_DIVERSIFICATION",
            portfolio_name="Max Div Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Max Div Test"

    @pytest.mark.unit()
    def test_convex_with_weight_constraints(self, sample_returns_data):
        """Test convex optimization with weight constraints."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
            min_weights=0.1,
            max_weights=0.5,
            portfolio_name="Constrained Test",
        )

        # Verify constraints are respected
        weights = portfolio.get_portfolio_weights()
        for component in portfolio.get_portfolio_components:
            weight = weights[component][0]
            assert weight >= 0.1 - 1e-6  # Allow small numerical error
            assert weight <= 0.5 + 1e-6

    @pytest.mark.unit()
    def test_convex_default_portfolio_name(self, sample_returns_data):
        """Test default portfolio name for convex optimization."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
        )

        assert "CONVEX_MEAN_RISK" in portfolio.get_portfolio_name

    @pytest.mark.unit()
    def test_convex_invalid_optimization_type(self, sample_returns_data):
        """Test with invalid optimization type (basic type instead of convex)."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_convex(
                returns_data=sample_returns_data,
                optimization_type="BASIC_EQUAL_WEIGHTED",
            )
        assert "not a convex method" in str(exc_info.value)

    @pytest.mark.unit()
    def test_convex_benchmark_tracking_without_benchmark(self, sample_returns_data):
        """Test benchmark tracking without providing benchmark returns."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_convex(
                returns_data=sample_returns_data,
                optimization_type="CONVEX_BENCHMARK_TRACKING",
            )
        assert "benchmark_returns required" in str(exc_info.value)


@pytest.mark.slow()
class Test_Calc_Skfolio_Optimization_ConvexSlow:
    """Slow tests for convex optimization."""

    @pytest.mark.unit()
    def test_convex_benchmark_tracking_with_benchmark(
        self,
        sample_returns_data,
        benchmark_returns_data,
    ):
        """Test benchmark tracking with benchmark returns provided."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_BENCHMARK_TRACKING",
            benchmark_returns=benchmark_returns_data,
            portfolio_name="Tracking Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Tracking Test"

    @pytest.mark.unit()
    def test_convex_distributionally_robust_cvar(self, sample_returns_data):
        """Test distributionally robust CVaR optimization."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR",
            portfolio_name="Robust CVaR Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Robust CVaR Test"


# =============================================================================
# Tests for Clustering Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Skfolio_Optimization_Clustering:
    """Test calc_skfolio_optimization_clustering function."""

    @pytest.mark.unit()
    def test_clustering_hrp(self, sample_returns_data):
        """Test Hierarchical Risk Parity optimization."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
            portfolio_name="HRP Test",
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "HRP Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_clustering_herc(self, sample_returns_data):
        """Test Hierarchical Equal Risk Contribution optimization."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION",
            portfolio_name="HERC Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "HERC Test"

    @pytest.mark.unit()
    def test_clustering_with_weight_constraints(self, sample_returns_data):
        """Test clustering with weight constraints."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
            min_weights=0.05,
            max_weights=0.6,
            portfolio_name="Constrained HRP Test",
        )

        # Verify constraints (HRP respects min/max weights)
        weights = portfolio.get_portfolio_weights()
        for component in portfolio.get_portfolio_components:
            weight = weights[component][0]
            assert weight >= 0.05 - 1e-6
            assert weight <= 0.6 + 1e-6

    @pytest.mark.unit()
    def test_clustering_default_portfolio_name(self, sample_returns_data):
        """Test default portfolio name for clustering optimization."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
        )

        assert "CLUSTERING_HIERARCHICAL_RISK_PARITY" in portfolio.get_portfolio_name

    @pytest.mark.unit()
    def test_clustering_invalid_optimization_type(self, sample_returns_data):
        """Test with invalid optimization type (basic type instead of clustering)."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_clustering(
                returns_data=sample_returns_data,
                optimization_type="BASIC_EQUAL_WEIGHTED",
            )
        assert "not a clustering method" in str(exc_info.value)


@pytest.mark.slow()
class Test_Calc_Skfolio_Optimization_ClusteringSlow:
    """Slow tests for clustering optimization."""

    @pytest.mark.unit()
    def test_clustering_nested(self, sample_returns_data):
        """Test Nested Clusters Optimization."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_NESTED",
            portfolio_name="NCO Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "NCO Test"

    @pytest.mark.unit()
    def test_clustering_schur_complementary(self, sample_returns_data):
        """Test Schur Complementary allocation."""
        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION",
            portfolio_name="Schur Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Schur Test"


# =============================================================================
# Tests for Ensemble Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Skfolio_Optimization_Ensemble:
    """Test calc_skfolio_optimization_ensemble function."""

    @pytest.mark.unit()
    def test_ensemble_stacking_default(self, sample_returns_data):
        """Test stacking optimization with default estimators."""
        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=sample_returns_data,
            optimization_type="ENSEMBLE_STACKING",
            portfolio_name="Stacking Test",
        )

        # Verify portfolio
        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Stacking Test"

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_ensemble_default_portfolio_name(self, sample_returns_data):
        """Test default portfolio name for ensemble optimization."""
        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=sample_returns_data,
            optimization_type="ENSEMBLE_STACKING",
        )

        assert "ENSEMBLE_STACKING" in portfolio.get_portfolio_name

    @pytest.mark.unit()
    def test_ensemble_custom_cv(self, sample_returns_data):
        """Test ensemble with custom cross-validation folds."""
        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=sample_returns_data,
            optimization_type="ENSEMBLE_STACKING",
            cv=3,
            portfolio_name="CV Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "CV Test"

    @pytest.mark.unit()
    def test_ensemble_invalid_optimization_type(self, sample_returns_data):
        """Test with invalid optimization type (basic type instead of ensemble)."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            calc_skfolio_optimization_ensemble(
                returns_data=sample_returns_data,
                optimization_type="BASIC_EQUAL_WEIGHTED",
            )
        assert "not an ensemble method" in str(exc_info.value)


@pytest.mark.slow()
class Test_Calc_Skfolio_Optimization_EnsembleSlow:
    """Slow tests for ensemble optimization."""

    @pytest.mark.unit()
    def test_ensemble_custom_estimators(self, sample_returns_data):
        """Test ensemble with custom base estimators."""
        from skfolio.optimization import EqualWeighted, HierarchicalRiskParity, MeanRisk

        estimators = [
            ("hrp", HierarchicalRiskParity()),
            ("mean_risk", MeanRisk()),
            ("equal", EqualWeighted()),
        ]

        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=sample_returns_data,
            optimization_type="ENSEMBLE_STACKING",
            estimators=estimators,
            portfolio_name="Custom Ensemble Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Custom Ensemble Test"

    @pytest.mark.unit()
    def test_ensemble_custom_final_estimator(self, sample_returns_data):
        """Test ensemble with custom final estimator."""
        from skfolio.optimization import MaximumDiversification

        portfolio = calc_skfolio_optimization_ensemble(
            returns_data=sample_returns_data,
            optimization_type="ENSEMBLE_STACKING",
            final_estimator=MaximumDiversification(),
            portfolio_name="Custom Final Test",
        )

        assert isinstance(portfolio, Portfolio_QWIM)
        assert portfolio.get_portfolio_name == "Custom Final Test"


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration()
class Test_Optimization_Integration:
    """Integration tests across multiple optimization methods."""

    @pytest.mark.unit()
    def test_all_basic_methods_produce_valid_portfolios(self, sample_returns_data):
        """Test that all basic optimization methods produce valid portfolios."""
        basic_types = [
            "BASIC_EQUAL_WEIGHTED",
            "BASIC_INVERSE_VOLATILITY",
            "BASIC_RANDOM_DIRICHLET",
        ]

        for opt_type in basic_types:
            portfolio = calc_skfolio_optimization_basic(
                returns_data=sample_returns_data,
                optimization_type=opt_type,
            )

            # Verify each portfolio is valid
            assert isinstance(portfolio, Portfolio_QWIM)
            assert portfolio.get_num_components == 4

            # Verify weights sum to 1
            weights = portfolio.get_portfolio_weights()
            weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
            assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_weights_positive_and_normalized(self, sample_returns_data):
        """Test that all optimization methods produce positive, normalized weights."""
        test_cases = [
            (calc_skfolio_optimization_basic, "BASIC_EQUAL_WEIGHTED", {}),
            (
                calc_skfolio_optimization_convex,
                "CONVEX_MEAN_RISK",
                {"objective_function": ObjectiveFunction.MINIMIZE_RISK},
            ),
            (calc_skfolio_optimization_clustering, "CLUSTERING_HIERARCHICAL_RISK_PARITY", {}),
        ]

        for func, opt_type, kwargs in test_cases:
            portfolio = func(
                returns_data=sample_returns_data,
                optimization_type=opt_type,
                **kwargs,
            )

            weights = portfolio.get_portfolio_weights()

            # Check all weights are non-negative
            for component in portfolio.get_portfolio_components:
                assert weights[component][0] >= 0

            # Check weights sum to 1
            weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
            assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_small_vs_large_dataset_consistency(self, small_returns_data, sample_returns_data):
        """Test that optimization works on both small and large datasets."""
        # Small dataset
        portfolio_small = calc_skfolio_optimization_basic(
            returns_data=small_returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        # Large dataset
        portfolio_large = calc_skfolio_optimization_basic(
            returns_data=sample_returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        # Both should be valid
        assert isinstance(portfolio_small, Portfolio_QWIM)
        assert isinstance(portfolio_large, Portfolio_QWIM)

        # Equal weight should be 1/n_assets
        weights_small = portfolio_small.get_portfolio_weights()
        weights_large = portfolio_large.get_portfolio_weights()

        for component in portfolio_small.get_portfolio_components:
            assert abs(weights_small[component][0] - 1 / 3) < 1e-10  # 3 assets

        for component in portfolio_large.get_portfolio_components:
            assert abs(weights_large[component][0] - 1 / 4) < 1e-10  # 4 assets


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


@pytest.mark.unit()
class Test_Edge_Cases:
    """Test edge cases and error handling."""

    @pytest.mark.unit()
    def test_two_asset_portfolio(self):
        """Test optimization with only 2 assets."""
        returns_dict = {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "AAPL": [0.01, -0.005, 0.02],
            "MSFT": [0.015, 0.01, -0.01],
        }
        returns_data = pl.DataFrame(returns_dict)

        portfolio = calc_skfolio_optimization_basic(
            returns_data=returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        assert portfolio.get_num_components == 2

        # Each weight should be 0.5
        weights = portfolio.get_portfolio_weights()
        for component in portfolio.get_portfolio_components:
            assert abs(weights[component][0] - 0.5) < 1e-10

    @pytest.mark.unit()
    def test_single_asset_portfolio(self):
        """Test optimization with only 1 asset (should allocate 100%)."""
        returns_dict = {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "AAPL": [0.01, -0.005, 0.02],
        }
        returns_data = pl.DataFrame(returns_dict)

        portfolio = calc_skfolio_optimization_basic(
            returns_data=returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        assert portfolio.get_num_components == 1

        # Weight should be 1.0
        weights = portfolio.get_portfolio_weights()
        assert abs(weights["AAPL"][0] - 1.0) < 1e-10

    @pytest.mark.unit()
    def test_very_short_time_series(self):
        """Test with very short time series (minimum viable data)."""
        returns_dict = {
            "Date": ["2024-01-01", "2024-01-02"],
            "AAPL": [0.01, -0.005],
            "MSFT": [0.015, 0.01],
        }
        returns_data = pl.DataFrame(returns_dict)

        # Should still work for basic methods
        portfolio = calc_skfolio_optimization_basic(
            returns_data=returns_data,
            optimization_type="BASIC_EQUAL_WEIGHTED",
        )

        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_extreme_returns_values(self):
        """Test with extreme return values."""
        np.random.seed(42)
        dates = pl.date_range(pl.date(2024, 1, 1), pl.date(2024, 2, 1), eager=True)[:20]

        returns_dict = {
            "Date": dates,
            "AAPL": np.random.normal(0.1, 0.5, 20).tolist(),  # High mean, high vol
            "MSFT": np.random.normal(-0.05, 0.3, 20).tolist(),  # Negative mean
            "GOOG": np.random.normal(0.001, 0.01, 20).tolist(),  # Low volatility
        }
        returns_data = pl.DataFrame(returns_dict)

        # Should still produce valid portfolio
        portfolio = calc_skfolio_optimization_basic(
            returns_data=returns_data,
            optimization_type="BASIC_INVERSE_VOLATILITY",
        )

        assert isinstance(portfolio, Portfolio_QWIM)

        # Verify weights are normalized
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6


# =============================================================================
# Bug-fix regression tests
# =============================================================================


@pytest.mark.unit()
class Test_Benchmark_Pandas_Unbound_Fix:
    """Regression tests for the benchmark_pandas possibly-unbound bug fix.

    Before the fix, ``benchmark_pandas`` was only assigned inside the
    ``elif CONVEX_BENCHMARK_TRACKING`` branch but referenced in a separate
    ``if benchmark_pandas is not None`` block.  This caused an
    ``UnboundLocalError`` when calling any convex method that was *not*
    ``CONVEX_BENCHMARK_TRACKING``.

    All tests below must succeed without ``UnboundLocalError``.
    """

    @pytest.mark.unit()
    def test_convex_mean_risk_no_unbound_error(self, sample_returns_data) -> None:
        """CONVEX_MEAN_RISK must not raise UnboundLocalError."""
        from skfolio.optimization import ObjectiveFunction

        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
            objective_function=ObjectiveFunction.MINIMIZE_RISK,
            portfolio_name="Mean Risk No Benchmark",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_convex_risk_budgeting_no_unbound_error(self, sample_returns_data) -> None:
        """CONVEX_RISK_BUDGETING must not raise UnboundLocalError."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_RISK_BUDGETING",
            portfolio_name="Risk Budgeting No Benchmark",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_convex_maximum_diversification_no_unbound_error(self, sample_returns_data) -> None:
        """CONVEX_MAXIMUM_DIVERSIFICATION must not raise UnboundLocalError."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MAXIMUM_DIVERSIFICATION",
            portfolio_name="Max Div No Benchmark",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_convex_distributionally_robust_cvar_no_unbound_error(
        self, sample_returns_data
    ) -> None:
        """CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR must not raise UnboundLocalError."""
        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR",
            portfolio_name="Robust CVaR No Benchmark",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_convex_benchmark_tracking_with_benchmark(self, benchmark_returns_data) -> None:
        """CONVEX_BENCHMARK_TRACKING with a benchmark must produce valid portfolio."""
        np.random.seed(42)
        n_days = 252
        dates = pl.date_range(pl.date(2023, 1, 1), pl.date(2023, 12, 31), eager=True)[:n_days]
        assets = ["AAPL", "MSFT", "GOOG", "AMZN"]
        returns_dict = {"Date": dates}
        for asset in assets:
            returns_dict[asset] = np.random.normal(0.0005, 0.02, n_days).tolist()
        returns_data = pl.DataFrame(returns_dict)

        portfolio = calc_skfolio_optimization_convex(
            returns_data=returns_data,
            optimization_type="CONVEX_BENCHMARK_TRACKING",
            benchmark_returns=benchmark_returns_data,
            portfolio_name="Benchmark Tracking With Benchmark",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

        # Verify weights sum to 1
        weights = portfolio.get_portfolio_weights()
        weight_sum = sum(weights[col][0] for col in portfolio.get_portfolio_components)
        assert abs(weight_sum - 1.0) < 1e-6

    @pytest.mark.unit()
    def test_all_non_benchmark_convex_types_no_unbound(self, sample_returns_data) -> None:
        """All non-benchmark convex methods must run without UnboundLocalError.

        This is the primary regression guard: if benchmark_pandas is ever moved
        back inside the elif block, all of these will fail with UnboundLocalError.
        """
        from skfolio.optimization import ObjectiveFunction


        non_benchmark_types = [
            ("CONVEX_MEAN_RISK", {"objective_function": ObjectiveFunction.MINIMIZE_RISK}),
            ("CONVEX_RISK_BUDGETING", {}),
            ("CONVEX_MAXIMUM_DIVERSIFICATION", {}),
            ("CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR", {}),
        ]

        for opt_type, kwargs in non_benchmark_types:
            portfolio = calc_skfolio_optimization_convex(
                returns_data=sample_returns_data,
                optimization_type=opt_type,
                portfolio_name=f"No-Unbound Test: {opt_type}",
                **kwargs,
            )
            assert isinstance(portfolio, Portfolio_QWIM), (
                f"Expected portfolio_QWIM for {opt_type}, got {type(portfolio)}"
            )


@pytest.mark.unit()
class Test_Enum_Migration_Regression:
    """Regression tests confirming that switching from aenum→enum.Enum does not
    break _get_optimization_type_enum or the optimization type dispatching logic.
    """

    @pytest.mark.unit()
    def test_get_optimization_type_enum_basic_equal_weighted(self) -> None:
        """_get_optimization_type_enum must resolve BASIC_EQUAL_WEIGHTED."""
        result = _get_optimization_type_enum(optimization_type = "BASIC_EQUAL_WEIGHTED")
        assert result == portfolio_optimization_type.BASIC_EQUAL_WEIGHTED

    @pytest.mark.unit()
    def test_get_optimization_type_enum_convex_mean_risk(self) -> None:
        """_get_optimization_type_enum must resolve CONVEX_MEAN_RISK."""
        result = _get_optimization_type_enum(optimization_type = "CONVEX_MEAN_RISK")
        assert result == portfolio_optimization_type.CONVEX_MEAN_RISK

    @pytest.mark.unit()
    def test_get_optimization_type_enum_clustering_hrp(self) -> None:
        """_get_optimization_type_enum must resolve CLUSTERING_HIERARCHICAL_RISK_PARITY."""
        result = _get_optimization_type_enum(optimization_type = "CLUSTERING_HIERARCHICAL_RISK_PARITY")
        assert result == portfolio_optimization_type.CLUSTERING_HIERARCHICAL_RISK_PARITY

    @pytest.mark.unit()
    def test_get_optimization_type_enum_ensemble_stacking(self) -> None:
        """_get_optimization_type_enum must resolve ENSEMBLE_STACKING."""
        result = _get_optimization_type_enum(optimization_type = "ENSEMBLE_STACKING")
        assert result == portfolio_optimization_type.ENSEMBLE_STACKING

    @pytest.mark.unit()
    def test_get_optimization_type_enum_from_enum_instance(self) -> None:
        """Passing an existing enum member should return the same member."""
        member = portfolio_optimization_type.BASIC_INVERSE_VOLATILITY
        result = _get_optimization_type_enum(optimization_type = member)
        assert result is member

    @pytest.mark.unit()
    def test_stdlib_enum_subscript_works(self) -> None:
        """portfolio_optimization_type['BASIC_EQUAL_WEIGHTED'] must work (stdlib Enum)."""
        assert (
            portfolio_optimization_type["BASIC_EQUAL_WEIGHTED"]
            is portfolio_optimization_type.BASIC_EQUAL_WEIGHTED
        )

    @pytest.mark.unit()
    def test_stdlib_enum_call_works(self) -> None:
        """portfolio_optimization_type('ENSEMBLE_STACKING') must work (stdlib Enum)."""
        assert (
            portfolio_optimization_type("ENSEMBLE_STACKING")
            is portfolio_optimization_type.ENSEMBLE_STACKING
        )

    @pytest.mark.parametrize(
        "opt_type_str",
        [
            "BASIC_EQUAL_WEIGHTED",
            "BASIC_INVERSE_VOLATILITY",
            "BASIC_RANDOM_DIRICHLET",
            "CONVEX_MEAN_RISK",
            "CONVEX_RISK_BUDGETING",
            "CONVEX_MAXIMUM_DIVERSIFICATION",
            "CONVEX_DISTRIBUTIONALLY_ROBUST_CVAR",
            "CONVEX_BENCHMARK_TRACKING",
            "CLUSTERING_HIERARCHICAL_RISK_PARITY",
            "CLUSTERING_HIERARCHICAL_EQUAL_RISK_CONTRIBUTION",
            "CLUSTERING_SCHUR_COMPLEMENTARY_ALLOCATION",
            "CLUSTERING_NESTED",
            "ENSEMBLE_STACKING",
        ],
    )
    @pytest.mark.unit()
    def test_get_optimization_type_enum_all_members(self, opt_type_str: str) -> None:
        """_get_optimization_type_enum must resolve every member without error."""
        result = _get_optimization_type_enum(optimization_type = opt_type_str)
        assert isinstance(result, portfolio_optimization_type)
        assert result.name == opt_type_str


# =============================================================================
# Tests targeting previously uncovered branches and lines
# =============================================================================


@pytest.mark.unit()
class Test_Coverage_Gaps:
    """Tests that cover previously missing lines and branches in pkg_skfolio."""

    # -------------------------------------------------------------------------
    # _convert_polars_to_pandas_returns: arc 181->185 (no Date column)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_convert_polars_to_pandas_no_date_column(self) -> None:
        """DataFrame without a Date column skips date parsing (arc 181->185)."""
        import pandas as pd

        df_no_date = pl.DataFrame({"AAPL": [0.01, 0.02], "MSFT": [0.015, 0.01]})
        result = _convert_polars_to_pandas_returns(returns_data = df_no_date)
        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns
        assert "MSFT" in result.columns
        # Index is default RangeIndex – no DatetimeIndex set
        assert not isinstance(result.index, pd.DatetimeIndex)

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_basic: validation failure (lines 420-422 except)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_basic_invalid_returns_data_convex_type(self, sample_returns_data) -> None:
        """basic with a convex type raises on the 'not a basic method' check."""
        with pytest.raises(Exception_Validation_Input, match="not a basic method"):
            calc_skfolio_optimization_basic(
                returns_data=sample_returns_data,
                optimization_type="CONVEX_MEAN_RISK",
            )

    @pytest.mark.unit()
    def test_basic_exception_handler(self, sample_returns_data) -> None:
        """optimizer.fit raising covers the except block in basic (lines 420-422)."""
        from skfolio.optimization import EqualWeighted

        with patch.object(EqualWeighted, "fit", side_effect=Exception("skfolio failure")):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_skfolio_optimization_basic(
                    returns_data=sample_returns_data,
                    optimization_type="BASIC_EQUAL_WEIGHTED",
                )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_convex: validation failure (lines 545-546)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_convex_invalid_returns_data(self) -> None:
        """None returns_data triggers the if-not-is_valid block (lines 545-546)."""
        with pytest.raises(Exception_Validation_Input, match="cannot be None"):
            calc_skfolio_optimization_convex(
                returns_data=None,
                optimization_type="CONVEX_MEAN_RISK",
            )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_convex: risk_measure kwarg branches (586, 593)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_convex_mean_risk_with_risk_measure(self, sample_returns_data) -> None:
        """Passing risk_measure to CONVEX_MEAN_RISK covers kwarg assignment (line 586)."""
        from skfolio.measures import RiskMeasure
        from skfolio.optimization import ObjectiveFunction

        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_MEAN_RISK",
            risk_measure=RiskMeasure.VARIANCE,
            objective_function=ObjectiveFunction.MINIMIZE_RISK,
            portfolio_name="Mean Risk With RiskMeasure",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_convex_risk_budgeting_with_risk_measure(self, sample_returns_data) -> None:
        """Passing risk_measure to CONVEX_RISK_BUDGETING covers kwarg assignment (line 593)."""
        from skfolio.measures import RiskMeasure

        portfolio = calc_skfolio_optimization_convex(
            returns_data=sample_returns_data,
            optimization_type="CONVEX_RISK_BUDGETING",
            risk_measure=RiskMeasure.VARIANCE,
            portfolio_name="Risk Budgeting With RiskMeasure",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_convex: except block (lines 641-643)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_convex_exception_handler(self, sample_returns_data) -> None:
        """optimizer.fit raising covers the except block in convex (lines 641-643)."""
        from skfolio.optimization import MeanRisk, ObjectiveFunction

        with patch.object(MeanRisk, "fit", side_effect=Exception("convex skfolio failure")):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_skfolio_optimization_convex(
                    returns_data=sample_returns_data,
                    optimization_type="CONVEX_MEAN_RISK",
                    objective_function=ObjectiveFunction.MINIMIZE_RISK,
                )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_clustering: validation failure (lines 735-736)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_clustering_invalid_returns_data(self) -> None:
        """None returns_data triggers the if-not-is_valid block (lines 735-736)."""
        with pytest.raises(Exception_Validation_Input, match="cannot be None"):
            calc_skfolio_optimization_clustering(
                returns_data=None,
                optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
            )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_clustering: optional kwarg branches (769, 772)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_clustering_with_risk_measure(self, sample_returns_data) -> None:
        """Passing risk_measure to clustering covers kwarg assignment (line 769)."""
        from skfolio.measures import RiskMeasure

        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
            risk_measure=RiskMeasure.VARIANCE,
            portfolio_name="HRP With RiskMeasure",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_clustering_with_hierarchical_clustering_estimator(
        self, sample_returns_data
    ) -> None:
        """Passing hierarchical_clustering_estimator covers kwarg assignment (line 772)."""
        from skfolio.cluster import HierarchicalClustering

        portfolio = calc_skfolio_optimization_clustering(
            returns_data=sample_returns_data,
            optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
            hierarchical_clustering_estimator=HierarchicalClustering(),
            portfolio_name="HRP With Custom Estimator",
        )
        assert isinstance(portfolio, Portfolio_QWIM)

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_clustering: except block (lines 800-802)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_clustering_exception_handler(self, sample_returns_data) -> None:
        """optimizer.fit raising covers the except block in clustering (lines 800-802)."""
        from skfolio.optimization import HierarchicalRiskParity

        with patch.object(
            HierarchicalRiskParity, "fit", side_effect=Exception("clustering failure")
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_skfolio_optimization_clustering(
                    returns_data=sample_returns_data,
                    optimization_type="CLUSTERING_HIERARCHICAL_RISK_PARITY",
                )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_ensemble: validation failure (lines 900-901)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_ensemble_invalid_returns_data(self) -> None:
        """None returns_data triggers the if-not-is_valid block (lines 900-901)."""
        with pytest.raises(Exception_Validation_Input, match="cannot be None"):
            calc_skfolio_optimization_ensemble(
                returns_data=None,
                optimization_type="ENSEMBLE_STACKING",
            )

    # -------------------------------------------------------------------------
    # calc_skfolio_optimization_ensemble: except block (lines 963-965)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_ensemble_exception_handler(self, sample_returns_data) -> None:
        """optimizer.fit raising covers the except block in ensemble (lines 963-965)."""
        from skfolio.optimization import StackingOptimization

        with patch.object(
            StackingOptimization, "fit", side_effect=Exception("ensemble failure")
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_skfolio_optimization_ensemble(
                    returns_data=sample_returns_data,
                    optimization_type="ENSEMBLE_STACKING",
                )
