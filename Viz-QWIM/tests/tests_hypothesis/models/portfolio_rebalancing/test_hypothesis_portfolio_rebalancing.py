"""Hypothesis-based tests for portfolio rebalancing models.

Tests cover:
- Portfolio_Rebalancing_Base shared helpers (_validate_weights_array,
  _validate_portfolio_value, _validate_asset_names, _weight_drifts,
  _compute_turnover, get_summary_statistics)
- Portfolio_Rebalancing_Standard construction, configure, should_rebalance,
  rebalance, get_turnover, get_estimated_cost, reset
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pytest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.models.portfolio_rebalancing.portfolio_rebalancing_base import (
    Portfolio_Rebalancing_Base,
    Rebalancing_Strategy_Status,
)
from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
    Portfolio_Rebalancing_Standard,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_weights(n: int, rng: np.random.Generator | None = None) -> np.ndarray:
    """Return a valid normalised weight vector of length *n*."""
    if rng is None:
        rng = np.random.default_rng(42)
    raw = rng.uniform(0.01, 1.0, n)
    return raw / raw.sum()


def _make_strategy(
    n_assets: int,
    tolerance_abs: float = 0.05,
) -> Portfolio_Rebalancing_Standard:
    """Return a configured strategy with *n_assets* equal-weight assets."""
    target = np.ones(n_assets) / n_assets
    names = [f"Asset{i+1}" for i in range(n_assets)]
    s = Portfolio_Rebalancing_Standard(tolerance_abs=tolerance_abs)
    s.configure(target_weights = target, names_assets = names)
    return s


# ---------------------------------------------------------------------------
# Tests for _validate_weights_array
# ---------------------------------------------------------------------------


class Class_Test_Validate_Weights_Array:
    """Hypothesis-driven tests for the base-class weight validator."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=200)
    def Test_Valid_Normalised_Weights_Pass(self, n: int) -> None:
        """A normalised weight vector always passes validation."""
        w = _make_weights(n)
        s = Portfolio_Rebalancing_Standard()
        result = s._validate_weights_array(weights = w, must_sum_to_one=True)
        assert result.dtype == np.float64
        assert result.shape == (n,)

    @pytest.mark.unit()
    def Test_Non_Array_Raises(self) -> None:
        """Passing a string raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input):
            s._validate_weights_array(weights = "bad", must_sum_to_one=False)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Negative_Weight_Raises(self) -> None:
        """Negative weight raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="non-negative"):
            s._validate_weights_array(weights = np.array([-0.1, 1.1]), must_sum_to_one=False)

    @pytest.mark.unit()
    def Test_Nan_Weight_Raises(self) -> None:
        """NaN in weights raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="NaN or Inf"):
            s._validate_weights_array(weights = np.array([float("nan"), 0.5]), must_sum_to_one=False)

    @pytest.mark.unit()
    def Test_Not_Summing_To_One_Raises(self) -> None:
        """Weights not summing to 1.0 raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="sum to 1.0"):
            s._validate_weights_array(weights = np.array([0.3, 0.3]), must_sum_to_one=True)

    @pytest.mark.unit()
    def Test_Empty_Array_Raises(self) -> None:
        """Empty array raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="non-empty"):
            s._validate_weights_array(weights = np.array([]), must_sum_to_one=False)

    @pytest.mark.unit()
    def Test_Bool_Weights_Raise(self) -> None:
        """Boolean weights raise Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="bool"):
            s._validate_weights_array(weights = [True, False, False], must_sum_to_one=False)

    @pytest.mark.unit()
    def Test_2d_Array_Raises(self) -> None:
        """2-D array raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="1-D"):
            s._validate_weights_array(weights = np.array([[0.5, 0.5]]), must_sum_to_one=False)

    @pytest.mark.unit()
    def Test_Length_Mismatch_After_Configure_Raises(self) -> None:
        """Weight length != n_assets raises after configure."""
        s = _make_strategy(3)
        with pytest.raises(Exception_Validation_Input, match="does not match"):
            s._validate_weights_array(weights = np.array([0.5, 0.5]), must_sum_to_one=True)


# ---------------------------------------------------------------------------
# Tests for _validate_portfolio_value
# ---------------------------------------------------------------------------


class Class_Test_Validate_Portfolio_Value:
    """Tests for the portfolio-value validator."""

    @pytest.mark.unit()
    @given(pv=st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def Test_Positive_Float_Passes(self, pv: float) -> None:
        """Any positive finite float should pass."""
        s = Portfolio_Rebalancing_Standard()
        result = s._validate_portfolio_value(portfolio_value = pv)
        assert result == pytest.approx(pv, rel=1e-9)

    @pytest.mark.unit()
    def Test_Zero_Raises(self) -> None:
        """portfolio_value=0 raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="positive finite"):
            s._validate_portfolio_value(portfolio_value = 0.0)

    @pytest.mark.unit()
    def Test_Negative_Raises(self) -> None:
        """Negative portfolio_value raises."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="positive finite"):
            s._validate_portfolio_value(portfolio_value = -1.0)

    @pytest.mark.unit()
    def Test_Inf_Raises(self) -> None:
        """Infinite portfolio_value raises."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="positive finite"):
            s._validate_portfolio_value(portfolio_value = float("inf"))

    @pytest.mark.unit()
    def Test_Bool_Raises(self) -> None:
        """bool input raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input):
            s._validate_portfolio_value(portfolio_value = True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_String_Raises(self) -> None:
        """String input raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input):
            s._validate_portfolio_value(portfolio_value = "1000")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests for _validate_asset_names
