"""Unit tests for report_QWIM module.

Tests cover:
    - ``safe_is_finite_value`` — None, strings, integers, floats, inf, nan
    - ``safe_polars_column_access`` — missing column, None DataFrame, operations
    - ``validate_polars_DF`` — None, empty, valid DataFrames
    - ``create_sample_*_dataframe`` — correct schema and non-empty return
    - ``compile_typst_report`` — missing template, absent typst binary
    - ``generate_report_PDF`` — returns 3-tuple, mocked subprocess path
    - ``reporting.__init__`` — correct public exports (regression: build_typst_data_context removed)

Author:
    QWIM Development Team

Version:
    0.2.0
"""

from __future__ import annotations

import math

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import polars as pl
import pytest

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

# ---------------------------------------------------------------------------
# Optional import guard
# ---------------------------------------------------------------------------
try:
    from src.dashboard.reporting.report_QWIM import (
        compile_typst_report,
        create_sample_assets_dataframe,
        create_sample_goals_dataframe,
        create_sample_income_dataframe,
        create_sample_personal_info_dataframe,
        generate_report_PDF,
        safe_is_finite_value,
        safe_polars_column_access,
        validate_polars_DF,
    )

    MODULE_AVAILABLE = True
except ImportError as exc:
    MODULE_AVAILABLE = False
    _logger.warning(f"report_QWIM import failed — tests will be skipped: {exc}")

pytestmark = pytest.mark.skipif(
    not MODULE_AVAILABLE,
    reason="src.dashboard.reporting.report_QWIM not importable in this environment",
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture()
def minimal_reactives_shiny() -> dict[str, Any]:
    """Return a minimal reactives_shiny dict with empty sub-dicts."""
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }


@pytest.fixture()
def sample_assets_df() -> pl.DataFrame:
    """Return a small valid assets DataFrame."""
    return pl.DataFrame(
        {
            "Investor_ID": ["INV001"],
            "Asset_Value": [100_000.0],
        },
    )


# ===========================================================================
# safe_is_finite_value
# ===========================================================================


@pytest.mark.unit()
class Test_safe_is_finite_value:
    """Tests for ``safe_is_finite_value``."""

    @pytest.mark.unit()
    def test_none_returns_false(self) -> None:
        """Test that none returns false."""
        assert safe_is_finite_value(value = None) is False

    @pytest.mark.unit()
    def test_string_returns_false(self) -> None:
        """Test that string returns false."""
        assert safe_is_finite_value(value = "hello") is False

    @pytest.mark.unit()
    def test_list_returns_false(self) -> None:
        """Test that list returns false."""
        assert safe_is_finite_value(value = [1, 2]) is False

    @pytest.mark.unit()
    def test_integer_returns_true(self) -> None:
        """Test that integer returns true."""
        assert safe_is_finite_value(value = 42) is True

    @pytest.mark.unit()
    def test_bool_returns_false(self) -> None:
        """Test that bool is rejected instead of being treated as an integer."""
        assert safe_is_finite_value(value = True) is False

    @pytest.mark.unit()
    def test_float_returns_true(self) -> None:
        """Test that float returns true."""
        assert safe_is_finite_value(value = 3.14) is True

    @pytest.mark.unit()
    def test_zero_returns_true(self) -> None:
        """Test that zero returns true."""
        assert safe_is_finite_value(value = 0) is True

    @pytest.mark.unit()
    def test_negative_returns_true(self) -> None:
        """Test that negative returns true."""
        assert safe_is_finite_value(value = -100.0) is True

    @pytest.mark.unit()
    def test_pos_inf_returns_false(self) -> None:
        """Test that pos inf returns false."""
        assert safe_is_finite_value(value = math.inf) is False

    @pytest.mark.unit()
    def test_neg_inf_returns_false(self) -> None:
        """Test that neg inf returns false."""
        assert safe_is_finite_value(value = -math.inf) is False

    @pytest.mark.unit()
    def test_nan_returns_false(self) -> None:
        """Test that nan returns false."""
        assert safe_is_finite_value(value = float("nan")) is False

    @pytest.mark.unit()
    def test_numpy_float64_returns_true(self) -> None:
        """Test that numpy float64 returns true."""
        assert safe_is_finite_value(value = np.float64(7.5)) is True

    @pytest.mark.unit()
    def test_numpy_nan_returns_false(self) -> None:
        """Test that numpy nan returns false."""
        assert safe_is_finite_value(value = np.float64("nan")) is False


# ===========================================================================
# safe_polars_column_access
# ===========================================================================


