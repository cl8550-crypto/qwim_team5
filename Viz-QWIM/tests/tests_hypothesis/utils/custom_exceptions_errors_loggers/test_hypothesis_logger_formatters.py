"""Hypothesis tests for _logger_formatters console-prefix precedence."""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

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
    """Reset per-subtab console rules around each property test."""
    _subtab_console_rules.clear()
    yield
    _subtab_console_rules.clear()


class Class_Test_Hypothesis_Logger_Formatters:
    """Property-based tests for overlapping console prefix rules."""

    @pytest.mark.unit()
    @given(
        dashboard_suffix=st.from_regex(r"[a-z]{3,8}", fullmatch=True),
        subtab_suffix=st.from_regex(r"[a-z]{3,8}", fullmatch=True),
        specific_level_key=st.sampled_from(["debug", "info", "info_debug"]),
        insertion_order=st.sampled_from(["broader_first", "specific_first"]),
    )
    @settings(max_examples=40)
    def Test_most_specific_prefix_controls_debug_and_info_records(
        self,
        dashboard_suffix: str,
        subtab_suffix: str,
        specific_level_key: str,
        insertion_order: str,
    ) -> None:
        """The longest matching prefix should win regardless of insertion order."""
        broader_prefix = f"src.dashboard.{dashboard_suffix}"
        specific_prefix = f"{broader_prefix}.{subtab_suffix}"
        module_name = f"{specific_prefix}.helper"
        broader_level_key = "info" if specific_level_key != "info" else "debug"

        if insertion_order == "broader_first":
            set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = broader_level_key)
            set_console_level_for_subtab(_subtab_key = "subtab", module_prefix = specific_prefix, level_key = specific_level_key)
        else:
            set_console_level_for_subtab(_subtab_key = "subtab", module_prefix = specific_prefix, level_key = specific_level_key)
            set_console_level_for_subtab(_subtab_key = "dashboard", module_prefix = broader_prefix, level_key = broader_level_key)

        debug_record = _make_record(module_name, "DEBUG", LOG_LEVEL_DEBUG)
        info_record = _make_record(module_name, "INFO", LOG_LEVEL_INFO)

        expected_debug = specific_level_key in {"debug", "info_debug"}
        expected_info = specific_level_key in {"info", "info_debug"}

        assert filter_console_dynamic(record = debug_record) is expected_debug
        assert filter_console_dynamic(record = info_record) is expected_info