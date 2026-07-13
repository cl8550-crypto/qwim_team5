"""Tests for optimalportfolios package wrapper functions.

This module contains comprehensive tests for all functions in
pkg_optimalportfolios.py, including the 3 (now 5) helpers and all 7 main
optimization functions.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)

from src.models.portfolio_optimization.pkg_optimalportfolios import (
    _build_constraints,
    _compute_covar_and_means,
    _convert_polars_to_numpy_returns,
    _extract_weights_to_portfolio_qwim,
    _validate_returns_data,
    calc_optimalportfolios_budgeted_risk_contribution,
    calc_optimalportfolios_maximum_cara_gaussian_mixture,
    calc_optimalportfolios_maximum_diversification,
    calc_optimalportfolios_maximum_quadratic_utility,
    calc_optimalportfolios_maximum_sharpe_ratio,
    calc_optimalportfolios_minimum_variance,
    calc_optimalportfolios_tracking_error_minimization,
)
from src.portfolios.portfolio_QWIM import Portfolio_QWIM


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_returns_data():
    """Create sample returns DataFrame (200 daily obs, 4 assets, reproducible)."""
    rng = np.random.default_rng(42)
    n_days = 200
    assets = ["AAPL", "MSFT", "GOOG", "AMZN"]

    mean_returns = np.array([0.0005, 0.0007, 0.0004, 0.0006])
    vols = np.array([0.018, 0.015, 0.020, 0.017])
    corr = np.array(
        [
            [1.00, 0.60, 0.40, 0.50],
            [0.60, 1.00, 0.50, 0.45],
            [0.40, 0.50, 1.00, 0.35],
            [0.50, 0.45, 0.35, 1.00],
        ]
    )
    cov = np.outer(vols, vols) * corr
    returns = rng.multivariate_normal(mean_returns, cov, n_days)

    dates = (
        pl.date_range(
            start=datetime(2023, 1, 1),
            end=datetime(2024, 12, 31),
            interval="1d",
            eager=True,
        )
        .head(n_days)
        .cast(pl.Utf8)
    )
    data = {"Date": dates}
    for i, asset in enumerate(assets):
        data[asset] = returns[:, i].tolist()

    return pl.DataFrame(data)


@pytest.fixture()
def small_returns_data():
    """Create small 5-row returns DataFrame for quick tests."""
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "AAPL": [0.01, -0.005, 0.02, 0.015, -0.01],
            "MSFT": [0.015, 0.01, -0.01, 0.005, 0.02],
            "GOOG": [0.005, 0.02, 0.015, -0.015, 0.01],
        }
    )


@pytest.fixture()
def three_asset_returns(sample_returns_data):
    """3-asset subset for faster optimization tests."""
    return sample_returns_data.select(["Date", "AAPL", "MSFT", "GOOG"])


@pytest.fixture()
def benchmark_returns(sample_returns_data):
    """Benchmark returns DataFrame aligned with sample_returns_data."""
    rng = np.random.default_rng(99)
    n = len(sample_returns_data)
    benchmark = rng.normal(0.0004, 0.012, n).tolist()
    return pl.DataFrame(
        {
            "Date": sample_returns_data["Date"].to_list(),
            "SPY": benchmark,
        }
    )


# =============================================================================
# Shared assertion helper
# =============================================================================

ASSETS_3 = ["AAPL", "MSFT", "GOOG"]
ASSETS_4 = ["AAPL", "MSFT", "GOOG", "AMZN"]


def _check_portfolio(
    port: Portfolio_QWIM,
    assets: list[str],
    name_fragment: str | None = None,
) -> None:
    """Assert portfolio_QWIM invariants: type, components, weights sum to 1."""
    assert isinstance(port, Portfolio_QWIM), f"Expected portfolio_QWIM, got {type(port)}"
    assert set(port.get_portfolio_components) == set(assets)
    w_df = port.get_portfolio_weights()
    weights_sum = sum(float(w_df[a][0]) for a in assets)
    assert weights_sum == pytest.approx(1.0, abs=1e-4), (
        f"Weights sum {weights_sum:.8f} not close to 1.0"
    )
    if name_fragment:
        assert name_fragment.lower() in port.get_portfolio_name.lower()


# =============================================================================
# Helper: _validate_returns_data
# =============================================================================


@pytest.mark.unit()
class Test_Validate_Returns_Data:
    """Tests for _validate_returns_data."""

    @pytest.mark.unit()
    def test_valid_data_returns_true(self, sample_returns_data):
        """Test that valid data returns true."""
        is_valid, msg = _validate_returns_data(returns_data = sample_returns_data)
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_input(self):
        """Test that none input."""
        is_valid, msg = _validate_returns_data(returns_data = None)
        assert is_valid is False
        assert "None" in msg

    @pytest.mark.unit()
    def test_wrong_type(self):
        """Test that wrong type."""
        is_valid, msg = _validate_returns_data(returns_data = [1, 2, 3])
        assert is_valid is False
        assert "Polars DataFrame" in msg

    @pytest.mark.unit()
    def test_empty_dataframe(self):
        """Test that empty dataframe."""
        df = pl.DataFrame({"Date": [], "AAPL": []})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "empty" in msg

    @pytest.mark.unit()
    def test_missing_date_column(self):
        """Test that missing date column."""
        df = pl.DataFrame({"AAPL": [0.01], "MSFT": [0.02]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "Date" in msg

    @pytest.mark.unit()
    def test_no_asset_columns(self):
        """Test that no asset columns."""
        df = pl.DataFrame({"Date": ["2024-01-01"]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "asset column" in msg

    @pytest.mark.unit()
    def test_non_numeric_column(self):
        """Test that non numeric column."""
        df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "AAPL": [0.01, 0.02],
                "MSFT": ["up", "down"],
            }
        )
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "numeric" in msg

    @pytest.mark.unit()
    def test_single_asset_valid(self):
        """Test that single asset valid."""
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-01-02"], "AAPL": [0.01, -0.01]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is True


# =============================================================================
# Helper: _convert_polars_to_numpy_returns
# =============================================================================


@pytest.mark.unit()
class Test_Convert_Polars_To_Numpy_Returns:
    """Tests for _convert_polars_to_numpy_returns."""

    @pytest.mark.unit()
    def test_basic_shape(self, sample_returns_data):
        """Test that basic shape."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (len(sample_returns_data), 4)

    @pytest.mark.unit()
    def test_date_column_excluded(self, small_returns_data):
        """Test that date column excluded."""
        arr = _convert_polars_to_numpy_returns(returns_data = small_returns_data)
        assert arr.shape == (5, 3)

    @pytest.mark.unit()
    def test_values_preserved(self, small_returns_data):
        """Test that values preserved."""
        arr = _convert_polars_to_numpy_returns(returns_data = small_returns_data)
        np.testing.assert_almost_equal(arr[0, 0], 0.01)
        np.testing.assert_almost_equal(arr[0, 1], 0.015)

    @pytest.mark.unit()
    def test_column_order_preserved(self):
        """Test that column order preserved."""
        df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "ZZZ": [0.01, 0.02],
                "AAA": [0.03, 0.04],
                "MMM": [0.05, 0.06],
            }
        )
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        np.testing.assert_almost_equal(arr[0, 0], 0.01)

    @pytest.mark.unit()
    def test_dtype_is_float64(self, sample_returns_data):
        """Test that dtype is float64."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        assert arr.dtype == np.float64

    @pytest.mark.unit()
    def test_large_dataset(self):
        """Test that large dataset."""
        rng = np.random.default_rng(0)
        n, k = 1000, 10
        dates = pl.date_range(
            start=datetime(2020, 1, 1),
            end=datetime(2025, 12, 31),
            interval="1d",
            eager=True,
        ).head(n).cast(pl.Utf8)
        data = {"Date": dates}
        for i in range(k):
            data[f"A{i}"] = rng.normal(0.001, 0.02, n).tolist()
        df = pl.DataFrame(data)
        arr = _convert_polars_to_numpy_returns(returns_data = df)
        assert arr.shape == (n, k)


# =============================================================================
# Helper: _compute_covar_and_means
# =============================================================================


@pytest.mark.unit()
class Test_Compute_Covar_And_Means:
    """Tests for _compute_covar_and_means."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("returns_array", "expected_fragment"),
        [
            (np.array([0.01, -0.02, 0.03]), "2-D NumPy array"),
            (np.empty((0, 3)), "at least 2 observations"),
        ],
    )
    def test_invalid_array_shapes_raise_validation_input(
        self,
        returns_array: np.ndarray,
        expected_fragment: str,
    ):
        """Invalid array shapes should fail before NumPy emits NaN warnings."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            _compute_covar_and_means(returns_array = returns_array)

        assert expected_fragment in str(exc_info.value)

    @pytest.mark.unit()
    def test_non_numpy_input_raises_validation_input(self):
        """Non-NumPy input should fail at the first defensive type boundary."""
        returns_list = [[0.01], [-0.02], [0.03]]

        with pytest.raises(Exception_Validation_Input) as exc_info:
            _compute_covar_and_means(returns_array = returns_list)  # type: ignore[arg-type]

        assert "NumPy array" in str(exc_info.value)

    @pytest.mark.unit()
    def test_returns_tuple_of_ndarrays(self, sample_returns_data):
        """Test that returns tuple of ndarrays."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        covar, means = _compute_covar_and_means(returns_array = arr)
        assert isinstance(covar, np.ndarray)
        assert isinstance(means, np.ndarray)

    @pytest.mark.unit()
    def test_covar_shape(self, sample_returns_data):
        """Test that covar shape."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        covar, means = _compute_covar_and_means(returns_array = arr)
        n = arr.shape[1]
        assert covar.shape == (n, n)
        assert means.shape == (n,)

    @pytest.mark.unit()
    def test_covar_symmetric(self, sample_returns_data):
        """Test that covar symmetric."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        covar, _ = _compute_covar_and_means(returns_array = arr)
        np.testing.assert_array_almost_equal(covar, covar.T)

    @pytest.mark.unit()
    def test_covar_positive_semidefinite(self, sample_returns_data):
        """Test that covar positive semidefinite."""
        arr = _convert_polars_to_numpy_returns(returns_data = sample_returns_data)
        covar, _ = _compute_covar_and_means(returns_array = arr)
        eigenvalues = np.linalg.eigvalsh(covar)
        assert np.all(eigenvalues >= -1e-10)


