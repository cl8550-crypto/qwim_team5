"""Unit tests for Portfolio_Rebalancing_Base abstract base class.

Covers construction, properties, shared validators, and helper methods,
using a minimal concrete stub that implements the three abstract methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from datetime import datetime

import numpy as np
import polars as pl
import pytest

from src.models.portfolio_rebalancing.portfolio_rebalancing_base import (
    Portfolio_Rebalancing_Base,
    REBALANCING_STRATEGY_STATUS_CONFIGURED,
    Rebalancing_Strategy_Status,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Minimal concrete stub
# =============================================================================

_NAMES_3 = ["A", "B", "C"]
_WEIGHTS_3 = np.array([0.5, 0.3, 0.2])


class _ConcreteStrategy(Portfolio_Rebalancing_Base):
    """Minimal concrete subclass for testing the base-class API."""

    def configure(
        self,
        target_weights: np.ndarray,
        names_assets: list[str],
    ) -> _ConcreteStrategy:
        """Configure."""
        w = self._validate_weights_array(weights = target_weights, field_name="target_weights")
        self._validate_asset_names(names_assets = names_assets, n_assets_expected=len(w))
        self.m_target_weights = w.copy()
        self.m_names_assets = list(names_assets)
        self.m_status = REBALANCING_STRATEGY_STATUS_CONFIGURED
        return self

    def should_rebalance(
        self,
        current_weights: np.ndarray,
        *,
        current_date: datetime | None = None,
    ) -> bool:
        """Should rebalance."""
        self._check_is_configured()
        return True  # always rebalance for testing

    def rebalance(
        self,
        current_weights: np.ndarray,
        *,
        current_date: datetime | None = None,
        portfolio_value: float = 1_000_000.0,
    ) -> pl.DataFrame:
        """Rebalance."""
        self._check_is_configured()
        assert self.m_target_weights is not None
        w = self._validate_weights_array(weights = current_weights, field_name="current_weights")
        pv = self._validate_portfolio_value(portfolio_value = portfolio_value)
        target: np.ndarray = self.m_target_weights
        drift = w - target
        trade_w = target - w
        trade_v = trade_w * pv
        costs = np.zeros(len(w))
        return pl.DataFrame(
            {
                "Asset": self.m_names_assets,
                "Current_Weight": w.tolist(),
                "Target_Weight": target.tolist(),
                "Drift": drift.tolist(),
                "Trade_Weight": trade_w.tolist(),
                "Trade_Value": trade_v.tolist(),
                "Cost": costs.tolist(),
            },
        )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def strategy() -> _ConcreteStrategy:
    """Strategy."""
    return _ConcreteStrategy()


@pytest.fixture()
def configured_strategy() -> _ConcreteStrategy:
    """Configured strategy."""
    s = _ConcreteStrategy()
    s.configure(target_weights = _WEIGHTS_3, names_assets = _NAMES_3)
    return s


@pytest.fixture()
def rebalance_result(configured_strategy: _ConcreteStrategy) -> pl.DataFrame:
    """Rebalance result."""
    current = np.array([0.55, 0.25, 0.20])
    return configured_strategy.rebalance(current_weights = current, portfolio_value=100_000.0)


# =============================================================================
# Tests: Rebalancing_Strategy_Status enum
# =============================================================================


@pytest.mark.unit()
class Class_Test_Rebalancing_Strategy_Status:
    """Tests for the Rebalancing_Strategy_Status enum."""

    def Test_Not_Configured_Value(self) -> None:
        """Test that not Configured Value."""
        assert Rebalancing_Strategy_Status.NOT_CONFIGURED.value == "Not Configured"

    def Test_Configured_Value(self) -> None:
        """Test that configured Value."""
        assert Rebalancing_Strategy_Status.CONFIGURED.value == "Configured"

    def Test_Failed_Value(self) -> None:
        """Test that failed Value."""
        assert Rebalancing_Strategy_Status.FAILED.value == "Failed"

    def Test_Enum_Has_Three_Members(self) -> None:
        """Test that enum Has Three Members."""
        members = list(Rebalancing_Strategy_Status)
        assert len(members) == 3


# =============================================================================
# Tests: construction
# =============================================================================


@pytest.mark.unit()
class Class_Test_Portfolio_Rebalancing_Base_Construction:
    """Tests for Portfolio_Rebalancing_Base constructor."""

    def Test_Default_Name_Accepted(self) -> None:
        """Test that default Name Accepted."""
        s = _ConcreteStrategy()
        assert isinstance(s.name_strategy, str)
        assert len(s.name_strategy) > 0

    def Test_Custom_Name_Accepted(self) -> None:
        """Test that custom Name Accepted."""
        s = _ConcreteStrategy(name_strategy="My Strategy")
        assert s.name_strategy == "My Strategy"

    def Test_Name_Stripped(self) -> None:
        """Test that name Stripped."""
        s = _ConcreteStrategy(name_strategy="  Trim Me  ")
        assert s.name_strategy == "Trim Me"

    def Test_Empty_Name_Raises(self) -> None:
        """Test that empty Name Raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteStrategy(name_strategy="")

    def Test_Whitespace_Name_Raises(self) -> None:
        """Test that whitespace Name Raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteStrategy(name_strategy="   ")

    def Test_Non_String_Name_Raises(self) -> None:
        """Test that non String Name Raises."""
        with pytest.raises(Exception_Validation_Input):
            _ConcreteStrategy(name_strategy=42)  # type: ignore[arg-type]

    def Test_Abstract_Class_Not_Instantiable(self) -> None:
        """Test that abstract Class Not Instantiable."""
        with pytest.raises(TypeError):
            Portfolio_Rebalancing_Base()  # type: ignore[abstract]

    def Test_Initial_Status_Not_Configured(self, strategy: _ConcreteStrategy) -> None:
        """Test that initial Status Not Configured."""
        assert strategy.status == Rebalancing_Strategy_Status.NOT_CONFIGURED

    def Test_Initial_Is_Configured_False(self, strategy: _ConcreteStrategy) -> None:
        """Test that initial Is Configured False."""
        assert strategy.is_configured is False

    def Test_Initial_Parameters_Empty(self, strategy: _ConcreteStrategy) -> None:
        """Test that initial Parameters Empty."""
        assert strategy.parameters == {}

    def Test_Initial_N_Assets_Zero(self, strategy: _ConcreteStrategy) -> None:
        """Test that initial N Assets Zero."""
        assert strategy.n_assets == 0


# =============================================================================
# Tests: properties
# =============================================================================


@pytest.mark.unit()
class Class_Test_Portfolio_Rebalancing_Base_Properties:
    """Tests for Portfolio_Rebalancing_Base properties."""

    def Test_Is_Configured_True_After_Configure(
        self, configured_strategy: _ConcreteStrategy,
    ) -> None:
        """Test that is Configured True After Configure."""
        assert configured_strategy.is_configured is True

    def Test_Status_Configured_After_Configure(
        self, configured_strategy: _ConcreteStrategy,
    ) -> None:
        """Test that status Configured After Configure."""
        assert configured_strategy.status == Rebalancing_Strategy_Status.CONFIGURED

    def Test_Target_Weights_Returns_Copy(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that target Weights Returns Copy."""
        w = configured_strategy.target_weights
        assert w is not None
        w[0] = 999.0
        np.testing.assert_array_equal(configured_strategy.target_weights, _WEIGHTS_3)

    def Test_Target_Weights_None_Before_Configure(self, strategy: _ConcreteStrategy) -> None:
        """Test that target Weights None Before Configure."""
        assert strategy.target_weights is None

    def Test_Names_Assets_Returns_Copy(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that names Assets Returns Copy."""
        names = configured_strategy.names_assets
        names.append("EXTRA")
        assert "EXTRA" not in configured_strategy.names_assets

    def Test_Names_Assets_Empty_Before_Configure(self, strategy: _ConcreteStrategy) -> None:
        """Test that names Assets Empty Before Configure."""
        assert strategy.names_assets == []

    def Test_N_Assets_Correct_After_Configure(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that n Assets Correct After Configure."""
        assert configured_strategy.n_assets == 3

    def Test_Parameters_Returns_Copy(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that parameters Returns Copy."""
        params = configured_strategy.parameters
        params["injected"] = 1.0
        assert "injected" not in configured_strategy.parameters


# =============================================================================
# Tests: _validate_weights_array
# =============================================================================


@pytest.mark.unit()
class Class_Test_Validate_Weights_Array:
    """Tests for the _validate_weights_array helper."""

    def Test_Valid_1D_Sums_To_One(self, strategy: _ConcreteStrategy) -> None:
        """Test that valid 1D Sums To One."""
        w = strategy._validate_weights_array(weights = _WEIGHTS_3, field_name="w")
        np.testing.assert_allclose(w.sum(), 1.0, atol=1e-9)

    def Test_Returns_Ndarray(self, strategy: _ConcreteStrategy) -> None:
        """Test that returns Ndarray."""
        result = strategy._validate_weights_array(weights = _WEIGHTS_3, field_name="w")
        assert isinstance(result, np.ndarray)

    def Test_None_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that none Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = None, field_name="w")  # type: ignore[arg-type]

    def Test_2D_Array_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that 2D Array Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([[0.5, 0.5]]), field_name="w")

    def Test_Empty_Array_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that empty Array Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([]), field_name="w")

    def Test_Negative_Weight_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that negative Weight Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([0.6, -0.1, 0.5]), field_name="w")

    def Test_Nan_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that nan Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([float("nan"), 0.5, 0.5]), field_name="w")

    def Test_Inf_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that inf Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([float("inf"), 0.5, 0.5]), field_name="w")

    def Test_Does_Not_Sum_To_One_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that does Not Sum To One Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = np.array([0.4, 0.4, 0.4]), field_name="w")

    def Test_Must_Sum_To_One_False_Accepts_Unnormalized(self, strategy: _ConcreteStrategy) -> None:
        """Test that must Sum To One False Accepts Unnormalized."""
        # When must_sum_to_one=False, non-unit vectors are accepted
        w = strategy._validate_weights_array(
            weights = np.array([0.4, 0.3, 0.2]),
            field_name="w",
            must_sum_to_one=False,
        )
        assert isinstance(w, np.ndarray)

    def Test_List_Converted_To_Ndarray(self, strategy: _ConcreteStrategy) -> None:
        """Test that list Converted To Ndarray."""
        result = strategy._validate_weights_array(weights = [0.5, 0.3, 0.2], field_name="w")  # type: ignore[arg-type]
        assert isinstance(result, np.ndarray)

    def Test_Bool_Weights_Raise(self, strategy: _ConcreteStrategy) -> None:
        """Test that bool weights Raise."""
        with pytest.raises(Exception_Validation_Input, match="bool"):
            strategy._validate_weights_array(weights = [True, False, False], field_name="w")

    def Test_Non_Convertible_List_Raises(
        self, strategy: _ConcreteStrategy,
    ) -> None:
        """Test that a list of non-numeric strings raises (TypeError/ValueError in np.asarray)."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_weights_array(weights = ["a", "b", "c"], field_name="w")  # type: ignore[arg-type]

    def Test_Wrong_Size_On_Configured_Strategy_Raises(
        self, configured_strategy: _ConcreteStrategy,
    ) -> None:
        """Test that weights with size != n_assets raises when strategy is already configured."""
        with pytest.raises(Exception_Validation_Input):
            configured_strategy._validate_weights_array(
                weights = np.array([0.6, 0.4]),
                field_name="w",
                must_sum_to_one=False,
            )


# =============================================================================
# Tests: _validate_portfolio_value
# =============================================================================


@pytest.mark.unit()
class Class_Test_Validate_Portfolio_Value:
    """Tests for the _validate_portfolio_value helper."""

    def Test_Positive_Value_Accepted(self, strategy: _ConcreteStrategy) -> None:
        """Test that positive Value Accepted."""
        pv = strategy._validate_portfolio_value(portfolio_value = 100_000.0)
        assert pv == pytest.approx(100_000.0)

    def Test_Zero_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that zero Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = 0.0)

    def Test_Negative_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that negative Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = -1.0)

    def Test_Nan_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that nan Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = float("nan"))

    def Test_Inf_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that inf Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = float("inf"))

    def Test_Bool_Input_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that bool Input Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = True)  # type: ignore[arg-type]  # noqa: FBT003

    def Test_String_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that string Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_portfolio_value(portfolio_value = "100000")  # type: ignore[arg-type]