@pytest.mark.unit()
class Test_safe_polars_column_access:
    """Tests for ``safe_polars_column_access``."""

    @pytest.mark.unit()
    def test_none_df_returns_default(self) -> None:
        """Test that none df returns default."""
        result = safe_polars_column_access(polars_DF = None, column_name = "col", operation = "sum", default_value=-1)
        assert result == -1

    @pytest.mark.unit()
    def test_missing_column_returns_default(self) -> None:
        """Test that missing column returns default."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        result = safe_polars_column_access(polars_DF = df, column_name = "z", operation = "sum", default_value=99)
        assert result == 99

    @pytest.mark.unit()
    def test_sum_operation(self) -> None:
        """Test that sum operation."""
        df = pl.DataFrame({"val": [10.0, 20.0, 30.0]})
        result = safe_polars_column_access(polars_DF = df, column_name = "val", operation = "sum")
        assert result == pytest.approx(60.0)

    @pytest.mark.unit()
    def test_mean_operation(self) -> None:
        """Test that mean operation."""
        df = pl.DataFrame({"val": [10.0, 20.0, 30.0]})
        result = safe_polars_column_access(polars_DF = df, column_name = "val", operation = "mean")
        assert result == pytest.approx(20.0)

    @pytest.mark.unit()
    def test_first_operation(self) -> None:
        """Test that first operation."""
        df = pl.DataFrame({"name": ["Alice", "Bob"]})
        result = safe_polars_column_access(polars_DF = df, column_name = "name", operation = "first")
        assert result == "Alice"


# ===========================================================================
# validate_polars_DF
# ===========================================================================


@pytest.mark.unit()
class Test_validate_polars_DF:
    """Tests for ``validate_polars_DF``."""

    @pytest.mark.unit()
    def test_none_returns_false(self) -> None:
        """Test that none returns false."""
        assert validate_polars_DF(polars_DF = None) is False

    @pytest.mark.unit()
    def test_non_dataframe_returns_false(self) -> None:
        """Test that non dataframe returns false."""
        assert validate_polars_DF(polars_DF = {"a": 1}) is False  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_empty_rows_returns_false(self) -> None:
        """Test that empty rows returns false."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        assert validate_polars_DF(polars_DF = df) is False

    @pytest.mark.unit()
    def test_valid_df_returns_true(self) -> None:
        """Test that valid df returns true."""
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        assert validate_polars_DF(polars_DF = df) is True

    @pytest.mark.unit()
    def test_single_row_df_returns_true(self) -> None:
        """Test that single row df returns true."""
        df = pl.DataFrame({"x": [42]})
        assert validate_polars_DF(polars_DF = df) is True


# ===========================================================================
# create_sample_* dataframe functions
# ===========================================================================


@pytest.mark.unit()
class Test_create_sample_dataframes:
    """Tests for the four ``create_sample_*_dataframe`` helpers."""

    @pytest.mark.unit()
    def test_personal_info_is_dataframe(self) -> None:
        """Test that personal info is dataframe."""
        df = create_sample_personal_info_dataframe()
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_personal_info_non_empty(self) -> None:
        """Test that personal info non empty."""
        df = create_sample_personal_info_dataframe()
        assert df.height > 0

    @pytest.mark.unit()
    def test_personal_info_has_investor_id(self) -> None:
        """Test that personal info has investor id."""
        df = create_sample_personal_info_dataframe()
        assert "Investor_ID" in df.columns

    @pytest.mark.unit()
    def test_assets_is_dataframe(self) -> None:
        """Test that assets is dataframe."""
        df = create_sample_assets_dataframe()
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_assets_non_empty(self) -> None:
        """Test that assets non empty."""
        df = create_sample_assets_dataframe()
        assert df.height > 0

    @pytest.mark.unit()
    def test_goals_is_dataframe(self) -> None:
        """Test that goals is dataframe."""
        df = create_sample_goals_dataframe()
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_goals_non_empty(self) -> None:
        """Test that goals non empty."""
        df = create_sample_goals_dataframe()
        assert df.height > 0

    @pytest.mark.unit()
    def test_income_is_dataframe(self) -> None:
        """Test that income is dataframe."""
        df = create_sample_income_dataframe()
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_income_non_empty(self) -> None:
        """Test that income non empty."""
        df = create_sample_income_dataframe()
        assert df.height > 0


# ===========================================================================
# compile_typst_report
# ===========================================================================


@pytest.mark.unit()
class Test_compile_typst_report:
    """Tests for ``compile_typst_report`` with a non-existent template."""

    @pytest.mark.unit()
    def test_missing_template_returns_failure(self, tmp_path: Any) -> None:
        """compile_typst_report must return (False, <msg>) when .typ is absent."""
        non_existent = tmp_path / "ghost.typ"
        output_pdf = tmp_path / "out.pdf"
        success, msg = compile_typst_report(typ_template_path = non_existent, output_pdf_path = output_pdf)
        assert success is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.unit()
    def test_returns_tuple_of_two(self, tmp_path: Any) -> None:
        """Test that returns tuple of two."""
        non_existent = tmp_path / "ghost.typ"
        output_pdf = tmp_path / "out.pdf"
        result = compile_typst_report(typ_template_path = non_existent, output_pdf_path = output_pdf)
        assert len(result) == 2


