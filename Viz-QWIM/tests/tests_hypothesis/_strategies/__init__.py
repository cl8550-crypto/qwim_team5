"""Shared Polars DataFrame hypothesis strategies for the QWIM test suite.

Re-exports all public composite strategies from ``polars_strategies`` so
callers only need one import path::

    from tests.tests_hypothesis._strategies import strategy_time_series_df

Version: 1.0.0
"""

from tests.tests_hypothesis._strategies.polars_strategies import (
    strategy_client_record_df,
    strategy_instrument_struct_df,
    strategy_monetary_decimal_series,
    strategy_returns_series,
    strategy_time_series_df,
)

__all__ = [
    "strategy_client_record_df",
    "strategy_instrument_struct_df",
    "strategy_monetary_decimal_series",
    "strategy_returns_series",
    "strategy_time_series_df",
]
