"""Unit tests for the daycount module.

Tests for day-count convention enumerator, abstract base class,
all five concrete calculators (30/360, 30/365, ACTUAL/360, ACTUAL/365,
ACTUAL/ACTUAL), and the factory function.

Author: QWIM Team
Version: 0.5.1
"""

from __future__ import annotations

from datetime import date

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.dates_times_utils.daycount import (
    Daycount_Actual_360,
    Daycount_Actual_365,
    Daycount_Actual_Actual,
    Daycount_Calculator_Base,
    Daycount_Convention,
    Daycount_Thirty_360,
    Daycount_Thirty_365,
    get_daycount_calculator,
)


# ==============================================================================
# Fixtures
# ==============================================================================


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
    """Return 2025-01-01 (non-leap year)."""
    return date(2025, 1, 1)


@pytest.fixture()
def date_jan1_2023() -> date:
    """Return 2023-01-01 (non-leap year)."""
    return date(2023, 1, 1)


@pytest.fixture()
def date_mar1_2024() -> date:
    """Return 2024-03-01."""
    return date(2024, 3, 1)


@pytest.fixture()
def date_feb28_2024() -> date:
    """Return 2024-02-28."""
    return date(2024, 2, 28)


@pytest.fixture()
def date_feb29_2024() -> date:
    """Return 2024-02-29 (leap day)."""
    return date(2024, 2, 29)


@pytest.fixture()
def date_apr1_2024() -> date:
    """Return 2024-04-01."""
    return date(2024, 4, 1)


@pytest.fixture()
def calc_30_360() -> Daycount_Thirty_360:
    """Return a 30/360 calculator."""
    return Daycount_Thirty_360()


@pytest.fixture()
def calc_30_365() -> Daycount_Thirty_365:
    """Return a 30/365 calculator."""
    return Daycount_Thirty_365()


@pytest.fixture()
def calc_act_360() -> Daycount_Actual_360:
    """Return an ACTUAL/360 calculator."""
    return Daycount_Actual_360()


@pytest.fixture()
def calc_act_365() -> Daycount_Actual_365:
    """Return an ACTUAL/365 calculator."""
    return Daycount_Actual_365()


@pytest.fixture()
def calc_act_act() -> Daycount_Actual_Actual:
    """Return an ACTUAL/ACTUAL calculator."""
    return Daycount_Actual_Actual()


# ==============================================================================
# Tests: Daycount_Convention Enum
# ==============================================================================


class Test_Daycount_Convention_Enum:
    """Test the Daycount_Convention enumeration."""

    @pytest.mark.unit()
    def test_all_members_exist(self):
        """Test that all members exist."""
        members = list(Daycount_Convention)
        assert len(members) == 5

    @pytest.mark.parametrize(
        ("member", "expected_value"),
        [
            (Daycount_Convention.THIRTY_360, "30/360"),
            (Daycount_Convention.THIRTY_365, "30/365"),
            (Daycount_Convention.ACTUAL_360, "ACTUAL/360"),
            (Daycount_Convention.ACTUAL_365, "ACTUAL/365"),
            (Daycount_Convention.ACTUAL_ACTUAL, "ACTUAL/ACTUAL"),
        ],
    )
    @pytest.mark.unit()
    def test_member_values(self, member, expected_value):
        """Test that member values."""
        assert member.value == expected_value

    @pytest.mark.unit()
    def test_members_are_unique(self):
        """Test that members are unique."""
        values = [m.value for m in Daycount_Convention]
        assert len(values) == len(set(values))


# ==============================================================================
# Tests: Daycount_Calculator_Base
# ==============================================================================