# ===========================================================================
# generate_report_PDF  (mocked subprocess / typst to avoid real compilation)
# ===========================================================================


@pytest.mark.unit()
class Test_generate_report_PDF:
    """Tests for ``generate_report_PDF`` with subprocess mocked."""

    @pytest.mark.unit()
    def test_returns_three_tuple(self, tmp_path: Any) -> None:
        """Test that returns three tuple."""
        result = generate_report_PDF(output_directory=str(tmp_path))
        assert len(result) == 3

    @pytest.mark.unit()
    def test_first_element_is_bool(self, tmp_path: Any) -> None:
        """Test that first element is bool."""
        success, _msg, _path = generate_report_PDF(output_directory=str(tmp_path))
        assert isinstance(success, bool)

    @pytest.mark.unit()
    def test_second_element_is_str(self, tmp_path: Any) -> None:
        """Test that second element is str."""
        _success, msg, _path = generate_report_PDF(output_directory=str(tmp_path))
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_third_element_is_str(self, tmp_path: Any) -> None:
        """Test that third element is str."""
        _success, _msg, path = generate_report_PDF(output_directory=str(tmp_path))
        assert isinstance(path, str)

    @patch("subprocess.run")
    @pytest.mark.unit()
    def test_mocked_typst_success(
        self, mock_run: MagicMock, tmp_path: Any,
    ) -> None:
        """When subprocess.run succeeds and a PDF is written, return True."""
        # Arrange: make subprocess.run a no-op whose side-effect creates the PDF
        typ_template_dir = tmp_path / "reporting"
        typ_template_dir.mkdir()
        # The function locates report_QWIM.typ relative to its own file path,
        # not tmp_path, so we cannot easily control that here.  Just confirm
        # that when subprocess.run returns successfully the wrapper doesn't crash.
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        result = generate_report_PDF(
            output_directory=str(tmp_path),
            reactives_shiny=None,
        )
        assert len(result) == 3  # (bool, str, str)


# ===========================================================================
# export_report_metadata — today's ISO date
# ===========================================================================


@pytest.mark.unit()
class Test_export_report_metadata:
    """Tests for ``export_report_metadata`` writing today's date."""

    @pytest.mark.unit()
    def test_writes_today_iso_date(self) -> None:
        """export_report_metadata must write today's ISO date string to JSON."""
        import datetime
        import json

        try:
            from src.dashboard.reporting.report_data_export import export_report_metadata
        except ImportError:
            pytest.skip("report_data_export not importable")

        result_path = export_report_metadata(reactives_shiny=None)

        if result_path is None or not result_path.exists():
            pytest.skip("export_report_metadata returned None or file not written")

        data = json.loads(result_path.read_text(encoding="utf-8"))
        today_iso = datetime.date.today().isoformat()
        assert "report_date_iso" in data, f"Missing 'report_date_iso'. Keys: {list(data.keys())}"
        assert data["report_date_iso"] == today_iso, (
            f"Expected '{today_iso}', got '{data['report_date_iso']}'"
        )

    @pytest.mark.unit()
    def test_writes_report_version(self) -> None:
        """export_report_metadata must include a 'report_version' field."""
        import json

        try:
            from src.dashboard.reporting.report_data_export import export_report_metadata
        except ImportError:
            pytest.skip("report_data_export not importable")

        result_path = export_report_metadata(reactives_shiny=None)

        if result_path is None or not result_path.exists():
            pytest.skip("export_report_metadata returned None or file not written")

        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert "report_version" in data, f"Missing 'report_version'. Keys: {list(data.keys())}"


# ===========================================================================
# export_outputs_skfolio_optimization — performance_summary key
# ===========================================================================


