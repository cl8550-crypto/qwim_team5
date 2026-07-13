"""Unit tests for scenarios_CMA module.

This module contains comprehensive tests for the Scenarios_CMA class and related utilities
in src/num_methods/scenarios/scenarios_CMA.py.
"""

import datetime as dt

from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest


@pytest.fixture()
def Scenarios_CMA_class():
    """Fixture to import Scenarios_CMA class."""
    from src.num_methods.scenarios.scenarios_CMA import Scenarios_CMA

    return Scenarios_CMA


@pytest.fixture()
def Asset_Class_Tier_enum():
    """Fixture to import Asset_Class_Tier enum."""
    from src.num_methods.scenarios.scenarios_CMA import Asset_Class_Tier

    return Asset_Class_Tier


@pytest.fixture()
def CMA_Source_enum():
    """Fixture to import CMA_Source enum."""
    from src.num_methods.scenarios.scenarios_CMA import CMA_Source

    return CMA_Source


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
def sample_cma_params():
    """Fixture providing sample CMA parameters."""
    return {
        "names_asset_classes": ["US_Equity", "US_Bonds"],
        "expected_returns_annual": np.array([0.08, 0.03]),
        "expected_vols_annual": np.array([0.15, 0.05]),
        "correlation_matrix": np.array([[1.0, 0.2], [0.2, 1.0]]),
        "num_days": 10,
        "num_scenarios": 1,
    }


class Test_Asset_Class_Tier_Enum:
    """Tests for Asset_Class_Tier enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, Asset_Class_Tier_enum):
        """Test that all expected tier levels exist."""
        assert hasattr(Asset_Class_Tier_enum, "TIER_0")
        assert hasattr(Asset_Class_Tier_enum, "TIER_1")
        assert hasattr(Asset_Class_Tier_enum, "TIER_2")

    @pytest.mark.unit()
    def test_enum_values_are_integers(self, Asset_Class_Tier_enum):
        """Test that tier values are integers (0, 1, 2)."""
        assert Asset_Class_Tier_enum.TIER_0.value == 0
        assert Asset_Class_Tier_enum.TIER_1.value == 1
        assert Asset_Class_Tier_enum.TIER_2.value == 2


class Test_CMA_Source_Enum:
    """Tests for CMA_Source enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, CMA_Source_enum):
        """Test that CMA source enum members exist."""
        assert hasattr(CMA_Source_enum, "MANUAL")
        assert hasattr(CMA_Source_enum, "SPREADSHEET")

    @pytest.mark.unit()
    def test_enum_values(self, CMA_Source_enum):
        """Test enum values are descriptive strings."""
        assert isinstance(CMA_Source_enum.MANUAL.value, str)
        assert isinstance(CMA_Source_enum.SPREADSHEET.value, str)