class Test_Daycount_Calculator_Base:
    """Test the abstract base class."""

    @pytest.mark.unit()
    def test_cannot_instantiate_abstract_class(self):
        """Test that cannot instantiate abstract class."""
        with pytest.raises(TypeError):
            Daycount_Calculator_Base(Daycount_Convention.THIRTY_360)  # type: ignore[abstract]

    @pytest.mark.unit()
    def test_convention_property(self, calc_30_360):
        """Test that convention property."""
        assert calc_30_360.convention is Daycount_Convention.THIRTY_360

    @pytest.mark.unit()
    def test_repr(self, calc_30_360):
        """Test that repr."""
        assert repr(calc_30_360) == "Daycount_Thirty_360(convention='30/360')"

    @pytest.mark.unit()
    def test_invalid_convention_type(self):
        """Test that invalid convention type."""
        calc_instance = Daycount_Thirty_360.__new__(Daycount_Thirty_360)

        with pytest.raises(Exception_Validation_Input):
            Daycount_Calculator_Base.__init__(
                calc_instance,
                convention="not_an_enum",  # type: ignore[arg-type]
            )


# ==============================================================================
# Tests: Date Validation (shared across all calculators)
# ==============================================================================


class Test_Date_Validation:
    """Test date validation logic inherited from the base class."""

    @pytest.mark.unit()
    def test_invalid_date_start_type(self, calc_30_360):
        """Test that invalid date start type."""
        with pytest.raises(Exception_Validation_Input, match="date_start"):
            calc_30_360.calc_year_fraction(date_start = "2024-01-01", date_end = date(2024, 7, 1))  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_invalid_date_end_type(self, calc_30_360, date_jan1_2024):
        """Test that invalid date end type."""
        with pytest.raises(Exception_Validation_Input, match="date_end"):
            calc_30_360.calc_year_fraction(date_start = date_jan1_2024, date_end = "2024-07-01")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_end_before_start_raises(self, calc_30_360, date_jan1_2024, date_jul1_2024):
        """Test that end before start raises."""
        with pytest.raises(Exception_Validation_Input, match="date_end must not be before"):
            calc_30_360.calc_year_fraction(date_start = date_jul1_2024, date_end = date_jan1_2024)

    @pytest.mark.unit()
    def test_same_dates_returns_zero(self, calc_30_360, date_jan1_2024):
        """Test that same dates returns zero."""
        assert calc_30_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2024) == 0.0

    @pytest.mark.parametrize(
        "calc_fixture",
        [
            "calc_30_360",
            "calc_30_365",
            "calc_act_360",
            "calc_act_365",
            "calc_act_act",
        ],
    )
    @pytest.mark.unit()
    def test_same_dates_zero_all_conventions(
        self,
        calc_fixture,
        date_jan1_2024,
        request,
    ):
        """Test that same dates zero all conventions."""
        calc = request.getfixturevalue(calc_fixture)
        assert calc.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2024) == 0.0


# ==============================================================================
# Tests: Daycount_Thirty_360
# ==============================================================================


class Test_Daycount_Thirty_360:
    """Test the 30/360 day-count calculator.

    30/360: daily interest = annual_rate / 360, accrued over 30-day months.
    Year fraction = (360*(Y2-Y1) + 30*(M2-M1) + (D2-D1)) / 360.
    """

    @pytest.mark.unit()
    def test_convention_attribute(self, calc_30_360):
        """Test that convention attribute."""
        assert calc_30_360.convention is Daycount_Convention.THIRTY_360

    @pytest.mark.unit()
    def test_half_year(self, calc_30_360, date_jan1_2024, date_jul1_2024):
        """Test that half year."""
        # 6 months → 180 / 360 = 0.5
        assert calc_30_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024) == 0.5

    @pytest.mark.unit()
    def test_full_year(self, calc_30_360, date_jan1_2024, date_jan1_2025):
        """Test that full year."""
        # 12 months → 360 / 360 = 1.0
        assert calc_30_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2025) == 1.0

    @pytest.mark.unit()
    def test_one_month(self, calc_30_360):
        """Test that one month."""
        # 1 month → 30 / 360
        result = calc_30_360.calc_year_fraction(date_start = date(2024, 1, 1), date_end = date(2024, 2, 1))
        assert result == pytest.approx(30 / 360)

    @pytest.mark.unit()
    def test_quarter(self, calc_30_360, date_jan1_2024, date_apr1_2024):
        """Test that quarter."""
        # 3 months → 90 / 360 = 0.25
        assert calc_30_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_apr1_2024) == 0.25

    @pytest.mark.unit()
    def test_day_capping_at_30(self, calc_30_360):
        """Test that day capping at 30."""
        # Both D1=31 and D2=31 → capped to 30
        result = calc_30_360.calc_year_fraction(date_start = date(2024, 1, 31), date_end = date(2024, 3, 31))
        expected = (30 * 2 + (30 - 30)) / 360  # 60 / 360
        assert result == pytest.approx(expected)

    @pytest.mark.unit()
    def test_two_years(self, calc_30_360, date_jan1_2023, date_jan1_2025):
        """Test that two years."""
        # 2 years → 720 / 360 = 2.0
        assert calc_30_360.calc_year_fraction(date_start = date_jan1_2023, date_end = date_jan1_2025) == 2.0