# ---------------------------------------------------------------------------


class Class_Test_Validate_Asset_Names:
    """Tests for the asset names validator."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=200)
    def Test_Valid_Names_Pass(self, n: int) -> None:
        """A list of unique non-empty names always passes."""
        names = [f"Asset_{i}" for i in range(n)]
        s = Portfolio_Rebalancing_Standard()
        result = s._validate_asset_names(names_assets = names)
        assert len(result) == n

    @pytest.mark.unit()
    def Test_Empty_List_Raises(self) -> None:
        """Empty list raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="non-empty"):
            s._validate_asset_names(names_assets = [])

    @pytest.mark.unit()
    def Test_Non_List_Raises(self) -> None:
        """Non-list raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="non-empty"):
            s._validate_asset_names(names_assets = ("A", "B"))  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Empty_String_Name_Raises(self) -> None:
        """Empty string within list raises Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="non-empty string"):
            s._validate_asset_names(names_assets = ["A", "", "C"])

    @pytest.mark.unit()
    def Test_Duplicate_Names_Raise(self) -> None:
        """Duplicate names raise Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="unique"):
            s._validate_asset_names(names_assets = ["A", "B", "A"])

    @pytest.mark.unit()
    def Test_Expected_Count_Mismatch_Raises(self) -> None:
        """Length != n_assets_expected raises."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="does not match"):
            s._validate_asset_names(names_assets = ["A", "B", "C"], n_assets_expected=2)


# ---------------------------------------------------------------------------
# Tests for _compute_turnover
# ---------------------------------------------------------------------------