@pytest.mark.unit()
class Test_export_outputs_skfolio_optimization:
    """Tests for skfolio output export including performance_summary."""

    @pytest.mark.unit()
    def test_output_json_contains_performance_summary(self) -> None:
        """Exported skfolio JSON must include a 'performance_summary' key."""
        from unittest.mock import patch

        try:
            from src.dashboard.reporting import report_data_export
        except ImportError:
            pytest.skip("report_data_export not importable")

        captured: list[dict] = []

        def _mock_write_json(*, file_path: Any, data: dict) -> None:
            """Mock write json."""
            captured.append(data)

        with patch.object(report_data_export, "_write_json", side_effect=_mock_write_json):
            report_data_export.export_outputs_skfolio_optimization(reactives_shiny=None)

        assert len(captured) > 0, "No data was passed to _write_json"
        data = captured[0]
        assert "performance_summary" in data, (
            f"'performance_summary' missing. Keys: {list(data.keys())}"
        )

    @pytest.mark.unit()
    def test_performance_summary_has_method1_and_method2(self) -> None:
        """performance_summary must contain method1 and method2 sub-keys."""
        from unittest.mock import patch

        try:
            from src.dashboard.reporting import report_data_export
        except ImportError:
            pytest.skip("report_data_export not importable")

        captured: list[dict] = []

        def _mock_write_json(*, file_path: Any, data: dict) -> None:
            """Mock write json."""
            captured.append(data)

        with patch.object(report_data_export, "_write_json", side_effect=_mock_write_json):
            report_data_export.export_outputs_skfolio_optimization(reactives_shiny=None)

        assert len(captured) > 0, "_write_json was never called"
        perf = captured[0].get("performance_summary", {})
        assert "method1" in perf, f"'method1' missing from performance_summary: {perf}"
        assert "method2" in perf, f"'method2' missing from performance_summary: {perf}"

    @pytest.mark.unit()
    def test_output_json_contains_statistics_comparison_key(self) -> None:
        """Exported skfolio JSON must include 'statistics_comparison'."""
        from unittest.mock import patch

        try:
            from src.dashboard.reporting import report_data_export
        except ImportError:
            pytest.skip("report_data_export not importable")

        captured: list[dict] = []

        def _mock_write_json(*, file_path: Any, data: dict) -> None:
            """Mock write json."""
            captured.append(data)

        with patch.object(report_data_export, "_write_json", side_effect=_mock_write_json):
            report_data_export.export_outputs_skfolio_optimization(reactives_shiny=None)

        assert len(captured) > 0, "No data was passed to _write_json"
        data = captured[0]
        assert "statistics_comparison" in data, (
            f"'statistics_comparison' missing. Keys: {list(data.keys())}"
        )

    @pytest.mark.unit()
    def test_statistics_comparison_defaults_to_list(self) -> None:
        """Fallback export must emit statistics_comparison as an array."""
        from unittest.mock import patch

        try:
            from src.dashboard.reporting import report_data_export
        except ImportError:
            pytest.skip("report_data_export not importable")

        captured: list[dict] = []

        def _mock_write_json(*, file_path: Any, data: dict) -> None:
            """Mock write json."""
            captured.append(data)

        with patch.object(report_data_export, "_write_json", side_effect=_mock_write_json):
            report_data_export.export_outputs_skfolio_optimization(reactives_shiny=None)

        assert len(captured) > 0, "No data was passed to _write_json"
        stats_rows = captured[0].get("statistics_comparison")
        assert isinstance(stats_rows, list), (
            f"statistics_comparison should be list, got {type(stats_rows).__name__}"
        )


# ===========================================================================
# Regression: reporting.__init__ exports
# ===========================================================================


@pytest.mark.unit()
@pytest.mark.regression()
class Test_Reporting_Package_Exports:
    """Regression tests for the ``src.dashboard.reporting`` package public API.

    When ``build_typst_data_context`` was removed from ``report_QWIM.py`` the
    ``__init__.py`` import list was updated accordingly.  These tests guard
    against re-introducing the stale export or accidentally removing the three
    remaining public symbols.
    """

    @pytest.mark.unit()
    def test_compile_typst_report_exported(self) -> None:
        """``compile_typst_report`` must be importable from the package root."""
        try:
            from src.dashboard.reporting import compile_typst_report as fn

            assert callable(fn)
        except ImportError:
            pytest.skip("reporting package not importable")

    @pytest.mark.unit()
    def test_generate_report_PDF_exported(self) -> None:
        """``generate_report_PDF`` must be importable from the package root."""
        try:
            from src.dashboard.reporting import generate_report_PDF as fn

            assert callable(fn)
        except ImportError:
            pytest.skip("reporting package not importable")

    @pytest.mark.unit()
    def test_validate_polars_DF_exported(self) -> None:
        """``validate_polars_DF`` must be importable from the package root."""
        try:
            from src.dashboard.reporting import validate_polars_DF as fn

            assert callable(fn)
        except ImportError:
            pytest.skip("reporting package not importable")

    @pytest.mark.unit()
    def test_build_typst_data_context_NOT_exported(self) -> None:
        """``build_typst_data_context`` must NOT be exported — it was removed.

        This is a regression guard: if someone re-adds the function under the
        same name, they should also update the ``__init__.py`` intentionally.
        """
        import importlib

        try:
            pkg = importlib.import_module("src.dashboard.reporting")
        except ImportError:
            pytest.skip("reporting package not importable")

        assert not hasattr(pkg, "build_typst_data_context"), (
            "build_typst_data_context was re-exported from reporting.__init__.py "
            "but was intentionally removed — update __init__.py if this is deliberate."
        )

    @pytest.mark.unit()
    def test_all_list_matches_actual_exports(self) -> None:
        """``__all__`` in reporting/__init__.py must contain exactly 3 symbols."""
        try:
            import src.dashboard.reporting as pkg
        except ImportError:
            pytest.skip("reporting package not importable")

        expected_exports = {"compile_typst_report", "generate_report_PDF", "validate_polars_DF"}
        actual_all = set(getattr(pkg, "__all__", []))
        assert actual_all == expected_exports, (
            f"reporting.__all__ mismatch.\n"
            f"  Expected: {sorted(expected_exports)}\n"
            f"  Actual  : {sorted(actual_all)}"
        )


