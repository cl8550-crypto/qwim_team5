"""Portfolios Module.

This module contains portfolio construction, optimization, and risk management tools.

Overview
--------
The portfolios module provides the core portfolio data structures and utility
functions used throughout the QWIM framework:

- ``portfolio_QWIM`` — Core portfolio class for managing time-varying component weights.
- ``utils_portfolio`` — Utility functions for loading data, calculating portfolio
  values, creating benchmarks, and visualizing portfolio weights.

Key Components
--------------
portfolio_QWIM
    A class representing a financial portfolio with weights of components over time.
    Supports initialization from component names (equal weights) or from a Polars
    DataFrame of weights. Provides methods for adding, modifying, and validating
    weights, plus serialization support.

utils_portfolio
    Module providing functions for:
    - Loading ETF price data and portfolio weights from CSV files
    - Creating deterministic sample portfolio weights
    - Calculating portfolio value time series
    - Creating benchmark portfolio values
    - Saving portfolio data to CSV
    - Visualizing portfolio weights over time

Usage
-----
Basic usage for creating and working with portfolios:

>>> from src.portfolios.portfolio_QWIM import portfolio_QWIM
>>> from src.portfolios.utils_portfolio import get_sample_portfolio
>>>
>>> # Create a portfolio from component names (equal weights)
>>> portfolio = portfolio_QWIM(
...     name_portfolio="My Portfolio",
...     names_components=["VTI", "AGG", "VNQ"],
... )
>>> portfolio.get_num_components
3
>>>
>>> # Get a pre-configured sample portfolio with data
>>> portfolio_obj, etf_data, values = get_sample_portfolio()

See Also
--------
src.models.portfolio_optimization : Portfolio optimization models
src.models.portfolio_rebalancing : Portfolio rebalancing strategies
src.dashboard.shiny_tab_portfolios : Shiny dashboard portfolio tab

Notes
-----
All data structures in this module use Polars DataFrames exclusively.
Never use pandas — all tabular data operations must use Polars.
"""

from __future__ import annotations