class Class_Test_Compute_Turnover:
    """Tests for the turnover helper."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=200)
    def Test_Turnover_Range(self, n: int) -> None:
        """One-way turnover must be in [0, 1]."""
        rng = np.random.default_rng(0)
        trade_w = rng.uniform(-0.1, 0.1, n)
        s = Portfolio_Rebalancing_Standard()
        to = s._compute_turnover(trade_weights = trade_w)
        assert 0.0 <= to

    @pytest.mark.unit()
    def Test_Zero_Trades_Zero_Turnover(self) -> None:
        """Zero trade weights give zero turnover."""
        s = Portfolio_Rebalancing_Standard()
        assert s._compute_turnover(trade_weights = np.zeros(4)) == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Turnover_Formula(self) -> None:
        """Turnover = sum(|w|) / 2."""
        trade = np.array([0.10, -0.10])
        s = Portfolio_Rebalancing_Standard()
        assert s._compute_turnover(trade_weights = trade) == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# Tests for Portfolio_Rebalancing_Standard construction
# ---------------------------------------------------------------------------


class Class_Test_Standard_Construction:
    """Tests for the Standard strategy constructor."""

    @pytest.mark.unit()
    def Test_Default_Construction(self) -> None:
        """Default constructor succeeds."""
        s = Portfolio_Rebalancing_Standard()
        assert s.m_tolerance_abs == pytest.approx(0.05)
        assert s.m_frequency_days == 0
        assert s.m_cost_bps == pytest.approx(10.0)
        assert s.m_status.value == "Not Configured"

    @pytest.mark.unit()
    @given(
        tol=st.floats(min_value=0.001, max_value=0.50, allow_nan=False, allow_infinity=False),
        freq=st.integers(min_value=0, max_value=365),
        bps=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Valid_Parameters_Pass(self, tol: float, freq: int, bps: float) -> None:
        """Any valid parameter combination constructs successfully."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=tol,
            rebalancing_frequency_days=freq,
            transaction_cost_bps=bps,
        )
        assert s.m_tolerance_abs == pytest.approx(tol)
        assert s.m_frequency_days == freq
        assert s.m_cost_bps == pytest.approx(bps)

    @pytest.mark.unit()
    def Test_Tolerance_Too_Small_Raises(self) -> None:
        """tolerance_abs < 0.001 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="tolerance_abs"):
            Portfolio_Rebalancing_Standard(tolerance_abs=0.0005)

    @pytest.mark.unit()
    def Test_Tolerance_Too_Large_Raises(self) -> None:
        """tolerance_abs > 0.50 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="tolerance_abs"):
            Portfolio_Rebalancing_Standard(tolerance_abs=0.51)

    @pytest.mark.unit()
    def Test_Tolerance_Bool_Raises(self) -> None:
        """bool tolerance_abs raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="tolerance_abs"):
            Portfolio_Rebalancing_Standard(tolerance_abs=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Tolerance_Nan_Raises(self) -> None:
        """NaN tolerance_abs raises."""
        with pytest.raises(Exception_Validation_Input, match="tolerance_abs"):
            Portfolio_Rebalancing_Standard(tolerance_abs=float("nan"))

    @pytest.mark.unit()
    def Test_Negative_Frequency_Raises(self) -> None:
        """Negative frequency raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="rebalancing_frequency_days"):
            Portfolio_Rebalancing_Standard(rebalancing_frequency_days=-1)

    @pytest.mark.unit()
    def Test_Float_Frequency_Raises(self) -> None:
        """Float frequency raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="rebalancing_frequency_days"):
            Portfolio_Rebalancing_Standard(rebalancing_frequency_days=30.5)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Negative_Cost_Raises(self) -> None:
        """Negative cost_bps raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="transaction_cost_bps"):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=-1.0)

    @pytest.mark.unit()
    def Test_Cost_Above_Max_Raises(self) -> None:
        """cost_bps > 500 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input, match="transaction_cost_bps"):
            Portfolio_Rebalancing_Standard(transaction_cost_bps=501.0)

    @pytest.mark.unit()
    def Test_Empty_Name_Strategy_Raises(self) -> None:
        """Empty name_strategy raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Portfolio_Rebalancing_Standard(name_strategy="  ")


# ---------------------------------------------------------------------------
# Tests for configure
# ---------------------------------------------------------------------------


class Class_Test_Standard_Configure:
    """Tests for Portfolio_Rebalancing_Standard.configure."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Configure_Sets_Status(self, n: int) -> None:
        """After configure, status is CONFIGURED."""
        s = _make_strategy(n)
        assert s.m_status.value == "Configured"
        assert s.n_assets == n

    @pytest.mark.unit()
    def Test_Configure_Returns_Self(self) -> None:
        """configure() returns self (fluent API)."""
        s = Portfolio_Rebalancing_Standard()
        result = s.configure(target_weights = np.array([0.6, 0.4]), names_assets = ["A", "B"])
        assert result is s

    @pytest.mark.unit()
    def Test_Configure_Length_Mismatch_Raises(self) -> None:
        """Different-length weights and names raise Exception_Validation_Input."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Validation_Input, match="length"):
            s.configure(target_weights = np.array([0.5, 0.3, 0.2]), names_assets = ["A", "B"])

    @pytest.mark.unit()
    def Test_Target_Weights_Are_Copied(self) -> None:
        """Mutating original array does not affect stored weights."""
        orig = np.array([0.6, 0.4])
        s = Portfolio_Rebalancing_Standard()
        s.configure(target_weights = orig, names_assets = ["A", "B"])
        orig[0] = 0.99
        assert s.m_target_weights[0] == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Tests for should_rebalance
# ---------------------------------------------------------------------------