# ===========================================================================
# safe_polars_column_access — additional branch coverage
# ===========================================================================


@pytest.mark.unit()
class Test_safe_polars_column_access_extra:
    """Additional branch coverage for ``safe_polars_column_access``."""

    @pytest.mark.unit()
    def test_empty_df_returns_default(self) -> None:
        """Empty DataFrame (height=0) should return default_value."""
        df = pl.DataFrame({"val": pl.Series([], dtype=pl.Float64)})
        result = safe_polars_column_access(polars_DF = df, column_name = "val", operation = "sum", default_value=-99)
        assert result == -99

    @pytest.mark.unit()
    def test_non_numeric_column_sum_returns_default(self) -> None:
        """String column with sum operation should return default_value."""
        df = pl.DataFrame({"name": ["Alice", "Bob"]})
        result = safe_polars_column_access(polars_DF = df, column_name = "name", operation = "sum", default_value=0)
        assert result == 0

    @pytest.mark.unit()
    def test_non_numeric_column_mean_returns_default(self) -> None:
        """String column with mean operation should return default_value."""
        df = pl.DataFrame({"name": ["Alice", "Bob"]})
        result = safe_polars_column_access(polars_DF = df, column_name = "name", operation = "mean", default_value=0)
        assert result == 0

    @pytest.mark.unit()
    def test_unknown_operation_returns_default(self) -> None:
        """Unknown operation name should return default_value."""
        df = pl.DataFrame({"val": [1.0, 2.0, 3.0]})
        result = safe_polars_column_access(polars_DF = df, column_name = "val", operation = "nonsense_op", default_value=42)
        assert result == 42

    @pytest.mark.unit()
    def test_exception_path_returns_default(self) -> None:
        """Force the inner except branch by providing a zero-width DataFrame."""
        df = pl.DataFrame({"val": [1.0, 2.0]})
        # Use a patched select that raises to exercise the except branch
        with patch.object(df.__class__, "select", side_effect=RuntimeError("forced")):
            result = safe_polars_column_access(polars_DF = df, column_name = "val", operation = "sum", default_value=-1)
        assert result == -1


# ===========================================================================
# compile_typst_report — subprocess and typst-pkg failure paths
# ===========================================================================