# ==============================================================================
# Tests: Daycount_Thirty_365
# ==============================================================================


class Test_Daycount_Thirty_365:
    """Test the 30/365 day-count calculator.

    30/365: daily interest = annual_rate / 365, accrued over 30-day months.
    Year fraction = (360*(Y2-Y1) + 30*(M2-M1) + (D2-D1)) / 365.
    """

    @pytest.mark.unit()
    def test_convention_attribute(self, calc_30_365):
        """Test that convention attribute."""
        assert calc_30_365.convention is Daycount_Convention.THIRTY_365

    @pytest.mark.unit()
    def test_half_year(self, calc_30_365, date_jan1_2024, date_jul1_2024):
        """Test that half year."""
        # 180 / 365
        assert calc_30_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024) == pytest.approx(
            180 / 365,
        )

    @pytest.mark.unit()
    def test_full_year(self, calc_30_365, date_jan1_2024, date_jan1_2025):
        """Test that full year."""
        # 360 / 365
        assert calc_30_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2025) == pytest.approx(
            360 / 365,
        )

    @pytest.mark.unit()
    def test_one_month(self, calc_30_365):
        """Test that one month."""
        result = calc_30_365.calc_year_fraction(date_start = date(2024, 1, 1), date_end = date(2024, 2, 1))
        assert result == pytest.approx(30 / 365)

    @pytest.mark.unit()
    def test_quarter(self, calc_30_365, date_jan1_2024, date_apr1_2024):
        """Test that quarter."""
        # 90 / 365
        assert calc_30_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_apr1_2024) == pytest.approx(
            90 / 365,
        )

    @pytest.mark.unit()
    def test_denominator_is_365_not_360(self, calc_30_365, date_jan1_2024, date_jul1_2024):
        """Test that denominator is 365 not 360."""
        calc_360 = Daycount_Thirty_360()
        result_365 = calc_30_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        result_360 = calc_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        # Same numerator (180), different denominator → 30/365 < 30/360
        assert result_365 < result_360


# ==============================================================================
# Tests: Daycount_Actual_360
# ==============================================================================


class Test_Daycount_Actual_360:
    """Test the ACTUAL/360 day-count calculator.

    ACTUAL/360: daily interest = annual_rate / 360, accrued over actual days.
    Year fraction = actual_days / 360.
    """

    @pytest.mark.unit()
    def test_convention_attribute(self, calc_act_360):
        """Test that convention attribute."""
        assert calc_act_360.convention is Daycount_Convention.ACTUAL_360

    @pytest.mark.unit()
    def test_half_year_leap(self, calc_act_360, date_jan1_2024, date_jul1_2024):
        """Test that half year leap."""
        # 2024 is leap: Jan(31)+Feb(29)+Mar(31)+Apr(30)+May(31)+Jun(30) = 182 days
        actual_days = (date(2024, 7, 1) - date(2024, 1, 1)).days
        assert actual_days == 182
        assert calc_act_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024) == pytest.approx(
            182 / 360,
        )

    @pytest.mark.unit()
    def test_full_year_leap(self, calc_act_360, date_jan1_2024, date_jan1_2025):
        """Test that full year leap."""
        # 2024 leap → 366 days / 360
        assert calc_act_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2025) == pytest.approx(
            366 / 360,
        )

    @pytest.mark.unit()
    def test_full_year_non_leap(self, calc_act_360, date_jan1_2023, date_jan1_2024):
        """Test that full year non leap."""
        # 2023 non-leap → 365 days / 360
        assert calc_act_360.calc_year_fraction(date_start = date_jan1_2023, date_end = date_jan1_2024) == pytest.approx(
            365 / 360,
        )

    @pytest.mark.unit()
    def test_one_day(self, calc_act_360):
        """Test that one day."""
        result = calc_act_360.calc_year_fraction(date_start = date(2024, 3, 15), date_end = date(2024, 3, 16))
        assert result == pytest.approx(1 / 360)

    @pytest.mark.unit()
    def test_90_days(self, calc_act_360):
        """Test that 90 days."""
        # 90 actual days / 360 = 0.25
        result = calc_act_360.calc_year_fraction(date_start = date(2025, 1, 1), date_end = date(2025, 4, 1))
        actual_days = (date(2025, 4, 1) - date(2025, 1, 1)).days  # 90
        assert result == pytest.approx(actual_days / 360)


