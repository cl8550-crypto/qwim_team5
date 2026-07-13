"""Unit tests for the discounting models.

Tests for the abstract base class ``Discounting_Model_Base`` and the
concrete ``Discounting_Model_Constant`` implementation, covering:

- Construction and validation
- ``calc_discount_factor`` with date-based inputs
- ``calc_present_value`` for single cash flows
- ``calc_present_value_stream`` for cash-flow streams
- All five day-count conventions
- Default parameter behaviour (start_date=today, convention=ACTUAL_ACTUAL)
- Edge cases and error paths

Author: QWIM Team
Version: 0.5.1
"""

from __future__ import annotations

import datetime

from datetime import date

import pytest

from src.models.discounting import (
    Discounting_Model_Base,
    Discounting_Model_Constant,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.dates_times_utils.daycount import Daycount_Convention


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture()
def model_5pct() -> Discounting_Model_Constant:
    """Constant-rate model at 5 %."""
    return Discounting_Model_Constant(discount_rate=0.05)


@pytest.fixture()
def model_0pct() -> Discounting_Model_Constant:
    """Constant-rate model at 0 % (no discounting)."""
    return Discounting_Model_Constant(discount_rate=0.0)


@pytest.fixture()
def model_10pct() -> Discounting_Model_Constant:
    """Constant-rate model at 10 %."""
    return Discounting_Model_Constant(discount_rate=0.10)


@pytest.fixture()
def date_jan1_2024() -> date:
    """Return 2024-01-01 (leap year)."""
    return date(2024, 1, 1)


@pytest.fixture()
def date_jul1_2024() -> date:
    """Return 2024-07-01."""
    return date(2024, 7, 1)


@pytest.fixture()
def date_jan1_2025() -> date:
    """Return 2025-01-01."""
    return date(2025, 1, 1)


@pytest.fixture()
def date_jan1_2026() -> date:
    """Return 2026-01-01."""
    return date(2026, 1, 1)


@pytest.fixture()
def date_jan1_2029() -> date:
    """Return 2029-01-01."""
    return date(2029, 1, 1)


# ==============================================================================
# Test: Abstract Base Class Cannot Be Instantiated
# ==============================================================================


class Test_Discounting_Model_Base_ABC:
    """Verify that the abstract base class cannot be instantiated."""

    @pytest.mark.unit()
    def test_cannot_instantiate_abc(self) -> None:
        """``Discounting_Model_Base`` is abstract and should raise."""
        with pytest.raises(TypeError):
            Discounting_Model_Base(name_model="test")  # type: ignore[abstract]


# ==============================================================================
# Test: Discounting_Model_Constant - Construction
# ==============================================================================


class Test_Constant_Model_Construction:
    """Tests for ``Discounting_Model_Constant.__init__``."""

    @pytest.mark.unit()
    def test_valid_positive_rate(self) -> None:
        """Accept a positive discount rate."""
        model = Discounting_Model_Constant(discount_rate=0.05)
        assert model.discount_rate == pytest.approx(0.05)
        assert model.name_model == "Constant Discount Rate"

    @pytest.mark.unit()
    def test_valid_zero_rate(self) -> None:
        """Accept a zero discount rate (no discounting)."""
        model = Discounting_Model_Constant(discount_rate=0.0)
        assert model.discount_rate == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_valid_negative_rate_above_minus_one(self) -> None:
        """Accept a rate in (-1, 0) — rare but mathematically valid."""
        model = Discounting_Model_Constant(discount_rate=-0.02)
        assert model.discount_rate == pytest.approx(-0.02)

    @pytest.mark.unit()
    def test_valid_integer_rate(self) -> None:
        """Accept an integer rate (auto-converted to float)."""
        model = Discounting_Model_Constant(discount_rate=0)
        assert model.discount_rate == pytest.approx(0.0)

    @pytest.mark.unit()
    def test_custom_name(self) -> None:
        """Accept a custom model name."""
        model = Discounting_Model_Constant(
            discount_rate=0.03,
            name_model="My Custom Model",
        )
        assert model.name_model == "My Custom Model"

    @pytest.mark.unit()
    def test_reject_rate_minus_one(self) -> None:
        """Reject rate == -1.0 (division by zero in formula)."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=-1.0)

    @pytest.mark.unit()
    def test_reject_rate_below_minus_one(self) -> None:
        """Reject rate < -1.0."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=-2.0)

    @pytest.mark.unit()
    def test_reject_nan_rate(self) -> None:
        """Reject NaN value."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=float("nan"))

    @pytest.mark.unit()
    def test_reject_inf_rate(self) -> None:
        """Reject +inf value."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=float("inf"))

    @pytest.mark.unit()
    def test_reject_neg_inf_rate(self) -> None:
        """Reject -inf value."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=float("-inf"))

    @pytest.mark.unit()
    def test_reject_string_rate(self) -> None:
        """Reject non-numeric rate."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate="0.05")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_reject_none_rate(self) -> None:
        """Reject None as rate."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_Reject_Bool_Rate(self) -> None:
        """Reject bool as rate instead of coercing it to an integer."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_reject_empty_name(self) -> None:
        """Reject empty model name."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=0.05, name_model="")

    @pytest.mark.unit()
    def test_reject_whitespace_name(self) -> None:
        """Reject whitespace-only model name."""
        with pytest.raises(Exception_Validation_Input):
            Discounting_Model_Constant(discount_rate=0.05, name_model="   ")


# ==============================================================================
# Test: calc_discount_factor - ACTUAL/ACTUAL convention
# ==============================================================================


class Test_Calc_Discount_Factor_Actual_Actual:
    """Tests for ``calc_discount_factor`` with ACTUAL_ACTUAL convention."""

    @pytest.mark.unit()
    def test_one_year_5pct(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """d(1 year) = 1 / 1.05 for a non-leap to non-leap year boundary."""
        # 2024 is a leap year -> 366 days -> year_fraction = 366/366 = 1.0
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.ACTUAL_ACTUAL,
        )
        expected = 1.0 / 1.05
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_two_years_5pct(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2026: date,
    ) -> None:
        """d(2 years) = 1 / 1.05^2."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2026,
            start_date=date_jan1_2024,
        )
        # 2024: 366 days (leap), 2025: 365 days -> total 731 days
        # ACTUAL_ACTUAL: 366/366 + 365/365 = 2.0
        expected = 1.0 / (1.05**2)
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_same_dates_returns_one(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
    ) -> None:
        """Same start and end -> d(0) = 1."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2024,
            start_date=date_jan1_2024,
        )
        assert d == pytest.approx(1.0, rel=1e-12)

    @pytest.mark.unit()
    def test_zero_rate_always_one(
        self,
        model_0pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """With 0 % rate, discount factor is always 1."""
        d = model_0pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        assert d == pytest.approx(1.0, rel=1e-12)

    @pytest.mark.unit()
    def test_five_years_10pct(
        self,
        model_10pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2029: date,
    ) -> None:
        """d(5 years) = 1 / 1.10^5."""
        d = model_10pct.calc_discount_factor(
            end_date=date_jan1_2029,
            start_date=date_jan1_2024,
        )
        # Actual/actual for 5 years: should be ~5.0 year fraction
        # 2024(leap)=366/366 + 2025=365/365 + 2026=365/365 + 2027=365/365 + 2028(leap)=366/366 = 5.0
        expected = 1.0 / (1.10**5)
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_half_year_leap(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jul1_2024: date,
    ) -> None:
        """Half of a leap year using ACTUAL_ACTUAL."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jul1_2024,
            start_date=date_jan1_2024,
        )
        # Jan 1 to Jul 1, 2024: 182 days / 366 days (leap year)
        year_frac = 182.0 / 366.0
        expected = 1.0 / (1.05**year_frac)
        assert d == pytest.approx(expected, rel=1e-9)


