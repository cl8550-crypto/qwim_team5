"""Unit tests for Portfolio_Rebalancing_Standard strategy.

Covers construction, configure, should_rebalance, rebalance, extra
public methods (get_turnover, get_estimated_cost, reset), and all
properties.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import polars as pl
import pytest

from src.models.portfolio_rebalancing.portfolio_rebalancing_base import (
    Rebalancing_Strategy_Status,
)
from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
    Portfolio_Rebalancing_Standard,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# =============================================================================
# Shared test data
# =============================================================================

_NAMES_2 = ["Equity", "Bond"]
_TARGET_2 = np.array([0.60, 0.40])
_AT_TARGET_2 = np.array([0.60, 0.40])
_DRIFTED_2 = np.array([0.67, 0.33])  # equity +7 % — exceeds 5 % band
_SLIGHT_2 = np.array([0.62, 0.38])  # equity +2 % — within 5 % band

_NAMES_3 = ["A", "B", "C"]
_TARGET_3 = np.array([0.50, 0.30, 0.20])
_DRIFTED_3 = np.array([0.58, 0.25, 0.17])  # A +8 %, B -5 %, C -3 %

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def strategy() -> Portfolio_Rebalancing_Standard:
    """Strategy."""
    return Portfolio_Rebalancing_Standard()


@pytest.fixture()
def configured() -> Portfolio_Rebalancing_Standard:
    """Configured."""
    s = Portfolio_Rebalancing_Standard()
    s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
    return s


@pytest.fixture()
def configured_3() -> Portfolio_Rebalancing_Standard:
    """Configured 3."""
    s = Portfolio_Rebalancing_Standard()
    s.configure(target_weights = _TARGET_3, names_assets = _NAMES_3)
    return s


@pytest.fixture()
def rebalance_result(configured: Portfolio_Rebalancing_Standard) -> pl.DataFrame:
    """Rebalance result."""
    return configured.rebalance(current_weights = _DRIFTED_2, portfolio_value=100_000.0)


# =============================================================================
# Tests: construction — defaults
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Construction:
    """Tests for Portfolio_Rebalancing_Standard constructor."""

    def Test_Default_Name_Contains_Threshold(
        self, strategy: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that default Name Contains Threshold."""
        assert "Threshold" in strategy.name_strategy or "Standard" in strategy.name_strategy

    def Test_Default_Tolerance_Abs(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that default Tolerance Abs."""
        assert strategy.tolerance_abs == pytest.approx(0.05)

    def Test_Default_Frequency_Days_Zero(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that default Frequency Days Zero."""
        assert strategy.rebalancing_frequency_days == 0

    def Test_Default_Cost_Bps(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that default Cost Bps."""
        assert strategy.transaction_cost_bps == pytest.approx(10.0)

    def Test_Initial_Last_Rebalance_Date_None(
        self, strategy: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that initial Last Rebalance Date None."""
        assert strategy.last_rebalance_date is None

    def Test_Initial_N_Rebalances_Zero(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that initial N Rebalances Zero."""
        assert strategy.n_rebalances == 0

    def Test_Custom_Tolerance_Accepted(self) -> None:
        """Test that custom Tolerance Accepted."""
        s = Portfolio_Rebalancing_Standard(tolerance_abs=0.10)
        assert s.tolerance_abs == pytest.approx(0.10)

    def Test_Custom_Frequency_Accepted(self) -> None:
        """Test that custom Frequency Accepted."""
        s = Portfolio_Rebalancing_Standard(rebalancing_frequency_days=91)
        assert s.rebalancing_frequency_days == 91

    def Test_Custom_Cost_Accepted(self) -> None:
        """Test that custom Cost Accepted."""
        s = Portfolio_Rebalancing_Standard(transaction_cost_bps=5.0)
        assert s.transaction_cost_bps == pytest.approx(5.0)

    def Test_Zero_Cost_Accepted(self) -> None:
        """Test that zero Cost Accepted."""
        s = Portfolio_Rebalancing_Standard(transaction_cost_bps=0.0)
        assert s.transaction_cost_bps == pytest.approx(0.0)


# =============================================================================
# Tests: construction — invalid inputs
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Construction_Invalid:
    """Tests for Portfolio_Rebalancing_Standard constructor input validation."""

    def Test_Tolerance_Too_Small_Raises(self) -> None:
        """Test that tolerance Too Small Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs=0.0001)

    def Test_Tolerance_Too_Large_Raises(self) -> None:
        """Test that tolerance Too Large Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs=0.60)

    def Test_Tolerance_Negative_Raises(self) -> None:
        """Test that tolerance Negative Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs=-0.01)

    def Test_Tolerance_Nan_Raises(self) -> None:
        """Test that tolerance Nan Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs=float("nan"))

    def Test_Tolerance_Bool_Raises(self) -> None:
        """Test that tolerance Bool Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs=True)  # type: ignore[arg-type]

    def Test_Tolerance_String_Raises(self) -> None:
        """Test that tolerance String Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(tolerance_abs="0.05")  # type: ignore[arg-type]

    def Test_Frequency_Negative_Raises(self) -> None:
        """Test that frequency Negative Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(rebalancing_frequency_days=-1)

    def Test_Frequency_Float_Raises(self) -> None:
        """Test that frequency Float Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(rebalancing_frequency_days=30.5)  # type: ignore[arg-type]

    def Test_Frequency_Bool_Raises(self) -> None:
        """Test that frequency Bool Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(rebalancing_frequency_days=True)  # type: ignore[arg-type]

    def Test_Cost_Negative_Raises(self) -> None:
        """Test that cost Negative Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=-1.0)

    def Test_Cost_Too_Large_Raises(self) -> None:
        """Test that cost Too Large Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=600.0)

    def Test_Cost_Nan_Raises(self) -> None:
        """Test that cost Nan Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=float("nan"))

    def Test_Cost_Bool_Raises(self) -> None:
        """Test that cost Bool Raises."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=True)  # type: ignore[arg-type]


