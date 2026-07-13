"""Tests for azapy package wrapper functions.

This module contains comprehensive tests for all functions in pkg_azapy.py,
including the 3 helpers and all 6 main optimization functions.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)

from src.models.portfolio_optimization.pkg_azapy import (
    _convert_polars_to_pandas_returns,
    _extract_weights_from_azapy,
    _validate_returns_data,
    calc_azapy_cvar,
    calc_azapy_evar,
    calc_azapy_inverse_volatility,
    calc_azapy_kelly,
    calc_azapy_mad,
    calc_azapy_mean_variance,
)
from src.portfolios.portfolio_QWIM import Portfolio_QWIM


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_returns_data():
    """Create sample returns DataFrame (200 daily obs, 3 assets, reproducible)."""
    rng = np.random.default_rng(42)
    n_days = 200
    assets = ["AAPL", "MSFT", "GOOG"]

    mean_returns = np.array([0.0008, 0.0010, 0.0006])
    vols = np.array([0.018, 0.015, 0.020])
    corr = np.array(
        [
            [1.00, 0.60, 0.40],
            [0.60, 1.00, 0.50],
            [0.40, 0.50, 1.00],
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
    """Create small 5-row returns DataFrame for quick validation tests."""
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "AAPL": [0.01, -0.005, 0.02, 0.015, -0.01],
            "MSFT": [0.015, 0.01, -0.01, 0.005, 0.02],
            "GOOG": [0.005, 0.02, 0.015, -0.015, 0.01],
        }
    )


# =============================================================================
# Shared assertion helper
# =============================================================================

ASSETS = ["AAPL", "MSFT", "GOOG"]


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
    """Tests for _validate_returns_data (same logic as optimalportfolios version)."""

    @pytest.mark.unit()
    def test_valid_data(self, sample_returns_data):
        """Test that valid data."""
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
        is_valid, msg = _validate_returns_data(returns_data = 42)
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
        df = pl.DataFrame({"AAPL": [0.01, 0.02]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False
        assert "Date" in msg

    @pytest.mark.unit()
    def test_no_asset_columns(self):
        """Test that no asset columns."""
        df = pl.DataFrame({"Date": ["2024-01-01"]})
        is_valid, msg = _validate_returns_data(returns_data = df)
        assert is_valid is False

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


# =============================================================================
# Helper: _convert_polars_to_pandas_returns
# =============================================================================


@pytest.mark.unit()
class Test_Convert_Polars_To_Pandas_Returns:
    """Tests for _convert_polars_to_pandas_returns."""

    @pytest.mark.unit()
    def test_returns_pandas_dataframe(self, sample_returns_data):
        """Test that returns pandas dataframe."""
        result = _convert_polars_to_pandas_returns(returns_data = sample_returns_data)
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.unit()
    def test_date_column_excluded(self, sample_returns_data):
        """Test that date column excluded."""
        result = _convert_polars_to_pandas_returns(returns_data = sample_returns_data)
        assert "Date" not in result.columns

    @pytest.mark.unit()
    def test_correct_shape(self, sample_returns_data):
        """Test that correct shape."""
        result = _convert_polars_to_pandas_returns(returns_data = sample_returns_data)
        assert result.shape == (len(sample_returns_data), 3)

    @pytest.mark.unit()
    def test_asset_columns_present(self, sample_returns_data):
        """Test that asset columns present."""
        result = _convert_polars_to_pandas_returns(returns_data = sample_returns_data)
        for a in ASSETS:
            assert a in result.columns

    @pytest.mark.unit()
    def test_values_preserved(self, small_returns_data):
        """Test that values preserved."""
        result = _convert_polars_to_pandas_returns(returns_data = small_returns_data)
        assert result["AAPL"].iloc[0] == pytest.approx(0.01)
        assert result["MSFT"].iloc[0] == pytest.approx(0.015)

    @pytest.mark.unit()
    def test_no_date_index(self, sample_returns_data):
        """Azapy doesn't need date index — default integer index expected."""
        result = _convert_polars_to_pandas_returns(returns_data = sample_returns_data)
        assert isinstance(result.index[0], (int, np.integer))


# =============================================================================
# Helper: _extract_weights_from_azapy
# =============================================================================


