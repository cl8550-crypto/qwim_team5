"""Hypothesis property-based tests for Discounting_Model_Constant.

Property tests verify mathematical invariants of the constant-rate
discounting model:

- Discount factor in (0, 1] for r >= 0 and t >= 0.
- Discount factor == 1 when start_date == end_date (t = 0).
- Monotonicity: higher rate  → smaller discount factor.
- Monotonicity: later end_date → smaller discount factor.
- PV <= cash_flow for non-negative rates.
- Present-value stream equals sum of individual PVs.
- All five day-count conventions yield finite, positive results.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import pytest
from hypothesis import assume, given, HealthCheck, settings
from hypothesis import strategies as st

from src.models.discounting import Discounting_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.dates_times_utils.daycount import Daycount_Convention


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_strategy_rate_nonneg = st.floats(
    min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False
)

_strategy_rate_any_valid = st.floats(
    min_value=-0.9, max_value=10.0, allow_nan=False, allow_infinity=False
)

_strategy_date_base = st.dates(
    min_value=date(2000, 1, 1),
    max_value=date(2100, 12, 31),
)


def _strategy_date_pair():
    """Strategy producing (start, end) date pairs where start <= end."""
    return st.tuples(_strategy_date_base, _strategy_date_base).map(
        lambda pair: (min(pair), max(pair))
    )


# ---------------------------------------------------------------------------
# Construction invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discounting_Construction:
    """Property tests for ``Discounting_Model_Constant.__init__``."""

    @pytest.mark.unit()
    def Test_Bool_Rate_Raises(self) -> None:
        """Boolean discount rates are rejected as invalid numeric inputs."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(rate_val=_strategy_rate_nonneg)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_valid_nonneg_rate_stores_correctly(self, rate_val: float) -> None:
        """Constructor stores any valid non-negative rate without error."""
        model = Discounting_Model_Constant(discount_rate=rate_val)
        assert math.isclose(model.discount_rate, rate_val, rel_tol=1e-12, abs_tol=1e-15)

    @pytest.mark.unit()
    @given(rate_val=_strategy_rate_any_valid)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_valid_rate_above_minus_one_accepted(self, rate_val: float) -> None:
        """Any finite rate strictly greater than -1 is accepted."""
        assume(rate_val > -1.0)
        model = Discounting_Model_Constant(discount_rate=rate_val)
        assert math.isfinite(model.discount_rate)

    @pytest.mark.unit()
    @given(rate_val=st.floats(max_value=-1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_rate_le_minus_one_raises(self, rate_val: float) -> None:
        """Rates <= -1 raise Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=rate_val)


# ---------------------------------------------------------------------------
# calc_discount_factor: zero time
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discount_Factor_Zero_Time:
    """Discount factor must equal 1 when start == end."""

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_any_valid,
        date_val=_strategy_date_base,
        convention=st.sampled_from(Daycount_Convention),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_factor_one_at_zero_time(
        self,
        rate_val: float,
        date_val: date,
        convention: Daycount_Convention,
    ) -> None:
        """d(t=0) == 1 regardless of rate or convention."""
        assume(rate_val > -1.0)
        model = Discounting_Model_Constant(discount_rate=rate_val)
        factor = model.calc_discount_factor(
            end_date=date_val,
            start_date=date_val,
            daycount_convention=convention,
        )
        assert math.isclose(factor, 1.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# calc_discount_factor: non-negative rate invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discount_Factor_Nonneg_Rate:
    """For r >= 0 and t >= 0, discount factor must lie in (0, 1]."""

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_nonneg,
        pair=_strategy_date_pair(),
        convention=st.sampled_from(Daycount_Convention),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_factor_in_zero_one_interval(
        self,
        rate_val: float,
        pair: tuple[date, date],
        convention: Daycount_Convention,
    ) -> None:
        """0 < d(t) <= 1 for all r >= 0, t >= 0."""
        date_start, date_end = pair
        model = Discounting_Model_Constant(discount_rate=rate_val)
        factor = model.calc_discount_factor(
            end_date=date_end,
            start_date=date_start,
            daycount_convention=convention,
        )
        assert factor > 0.0
        assert factor <= 1.0 + 1e-12  # small tolerance for floating-point edge at t=0

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_nonneg,
        pair=_strategy_date_pair(),
        convention=st.sampled_from(Daycount_Convention),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_factor_is_finite(
        self,
        rate_val: float,
        pair: tuple[date, date],
        convention: Daycount_Convention,
    ) -> None:
        """Discount factor is always a finite positive float."""
        date_start, date_end = pair
        model = Discounting_Model_Constant(discount_rate=rate_val)
        factor = model.calc_discount_factor(
            end_date=date_end,
            start_date=date_start,
            daycount_convention=convention,
        )
        assert math.isfinite(factor)
        assert factor > 0.0


# ---------------------------------------------------------------------------
# calc_discount_factor: rate monotonicity
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discount_Factor_Rate_Monotonicity:
    """Higher rate implies smaller (or equal) discount factor."""

    @pytest.mark.unit()
    @given(
        rate_lo=st.floats(min_value=0.0, max_value=4.9, allow_nan=False, allow_infinity=False),
        rate_hi=st.floats(min_value=5.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        pair=_strategy_date_pair(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_higher_rate_smaller_factor(
        self,
        rate_lo: float,
        rate_hi: float,
        pair: tuple[date, date],
    ) -> None:
        """factor(r_low) >= factor(r_high) for any t >= 0."""
        date_start, date_end = pair
        model_lo = Discounting_Model_Constant(discount_rate=rate_lo)
        model_hi = Discounting_Model_Constant(discount_rate=rate_hi)
        factor_lo = model_lo.calc_discount_factor(end_date=date_end, start_date=date_start)
        factor_hi = model_hi.calc_discount_factor(end_date=date_end, start_date=date_start)
        assert factor_lo >= factor_hi - 1e-12


# ---------------------------------------------------------------------------
# calc_discount_factor: time monotonicity
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discount_Factor_Time_Monotonicity:
    """Later end date implies smaller discount factor (for r > 0)."""

    @pytest.mark.unit()
    @given(
        rate_val=st.floats(min_value=0.001, max_value=5.0, allow_nan=False, allow_infinity=False),
        date_start=_strategy_date_base,
        extra_days=st.integers(min_value=1, max_value=3650),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_later_end_date_smaller_factor(
        self,
        rate_val: float,
        date_start: date,
        extra_days: int,
    ) -> None:
        """d(t + extra) < d(t) when r > 0."""
        assume(date_start + timedelta(days=extra_days) <= date(2100, 12, 31))
        date_end_near = date_start
        date_end_far = date_start + timedelta(days=extra_days)
        model = Discounting_Model_Constant(discount_rate=rate_val)
        factor_near = model.calc_discount_factor(end_date=date_end_near, start_date=date_start)
        factor_far = model.calc_discount_factor(end_date=date_end_far, start_date=date_start)
        assert factor_far <= factor_near + 1e-12


# ---------------------------------------------------------------------------
# calc_present_value: PV <= cash_flow for r >= 0
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Present_Value_Upper_Bound:
    """PV of a positive cash flow is at most the cash flow for r >= 0."""

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_nonneg,
        cash_flow=st.floats(min_value=0.01, max_value=1e9, allow_nan=False, allow_infinity=False),
        pair=_strategy_date_pair(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_pv_le_cashflow_for_nonneg_rate(
        self,
        rate_val: float,
        cash_flow: float,
        pair: tuple[date, date],
    ) -> None:
        """PV(CF, t) <= CF for all t >= 0, r >= 0."""
        date_start, date_end = pair
        model = Discounting_Model_Constant(discount_rate=rate_val)
        pv_val = model.calc_present_value(
            cash_flow=cash_flow,
            end_date=date_end,
            start_date=date_start,
        )
        assert pv_val <= cash_flow + 1e-6


# ---------------------------------------------------------------------------
# calc_present_value_stream: additivity
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Present_Value_Stream_Additivity:
    """PV of stream equals sum of individual PVs."""

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_nonneg,
        date_start=_strategy_date_base,
        n_flows=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def Test_stream_pv_equals_sum_of_individual_pvs(
        self,
        rate_val: float,
        date_start: date,
        n_flows: int,
    ) -> None:
        """PV(stream) == sum_i PV(CF_i, date_i)."""
        cash_flows = [100.0 * (idx + 1) for idx in range(n_flows)]
        end_dates = [
            date_start + timedelta(days=365 * (idx + 1)) for idx in range(n_flows)
        ]
        assume(all(dt <= date(2100, 12, 31) for dt in end_dates))

        model = Discounting_Model_Constant(discount_rate=rate_val)

        stream_pv = model.calc_present_value_stream(
            cash_flows=cash_flows,
            end_dates=end_dates,
            start_date=date_start,
        )

        individual_sum = sum(
            model.calc_present_value(
                cash_flow=cf_val,
                end_date=dt_val,
                start_date=date_start,
            )
            for cf_val, dt_val in zip(cash_flows, end_dates)
        )

        assert math.isclose(stream_pv, individual_sum, rel_tol=1e-9, abs_tol=1e-9)
