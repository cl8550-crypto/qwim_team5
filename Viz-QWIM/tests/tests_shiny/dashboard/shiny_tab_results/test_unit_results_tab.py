"""Unit tests for the Results tab pure-logic helpers.

These tests exercise constants, validators, and callable checks from
``subtab_simulation`` and ``subtab_reporting`` — no browser, no Shiny
server, no Playwright dependency.

File location: tests/tests_shiny/dashboard/shiny_tab_results/test_unit_results_tab.py
Mirrors source:  src/dashboard/shiny_tab_results/subtab_simulation.py
                 src/dashboard/shiny_tab_results/subtab_reporting.py

Notes
-----
These classes were split out of ``test_shiny_results_tab.py`` so that
they continue to run even when the Playwright browser-test file is
excluded via ``--ignore`` in ``pyproject.toml`` addopts.
"""

from __future__ import annotations

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


# ===========================================================================
# Pure-logic tests — no browser required
# ===========================================================================


@pytest.mark.unit
class Test_Simulation_Pure_Logic:
    """Pure-Python logic tests for subtab_simulation constants and helpers.

    These run without playwright and without a Shiny server.
    """

    def test_all_etf_symbols_has_12_entries(self) -> None:
        """ALL_ETF_SYMBOLS contains exactly 12 ETF tickers."""
        from src.dashboard.shiny_tab_results.subtab_simulation import ALL_ETF_SYMBOLS

        assert len(ALL_ETF_SYMBOLS) == 12

    def test_default_selected_etfs_are_subset_of_all(self) -> None:
        """Every DEFAULT_SELECTED_ETFS entry is a member of ALL_ETF_SYMBOLS."""
        from src.dashboard.shiny_tab_results.subtab_simulation import (
            ALL_ETF_SYMBOLS,
            DEFAULT_SELECTED_ETFS,
        )

        for sym in DEFAULT_SELECTED_ETFS:
            assert sym in ALL_ETF_SYMBOLS, f"'{sym}' not in ALL_ETF_SYMBOLS"

    def test_distribution_choices_has_required_keys(self) -> None:
        """DISTRIBUTION_CHOICES includes normal, lognormal, and student_t."""
        from src.dashboard.shiny_tab_results.subtab_simulation import DISTRIBUTION_CHOICES

        for key in ("normal", "lognormal", "student_t"):
            assert key in DISTRIBUTION_CHOICES, (
                f"'{key}' missing from DISTRIBUTION_CHOICES"
            )

    def test_rng_type_choices_has_required_keys(self) -> None:
        """RNG_TYPE_CHOICES includes pcg64 and mt19937."""
        from src.dashboard.shiny_tab_results.subtab_simulation import RNG_TYPE_CHOICES

        for key in ("pcg64", "mt19937"):
            assert key in RNG_TYPE_CHOICES, (
                f"'{key}' missing from RNG_TYPE_CHOICES"
            )

    def test_simulate_ui_callable(self) -> None:
        """subtab_simulation_ui is a callable."""
        from src.dashboard.shiny_tab_results.subtab_simulation import subtab_simulation_ui

        assert callable(subtab_simulation_ui)

    def test_simulate_server_callable(self) -> None:
        """subtab_simulation_server is a callable."""
        from src.dashboard.shiny_tab_results.subtab_simulation import subtab_simulation_server

        assert callable(subtab_simulation_server)


@pytest.mark.unit
class Test_Reporting_Pure_Logic:
    """Pure-Python logic tests for subtab_reporting security helpers.

    These run without playwright and without a Shiny server.
    """

    def test_sanitize_accepts_well_formed_filename(self) -> None:
        """sanitize_filename_for_security accepts a valid PDF filename."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            sanitize_filename_for_security,
        )

        is_valid, sanitized, _ = sanitize_filename_for_security(filename="QWIM_Report_2024.pdf")
        assert is_valid is True
        assert len(sanitized) > 0

    def test_sanitize_rejects_empty_filename(self) -> None:
        """sanitize_filename_for_security rejects an empty filename."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            sanitize_filename_for_security,
        )

        is_valid, sanitized, _ = sanitize_filename_for_security(filename="")
        assert is_valid is False
        assert sanitized == ""

    def test_sanitize_rejects_path_traversal(self) -> None:
        """sanitize_filename_for_security rejects path traversal attempts."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            sanitize_filename_for_security,
        )

        is_valid, _, _ = sanitize_filename_for_security(filename="../../etc/passwd.pdf")
        assert is_valid is False

    def test_sanitize_rejects_non_pdf_extension(self) -> None:
        """sanitize_filename_for_security rejects filenames without .pdf extension."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            sanitize_filename_for_security,
        )

        is_valid, _, _ = sanitize_filename_for_security(filename="Report_2024.docx")
        assert is_valid is False

    def test_sanitize_rejects_overlong_filename(self) -> None:
        """sanitize_filename_for_security rejects filenames exceeding MAX_FILENAME_LENGTH."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            MAX_FILENAME_LENGTH,
            sanitize_filename_for_security,
        )

        long_name = "x" * (MAX_FILENAME_LENGTH + 10) + ".pdf"
        is_valid, _, _ = sanitize_filename_for_security(filename=long_name)
        assert is_valid is False

    def test_sanitize_returns_3_tuple(self) -> None:
        """sanitize_filename_for_security always returns a 3-element tuple."""
        from src.dashboard.shiny_tab_results.subtab_reporting import (
            sanitize_filename_for_security,
        )

        result = sanitize_filename_for_security(filename="Test.pdf")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_max_filename_length_is_positive_int(self) -> None:
        """MAX_FILENAME_LENGTH is a positive integer."""
        from src.dashboard.shiny_tab_results.subtab_reporting import MAX_FILENAME_LENGTH

        assert isinstance(MAX_FILENAME_LENGTH, int)
        assert MAX_FILENAME_LENGTH > 0