class Class_Test_Standard_Should_Rebalance:
    """Tests for Portfolio_Rebalancing_Standard.should_rebalance."""

    @pytest.mark.unit()
    def Test_Not_Configured_Raises(self) -> None:
        """should_rebalance on unconfigured strategy raises Exception_Calculation."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Calculation):
            s.should_rebalance(current_weights = np.array([0.5, 0.5]))

    @pytest.mark.unit()
    def Test_At_Target_No_Rebalance(self) -> None:
        """Weights exactly at target → no rebalance."""
        s = _make_strategy(2, tolerance_abs=0.05)
        assert s.should_rebalance(current_weights = np.ones(2) / 2) is False

    @pytest.mark.unit()
    def Test_Drift_Within_Band_No_Rebalance(self) -> None:
        """Drift below tolerance → no rebalance."""
        s = _make_strategy(2, tolerance_abs=0.05)
        close = np.array([0.52, 0.48])  # only 2% from 0.5/0.5
        assert s.should_rebalance(current_weights = close) is False

    @pytest.mark.unit()
    def Test_Drift_Exceeds_Band_Rebalance(self) -> None:
        """Drift above tolerance → should rebalance."""
        s = _make_strategy(2, tolerance_abs=0.05)
        drifted = np.array([0.58, 0.42])  # 8% drift
        assert s.should_rebalance(current_weights = drifted) is True

    @pytest.mark.unit()
    def Test_Calendar_Trigger_First_Eval(self) -> None:
        """First evaluation with calendar enabled → True (no prior date)."""
        s = _make_strategy(2, tolerance_abs=0.05)
        s.m_frequency_days = 91
        at_target = np.array([0.5, 0.5])
        assert s.should_rebalance(current_weights = at_target, current_date=datetime(2024, 1, 1)) is True

    @pytest.mark.unit()
    def Test_Calendar_Trigger_After_Frequency(self) -> None:
        """Calendar trigger fires after enough days have elapsed."""
        s = _make_strategy(2, tolerance_abs=0.05)
        s.m_frequency_days = 30
        s.m_last_rebalance_date = datetime(2024, 1, 1)
        future = datetime(2024, 2, 15)  # 45 days later
        at_target = np.array([0.5, 0.5])
        assert s.should_rebalance(current_weights = at_target, current_date=future) is True

    @pytest.mark.unit()
    def Test_Calendar_Not_Triggered_Too_Soon(self) -> None:
        """Calendar does not trigger before frequency days have elapsed."""
        s = _make_strategy(2, tolerance_abs=0.05)
        s.m_frequency_days = 90
        s.m_last_rebalance_date = datetime(2024, 1, 1)
        soon = datetime(2024, 1, 15)  # only 14 days later
        at_target = np.array([0.5, 0.5])
        assert s.should_rebalance(current_weights = at_target, current_date=soon) is False

    @pytest.mark.unit()
    def Test_Calendar_Disabled_No_Date_Trigger(self) -> None:
        """Calendar disabled (m_frequency_days=0) → date arg ignored."""
        s = _make_strategy(2, tolerance_abs=0.05)
        at_target = np.array([0.5, 0.5])
        # 366 days, but frequency=0
        assert s.should_rebalance(current_weights = at_target, current_date=datetime(2025, 1, 1)) is False

    @pytest.mark.unit()
    @given(n=st.integers(min_value=2, max_value=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_At_Target_Never_Rebalances(self, n: int) -> None:
        """With weights exactly at target and calendar off, no rebalance."""
        s = _make_strategy(n, tolerance_abs=0.05)
        target = s.m_target_weights.copy()
        assert s.should_rebalance(current_weights = target) is False


# ---------------------------------------------------------------------------
# Tests for rebalance
# ---------------------------------------------------------------------------


class Class_Test_Standard_Rebalance:
    """Tests for Portfolio_Rebalancing_Standard.rebalance."""

    @pytest.mark.unit()
    def Test_Not_Configured_Raises(self) -> None:
        """rebalance on unconfigured strategy raises Exception_Calculation."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Calculation):
            s.rebalance(current_weights = np.array([0.5, 0.5]))

    @pytest.mark.unit()
    @given(
        n=st.integers(min_value=1, max_value=10),
        pv=st.floats(min_value=1e3, max_value=1e9, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Rebalance_Returns_Correct_Columns(self, n: int, pv: float) -> None:
        """rebalance result has expected 7 columns."""
        s = _make_strategy(n)
        rng = np.random.default_rng(1)
        current = _make_weights(n, rng)
        result = s.rebalance(current_weights = current, portfolio_value=pv)
        expected_cols = {"Asset", "Current_Weight", "Target_Weight", "Drift", "Trade_Weight", "Trade_Value", "Cost"}
        assert set(result.columns) == expected_cols

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Rebalance_Row_Count_Matches_Assets(self, n: int) -> None:
        """rebalance result has exactly n_assets rows."""
        s = _make_strategy(n)
        current = _make_weights(n)
        result = s.rebalance(current_weights = current)
        assert len(result) == n

    @pytest.mark.unit()
    def Test_Rebalance_Drift_Formula(self) -> None:
        """Drift = current - target."""
        s = Portfolio_Rebalancing_Standard()
        s.configure(target_weights = np.array([0.60, 0.40]), names_assets = ["A", "B"])
        current = np.array([0.67, 0.33])
        result = s.rebalance(current_weights = current)
        drifts = result["Drift"].to_list()
        assert drifts[0] == pytest.approx(0.07, abs=1e-9)
        assert drifts[1] == pytest.approx(-0.07, abs=1e-9)

    @pytest.mark.unit()
    def Test_Rebalance_Increments_Counter(self) -> None:
        """Each call to rebalance increments m_n_rebalances."""
        s = _make_strategy(3)
        w = _make_weights(3)
        s.rebalance(current_weights = w)
        s.rebalance(current_weights = w)
        assert s.m_n_rebalances == 2

    @pytest.mark.unit()
    def Test_Rebalance_Updates_Last_Date(self) -> None:
        """rebalance stores current_date in m_last_rebalance_date."""
        s = _make_strategy(2)
        date = datetime(2024, 6, 1)
        s.rebalance(current_weights = np.array([0.5, 0.5]), current_date=date)
        assert s.m_last_rebalance_date == date

    @pytest.mark.unit()
    def Test_Rebalance_Costs_Non_Negative(self) -> None:
        """All Cost values must be >= 0."""
        s = _make_strategy(5)
        current = _make_weights(5)
        result = s.rebalance(current_weights = current, portfolio_value=500_000.0)
        assert all(c >= 0.0 for c in result["Cost"].to_list())

    @pytest.mark.unit()
    def Test_Rebalance_Trade_Value_Sign(self) -> None:
        """Trade_Value is positive for under-weight assets."""
        s = Portfolio_Rebalancing_Standard()
        s.configure(target_weights = np.array([0.6, 0.4]), names_assets = ["A", "B"])
        # A is under-weight → trade is to buy A
        current = np.array([0.50, 0.50])
        result = s.rebalance(current_weights = current, portfolio_value=1_000_000.0)
        # A needs +10% buy
        assert result.filter(result["Asset"] == "A")["Trade_Value"][0] > 0


# ---------------------------------------------------------------------------
# Tests for get_turnover / get_estimated_cost / reset
# ---------------------------------------------------------------------------


class Class_Test_Standard_Extra_Methods:
    """Tests for helper methods of Portfolio_Rebalancing_Standard."""

    @pytest.mark.unit()
    def Test_Turnover_Zero_At_Target(self) -> None:
        """Turnover is 0 when already at target."""
        s = _make_strategy(3)
        assert s.get_turnover(current_weights = s.m_target_weights) == pytest.approx(0.0)

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Turnover_Non_Negative(self, n: int) -> None:
        """Turnover is always >= 0."""
        s = _make_strategy(n)
        current = _make_weights(n)
        assert s.get_turnover(current_weights = current) >= 0.0

    @pytest.mark.unit()
    def Test_Estimated_Cost_At_Target_Is_Zero(self) -> None:
        """Cost is 0 when already at target."""
        s = _make_strategy(3)
        cost = s.get_estimated_cost(current_weights = s.m_target_weights, portfolio_value=1_000_000.0)
        assert cost == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_Reset_Clears_State(self) -> None:
        """reset() sets m_last_rebalance_date=None and m_n_rebalances=0."""
        s = _make_strategy(2)
        s.rebalance(current_weights = np.array([0.5, 0.5]), current_date=datetime(2024, 1, 1))
        assert s.m_n_rebalances == 1
        s.reset()
        assert s.m_n_rebalances == 0
        assert s.m_last_rebalance_date is None

    @pytest.mark.unit()
    def Test_Turnover_Not_Configured_Raises(self) -> None:
        """get_turnover on unconfigured raises Exception_Calculation."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Calculation):
            s.get_turnover(current_weights = np.array([0.5, 0.5]))

    @pytest.mark.unit()
    def Test_Estimated_Cost_Not_Configured_Raises(self) -> None:
        """get_estimated_cost on unconfigured raises Exception_Calculation."""
        s = Portfolio_Rebalancing_Standard()
        with pytest.raises(Exception_Calculation):
            s.get_estimated_cost(current_weights = np.array([0.5, 0.5]))


# ---------------------------------------------------------------------------
# Tests for get_summary_statistics
# ---------------------------------------------------------------------------


class Class_Test_Get_Summary_Statistics:
    """Tests for Portfolio_Rebalancing_Base.get_summary_statistics."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Summary_Has_Expected_Columns(self, n: int) -> None:
        """Summary DataFrame has the 5 expected columns."""
        s = _make_strategy(n)
        current = _make_weights(n)
        result_df = s.rebalance(current_weights = current, portfolio_value=1_000_000.0)
        summary = s.get_summary_statistics(rebalancing_result = result_df)
        expected_cols = {"Max_Abs_Drift", "Mean_Abs_Drift", "Turnover", "Total_Trade_Value", "Total_Cost"}
        assert set(summary.columns) == expected_cols

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def Test_Summary_Single_Row(self, n: int) -> None:
        """Summary DataFrame always has exactly 1 row."""
        s = _make_strategy(n)
        current = _make_weights(n)
        result_df = s.rebalance(current_weights = current, portfolio_value=1_000_000.0)
        summary = s.get_summary_statistics(rebalancing_result = result_df)
        assert len(summary) == 1

    @pytest.mark.unit()
    def Test_Summary_Missing_Column_Raises(self) -> None:
        """Missing column in rebalancing_result raises Exception_Validation_Input."""
        import polars as pl

        s = _make_strategy(2)
        bad_df = pl.DataFrame({"Asset": ["A", "B"], "Drift": [0.1, -0.1]})
        with pytest.raises(Exception_Validation_Input, match="missing columns"):
            s.get_summary_statistics(rebalancing_result = bad_df)

    @pytest.mark.unit()
    def Test_Summary_At_Target_Zero_Turnover(self) -> None:
        """At target → Turnover == 0."""
        s = _make_strategy(3)
        result_df = s.rebalance(current_weights = s.m_target_weights)
        summary = s.get_summary_statistics(rebalancing_result = result_df)
        assert summary["Turnover"][0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Tests for properties
# ---------------------------------------------------------------------------


class Class_Test_Standard_Properties:
    """Tests for Portfolio_Rebalancing_Standard property accessors."""

    @pytest.mark.unit()
    def Test_Properties_After_Configure(self) -> None:
        """Properties return correct values after configure."""
        s = Portfolio_Rebalancing_Standard(
            tolerance_abs=0.03,
            rebalancing_frequency_days=60,
            transaction_cost_bps=15.0,
        )
        target = np.array([0.5, 0.3, 0.2])
        names = ["X", "Y", "Z"]
        s.configure(target_weights = target, names_assets = names)
        assert s.tolerance_abs == pytest.approx(0.03)
        assert s.rebalancing_frequency_days == 60
        assert s.transaction_cost_bps == pytest.approx(15.0)
        assert s.n_rebalances == 0
        assert s.last_rebalance_date is None
        assert s.is_configured is True
        assert s.names_assets == names
        assert list(s.target_weights) == pytest.approx(target.tolist())

    @pytest.mark.unit()
    def Test_Target_Weights_Property_Returns_Copy(self) -> None:
        """target_weights property returns a copy (mutation-safe)."""
        s = _make_strategy(2)
        w1 = s.target_weights
        w1[0] = 9.99
        w2 = s.target_weights
        assert w2[0] != pytest.approx(9.99)

    @pytest.mark.unit()
    def Test_Names_Assets_Property_Returns_Copy(self) -> None:
        """names_assets property returns a copy."""
        s = _make_strategy(2)
        n1 = s.names_assets
        n1.append("Injected")
        assert len(s.names_assets) == 2

    @pytest.mark.unit()
    def Test_Not_Configured_Is_Configured_False(self) -> None:
        """is_configured is False before configure."""
        s = Portfolio_Rebalancing_Standard()
        assert s.is_configured is False

    @pytest.mark.unit()
    def Test_Repr_Contains_Name(self) -> None:
        """__repr__ contains the strategy name."""
        s = Portfolio_Rebalancing_Standard(name_strategy="My_Test_Strategy")
        assert "My_Test_Strategy" in repr(s)