# =============================================================================
# Tests: configure
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Configure:
    """Tests for Portfolio_Rebalancing_Standard.configure."""

    def Test_Returns_Self(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that returns Self."""
        result = strategy.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        assert result is strategy

    def Test_Status_Configured_After_Configure(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that status Configured After Configure."""
        assert configured.status == Rebalancing_Strategy_Status.CONFIGURED

    def Test_Is_Configured_True(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that is Configured True."""
        assert configured.is_configured is True

    def Test_Target_Weights_Stored(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that target Weights Stored."""
        np.testing.assert_allclose(configured.target_weights, _TARGET_2)

    def Test_Names_Assets_Stored(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that names Assets Stored."""
        assert configured.names_assets == _NAMES_2

    def Test_N_Assets_Set(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that n Assets Set."""
        assert configured.n_assets == 2

    def Test_Wrong_Length_Weights_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that wrong Length Weights Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy.configure(target_weights = np.array([0.5, 0.3]), names_assets = ["A", "B", "C"])

    def Test_Weights_Not_Sum_To_One_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that weights Not Sum To One Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy.configure(target_weights = np.array([0.4, 0.4]), names_assets = ["A", "B"])

    def Test_Duplicate_Names_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that duplicate Names Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy.configure(target_weights = _TARGET_2, names_assets = ["A", "A"])

    def Test_Negative_Weight_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that negative Weight Raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy.configure(target_weights = np.array([-0.1, 1.1]), names_assets = _NAMES_2)

    def Test_Parameters_Populated_After_Configure(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that parameters Populated After Configure."""
        assert len(configured.parameters) > 0

    def Test_Reconfigure_Updates_Target(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that reconfigure Updates Target."""
        new_target = np.array([0.70, 0.30])
        configured.configure(target_weights = new_target, names_assets = _NAMES_2)
        np.testing.assert_allclose(configured.target_weights, new_target)

    def Test_Valid_Weights_With_Mismatched_Names_Length_Raises(
        self, strategy: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that weights summing to 1.0 but mismatched in length vs names raises."""
        with pytest.raises(Exception_Validation_Input):
            strategy.configure(target_weights = np.array([0.60, 0.40]), names_assets = ["A", "B", "C"])


# =============================================================================
# Tests: should_rebalance — threshold trigger
# =============================================================================


@pytest.mark.unit()
class Class_Test_Should_Rebalance_Threshold:
    """Tests for the threshold-based trigger in should_rebalance."""

    def Test_Drifted_Above_Tolerance_Returns_True(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that drifted Above Tolerance Returns True."""
        # equity at 67 % vs target 60 % — drift 7 % > tolerance 5 %
        assert configured.should_rebalance(current_weights = _DRIFTED_2) is True

    def Test_Within_Tolerance_Returns_False(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that within Tolerance Returns False."""
        # equity at 62 % vs target 60 % — drift 2 % < tolerance 5 %
        assert configured.should_rebalance(current_weights = _SLIGHT_2) is False

    def Test_Exactly_At_Target_Returns_False(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that exactly At Target Returns False."""
        assert configured.should_rebalance(current_weights = _AT_TARGET_2) is False

    def Test_Not_Configured_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that not Configured Raises."""
        with pytest.raises(Exception_Calculation):
            strategy.should_rebalance(current_weights = _DRIFTED_2)

    def Test_Tight_Tolerance_Triggers_Easily(self) -> None:
        """Test that tight Tolerance Triggers Easily."""
        s = Portfolio_Rebalancing_Standard(tolerance_abs=0.01)
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        # drift of 2 % exceeds 1 % tolerance
        assert s.should_rebalance(current_weights = _SLIGHT_2) is True

    def Test_Wide_Tolerance_Does_Not_Trigger(self) -> None:
        """Test that wide Tolerance Does Not Trigger."""
        s = Portfolio_Rebalancing_Standard(tolerance_abs=0.10)
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        # drift of 7 % < 10 % tolerance
        assert s.should_rebalance(current_weights = _DRIFTED_2) is False


# =============================================================================
# Tests: should_rebalance — calendar trigger
# =============================================================================


@pytest.mark.unit()
class Class_Test_Should_Rebalance_Calendar:
    """Tests for the calendar (date-based) trigger in should_rebalance."""

    def Test_Calendar_Trigger_Fires_When_Enough_Days_Elapsed(self) -> None:
        """Test that calendar Trigger Fires When Enough Days Elapsed."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.30,  # wide — no threshold trigger
            rebalancing_frequency_days=90,
        )
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        # Simulate last rebalance 91 days ago
        last_date = datetime(2024, 1, 1)  # noqa: DTZ001
        s.m_last_rebalance_date = last_date
        current_date = last_date + timedelta(days=91)
        assert s.should_rebalance(current_weights = _AT_TARGET_2, current_date=current_date) is True

    def Test_Calendar_Trigger_Does_Not_Fire_Too_Early(self) -> None:
        """Test that calendar Trigger Does Not Fire Too Early."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.30,
            rebalancing_frequency_days=90,
        )
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        last_date = datetime(2024, 1, 1)  # noqa: DTZ001
        s.m_last_rebalance_date = last_date
        current_date = last_date + timedelta(days=30)
        assert s.should_rebalance(current_weights = _AT_TARGET_2, current_date=current_date) is False

    def Test_Calendar_Disabled_Never_Triggers_By_Date(self) -> None:
        """Test that calendar Disabled Never Triggers By Date."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.30,
            rebalancing_frequency_days=0,
        )
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        last_date = datetime(2024, 1, 1)  # noqa: DTZ001
        s.m_last_rebalance_date = last_date
        far_future = last_date + timedelta(days=10_000)
        assert s.should_rebalance(current_weights = _AT_TARGET_2, current_date=far_future) is False

    def Test_First_Evaluation_With_Calendar_Triggers(self) -> None:
        """Test that first Evaluation With Calendar Triggers."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.30,
            rebalancing_frequency_days=30,
        )
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        # No prior rebalance — special-case: first eval with calendar should trigger
        assert s.should_rebalance(current_weights = _AT_TARGET_2, current_date=datetime(2024, 6, 1)) is True  # noqa: DTZ001

    def Test_No_Date_Calendar_Disabled_No_Trigger(self) -> None:
        """Test that no Date Calendar Disabled No Trigger."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.30,
            rebalancing_frequency_days=30,
        )
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        # current_date=None — calendar trigger cannot fire
        assert s.should_rebalance(current_weights = _AT_TARGET_2, current_date=None) is False


# =============================================================================
# Tests: rebalance — return structure
# =============================================================================


@pytest.mark.unit()
class Class_Test_Rebalance_Structure:
    """Tests for Portfolio_Rebalancing_Standard.rebalance return structure."""

    def Test_Returns_Polars_Dataframe(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that returns Polars Dataframe."""
        assert isinstance(rebalance_result, pl.DataFrame)

    def Test_Row_Count_Equals_N_Assets(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that row Count Equals N Assets."""
        assert len(rebalance_result) == 2

    def Test_Expected_Columns_Present(self, rebalance_result: pl.DataFrame) -> None:
        """Test that expected Columns Present."""
        for col in (
            "Asset",
            "Current_Weight",
            "Target_Weight",
            "Drift",
            "Trade_Weight",
            "Trade_Value",
            "Cost",
        ):
            assert col in rebalance_result.columns

    def Test_Asset_Names_Match(self, rebalance_result: pl.DataFrame) -> None:
        """Test that asset Names Match."""
        assert list(rebalance_result["Asset"]) == _NAMES_2

    def Test_Not_Configured_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that not Configured Raises."""
        with pytest.raises(Exception_Calculation):
            strategy.rebalance(current_weights = _DRIFTED_2)

    def Test_Invalid_Portfolio_Value_Raises(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that invalid Portfolio Value Raises."""
        with pytest.raises(Exception_Validation_Input):
            configured.rebalance(current_weights = _DRIFTED_2, portfolio_value=0.0)


# =============================================================================
# Tests: rebalance — arithmetic
# =============================================================================


@pytest.mark.unit()
class Class_Test_Rebalance_Arithmetic:
    """Tests for trade weight / value / cost arithmetic in rebalance."""

    def Test_Drift_Equals_Current_Minus_Target(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that drift Equals Current Minus Target."""
        for row in rebalance_result.iter_rows(named=True):
            expected_drift = row["Current_Weight"] - row["Target_Weight"]
            assert row["Drift"] == pytest.approx(expected_drift, abs=1e-9)

    def Test_Trade_Weight_Equals_Target_Minus_Current(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that trade Weight Equals Target Minus Current."""
        for row in rebalance_result.iter_rows(named=True):
            expected_trade = row["Target_Weight"] - row["Current_Weight"]
            assert row["Trade_Weight"] == pytest.approx(expected_trade, abs=1e-9)

    def Test_Trade_Value_Equals_Trade_Weight_Times_Portfolio_Value(
        self,
        configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that trade Value Equals Trade Weight Times Portfolio Value."""
        pv = 500_000.0
        result = configured.rebalance(current_weights = _DRIFTED_2, portfolio_value=pv)
        for row in result.iter_rows(named=True):
            expected_tv = row["Trade_Weight"] * pv
            assert row["Trade_Value"] == pytest.approx(expected_tv, abs=1e-6)

    def Test_Cost_Equals_Abs_Trade_Value_Times_Cost_Rate(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that cost Equals Abs Trade Value Times Cost Rate."""
        pv = 100_000.0
        result = configured.rebalance(current_weights = _DRIFTED_2, portfolio_value=pv)
        cost_rate = configured.transaction_cost_bps / 10_000.0
        for row in result.iter_rows(named=True):
            expected_cost = abs(row["Trade_Value"]) * cost_rate
            assert row["Cost"] == pytest.approx(expected_cost, abs=1e-6)

    def Test_At_Target_Gives_Zero_Trades(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that at Target Gives Zero Trades."""
        result = configured.rebalance(current_weights = _AT_TARGET_2, portfolio_value=1_000_000.0)
        np.testing.assert_allclose(result["Trade_Weight"].to_numpy(), 0.0, atol=1e-9)

    def Test_At_Target_Gives_Zero_Costs(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that at Target Gives Zero Costs."""
        result = configured.rebalance(current_weights = _AT_TARGET_2, portfolio_value=1_000_000.0)
        np.testing.assert_allclose(result["Cost"].to_numpy(), 0.0, atol=1e-9)

    def Test_Zero_Cost_Bps_Gives_Zero_Costs(self) -> None:
        """Test that zero Cost Bps Gives Zero Costs."""
        s = Portfolio_Rebalancing_Standard(transaction_cost_bps=0.0)
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        result = s.rebalance(current_weights = _DRIFTED_2, portfolio_value=1_000_000.0)
        np.testing.assert_allclose(result["Cost"].to_numpy(), 0.0, atol=1e-9)


# =============================================================================
# Tests: rebalance — state updates
# =============================================================================


@pytest.mark.unit()
class Class_Test_Rebalance_State_Updates:
    """Tests for state mutations caused by rebalance calls."""

    def Test_N_Rebalances_Incremented(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that n Rebalances Incremented."""
        assert configured.n_rebalances == 0
        configured.rebalance(current_weights = _DRIFTED_2)
        assert configured.n_rebalances == 1
        configured.rebalance(current_weights = _DRIFTED_2)
        assert configured.n_rebalances == 2

    def Test_Last_Rebalance_Date_Set_When_Date_Provided(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that last Rebalance Date Set When Date Provided."""
        d = datetime(2024, 6, 15)  # noqa: DTZ001
        configured.rebalance(current_weights = _DRIFTED_2, current_date=d)
        assert configured.last_rebalance_date == d

    def Test_Last_Rebalance_Date_None_When_No_Date(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that last Rebalance Date None When No Date."""
        configured.rebalance(current_weights = _DRIFTED_2, current_date=None)
        # Without a date, last_rebalance_date stays None
        assert configured.last_rebalance_date is None

    def Test_Last_Rebalance_Date_Updated_On_Second_Call(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that last Rebalance Date Updated On Second Call."""
        d1 = datetime(2024, 1, 1)  # noqa: DTZ001
        d2 = datetime(2024, 6, 1)  # noqa: DTZ001
        configured.rebalance(current_weights = _DRIFTED_2, current_date=d1)
        configured.rebalance(current_weights = _DRIFTED_2, current_date=d2)
        assert configured.last_rebalance_date == d2


# =============================================================================
# Tests: get_turnover
# =============================================================================


@pytest.mark.unit()
class Class_Test_Get_Turnover:
    """Tests for Portfolio_Rebalancing_Standard.get_turnover."""

    def Test_Returns_Float(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that returns Float."""
        to = configured.get_turnover(current_weights = _DRIFTED_2)
        assert isinstance(to, float)

    def Test_At_Target_Zero_Turnover(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that at Target Zero Turnover."""
        assert configured.get_turnover(current_weights = _AT_TARGET_2) == pytest.approx(0.0, abs=1e-9)

    def Test_Turnover_Non_Negative(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that turnover Non Negative."""
        assert configured.get_turnover(current_weights = _DRIFTED_2) >= 0.0

    def Test_Not_Configured_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that not Configured Raises."""
        with pytest.raises(Exception_Calculation):
            strategy.get_turnover(current_weights = _DRIFTED_2)

    def Test_Turnover_Matches_Half_Abs_Sum(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that turnover Matches Half Abs Sum."""
        trades = _TARGET_2 - _DRIFTED_2
        expected = float(np.sum(np.abs(trades))) / 2.0
        assert configured.get_turnover(current_weights = _DRIFTED_2) == pytest.approx(expected, abs=1e-9)


# =============================================================================
# Tests: get_estimated_cost
# =============================================================================


@pytest.mark.unit()
class Class_Test_Get_Estimated_Cost:
    """Tests for Portfolio_Rebalancing_Standard.get_estimated_cost."""

    def Test_Returns_Float(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that returns Float."""
        cost = configured.get_estimated_cost(current_weights = _DRIFTED_2, portfolio_value=100_000.0)
        assert isinstance(cost, float)

    def Test_At_Target_Zero_Cost(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that at Target Zero Cost."""
        cost = configured.get_estimated_cost(current_weights = _AT_TARGET_2, portfolio_value=1_000_000.0)
        assert cost == pytest.approx(0.0, abs=1e-6)

    def Test_Cost_Scales_With_Portfolio_Value(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that cost Scales With Portfolio Value."""
        pv1 = 100_000.0
        pv2 = 200_000.0
        c1 = configured.get_estimated_cost(current_weights = _DRIFTED_2, portfolio_value=pv1)
        c2 = configured.get_estimated_cost(current_weights = _DRIFTED_2, portfolio_value=pv2)
        assert c2 == pytest.approx(c1 * 2.0, rel=1e-6)

    def Test_Zero_Cost_Bps_Gives_Zero_Cost(self) -> None:
        """Test that zero Cost Bps Gives Zero Cost."""
        s = Portfolio_Rebalancing_Standard(transaction_cost_bps=0.0)
        s.configure(target_weights = _TARGET_2, names_assets = _NAMES_2)
        assert s.get_estimated_cost(current_weights = _DRIFTED_2, portfolio_value=1_000_000.0) == pytest.approx(0.0)

    def Test_Not_Configured_Raises(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that not Configured Raises."""
        with pytest.raises(Exception_Calculation):
            strategy.get_estimated_cost(current_weights = _DRIFTED_2, portfolio_value=100_000.0)


# =============================================================================
# Tests: reset
# =============================================================================


@pytest.mark.unit()
class Class_Test_Reset:
    """Tests for Portfolio_Rebalancing_Standard.reset."""

    def Test_Reset_Clears_Last_Rebalance_Date(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that reset Clears Last Rebalance Date."""
        configured.rebalance(current_weights = _DRIFTED_2, current_date=datetime(2024, 6, 1))  # noqa: DTZ001
        configured.reset()
        assert configured.last_rebalance_date is None

    def Test_Reset_Clears_N_Rebalances(self, configured: Portfolio_Rebalancing_Standard) -> None:
        """Test that reset Clears N Rebalances."""
        configured.rebalance(current_weights = _DRIFTED_2)
        configured.rebalance(current_weights = _DRIFTED_2)
        configured.reset()
        assert configured.n_rebalances == 0

    def Test_Configured_Status_Preserved_After_Reset(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that configured Status Preserved After Reset."""
        configured.reset()
        assert configured.is_configured is True

    def Test_Target_Weights_Preserved_After_Reset(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that target Weights Preserved After Reset."""
        configured.reset()
        np.testing.assert_array_equal(configured.target_weights, _TARGET_2)


# =============================================================================
# Tests: properties
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Properties:
    """Tests for Portfolio_Rebalancing_Standard properties."""

    def Test_Tolerance_Abs_Property(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that tolerance Abs Property."""
        assert strategy.tolerance_abs == pytest.approx(0.05)

    def Test_Rebalancing_Frequency_Days_Property(
        self, strategy: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that rebalancing Frequency Days Property."""
        assert strategy.rebalancing_frequency_days == 0

    def Test_Transaction_Cost_Bps_Property(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that transaction Cost Bps Property."""
        assert strategy.transaction_cost_bps == pytest.approx(10.0)

    def Test_N_Rebalances_Property(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that n Rebalances Property."""
        assert strategy.n_rebalances == 0

    def Test_Last_Rebalance_Date_Property(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that last Rebalance Date Property."""
        assert strategy.last_rebalance_date is None


# =============================================================================
# Tests: get_summary_statistics (via base)
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Get_Summary_Statistics:
    """Tests for get_summary_statistics on a rebalance result."""

    def Test_Summary_Is_Dataframe(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that summary Is Dataframe."""
        summary = configured.get_summary_statistics(rebalancing_result = rebalance_result)
        assert isinstance(summary, pl.DataFrame)

    def Test_Summary_Has_One_Row(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that summary Has One Row."""
        assert len(configured.get_summary_statistics(rebalancing_result = rebalance_result)) == 1

    def Test_Total_Cost_Non_Negative(
        self,
        configured: Portfolio_Rebalancing_Standard,
        rebalance_result: pl.DataFrame,
    ) -> None:
        """Test that total Cost Non Negative."""
        summary = configured.get_summary_statistics(rebalancing_result = rebalance_result)
        assert summary["Total_Cost"][0] >= 0.0

    def Test_At_Target_Zero_Turnover_Summary(
        self, configured: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Test that at Target Zero Turnover Summary."""
        result = configured.rebalance(current_weights = _AT_TARGET_2, portfolio_value=1_000_000.0)
        summary = configured.get_summary_statistics(rebalancing_result = result)
        assert summary["Turnover"][0] == pytest.approx(0.0, abs=1e-9)
        assert summary["Total_Cost"][0] == pytest.approx(0.0, abs=1e-6)


# =============================================================================
# Tests: __repr__
# =============================================================================


@pytest.mark.unit()
class Class_Test_Standard_Repr:
    """Tests for Portfolio_Rebalancing_Standard.__repr__."""

    def Test_Repr_Is_String(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that repr Is String."""
        assert isinstance(repr(strategy), str)

    def Test_Repr_Contains_Class_Name(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that repr Contains Class Name."""
        r = repr(strategy)
        assert "Standard" in r or "Portfolio_Rebalancing" in r

    def Test_Repr_Contains_Tolerance(self, strategy: Portfolio_Rebalancing_Standard) -> None:
        """Test that repr Contains Tolerance."""
        r = repr(strategy)
        assert "0.05" in r or "tolerance" in r.lower()