# ==============================================================================
# Tests: Daycount_Actual_365
# ==============================================================================


class Test_Daycount_Actual_365:
    """Test the ACTUAL/365 day-count calculator.

    ACTUAL/365: daily interest = annual_rate / 365, accrued over actual days.
    Year fraction = actual_days / 365.
    """

    @pytest.mark.unit()
    def test_convention_attribute(self, calc_act_365):
        """Test that convention attribute."""
        assert calc_act_365.convention is Daycount_Convention.ACTUAL_365

    @pytest.mark.unit()
    def test_full_year_non_leap(self, calc_act_365, date_jan1_2023, date_jan1_2024):
        """Test that full year non leap."""
        # 365 / 365 = 1.0
        assert calc_act_365.calc_year_fraction(date_start = date_jan1_2023, date_end = date_jan1_2024) == pytest.approx(
            1.0,
        )

    @pytest.mark.unit()
    def test_full_year_leap(self, calc_act_365, date_jan1_2024, date_jan1_2025):
        """Test that full year leap."""
        # 366 / 365 > 1.0 (fixed 365 denominator)
        result = calc_act_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2025)
        assert result == pytest.approx(366 / 365)
        assert result > 1.0

    @pytest.mark.unit()
    def test_half_year_leap(self, calc_act_365, date_jan1_2024, date_jul1_2024):
        """Test that half year leap."""
        actual_days = (date(2024, 7, 1) - date(2024, 1, 1)).days  # 182
        assert calc_act_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024) == pytest.approx(
            actual_days / 365,
        )

    @pytest.mark.unit()
    def test_one_day(self, calc_act_365):
        """Test that one day."""
        result = calc_act_365.calc_year_fraction(date_start = date(2024, 6, 15), date_end = date(2024, 6, 16))
        assert result == pytest.approx(1 / 365)

    @pytest.mark.unit()
    def test_denominator_is_365_not_360(self, calc_act_365, date_jan1_2024, date_jul1_2024):
        """Test that denominator is 365 not 360."""
        calc_360 = Daycount_Actual_360()
        result_365 = calc_act_365.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        result_360 = calc_360.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        # Same numerator (182), different denominator → act/365 < act/360
        assert result_365 < result_360


# ==============================================================================
# Tests: Daycount_Actual_Actual
# ==============================================================================