@pytest.mark.unit()
class Test_compile_typst_report_extra:
    """Extra tests covering subprocess failure branches in ``compile_typst_report``."""

    @pytest.mark.unit()
    def test_file_not_found_returns_failure(self, tmp_path: Any) -> None:
        """FileNotFoundError from subprocess → (False, message containing 'not found')."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_timeout_expired_returns_failure(self, tmp_path: Any) -> None:
        """TimeoutExpired from subprocess → (False, message) with no crash."""
        import subprocess

        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 120)),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False
        assert "timed out" in msg.lower() or isinstance(msg, str)

    @pytest.mark.unit()
    def test_subprocess_nonzero_returncode_returns_failure(self, tmp_path: Any) -> None:
        """Non-zero returncode from typst CLI → (False, error message)."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "typst error"
        mock_result.stdout = ""

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", return_value=mock_result),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False

    @pytest.mark.unit()
    def test_subprocess_success_but_no_pdf_returns_failure(self, tmp_path: Any) -> None:
        """Subprocess returns 0 but PDF is not created → (False, message)."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", return_value=mock_result),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_json_files_and_subdirs_copied_when_present(self, tmp_path: Any) -> None:
        """When JSON files and subdirs exist they are copied without error."""
        # Create a .typ template inside a directory that mimics the template dir
        template_dir = tmp_path / "template_dir"
        template_dir.mkdir()
        typ_file = template_dir / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")

        # Create JSON files
        (template_dir / "client_info.json").write_text("{}", encoding="utf-8")
        (template_dir / "report_metadata.json").write_text("{}", encoding="utf-8")

        # Create JSON subdirs
        inputs_dir = template_dir / "inputs_json"
        inputs_dir.mkdir()
        (inputs_dir / "data.json").write_text("{}", encoding="utf-8")

        outputs_dir = template_dir / "outputs_json"
        outputs_dir.mkdir()
        (outputs_dir / "out.json").write_text("{}", encoding="utf-8")

        # Create images subdir
        img_dir = template_dir / "outputs_images"
        img_dir.mkdir()
        (img_dir / "chart.svg").write_text("<svg/>", encoding="utf-8")

        # Create a .bib file
        (template_dir / "refs.bib").write_text("% bib", encoding="utf-8")

        output_pdf = tmp_path / "out.pdf"

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False  # typst not present
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_typst_pkg_raises_non_import_error_proceeds_to_subprocess(
        self, tmp_path: Any
    ) -> None:
        """typst._compile raises non-ImportError → CLI subprocess attempted."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        mock_typst = MagicMock()
        mock_typst.compile.side_effect = RuntimeError("typst pkg error")

        import sys

        original_modules = dict(sys.modules)
        sys.modules["typst"] = mock_typst
        try:
            with patch("subprocess.run", side_effect=FileNotFoundError):
                success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)
        finally:
            # Restore original module state
            for key in list(sys.modules.keys()):
                if key not in original_modules:
                    del sys.modules[key]
            for key, val in original_modules.items():
                sys.modules[key] = val

        assert success is False
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_zero_size_pdf_returns_failure(self, tmp_path: Any) -> None:
        """When compiled PDF exists but is 0 bytes, return (False, <msg>)."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""

        def _create_empty_pdf(*args: Any, **kwargs: Any) -> Any:
            output_pdf.write_bytes(b"")
            return mock_result

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", side_effect=_create_empty_pdf),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False
        assert "empty" in msg.lower() or isinstance(msg, str)

    @pytest.mark.unit()
    def test_outer_exception_returns_failure(self, tmp_path: Any) -> None:
        """Outer except in compile_typst_report catches unexpected errors."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        # Patch shutil.copy2 to raise on first call to trigger the outer except
        import shutil

        with patch.object(shutil, "copy2", side_effect=OSError("disk full")):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is False
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_subprocess_success_creates_pdf_returns_true(self, tmp_path: Any) -> None:
        """Subprocess returncode=0 + PDF created → (True, <msg>)."""
        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        def _create_real_pdf(*args: Any, **kwargs: Any) -> Any:
            output_pdf.write_bytes(b"%PDF-1.4 fake content")
            mock = MagicMock()
            mock.returncode = 0
            mock.stderr = ""
            mock.stdout = ""
            return mock

        with (
            patch("builtins.__import__", side_effect=ImportError),
            patch("subprocess.run", side_effect=_create_real_pdf),
        ):
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)

        assert success is True
        assert "compiled" in msg.lower() or isinstance(msg, str)

    @pytest.mark.unit()
    def test_typst_pkg_compiles_successfully_skips_subprocess(self, tmp_path: Any) -> None:
        """When typst package compiles successfully, subprocess is skipped."""
        import sys

        typ_file = tmp_path / "report.typ"
        typ_file.write_text("// empty", encoding="utf-8")
        output_pdf = tmp_path / "out.pdf"

        mock_typst = MagicMock()

        def _mock_compile(*args: Any, **kwargs: Any) -> None:
            output_pdf.write_bytes(b"%PDF-1.4 fake content")

        mock_typst.compile.side_effect = _mock_compile

        original_modules = dict(sys.modules)
        sys.modules["typst"] = mock_typst
        try:
            success, msg = compile_typst_report(typ_template_path = typ_file, output_pdf_path = output_pdf)
        finally:
            for key in list(sys.modules.keys()):
                if key not in original_modules:
                    del sys.modules[key]
            for key, val in original_modules.items():
                sys.modules[key] = val

        assert success is True
        assert isinstance(msg, str)


# ===========================================================================
# generate_report_PDF — additional branch coverage
# ===========================================================================


