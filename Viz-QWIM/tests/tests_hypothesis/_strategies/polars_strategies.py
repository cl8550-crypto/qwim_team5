"""Shared Polars DataFrame hypothesis strategies for the QWIM test suite.

All strategies in this module produce Polars DataFrames (or Series) that
satisfy the project-wide data-structure conventions documented in
``coding-instructions-python.md``:

- ``Date`` column first, typed ``pl.Date``, sorted ascending.
- Column names in ``Title_Case``.
- Narrow integer types (``UInt8``, ``UInt16``) for non-negative bounded fields.
- ``pl.Float64`` for portfolio values, returns, prices.
- ``pl.Decimal`` for monetary amounts requiring exact arithmetic.
- ``pl.Enum`` for categorical fields with a fixed value set.
- ``pl.Struct`` for heterogeneous, schema-fixed nested properties.
- Explicit null handling — never silently propagate.

Functions
---------
strategy_time_series_df
    Polars DataFrame with a sorted ``Date`` column and one or more
    ``Float64`` value columns.
strategy_client_record_df
    Polars DataFrame with one row per synthetic client matching the
    ``Client_QWIM`` personal-info schema.
strategy_instrument_struct_df
    Polars DataFrame of financial instruments with a ``Struct`` properties
    column (nullable ``coupon``, ``strike``, ``rate``, ``maturity``).
strategy_monetary_decimal_series
    Polars ``Series`` of ``Decimal`` monetary amounts.
strategy_returns_series
    Polars ``Series`` of ``Float64`` returns with controlled null density.

Version: 1.0.0
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from hypothesis import strategies as st
from hypothesis.strategies import composite, SearchStrategy


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MARITAL_STATUS_VALUES: list[str] = [
    "Single",
    "Married",
    "Divorced",
    "Widowed",
    "Domestic Partnership",
]

_EMPLOYMENT_STATUS_VALUES: list[str] = [
    "Employed",
    "Unemployed",
    "Self-employed",
    "Retired",
    "Student",
]

_CLIENT_TYPE_VALUES: list[str] = [
    "Client Primary",
    "Client Partner",
]

_RISK_PROFILE_VALUES: list[str] = [
    "Conservative",
    "Moderate Conservative",
    "Moderate",
    "Moderate Aggressive",
    "Aggressive",
]

_INSTRUMENT_TYPES: list[str] = [
    "Bond",
    "Option",
    "Swap",
    "Equity",
    "ETF",
]


# ---------------------------------------------------------------------------
# Public composite strategies
# ---------------------------------------------------------------------------


@composite
def strategy_time_series_df(
    draw: st.DrawFn,
    min_rows: int = 2,
    max_rows: int = 120,
    value_columns: list[str] | None = None,
    null_density: float = 0.0,
) -> pl.DataFrame:
    """Generate a Polars time-series DataFrame matching project conventions.

    The returned DataFrame always has:

    - ``Date`` as the first column (``pl.Date``), sorted ascending with no
      duplicate dates.
    - One or more ``Float64`` value columns with ``Title_Case`` names.
    - Optionally, a controlled fraction of null values in each value column.

    Parameters
    ----------
    draw : st.DrawFn
        Hypothesis draw function (injected by ``@composite``).
    min_rows : int
        Minimum number of rows.  Defaults to ``2``.
    max_rows : int
        Maximum number of rows.  Defaults to ``120``.
    value_columns : list[str] or None
        Column names for value columns.  Defaults to
        ``["Portfolio_Value"]`` when ``None``.
    null_density : float
        Fraction of values to replace with ``null`` (0.0 = no nulls).
        Defaults to ``0.0``.

    Returns
    -------
    pl.DataFrame
        Time-series DataFrame sorted by ``Date`` with the requested schema.
    """
    if value_columns is None:
        value_columns = ["Portfolio_Value"]

    n_rows: int = draw(st.integers(min_value=min_rows, max_value=max_rows))

    # Generate n_rows unique calendar dates starting from a random origin.
    start_offset: int = draw(st.integers(min_value=0, max_value=365 * 10))
    origin = date(2015, 1, 1) + timedelta(days=start_offset)
    step_days: list[int] = draw(
        st.lists(
            st.integers(min_value=1, max_value=7),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )
    dates: list[date] = []
    current = origin
    for item_step in step_days:
        dates.append(current)
        current = current + timedelta(days=item_step)

    data: dict[str, list] = {"Date": dates}

    for item_col in value_columns:
        raw_values: list[float] = draw(
            st.lists(
                st.floats(
                    min_value=-1e6,
                    max_value=1e6,
                    allow_nan=False,
                    allow_infinity=False,
                ),
                min_size=n_rows,
                max_size=n_rows,
            ),
        )
        if null_density > 0.0:
            null_mask: list[bool] = draw(
                st.lists(
                    st.booleans(),
                    min_size=n_rows,
                    max_size=n_rows,
                ),
            )
            raw_values = [
                (None if item_mask and draw(st.floats(0.0, 1.0)) < null_density else item_val)
                for item_val, item_mask in zip(raw_values, null_mask)
            ]
        data[item_col] = raw_values

    return pl.DataFrame(data).sort("Date")


@composite
def strategy_client_record_df(
    draw: st.DrawFn,
    min_rows: int = 1,
    max_rows: int = 20,
) -> pl.DataFrame:
    """Generate a synthetic client-record Polars DataFrame.

    Each row represents one client.  Schema mirrors the ``Client_QWIM``
    personal-info structure with appropriate Polars types:

    - ``Client_ID`` — ``pl.String``
    - ``Current_Age`` — ``pl.UInt8`` (0–255, non-negative)
    - ``Retirement_Age`` — ``pl.UInt8`` (≥ current age)
    - ``Marital_Status`` — ``pl.Categorical``
    - ``Employment_Status`` — ``pl.Categorical``
    - ``Client_Type`` — ``pl.Categorical``
    - ``Risk_Profile`` — ``pl.Categorical``
    - ``Total_Assets`` — ``pl.Float64``

    Parameters
    ----------
    draw : st.DrawFn
        Hypothesis draw function (injected by ``@composite``).
    min_rows : int
        Minimum number of client rows.  Defaults to ``1``.
    max_rows : int
        Maximum number of client rows.  Defaults to ``20``.

    Returns
    -------
    pl.DataFrame
        Client-record DataFrame with the schema above.
    """
    n_rows: int = draw(st.integers(min_value=min_rows, max_value=max_rows))

    client_ids: list[str] = [f"CLIENT_{idx_row:06d}" for idx_row in range(n_rows)]

    current_ages: list[int] = draw(
        st.lists(
            st.integers(min_value=18, max_value=90),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    retirement_ages: list[int] = [
        draw(st.integers(min_value=item_age, max_value=min(item_age + 50, 100)))
        for item_age in current_ages
    ]

    marital_statuses: list[str] = draw(
        st.lists(
            st.sampled_from(_MARITAL_STATUS_VALUES),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    employment_statuses: list[str] = draw(
        st.lists(
            st.sampled_from(_EMPLOYMENT_STATUS_VALUES),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    client_types: list[str] = draw(
        st.lists(
            st.sampled_from(_CLIENT_TYPE_VALUES),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    risk_profiles: list[str] = draw(
        st.lists(
            st.sampled_from(_RISK_PROFILE_VALUES),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    total_assets: list[float] = draw(
        st.lists(
            st.floats(min_value=0.0, max_value=1e8, allow_nan=False, allow_infinity=False),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    return pl.DataFrame(
        {
            "Client_ID": pl.Series(client_ids, dtype=pl.String),
            "Current_Age": pl.Series(current_ages, dtype=pl.UInt8),
            "Retirement_Age": pl.Series(retirement_ages, dtype=pl.UInt8),
            "Marital_Status": pl.Series(marital_statuses, dtype=pl.Categorical),
            "Employment_Status": pl.Series(employment_statuses, dtype=pl.Categorical),
            "Client_Type": pl.Series(client_types, dtype=pl.Categorical),
            "Risk_Profile": pl.Series(risk_profiles, dtype=pl.Categorical),
            "Total_Assets": pl.Series(total_assets, dtype=pl.Float64),
        },
    )


@composite
def strategy_instrument_struct_df(
    draw: st.DrawFn,
    min_rows: int = 1,
    max_rows: int = 20,
) -> pl.DataFrame:
    """Generate a financial instrument Polars DataFrame with a Struct column.

    The ``properties`` column is a ``Struct`` with four nullable ``Float64``
    fields — ``coupon``, ``strike``, ``rate``, ``maturity`` — keeping all
    data within the Arrow memory format (no Python dicts at computation time).

    Parameters
    ----------
    draw : st.DrawFn
        Hypothesis draw function (injected by ``@composite``).
    min_rows : int
        Minimum number of instrument rows.  Defaults to ``1``.
    max_rows : int
        Maximum number of instrument rows.  Defaults to ``20``.

    Returns
    -------
    pl.DataFrame
        Instrument DataFrame with ``instrument_id``, ``instrument_type``,
        and ``properties`` (Struct) columns.
    """
    n_rows: int = draw(st.integers(min_value=min_rows, max_value=max_rows))

    instrument_ids: list[str] = [f"INSTR_{idx_row:04d}" for idx_row in range(n_rows)]

    instrument_types: list[str] = draw(
        st.lists(
            st.sampled_from(_INSTRUMENT_TYPES),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    _float_or_none: SearchStrategy = st.one_of(
        st.none(),
        st.floats(min_value=0.0, max_value=1e4, allow_nan=False, allow_infinity=False),
    )

    coupons: list[float | None] = draw(st.lists(_float_or_none, min_size=n_rows, max_size=n_rows))
    strikes: list[float | None] = draw(st.lists(_float_or_none, min_size=n_rows, max_size=n_rows))
    rates: list[float | None] = draw(st.lists(_float_or_none, min_size=n_rows, max_size=n_rows))
    maturities: list[float | None] = draw(
        st.lists(_float_or_none, min_size=n_rows, max_size=n_rows),
    )

    properties_series = pl.Series(
        "properties",
        [
            {
                "coupon": item_c,
                "strike": item_s,
                "rate": item_r,
                "maturity": item_m,
            }
            for item_c, item_s, item_r, item_m in zip(coupons, strikes, rates, maturities)
        ],
    )

    return pl.DataFrame(
        {
            "instrument_id": pl.Series(instrument_ids, dtype=pl.String),
            "instrument_type": pl.Series(instrument_types, dtype=pl.Categorical),
            "properties": properties_series,
        },
    )


@composite
def strategy_monetary_decimal_series(
    draw: st.DrawFn,
    min_rows: int = 1,
    max_rows: int = 50,
    precision: int = 12,
    scale: int = 2,
    min_value: float = 0.0,
    max_value: float = 1_000_000.0,
) -> pl.Series:
    """Generate a Polars ``Decimal`` Series for monetary amounts.

    Uses Python ``decimal.Decimal`` values to avoid floating-point rounding
    errors in financial calculations.

    Parameters
    ----------
    draw : st.DrawFn
        Hypothesis draw function (injected by ``@composite``).
    min_rows : int
        Minimum number of values.  Defaults to ``1``.
    max_rows : int
        Maximum number of values.  Defaults to ``50``.
    precision : int
        Decimal precision (total significant digits).  Defaults to ``12``.
    scale : int
        Decimal scale (digits after the decimal point).  Defaults to ``2``.
    min_value : float
        Minimum monetary value (inclusive).  Defaults to ``0.0``.
    max_value : float
        Maximum monetary value (inclusive).  Defaults to ``1_000_000.0``.

    Returns
    -------
    pl.Series
        A Polars ``Decimal`` series with the requested precision and scale.
    """
    from decimal import Decimal, ROUND_HALF_UP

    n_rows: int = draw(st.integers(min_value=min_rows, max_value=max_rows))

    raw_values: list[float] = draw(
        st.lists(
            st.floats(
                min_value=min_value,
                max_value=max_value,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    quantize_str = "0." + "0" * scale
    decimal_values = [
        Decimal(str(item_v)).quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        for item_v in raw_values
    ]

    return pl.Series(
        "Amount",
        decimal_values,
        dtype=pl.Decimal(precision=precision, scale=scale),
    )


@composite
def strategy_returns_series(
    draw: st.DrawFn,
    min_rows: int = 5,
    max_rows: int = 252,
    null_density: float = 0.0,
    name: str = "Returns",
) -> pl.Series:
    """Generate a Polars ``Float64`` returns Series with optional nulls.

    Returns are bounded to the range ``(-1.0, +10.0)`` to avoid
    numerically degenerate values (total loss or astronomical gains) in
    statistical property tests.

    Parameters
    ----------
    draw : st.DrawFn
        Hypothesis draw function (injected by ``@composite``).
    min_rows : int
        Minimum number of return observations.  Defaults to ``5``.
    max_rows : int
        Maximum number of return observations.  Defaults to ``252``.
    null_density : float
        Fraction of values to replace with ``null`` (0.0 = no nulls,
        1.0 = all nulls).  Defaults to ``0.0``.
    name : str
        Series name.  Defaults to ``"Returns"``.

    Returns
    -------
    pl.Series
        A ``Float64`` Polars Series of return values.
    """
    n_rows: int = draw(st.integers(min_value=min_rows, max_value=max_rows))

    raw_values: list[float | None] = draw(
        st.lists(
            st.one_of(
                st.floats(
                    min_value=-0.999,
                    max_value=10.0,
                    allow_nan=False,
                    allow_infinity=False,
                ),
                st.none() if null_density > 0.0 else st.floats(
                    min_value=-0.999,
                    max_value=10.0,
                    allow_nan=False,
                    allow_infinity=False,
                ),
            ),
            min_size=n_rows,
            max_size=n_rows,
        ),
    )

    if null_density == 0.0:
        raw_values = [item_v if item_v is not None else 0.0 for item_v in raw_values]

    return pl.Series(name, raw_values, dtype=pl.Float64)
