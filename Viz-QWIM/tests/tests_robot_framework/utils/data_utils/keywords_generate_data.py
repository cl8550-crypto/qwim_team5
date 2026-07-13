"""Robot Framework keyword library for generate_data tests.

Keyword wrappers for:
- generate_monthly_timeseries: stable monthly DataFrame shape and columns
- main: CSV file generation under a resolved project root
- generate_scenarios_daily_returns_CMA_Tier_0: workbook mapping and XLSX output

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-05-29
"""

from __future__ import annotations

import io
import sys
import tempfile

from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so that "src." imports resolve correctly
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
    import logging as _logging

    _logger = _logging.getLogger(__name__)
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging

    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
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


def module_is_importable() -> bool:
    """Return True if generate_data can be imported."""
    return MODULE_IMPORT_AVAILABLE


def monthly_timeseries_2020_has_expected_shape_and_columns() -> None:
    """Assert the 2020 monthly time series window has the expected shape and columns."""
    _require_imports()
    result = generate_monthly_timeseries(start_date="2020-01-01", end_date="2021-01-01")
    assert result.shape[0] == 12
    assert list(result.columns) == ["date", "AA", "BB", "CC", "DD", "EE", "FF", "GG"]


def main_writes_monthly_csv_in_temp_root() -> None:
    """Assert main() writes the expected CSV under a temporary project root."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=2)
    original_file = generate_data_module.__file__
    try:
        generate_data_module.__file__ = str(fake_file)
        generate_data_module.main()
    finally:
        generate_data_module.__file__ = original_file

    output_file = fake_file.parents[2] / "inputs" / "raw" / "data_timeseries.csv"
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def scenario_generation_returns_expected_sheets() -> None:
    """Assert scenario generation returns the expected workbook mapping."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=3)
    original_file = generate_data_module.__file__
    try:
        generate_data_module.__file__ = str(fake_file)
        result = generate_data_module.generate_scenarios_daily_returns_CMA_Tier_0(
            start_date="2024-01-01",
            end_date="2024-03-31",
            num_scenarios=5,
            random_seed=42,
        )
    finally:
        generate_data_module.__file__ = original_file

    assert set(result) == {
        "Expected Returns",
        "Volatilities",
        "Correlations",
        "Scenarios",
    }


def scenario_generation_writes_workbook_and_business_dates() -> None:
    """Assert scenario generation writes its workbook and excludes weekends."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=3)
    original_file = generate_data_module.__file__
    try:
        generate_data_module.__file__ = str(fake_file)
        result = generate_data_module.generate_scenarios_daily_returns_CMA_Tier_0(
            start_date="2024-01-01",
            end_date="2024-03-31",
            num_scenarios=5,
            random_seed=42,
        )
    finally:
        generate_data_module.__file__ = original_file

    output_file = fake_file.parents[3] / "inputs" / "raw" / "returns_CMA_Tier_0.xlsx"
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    dates = result["Scenarios"]["Date"].to_list()
    assert all(date_item.weekday() < 5 for date_item in dates)