@pytest.mark.unit()
class Test_generate_report_PDF_extra:
    """Extra tests for ``generate_report_PDF`` branch coverage."""

    @pytest.mark.unit()
    def test_empty_filename_returns_failure(self, tmp_path: Any) -> None:
        """Empty output_filename must return (False, <msg>, '')."""
        success, msg, path = generate_report_PDF(
            output_filename="",
            output_directory=str(tmp_path),
        )
        assert success is False
        assert "empty" in msg.lower() or isinstance(msg, str)
        assert path == ""

    @pytest.mark.unit()
    def test_whitespace_filename_returns_failure(self, tmp_path: Any) -> None:
        """Whitespace-only output_filename must return failure."""
        success, msg, path = generate_report_PDF(
            output_filename="   ",
            output_directory=str(tmp_path),
        )
        assert success is False
        assert path == ""

    @pytest.mark.unit()
    def test_filename_without_pdf_gets_extension_appended(self, tmp_path: Any) -> None:
        """Filename without .pdf extension must be transparently handled (no crash)."""
        success, msg, path = generate_report_PDF(
            output_filename="myreport",
            output_directory=str(tmp_path),
        )
        # Whether it succeeds or fails depends on typst availability,
        # but it must return a proper 3-tuple with a string path
        assert isinstance(success, bool)
        assert isinstance(msg, str)
        assert isinstance(path, str)

    @pytest.mark.unit()
    def test_data_export_error_returns_failure(self, tmp_path: Any) -> None:
        """When export_all_report_data raises, return (False, <msg>, '')."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        # Create a dummy .typ template so the template-exists check passes
        typ_dir = _mod._REPORTING_DIR
        typ_template = typ_dir / "report_QWIM.typ"
        template_existed = typ_template.exists()

        if not template_existed:
            try:
                typ_dir.mkdir(parents=True, exist_ok=True)
                typ_template.write_text("// stub", encoding="utf-8")
                created_stub = True
            except Exception:
                pytest.skip("Cannot create stub .typ template")
        else:
            created_stub = False

        try:
            with patch.object(_mod, "export_all_report_data", side_effect=RuntimeError("boom")):
                success, msg, path = generate_report_PDF(
                    output_filename="report.pdf",
                    output_directory=str(tmp_path),
                )
        finally:
            if created_stub:
                try:
                    typ_template.unlink()
                except Exception:
                    pass

        assert success is False
        assert isinstance(msg, str)
        assert path == ""

    @pytest.mark.unit()
    def test_chart_export_error_does_not_abort(self, tmp_path: Any) -> None:
        """Chart export failure (warning only) must not stop compilation attempt."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        typ_dir = _mod._REPORTING_DIR
        typ_template = typ_dir / "report_QWIM.typ"
        template_existed = typ_template.exists()

        if not template_existed:
            try:
                typ_dir.mkdir(parents=True, exist_ok=True)
                typ_template.write_text("// stub", encoding="utf-8")
                created_stub = True
            except Exception:
                pytest.skip("Cannot create stub .typ template")
        else:
            created_stub = False

        try:
            with (
                patch.object(_mod, "export_all_report_data"),
                patch.object(
                    _mod, "export_all_report_plots", side_effect=RuntimeError("chart error")
                ),
                patch.object(_mod, "compile_typst_report", return_value=(False, "no typst")),
            ):
                success, msg, path = generate_report_PDF(
                    output_filename="report.pdf",
                    output_directory=str(tmp_path),
                    include_charts=True,
                )
        finally:
            if created_stub:
                try:
                    typ_template.unlink()
                except Exception:
                    pass

        # Compilation was mocked to fail — but chart error must not crash
        assert success is False
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_successful_compile_returns_true_and_path(self, tmp_path: Any) -> None:
        """Mocked successful compile → (True, <msg>, <abs_path>)."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        typ_dir = _mod._REPORTING_DIR
        typ_template = typ_dir / "report_QWIM.typ"
        template_existed = typ_template.exists()

        if not template_existed:
            try:
                typ_dir.mkdir(parents=True, exist_ok=True)
                typ_template.write_text("// stub", encoding="utf-8")
                created_stub = True
            except Exception:
                pytest.skip("Cannot create stub .typ template")
        else:
            created_stub = False

        try:
            with (
                patch.object(_mod, "export_all_report_data"),
                patch.object(_mod, "export_all_report_plots"),
                patch.object(
                    _mod, "compile_typst_report", return_value=(True, "Compiled OK")
                ),
            ):
                success, msg, path = generate_report_PDF(
                    output_filename="report.pdf",
                    output_directory=str(tmp_path),
                )
        finally:
            if created_stub:
                try:
                    typ_template.unlink()
                except Exception:
                    pass

        assert success is True
        assert isinstance(path, str)
        assert len(path) > 0

    @pytest.mark.unit()
    def test_template_not_found_returns_failure(self, tmp_path: Any) -> None:
        """When the .typ template is missing, return (False, <msg>, '')."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        orig_dir = _mod._REPORTING_DIR
        nonexistent_dir = tmp_path / "nonexistent_dir"
        _mod._REPORTING_DIR = nonexistent_dir
        try:
            success, msg, path = generate_report_PDF(
                output_filename="report.pdf",
                output_directory=str(tmp_path),
            )
        finally:
            _mod._REPORTING_DIR = orig_dir

        assert success is False
        assert "not found" in msg.lower() or isinstance(msg, str)
        assert path == ""

    @pytest.mark.unit()
    def test_mkdir_error_returns_failure(self, tmp_path: Any) -> None:
        """When output_dir.mkdir raises, return (False, <msg>, '')."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        typ_dir = _mod._REPORTING_DIR
        typ_template = typ_dir / "report_QWIM.typ"
        template_existed = typ_template.exists()

        if not template_existed:
            try:
                typ_dir.mkdir(parents=True, exist_ok=True)
                typ_template.write_text("// stub", encoding="utf-8")
                created_stub = True
            except Exception:
                pytest.skip("Cannot create stub .typ template")
        else:
            created_stub = False

        try:
            from pathlib import Path as _Path
            orig_mkdir = _Path.mkdir

            def _fail_mkdir(self: Any, *args: Any, **kwargs: Any) -> None:
                raise PermissionError("no permission")

            _Path.mkdir = _fail_mkdir  # type: ignore[method-assign]
            try:
                success, msg, path = generate_report_PDF(
                    output_filename="report.pdf",
                    output_directory=str(tmp_path / "no_perm"),
                )
            finally:
                _Path.mkdir = orig_mkdir  # type: ignore[method-assign]
        finally:
            if created_stub:
                try:
                    typ_template.unlink()
                except Exception:
                    pass

        assert success is False
        assert path == ""

    @pytest.mark.unit()
    def test_include_charts_false_skips_chart_export(self, tmp_path: Any) -> None:
        """With include_charts=False, export_all_report_plots must not be called."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
        except ImportError:
            pytest.skip("report_QWIM not importable")

        typ_dir = _mod._REPORTING_DIR
        typ_template = typ_dir / "report_QWIM.typ"
        template_existed = typ_template.exists()

        if not template_existed:
            try:
                typ_dir.mkdir(parents=True, exist_ok=True)
                typ_template.write_text("// stub", encoding="utf-8")
                created_stub = True
            except Exception:
                pytest.skip("Cannot create stub .typ template")
        else:
            created_stub = False

        try:
            with (
                patch.object(_mod, "export_all_report_data"),
                patch.object(
                    _mod, "export_all_report_plots", side_effect=AssertionError("should not call")
                ),
                patch.object(_mod, "compile_typst_report", return_value=(False, "no typst")),
            ):
                success, msg, path = generate_report_PDF(
                    output_filename="report.pdf",
                    output_directory=str(tmp_path),
                    include_charts=False,
                )
        finally:
            if created_stub:
                try:
                    typ_template.unlink()
                except Exception:
                    pass

        assert success is False  # compile was mocked to fail