@pytest.mark.unit()
class Test_Extract_Weights_From_Azapy:
    """Tests for _extract_weights_from_azapy."""

    @pytest.mark.unit()
    def test_empty_series_raises_validation_input(self):
        """Empty azapy weights should fail before portfolio construction."""
        with pytest.raises(Exception_Validation_Input) as exc_info:
            _extract_weights_from_azapy(weights_series = pd.Series(dtype=float), portfolio_name = "Test", optimization_date = "2024-01-01")

        assert "weights_series cannot be empty" in str(exc_info.value)

    @pytest.mark.unit()
    def test_basic_extraction(self):
        """Test that basic extraction."""
        weights = pd.Series({"AAPL": 0.4, "MSFT": 0.35, "GOOG": 0.25})
        port = _extract_weights_from_azapy(weights_series = weights, portfolio_name = "Test Portfolio", optimization_date = "2024-01-01")
        assert isinstance(port, Portfolio_QWIM)
        assert port.get_portfolio_name == "Test Portfolio"
        assert port.get_num_components == 3

    @pytest.mark.unit()
    def test_weights_accessible(self):
        """Test that weights accessible."""
        weights = pd.Series({"AAPL": 0.5, "MSFT": 0.3, "GOOG": 0.2})
        port = _extract_weights_from_azapy(weights_series = weights, portfolio_name = "Test", optimization_date = "2024-01-01")
        w_df = port.get_portfolio_weights()
        assert float(w_df["AAPL"][0]) == pytest.approx(0.5, abs=1e-6)
        assert float(w_df["MSFT"][0]) == pytest.approx(0.3, abs=1e-6)

    @pytest.mark.unit()
    def test_default_date_no_crash(self):
        """Test that default date no crash."""
        weights = pd.Series({"A": 0.5, "B": 0.5})
        port = _extract_weights_from_azapy(weights_series = weights, portfolio_name = "Test")
        assert isinstance(port, Portfolio_QWIM)

    @pytest.mark.unit()
    def test_datetime_object(self):
        """Test that datetime object."""
        weights = pd.Series({"A": 0.6, "B": 0.4})
        opt_date = datetime(2024, 6, 15)
        port = _extract_weights_from_azapy(weights_series = weights, portfolio_name = "Test", optimization_date = opt_date)
        w_df = port.get_portfolio_weights()
        assert "2024-06-15" in str(w_df["Date"][0])

    @pytest.mark.unit()
    def test_components_match_series_index(self):
        """Test that components match series index."""
        weights = pd.Series({"AAPL": 0.33, "MSFT": 0.33, "GOOG": 0.34})
        port = _extract_weights_from_azapy(weights_series = weights, portfolio_name = "Test", optimization_date = "2024-01-01")
        assert set(port.get_portfolio_components) == {"AAPL", "MSFT", "GOOG"}


# =============================================================================
# Main Optimization Functions
# =============================================================================


@pytest.mark.unit()
class Test_Calc_Azapy_Mean_Variance:
    """Tests for calc_azapy_mean_variance."""

    @pytest.mark.unit()
    def test_min_risk_portfolio(self, sample_returns_data):
        """Test that min risk portfolio."""
        port = calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="MinRisk")
        _check_portfolio(port, ASSETS, "mv")

    @pytest.mark.unit()
    def test_sharpe_portfolio(self, sample_returns_data):
        """Test that sharpe portfolio."""
        port = calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="Sharpe")
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_default_rtype_is_min_risk(self, sample_returns_data):
        """Test that default rtype is min risk."""
        port = calc_azapy_mean_variance(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_mean_variance(
            returns_data = sample_returns_data, portfolio_name="My MV Portfolio"
        )
        assert port.get_portfolio_name == "My MV Portfolio"

    @pytest.mark.unit()
    def test_custom_optimization_date(self, sample_returns_data):
        """Test that custom optimization date."""
        port = calc_azapy_mean_variance(
            returns_data = sample_returns_data, optimization_date="2024-06-01"
        )
        w_df = port.get_portfolio_weights()
        assert "2024-06-01" in str(w_df["Date"][0])

    @pytest.mark.unit()
    def test_invalid_rtype_raises(self, sample_returns_data):
        """Test that invalid rtype raises."""
        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="INVALID")

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_mean_variance(returns_data = None)

    @pytest.mark.unit()
    def test_inv_nrisk_rtype(self, sample_returns_data):
        """Test that inv nrisk rtype."""
        port = calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="InvNrisk")
        _check_portfolio(port, ASSETS)


