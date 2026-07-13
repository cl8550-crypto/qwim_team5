r"""
Functionalities for daycount conventions.

===============================

Day-count conventions determine how the *year fraction* $\alpha$ between
two dates is computed.  They are fundamental building blocks in
fixed-income analytics, discounting, and accrued-interest calculations.

Common daycount conventions include:

- **30/360**: calculates the daily interest using a 360-day year and then multiplies that by 30 (standardized month).
- **30/365**: calculates the daily interest using a 365-day year and then multiplies that by 30 (standardized month).
- **ACTUAL/360**: calculates the daily interest using a 360-day year and then multiplies that by the actual number of days in each time period.
- **ACTUAL/365**: calculates the daily interest using a 365-day year and then multiplies that by the actual number of days in each time period.
- **ACTUAL/ACTUAL**: calculates the daily interest using the actual number of days in the year and then multiplies that by the actual number of days in each time period.

Author
------
QWIM Team

Version
-------
0.5.1 (2026-03-01)
"""

from __future__ import annotations

import calendar

from abc import ABC, abstractmethod
import attrs
from datetime import date

from aenum import Enum  # type: ignore[misc]

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# ======================================================================
# Enumerator
# ======================================================================


class Daycount_Convention(Enum):
    """Enumeration of supported day-count conventions.

    Each member maps to a human-readable label that can be used for
    display purposes in dashboards and reports.

    Examples
    --------
    >>> Daycount_Convention.THIRTY_360.value
    '30/360'
    >>> Daycount_Convention.ACTUAL_ACTUAL.value
    'ACTUAL/ACTUAL'
    """

    THIRTY_360 = "30/360"
    THIRTY_365 = "30/365"
    ACTUAL_360 = "ACTUAL/360"
    ACTUAL_365 = "ACTUAL/365"
    ACTUAL_ACTUAL = "ACTUAL/ACTUAL"


# ======================================================================
# Base class
# ======================================================================


