"""Shared fixtures for dashboard unit tests.

Provides sample data structures for testing Shiny dashboard modules
including data_utils, data_inputs, and reactives_shiny dictionaries.
"""

from __future__ import annotations

import polars as pl
import pytest


@pytest.fixture()
def sample_data_utils() -> dict:
    """Create sample data_utils dictionary matching get_data_utils() output."""
    return {
        "Enable_PNG_Saving_Tab_Inputs": False,
        "Select_Time_Period": "Custom",
        "Custom_Date_Range_Start": "2018-01-10",
        "Custom_Date_Range_End": "2023-03-12",
    }


@pytest.fixture()
def sample_data_inputs() -> dict:
    """Create sample data_inputs dictionary matching get_data_inputs() output."""
    return {
        "Time_Series_Sample": pl.DataFrame(
            {"Date": ["2023-01-01", "2023-02-01"], "Value": [100.0, 102.0]},
        ),
        "Time_Series_ETFs": pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01"],
                "SPY": [400.0, 410.0],
                "AGG": [100.0, 99.5],
            },
        ),
        "Weights_My_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01"],
                "SPY": [0.6, 0.6],
                "AGG": [0.4, 0.4],
            },
        ),
        "My_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                "Value": [100.0, 105.0, 103.0],
            },
        ),
        "Benchmark_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                "Value": [100.0, 103.0, 104.0],
            },
        ),
    }


@pytest.fixture()
def sample_reactives_shiny() -> dict:
    """Create sample reactives_shiny dictionary with required 4 categories."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }
