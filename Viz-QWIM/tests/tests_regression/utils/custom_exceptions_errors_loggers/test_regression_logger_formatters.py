"""Regression tests for _logger_formatters console-prefix precedence."""

from __future__ import annotations

import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    _subtab_console_rules,
    filter_console_dynamic,
    set_console_level_for_subtab,
)


def _make_record(module_name: str, level_name: str, level_no: int) -> dict:
    """Build a minimal record accepted by filter_console_dynamic."""
    return {
        "level": type("Level", (), {"no": level_no, "name": level_name})(),
        "name": module_name,
        "extra": {"name": module_name},
    }


@pytest.fixture(autouse=True)
def fixture_reset_console_rules() -> None:
    """Reset per-subtab console rules around each regression test."""
    _subtab_console_rules.clear()
    yield
    _subtab_console_rules.clear()


class Class_Test_Regression_Logger_Formatters:
    """Regression baselines for overlapping console prefix handling."""

    @pytest.mark.regression()
    def Test_overlapping_prefix_debug_baseline(self) -> None:
        """A specific debug rule must win over a broader info rule."""
        broader_prefix = "src.dashboard"
        specific_prefix = (
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"
        )
        module_name = f"{specific_prefix}.helper"

        set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = "info")
        set_console_level_for_subtab(_subtab_key = "portfolio_comparison", module_prefix = specific_prefix, level_key = "debug")

        assert filter_console_dynamic(
            record = _make_record(module_name, "DEBUG", LOG_LEVEL_DEBUG)
        ) is True

    @pytest.mark.regression()
    def Test_overlapping_prefix_info_baseline(self) -> None:
        """A specific debug rule must keep INFO blocked despite a broader info rule."""
        broader_prefix = "src.dashboard"
        specific_prefix = (
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_comparison"
        )
        module_name = f"{specific_prefix}.helper"

        set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = "info")
        set_console_level_for_subtab(_subtab_key = "portfolio_comparison", module_prefix = specific_prefix, level_key = "debug")

        assert filter_console_dynamic(
            record = _make_record(module_name, "INFO", LOG_LEVEL_INFO)
        ) is False