"""Pytest configuration for the unit test suite.

Provides fixtures specific to unit tests (fast, isolated, no external I/O).
Shared cross-layer fixtures live in ``tests/conftest.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_TESTS_UNIT_DIR = Path(__file__).resolve().parent
_TESTS_DIR = _TESTS_UNIT_DIR.parent
_PROJECT_ROOT = _TESTS_DIR.parent


# ---------------------------------------------------------------------------
# Minimal model-config fixtures used across unit tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def minimal_simulation_config() -> dict:
    """Return a minimal simulation configuration dict for unit tests.

    Returns
    -------
    dict
        Smallest valid configuration that exercises the simulation path
        without requiring external data or long runtimes.
    """
    return {
        "n_paths": 10,
        "n_years": 5,
        "dt": 1.0 / 12.0,
        "seed": 42,
        "model": "standard",
    }


@pytest.fixture(scope="session")
def minimal_client_dict() -> dict:
    """Return a minimal client record for unit tests.

    Returns
    -------
    dict
        Dict with only the required fields for a ``Client_QWIM``-style record.
    """
    return {
        "client_id": "TEST-0001",
        "name": "Unit Test Client",
        "age": 65,
        "retirement_age": 65,
        "portfolio_value": 1_000_000.0,
        "annual_income_needed": 60_000.0,
    }


@pytest.fixture(scope="session")
def minimal_longevity_table() -> dict[str, list[float]]:
    """Return a trivial longevity table for deterministic unit tests.

    Returns
    -------
    dict[str, list[float]]
        ``{"age": [...], "q_x": [...]}`` — 5-row stub table.
    """
    return {
        "age": [65, 70, 75, 80, 85],
        "q_x": [0.010, 0.020, 0.035, 0.060, 0.100],
    }
