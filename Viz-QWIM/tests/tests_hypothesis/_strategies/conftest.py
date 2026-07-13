"""Pytest conftest for ``tests/tests_hypothesis/_strategies``.

Exposes each Polars strategy as a pytest fixture so individual test modules
can request strategies by name rather than importing directly.

Fixtures
--------
time_series_df_strategy
    Returns the ``strategy_time_series_df`` composite strategy.
client_record_df_strategy
    Returns the ``strategy_client_record_df`` composite strategy.
instrument_struct_df_strategy
    Returns the ``strategy_instrument_struct_df`` composite strategy.
monetary_decimal_series_strategy
    Returns the ``strategy_monetary_decimal_series`` composite strategy.
returns_series_strategy
    Returns the ``strategy_returns_series`` composite strategy.

Version: 1.0.0
"""

from __future__ import annotations

import pytest

from tests.tests_hypothesis._strategies.polars_strategies import (
    strategy_client_record_df,
    strategy_instrument_struct_df,
    strategy_monetary_decimal_series,
    strategy_returns_series,
    strategy_time_series_df,
)


@pytest.fixture(scope="session")
def time_series_df_strategy():
    """Return the ``strategy_time_series_df`` composite strategy."""
    return strategy_time_series_df


@pytest.fixture(scope="session")
def client_record_df_strategy():
    """Return the ``strategy_client_record_df`` composite strategy."""
    return strategy_client_record_df


@pytest.fixture(scope="session")
def instrument_struct_df_strategy():
    """Return the ``strategy_instrument_struct_df`` composite strategy."""
    return strategy_instrument_struct_df


@pytest.fixture(scope="session")
def monetary_decimal_series_strategy():
    """Return the ``strategy_monetary_decimal_series`` composite strategy."""
    return strategy_monetary_decimal_series


@pytest.fixture(scope="session")
def returns_series_strategy():
    """Return the ``strategy_returns_series`` composite strategy."""
    return strategy_returns_series