@attrs.define(kw_only=True)
class Daycount_Calculator_Base(ABC):
    r"""Abstract base class for day-count calculators.

    Every concrete calculator must implement :meth:`calc_year_fraction`
    which returns the year fraction $\alpha$ between two dates.

    Attributes
    ----------
    convention : Daycount_Convention
        The day-count convention used by this calculator.
    """

    convention: Daycount_Convention = attrs.field()

    def __attrs_post_init__(self) -> None:
        """Validate and log after attrs initialization.

        Raises
        ------
        Exception_Validation_Input
            If ``convention`` is not a ``Daycount_Convention`` member.
        """
        if not isinstance(self.convention, Daycount_Convention):
            raise Exception_Validation_Input(
                "convention must be a Daycount_Convention enum member",
                field_name="convention",
                expected_type=Daycount_Convention,
                actual_value=self.convention,
            )

        _logger.info(
            "Created day-count calculator (convention: %s)",
            self.convention.value,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def convention_prop(self) -> Daycount_Convention:
        """Return the day-count convention used by this calculator."""
        return self.convention

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction between two dates.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha \ge 0$.

        Raises
        ------
        Exception_Validation_Input
            If ``date_start`` or ``date_end`` is not a ``date`` instance.
            If ``date_end`` is before ``date_start``.
        """

    # ------------------------------------------------------------------
    # Concrete helpers
    # ------------------------------------------------------------------

    def _validate_dates(
        self, *, date_start: date, date_end: date) -> None:
        """Validate that inputs are ``date`` objects and properly ordered.

        Parameters
        ----------
        date_start : date
            The start date.
        date_end : date
            The end date.

        Raises
        ------
        Exception_Validation_Input
            If either argument is not a ``date`` instance or if
            ``date_end`` is before ``date_start``.
        """
        if not isinstance(date_start, date):
            raise Exception_Validation_Input(
                "date_start must be a datetime.date instance",
                field_name="date_start",
                expected_type=date,
                actual_value=date_start,
            )

        if not isinstance(date_end, date):
            raise Exception_Validation_Input(
                "date_end must be a datetime.date instance",
                field_name="date_end",
                expected_type=date,
                actual_value=date_end,
            )

        if date_end < date_start:
            raise Exception_Validation_Input(
                "date_end must not be before date_start",
                field_name="date_end",
                expected_type=date,
                actual_value=f"date_start={date_start}, date_end={date_end}",
            )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return a developer-oriented string representation."""
        return f"{self.__class__.__name__}(convention='{self.convention.value}')"


# ======================================================================
# Concrete implementations
# ======================================================================


@attrs.define(kw_only=True, repr=False)
class Daycount_Thirty_360(Daycount_Calculator_Base):
    r"""Day-count calculator using the **30/360** convention.

    Every month is assumed to have 30 days and every year 360 days.
    The day-count numerator between two dates
    $(Y_1, M_1, D_1)$ and $(Y_2, M_2, D_2)$ is:

    $$
    \text{days} = 360 \times (Y_2 - Y_1) + 30 \times (M_2 - M_1)
                  + (D_2 - D_1)
    $$

    with the standard adjustment: $D_1$ and $D_2$ are capped at 30.

    The year fraction is then $\alpha = \text{days} / 360$.
    """

    def __init__(self) -> None:
        """Initialize the 30/360 day-count calculator."""
        super().__init__(convention=Daycount_Convention.THIRTY_360)

    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction using the 30/360 convention.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha$.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid (see base class).

        Examples
        --------
        >>> from datetime import date
        >>> calc = Daycount_Thirty_360()
        >>> calc.calc_year_fraction(date(2024, 1, 1), date(2024, 7, 1))
        0.5
        """
        self._validate_dates(date_start = date_start, date_end = date_end)

        d1 = min(date_start.day, 30)
        d2 = min(date_end.day, 30) if d1 == 30 else date_end.day
        d2 = min(d2, 30)

        days = (
            360 * (date_end.year - date_start.year)
            + 30 * (date_end.month - date_start.month)
            + (d2 - d1)
        )

        return days / 360.0


@attrs.define(kw_only=True, repr=False)
class Daycount_Thirty_365(Daycount_Calculator_Base):
    r"""Day-count calculator using the **30/365** convention.

    Every month is assumed to have 30 days and the year has 365 days.
    The day-count numerator is computed the same way as 30/360 but the
    denominator is 365:

    $$
    \alpha = \frac{360 (Y_2 - Y_1) + 30 (M_2 - M_1) + (D_2 - D_1)}{365}
    $$
    """

    def __init__(self) -> None:
        """Initialize the 30/365 day-count calculator."""
        super().__init__(convention=Daycount_Convention.THIRTY_365)

    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction using the 30/365 convention.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha$.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid (see base class).

        Examples
        --------
        >>> from datetime import date
        >>> calc = Daycount_Thirty_365()
        >>> round(calc.calc_year_fraction(date(2024, 1, 1), date(2024, 7, 1)), 6)
        0.493151
        """
        self._validate_dates(date_start = date_start, date_end = date_end)

        d1 = min(date_start.day, 30)
        d2 = min(date_end.day, 30) if d1 == 30 else date_end.day
        d2 = min(d2, 30)

        days = (
            360 * (date_end.year - date_start.year)
            + 30 * (date_end.month - date_start.month)
            + (d2 - d1)
        )

        return days / 365.0


@attrs.define(kw_only=True, repr=False)
class Daycount_Actual_360(Daycount_Calculator_Base):
    r"""Day-count calculator using the **ACTUAL/360** convention.

    Uses the actual number of calendar days elapsed as the numerator
    and 360 as the denominator:

    $$
    \alpha = \frac{\text{actual days}}{360}
    $$

    This convention is common in money-market instruments.
    """

    def __init__(self) -> None:
        """Initialize the ACTUAL/360 day-count calculator."""
        super().__init__(convention=Daycount_Convention.ACTUAL_360)

    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction using the ACTUAL/360 convention.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha$.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid (see base class).

        Examples
        --------
        >>> from datetime import date
        >>> calc = Daycount_Actual_360()
        >>> round(calc.calc_year_fraction(date(2024, 1, 1), date(2024, 7, 1)), 6)
        0.505556
        """
        self._validate_dates(date_start = date_start, date_end = date_end)

        actual_days = (date_end - date_start).days

        return actual_days / 360.0


@attrs.define(kw_only=True, repr=False)
class Daycount_Actual_365(Daycount_Calculator_Base):
    r"""Day-count calculator using the **ACTUAL/365** convention.

    Uses the actual number of calendar days elapsed as the numerator
    and a fixed 365 as the denominator (ignoring leap years):

    $$
    \alpha = \frac{\text{actual days}}{365}
    $$

    This convention is also known as **ACTUAL/365 Fixed**.
    """

    def __init__(self) -> None:
        """Initialize the ACTUAL/365 day-count calculator."""
        super().__init__(convention=Daycount_Convention.ACTUAL_365)

    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction using the ACTUAL/365 convention.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha$.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid (see base class).

        Examples
        --------
        >>> from datetime import date
        >>> calc = Daycount_Actual_365()
        >>> calc.calc_year_fraction(date(2024, 1, 1), date(2025, 1, 1))
        1.0027397260273974
        """
        self._validate_dates(date_start = date_start, date_end = date_end)

        actual_days = (date_end - date_start).days

        return actual_days / 365.0


@attrs.define(kw_only=True, repr=False)
class Daycount_Actual_Actual(Daycount_Calculator_Base):
    r"""Day-count calculator using the **ACTUAL/ACTUAL** convention.

    Uses the actual number of calendar days elapsed as the numerator
    and the actual number of days in each year as the denominator.
    When the period spans multiple years, each year's contribution is
    computed separately:

    $$
    \alpha = \sum_{y} \frac{\text{days in year } y}
                           {\text{total days in year } y}
    $$

    where the total days in year $y$ is 366 for a leap year and 365
    otherwise.  This is the **ISDA** variant of the ACTUAL/ACTUAL
    convention.
    """

    def __init__(self) -> None:
        """Initialize the ACTUAL/ACTUAL day-count calculator."""
        super().__init__(convention=Daycount_Convention.ACTUAL_ACTUAL)

    def calc_year_fraction(
        self, *, date_start: date, date_end: date) -> float:
        r"""Calculate the year fraction using the ACTUAL/ACTUAL convention.

        Parameters
        ----------
        date_start : date
            The start date of the period (inclusive).
        date_end : date
            The end date of the period (exclusive).

        Returns
        -------
        float
            The year fraction $\alpha$.

        Raises
        ------
        Exception_Validation_Input
            If inputs are invalid (see base class).

        Examples
        --------
        >>> from datetime import date
        >>> calc = Daycount_Actual_Actual()
        >>> calc.calc_year_fraction(date(2024, 1, 1), date(2025, 1, 1))
        1.0
        """
        self._validate_dates(date_start = date_start, date_end = date_end)

        if date_start == date_end:
            return 0.0

        year_fraction = 0.0
        current = date_start

        for year in range(date_start.year, date_end.year + 1):
            year_start = max(current, date(year, 1, 1))
            year_end = min(date_end, date(year + 1, 1, 1))

            if year_start >= year_end:
                continue

            days_in_year = 366 if calendar.isleap(year) else 365
            days_in_period = (year_end - year_start).days

            year_fraction += days_in_period / days_in_year

        return year_fraction


# ======================================================================
# Factory function
# ======================================================================


def get_daycount_calculator(
    *, convention: Daycount_Convention) -> Daycount_Calculator_Base:
    """Return a day-count calculator for the given convention.

    This is the recommended way to obtain calculator instances.

    Parameters
    ----------
    convention : Daycount_Convention
        The desired day-count convention.

    Returns
    -------
    Daycount_Calculator_Base
        A concrete calculator implementing the requested convention.

    Raises
    ------
    Exception_Validation_Input
        If ``convention`` is not a valid ``Daycount_Convention`` member.

    Examples
    --------
    >>> from datetime import date
    >>> calc = get_daycount_calculator(Daycount_Convention.ACTUAL_365)
    >>> round(calc.calc_year_fraction(date(2024, 1, 1), date(2024, 4, 1)), 6)
    0.249315
    """
    if not isinstance(convention, Daycount_Convention):
        raise Exception_Validation_Input(
            "convention must be a Daycount_Convention enum member",
            field_name="convention",
            expected_type=Daycount_Convention,
            actual_value=convention,
        )

    if convention is Daycount_Convention.THIRTY_360:
        return Daycount_Thirty_360()
    if convention is Daycount_Convention.THIRTY_365:
        return Daycount_Thirty_365()
    if convention is Daycount_Convention.ACTUAL_360:
        return Daycount_Actual_360()
    if convention is Daycount_Convention.ACTUAL_365:
        return Daycount_Actual_365()

    return Daycount_Actual_Actual()


# ======================================================================
# Polars-vectorized API
# ======================================================================

import os as _os  # noqa: E402 — kept local to this section  # noqa: PLC0415


try:
    import polars as pl

    _HAS_POLARS = True
except ImportError:  # pragma: no cover
    _HAS_POLARS = False


def year_fraction_series(
    *, convention: Daycount_Convention, dates_start: pl.Series, dates_end: pl.Series) -> pl.Series:
    r"""Compute year fractions for two parallel date ``pl.Series``.

    This is the vectorized counterpart to :meth:`Daycount_Calculator_Base.calc_year_fraction`
    for bulk fixed-income / discounting calculations.

    The implementation uses ``pl.Series.map_elements`` to call the scalar
    calculator for each row.  When the environment variable
    ``QWIM_USE_NUMBA=1`` is set **and** ``numba`` is installed, a
    JIT-compiled scalar kernel is used instead, reducing Python overhead
    for large series (> 10 000 rows).

    Parameters
    ----------
    convention : Daycount_Convention
        The desired day-count convention.
    dates_start : pl.Series
        Series of start dates (``pl.Date`` dtype).
    dates_end : pl.Series
        Series of end dates (``pl.Date`` dtype).

    Returns
    -------
    pl.Series
        ``Float64`` series of year fractions.  Length equals ``len(dates_start)``.

    Raises
    ------
    ImportError
        If ``polars`` is not installed.
    Exception_Validation_Input
        If either Series is not of ``pl.Date`` dtype, or if the series
        have different lengths.

    Examples
    --------
    >>> import polars as pl
    >>> starts = pl.Series([date(2025, 1, 1), date(2025, 7, 1)])
    >>> ends = pl.Series([date(2025, 7, 1), date(2026, 1, 1)])
    >>> fracs = year_fraction_series(Daycount_Convention.ACTUAL_365, starts, ends)
    >>> fracs.dtype
    Float64
    >>> len(fracs)
    2
    """
    if not _HAS_POLARS:
        msg = "polars is required for year_fraction_series"
        raise ImportError(msg)

    if len(dates_start) != len(dates_end):
        raise Exception_Validation_Input(
            "dates_start and dates_end must have the same length",
            field_name="dates_end",
            expected_type=int,
            actual_value=len(dates_end),
        )

    calc = get_daycount_calculator(convention = convention)

    # ---- Optional numba fast path ----
    _use_numba = _os.environ.get("QWIM_USE_NUMBA", "0") == "1"
    if _use_numba:  # pragma: no cover  # reason: numba optional JIT runtime, not installed in CI
        try:
            from datetime import date as _date  # noqa: PLC0415

            import numba as _nb  # noqa: PLC0415

            @_nb.njit(cache=True)  # type: ignore[misc]
            def _days_between(*, y1: int, m1: int, d1: int, y2: int, m2: int, d2: int) -> int:
                """Compute exact number of days between two dates (numba kernel)."""

                # Gauss / Zeller ordinal day formula
                def _to_ordinal(*, y: int, m: int, d: int) -> int:
                    if m <= 2:
                        y -= 1
                        m += 12
                    a = y // 100
                    b = 2 - a + a // 4
                    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524

                return _to_ordinal(y = y2, m = m2, d = d2) - _to_ordinal(y = y1, m = m1, d = d1)

            # Use polars struct extraction for zero-copy date decomposition
            struct_start = dates_start.dt.to_string("%Y-%m-%d")  # type: ignore[attr-defined]
            struct_end = dates_end.dt.to_string("%Y-%m-%d")  # type: ignore[attr-defined]

            def _scalar(*, s: str, e: str) -> float:
                y1, m1, d1 = int(s[:4]), int(s[5:7]), int(s[8:10])
                y2, m2, d2 = int(e[:4]), int(e[5:7]), int(e[8:10])
                if convention == Daycount_Convention.ACTUAL_360:
                    return _days_between(y1 = y1, m1 = m1, d1 = d1, y2 = y2, m2 = m2, d2 = d2) / 360.0
                if convention == Daycount_Convention.ACTUAL_365:
                    return _days_between(y1 = y1, m1 = m1, d1 = d1, y2 = y2, m2 = m2, d2 = d2) / 365.0
                # Fallback for non-numba-friendly conventions
                return calc.calc_year_fraction(
                    date_start = _date(y1, m1, d1),
                    date_end = _date(y2, m2, d2),
                )

            return pl.Series(
                name="year_fraction",
                values=[
                    _scalar(s = s, e = e)
                    for s, e in zip(struct_start.to_list(), struct_end.to_list(), strict=False)
                ],
                dtype=pl.Float64,
            )
        except ImportError:
            pass  # numba not available — fall through to map_elements

    # ---- Default: polars map_elements ----
    from datetime import date as _date  # noqa: PLC0415

    paired = pl.DataFrame({"s": dates_start, "e": dates_end})
    return (
        paired.select(
            pl.struct(["s", "e"]).map_elements(
                lambda row: calc.calc_year_fraction(date_start = row["s"], date_end = row["e"]),
                return_dtype=pl.Float64,
            ),
        )
        .to_series()
        .alias("year_fraction")
    )


def day_count_fraction(
    *, date_start: str | object, date_end: str | object, convention_str: str) -> float:
    """Compute a single year fraction from string dates.

    Parses ISO-8601 strings and delegates to the appropriate concrete
    :class:`Daycount_Calculator_Base` implementation.

    Parameters
    ----------
    date_start : str or date
        Start date — either an ISO-8601 string (``"YYYY-MM-DD"``) or a
        ``datetime.date`` object.
    date_end : str or date
        End date — either an ISO-8601 string or a ``datetime.date`` object.
    convention_str : str
        One of the ``Daycount_Convention`` *values*: ``"30/360"``,
        ``"30/365"``, ``"ACTUAL/360"``, ``"ACTUAL/365"``,
        ``"ACTUAL/ACTUAL"``.

    Returns
    -------
    float
        The year fraction between the two dates under the given convention.

    Raises
    ------
    Exception_Validation_Input
        If the convention string is not recognised.

    Examples
    --------
    >>> day_count_fraction("2025-01-01", "2025-07-01", "ACTUAL/365")
    0.4986301369863014
    """
    from datetime import date as _date  # noqa: PLC0415

    d_start = (
        _date.fromisoformat(str(date_start)) if not isinstance(date_start, _date) else date_start
    )
    d_end = _date.fromisoformat(str(date_end)) if not isinstance(date_end, _date) else date_end

    # Map human-readable string to enum member value
    try:
        conv = Daycount_Convention(convention_str)
    except ValueError:
        raise Exception_Validation_Input(
            f"Unknown day-count convention: {convention_str!r}. "
            f"Valid values: {[c.value for c in Daycount_Convention]}",
            field_name="convention_str",
            expected_type=str,
            actual_value=convention_str,
        ) from None

    return get_daycount_calculator(convention = conv).calc_year_fraction(date_start = d_start, date_end = d_end)
