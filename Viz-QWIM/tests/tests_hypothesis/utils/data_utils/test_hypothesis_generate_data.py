"""Property-based tests for generate_data utility helpers."""

from __future__ import annotations

import datetime as dt

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.data_utils.generate_data import generate_monthly_timeseries


def _add_months(start_date: dt.date, months: int) -> dt.date:
    """Return the first day of the month *months* after *start_date*."""
    month_index = (start_date.month - 1) + months
    return dt.date(start_date.year + month_index // 12, month_index % 12 + 1, 1)


START_YEAR_STRATEGY = st.integers(min_value=2018, max_value=2025)
START_MONTH_STRATEGY = st.integers(min_value=1, max_value=12)
MONTH_COUNT_STRATEGY = st.integers(min_value=1, max_value=18)


class Class_Test_Hypothesis_Generate_Data:
    """Property-based tests for deterministic monthly-series generation."""

    @pytest.mark.unit()
    @given(
        start_year=START_YEAR_STRATEGY,
        start_month=START_MONTH_STRATEGY,
        month_count=MONTH_COUNT_STRATEGY,
    )
    @settings(max_examples=60)
    def Test_Generate_Monthly_Timeseries_Uses_Requested_Number_Of_Months(
        self,
        start_year: int,
        start_month: int,
        month_count: int,
    ) -> None:
        """Monthly generation returns one row per requested month window."""
        start_date = dt.date(start_year, start_month, 1)
        end_date = _add_months(start_date, month_count)

        result = generate_monthly_timeseries(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        assert result.shape[0] == month_count
        assert list(result.columns) == ["date", "AA", "BB", "CC", "DD", "EE", "FF", "GG"]

    @pytest.mark.unit()
    @given(
        start_year=START_YEAR_STRATEGY,
        start_month=START_MONTH_STRATEGY,
        month_count=MONTH_COUNT_STRATEGY,
    )
    @settings(max_examples=60)
    def Test_Generate_Monthly_Timeseries_Dates_Are_Strictly_Increasing(
        self,
        start_year: int,
        start_month: int,
        month_count: int,
    ) -> None:
        """Generated monthly dates stay unique and strictly increasing."""
        start_date = dt.date(start_year, start_month, 1)
        end_date = _add_months(start_date, month_count)

        result = generate_monthly_timeseries(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        dates = result["date"].to_list()

        assert dates == sorted(dates)
        assert len(dates) == len(set(dates))