class Test_Daycount_Actual_Actual:
    """Test the ACTUAL/ACTUAL day-count calculator.

    ACTUAL/ACTUAL: daily interest = annual_rate / actual_days_in_year,
    accrued over actual days.  Splits across year boundaries.
    """

    @pytest.mark.unit()
    def test_convention_attribute(self, calc_act_act):
        """Test that convention attribute."""
        assert calc_act_act.convention is Daycount_Convention.ACTUAL_ACTUAL

    @pytest.mark.unit()
    def test_full_year_leap(self, calc_act_act, date_jan1_2024, date_jan1_2025):
        """Test that full year leap."""
        # Exactly 1 leap year → 366 / 366 = 1.0
        assert calc_act_act.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2025) == 1.0

    @pytest.mark.unit()
    def test_full_year_non_leap(self, calc_act_act, date_jan1_2023, date_jan1_2024):
        """Test that full year non leap."""
        # Exactly 1 non-leap year → 365 / 365 = 1.0
        assert calc_act_act.calc_year_fraction(date_start = date_jan1_2023, date_end = date_jan1_2024) == 1.0

    @pytest.mark.unit()
    def test_two_full_years(self, calc_act_act, date_jan1_2023, date_jan1_2025):
        """Test that two full years."""
        # 2023 (365/365) + 2024 (366/366) = 2.0
        assert calc_act_act.calc_year_fraction(date_start = date_jan1_2023, date_end = date_jan1_2025) == 2.0

    @pytest.mark.unit()
    def test_half_year_leap(self, calc_act_act, date_jan1_2024, date_jul1_2024):
        """Test that half year leap."""
        # 182 days in a 366-day year → 182/366
        result = calc_act_act.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        assert result == pytest.approx(182 / 366)

    @pytest.mark.unit()
    def test_half_year_non_leap(self, calc_act_act):
        """Test that half year non leap."""
        # 2023 is not leap: Jan-Jun = 31+28+31+30+31+30 = 181 days / 365
        result = calc_act_act.calc_year_fraction(date_start = date(2023, 1, 1), date_end = date(2023, 7, 1))
        assert result == pytest.approx(181 / 365)

    @pytest.mark.unit()
    def test_cross_year_boundary(self, calc_act_act):
        """Test that cross year boundary."""
        # Oct 1 2023 → Mar 1 2024
        # 2023 portion: Oct+Nov+Dec = 31+30+31 = 92 days / 365
        # 2024 portion: Jan+Feb = 31+29 = 60 days / 366
        d_start = date(2023, 10, 1)
        d_end = date(2024, 3, 1)
        result = calc_act_act.calc_year_fraction(date_start = d_start, date_end = d_end)
        expected = 92 / 365 + 60 / 366
        assert result == pytest.approx(expected)

    @pytest.mark.unit()
    def test_same_date_returns_zero(self, calc_act_act, date_jan1_2024):
        """Test that same date returns zero."""
        assert calc_act_act.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jan1_2024) == 0.0

    @pytest.mark.unit()
    def test_one_day_leap_year(self, calc_act_act):
        """Test that one day leap year."""
        result = calc_act_act.calc_year_fraction(date_start = date(2024, 2, 28), date_end = date(2024, 2, 29))
        assert result == pytest.approx(1 / 366)

    @pytest.mark.unit()
    def test_one_day_non_leap_year(self, calc_act_act):
        """Test that one day non leap year."""
        result = calc_act_act.calc_year_fraction(date_start = date(2023, 3, 15), date_end = date(2023, 3, 16))
        assert result == pytest.approx(1 / 365)

    @pytest.mark.unit()
    def test_three_year_span(self, calc_act_act):
        """Test that three year span."""
        # 2022 (non-leap) + 2023 (non-leap) + 2024 (leap) = 3.0
        result = calc_act_act.calc_year_fraction(date_start = date(2022, 1, 1), date_end = date(2025, 1, 1))
        assert result == pytest.approx(3.0)


# ==============================================================================
# Tests: get_daycount_calculator factory
# ==============================================================================


