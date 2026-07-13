"""Unit tests for scenarios_base module.

This module contains comprehensive tests for the Scenarios_Base abstract base class
and related utilities in src/num_methods/scenarios/scenarios_base.py.
"""

import datetime as dt

import numpy as np
import polars as pl
import pytest


@pytest.fixture()
def Scenarios_Base_class():
    """Fixture to import Scenarios_Base class."""
    from src.num_methods.scenarios.scenarios_base import Scenarios_Base

    return Scenarios_Base


@pytest.fixture()
def Scenario_Data_Type_enum():
    """Fixture to import Scenario_Data_Type enum."""
    from src.num_methods.scenarios.scenarios_base import Scenario_Data_Type

    return Scenario_Data_Type


@pytest.fixture()
def Frequency_Time_Series_enum():
    """Fixture to import Frequency_Time_Series enum."""
    from src.num_methods.scenarios.scenarios_base import Frequency_Time_Series

    return Frequency_Time_Series


@pytest.fixture()
def concrete_scenarios_class(
    Scenarios_Base_class, Scenario_Data_Type_enum, Frequency_Time_Series_enum
):
    """Fixture creating a concrete implementation for testing.

    The concrete class accepts data_type, frequency, and dates as keyword
    arguments and forwards them to Scenarios_Base.__init__ in the correct
    positional order:

        super().__init__(names_components, dates, data_type, frequency, ...)
    """

    class ConcreteScenarios(Scenarios_Base_class):
        """Concrete implementation for testing abstract base class."""

        def __init__(
            self,
            names_components,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=None,
            num_days=252,
            num_scenarios=1,
        ):
            """Initialize with num_days and num_scenarios."""
            # If no dates supplied, generate business dates so base class
            # can derive num_dates.
            if dates is None:
                dates = self._generate_business_dates(start_date = dt.date(2024, 1, 1), num_days = num_days)

            super().__init__(
                names_components=names_components,
                dates=dates,
                data_type=data_type,
                frequency=frequency,
                num_scenarios=num_scenarios,
            )
            self._num_days_requested = num_days

        def generate(self):
            """Simple implementation that generates random returns."""
            dates = self.dates
            num_days = len(dates)
            n_components = self.num_components

            # Generate random returns
            data = np.random.randn(num_days, n_components) * 0.01

            # Build DataFrame with Date + component columns only (no Scenario column)
            scenario_data = {"Date": dates}
            for idx, component in enumerate(self.names_components):
                scenario_data[component] = data[:, idx]

            self.m_df_scenarios = pl.DataFrame(scenario_data)
            return self.m_df_scenarios

    return ConcreteScenarios


@pytest.fixture()
def sample_scenario_data():
    """Fixture providing sample scenario data."""
    dates = [dt.date(2024, 1, i) for i in range(1, 6)]
    return pl.DataFrame(
        {
            "Date": dates,
            "Stock": [0.01, -0.005, 0.02, 0.015, -0.01],
            "Bond": [0.002, 0.001, 0.003, 0.002, 0.001],
        }
    )