# =============================================================================
# Helper: _build_constraints
# =============================================================================


@pytest.mark.unit()
class Test_Build_Constraints:
    """Tests for _build_constraints."""

    @pytest.mark.unit()
    def test_default_creates_constraints_object(self):
        """Test that default creates constraints object."""
        from optimalportfolios import Constraints

        c = _build_constraints(asset_names = ["AAPL", "MSFT", "GOOG"])
        assert isinstance(c, Constraints)

    @pytest.mark.unit()
    def test_no_min_max_is_none(self):
        """Test that no min max is none."""
        c = _build_constraints(asset_names = ["AAPL", "MSFT"])
        assert c.min_weights is None
        assert c.max_weights is None

    @pytest.mark.unit()
    def test_min_weight_scalar_applied(self):
        """Test that min weight scalar applied."""
        c = _build_constraints(asset_names = ["AAPL", "MSFT"], min_w_scalar=0.05)
        assert c.min_weights is not None
        assert float(c.min_weights["AAPL"]) == pytest.approx(0.05)
        assert float(c.min_weights["MSFT"]) == pytest.approx(0.05)

    @pytest.mark.unit()
    def test_max_weight_scalar_applied(self):
        """Test that max weight scalar applied."""
        c = _build_constraints(asset_names = ["AAPL", "MSFT", "GOOG"], max_w_scalar=0.40)
        assert c.max_weights is not None
        assert float(c.max_weights["GOOG"]) == pytest.approx(0.40)