# =============================================================================
# Tests: _validate_asset_names
# =============================================================================


@pytest.mark.unit()
class Class_Test_Validate_Asset_Names:
    """Tests for the _validate_asset_names helper."""

    def Test_Valid_Names_Accepted(self, strategy: _ConcreteStrategy) -> None:
        """Test that valid Names Accepted."""
        strategy._validate_asset_names(names_assets = ["A", "B", "C"], n_assets_expected=3)

    def Test_Wrong_Length_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that wrong Length Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_asset_names(names_assets = ["A", "B"], n_assets_expected=3)

    def Test_Duplicate_Names_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that duplicate Names Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_asset_names(names_assets = ["A", "A", "C"], n_assets_expected=3)

    def Test_Empty_Name_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that empty Name Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_asset_names(names_assets = ["A", "", "C"], n_assets_expected=3)

    def Test_Non_String_Element_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that non String Element Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_asset_names(names_assets = ["A", 2, "C"], n_assets_expected=3)  # type: ignore[list-item]

    def Test_Not_A_List_Raises(self, strategy: _ConcreteStrategy) -> None:
        """Test that not A List Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy._validate_asset_names(names_assets = ("A", "B", "C"), n_assets_expected=3)  # type: ignore[arg-type]


# =============================================================================
# Tests: _check_is_configured
# =============================================================================


@pytest.mark.unit()
class Class_Test_Check_Is_Configured:
    """Tests for the _check_is_configured helper."""

    def Test_Raises_When_Not_Configured(self, strategy: _ConcreteStrategy) -> None:
        """Test that raises When Not Configured."""
        with pytest.raises(Exception_Calculation):
            strategy._check_is_configured()

    def Test_Does_Not_Raise_When_Configured(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that does Not Raise When Configured."""
        configured_strategy._check_is_configured()  # should not raise