class Test_Get_Daycount_Calculator:
    """Test the factory function."""

    @pytest.mark.parametrize(
        ("convention", "expected_cls"),
        [
            (Daycount_Convention.THIRTY_360, Daycount_Thirty_360),
            (Daycount_Convention.THIRTY_365, Daycount_Thirty_365),
            (Daycount_Convention.ACTUAL_360, Daycount_Actual_360),
            (Daycount_Convention.ACTUAL_365, Daycount_Actual_365),
            (Daycount_Convention.ACTUAL_ACTUAL, Daycount_Actual_Actual),
        ],
    )
    @pytest.mark.unit()
    def test_returns_correct_type(self, convention, expected_cls):
        """Test that returns correct type."""
        calc = get_daycount_calculator(convention = convention)
        assert isinstance(calc, expected_cls)

    @pytest.mark.parametrize(
        "convention",
        list(Daycount_Convention),
    )
    @pytest.mark.unit()
    def test_convention_matches(self, convention):
        """Test that convention matches."""
        calc = get_daycount_calculator(convention = convention)
        assert calc.convention is convention

    @pytest.mark.unit()
    def test_invalid_convention_raises(self):
        """Test that invalid convention raises."""
        with pytest.raises(Exception_Validation_Input, match="Daycount_Convention"):
            get_daycount_calculator(convention = "30/360")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_none_raises(self):
        """Test that none raises."""
        with pytest.raises(Exception_Validation_Input):
            get_daycount_calculator(convention = None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_factory_produces_working_calculator(self, date_jan1_2024, date_jul1_2024):
        """Test that factory produces working calculator."""
        calc = get_daycount_calculator(convention = Daycount_Convention.THIRTY_360)
        result = calc.calc_year_fraction(date_start = date_jan1_2024, date_end = date_jul1_2024)
        assert result == 0.5


# ==============================================================================
# Tests: Cross-convention comparisons
# ==============================================================================


class Test_Cross_Convention_Comparisons:
    """Compare results across different conventions for the same date pair."""

    @pytest.mark.unit()
    def test_full_non_leap_year_ordering(self):
        """For a full non-leap year (365 days), verify relative ordering."""
        d_start = date(2023, 1, 1)
        d_end = date(2024, 1, 1)

        results = {}
        for conv in Daycount_Convention:
            calc = get_daycount_calculator(convention = conv)
            results[conv] = calc.calc_year_fraction(date_start = d_start, date_end = d_end)

        # 30/360: 360/360 = 1.0
        assert results[Daycount_Convention.THIRTY_360] == pytest.approx(1.0)
        # 30/365: 360/365 < 1.0
        assert results[Daycount_Convention.THIRTY_365] < 1.0
        # ACT/360: 365/360 > 1.0
        assert results[Daycount_Convention.ACTUAL_360] > 1.0
        # ACT/365: 365/365 = 1.0
        assert results[Daycount_Convention.ACTUAL_365] == pytest.approx(1.0)
        # ACT/ACT: 365/365 = 1.0
        assert results[Daycount_Convention.ACTUAL_ACTUAL] == pytest.approx(1.0)

    @pytest.mark.unit()
    def test_full_leap_year_ordering(self):
        """For a full leap year (366 days), verify relative ordering."""
        d_start = date(2024, 1, 1)
        d_end = date(2025, 1, 1)

        results = {}
        for conv in Daycount_Convention:
            calc = get_daycount_calculator(convention = conv)
            results[conv] = calc.calc_year_fraction(date_start = d_start, date_end = d_end)

        # 30/360: 360/360 = 1.0
        assert results[Daycount_Convention.THIRTY_360] == pytest.approx(1.0)
        # ACT/360: 366/360 > 1.0
        assert results[Daycount_Convention.ACTUAL_360] > 1.0
        # ACT/365: 366/365 > 1.0
        assert results[Daycount_Convention.ACTUAL_365] > 1.0
        # ACT/ACT: 366/366 = 1.0
        assert results[Daycount_Convention.ACTUAL_ACTUAL] == pytest.approx(1.0)


# ==============================================================================
# Tests: Polars vectorized API (P1 additions)
# ==============================================================================


class Test_Year_Fraction_Series:
    """Tests for the polars-vectorized year_fraction_series function."""

    @pytest.mark.unit()
    def Test_Raises_Import_Error_When_Polars_Runtime_Is_Disabled(self, monkeypatch):
        """The explicit missing-polars guard should raise ImportError."""
        import polars as pl

        from src.utils.dates_times_utils import daycount as module

        starts = pl.Series([date(2025, 1, 1)], dtype=pl.Date)
        ends = pl.Series([date(2025, 7, 1)], dtype=pl.Date)
        monkeypatch.setattr(module, "_HAS_POLARS", False)

        with pytest.raises(ImportError, match="polars is required"):
            module.year_fraction_series(
                convention = Daycount_Convention.ACTUAL_365,
                dates_start = starts,
                dates_end = ends,
            )

    @pytest.mark.unit()
    def test_returns_polars_series(self):
        """year_fraction_series returns a pl.Series."""
        import polars as pl

        from src.utils.dates_times_utils.daycount import year_fraction_series

        starts = pl.Series([date(2025, 1, 1), date(2025, 7, 1)], dtype=pl.Date)
        ends   = pl.Series([date(2025, 7, 1), date(2026, 1, 1)], dtype=pl.Date)
        result = year_fraction_series(convention = Daycount_Convention.ACTUAL_365, dates_start = starts, dates_end = ends)
        assert isinstance(result, pl.Series)
        assert result.dtype == pl.Float64
        assert len(result) == 2

    @pytest.mark.unit()
    def test_values_match_scalar_calculator(self):
        """Vectorized results must match the scalar calculator for each row."""
        import polars as pl

        from src.utils.dates_times_utils.daycount import year_fraction_series

        date_pairs = [
            (date(2024, 1, 1), date(2024, 7, 1)),
            (date(2025, 3, 15), date(2025, 9, 15)),
        ]
        starts = pl.Series([p[0] for p in date_pairs], dtype=pl.Date)
        ends   = pl.Series([p[1] for p in date_pairs], dtype=pl.Date)
        result = year_fraction_series(convention = Daycount_Convention.ACTUAL_365, dates_start = starts, dates_end = ends)

        calc = get_daycount_calculator(convention = Daycount_Convention.ACTUAL_365)
        expected = [calc.calc_year_fraction(date_start = s, date_end = e) for s, e in date_pairs]
        for got, exp in zip(result.to_list(), expected, strict=False):
            assert got == pytest.approx(exp, rel=1e-9)

    @pytest.mark.unit()
    def test_length_mismatch_raises(self):
        """Mismatched series lengths raise Exception_Validation_Input."""
        import polars as pl

        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        from src.utils.dates_times_utils.daycount import year_fraction_series

        starts = pl.Series([date(2025, 1, 1)], dtype=pl.Date)
        ends   = pl.Series([date(2025, 7, 1), date(2026, 1, 1)], dtype=pl.Date)
        with pytest.raises(Exception_Validation_Input):
            year_fraction_series(convention = Daycount_Convention.ACTUAL_365, dates_start = starts, dates_end = ends)

    @pytest.mark.unit()
    def test_empty_series(self):
        """Empty input series returns empty pl.Series."""
        import polars as pl

        from src.utils.dates_times_utils.daycount import year_fraction_series

        starts = pl.Series([], dtype=pl.Date)
        ends   = pl.Series([], dtype=pl.Date)
        result = year_fraction_series(convention = Daycount_Convention.THIRTY_360, dates_start = starts, dates_end = ends)
        assert len(result) == 0

    @pytest.mark.unit()
    def test_all_conventions_vectorize(self):
        """year_fraction_series works for all five Daycount_Convention members."""
        import polars as pl

        from src.utils.dates_times_utils.daycount import year_fraction_series

        starts = pl.Series([date(2025, 1, 1)], dtype=pl.Date)
        ends   = pl.Series([date(2025, 7, 1)], dtype=pl.Date)
        for conv in Daycount_Convention:
            result = year_fraction_series(convention = conv, dates_start = starts, dates_end = ends)
            assert len(result) == 1
            assert result[0] > 0


class Test_Day_Count_Fraction:
    """Tests for the day_count_fraction convenience function."""

    @pytest.mark.unit()
    def test_string_dates(self):
        """Accepts ISO-8601 string dates."""
        from src.utils.dates_times_utils.daycount import day_count_fraction

        result = day_count_fraction(date_start = "2025-01-01", date_end = "2025-07-01", convention_str = "ACTUAL/365")
        assert result == pytest.approx(181 / 365, rel=1e-9)

    @pytest.mark.unit()
    def test_date_objects(self):
        """Accepts datetime.date objects directly."""
        from src.utils.dates_times_utils.daycount import day_count_fraction

        result = day_count_fraction(date_start = date(2025, 1, 1), date_end = date(2025, 7, 1), convention_str = "ACTUAL/365")
        assert result == pytest.approx(181 / 365, rel=1e-9)

    @pytest.mark.unit()
    def test_invalid_convention_raises(self):
        """Unknown convention string raises Exception_Validation_Input."""
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        from src.utils.dates_times_utils.daycount import day_count_fraction

        with pytest.raises(Exception_Validation_Input):
            day_count_fraction(date_start = "2025-01-01", date_end = "2025-07-01", convention_str = "BOGUS/999")