# =============================================================================
# Helper: _extract_weights_to_portfolio_qwim
# =============================================================================


@pytest.mark.unit()
class Test_Extract_Weights_To_Portfolio_QWIM:
    """Tests for _extract_weights_to_portfolio_qwim."""

    @pytest.mark.unit()
    def test_basic_extraction(self):
        """Test that basic extraction."""
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        assets = ["AAPL", "MSFT", "GOOG", "AMZN"]
        port = _extract_weights_to_portfolio_qwim(weights=weights, asset_names=assets, portfolio_name="Test", optimization_date="2024-01-01")
        assert isinstance(port, Portfolio_QWIM)
        assert port.get_portfolio_name == "Test"
        assert port.get_num_components == 4

    @pytest.mark.unit()
    def test_specific_weight_value(self):
        """Test that specific weight value."""
        weights = np.array([0.3, 0.4, 0.3])
        assets = ["AAPL", "MSFT", "GOOG"]
        port = _extract_weights_to_portfolio_qwim(weights=weights, asset_names=assets, portfolio_name="Test", optimization_date="2024-01-01")
        w_df = port.get_portfolio_weights()
        assert float(w_df["MSFT"][0]) == pytest.approx(0.4, abs=1e-6)

    @pytest.mark.unit()
    def test_default_date_no_crash(self):
        """Test that default date no crash."""
        weights = np.array([0.5, 0.5])
        port = _extract_weights_to_portfolio_qwim(weights=weights, asset_names=["A", "B"], portfolio_name="Test")
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_datetime_object_as_date(self):
        """Test that datetime object as date."""
        weights = np.array([0.6, 0.4])
        opt_date = datetime(2024, 6, 15)
        port = _extract_weights_to_portfolio_qwim(weights=weights, asset_names=["A", "B"], portfolio_name="Test", optimization_date=opt_date)
        w_df = port.get_portfolio_weights()
        assert "2024-06-15" in str(w_df["Date"][0])

    @pytest.mark.unit()
    def test_components_match(self):
        """Test that components match."""
        assets = ["AAPL", "MSFT", "GOOG"]
        port = _extract_weights_to_portfolio_qwim(
            weights=np.array([0.33, 0.33, 0.34]), asset_names=assets, portfolio_name="Test", optimization_date="2024-01-01"
        )
        assert set(port.get_portfolio_components) == set(assets)

    @pytest.mark.unit()
    def test_weight_length_mismatch_raises_validation_input(self):
        """Mismatched weight and asset lengths should fail fast."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            _extract_weights_to_portfolio_qwim(
                weights=np.array([0.50, 0.30, 0.20]),
                asset_names=["AAPL", "MSFT"],
                portfolio_name="Test",
                optimization_date="2024-01-01",
            )

        assert "same length" in str(exc_info.value)


# =============================================================================
# Main Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Minimum_Variance:
    """Tests for calc_optimalportfolios_minimum_variance."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, three_asset_returns):
        """Test that returns valid portfolio."""
        port = calc_optimalportfolios_minimum_variance(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "variance")

    @pytest.mark.unit()
    def test_all_weights_non_negative(self, three_asset_returns):
        """Test that all weights non negative."""
        port = calc_optimalportfolios_minimum_variance(returns_data = three_asset_returns)
        w_df = port.get_portfolio_weights()
        for a in ASSETS_3:
            assert float(w_df[a][0]) >= -1e-6

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, three_asset_returns):
        """Test that custom portfolio name."""
        port = calc_optimalportfolios_minimum_variance(
            returns_data = three_asset_returns, portfolio_name="My Min-Var"
        )
        assert port.get_portfolio_name == "My Min-Var"

    @pytest.mark.unit()
    def test_custom_optimization_date(self, three_asset_returns):
        """Test that custom optimization date."""
        port = calc_optimalportfolios_minimum_variance(
            returns_data = three_asset_returns, optimization_date="2024-06-01"
        )
        w_df = port.get_portfolio_weights()
        assert "2024-06-01" in str(w_df["Date"][0])

    @pytest.mark.unit()
    def test_four_assets(self, sample_returns_data):
        """Test that four assets."""
        port = calc_optimalportfolios_minimum_variance(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS_4)

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_minimum_variance(returns_data = None)

    @pytest.mark.unit()
    def test_invalid_non_dataframe_raises(self):
        """Test that invalid non dataframe raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_minimum_variance(returns_data = {"a": [1, 2]})


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Maximum_Quadratic_Utility:
    """Tests for calc_optimalportfolios_maximum_quadratic_utility."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, three_asset_returns):
        """Test that returns valid portfolio."""
        port = calc_optimalportfolios_maximum_quadratic_utility(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "quadratic")

    @pytest.mark.unit()
    def test_custom_risk_aversion(self, three_asset_returns):
        """Test that custom risk aversion."""
        port = calc_optimalportfolios_maximum_quadratic_utility(
            returns_data = three_asset_returns, risk_aversion=5.0
        )
        _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_high_vs_low_risk_aversion_differ(self, three_asset_returns):
        """Test that high vs low risk aversion differ."""
        port_low = calc_optimalportfolios_maximum_quadratic_utility(
            returns_data = three_asset_returns, risk_aversion=1.0
        )
        port_high = calc_optimalportfolios_maximum_quadratic_utility(
            returns_data = three_asset_returns, risk_aversion=10.0
        )
        w_low = port_low.get_portfolio_weights()
        w_high = port_high.get_portfolio_weights()
        diffs = [abs(float(w_low[a][0]) - float(w_high[a][0])) for a in ASSETS_3]
        assert sum(diffs) > 0.001

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_maximum_quadratic_utility(returns_data = None)


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Budgeted_Risk_Contribution:
    """Tests for calc_optimalportfolios_budgeted_risk_contribution."""

    @pytest.mark.unit()
    def test_equal_risk_parity(self, three_asset_returns):
        """Test that equal risk parity."""
        port = calc_optimalportfolios_budgeted_risk_contribution(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "risk")

    @pytest.mark.unit()
    def test_custom_risk_budgets(self, three_asset_returns):
        """Test that custom risk budgets."""
        budgets = {"AAPL": 0.5, "MSFT": 0.25, "GOOG": 0.25}
        port = calc_optimalportfolios_budgeted_risk_contribution(
            returns_data = three_asset_returns, risk_budgets=budgets
        )
        _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_budgeted_risk_contribution(returns_data = None)


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Maximum_Diversification:
    """Tests for calc_optimalportfolios_maximum_diversification."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, three_asset_returns):
        """Test that returns valid portfolio."""
        port = calc_optimalportfolios_maximum_diversification(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "diversification")

    @pytest.mark.unit()
    def test_weights_non_negative(self, three_asset_returns):
        """Test that weights non negative."""
        port = calc_optimalportfolios_maximum_diversification(returns_data = three_asset_returns)
        w_df = port.get_portfolio_weights()
        for a in ASSETS_3:
            assert float(w_df[a][0]) >= -1e-6

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_maximum_diversification(returns_data = None)


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Maximum_Sharpe_Ratio:
    """Tests for calc_optimalportfolios_maximum_sharpe_ratio."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, three_asset_returns):
        """Test that returns valid portfolio."""
        port = calc_optimalportfolios_maximum_sharpe_ratio(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "sharpe")

    @pytest.mark.unit()
    def test_custom_risk_free_rate(self, three_asset_returns):
        """Test that custom risk free rate."""
        # Use small daily risk-free rate (0.02% per day ≈ 5% annualized)
        port = calc_optimalportfolios_maximum_sharpe_ratio(
            returns_data = three_asset_returns, risk_free_rate=0.0001
        )
        _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_high_vs_low_risk_free_rate_differ(self, three_asset_returns):
        """Test that high vs low risk free rate differ."""
        port_low = calc_optimalportfolios_maximum_sharpe_ratio(
            returns_data = three_asset_returns, risk_free_rate=0.0
        )
        port_high = calc_optimalportfolios_maximum_sharpe_ratio(
            returns_data = three_asset_returns, risk_free_rate=0.0003
        )
        _check_portfolio(port_low, ASSETS_3)
        _check_portfolio(port_high, ASSETS_3)

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_maximum_sharpe_ratio(returns_data = None)


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Maximum_CARA_Gaussian_Mixture:
    """Tests for calc_optimalportfolios_maximum_cara_gaussian_mixture."""

    @pytest.mark.unit()
    def test_default_parameters(self, three_asset_returns):
        """Test that default parameters."""
        port = calc_optimalportfolios_maximum_cara_gaussian_mixture(returns_data = three_asset_returns)
        _check_portfolio(port, ASSETS_3, "cara")

    @pytest.mark.unit()
    def test_custom_n_components(self, three_asset_returns):
        """Test that custom n components."""
        port = calc_optimalportfolios_maximum_cara_gaussian_mixture(
            returns_data = three_asset_returns, n_components=3
        )
        _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_custom_risk_aversion(self, three_asset_returns):
        """Test that custom risk aversion."""
        port = calc_optimalportfolios_maximum_cara_gaussian_mixture(
            returns_data = three_asset_returns, risk_aversion=2.0
        )
        _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_invalid_none_raises(self):
        """Test that invalid none raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_maximum_cara_gaussian_mixture(returns_data = None)


@pytest.mark.unit()
class Test_Calc_Optimalportfolios_Tracking_Error_Minimization:
    """Tests for calc_optimalportfolios_tracking_error_minimization."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, three_asset_returns, benchmark_returns):
        """Test that returns valid portfolio."""
        port = calc_optimalportfolios_tracking_error_minimization(
            returns_data = three_asset_returns, benchmark_returns = benchmark_returns
        )
        _check_portfolio(port, ASSETS_3, "tracking")

    @pytest.mark.unit()
    def test_weights_non_negative(self, three_asset_returns, benchmark_returns):
        """Test that weights non negative."""
        port = calc_optimalportfolios_tracking_error_minimization(
            returns_data = three_asset_returns, benchmark_returns = benchmark_returns
        )
        w_df = port.get_portfolio_weights()
        for a in ASSETS_3:
            assert float(w_df[a][0]) >= -1e-6

    @pytest.mark.unit()
    def test_invalid_returns_raises(self, benchmark_returns):
        """Test that invalid returns raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_optimalportfolios_tracking_error_minimization(returns_data = None, benchmark_returns = benchmark_returns)

    @pytest.mark.unit()
    def test_invalid_benchmark_raises(self, three_asset_returns):
        """Test that invalid benchmark raises."""
        with pytest.raises((Exception_Validation_Input, TypeError)):
            calc_optimalportfolios_tracking_error_minimization(returns_data = three_asset_returns, benchmark_returns = None)


# =============================================================================
# Cross-function sanity tests
# =============================================================================


@pytest.mark.unit()
class Test_Optimization_Cross_Function:
    """Sanity checks comparing multiple optimization functions."""

    @pytest.mark.unit()
    def test_all_seven_functions_return_valid(self, three_asset_returns, benchmark_returns):
        """All 7 functions return valid portfolio_QWIM with matching assets."""
        benchmark_3 = pl.DataFrame(
            {
                "Date": three_asset_returns["Date"].to_list(),
                "SPY": benchmark_returns["SPY"].to_list(),
            }
        )
        ports = [
            calc_optimalportfolios_minimum_variance(returns_data = three_asset_returns),
            calc_optimalportfolios_maximum_quadratic_utility(returns_data = three_asset_returns),
            calc_optimalportfolios_budgeted_risk_contribution(returns_data = three_asset_returns),
            calc_optimalportfolios_maximum_diversification(returns_data = three_asset_returns),
            calc_optimalportfolios_maximum_sharpe_ratio(returns_data = three_asset_returns),
            calc_optimalportfolios_maximum_cara_gaussian_mixture(returns_data = three_asset_returns),
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = three_asset_returns, benchmark_returns = benchmark_3
            ),
        ]
        for port in ports:
            _check_portfolio(port, ASSETS_3)

    @pytest.mark.unit()
    def test_min_var_vs_max_sharpe_differ(self, three_asset_returns):
        """Min-variance and max-Sharpe should generally differ."""
        min_var = calc_optimalportfolios_minimum_variance(returns_data = three_asset_returns)
        max_sharpe = calc_optimalportfolios_maximum_sharpe_ratio(returns_data = three_asset_returns)
        w_mv = min_var.get_portfolio_weights()
        w_ms = max_sharpe.get_portfolio_weights()
        diffs = [abs(float(w_mv[a][0]) - float(w_ms[a][0])) for a in ASSETS_3]
        assert sum(diffs) > 0.001


# =============================================================================
# Logger correctness
# =============================================================================


@pytest.mark.unit()
class Test_Module_Logger:
    """Verify that the module-level logger is properly defined as _logger."""

    def test_logger_attribute_exists_in_module(self) -> None:
        """_optport_validators must expose _logger (not bare logger)."""
        import src.models.portfolio_optimization._optport_validators as mod

        assert hasattr(mod, "_logger"), (
            "Module must define '_logger', not 'logger', to avoid NameError at runtime."
        )

    def test_logger_is_not_bare_logger_name(self) -> None:
        """Verify the module does NOT expose an attribute named 'logger'."""
        import src.models.portfolio_optimization._optport_validators as mod

        assert not hasattr(mod, "logger"), (
            "Module should not have a bare 'logger' attribute; only '_logger' is expected."
        )


# =============================================================================
# Coverage gap tests
# =============================================================================


@pytest.mark.unit()
class Test_Coverage_Gaps:
    """Targeted tests for uncovered branches and exception handlers."""

    # -------------------------------------------------------------------------
    # _compute_covar_and_means: single-asset path (covar.ndim == 0 branch)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_compute_covar_single_asset_is_2d(self):
        """Single-asset array: covar scalar (ndim==0) is reshaped to (1, 1)."""
        returns_1d = np.array([[0.01], [0.02], [-0.01], [0.005], [0.015]])
        covar, means = _compute_covar_and_means(returns_array = returns_1d)
        assert covar.ndim == 2
        assert covar.shape == (1, 1)

    # -------------------------------------------------------------------------
    # Validation branches in main optimization functions
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_max_quadratic_utility_zero_risk_aversion_raises(self, small_returns_data):
        """risk_aversion=0 must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="risk_aversion must be positive"):
            calc_optimalportfolios_maximum_quadratic_utility(
                returns_data = small_returns_data, risk_aversion=0.0
            )

    @pytest.mark.unit()
    def test_max_quadratic_utility_negative_risk_aversion_raises(self, small_returns_data):
        """risk_aversion < 0 must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="risk_aversion must be positive"):
            calc_optimalportfolios_maximum_quadratic_utility(
                returns_data = small_returns_data, risk_aversion=-1.0
            )

    @pytest.mark.unit()
    def test_max_cara_gmm_zero_risk_aversion_raises(self, small_returns_data):
        """risk_aversion=0 in CARA GMM must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="risk_aversion must be positive"):
            calc_optimalportfolios_maximum_cara_gaussian_mixture(
                returns_data = small_returns_data, risk_aversion=0.0
            )

    @pytest.mark.unit()
    def test_max_cara_gmm_zero_n_components_raises(self, small_returns_data):
        """n_components=0 must raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="n_components must be at least 1"):
            calc_optimalportfolios_maximum_cara_gaussian_mixture(
                returns_data = small_returns_data, n_components=0
            )

    @pytest.mark.unit()
    def test_budgeted_risk_dict_missing_key_raises(self, small_returns_data):
        """Dict risk_budgets missing an asset key must raise Exception_Validation_Input."""
        incomplete_dict = {"AAPL": 0.5, "MSFT": 0.5}  # missing GOOG
        with pytest.raises(Exception_Validation_Input, match="missing keys"):
            calc_optimalportfolios_budgeted_risk_contribution(
                returns_data = small_returns_data, risk_budgets=incomplete_dict
            )

    @pytest.mark.unit()
    def test_budgeted_risk_array_wrong_length_raises(self, small_returns_data):
        """Array risk_budgets with wrong length must raise Exception_Validation_Input."""
        wrong_length = np.array([0.5, 0.5])  # small_returns_data has 3 assets
        with pytest.raises(Exception_Validation_Input, match="length"):
            calc_optimalportfolios_budgeted_risk_contribution(
                returns_data = small_returns_data, risk_budgets=wrong_length
            )

    @pytest.mark.unit()
    def test_budgeted_risk_sum_not_one_raises(self, small_returns_data):
        """risk_budgets not summing to 1.0 must raise Exception_Validation_Input."""
        bad_budget = np.array([0.4, 0.4, 0.4])  # sums to 1.2
        with pytest.raises(Exception_Validation_Input, match="sum to 1.0"):
            calc_optimalportfolios_budgeted_risk_contribution(
                returns_data = small_returns_data, risk_budgets=bad_budget
            )

    @pytest.mark.unit()
    def test_tracking_error_multiple_benchmark_columns_raises(self, small_returns_data):
        """Benchmark with 2 asset columns must raise Exception_Validation_Input."""
        multi_bench = pl.DataFrame(
            {
                "Date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "SPY": [0.01, 0.02, -0.01, 0.005, 0.015],
                "AGG": [0.005, -0.005, 0.01, 0.015, -0.005],
            }
        )
        with pytest.raises(Exception_Validation_Input, match="exactly one asset column"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = small_returns_data, benchmark_returns = multi_bench
            )

    @pytest.mark.unit()
    def test_tracking_error_length_mismatch_raises(self, small_returns_data):
        """Benchmark with different row count must raise Exception_Validation_Input."""
        short_bench = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "SPY": [0.01, 0.02, -0.01],
            }
        )
        with pytest.raises(Exception_Validation_Input, match="same length"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = small_returns_data, benchmark_returns = short_bench
            )

    # -------------------------------------------------------------------------
    # Exception handlers (mock optimization functions to raise)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_min_variance_exception_handler(self, small_returns_data):
        """Exception in cvx_quadratic_optimisation → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_convex.cvx_quadratic_optimisation",
            side_effect=Exception("cvxpy error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_minimum_variance(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_max_quadratic_utility_exception_handler(self, small_returns_data):
        """Exception in cvx_quadratic_optimisation → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_convex.cvx_quadratic_optimisation",
            side_effect=Exception("cvxpy error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_maximum_quadratic_utility(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_budgeted_risk_contribution_exception_handler(self, small_returns_data):
        """Exception in opt_risk_budgeting → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_convex.opt_risk_budgeting",
            side_effect=Exception("budgeting error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_budgeted_risk_contribution(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_max_diversification_exception_handler(self, small_returns_data):
        """Exception in opt_maximise_diversification → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_hierarchical.opt_maximise_diversification",
            side_effect=Exception("diversification error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_maximum_diversification(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_max_sharpe_ratio_exception_handler(self, small_returns_data):
        """Exception in cvx_maximize_portfolio_sharpe → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_hierarchical.cvx_maximize_portfolio_sharpe",
            side_effect=Exception("sharpe error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_maximum_sharpe_ratio(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_max_cara_gmm_exception_handler(self, small_returns_data):
        """Exception in fit_gaussian_mixture → Exception_Validation_Input."""
        with patch(
            "src.models.portfolio_optimization._optport_hierarchical.fit_gaussian_mixture",
            side_effect=Exception("GMM fitting error"),
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_maximum_cara_gaussian_mixture(returns_data = small_returns_data)

    @pytest.mark.unit()
    def test_tracking_error_infeasible_status_raises(self, small_returns_data):
        """cvxpy infeasible status → Exception_Calculation inside try, re-raised as
        Exception_Validation_Input by the except handler."""
        bench = pl.DataFrame(
            {
                "Date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "SPY": [0.01, 0.02, -0.01, 0.005, 0.015],
            }
        )
        mock_prob = MagicMock()
        mock_prob.solve.return_value = None
        mock_prob.status = "infeasible"
        with patch(
            "src.models.portfolio_optimization._optport_hierarchical.cp.Problem",
            return_value=mock_prob,
        ):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_optimalportfolios_tracking_error_minimization(
                    returns_data = small_returns_data, benchmark_returns = bench
                )

    # -------------------------------------------------------------------------
    # is_long_only=False paths (False arc of the is_long_only branch)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_min_variance_short_selling(self, three_asset_returns):
        """is_long_only=False path in minimum variance."""
        port = calc_optimalportfolios_minimum_variance(
            returns_data = three_asset_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_quadratic_utility_short_selling(self, three_asset_returns):
        """is_long_only=False path in maximum quadratic utility."""
        port = calc_optimalportfolios_maximum_quadratic_utility(
            returns_data = three_asset_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_diversification_short_selling(self, three_asset_returns):
        """is_long_only=False path in maximum diversification."""
        port = calc_optimalportfolios_maximum_diversification(
            returns_data = three_asset_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_sharpe_ratio_short_selling(self, three_asset_returns):
        """is_long_only=False path in maximum Sharpe ratio."""
        port = calc_optimalportfolios_maximum_sharpe_ratio(
            returns_data = three_asset_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_cara_gmm_short_selling(self, three_asset_returns):
        """is_long_only=False path in maximum CARA GMM."""
        port = calc_optimalportfolios_maximum_cara_gaussian_mixture(
            returns_data = three_asset_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_tracking_error_short_selling(self, three_asset_returns, benchmark_returns):
        """is_long_only=False path in tracking error minimization."""
        port = calc_optimalportfolios_tracking_error_minimization(
            returns_data = three_asset_returns, benchmark_returns = benchmark_returns, is_long_only=False
        )
        assert isinstance(port, Portfolio_QWIM)

    # -------------------------------------------------------------------------
    # portfolio_name is not None paths (False arc of each portfolio_name is None branch)
    # -------------------------------------------------------------------------

    @pytest.mark.unit()
    def test_max_quadratic_utility_explicit_name(self, three_asset_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_maximum_quadratic_utility(
            returns_data = three_asset_returns, portfolio_name="Custom QU"
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_budgeted_risk_explicit_name(self, three_asset_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_budgeted_risk_contribution(
            returns_data = three_asset_returns, portfolio_name="Custom BRC"
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_diversification_explicit_name(self, three_asset_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_maximum_diversification(
            returns_data = three_asset_returns, portfolio_name="Custom MD"
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_sharpe_explicit_name(self, three_asset_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_maximum_sharpe_ratio(
            returns_data = three_asset_returns, portfolio_name="Custom SR"
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_max_cara_gmm_explicit_name(self, three_asset_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_maximum_cara_gaussian_mixture(
            returns_data = three_asset_returns, portfolio_name="Custom CARA"
        )
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_tracking_error_explicit_name(self, three_asset_returns, benchmark_returns):
        """Explicit portfolio_name passes the False arc of portfolio_name is None."""
        port = calc_optimalportfolios_tracking_error_minimization(
            returns_data = three_asset_returns, benchmark_returns = benchmark_returns, portfolio_name="Custom TE"
        )
        assert isinstance(port, Portfolio_QWIM)
