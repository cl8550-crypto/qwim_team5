"""Unit tests for model_simulation_base module.

Tests for Simulation_Base abstract class, Simulation_Status enum,
and Aggregation_Method enum.
"""
# ruff: noqa: PLC0415, N803

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def Simulation_Base_class():
    """Import Simulation_Base abstract class."""
    from src.models.simulation.model_simulation_base import Simulation_Base

    return Simulation_Base


@pytest.fixture()
def Simulation_Status_enum():
    """Import Simulation_Status enum."""
    from src.models.simulation.model_simulation_base import Simulation_Status

    return Simulation_Status


@pytest.fixture()
def Aggregation_Method_enum():
    """Import Aggregation_Method enum."""
    from src.models.simulation.model_simulation_base import Aggregation_Method

    return Aggregation_Method


@pytest.fixture()
def concrete_simulation_class(Simulation_Base_class):
    """Create a minimal concrete subclass of Simulation_Base for testing."""

    class _Concrete_Simulation(Simulation_Base_class):
        """Thin concrete subclass that returns a canned result."""

        def run(self) -> pl.DataFrame:
            """Return a simple DataFrame for testing."""
            dates = [dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
            data = {
                "Date": dates,
                "Scenario_1": [100.0, 101.0, 102.0, 103.0, 104.0],
                "Scenario_2": [100.0, 99.0, 98.0, 97.0, 96.0],
                "Scenario_3": [100.0, 100.5, 101.0, 101.5, 102.0],
            }
            self.m_df_results = pl.DataFrame(data)
            return self.m_df_results

    return _Concrete_Simulation


@pytest.fixture()
def mock_scenarios():
    """Create a minimal Scenarios_Base subclass instance."""
    from src.num_methods.scenarios.scenarios_base import Scenarios_Base

    class _Mock_Scenarios(Scenarios_Base):
        """Tests for Mock Scenarios."""
        def generate(self) -> pl.DataFrame:
            """Generate."""
            return pl.DataFrame(
                {
                    "Date": [dt.date(2024, 1, 1)],
                    "A": [0.01],
                    "B": [0.02],
                },
            )

    return _Mock_Scenarios(
        names_components=["A", "B"],
        dates=[dt.date(2024, 1, 1)],
    )


# ======================================================================
# Simulation_Status enum
# ======================================================================


class Test_Simulation_Status_Enum:
    """Tests for the Simulation_Status enum."""

    @pytest.mark.unit()
    def test_members_exist(self, Simulation_Status_enum):
        """All expected members should be present."""
        assert hasattr(Simulation_Status_enum, "NOT_STARTED")
        assert hasattr(Simulation_Status_enum, "RUNNING")
        assert hasattr(Simulation_Status_enum, "COMPLETED")
        assert hasattr(Simulation_Status_enum, "FAILED")

    @pytest.mark.unit()
    def test_values_are_strings(self, Simulation_Status_enum):
        """Enum values should be descriptive strings."""
        for member in Simulation_Status_enum:
            assert isinstance(member.value, str)


# ======================================================================
# Aggregation_Method enum
# ======================================================================


class Test_Aggregation_Method_Enum:
    """Tests for the Aggregation_Method enum."""

    @pytest.mark.unit()
    def test_members_exist(self, Aggregation_Method_enum):
        """All expected members should be present."""
        assert hasattr(Aggregation_Method_enum, "MEAN")
        assert hasattr(Aggregation_Method_enum, "MEDIAN")
        assert hasattr(Aggregation_Method_enum, "PERCENTILE")


# ======================================================================
# Simulation_Base construction
# ======================================================================


class Test_Simulation_Base_Construction:
    """Tests for Simulation_Base constructor validation."""

    @pytest.mark.unit()
    def test_valid_construction(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Construction with valid parameters should succeed."""
        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.6, 0.4]),
            initial_value=1000.0,
            num_scenarios=100,
            name_simulation="Test Sim",
        )
        assert sim.num_components == 2
        assert sim.initial_value == 1000.0
        assert sim.num_scenarios == 100
        assert sim.name_simulation == "Test Sim"

    @pytest.mark.unit()
    def test_weights_normalized_when_not_summing_to_one(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Weights not summing to 1.0 should be auto-normalized."""
        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([3.0, 7.0]),
        )
        # Should normalize: [0.3, 0.7]
        assert np.isclose(np.sum(sim.weights), 1.0)

    @pytest.mark.unit()
    def test_invalid_scenarios_type_raises(self, concrete_simulation_class):
        """Passing non-Scenarios_Base should raise Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios="not_a_scenario",
                names_components=["A"],
                weights=np.array([1.0]),
            )

    @pytest.mark.unit()
    def test_empty_components_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Empty component list should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=[],
                weights=np.array([]),
            )

    @pytest.mark.unit()
    def test_wrong_weights_shape_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Mismatched weights shape should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([1.0]),  # shape (1,) != (2,)
            )

    @pytest.mark.unit()
    def test_non_finite_weights_raise(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """NaN or inf weights should be rejected before normalization."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input, match="finite"):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([np.nan, 0.5]),
            )

    @pytest.mark.unit()
    def test_zero_sum_weights_raise(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Zero-sum weights should be rejected instead of normalized."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input, match="non-zero"):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([0.0, 0.0]),
            )

    @pytest.mark.unit()
    def test_negative_initial_value_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Non-positive initial value should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([0.5, 0.5]),
                initial_value=-100.0,
            )

    @pytest.mark.unit()
    def test_bool_initial_value_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Boolean initial_value should raise instead of coercing to 1.0."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([0.5, 0.5]),
                initial_value=True,
            )

    @pytest.mark.unit()
    def test_non_finite_initial_value_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """NaN or inf initial_value should raise before storage."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_initial_value in (float("nan"), float("inf")):
            with pytest.raises(Exception_Validation_Input):
                concrete_simulation_class(
                    scenarios=mock_scenarios,
                    names_components=["A", "B"],
                    weights=np.array([0.5, 0.5]),
                    initial_value=item_initial_value,
                )

    @pytest.mark.unit()
    def test_zero_num_scenarios_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Zero or negative num_scenarios should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([0.5, 0.5]),
                num_scenarios=0,
            )

    @pytest.mark.unit()
    def test_bool_num_scenarios_raises(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Boolean num_scenarios should raise instead of coercing to 1."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            concrete_simulation_class(
                scenarios=mock_scenarios,
                names_components=["A", "B"],
                weights=np.array([0.5, 0.5]),
                num_scenarios=True,
            )


# ======================================================================
# Properties
# ======================================================================


class Test_Simulation_Base_Properties:
    """Tests for Simulation_Base properties."""

    @pytest.fixture()
    def sim_instance(self, concrete_simulation_class, mock_scenarios):
        """Return a constructed simulation."""
        return concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.6, 0.4]),
            initial_value=500.0,
            num_scenarios=50,
            name_simulation="PropTest",
        )

    @pytest.mark.unit()
    def test_names_components_returns_copy(self, sim_instance):
        """names_components should return a copy."""
        comps = sim_instance.names_components
        comps.append("C")
        assert len(sim_instance.names_components) == 2

    @pytest.mark.unit()
    def test_weights_returns_copy(self, sim_instance):
        """Mutating returned weights should not affect internal state."""
        w = sim_instance.weights
        w[0] = 999.0
        assert sim_instance.weights[0] != 999.0

    @pytest.mark.unit()
    def test_initial_status_is_not_started(self, sim_instance, Simulation_Status_enum):
        """Newly created simulation should be NOT_STARTED."""
        assert sim_instance.status == Simulation_Status_enum.NOT_STARTED

    @pytest.mark.unit()
    def test_df_results_is_none_before_run(self, sim_instance):
        """Results should be None before run() is called."""
        assert sim_instance.df_results is None

    @pytest.mark.unit()
    def test_df_results_returns_clone_after_run(self, sim_instance):
        """df_results should return a clone, not the internal DataFrame object."""
        sim_instance.run()

        returned = sim_instance.df_results

        assert returned is not None
        assert returned is not sim_instance.m_df_results
        assert returned.equals(sim_instance.m_df_results)


# ======================================================================
# Statistics helpers
# ======================================================================


class Test_Simulation_Base_Statistics:
    """Test get_summary_statistics and get_terminal_values."""

    @pytest.fixture()
    def sim_with_results(self, concrete_simulation_class, mock_scenarios):
        """Create a simulation and run it."""
        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
        )
        sim.run()
        return sim

    @pytest.mark.unit()
    def test_summary_statistics_columns(self, sim_with_results):
        """Summary statistics should contain expected columns."""
        stats = sim_with_results.get_summary_statistics()
        expected_cols = {"Date", "Mean", "Median", "Std", "P5", "P25", "P75", "P95", "Min", "Max"}
        assert expected_cols.issubset(set(stats.columns))

    @pytest.mark.unit()
    def test_summary_statistics_row_count(self, sim_with_results):
        """Stats rows should match results rows."""
        stats = sim_with_results.get_summary_statistics()
        assert stats.height == sim_with_results.m_df_results.height

    @pytest.mark.unit()
    def test_terminal_values_shape(self, sim_with_results):
        """Terminal values should have 1 row and N scenario columns."""
        tv = sim_with_results.get_terminal_values()
        assert tv.height == 1
        assert tv.width == 3  # 3 scenarios in the concrete class

    @pytest.mark.unit()
    def test_summary_raises_before_run(self, concrete_simulation_class, mock_scenarios):
        """get_summary_statistics before run should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
        )
        with pytest.raises(Exception_Calculation):
            sim.get_summary_statistics()

    @pytest.mark.unit()
    def test_terminal_values_raises_before_run(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """get_terminal_values before run should raise."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
        )
        with pytest.raises(Exception_Calculation):
            sim.get_terminal_values()

    @pytest.mark.unit()
    def test_summary_raises_when_results_have_no_scenario_columns(
        self,
        concrete_simulation_class,
        mock_scenarios,
    ):
        """Summary statistics should reject result frames with only a Date column."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        sim = concrete_simulation_class(
            scenarios=mock_scenarios,
            names_components=["A", "B"],
            weights=np.array([0.5, 0.5]),
        )
        sim.m_df_results = pl.DataFrame({"Date": [dt.date(2024, 1, 1)]})

        with pytest.raises(Exception_Calculation, match="No scenario columns"):
            sim.get_summary_statistics()

    @pytest.mark.unit()
    def test_repr(self, sim_with_results):
        """__repr__ should return a non-empty string."""
        r = repr(sim_with_results)
        assert "Simulation_Base" in r