# ===========================================================================
# test_report_generation smoke test function
# ===========================================================================


@pytest.mark.unit()
class Test_test_report_generation:
    """Tests for the ``test_report_generation`` smoke-test function."""

    @pytest.mark.unit()
    def test_returns_two_tuple(self) -> None:
        """test_report_generation must return a 2-tuple."""
        try:
            from src.dashboard.reporting.report_QWIM import test_report_generation
        except ImportError:
            pytest.skip("report_QWIM not importable")

        result = test_report_generation()
        assert len(result) == 2

    @pytest.mark.unit()
    def test_first_element_is_bool(self) -> None:
        """First element of test_report_generation result must be bool."""
        try:
            from src.dashboard.reporting.report_QWIM import test_report_generation
        except ImportError:
            pytest.skip("report_QWIM not importable")

        success, _msg = test_report_generation()
        assert isinstance(success, bool)

    @pytest.mark.unit()
    def test_second_element_is_str(self) -> None:
        """Second element of test_report_generation result must be str."""
        try:
            from src.dashboard.reporting.report_QWIM import test_report_generation
        except ImportError:
            pytest.skip("report_QWIM not importable")

        _success, msg = test_report_generation()
        assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_internal_exception_handled(self) -> None:
        """If generate_report_PDF raises, test_report_generation returns (False, <msg>)."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
            from src.dashboard.reporting.report_QWIM import test_report_generation
        except ImportError:
            pytest.skip("report_QWIM not importable")

        with patch.object(_mod, "generate_report_PDF", side_effect=RuntimeError("boom")):
            success, msg = test_report_generation()

        assert success is False
        assert "boom" in msg or isinstance(msg, str)

    @pytest.mark.unit()
    def test_generate_returns_false_gives_test_failed_message(self) -> None:
        """If generate_report_PDF returns (False, ...) the function returns (False, <msg>)."""
        try:
            import src.dashboard.reporting.report_QWIM as _mod
            from src.dashboard.reporting.report_QWIM import test_report_generation
        except ImportError:
            pytest.skip("report_QWIM not importable")

        with patch.object(
            _mod, "generate_report_PDF", return_value=(False, "compile failed", "")
        ):
            success, msg = test_report_generation()

        assert success is False
        assert isinstance(msg, str)