class Test_Scenario_Data_Type_Enum:
    """Tests for Scenario_Data_Type enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, Scenario_Data_Type_enum):
        """Test that all expected enum members exist."""
        assert hasattr(Scenario_Data_Type_enum, "RETURN_ARITHMETIC")
        assert hasattr(Scenario_Data_Type_enum, "RETURN_LOG")
        assert hasattr(Scenario_Data_Type_enum, "PRICE")
        assert hasattr(Scenario_Data_Type_enum, "INDEX_LEVEL")

    @pytest.mark.unit()
    def test_enum_values(self, Scenario_Data_Type_enum):
        """Test enum values are strings as expected."""
        assert isinstance(Scenario_Data_Type_enum.RETURN_ARITHMETIC.value, str)
        assert "Return" in Scenario_Data_Type_enum.RETURN_ARITHMETIC.value
        assert "Log" in Scenario_Data_Type_enum.RETURN_LOG.value


class Test_Frequency_Time_Series_Enum:
    """Tests for Frequency_Time_Series enum."""

    @pytest.mark.unit()
    def test_enum_members_exist(self, Frequency_Time_Series_enum):
        """Test that frequency enum members exist."""
        assert hasattr(Frequency_Time_Series_enum, "DAILY")
        assert hasattr(Frequency_Time_Series_enum, "WEEKLY")
        assert hasattr(Frequency_Time_Series_enum, "MONTHLY")

    @pytest.mark.unit()
    def test_enum_values_are_integers(self, Frequency_Time_Series_enum):
        """Test that frequency values represent periods per year."""
        # Should be approximate trading days per year
        assert Frequency_Time_Series_enum.DAILY.value == 252
        assert Frequency_Time_Series_enum.MONTHLY.value == 12


class Test_Scenarios_Base_Instantiation:
    """Tests for Scenarios_Base initialization."""

    @pytest.mark.unit()
    def test_cannot_instantiate_abstract_class(self, Scenarios_Base_class):
        """Test that abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Scenarios_Base_class(
                names_components=["Stock", "Bond"],
                data_type="Arithmetic Return",
                frequency=252,
            )

    @pytest.mark.unit()
    def test_concrete_class_can_be_instantiated(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that concrete implementation can be instantiated."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=10,
            num_scenarios=2,
        )
        assert obj is not None
        assert obj.num_components == 2

    @pytest.mark.unit()
    def test_initialization_with_dates(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test initialization with explicit dates."""
        dates = [dt.date(2024, 1, i) for i in range(1, 4)]
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=dates,
            num_scenarios=1,
        )
        assert obj.num_dates == 3

    @pytest.mark.unit()
    def test_empty_components_raises_error(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that empty component names raise validation error."""
        with pytest.raises(Exception):  # Exception_Validation_Input
            concrete_scenarios_class(
                names_components=[],
                data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series_enum.DAILY,
            )


class Test_Scenarios_Base_Properties:
    """Tests for Scenarios_Base property accessors."""

    @pytest.mark.unit()
    def test_names_components(
        self, concrete_scenarios_class, Scenario_Data_Type_enum, Frequency_Time_Series_enum
    ):
        """Test names_components property returns correct list."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond", "Cash"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj.names_components == ["Stock", "Bond", "Cash"]

    @pytest.mark.unit()
    def test_num_components(
        self, concrete_scenarios_class, Scenario_Data_Type_enum, Frequency_Time_Series_enum
    ):
        """Test num_components property returns correct count."""
        obj = concrete_scenarios_class(
            names_components=["A", "B", "C", "D"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj.num_components == 4

    @pytest.mark.unit()
    def test_data_type(
        self, concrete_scenarios_class, Scenario_Data_Type_enum, Frequency_Time_Series_enum
    ):
        """Test data_type property returns enum value."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_LOG,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj.data_type == Scenario_Data_Type_enum.RETURN_LOG

    @pytest.mark.unit()
    def test_frequency(
        self, concrete_scenarios_class, Scenario_Data_Type_enum, Frequency_Time_Series_enum
    ):
        """Test frequency property returns enum value."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.MONTHLY,
        )
        assert obj.frequency == Frequency_Time_Series_enum.MONTHLY


class Test_Scenarios_Base_Data_Access:
    """Tests for data access methods."""

    @pytest.mark.unit()
    def test_df_scenarios_returns_dataframe(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that df_scenarios returns Polars DataFrame after generation."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=10,
            num_scenarios=1,
        )
        obj.generate()

        result = obj.df_scenarios
        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "Stock" in result.columns
        assert "Bond" in result.columns

    @pytest.mark.unit()
    def test_get_component_series(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test get_component_series method for single component."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=10,
            num_scenarios=1,
        )
        obj.generate()

        stock_series = obj.get_component_series(component_name = "Stock")
        assert isinstance(stock_series, pl.Series)
        assert len(stock_series) == 10


class Test_Statistical_Methods:
    """Tests for statistical calculation methods."""

    @pytest.mark.unit()
    def test_calc_correlation_matrix(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test correlation matrix calculation."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=100,
            num_scenarios=1,
        )

        # Generate data
        obj.generate()

        corr_df = obj.calc_correlation_matrix()

        assert isinstance(corr_df, pl.DataFrame)

    @pytest.mark.unit()
    def test_calc_summary_statistics(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test summary statistics calculation."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=100,
            num_scenarios=1,
        )

        # Generate data
        obj.generate()

        stats_df = obj.calc_summary_statistics()

        assert isinstance(stats_df, pl.DataFrame)


class Test_Conversion_Methods:
    """Tests for data conversion methods (returns to prices)."""

    @pytest.mark.unit()
    def test_convert_returns_to_prices_arithmetic(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test converting arithmetic returns to prices."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=[dt.date(2024, 1, i) for i in range(1, 4)],
            num_scenarios=1,
        )

        # Override generated data with known returns
        returns_data = pl.DataFrame(
            {
                "Date": [dt.date(2024, 1, i) for i in range(1, 4)],
                "Stock": [0.10, 0.05, -0.05],  # 10%, 5%, -5%
            }
        )
        obj.m_df_scenarios = returns_data

        prices = obj.convert_returns_to_prices(initial_prices=[100.0])

        assert isinstance(prices, pl.DataFrame)
        assert "Stock" in prices.columns
        # Check price calculation: 100 * 1.1 = 110, 110 * 1.05 = 115.5, 115.5 * 0.95 = 109.725
        stock_prices = prices["Stock"].to_list()
        assert np.isclose(stock_prices[0], 110.0, rtol=1e-5)
        assert np.isclose(stock_prices[1], 115.5, rtol=1e-5)
        assert np.isclose(stock_prices[2], 109.725, rtol=1e-5)

    @pytest.mark.unit()
    def test_convert_returns_to_prices_log(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test converting log returns to prices."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_LOG,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=[dt.date(2024, 1, i) for i in range(1, 4)],
            num_scenarios=1,
        )

        # Create log return data
        log_returns_data = pl.DataFrame(
            {
                "Date": [dt.date(2024, 1, i) for i in range(1, 4)],
                "Stock": [0.10, 0.05, -0.05],
            }
        )
        obj.m_df_scenarios = log_returns_data

        prices = obj.convert_returns_to_prices(initial_prices=[100.0])

        assert isinstance(prices, pl.DataFrame)
        # Log returns use exponential: price = 100 * exp(cumulative_log_return)
        stock_prices = prices["Stock"].to_list()
        assert stock_prices[0] > 100.0  # Should increase with positive log return


class Test_CSV_Input_Output:
    """Tests for CSV save/load functionality."""

    @pytest.mark.unit()
    def test_save_scenarios_to_csv(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        tmp_path,
    ):
        """Test saving scenarios to CSV file."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
            num_scenarios=1,
        )

        obj.generate()

        # Save to temporary path
        output_path = tmp_path / "test_scenarios.csv"
        obj.to_csv(path = str(output_path))

        assert output_path.exists()

        # Load and verify
        loaded = pl.read_csv(output_path)
        assert "Date" in loaded.columns
        assert "Stock" in loaded.columns

    @pytest.mark.unit()
    def test_load_scenarios_from_csv(
        self,
        Scenarios_Base_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        tmp_path,
    ):
        """Test loading scenarios from CSV file."""
        # Create a sample CSV (no Scenario column - base class does not use it)
        sample_data = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "Stock": [0.01, -0.005],
                "Bond": [0.002, 0.001],
            }
        )

        csv_path = tmp_path / "sample.csv"
        sample_data.write_csv(csv_path)

        # Load using class method (from_csv, not load_from_csv)
        obj = Scenarios_Base_class.from_csv(
            path = str(csv_path),
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj is not None
        assert obj.num_components == 2
        assert "Stock" in obj.names_components
        assert "Bond" in obj.names_components


class Test_Validation_Methods:
    """Tests for validation functionality."""

    @pytest.mark.unit()
    def test_validate_scenarios_after_generation(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that validation passes after scenario generation."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=10,
            num_scenarios=1,
        )

        obj.generate()

        # validate_scenarios should return True on well-formed data
        assert obj.validate_scenarios() is True

    @pytest.mark.unit()
    def test_validate_component_names(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validation of component names."""
        # Should not raise error with valid names
        obj = concrete_scenarios_class(
            names_components=["Stock_US", "Bond_10Y", "Cash_USD"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )
        assert obj.num_components == 3


class Test_Business_Dates_Generation:
    """Tests for business dates generation."""

    @pytest.mark.unit()
    def test_generate_business_dates_excludes_weekends(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that generated business dates exclude weekends."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        # Generate 10 business days starting from Monday, Jan 1, 2024
        dates = obj._generate_business_dates(start_date = dt.date(2024, 1, 1), num_days = 10)

        assert len(dates) == 10

        # Check no weekends (Saturday=5, Sunday=6)
        for date in dates:
            assert date.weekday() < 5  # Monday=0, Friday=4

    @pytest.mark.unit()
    def test_generate_business_dates_sequential(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test that generated dates are in sequential order."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        dates = obj._generate_business_dates(start_date = dt.date(2024, 1, 1), num_days = 20)

        # Check dates are strictly increasing
        for i in range(len(dates) - 1):
            assert dates[i] < dates[i + 1]


class Test_Edge_Cases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit()
    def test_single_component_scenarios(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test scenarios with single component."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
            num_scenarios=1,
        )

        data = obj.generate()

        assert data.shape[0] == 5
        assert "Stock" in data.columns

    @pytest.mark.unit()
    def test_large_number_of_components(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test scenarios with large number of components."""
        # 50 components
        components = [f"Asset_{i:02d}" for i in range(50)]

        obj = concrete_scenarios_class(
            names_components=components,
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
        )

        assert obj.num_components == 50

    @pytest.mark.unit()
    def test_invalid_initial_prices_length(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test error when initial prices don't match components."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
            num_scenarios=1,
        )

        obj.generate()

        # Provide wrong number of initial prices
        with pytest.raises(Exception):  # Should raise validation error
            obj.convert_returns_to_prices(initial_prices=[100.0])  # Need 2, gave 1


# ======================================================================
# Additional test classes for missing coverage
# ======================================================================


@pytest.mark.unit()
class Class_Test_Init_Validation_Extra:
    """Tests for __init__ validation branches not covered by existing tests."""

    @pytest.mark.unit()
    def Test_Non_String_Component_Name_Raises(self):
        """Test that non-string component name raises Exception_Validation_Input."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=[42],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Empty_String_Component_Name_Raises(self):
        """Test that empty string component name raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=[""],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Whitespace_Component_Name_Raises(self):
        """Test that whitespace-only component name raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["   "],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Duplicate_Component_Names_Raises(self):
        """Test that duplicate component names raise."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception):
            _Concrete(
                names_components=["A", "A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Invalid_Data_Type_Raises(self):
        """Test that invalid data_type (string) raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type="Price",
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Invalid_Frequency_Raises(self):
        """Test that invalid frequency (integer) raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=252,
            )

    @pytest.mark.unit()
    def Test_Num_Scenarios_Zero_Raises(self):
        """Test that num_scenarios=0 raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
                num_scenarios=0,
            )

    @pytest.mark.unit()
    def Test_Num_Scenarios_Negative_Raises(self):
        """Test that num_scenarios < 0 raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
                num_scenarios=-1,
            )

    @pytest.mark.unit()
    def Test_Num_Scenarios_Float_Raises(self):
        """Test that float num_scenarios raises."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
                num_scenarios=1.5,
            )

    @pytest.mark.unit()
    def Test_Num_Scenarios_Bool_Raises(self):
        """Test that boolean num_scenarios raises instead of coercing to 1."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception_Validation_Input):
            _Concrete(
                names_components=["A"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
                num_scenarios=True,
            )

    @pytest.mark.unit()
    def Test_Dates_None_Initializes_Empty(self):
        """Test that dates=None initializes m_dates as empty list (lines 240-241)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        obj = _Concrete(
            names_components=["A"],
            dates=None,
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        assert obj.m_dates == []
        assert obj.m_num_dates == 0


@pytest.mark.unit()
class Class_Test_Properties_Extra:
    """Tests for properties not covered by existing tests."""

    @pytest.mark.unit()
    def Test_Num_Scenarios_Property(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test num_scenarios property returns stored value (line 292)."""
        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
            num_scenarios=3,
        )
        assert obj.num_scenarios == 3

    @pytest.mark.unit()
    def Test_Name_Scenarios_Property(self):
        """Test name_scenarios property returns stored label (line 297)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        obj = _Concrete(
            names_components=["A"],
            dates=[dt.date(2024, 1, 1)],
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
            name_scenarios="My Scenario Set",
        )
        assert obj.name_scenarios == "My Scenario Set"

    @pytest.mark.unit()
    def Test_Df_Scenarios_None_Before_Generate(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test df_scenarios returns None before generate() is called (line 304)."""
        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        assert obj.df_scenarios is None


@pytest.mark.unit()
class Class_Test_Validate_Scenarios_Extra:
    """Tests for validate_scenarios failure branches."""

    @pytest.mark.unit()
    def Test_Validate_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validate_scenarios raises when df not generated (line 351)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.validate_scenarios()

    @pytest.mark.unit()
    def Test_Validate_Column_Mismatch_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validate_scenarios raises on column mismatch (line 363)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(
                    [dt.date(2024, 1, i) for i in range(1, 6)], dtype=pl.Date
                ),
                "WrongCol": pl.Series([0.01] * 5, dtype=pl.Float64),
            }
        )
        with pytest.raises(Exception_Validation_Input):
            obj.validate_scenarios()

    @pytest.mark.unit()
    def Test_Validate_Bad_Date_Dtype_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validate_scenarios raises for non-Date dtype in Date col (line 373)."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series([1, 2, 3, 4, 5], dtype=pl.Int64),
                "Stock": pl.Series([0.01, 0.02, 0.03, 0.04, 0.05], dtype=pl.Float64),
            }
        )
        with pytest.raises(Exception):
            obj.validate_scenarios()

    @pytest.mark.unit()
    def Test_Validate_Non_Float64_Col_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validate_scenarios raises for non-Float64 numeric column (line 383)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(
                    [dt.date(2024, 1, i) for i in range(1, 6)], dtype=pl.Date
                ),
                "Stock": pl.Series([1, 2, 3, 4, 5], dtype=pl.Int32),
            }
        )
        with pytest.raises(Exception_Validation_Input):
            obj.validate_scenarios()

    @pytest.mark.unit()
    def Test_Validate_Null_Values_Logs_Warning(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test validate_scenarios logs warning for null values (line 395)."""
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(
                    [dt.date(2024, 1, i) for i in range(1, 6)], dtype=pl.Date
                ),
                "Stock": pl.Series([0.01, None, 0.03, 0.04, 0.05], dtype=pl.Float64),
            }
        )
        result = obj.validate_scenarios()
        assert result is True


@pytest.mark.unit()
class Class_Test_Data_Access_None_Extra:
    """Tests for data-access methods when df_scenarios is None."""

    @pytest.mark.unit()
    def Test_Get_Component_Series_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test get_component_series raises when df not generated (line 431)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.get_component_series(component_name = "A")

    @pytest.mark.unit()
    def Test_Get_Component_Series_Unknown_Name_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test get_component_series raises for unknown component (line 439)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.generate()
        with pytest.raises(Exception_Validation_Input):
            obj.get_component_series(component_name = "Unknown")

    @pytest.mark.unit()
    def Test_Get_Returns_Matrix_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test get_returns_matrix raises when df not generated (line 466)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.get_returns_matrix()

    @pytest.mark.unit()
    def Test_Get_Date_Range_No_Dates_Raises(self):
        """Test get_date_range raises when no dates (lines 488-494)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        obj = _Concrete(
            names_components=["A"],
            dates=None,
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        with pytest.raises(Exception):
            obj.get_date_range()

    @pytest.mark.unit()
    def Test_Get_Date_Range_Returns_First_And_Last(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test get_date_range returns first and last date (line 495)."""
        dates = [dt.date(2024, 1, 2), dt.date(2024, 1, 3), dt.date(2024, 1, 4)]
        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=dates,
        )
        start, end = obj.get_date_range()
        assert start == dt.date(2024, 1, 2)
        assert end == dt.date(2024, 1, 4)


@pytest.mark.unit()
class Class_Test_Filter_Select_Extra:
    """Tests for filter_by_date_range and select_components missing branches."""

    @pytest.mark.unit()
    def Test_Filter_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test filter_by_date_range raises when df not generated (lines 521-527)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.filter_by_date_range(start_date = dt.date(2024, 1, 1), end_date = dt.date(2024, 1, 5))

    @pytest.mark.unit()
    def Test_Filter_Returns_Filtered_DataFrame(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test filter_by_date_range returns filtered rows (line 529)."""
        dates = [dt.date(2024, 1, i) for i in range(1, 6)]
        obj = concrete_scenarios_class(
            names_components=["Stock"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=dates,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(dates, dtype=pl.Date),
                "Stock": pl.Series(
                    [0.01, 0.02, 0.03, 0.04, 0.05], dtype=pl.Float64
                ),
            }
        )
        result = obj.filter_by_date_range(start_date = dt.date(2024, 1, 2), end_date = dt.date(2024, 1, 4))
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    @pytest.mark.unit()
    def Test_Select_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test select_components raises when df not generated (lines 549-555)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A", "B"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.select_components(component_names = ["A"])

    @pytest.mark.unit()
    def Test_Select_Invalid_Component_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test select_components raises for invalid component (lines 558-564)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A", "B"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.generate()
        with pytest.raises(Exception_Validation_Input):
            obj.select_components(component_names = ["A", "Unknown"])

    @pytest.mark.unit()
    def Test_Select_Returns_Subset_Df(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test select_components returns correct subset (line 566)."""
        obj = concrete_scenarios_class(
            names_components=["A", "B", "C"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.generate()
        result = obj.select_components(component_names = ["A", "C"])
        assert isinstance(result, pl.DataFrame)
        assert "Date" in result.columns
        assert "A" in result.columns
        assert "C" in result.columns
        assert "B" not in result.columns


@pytest.mark.unit()
class Class_Test_Convert_Prices_To_Returns:
    """Tests for convert_prices_to_returns method (lines 602-629)."""

    @pytest.mark.unit()
    def Test_Wrong_Data_Type_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test raises Exception_Calculation for RETURN_ARITHMETIC type (lines 602-609)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        obj.generate()
        with pytest.raises(Exception_Calculation):
            obj.convert_prices_to_returns()

    @pytest.mark.unit()
    def Test_Price_Data_None_Df_Raises(self):
        """Test raises when PRICE type but df not generated (lines 611-617)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        obj = _Concrete(
            names_components=["A"],
            dates=[dt.date(2024, 1, i) for i in range(1, 6)],
            data_type=Scenario_Data_Type.PRICE,
            frequency=Frequency_Time_Series.DAILY,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.convert_prices_to_returns()

    @pytest.mark.unit()
    def Test_Price_Arithmetic_Returns(self):
        """Test arithmetic return calculation from PRICE data (lines 619-628)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        dates = [dt.date(2024, 1, i) for i in range(1, 6)]
        obj = _Concrete(
            names_components=["Stock"],
            dates=dates,
            data_type=Scenario_Data_Type.PRICE,
            frequency=Frequency_Time_Series.DAILY,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(dates, dtype=pl.Date),
                "Stock": pl.Series(
                    [100.0, 110.0, 105.0, 115.0, 110.0], dtype=pl.Float64
                ),
            }
        )
        result = obj.convert_prices_to_returns(log_returns=False)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 4

    @pytest.mark.unit()
    def Test_Price_Log_Returns(self):
        """Test log return calculation from PRICE data (line 622 branch)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        dates = [dt.date(2024, 1, i) for i in range(1, 6)]
        obj = _Concrete(
            names_components=["Stock"],
            dates=dates,
            data_type=Scenario_Data_Type.PRICE,
            frequency=Frequency_Time_Series.DAILY,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(dates, dtype=pl.Date),
                "Stock": pl.Series(
                    [100.0, 110.0, 105.0, 115.0, 110.0], dtype=pl.Float64
                ),
            }
        )
        result = obj.convert_prices_to_returns(log_returns=True)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 4

    @pytest.mark.unit()
    def Test_Index_Level_Arithmetic_Returns(self):
        """Test arithmetic returns from INDEX_LEVEL type."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        dates = [dt.date(2024, 1, i) for i in range(1, 5)]
        obj = _Concrete(
            names_components=["Index"],
            dates=dates,
            data_type=Scenario_Data_Type.INDEX_LEVEL,
            frequency=Frequency_Time_Series.DAILY,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(dates, dtype=pl.Date),
                "Index": pl.Series([100.0, 102.0, 101.0, 103.0], dtype=pl.Float64),
            }
        )
        result = obj.convert_prices_to_returns(log_returns=False)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3


@pytest.mark.unit()
class Class_Test_Convert_Returns_Extra:
    """Tests for convert_returns_to_prices extra branches (lines 660, 666, 674)."""

    @pytest.mark.unit()
    def Test_Price_Data_Type_Raises(self):
        """Test raises Exception_Calculation for PRICE type (line 660)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        dates = [dt.date(2024, 1, i) for i in range(1, 6)]
        obj = _Concrete(
            names_components=["A"],
            dates=dates,
            data_type=Scenario_Data_Type.PRICE,
            frequency=Frequency_Time_Series.DAILY,
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(dates, dtype=pl.Date),
                "A": pl.Series([100.0, 101.0, 102.0, 103.0, 104.0], dtype=pl.Float64),
            }
        )
        with pytest.raises(Exception_Calculation):
            obj.convert_returns_to_prices()

    @pytest.mark.unit()
    def Test_Return_Data_None_Df_Raises(self):
        """Test raises when RETURN_ARITHMETIC type but df not generated (line 666)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        obj = _Concrete(
            names_components=["A"],
            dates=[dt.date(2024, 1, i) for i in range(1, 6)],
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.convert_returns_to_prices()

    @pytest.mark.unit()
    def Test_Initial_Prices_None_Uses_Default(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test initial_prices=None defaults to [100.0]*n (line 674)."""
        obj = concrete_scenarios_class(
            names_components=["A", "B"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            dates=[dt.date(2024, 1, i) for i in range(1, 4)],
        )
        obj.m_df_scenarios = pl.DataFrame(
            {
                "Date": pl.Series(
                    [dt.date(2024, 1, i) for i in range(1, 4)], dtype=pl.Date
                ),
                "A": pl.Series([0.01, 0.02, 0.03], dtype=pl.Float64),
                "B": pl.Series([-0.01, 0.01, -0.02], dtype=pl.Float64),
            }
        )
        result = obj.convert_returns_to_prices(initial_prices=None)
        assert isinstance(result, pl.DataFrame)
        assert "A" in result.columns
        assert "B" in result.columns


@pytest.mark.unit()
class Class_Test_Calc_Stats_None:
    """Tests for calc_* methods when df_scenarios is None."""

    @pytest.mark.unit()
    def Test_Calc_Summary_Statistics_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test calc_summary_statistics raises when df not generated (line 718)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.calc_summary_statistics()

    @pytest.mark.unit()
    def Test_Calc_Correlation_Matrix_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test calc_correlation_matrix raises when df not generated (line 753)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.calc_correlation_matrix()

    @pytest.mark.unit()
    def Test_Calc_Covariance_Matrix_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test calc_covariance_matrix raises when df not generated (lines 781-787)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.calc_covariance_matrix()

    @pytest.mark.unit()
    def Test_Calc_Covariance_Matrix_Success(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test calc_covariance_matrix full computation path (lines 789-799)."""
        obj = concrete_scenarios_class(
            names_components=["Stock", "Bond"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=100,
        )
        obj.generate()
        result = obj.calc_covariance_matrix()
        assert isinstance(result, pl.DataFrame)
        assert "component" in result.columns
        assert "Stock" in result.columns
        assert "Bond" in result.columns


@pytest.mark.unit()
class Class_Test_To_CSV_None:
    """Tests for to_csv when df_scenarios is None."""

    @pytest.mark.unit()
    def Test_To_CSV_None_Df_Raises(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
        tmp_path,
    ):
        """Test to_csv raises when df not generated (line 814)."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        with pytest.raises(Exception_Validation_Input):
            obj.to_csv(path = str(tmp_path / "output.csv"))


@pytest.mark.unit()
class Class_Test_From_CSV_Extra:
    """Tests for from_csv extra branches."""

    @pytest.mark.unit()
    def Test_From_CSV_No_Date_Column_Raises(self, tmp_path):
        """Test from_csv raises when CSV has no Date column (line 864)."""
        from src.num_methods.scenarios.scenarios_base import Scenarios_Base

        df = pl.DataFrame(
            {
                "Stock": pl.Series([0.01, -0.01], dtype=pl.Float64),
                "Bond": pl.Series([0.002, 0.001], dtype=pl.Float64),
            }
        )
        csv_path = tmp_path / "no_date.csv"
        df.write_csv(csv_path)
        with pytest.raises(Exception):
            Scenarios_Base.from_csv(path = str(csv_path))

    @pytest.mark.unit()
    def Test_From_CSV_String_Dates_Casts_To_Date(self, tmp_path):
        """Test from_csv with Utf8 Date column casts to pl.Date (lines 872-875)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "Stock": [0.01, -0.005, 0.02],
            }
        )
        csv_path = tmp_path / "string_date.csv"
        df.write_csv(csv_path)
        obj = Scenarios_Base.from_csv(
            path = str(csv_path),
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        assert obj.num_dates == 3
        assert obj.num_components == 1

    @pytest.mark.unit()
    def Test_From_CSV_Non_Utf8_Date_Skips_Cast(self, tmp_path):
        """Test from_csv with integer Date column skips Utf8 cast (branch 872->877)."""
        from src.num_methods.scenarios.scenarios_base import Scenarios_Base

        # Integer Date column: polars reads as Int64, not Utf8, so cast is skipped.
        # _parse_dates then fails on int values -> Exception_Validation_Input.
        df = pl.DataFrame(
            {
                "Date": pl.Series([20240101, 20240102], dtype=pl.Int64),
                "Stock": pl.Series([0.01, -0.01], dtype=pl.Float64),
            }
        )
        csv_path = tmp_path / "int_date.csv"
        df.write_csv(csv_path)
        with pytest.raises(Exception):
            Scenarios_Base.from_csv(path = str(csv_path))

    @pytest.mark.unit()
    def Test_From_CSV_Generate_Returns_Df(self, tmp_path):
        """Test _Loaded_Scenarios.generate() returns m_df_scenarios (line 891)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "Stock": [0.01, -0.01],
            }
        )
        csv_path = tmp_path / "gen_test.csv"
        df.write_csv(csv_path)
        obj = Scenarios_Base.from_csv(
            path = str(csv_path),
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        result = obj.generate()
        assert isinstance(result, pl.DataFrame)


@pytest.mark.unit()
class Class_Test_Parse_Dates_Extra:
    """Tests for _parse_dates static method branches."""

    @pytest.mark.unit()
    def Test_Parse_Dates_Datetime_Objects(self):
        """Test _parse_dates accepts datetime.datetime objects (line 932)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        datetimes = [
            dt.datetime(2024, 1, 3, 9, 30),
            dt.datetime(2024, 1, 2, 10, 0),
        ]
        obj = _Concrete(
            names_components=["A"],
            dates=datetimes,
            data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series.DAILY,
        )
        assert obj.num_dates == 2
        assert obj.m_dates[0] == dt.date(2024, 1, 2)

    @pytest.mark.unit()
    def Test_Parse_Dates_Invalid_String_Raises(self):
        """Test _parse_dates raises for invalid ISO string (lines 935-944)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception):
            _Concrete(
                names_components=["A"],
                dates=["not-a-valid-date"],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )

    @pytest.mark.unit()
    def Test_Parse_Dates_Unsupported_Type_Raises(self):
        """Test _parse_dates raises for unsupported type (line 946)."""
        from src.num_methods.scenarios.scenarios_base import (
            Frequency_Time_Series,
            Scenario_Data_Type,
            Scenarios_Base,
        )

        class _Concrete(Scenarios_Base):
            def generate(self):
                return self.m_df_scenarios

        with pytest.raises(Exception):
            _Concrete(
                names_components=["A"],
                dates=[20240101],
                data_type=Scenario_Data_Type.RETURN_ARITHMETIC,
                frequency=Frequency_Time_Series.DAILY,
            )


@pytest.mark.unit()
class Class_Test_Dunder_Methods:
    """Tests for __repr__ and __len__ dunder methods."""

    @pytest.mark.unit()
    def Test_Repr_Returns_String(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test __repr__ returns a descriptive string (line 991)."""
        obj = concrete_scenarios_class(
            names_components=["A", "B"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=5,
        )
        r = repr(obj)
        assert isinstance(r, str)
        assert "Arithmetic Return" in r
        assert "2" in r

    @pytest.mark.unit()
    def Test_Len_Returns_Num_Dates(
        self,
        concrete_scenarios_class,
        Scenario_Data_Type_enum,
        Frequency_Time_Series_enum,
    ):
        """Test __len__ returns num_dates (line 1001)."""
        obj = concrete_scenarios_class(
            names_components=["A"],
            data_type=Scenario_Data_Type_enum.RETURN_ARITHMETIC,
            frequency=Frequency_Time_Series_enum.DAILY,
            num_days=10,
        )
        assert len(obj) == 10
        assert len(obj) == obj.num_dates
