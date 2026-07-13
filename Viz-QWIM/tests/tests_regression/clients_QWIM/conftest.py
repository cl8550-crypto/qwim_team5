"""Shared fixtures for utils_client regression tests.

These fixtures create deterministic extracted_data dictionaries that
represent typical completed worksheet states.  All regression tests use
these fixtures and snapshot structured validation output as Parquet files
(no PDF byte-hashing).

Usage
-----
    # Generate baselines:
    REGENERATE_BASELINES=1 pytest tests/tests_regression/clients_QWIM/ -q

    # Assert no regression:
    pytest tests/tests_regression/clients_QWIM/ -q -m regression
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl
import pytest

from src.clients_QWIM.utils_client import (
    build_checkbox_fields_by_section,
    validate_extracted_client_data,
    validate_required_advisor_info_section,
    worksheet_has_client_partner,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASELINES_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "_baselines"
    / "clients_QWIM"
    / "utils_client"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_baseline(filename: str) -> pl.DataFrame:
    """Load a Parquet regression baseline."""
    return pl.read_parquet(BASELINES_DIR / filename)


def save_baseline(df: pl.DataFrame, filename: str) -> None:
    """Save a DataFrame as a Parquet regression baseline."""
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASELINES_DIR / filename)


def _assert_frames_approx_equal(actual: pl.DataFrame, baseline: pl.DataFrame) -> None:
    """Assert two DataFrames are equal within floating-point tolerance."""
    assert set(actual.columns) == set(baseline.columns), (
        f"Column mismatch: {actual.columns} != {baseline.columns}"
    )
    for col in actual.columns:
        if actual[col].dtype in (pl.Float32, pl.Float64):
            for a, b in zip(actual[col].to_list(), baseline[col].to_list()):
                assert abs(a - b) < 1e-9, f"Column '{col}': {a} != {b}"
        else:
            assert actual[col].to_list() == baseline[col].to_list(), (
                f"Column '{col}' mismatch"
            )


# ---------------------------------------------------------------------------
# Constants — typical single-client worksheet data
# ---------------------------------------------------------------------------

_VALID_ADVISOR_INFO: dict = {
    "name": "Jane Smith",
    "title": "CFP",
    "credentials": "CFP, CFA",
    "team": "Wealth Advisory",
    "firm": "QWIM AI Wealth Management",
    "email": "jane.smith@example.com",
    "phone_number": "212-555-1234",
    "address": "123 Main St, New York, NY",
}

_VALID_PERSONAL_INFO_PRIMARY: dict = {
    "name": "John Doe",
    "age_current": "55",
    "age_retirement": "65",
    "age_annuity_income_starting": "65",
    "status_marital": "Married",
    "gender": "Male",
    "tolerance_risk": "Moderate",
    "state": "California",
    "code_zip": "90210",
}

_VALID_ASSETS_PRIMARY: dict = {
    "assets_taxable": "250,000",
    "assets_tax_deferred": "500,000",
    "assets_tax_free": "100,000",
}

_VALID_GOALS_PRIMARY: dict = {
    "goal_essential": "60,000",
    "goal_important": "20,000",
    "goal_aspirational": "10,000",
    "growth_rate_flag": False,
    "growth_rate_same_as_inflation_flag": False,
    "growth_rate": "",
}

_VALID_INCOME_PRIMARY: dict = {
    "income_social_security": "24,000",
    "social_security_cola_indexed": True,
    "income_pension": "0",
    "income_pension_inflation_indexed": False,
    "income_annuity_existing": "0",
    "income_annuity_existing_inflation_indexed": False,
    "income_other": "0",
    "income_other_inflation_indexed": False,
}

_EMPTY_CLIENT: dict = {}


def _make_single_client_data() -> dict:
    """Return a valid single-client extracted_data dict."""
    return {
        "Header": {"date": "06/01/2026"},
        "Advisor_Info": dict(_VALID_ADVISOR_INFO),
        "Personal_Info": {
            "client_primary": dict(_VALID_PERSONAL_INFO_PRIMARY),
            "client_partner": dict(_EMPTY_CLIENT),
        },
        "Assets": {
            "client_primary": dict(_VALID_ASSETS_PRIMARY),
            "client_partner": dict(_EMPTY_CLIENT),
        },
        "Goals": {
            "client_primary": dict(_VALID_GOALS_PRIMARY),
            "client_partner": dict(_EMPTY_CLIENT),
        },
        "Income": {
            "client_primary": dict(_VALID_INCOME_PRIMARY),
            "client_partner": dict(_EMPTY_CLIENT),
        },
    }


def _make_data_with_invalid_fields() -> dict:
    """Return extracted_data with known validation failures."""
    data = _make_single_client_data()
    pi = data["Personal_Info"]["client_primary"]
    pi["status_marital"] = "Invalid_Status"
    pi["gender"] = "Robot"
    pi["age_current"] = "200"  # out of range
    return data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def valid_single_client_data() -> dict:
    """Extracted data dict for a valid single-client worksheet."""
    return _make_single_client_data()


@pytest.fixture()
def invalid_fields_data() -> dict:
    """Extracted data dict with several invalid field values."""
    return _make_data_with_invalid_fields()
