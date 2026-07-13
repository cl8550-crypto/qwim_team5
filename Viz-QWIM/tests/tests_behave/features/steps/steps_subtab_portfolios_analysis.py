"""Behave steps for the active portfolio-analysis subtab feature."""

from __future__ import annotations

import importlib
import importlib.util
import re

from pathlib import Path
from typing import Any

from behave import given, then, when  # type: ignore[import-untyped]

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def _import_portfolios_analysis_module() -> Any:
    """Return the public portfolio-analysis facade module."""
    try:
        return importlib.import_module(
            "src.dashboard.shiny_tab_portfolios.subtab_portfolios_analysis",
        )
    except ImportError as exc:
        raise AssertionError(
            f"Portfolio analysis module not importable: {exc}",
        ) from exc


def _read_portfolios_analysis_source() -> str:
    """Return the public portfolio-analysis source text."""
    spec = importlib.util.find_spec(
        "src.dashboard.shiny_tab_portfolios.subtab_portfolios_analysis",
    )
    if spec and spec.origin:
        return Path(spec.origin).read_text(encoding="utf-8")
    return ""


@given("the active portfolio analysis subtab module is importable")
def step_given_active_portfolios_analysis_importable(context: Any) -> None:
    """Load the active portfolio-analysis module and source text."""
    context.portfolios_analysis_module = _import_portfolios_analysis_module()
    context.portfolios_analysis_source = _read_portfolios_analysis_source()


@when("I inspect the active portfolio analysis exports")
def step_when_inspect_active_portfolios_analysis_exports(context: Any) -> None:
    """Collect the public exports from the portfolio-analysis facade."""
    module_analysis = getattr(context, "portfolios_analysis_module", None)
    if module_analysis is None:
        module_analysis = _import_portfolios_analysis_module()

    context.portfolios_analysis_exports = {
        "subtab_portfolios_analysis_ui": getattr(
            module_analysis,
            "subtab_portfolios_analysis_ui",
            None,
        ),
        "subtab_portfolios_analysis_server": getattr(
            module_analysis,
            "subtab_portfolios_analysis_server",
            None,
        ),
    }


@when("I inspect the active portfolio analysis default time period")
def step_when_inspect_active_portfolios_analysis_default(context: Any) -> None:
    """Extract the default time-period value from the public facade source."""
    source_text = getattr(context, "portfolios_analysis_source", "")
    match = re.search(
        r'input_ID_tab_portfolios_subtab_portfolios_analysis_time_period[\s\S]{0,400}?selected="([^"]+)"',
        source_text,
    )
    context.portfolios_analysis_default_time_period = match.group(1) if match else ""
    _logger.debug(
        "Active portfolio analysis default time period: %s",
        context.portfolios_analysis_default_time_period,
    )


@then('the active portfolio analysis export "{export_name}" should be callable')
def step_then_active_portfolios_analysis_export_callable(
    context: Any,
    export_name: str,
) -> None:
    """Assert the named public portfolio-analysis export is callable."""
    export_map = getattr(context, "portfolios_analysis_exports", {})
    export_value = export_map.get(export_name)
    assert export_value is not None, f"Missing export '{export_name}'"
    assert callable(export_value), f"Export '{export_name}' is not callable"


@then('the active portfolio analysis default time period should be "{expected_value}"')
def step_then_active_portfolios_analysis_default_value(
    context: Any,
    expected_value: str,
) -> None:
    """Assert the public time-period default remains stable."""
    actual_value = getattr(context, "portfolios_analysis_default_time_period", "")
    assert actual_value == expected_value, (
        f"Expected default time period '{expected_value}', got '{actual_value}'"
    )


@then('the active portfolio analysis source should include "{expected_text}"')
def step_then_active_portfolios_analysis_source_contains(
    context: Any,
    expected_text: str,
) -> None:
    """Assert the public portfolio-analysis facade source includes a fragment."""
    source_text = getattr(context, "portfolios_analysis_source", "")
    assert expected_text in source_text, (
        f"Expected '{expected_text}' in active portfolio analysis source"
    )