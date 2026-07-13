"""Behave step definitions for generate_data feature.

Covers:
  - generate_monthly_timeseries
  - generate_scenarios_daily_returns_CMA_Tier_0
  - main

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-29
"""

from __future__ import annotations

import io
import sys
import tempfile

from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch for exception_custom.py compatibility
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    import src.utils.data_utils.generate_data as generate_data_module

    from src.utils.data_utils.generate_data import generate_monthly_timeseries
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Require imports."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"generate_data could not be imported: {_import_error_message}")


def _build_fake_module_path(depth: int) -> Path:
    """Create a fake module path whose fallback root resolves to a temp directory."""
    tmp_dir = Path(tempfile.mkdtemp())
    fake_path = tmp_dir
    for index in range(depth):
        fake_path = fake_path / chr(ord("a") + index)
    fake_path.mkdir(parents=True, exist_ok=True)
    fake_file = fake_path / "generate_data.py"
    fake_file.touch()
    return fake_file


@given("generate_data utilities are importable")
def step_given_generate_data_importable(context) -> None:
    """Require generate_data imports and initialize context state."""
    _require_imports()
    context.monthly_df = None
    context.scenario_result = None
    context.output_file = None


@when("I generate monthly time series data for the 2020 calendar year")
def step_generate_monthly_time_series_2020(context) -> None:
    """Generate the 2020 monthly time series window."""
    _require_imports()
    context.monthly_df = generate_monthly_timeseries(
        start_date="2020-01-01",
        end_date="2021-01-01",
    )


@when("I run generate_data main with a temporary project root")
def step_run_generate_data_main_temp_root(context) -> None:
    """Run main() with a temporary patched project root."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=2)
    original_file = generate_data_module.__file__
    try:
        generate_data_module.__file__ = str(fake_file)
        generate_data_module.main()
    finally:
        generate_data_module.__file__ = original_file

    context.output_file = fake_file.parents[2] / "inputs" / "raw" / "data_timeseries.csv"


@when("I generate CMA Tier 0 scenarios with a temporary project root")
def step_generate_cma_scenarios_temp_root(context) -> None:
    """Run scenario generation with a temporary patched project root."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=3)
    original_file = generate_data_module.__file__
    try:
        generate_data_module.__file__ = str(fake_file)
        context.scenario_result = generate_data_module.generate_scenarios_daily_returns_CMA_Tier_0(
            start_date="2024-01-01",
            end_date="2024-03-31",
            num_scenarios=5,
            random_seed=42,
        )
    finally:
        generate_data_module.__file__ = original_file

    context.output_file = fake_file.parents[3] / "inputs" / "raw" / "returns_CMA_Tier_0.xlsx"


@then("the generated monthly time series should have 12 rows")
def step_then_monthly_timeseries_rows(context) -> None:
    """Assert the generated monthly time series has the expected row count."""
    assert context.monthly_df is not None
    assert context.monthly_df.shape[0] == 12


@then("the generated monthly time series should have the expected columns")
def step_then_monthly_timeseries_columns(context) -> None:
    """Assert the generated monthly time series columns stay stable."""
    assert context.monthly_df is not None
    assert list(context.monthly_df.columns) == ["date", "AA", "BB", "CC", "DD", "EE", "FF", "GG"]


@then("the monthly CSV output file should exist and be non-empty")
def step_then_monthly_csv_exists(context) -> None:
    """Assert the generated CSV file exists and has content."""
    assert context.output_file is not None
    assert context.output_file.exists()
    assert context.output_file.stat().st_size > 0


@then("the scenario workbook mapping should contain the expected sheet names")
def step_then_scenario_sheet_names(context) -> None:
    """Assert the returned workbook mapping has the expected public keys."""
    assert context.scenario_result is not None
    assert set(context.scenario_result) == {
        "Expected Returns",
        "Volatilities",
        "Correlations",
        "Scenarios",
    }


@then("the scenario workbook output file should exist and be non-empty")
def step_then_scenario_workbook_exists(context) -> None:
    """Assert the generated scenario workbook exists and has content."""
    assert context.output_file is not None
    assert context.output_file.exists()
    assert context.output_file.stat().st_size > 0


@then("the scenario dates should contain only business days")
def step_then_scenario_dates_business_days(context) -> None:
    """Assert the generated scenario dates exclude weekends."""
    assert context.scenario_result is not None
    dates = context.scenario_result["Scenarios"]["Date"].to_list()
    assert all(date_item.weekday() < 5 for date_item in dates)