# =============================================================================
# Tests: _weight_drifts
# =============================================================================


@pytest.mark.unit()
class Class_Test_Weight_Drifts:
    """Tests for the _weight_drifts helper."""

    def Test_Exact_Target_Gives_Zero_Drift(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that exact Target Gives Zero Drift."""
        drifts = configured_strategy._weight_drifts(current_weights = _WEIGHTS_3)
        np.testing.assert_allclose(drifts, 0.0, atol=1e-12)

    def Test_Over_Weight_Positive_Drift(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that over Weight Positive Drift."""
        current = np.array([0.6, 0.2, 0.2])
        drifts = configured_strategy._weight_drifts(current_weights = current)
        assert drifts[0] > 0  # A over-weight
        assert drifts[1] < 0  # B under-weight

    def Test_Drift_Shape_Matches_Assets(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that drift Shape Matches Assets."""
        current = np.array([0.4, 0.4, 0.2])
        drifts = configured_strategy._weight_drifts(current_weights = current)
        assert drifts.shape == (3,)

    def Test_Raises_When_Not_Configured(self, strategy: _ConcreteStrategy) -> None:
        """Test that raises When Not Configured."""
        with pytest.raises(Exception_Calculation):
            strategy._weight_drifts(current_weights = _WEIGHTS_3)


# =============================================================================
# Tests: _compute_turnover
# =============================================================================


@pytest.mark.unit()
class Class_Test_Compute_Turnover:
    """Tests for the _compute_turnover helper."""

    def Test_Zero_Trades_Gives_Zero_Turnover(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that zero Trades Gives Zero Turnover."""
        trades = np.zeros(3)
        to = configured_strategy._compute_turnover(trade_weights = trades)
        assert to == pytest.approx(0.0)

    def Test_Full_Rebalance_Equals_Half_Sum_Of_Abs_Trades(
        self, configured_strategy: _ConcreteStrategy,
    ) -> None:
        """Test that full Rebalance Equals Half Sum Of Abs Trades."""
        trades = np.array([0.1, -0.05, -0.05])
        expected = float(np.sum(np.abs(trades))) / 2.0
        assert configured_strategy._compute_turnover(trade_weights = trades) == pytest.approx(expected)

    def Test_Returns_Float(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that returns Float."""
        to = configured_strategy._compute_turnover(trade_weights = np.array([0.05, -0.05, 0.0]))
        assert isinstance(to, float)


# =============================================================================
# Tests: get_summary_statistics
# =============================================================================


@pytest.mark.unit()
class Class_Test_Get_Summary_Statistics:
    """Tests for Portfolio_Rebalancing_Base.get_summary_statistics."""

    def Test_Returns_Dataframe(
        self,
        configured_strategy: _ConcreteStrategy,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that returns Dataframe."""
        summary = configured_strategy.get_summary_statistics(rebalancing_result = rebalance_result)
        assert isinstance(summary, pl.DataFrame)

    def Test_Single_Row(
        self,
        configured_strategy: _ConcreteStrategy,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that single Row."""
        summary = configured_strategy.get_summary_statistics(rebalancing_result = rebalance_result)
        assert len(summary) == 1

    def Test_Expected_Columns_Present(
        self,
        configured_strategy: _ConcreteStrategy,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that expected Columns Present."""
        summary = configured_strategy.get_summary_statistics(rebalancing_result = rebalance_result)
        for col in (
            "Max_Abs_Drift",
            "Mean_Abs_Drift",
            "Turnover",
            "Total_Trade_Value",
            "Total_Cost",
        ):
            assert col in summary.columns

    def Test_Max_Drift_Non_Negative(
        self,
        configured_strategy: _ConcreteStrategy,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that max Drift Non Negative."""
        summary = configured_strategy.get_summary_statistics(rebalancing_result = rebalance_result)
        assert summary["Max_Abs_Drift"][0] >= 0.0

    def Test_Turnover_Non_Negative(
        self,
        configured_strategy: _ConcreteStrategy,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that turnover Non Negative."""
        summary = configured_strategy.get_summary_statistics(rebalancing_result = rebalance_result)
        assert summary["Turnover"][0] >= 0.0

    def Test_Missing_Column_Raises(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that missing Column Raises."""
        bad_df = pl.DataFrame({"Asset": ["A"], "Drift": [0.05]})
        with pytest.raises((Exception_Validation_Input, KeyError, Exception)):
            configured_strategy.get_summary_statistics(rebalancing_result = bad_df)

    def Test_Zero_Drift_Result(self, configured_strategy: _ConcreteStrategy) -> None:
        """Test that zero Drift Result."""
        exact = configured_strategy.rebalance(current_weights = _WEIGHTS_3, portfolio_value=1_000_000.0)
        summary = configured_strategy.get_summary_statistics(rebalancing_result = exact)
        assert summary["Max_Abs_Drift"][0] == pytest.approx(0.0, abs=1e-9)
        assert summary["Turnover"][0] == pytest.approx(0.0, abs=1e-9)


# =============================================================================
# Tests: __repr__
# =============================================================================


@pytest.mark.unit()
class Class_Test_Repr:
    """Tests for Portfolio_Rebalancing_Base.__repr__."""

    def Test_Repr_Contains_Class_Name(self, strategy: _ConcreteStrategy) -> None:
        """Test that repr Contains Class Name."""
        r = repr(strategy)
        assert "_ConcreteStrategy" in r or "Portfolio_Rebalancing" in r or "Concrete" in r

    def Test_Repr_Contains_Strategy_Name(self, strategy: _ConcreteStrategy) -> None:
        """Test that repr Contains Strategy Name."""
        s = _ConcreteStrategy(name_strategy="TestStrat")
        assert "TestStrat" in repr(s)
