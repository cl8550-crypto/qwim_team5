"""Hypothesis property-based tests for the daycount module.

Property tests cover all five concrete day-count calculators
(30/360, 30/365, ACTUAL/360, ACTUAL/365, ACTUAL/ACTUAL) and the
factory function, verifying universal mathematical invariants:

- Non-negativity: year fraction >= 0 for any valid date pair.
- Zero-crossing: year fraction == 0 when start == end.
- Actual/360 exact formula: days / 360.
- Actual/365 exact formula: days / 365.
- 30/360 symmetry: Jan 01 to Jul 01 always 0.5.
- Factory round-trip: correct calculator type per convention.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math
from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.dates_times_utils.daycount import (
    Daycount_Actual_360,
    Daycount_Actual_365,
    Daycount_Actual_Actual,
    Daycount_Convention,
    Daycount_Thirty_360,
    Daycount_Thirty_365,
    get_daycount_calculator,
)


# ---------------------------------------------------------------------------
# Shared strategy helpers
# ---------------------------------------------------------------------------

# Dates bounded to a financially meaningful range (1900–2200)
_strategy_date = st.dates(
    min_value=date(1900, 1, 1),
    max_value=date(2200, 12, 31),
)


def _strategy_date_pair():
    """Strategy that produces (start, end) pairs where start <= end."""
    return st.tuples(_strategy_date, _strategy_date).map(
        lambda pair: (min(pair), max(pair))
    )


# Reuse stateless calculators so Hypothesis examples do not pay constructor
# logging overhead on every draw.
_CALC_DAYCOUNT_THIRTY_360 = Daycount_Thirty_360()
_CALC_DAYCOUNT_THIRTY_365 = Daycount_Thirty_365()
_CALC_DAYCOUNT_ACTUAL_360 = Daycount_Actual_360()
_CALC_DAYCOUNT_ACTUAL_365 = Daycount_Actual_365()
_CALC_DAYCOUNT_ACTUAL_ACTUAL = Daycount_Actual_Actual()


# ---------------------------------------------------------------------------
# 30/360 calculator
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Daycount_Thirty_360:
    """Property-based tests for :class:`Daycount_Thirty_360`."""

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_year_fraction_nonneg(self, pair: tuple[date, date]) -> None:
        """Year fraction is >= 0 for any valid date pair."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(date_val=_strategy_date)
    @settings(max_examples=200)
    def Test_zero_when_equal_dates(self, date_val: date) -> None:
        """Year fraction is exactly 0 when start == end."""
        result = _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date_val, date_end = date_val)
        assert result == 0.0

    @pytest.mark.unit()
    @given(year_val=st.integers(min_value=1900, max_value=2199))
    @settings(max_examples=200)
    def Test_jan_to_jul_is_half_year(self, year_val: int) -> None:
        """Jan 01 to Jul 01 equals 0.5 under 30/360 for any non-EOM year."""
        date_start = date(year_val, 1, 1)
        date_end = date(year_val, 7, 1)
        result = _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert math.isclose(result, 0.5, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_result_is_finite(self, pair: tuple[date, date]) -> None:
        """Year fraction is always a finite float."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert math.isfinite(result)

    @pytest.mark.unit()
    def Test_raises_on_reversed_dates(self) -> None:
        """Raises when end < start."""
        with pytest.raises(Exception_Validation_Input):
            _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date(2025, 6, 1), date_end = date(2025, 1, 1))


# ---------------------------------------------------------------------------
# 30/365 calculator
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Daycount_Thirty_365:
    """Property-based tests for :class:`Daycount_Thirty_365`."""

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_year_fraction_nonneg(self, pair: tuple[date, date]) -> None:
        """Year fraction is >= 0 for any valid date pair."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_THIRTY_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(date_val=_strategy_date)
    @settings(max_examples=200)
    def Test_zero_when_equal_dates(self, date_val: date) -> None:
        """Year fraction is exactly 0 when start == end."""
        result = _CALC_DAYCOUNT_THIRTY_365.calc_year_fraction(date_start = date_val, date_end = date_val)
        assert result == 0.0

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_result_is_finite(self, pair: tuple[date, date]) -> None:
        """Year fraction is always a finite float."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_THIRTY_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert math.isfinite(result)

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_larger_than_thirty_360_for_same_period(
        self, pair: tuple[date, date]
    ) -> None:
        """30/365 fraction <= 30/360 fraction (365 denominator > 360)."""
        date_start, date_end = pair
        frac_360 = _CALC_DAYCOUNT_THIRTY_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        frac_365 = _CALC_DAYCOUNT_THIRTY_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        # same numerator, larger denominator → smaller or equal fraction
        assert frac_365 <= frac_360 + 1e-12


# ---------------------------------------------------------------------------
# ACTUAL/360 calculator
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Daycount_Actual_360:
    """Property-based tests for :class:`Daycount_Actual_360`."""

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_exact_formula_days_over_360(self, pair: tuple[date, date]) -> None:
        """Year fraction equals (date_end - date_start).days / 360."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        expected = (date_end - date_start).days / 360.0
        assert math.isclose(result, expected, rel_tol=1e-12, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(date_val=_strategy_date)
    @settings(max_examples=200)
    def Test_zero_when_equal_dates(self, date_val: date) -> None:
        """Year fraction is exactly 0 when start == end."""
        result = _CALC_DAYCOUNT_ACTUAL_360.calc_year_fraction(date_start = date_val, date_end = date_val)
        assert result == 0.0

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_year_fraction_nonneg(self, pair: tuple[date, date]) -> None:
        """Year fraction is >= 0 for any valid date pair."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0


# ---------------------------------------------------------------------------
# ACTUAL/365 calculator
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Daycount_Actual_365:
    """Property-based tests for :class:`Daycount_Actual_365`."""

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_exact_formula_days_over_365(self, pair: tuple[date, date]) -> None:
        """Year fraction equals (date_end - date_start).days / 365."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        expected = (date_end - date_start).days / 365.0
        assert math.isclose(result, expected, rel_tol=1e-12, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(date_val=_strategy_date)
    @settings(max_examples=200)
    def Test_zero_when_equal_dates(self, date_val: date) -> None:
        """Year fraction is exactly 0 when start == end."""
        result = _CALC_DAYCOUNT_ACTUAL_365.calc_year_fraction(date_start = date_val, date_end = date_val)
        assert result == 0.0

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_year_fraction_nonneg(self, pair: tuple[date, date]) -> None:
        """Year fraction is >= 0 for any valid date pair."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_smaller_than_actual_360_for_same_period(
        self, pair: tuple[date, date]
    ) -> None:
        """Actual/365 fraction <= Actual/360 fraction (larger denominator)."""
        date_start, date_end = pair
        frac_360 = _CALC_DAYCOUNT_ACTUAL_360.calc_year_fraction(date_start = date_start, date_end = date_end)
        frac_365 = _CALC_DAYCOUNT_ACTUAL_365.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert frac_365 <= frac_360 + 1e-12


# ---------------------------------------------------------------------------
# ACTUAL/ACTUAL calculator
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Daycount_Actual_Actual:
    """Property-based tests for :class:`Daycount_Actual_Actual`."""

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_year_fraction_nonneg(self, pair: tuple[date, date]) -> None:
        """Year fraction is >= 0 for any valid date pair."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_ACTUAL.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0

    @pytest.mark.unit()
    @given(date_val=_strategy_date)
    @settings(max_examples=200)
    def Test_zero_when_equal_dates(self, date_val: date) -> None:
        """Year fraction is exactly 0 when start == end."""
        result = _CALC_DAYCOUNT_ACTUAL_ACTUAL.calc_year_fraction(date_start = date_val, date_end = date_val)
        assert result == 0.0

    @pytest.mark.unit()
    @given(pair=_strategy_date_pair())
    @settings(max_examples=200)
    def Test_result_is_finite(self, pair: tuple[date, date]) -> None:
        """Year fraction is always a finite float."""
        date_start, date_end = pair
        result = _CALC_DAYCOUNT_ACTUAL_ACTUAL.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert math.isfinite(result)

    @pytest.mark.unit()
    @given(year_val=st.integers(min_value=1901, max_value=2199))
    @settings(max_examples=200)
    def Test_full_non_leap_year_is_one(self, year_val: int) -> None:
        """A full non-leap year spans exactly 1.0 under ACTUAL/ACTUAL."""
        import calendar
        if calendar.isleap(year_val):
            return
        date_start = date(year_val, 1, 1)
        date_end = date(year_val + 1, 1, 1)
        result = _CALC_DAYCOUNT_ACTUAL_ACTUAL.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert math.isclose(result, 1.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Get_Daycount_Calculator:
    """Property-based tests for :func:`get_daycount_calculator`."""

    @pytest.mark.unit()
    @given(convention=st.sampled_from(Daycount_Convention))
    @settings(max_examples=200)
    def Test_factory_returns_correct_type(
        self, convention: Daycount_Convention
    ) -> None:
        """Factory returns a calculator whose ``convention`` attribute matches."""
        calc = get_daycount_calculator(convention = convention)
        assert calc.convention == convention

    @pytest.mark.unit()
    @given(
        convention=st.sampled_from(Daycount_Convention),
        pair=_strategy_date_pair(),
    )
    @settings(max_examples=200)
    def Test_factory_calc_year_fraction_nonneg(
        self,
        convention: Daycount_Convention,
        pair: tuple[date, date],
    ) -> None:
        """Year fraction from any factory-produced calculator is >= 0."""
        date_start, date_end = pair
        calc = get_daycount_calculator(convention = convention)
        result = calc.calc_year_fraction(date_start = date_start, date_end = date_end)
        assert result >= 0.0