@pytest.mark.unit()
class Test_Calc_Azapy_CVaR:
    """Tests for calc_azapy_cvar."""

    @pytest.mark.unit()
    def test_default_parameters(self, sample_returns_data):
        """Test that default parameters."""
        port = calc_azapy_cvar(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS, "cvar")

    @pytest.mark.unit()
    def test_min_risk_rtype(self, sample_returns_data):
        """Test that min risk rtype."""
        port = calc_azapy_cvar(returns_data = sample_returns_data, rtype="MinRisk")
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_custom_alpha(self, sample_returns_data):
        """Test that custom alpha."""
        port = calc_azapy_cvar(returns_data = sample_returns_data, alpha=0.99)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_alpha_095(self, sample_returns_data):
        """Test that alpha 095."""
        port = calc_azapy_cvar(returns_data = sample_returns_data, alpha=0.95)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_invalid_alpha_zero_raises(self, sample_returns_data):
        """Test that invalid alpha zero raises."""
        with pytest.raises(Exception_Validation_Input, match="alpha"):
            calc_azapy_cvar(returns_data = sample_returns_data, alpha=0.0)

    @pytest.mark.unit()
    def test_invalid_alpha_one_raises(self, sample_returns_data):
        """Test that invalid alpha one raises."""
        with pytest.raises(Exception_Validation_Input, match="alpha"):
            calc_azapy_cvar(returns_data = sample_returns_data, alpha=1.0)

    @pytest.mark.unit()
    def test_invalid_rtype_raises(self, sample_returns_data):
        """Test that invalid rtype raises."""
        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_azapy_cvar(returns_data = sample_returns_data, rtype="WRONG")

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_cvar(returns_data = None)

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_cvar(returns_data = sample_returns_data, portfolio_name="My CVaR")
        assert port.get_portfolio_name == "My CVaR"