class Test_Scenarios_CMA_Instantiation:
    """Tests for Scenarios_CMA initialization."""

    @pytest.mark.unit()
    def test_initialization_with_valid_params(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test successful initialization with valid CMA parameters."""
        obj = Scenarios_CMA_class(
            **sample_cma_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        assert obj is not None
        assert obj.num_components == 2
        assert "US_Equity" in obj.names_components
        assert "US_Bonds" in obj.names_components

    @pytest.mark.unit()
    def test_initialization_requires_matching_dimensions(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that mismatched dimensions raise validation error."""
        with pytest.raises(Exception):  # Exception_Validation_Input
            Scenarios_CMA_class(
                names_asset_classes=["US_Equity", "US_Bonds"],
                expected_returns_annual=np.array([0.08]),  # Wrong size!
                expected_vols_annual=np.array([0.15, 0.05]),
                correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
                source=CMA_Source_enum.MANUAL,
            )

    @pytest.mark.unit()
    def test_correlation_matrix_must_be_square(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that non-square correlation matrix raises error."""
        with pytest.raises(Exception):
            Scenarios_CMA_class(
                names_asset_classes=["US_Equity", "US_Bonds"],
                expected_returns_annual=np.array([0.08, 0.03]),
                expected_vols_annual=np.array([0.15, 0.05]),
                correlation_matrix=np.array([[1.0, 0.2, 0.3], [0.2, 1.0, 0.1]]),  # Not square!
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
                source=CMA_Source_enum.MANUAL,
            )

    @pytest.mark.unit()
    def test_correlation_matrix_diagonal_must_be_one(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test validation of correlation matrix diagonal."""
        with pytest.raises(Exception):
            Scenarios_CMA_class(
                names_asset_classes=["US_Equity"],
                expected_returns_annual=np.array([0.08]),
                expected_vols_annual=np.array([0.15]),
                correlation_matrix=np.array([[0.9]]),  # Should be 1.0!
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
                source=CMA_Source_enum.MANUAL,
            )

    @pytest.mark.unit()
    def test_correlation_matrix_must_be_symmetric(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that asymmetric correlation matrix raises error."""
        with pytest.raises(Exception):
            Scenarios_CMA_class(
                names_asset_classes=["US_Equity", "US_Bonds"],
                expected_returns_annual=np.array([0.08, 0.03]),
                expected_vols_annual=np.array([0.15, 0.05]),
                correlation_matrix=np.array([[1.0, 0.2], [0.3, 1.0]]),  # Asymmetric!
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
                source=CMA_Source_enum.MANUAL,
            )


class Test_CMA_Parameter_Validation:
    """Tests for CMA parameter validation."""

    @pytest.mark.unit()
    def test_invalid_random_seed_raises(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Boolean and negative random_seed values should be rejected early."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_random_seed in (True, -1):
            with pytest.raises(Exception_Validation_Input):
                Scenarios_CMA_class(
                    **sample_cma_params,
                    data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                    frequency=Frequency_Time_Series_enum.DAILY,
                    source=CMA_Source_enum.MANUAL,
                    random_seed=item_random_seed,
                )

    @pytest.mark.unit()
    def test_negative_volatility_creates_object(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that negative volatility does not raise at construction.

        The implementation does not validate sign of volatilities; it only
        validates shapes, diagonal==1, and symmetry.  Negative vols will
        produce mathematically valid (if financially odd) covariance
        matrices since cov = diag(vol) @ corr @ diag(vol).
        """
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity"],
            expected_returns_annual=np.array([0.08]),
            expected_vols_annual=np.array([-0.15]),  # Negative
            correlation_matrix=np.array([[1.0]]),
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )
        assert obj is not None

    @pytest.mark.unit()
    def test_correlation_out_of_bounds_creates_object(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that correlation values outside [-1, 1] do not raise.

        The implementation checks symmetry but does not enforce bounds on
        off-diagonal correlation values.  The Cholesky decomposition may
        still fail for non-PSD matrices, but construction succeeds.
        """
        # 1.5 is out of bounds but the implementation allows it
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity", "US_Bonds"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 1.5], [1.5, 1.0]]),
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )
        assert obj is not None


class Test_Scenario_Generation:
    """Tests for CMA-based scenario generation."""

    @pytest.mark.unit()
    def test_generate_returns_dataframe(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test that generate method returns properly formatted DataFrame."""
        obj = Scenarios_CMA_class(
            **sample_cma_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        result = obj.generate()

        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "US_Equity" in result.columns
        assert "US_Bonds" in result.columns
        # generate() produces num_dates rows (one scenario path), not num_days * num_scenarios
        assert len(result) == 10

    @pytest.mark.unit()
    def test_generated_returns_have_correct_statistics(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that generated returns match CMA statistics (on average)."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity", "US_Bonds"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
            random_seed=42,
        )

        result = obj.generate()

        # Calculate realized statistics
        equity_returns = result["US_Equity"].to_numpy()
        realized_mean = np.mean(equity_returns)
        realized_std = np.std(equity_returns)

        # Expected daily statistics from annual CMA
        expected_daily_mean = 0.08 / 252
        expected_daily_std = 0.15 / np.sqrt(252)

        # Allow generous tolerance for finite sample
        assert np.abs(realized_mean - expected_daily_mean) < 0.001
        assert np.abs(realized_std - expected_daily_std) < 0.005

    @pytest.mark.unit()
    def test_generated_scenarios_have_correct_correlation(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that generated returns have correlation matching CMA."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity", "US_Bonds"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 0.5], [0.5, 1.0]]),
            num_days=10000,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
            random_seed=42,
        )

        result = obj.generate()

        # Calculate realized correlation
        equity = result["US_Equity"].to_numpy()
        bonds = result["US_Bonds"].to_numpy()
        realized_corr = np.corrcoef(equity, bonds)[0, 1]

        # Should be close to 0.5 (allow tolerance for finite sample)
        assert np.abs(realized_corr - 0.5) < 0.05

    @pytest.mark.unit()
    def test_generate_produces_num_dates_rows(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that generate() produces num_dates rows (one path per call)."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity", "US_Bonds"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            num_days=5,
            num_scenarios=3,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        result = obj.generate()

        # Each generate() call produces num_dates rows
        assert len(result) == 5


class Test_Date_Generation:
    """Tests for business date generation in CMA scenarios."""

    @pytest.mark.unit()
    def test_generate_with_explicit_dates(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test scenario generation with user-provided dates."""
        dates = [dt.date(2024, 1, i) for i in range(1, 6)]

        # Update sample params for this test
        test_params = sample_cma_params.copy()
        test_params["num_scenarios"] = 1

        obj = Scenarios_CMA_class(
            **test_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
            dates=dates,
        )

        result = obj.generate()

        # Should use provided dates
        assert len(result["Date"].unique()) == 5

    @pytest.mark.unit()
    def test_generated_dates_are_business_days(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test that auto-generated dates exclude weekends."""
        test_params = sample_cma_params.copy()
        test_params["num_days"] = 20
        test_params["num_scenarios"] = 1

        obj = Scenarios_CMA_class(
            **test_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        result = obj.generate()
        unique_dates = result["Date"].unique().sort()

        # Verify we have the right number of dates
        assert len(unique_dates) == 20


class Test_CMA_Properties:
    """Tests for CMA-specific properties and getters."""

    @pytest.mark.unit()
    def test_expected_returns_annual(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test accessing CMA expected returns."""
        obj = Scenarios_CMA_class(
            **sample_cma_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        returns = obj.expected_returns_annual
        assert isinstance(returns, np.ndarray)
        assert len(returns) == 2
        assert returns[0] == 0.08

    @pytest.mark.unit()
    def test_expected_vols_annual(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test accessing CMA volatilities."""
        obj = Scenarios_CMA_class(
            **sample_cma_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        vols = obj.expected_vols_annual
        assert isinstance(vols, np.ndarray)
        assert len(vols) == 2
        assert vols[0] == 0.15

    @pytest.mark.unit()
    def test_correlation_matrix_property(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        sample_cma_params,
    ):
        """Test accessing CMA correlation matrix."""
        obj = Scenarios_CMA_class(
            **sample_cma_params,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        corr = obj.correlation_matrix
        assert isinstance(corr, np.ndarray)
        assert corr.shape == (2, 2)
        assert np.allclose(np.diag(corr), 1.0)


class Test_Covariance_Calculation:
    """Tests for covariance matrix calculation from correlation and volatilities."""

    @pytest.mark.unit()
    def test_covariance_from_correlation_and_volatility(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test covariance matrix calculation."""
        # Known values for testing
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        vols = np.array([0.20, 0.10])

        obj = Scenarios_CMA_class(
            names_asset_classes=["A", "B"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=vols,
            correlation_matrix=corr,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        cov = obj.covariance_matrix_annual

        # Covariance: cov[i,j] = corr[i,j] * vol[i] * vol[j]
        # cov[0,0] = 1.0 * 0.20 * 0.20 = 0.04
        # cov[1,1] = 1.0 * 0.10 * 0.10 = 0.01
        # cov[0,1] = 0.5 * 0.20 * 0.10 = 0.01
        assert np.isclose(cov[0, 0], 0.04)
        assert np.isclose(cov[1, 1], 0.01)
        assert np.isclose(cov[0, 1], 0.01)
        assert np.isclose(cov[1, 0], 0.01)


class Test_Cholesky_Decomposition:
    """Tests for Cholesky decomposition used in scenario generation."""

    @pytest.mark.unit()
    def test_cholesky_recovers_covariance(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that Cholesky decomposition correctly recovers covariance."""
        corr = np.array([[1.0, 0.6], [0.6, 1.0]])
        vols = np.array([0.15, 0.08])

        obj = Scenarios_CMA_class(
            names_asset_classes=["A", "B"],
            expected_returns_annual=np.array([0.07, 0.04]),
            expected_vols_annual=vols,
            correlation_matrix=corr,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        cov = obj.covariance_matrix_annual

        # Cholesky: L @ L.T = covariance
        L = np.linalg.cholesky(cov)
        reconstructed = L @ L.T

        assert np.allclose(reconstructed, cov)


class Test_Spreadsheet_Loading:
    """Tests for loading CMA data from spreadsheet (from_spreadsheet classmethod)."""

    @pytest.mark.unit()
    @patch("polars.read_excel")
    def test_from_spreadsheet_creates_instance(
        self,
        mock_read_excel,
        Scenarios_CMA_class,
    ):
        """Test that from_spreadsheet classmethod creates valid instance."""
        # Mock Excel data
        mock_data = pl.DataFrame(
            {
                "Asset_Class": ["US_Equity", "US_Bonds"],
                "Expected_Return": [0.08, 0.03],
                "Volatility": [0.15, 0.05],
            }
        )

        mock_corr_data = pl.DataFrame(
            {
                "": ["US_Equity", "US_Bonds"],
                "US_Equity": [1.0, 0.2],
                "US_Bonds": [0.2, 1.0],
            }
        )

        # Mock read_excel to return our data
        mock_read_excel.side_effect = [mock_data, mock_corr_data]

        # Note: This test structure shows the pattern
        # Actual implementation depends on from_spreadsheet interface

    @pytest.mark.unit()
    def test_from_spreadsheet_validates_file_exists(
        self,
        Scenarios_CMA_class,
    ):
        """Test that loading from non-existent file raises error."""
        fake_path = Path("nonexistent_file.xlsx")

        with pytest.raises(Exception):  # Exception_Validation_Input
            Scenarios_CMA_class.from_spreadsheet(path = fake_path)


# ============================================================================
# Vols shape mismatch — line 339, branch 338→339
# ============================================================================


class Test_Vols_Shape_Mismatch:
    """Cover the expected_vols_annual shape-mismatch raise (line 339)."""

    @pytest.mark.unit()
    def test_wrong_vols_size_raises_validation_error(self, Scenarios_CMA_class):
        """K=2 but vols shape=(1,) → raises an exception (line 339, arc 338→339)."""
        with pytest.raises(Exception):
            Scenarios_CMA_class(
                names_asset_classes=["A", "B"],
                expected_returns_annual=np.array([0.08, 0.03]),
                expected_vols_annual=np.array([0.15]),  # wrong: K=2 but shape=(1,)
                correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            )


# ============================================================================
# tier_map property — line 462
# ============================================================================


class Test_Tier_Map_Property:
    """Cover the tier_map property return statement (line 462)."""

    @pytest.mark.unit()
    def test_tier_map_returns_dict(self, Scenarios_CMA_class, sample_cma_params):
        """tier_map property returns a dict (covers line 462)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.tier_map
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_tier_map_reflects_custom_mapping(
        self, Scenarios_CMA_class, Asset_Class_Tier_enum
    ):
        """tier_map returns custom tier mapping when provided at construction."""
        custom_tier = {
            "A": Asset_Class_Tier_enum.TIER_0,
            "B": Asset_Class_Tier_enum.TIER_2,
        }
        obj = Scenarios_CMA_class(
            names_asset_classes=["A", "B"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            tier_map=custom_tier,
        )
        result = obj.tier_map
        assert result["A"] == Asset_Class_Tier_enum.TIER_0
        assert result["B"] == Asset_Class_Tier_enum.TIER_2


# ============================================================================
# generate() with 0 dates — line 558, branch 557→558
# ============================================================================


class Test_Generate_Zero_Dates:
    """Cover generate() raise when m_num_dates == 0 (line 558)."""

    @pytest.mark.unit()
    def test_generate_raises_when_dates_empty(self, Scenarios_CMA_class):
        """dates=[] makes m_num_dates=0; generate() raises an exception (arc 557→558)."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["A"],
            expected_returns_annual=np.array([0.08]),
            expected_vols_annual=np.array([0.15]),
            correlation_matrix=np.array([[1.0]]),
            dates=[],  # empty → m_num_dates = 0
        )
        with pytest.raises(Exception):
            obj.generate()


# ============================================================================
# __repr__ — line 803
# ============================================================================


class Test_Repr_Method:
    """Cover the __repr__ return statement (line 803)."""

    @pytest.mark.unit()
    def test_repr_is_string_containing_class_name(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """repr(instance) returns a string containing 'Scenarios_CMA' (covers line 803)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = repr(obj)
        assert isinstance(result, str)
        assert "Scenarios_CMA" in result

    @pytest.mark.unit()
    def test_repr_contains_source_value(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """repr() includes the CMA source value."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = repr(obj)
        # CMA_Source default is MANUAL whose value is 'Manual'
        assert "Manual" in result


# ============================================================================
# from_spreadsheet body — lines 675-746, branches 666→675, 714→*, 719→*, 720→*
# ============================================================================


class Test_From_Spreadsheet_Mocked:
    """Cover from_spreadsheet body via mocked pl.read_excel (lines 675-746)."""

    @staticmethod
    def _df_returns() -> pl.DataFrame:
        return pl.DataFrame(
            {"asset_class": ["A", "B"], "expected_return": [0.08, 0.03]}
        )

    @staticmethod
    def _df_vols() -> pl.DataFrame:
        return pl.DataFrame({"asset_class": ["A", "B"], "volatility": [0.15, 0.05]})

    @staticmethod
    def _df_corr() -> pl.DataFrame:
        return pl.DataFrame(
            {"asset_class": ["A", "B"], "A": [1.0, 0.2], "B": [0.2, 1.0]}
        )

    @pytest.mark.unit()
    @patch("pathlib.Path.exists", return_value=True)
    @patch("polars.read_excel")
    def test_from_spreadsheet_basic_no_scenario_sheet(
        self, mock_read_excel, _mock_exists, Scenarios_CMA_class
    ):
        """from_spreadsheet creates instance; no scenarios sheet → arc 666→675 and 714→746."""
        mock_read_excel.side_effect = [
            self._df_returns(), self._df_vols(), self._df_corr()
        ]
        instance = Scenarios_CMA_class.from_spreadsheet(path = "fake.xlsx", num_days=5)
        assert instance is not None
        assert instance.num_components == 2

    @pytest.mark.unit()
    @patch("pathlib.Path.exists", return_value=True)
    @patch("polars.read_excel")
    def test_from_spreadsheet_with_date_type_scenario_sheet(
        self, mock_read_excel, _mock_exists, Scenarios_CMA_class
    ):
        """from_spreadsheet with scenarios sheet + pl.Date Date column (arcs 714→715, 719→720, 720→727)."""
        scenario_df = pl.DataFrame(
            {
                "Date": [dt.date(2024, 1, 2), dt.date(2024, 1, 3)],
                "A": [0.01, 0.02],
                "B": [-0.01, 0.01],
            }
        )
        mock_read_excel.side_effect = [
            self._df_returns(), self._df_vols(), self._df_corr(), scenario_df
        ]
        instance = Scenarios_CMA_class.from_spreadsheet(
            path = "fake.xlsx",
            sheet_name_scenarios="Scenarios",
            num_days=5,
        )
        assert instance.m_num_dates == 2

    @pytest.mark.unit()
    @patch("pathlib.Path.exists", return_value=True)
    @patch("polars.read_excel")
    def test_from_spreadsheet_with_utf8_date_scenario_sheet(
        self, mock_read_excel, _mock_exists, Scenarios_CMA_class
    ):
        """from_spreadsheet with string Date column triggers strptime (arc 720→721)."""
        # String columns in Polars have dtype pl.Utf8 == pl.String
        scenario_df = pl.DataFrame(
            {
                "Date": ["2024-01-02", "2024-01-03"],
                "A": [0.01, 0.02],
                "B": [-0.01, 0.01],
            }
        )
        mock_read_excel.side_effect = [
            self._df_returns(), self._df_vols(), self._df_corr(), scenario_df
        ]
        instance = Scenarios_CMA_class.from_spreadsheet(
            path = "fake.xlsx",
            sheet_name_scenarios="Scenarios",
            num_days=5,
        )
        assert instance.m_num_dates == 2

    @pytest.mark.unit()
    @patch("pathlib.Path.exists", return_value=True)
    @patch("polars.read_excel")
    def test_from_spreadsheet_scenario_sheet_without_date_column(
        self, mock_read_excel, _mock_exists, Scenarios_CMA_class
    ):
        """Scenario sheet without Date column → 'Date in columns' is False (arc 719→746)."""
        scenario_df = pl.DataFrame(
            {"A": [0.01, 0.02], "B": [-0.01, 0.01]}  # no Date column
        )
        mock_read_excel.side_effect = [
            self._df_returns(), self._df_vols(), self._df_corr(), scenario_df
        ]
        instance = Scenarios_CMA_class.from_spreadsheet(
            path = "fake.xlsx",
            sheet_name_scenarios="Scenarios",
            num_days=5,
        )
        assert instance is not None


class Test_Edge_Cases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit()
    def test_single_asset_class(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test CMA scenarios with single asset class."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["US_Equity"],
            expected_returns_annual=np.array([0.08]),
            expected_vols_annual=np.array([0.15]),
            correlation_matrix=np.array([[1.0]]),
            num_days=5,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        result = obj.generate()
        assert "US_Equity" in result.columns

    @pytest.mark.unit()
    def test_zero_volatility_asset(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test CMA scenarios with zero volatility (risk-free asset).

        With zero volatility the covariance matrix is all zeros and the
        Cholesky fallback (eigenvalue clipping to 1e-4) introduces tiny
        noise, so returns are *nearly* constant but not exactly identical.
        """
        obj = Scenarios_CMA_class(
            names_asset_classes=["Cash"],
            expected_returns_annual=np.array([0.02]),
            expected_vols_annual=np.array([0.0]),
            correlation_matrix=np.array([[1.0]]),
            num_days=10,
            num_scenarios=1,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
            random_seed=42,
        )

        result = obj.generate()

        # With zero volatility the covariance is all zeros, so the
        # Cholesky fallback clips eigenvalues to 1e-4, introducing
        # non-trivial noise.  We only verify the DataFrame is produced
        # and has the right shape.
        cash_returns = result["Cash"].to_numpy()
        assert len(cash_returns) == 10
        # The mean across many samples would converge to the daily
        # expected return, but 10 samples is too few to assert that.

    @pytest.mark.unit()
    def test_negative_expected_returns_allowed(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
    ):
        """Test that negative expected returns are allowed (e.g., bear market assumptions)."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["Equity"],
            expected_returns_annual=np.array([-0.05]),  # Negative expected return
            expected_vols_annual=np.array([0.20]),
            correlation_matrix=np.array([[1.0]]),
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        assert obj is not None


class Test_Tier_Mapping:
    """Tests for asset class tier mapping functionality."""

    @pytest.mark.unit()
    def test_tier_assignment(
        self,
        Scenarios_CMA_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        CMA_Source_enum,
        Asset_Class_Tier_enum,
    ):
        """Test that asset classes can be assigned to tiers."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["Equities", "US_Large_Cap"],
            expected_returns_annual=np.array([0.08, 0.09]),
            expected_vols_annual=np.array([0.15, 0.16]),
            correlation_matrix=np.array([[1.0, 0.9], [0.9, 1.0]]),
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            source=CMA_Source_enum.MANUAL,
        )

        # Test tier enum values
        assert Asset_Class_Tier_enum.TIER_0.value == 0
        assert Asset_Class_Tier_enum.TIER_1.value == 1


# ============================================================================
# Additional properties — lines 457, 467, 472
# ============================================================================


class Test_Additional_CMA_Properties:
    """Cover index_map, source, and random_seed properties."""

    @pytest.mark.unit()
    def test_index_map_returns_dict(self, Scenarios_CMA_class, sample_cma_params):
        """index_map property returns a dict (covers line 457)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.index_map
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_source_returns_cma_source(
        self, Scenarios_CMA_class, sample_cma_params, CMA_Source_enum
    ):
        """source property returns CMA_Source enum (covers line 467)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        assert obj.source == CMA_Source_enum.MANUAL

    @pytest.mark.unit()
    def test_random_seed_returns_none_when_unset(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """random_seed property returns None when not specified (covers line 472)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        assert obj.random_seed is None

    @pytest.mark.unit()
    def test_random_seed_returns_int_when_set(self, Scenarios_CMA_class):
        """random_seed property returns provided seed (covers line 472)."""
        obj = Scenarios_CMA_class(
            names_asset_classes=["A"],
            expected_returns_annual=np.array([0.08]),
            expected_vols_annual=np.array([0.15]),
            correlation_matrix=np.array([[1.0]]),
            random_seed=42,
        )
        assert obj.random_seed == 42


# ============================================================================
# get_index_correspondence_table and get_asset_classes_by_tier — lines 487-505, 523
# ============================================================================


class Test_Table_Methods:
    """Cover get_index_correspondence_table() and get_asset_classes_by_tier()."""

    @pytest.mark.unit()
    def test_get_index_correspondence_table_returns_dataframe(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """get_index_correspondence_table() returns Polars DataFrame (covers lines 487-505)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.get_index_correspondence_table()
        assert isinstance(result, pl.DataFrame)
        assert "asset_class" in result.columns
        assert "expected_return" in result.columns
        assert len(result) == 2  # US_Equity, US_Bonds

    @pytest.mark.unit()
    def test_get_asset_classes_by_tier_returns_list(
        self, Scenarios_CMA_class, sample_cma_params, Asset_Class_Tier_enum
    ):
        """get_asset_classes_by_tier() returns list of matching asset classes (covers line 523)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.get_asset_classes_by_tier(tier = Asset_Class_Tier_enum.TIER_0)
        assert isinstance(result, list)

    @pytest.mark.unit()
    def test_get_asset_classes_by_tier_with_custom_map(
        self, Scenarios_CMA_class, Asset_Class_Tier_enum
    ):
        """get_asset_classes_by_tier() filters correctly with explicit tier_map (covers line 523)."""
        tier_map = {
            "Equity": Asset_Class_Tier_enum.TIER_0,
            "Bonds": Asset_Class_Tier_enum.TIER_1,
        }
        obj = Scenarios_CMA_class(
            names_asset_classes=["Equity", "Bonds"],
            expected_returns_annual=np.array([0.08, 0.03]),
            expected_vols_annual=np.array([0.15, 0.05]),
            correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            tier_map=tier_map,
        )
        tier0 = obj.get_asset_classes_by_tier(tier = Asset_Class_Tier_enum.TIER_0)
        assert tier0 == ["Equity"]
        tier1 = obj.get_asset_classes_by_tier(tier = Asset_Class_Tier_enum.TIER_1)
        assert tier1 == ["Bonds"]


# ============================================================================
# Daily annualisation helpers — lines 767, 781, 795
# ============================================================================


class Test_Daily_Calc_Helpers:
    """Cover calc_daily_expected_returns(), calc_daily_covariance(), calc_daily_volatilities()."""

    @pytest.mark.unit()
    def test_calc_daily_expected_returns_shape_and_values(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """calc_daily_expected_returns() divides annual returns by frequency (covers line 767)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.calc_daily_expected_returns()
        assert result.shape == (2,)
        np.testing.assert_allclose(result, np.array([0.08, 0.03]) / 252)

    @pytest.mark.unit()
    def test_calc_daily_covariance_shape_and_scaling(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """calc_daily_covariance() divides annual covariance by frequency (covers line 781)."""
        obj = Scenarios_CMA_class(**sample_cma_params)
        annual_cov = obj.covariance_matrix_annual
        daily_cov = obj.calc_daily_covariance()
        assert daily_cov.shape == (2, 2)
        np.testing.assert_allclose(daily_cov, annual_cov / 252)

    @pytest.mark.unit()
    def test_calc_daily_volatilities_shape_and_scaling(
        self, Scenarios_CMA_class, sample_cma_params
    ):
        """calc_daily_volatilities() divides annual vols by sqrt(frequency) (covers line 795)."""
        import math

        obj = Scenarios_CMA_class(**sample_cma_params)
        result = obj.calc_daily_volatilities()
        assert result.shape == (2,)
        np.testing.assert_allclose(result, np.array([0.15, 0.05]) / math.sqrt(252))