# ==============================================================================
# Test: calc_discount_factor - Other day-count conventions
# ==============================================================================


class Test_Calc_Discount_Factor_Other_Conventions:
    """Tests for ``calc_discount_factor`` with non-ACTUAL_ACTUAL conventions."""

    @pytest.mark.unit()
    def test_thirty_360(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """30/360 convention: 360/360 = 1.0 year."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.THIRTY_360,
        )
        expected = 1.0 / 1.05
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_thirty_365(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """30/365 convention: 360/365 year fraction."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.THIRTY_365,
        )
        year_frac = 360.0 / 365.0
        expected = 1.0 / (1.05**year_frac)
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_actual_360(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """ACTUAL/360 convention: 366/360 year fraction (leap year)."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.ACTUAL_360,
        )
        year_frac = 366.0 / 360.0
        expected = 1.0 / (1.05**year_frac)
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_actual_365(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """ACTUAL/365 convention: 366/365 year fraction (leap year)."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.ACTUAL_365,
        )
        year_frac = 366.0 / 365.0
        expected = 1.0 / (1.05**year_frac)
        assert d == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize(
        "convention",
        list(Daycount_Convention),
        ids=lambda c: c.name,
    )
    @pytest.mark.unit()
    def test_all_conventions_same_date(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        convention: Daycount_Convention,
    ) -> None:
        """Same start and end date -> d(0) = 1 for every convention."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2024,
            start_date=date_jan1_2024,
            daycount_convention=convention,
        )
        assert d == pytest.approx(1.0, rel=1e-12)

    @pytest.mark.parametrize(
        "convention",
        list(Daycount_Convention),
        ids=lambda c: c.name,
    )
    @pytest.mark.unit()
    def test_all_conventions_zero_rate(
        self,
        model_0pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
        convention: Daycount_Convention,
    ) -> None:
        """Zero rate => d(t) = 1 for all conventions."""
        d = model_0pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=convention,
        )
        assert d == pytest.approx(1.0, rel=1e-12)


# ==============================================================================
# Test: calc_discount_factor - Default parameters
# ==============================================================================


class Test_Calc_Discount_Factor_Defaults:
    """Tests for default ``start_date`` and ``daycount_convention``."""

    @pytest.mark.unit()
    def test_default_start_date_is_today(
        self,
        model_5pct: Discounting_Model_Constant,
    ) -> None:
        """When ``start_date`` is omitted, today's date is used."""
        today = datetime.datetime.now(tz=datetime.UTC).date()
        future = date(today.year + 1, today.month, today.day)

        d_explicit = model_5pct.calc_discount_factor(
            end_date=future,
            start_date=today,
        )
        d_default = model_5pct.calc_discount_factor(
            end_date=future,
        )
        # Should be identical (both use today)
        assert d_default == pytest.approx(d_explicit, rel=1e-12)

    @pytest.mark.unit()
    def test_default_convention_is_actual_actual(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Default convention should match explicit ACTUAL_ACTUAL."""
        d_default = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        d_explicit = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.ACTUAL_ACTUAL,
        )
        assert d_default == pytest.approx(d_explicit, rel=1e-12)


# ==============================================================================
# Test: calc_discount_factor - Validation errors
# ==============================================================================


class Test_Calc_Discount_Factor_Validation:
    """Tests for input validation in ``calc_discount_factor``."""

    @pytest.mark.unit()
    def test_reject_string_end_date(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
    ) -> None:
        """Reject string instead of date for end_date."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_discount_factor(
                end_date="2025-01-01",  # type: ignore[arg-type]
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_reject_string_start_date(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2025: date,
    ) -> None:
        """Reject string instead of date for start_date."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_discount_factor(
                end_date=date_jan1_2025,
                start_date="2024-01-01",  # type: ignore[arg-type]
            )

    @pytest.mark.unit()
    def test_reject_end_before_start(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject end_date before start_date."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_discount_factor(
                end_date=date_jan1_2024,
                start_date=date_jan1_2025,
            )

    @pytest.mark.unit()
    def test_reject_none_end_date(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
    ) -> None:
        """Reject None as end_date."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_discount_factor(
                end_date=None,  # type: ignore[arg-type]
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_reject_integer_end_date(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
    ) -> None:
        """Reject int as end_date."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_discount_factor(
                end_date=20250101,  # type: ignore[arg-type]
                start_date=date_jan1_2024,
            )


# ==============================================================================
# Test: calc_present_value
# ==============================================================================


class Test_Calc_Present_Value:
    """Tests for ``calc_present_value``."""

    @pytest.mark.unit()
    def test_pv_one_year_5pct(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """PV of 1000 in 1 year at 5 % = 1000 / 1.05."""
        pv = model_5pct.calc_present_value(
            cash_flow=1000.0,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        expected = 1000.0 / 1.05
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_pv_zero_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """PV of 0 cash flow is always 0."""
        pv = model_5pct.calc_present_value(
            cash_flow=0.0,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        assert pv == pytest.approx(0.0, abs=1e-15)

    @pytest.mark.unit()
    def test_pv_negative_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """PV of negative cash flow returns negative PV."""
        pv = model_5pct.calc_present_value(
            cash_flow=-500.0,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        expected = -500.0 / 1.05
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_pv_integer_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Accept integer cash flow."""
        pv = model_5pct.calc_present_value(
            cash_flow=1000,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        expected = 1000.0 / 1.05
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_pv_with_thirty_360(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """PV with 30/360 convention."""
        pv = model_5pct.calc_present_value(
            cash_flow=1000.0,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
            daycount_convention=Daycount_Convention.THIRTY_360,
        )
        # 30/360: 360/360 = 1.0 year
        expected = 1000.0 / 1.05
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_pv_reject_string_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject non-numeric cash flow."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value(
                cash_flow="1000",  # type: ignore[arg-type]
                end_date=date_jan1_2025,
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_pv_reject_none_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject None as cash flow."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value(
                cash_flow=None,  # type: ignore[arg-type]
                end_date=date_jan1_2025,
                start_date=date_jan1_2024,
            )


# ==============================================================================
# Test: calc_present_value_stream
# ==============================================================================


class Test_Calc_Present_ValueStream:
    """Tests for ``calc_present_value_stream``."""

    @pytest.mark.unit()
    def test_stream_single_cashflow(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Stream with one cash flow matches single PV."""
        pv_stream = model_5pct.calc_present_value_stream(
            cash_flows=[1000.0],
            end_dates=[date_jan1_2025],
            start_date=date_jan1_2024,
        )
        pv_single = model_5pct.calc_present_value(
            cash_flow=1000.0,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        assert pv_stream == pytest.approx(pv_single, rel=1e-12)

    @pytest.mark.unit()
    def test_stream_multiple_cashflows(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
        date_jan1_2026: date,
    ) -> None:
        """PV of two annual cash flows at 5 %."""
        pv = model_5pct.calc_present_value_stream(
            cash_flows=[100.0, 100.0],
            end_dates=[date_jan1_2025, date_jan1_2026],
            start_date=date_jan1_2024,
        )
        # year fractions: 1.0 and 2.0 (ACTUAL_ACTUAL, whole years)
        expected = 100.0 / 1.05 + 100.0 / (1.05**2)
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_stream_three_annual_cashflows(
        self,
        model_10pct: Discounting_Model_Constant,
    ) -> None:
        """PV of three annual cash flows at 10 %."""
        start = date(2023, 1, 1)
        dates = [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1)]
        cfs = [1000.0, 2000.0, 3000.0]

        pv = model_10pct.calc_present_value_stream(
            cash_flows=cfs,
            end_dates=dates,
            start_date=start,
        )

        # Manual calculation
        # 2023 is not a leap year: 365 days -> yf = 365/365 = 1.0
        # 2024 is leap year: 366 days -> cumulative yf = 1.0 + 366/366 = 2.0
        # 2025 is not leap: 365 days -> cumulative yf = 2.0 + 365/365 = 3.0
        expected = 1000.0 / (1.10**1.0) + 2000.0 / (1.10**2.0) + 3000.0 / (1.10**3.0)
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_stream_with_convention(
        self,
        model_5pct: Discounting_Model_Constant,
    ) -> None:
        """PV stream using 30/360 convention."""
        start = date(2024, 1, 1)
        dates = [date(2024, 7, 1), date(2025, 1, 1)]
        cfs = [500.0, 500.0]

        pv = model_5pct.calc_present_value_stream(
            cash_flows=cfs,
            end_dates=dates,
            start_date=start,
            daycount_convention=Daycount_Convention.THIRTY_360,
        )

        # 30/360: Jan1 to Jul1 = 6*30 = 180 days / 360 = 0.5
        # 30/360: Jan1 to Jan1 = 12*30 = 360 days / 360 = 1.0
        expected = 500.0 / (1.05**0.5) + 500.0 / (1.05**1.0)
        assert pv == pytest.approx(expected, rel=1e-9)

    @pytest.mark.unit()
    def test_stream_reject_length_mismatch(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject mismatched lengths of cash_flows and end_dates."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value_stream(
                cash_flows=[100.0, 200.0],
                end_dates=[date_jan1_2025],
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_stream_reject_empty_lists(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
    ) -> None:
        """Reject empty cash_flows list."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value_stream(
                cash_flows=[],
                end_dates=[],
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_stream_reject_non_list_cashflows(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject tuple instead of list for cash_flows."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value_stream(
                cash_flows=(100.0,),  # type: ignore[arg-type]
                end_dates=[date_jan1_2025],
                start_date=date_jan1_2024,
            )

    @pytest.mark.unit()
    def test_stream_reject_non_list_dates(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """Reject tuple instead of list for end_dates."""
        with pytest.raises(Exception_Validation_Input):
            model_5pct.calc_present_value_stream(
                cash_flows=[100.0],
                end_dates=(date_jan1_2025,),  # type: ignore[arg-type]
                start_date=date_jan1_2024,
            )


# ==============================================================================
# Test: Properties and dunder methods
# ==============================================================================


class Test_Model_Properties:
    """Tests for properties and dunder methods."""

    @pytest.mark.unit()
    def test_name_model_property(self, model_5pct: Discounting_Model_Constant) -> None:
        """``name_model`` property returns the model name."""
        assert model_5pct.name_model == "Constant Discount Rate"

    @pytest.mark.unit()
    def test_discount_rate_property(
        self,
        model_5pct: Discounting_Model_Constant,
    ) -> None:
        """``discount_rate`` property returns the rate."""
        assert model_5pct.discount_rate == pytest.approx(0.05)

    @pytest.mark.unit()
    def test_repr_constant(self, model_5pct: Discounting_Model_Constant) -> None:
        """``__repr__`` contains class name, model name, and rate."""
        r = repr(model_5pct)
        assert "Discounting_Model_Constant" in r
        assert "Constant Discount Rate" in r
        assert "0.05" in r

    @pytest.mark.unit()
    def test_repr_base_info(self, model_5pct: Discounting_Model_Constant) -> None:
        """``__repr__`` from base includes name_model."""
        r = repr(model_5pct)
        assert "name_model=" in r


# ==============================================================================
# Test: Mathematical properties
# ==============================================================================


class Test_Mathematical_Properties:
    """Verify key mathematical properties of the discount factor."""

    @pytest.mark.unit()
    def test_discount_factor_between_zero_and_one(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """For positive rate, 0 < d(t) < 1 when t > 0."""
        d = model_5pct.calc_discount_factor(
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        assert 0.0 < d < 1.0

    @pytest.mark.unit()
    def test_discount_factor_decreases_with_time(
        self,
        model_5pct: Discounting_Model_Constant,
    ) -> None:
        """Longer time => smaller discount factor (positive rate)."""
        start = date(2024, 1, 1)
        d1 = model_5pct.calc_discount_factor(
            end_date=date(2025, 1, 1),
            start_date=start,
        )
        d2 = model_5pct.calc_discount_factor(
            end_date=date(2026, 1, 1),
            start_date=start,
        )
        d3 = model_5pct.calc_discount_factor(
            end_date=date(2029, 1, 1),
            start_date=start,
        )
        assert d1 > d2 > d3

    @pytest.mark.unit()
    def test_higher_rate_gives_lower_factor(self) -> None:
        """Higher discount rate => lower discount factor."""
        start = date(2024, 1, 1)
        end = date(2025, 1, 1)

        model_low = Discounting_Model_Constant(discount_rate=0.03)
        model_high = Discounting_Model_Constant(discount_rate=0.10)

        d_low = model_low.calc_discount_factor(end_date=end, start_date=start)
        d_high = model_high.calc_discount_factor(end_date=end, start_date=start)

        assert d_low > d_high

    @pytest.mark.unit()
    def test_pv_less_than_future_value(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
    ) -> None:
        """PV is less than future value for positive rate and t > 0."""
        fv = 1000.0
        pv = model_5pct.calc_present_value(
            cash_flow=fv,
            end_date=date_jan1_2025,
            start_date=date_jan1_2024,
        )
        assert pv < fv

    @pytest.mark.unit()
    def test_additivity_of_pv_stream(
        self,
        model_5pct: Discounting_Model_Constant,
        date_jan1_2024: date,
        date_jan1_2025: date,
        date_jan1_2026: date,
    ) -> None:
        """PV stream == sum of individual PVs."""
        cfs = [100.0, 200.0]
        dates = [date_jan1_2025, date_jan1_2026]

        pv_stream = model_5pct.calc_present_value_stream(
            cash_flows=cfs,
            end_dates=dates,
            start_date=date_jan1_2024,
        )

        pv_sum = sum(
            model_5pct.calc_present_value(
                cash_flow=cf,
                end_date=ed,
                start_date=date_jan1_2024,
            )
            for cf, ed in zip(cfs, dates, strict=True)
        )

        assert pv_stream == pytest.approx(pv_sum, rel=1e-12)

    @pytest.mark.unit()
    def test_negative_rate_gives_factor_above_one(self) -> None:
        """Negative rate (above -1) => d(t) > 1 for t > 0."""
        model_neg = Discounting_Model_Constant(discount_rate=-0.02)
        start = date(2024, 1, 1)
        end = date(2025, 1, 1)

        d = model_neg.calc_discount_factor(end_date=end, start_date=start)
        assert d > 1.0


# ==============================================================================
# Tests: Discounting_Model_Base __repr__ (base-class method)
# ==============================================================================


class Test_Discounting_Model_Base_Repr:
    """Verify that the base-class ``__repr__`` is reachable.

    ``Discounting_Model_Constant`` overrides ``__repr__`` without calling
    ``super()``, so the base implementation at line 342 is never reached via
    the concrete class.  A minimal stub subclass that does *not* override
    ``__repr__`` is used to exercise the base implementation directly.
    """

    @pytest.mark.unit()
    def test_base_repr_contains_name_model(self) -> None:
        """Base ``__repr__`` must contain name_model."""

        class Discounting_Stub(Discounting_Model_Base):
            """Minimal concrete subclass with no ``__repr__`` override."""

            def calc_discount_factor(
                self,
                end_date: date,
                *,
                start_date: date | None = None,
            ) -> float:
                """Stub: always returns 1.0."""
                return 1.0

        stub = Discounting_Stub(name_model="Stub_Model")
        r = repr(stub)
        assert "Discounting_Stub" in r
        assert "name_model=" in r
        assert "Stub_Model" in r