@pytest.mark.unit()
class Test_Calc_Azapy_MAD:
    """Tests for calc_azapy_mad."""

    @pytest.mark.unit()
    def test_min_risk_portfolio(self, sample_returns_data):
        """Test that min risk portfolio."""
        port = calc_azapy_mad(returns_data = sample_returns_data, rtype="MinRisk")
        _check_portfolio(port, ASSETS, "mad")

    @pytest.mark.unit()
    def test_sharpe_portfolio(self, sample_returns_data):
        """Test that sharpe portfolio."""
        port = calc_azapy_mad(returns_data = sample_returns_data, rtype="Sharpe")
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_default_rtype(self, sample_returns_data):
        """Test that default rtype."""
        port = calc_azapy_mad(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_invalid_rtype_raises(self, sample_returns_data):
        """Test that invalid rtype raises."""
        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_azapy_mad(returns_data = sample_returns_data, rtype="BAD")

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_mad(returns_data = None)

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_mad(returns_data = sample_returns_data, portfolio_name="MAD Min Risk")
        assert port.get_portfolio_name == "MAD Min Risk"


@pytest.mark.unit()
class Test_Calc_Azapy_Inverse_Volatility:
    """Tests for calc_azapy_inverse_volatility."""

    @pytest.mark.unit()
    def test_returns_valid_portfolio(self, sample_returns_data):
        """Test that returns valid portfolio."""
        port = calc_azapy_inverse_volatility(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS, "inverse")

    @pytest.mark.unit()
    def test_all_weights_positive(self, sample_returns_data):
        """Inverse volatility should always yield positive weights."""
        port = calc_azapy_inverse_volatility(returns_data = sample_returns_data)
        w_df = port.get_portfolio_weights()
        for a in ASSETS:
            assert float(w_df[a][0]) > 0

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_inverse_volatility(
            returns_data = sample_returns_data, portfolio_name="My InvVol"
        )
        assert port.get_portfolio_name == "My InvVol"

    @pytest.mark.unit()
    def test_custom_optimization_date(self, sample_returns_data):
        """Test that custom optimization date."""
        port = calc_azapy_inverse_volatility(
            returns_data = sample_returns_data, optimization_date="2024-03-01"
        )
        w_df = port.get_portfolio_weights()
        assert "2024-03-01" in str(w_df["Date"][0])

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_inverse_volatility(returns_data = None)

    @pytest.mark.unit()
    def test_higher_vol_lower_weight(self, sample_returns_data):
        """Asset with higher volatility should have lower weight."""
        port = calc_azapy_inverse_volatility(returns_data = sample_returns_data)
        w_df = port.get_portfolio_weights()
        # GOOG (vol=0.020) should have lower weight than MSFT (vol=0.015)
        w_goog = float(w_df["GOOG"][0])
        w_msft = float(w_df["MSFT"][0])
        assert w_goog < w_msft


@pytest.mark.unit()
class Test_Calc_Azapy_Kelly:
    """Tests for calc_azapy_kelly."""

    @pytest.mark.unit()
    def test_expcone_portfolio(self, sample_returns_data):
        """Test that expcone portfolio."""
        port = calc_azapy_kelly(returns_data = sample_returns_data, rtype="ExpCone")
        _check_portfolio(port, ASSETS, "kelly")

    @pytest.mark.unit()
    def test_default_rtype_expcone(self, sample_returns_data):
        """Test that default rtype expcone."""
        port = calc_azapy_kelly(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_invalid_rtype_raises(self, sample_returns_data):
        """Test that invalid rtype raises."""
        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_azapy_kelly(returns_data = sample_returns_data, rtype="INVALID")

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_kelly(returns_data = None)

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_kelly(returns_data = sample_returns_data, portfolio_name="My Kelly")
        assert port.get_portfolio_name == "My Kelly"


@pytest.mark.unit()
class Test_Calc_Azapy_EVaR:
    """Tests for calc_azapy_evar."""

    @pytest.mark.unit()
    def test_default_parameters(self, sample_returns_data):
        """Test that default parameters."""
        port = calc_azapy_evar(returns_data = sample_returns_data)
        _check_portfolio(port, ASSETS, "evar")

    @pytest.mark.unit()
    def test_min_risk_rtype(self, sample_returns_data):
        """Test that min risk rtype."""
        port = calc_azapy_evar(returns_data = sample_returns_data, rtype="MinRisk")
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_custom_alpha(self, sample_returns_data):
        """Test that custom alpha."""
        port = calc_azapy_evar(returns_data = sample_returns_data, alpha=0.99)
        _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_invalid_alpha_raises(self, sample_returns_data):
        """Test that invalid alpha raises."""
        with pytest.raises(Exception_Validation_Input, match="alpha"):
            calc_azapy_evar(returns_data = sample_returns_data, alpha=1.5)

    @pytest.mark.unit()
    def test_invalid_rtype_raises(self, sample_returns_data):
        """Test that invalid rtype raises."""
        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_azapy_evar(returns_data = sample_returns_data, rtype="BAD")

    @pytest.mark.unit()
    def test_none_input_raises(self):
        """Test that none input raises."""
        with pytest.raises(Exception_Validation_Input):
            calc_azapy_evar(returns_data = None)

    @pytest.mark.unit()
    def test_custom_portfolio_name(self, sample_returns_data):
        """Test that custom portfolio name."""
        port = calc_azapy_evar(returns_data = sample_returns_data, portfolio_name="EVaR Sharpe")
        assert port.get_portfolio_name == "EVaR Sharpe"


# =============================================================================
# Cross-function sanity tests
# =============================================================================


@pytest.mark.unit()
class Test_Azapy_Cross_Function:
    """Sanity checks comparing outputs across all 6 optimization functions."""

    @pytest.mark.unit()
    def test_all_six_functions_return_valid_portfolio(self, sample_returns_data):
        """All 6 functions should return portfolio_QWIM with valid weights."""
        ports = [
            calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="MinRisk"),
            calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="Sharpe"),
            calc_azapy_cvar(returns_data = sample_returns_data, rtype="MinRisk"),
            calc_azapy_mad(returns_data = sample_returns_data, rtype="Sharpe"),
            calc_azapy_inverse_volatility(returns_data = sample_returns_data),
            calc_azapy_kelly(returns_data = sample_returns_data),
            calc_azapy_evar(returns_data = sample_returns_data, rtype="MinRisk"),
        ]
        for port in ports:
            _check_portfolio(port, ASSETS)

    @pytest.mark.unit()
    def test_inv_vol_vs_min_var_differ(self, sample_returns_data):
        """Inverse volatility and min-variance generally produce different portfolios."""
        inv_vol = calc_azapy_inverse_volatility(returns_data = sample_returns_data)
        min_var = calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="MinRisk")
        w_iv = inv_vol.get_portfolio_weights()
        w_mv = min_var.get_portfolio_weights()
        diffs = [abs(float(w_iv[a][0]) - float(w_mv[a][0])) for a in ASSETS]
        assert sum(diffs) > 0.001

    @pytest.mark.unit()
    def test_cvar_vs_mv_can_differ(self, sample_returns_data):
        """CVaR-sharpe and MV-sharpe can differ due to different risk measures."""
        cvar_port = calc_azapy_cvar(returns_data = sample_returns_data, rtype="Sharpe")
        mv_port = calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="Sharpe")
        _check_portfolio(cvar_port, ASSETS)
        _check_portfolio(mv_port, ASSETS)


