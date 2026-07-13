"""Integration tests for traceback_custom."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from src.utils.custom_exceptions_errors_loggers.traceback_custom import (
    Extract_Relevant_Frames,
    Format_Traceback_Compact,
    Format_Traceback_Context,
)


def _capture_exception_info(function_under_test):
    try:
        function_under_test()
    except BaseException:
        return sys.exc_info()
    raise AssertionError("Expected helper to raise an exception")


class Class_Test_Integration_Traceback_Custom:
    """Integration coverage for traceback_custom public helpers."""

    @pytest.mark.integration()
    def Test_compact_formatter_preserves_real_traceback_information(self) -> None:
        """Compact formatting should include real file and exception information."""

        def _raise_nested_error() -> None:
            raise RuntimeError("integration compact")

        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_error)

        text = Format_Traceback_Compact(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb)

        assert "test_integration_traceback_custom.py" in text
        assert text.endswith("RuntimeError: integration compact")

    @pytest.mark.integration()
    def Test_context_formatter_reads_source_context_from_temp_file(self, tmp_path) -> None:
        """Context formatting should include surrounding lines from a real file."""
        source_path = tmp_path / "integration_trace_source.py"
        source_path.write_text(
            "def explode():\n"
            "    marker = 123\n"
            "    raise LookupError('integration context')\n"
            "\n"
            "explode()\n",
            encoding="utf-8",
        )

        code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
        exc_type, exc_value, exc_tb = _capture_exception_info(lambda: exec(code, {}))

        text = Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb, context_lines=1)

        assert f'File "{source_path}"' in text
        assert "marker = 123" in text
        assert ">> " in text
        assert text.endswith("LookupError: integration context")

    @pytest.mark.integration()
    def Test_relevant_frame_extraction_filters_real_tracebacks_by_root(self, tmp_path) -> None:
        """Relevant-frame extraction should keep only frames under the supplied root."""
        inside_root = tmp_path / "inside"
        outside_root = tmp_path / "outside"
        inside_root.mkdir()
        outside_root.mkdir()

        source_path = inside_root / "integration_relevant.py"
        source_path.write_text(
            "def explode():\n"
            "    raise ValueError('relevant frame')\n"
            "\n"
            "explode()\n",
            encoding="utf-8",
        )

        code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
        _, _, exc_tb = _capture_exception_info(lambda: exec(code, {}))

        relevant_frames = Extract_Relevant_Frames(exc_tb = exc_tb, project_root=f"  {inside_root}  ")
        unrelated_frames = Extract_Relevant_Frames(exc_tb = exc_tb, project_root=str(outside_root))

        assert relevant_frames
        assert all(frame.filename.startswith(str(inside_root)) for frame in relevant_frames)
        assert unrelated_frames == []

    @pytest.mark.integration()
    def Test_validation_errors_are_deterministic(self) -> None:
        """Boundary validation should raise stable TypeError and ValueError classes."""
        exc_type, exc_value, exc_tb = _capture_exception_info(lambda: (_ for _ in ()).throw(ValueError("x")))

        with pytest.raises(TypeError, match="context_lines must be an integer"):
            Format_Traceback_Context(
                exc_type = exc_type,
                exc_value = exc_value,
                exc_tb = exc_tb,
                context_lines="2",  # type: ignore[arg-type]
            )

        with pytest.raises(ValueError, match="project_root must be a non-empty string"):
            Extract_Relevant_Frames(exc_tb = exc_tb, project_root="   ")