# =============================================================================
# Exception-path coverage: mock azapy analyzers to trigger error branches
# =============================================================================


@pytest.mark.unit()
class Test_Azapy_Exception_Paths:
    """Cover exception-handler branches in all 6 optimizer wrappers.

    Each test mocks the underlying azapy analyzer so that ``getWeights``
    returns ``None`` (for functions with an explicit None-guard) or raises
    directly (for InvVol / Kelly which have no None-guard).  Both paths
    ultimately exercise the ``except Exception as e:`` handler that
    re-raises ``Exception_Validation_Input``.
    """

    @pytest.mark.unit()
    def test_mv_none_weights_triggers_exception_handler(self, sample_returns_data):
        """Mock MVAnalyzer.getWeights returning None covers the None-guard raise
        and the except-block re-raise in calc_azapy_mean_variance."""
        mock_inst = MagicMock()
        mock_inst.getWeights.return_value = None
        with patch("azapy.MVAnalyzer", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_mean_variance(returns_data = sample_returns_data, rtype="MinRisk")

    @pytest.mark.unit()
    def test_cvar_none_weights_triggers_exception_handler(self, sample_returns_data):
        """Mock CVaRAnalyzer.getWeights returning None covers the None-guard raise
        and the except-block re-raise in calc_azapy_cvar."""
        mock_inst = MagicMock()
        mock_inst.getWeights.return_value = None
        with patch("azapy.CVaRAnalyzer", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_cvar(returns_data = sample_returns_data, rtype="MinRisk")

    @pytest.mark.unit()
    def test_mad_none_weights_triggers_exception_handler(self, sample_returns_data):
        """Mock MADAnalyzer.getWeights returning None covers the None-guard raise
        and the except-block re-raise in calc_azapy_mad."""
        mock_inst = MagicMock()
        mock_inst.getWeights.return_value = None
        with patch("azapy.MADAnalyzer", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_mad(returns_data = sample_returns_data, rtype="MinRisk")

    @pytest.mark.unit()
    def test_invvol_analyzer_error_triggers_exception_handler(self, sample_returns_data):
        """Mock InvVolEngine.getWeights raising covers the except-block in
        calc_azapy_inverse_volatility (no None-guard in this function)."""
        mock_inst = MagicMock()
        mock_inst.getWeights.side_effect = Exception("azapy InvVol failed")
        with patch("azapy.InvVolEngine", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_inverse_volatility(returns_data = sample_returns_data)

    @pytest.mark.unit()
    def test_kelly_analyzer_error_triggers_exception_handler(self, sample_returns_data):
        """Mock KellyEngine.getWeights raising covers the except-block in
        calc_azapy_kelly (no None-guard in this function)."""
        mock_inst = MagicMock()
        mock_inst.getWeights.side_effect = Exception("azapy Kelly failed")
        with patch("azapy.KellyEngine", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_kelly(returns_data = sample_returns_data, rtype="ExpCone")

    @pytest.mark.unit()
    def test_evar_none_weights_triggers_exception_handler(self, sample_returns_data):
        """Mock EVaRAnalyzer.getWeights returning None covers the None-guard raise
        and the except-block re-raise in calc_azapy_evar."""
        mock_inst = MagicMock()
        mock_inst.getWeights.return_value = None
        with patch("azapy.EVaRAnalyzer", return_value=mock_inst):
            with pytest.raises(Exception_Validation_Input, match="Optimization failed"):
                calc_azapy_evar(returns_data = sample_returns_data, rtype="MinRisk")

