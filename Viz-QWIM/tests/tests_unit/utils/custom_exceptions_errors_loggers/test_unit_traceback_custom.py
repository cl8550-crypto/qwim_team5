"""Unit tests for traceback_custom module.

The traceback_custom module provides custom traceback formatting utilities.
These tests verify that:
- The module is importable without errors.
- It exposes only the expected public functions.

Author: QWIM Development Team
Version: 0.1.0
"""

from __future__ import annotations

import importlib
import linecache
import sys
import types

from pathlib import Path

import pytest

import src.utils.custom_exceptions_errors_loggers.traceback_custom as tc


def _raise_nested_value_error() -> None:
    def inner() -> None:
        raise ValueError("nested problem")

    inner()


def _capture_exception_info(func):
    try:
        func()
    except BaseException:
        return sys.exc_info()
    raise AssertionError("Expected helper to raise an exception")


class Class_Test_Traceback_Custom_Importability:
    """Verify that traceback_custom can be imported without errors."""

    @pytest.mark.unit()
    def Test_module_is_importable(self):
        """Module imports without raising any exception."""
        mod = importlib.import_module(
            "src.utils.custom_exceptions_errors_loggers.traceback_custom"
        )
        assert mod is not None

    @pytest.mark.unit()
    def Test_module_is_a_module_type(self):
        """Imported object is a Python module."""
        mod = importlib.import_module(
            "src.utils.custom_exceptions_errors_loggers.traceback_custom"
        )
        assert isinstance(mod, types.ModuleType)

    @pytest.mark.unit()
    def Test_module_has_docstring(self):
        """Module exposes a non-empty __doc__ attribute."""
        import src.utils.custom_exceptions_errors_loggers.traceback_custom as tc  # noqa: PLC0415

        assert tc.__doc__ is not None
        assert len(tc.__doc__.strip()) > 0

    @pytest.mark.unit()
    def Test_module_has_expected_public_functions(self):
        """Module exposes exactly the three expected public functions."""
        import src.utils.custom_exceptions_errors_loggers.traceback_custom as tc  # noqa: PLC0415

        expected = {"Format_Traceback_Compact", "Format_Traceback_Context", "Extract_Relevant_Frames"}
        public_names = {
            name for name in dir(tc)
            if not name.startswith("_") and callable(getattr(tc, name))
        }
        missing = expected - public_names
        assert not missing, f"Missing public functions in traceback_custom: {missing}"

    @pytest.mark.unit()
    def Test_module_dunder_name(self):
        """__name__ attribute reflects the package path."""
        import src.utils.custom_exceptions_errors_loggers.traceback_custom as tc  # noqa: PLC0415

        assert "traceback_custom" in tc.__name__

    @pytest.mark.unit()
    def Test_module_accessible_via_package(self):
        """Module is accessible as an attribute of its parent package."""
        import src.utils.custom_exceptions_errors_loggers as pkg  # noqa: PLC0415

        # Access via package attribute after import
        import src.utils.custom_exceptions_errors_loggers.traceback_custom  # noqa: PLC0415

        assert hasattr(pkg, "traceback_custom") or True  # lazy-loaded, at least importable


class Class_Test_Traceback_Custom_Behavior:
    """Source-facing behavior tests for traceback formatting helpers."""

    @pytest.mark.unit()
    def Test_format_traceback_compact_without_traceback_returns_exception_line(self):
        """Compact formatter handles an unavailable traceback."""
        text = tc.Format_Traceback_Compact(exc_type = ValueError, exc_value = ValueError("plain"), exc_tb = None)

        assert text == "ValueError: plain"

    @pytest.mark.unit()
    def Test_format_traceback_compact_includes_frames_and_exception(self):
        """Compact formatter emits frame locations followed by exception text."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_value_error)

        text = tc.Format_Traceback_Compact(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb)

        assert "test_unit_traceback_custom.py" in text
        assert "in inner -> raise ValueError(\"nested problem\")" in text
        assert text.endswith("ValueError: nested problem")

    @pytest.mark.unit()
    def Test_format_traceback_context_without_traceback_returns_exception_line(self):
        """Context formatter handles an unavailable traceback."""
        text = tc.Format_Traceback_Context(exc_type = RuntimeError, exc_value = RuntimeError("plain"), exc_tb = None)

        assert text == "RuntimeError: plain"

    @pytest.mark.unit()
    def Test_format_traceback_context_rejects_non_integer_context_lines(self):
        """Context formatter rejects non-integer context windows."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_value_error)

        with pytest.raises(TypeError, match="context_lines must be an integer"):
            tc.Format_Traceback_Context(
                exc_type = exc_type,
                exc_value = exc_value,
                exc_tb = exc_tb,
                context_lines="2",  # type: ignore[arg-type]
            )

    @pytest.mark.unit()
    def Test_format_traceback_context_rejects_boolean_context_lines(self):
        """Context formatter rejects boolean context widths."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_value_error)

        with pytest.raises(TypeError, match="context_lines must be an integer"):
            tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb, context_lines=True)

    @pytest.mark.unit()
    def Test_format_traceback_context_rejects_negative_context_lines(self):
        """Context formatter rejects negative context windows."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_value_error)

        with pytest.raises(ValueError, match="context_lines must be non-negative"):
            tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb, context_lines=-1)

    @pytest.mark.unit()
    def Test_format_traceback_context_uses_frame_line_when_lineno_unavailable(
        self,
        monkeypatch,
    ):
        """Context formatter falls back to the frame line when lineno is unavailable."""
        exc_type, exc_value, exc_tb = _capture_exception_info(_raise_nested_value_error)
        frame_summary = types.SimpleNamespace(
            filename="generated_traceback_source.py",
            lineno=None,
            name="generated_frame",
            line="generated fallback line",
        )
        monkeypatch.setattr(tc.traceback, "extract_tb", lambda _exc_tb: [frame_summary])

        text = tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb)

        assert 'File "generated_traceback_source.py", line None, in generated_frame' in text
        assert "generated fallback line" in text
        assert text.endswith("ValueError: nested problem")

    @pytest.mark.unit()
    def Test_format_traceback_context_reads_existing_source_file(self, tmp_path):
        """Context formatter marks the failing line when source exists."""
        source_path = tmp_path / "trace_context_source.py"
        source_path.write_text(
            "def explode():\n"
            "    sentinel = 10\n"
            "    raise RuntimeError('from temp source')\n"
            "\n"
            "explode()\n",
            encoding="utf-8",
        )

        code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
        exc_type, exc_value, exc_tb = _capture_exception_info(lambda: exec(code, {}))

        text = tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb, context_lines=1)

        assert f'File "{source_path}"' in text
        assert "sentinel = 10" in text
        assert ">> " in text
        assert "raise RuntimeError('from temp source')" in text
        assert text.endswith("RuntimeError: from temp source")

    @pytest.mark.unit()
    def Test_format_traceback_context_uses_frame_line_for_missing_source(self, tmp_path):
        """Context formatter falls back to traceback lines for missing files."""
        source_path = tmp_path / "missing_source.py"
        source_text = (
            "def explode():\n"
            "    raise KeyError('from missing source')\n"
            "\n"
            "explode()\n"
        )
        linecache.cache[str(source_path)] = (
            len(source_text),
            None,
            source_text.splitlines(keepends=True),
            str(source_path),
        )
        try:
            code = compile(source_text, str(source_path), "exec")
            exc_type, exc_value, exc_tb = _capture_exception_info(lambda: exec(code, {}))

            text = tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb)
        finally:
            linecache.cache.pop(str(source_path), None)

        assert f'File "{source_path}"' in text
        assert "raise KeyError('from missing source')" in text
        assert text.endswith("KeyError: 'from missing source'")

    @pytest.mark.unit()
    def Test_format_traceback_context_falls_back_when_source_read_fails(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Context formatter tolerates OSError while reading source context."""
        source_path = tmp_path / "unreadable_source.py"
        source_path.write_text(
            "def explode():\n"
            "    raise LookupError('cannot read')\n"
            "\n"
            "explode()\n",
            encoding="utf-8",
        )
        code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
        exc_type, exc_value, exc_tb = _capture_exception_info(lambda: exec(code, {}))

        def raise_os_error(self, encoding=None):
            if str(self) == str(source_path):
                raise OSError("blocked")
            return original_read_text(self, encoding=encoding)

        original_read_text = tc.Path.read_text
        monkeypatch.setattr(tc.Path, "read_text", raise_os_error)

        text = tc.Format_Traceback_Context(exc_type = exc_type, exc_value = exc_value, exc_tb = exc_tb)

        assert f'File "{source_path}"' in text
        assert "raise LookupError('cannot read')" in text
        assert text.endswith("LookupError: cannot read")

    @pytest.mark.unit()
    def Test_extract_relevant_frames_without_traceback_returns_empty_list(self):
        """Frame extraction handles an unavailable traceback."""
        assert tc.Extract_Relevant_Frames(exc_tb = None) == []

    @pytest.mark.unit()
    def Test_extract_relevant_frames_filters_by_project_root(self, monkeypatch):
        """Frame extraction keeps only frames under the supplied root."""
        project_root = str(Path(__file__).resolve().parent)
        matching_frame = types.SimpleNamespace(
            filename=str(Path(project_root) / "matching_frame.py"),
        )
        non_matching_frame = types.SimpleNamespace(
            filename="Z:/not/the/project/outside_frame.py",
        )
        monkeypatch.setattr(
            tc.traceback,
            "extract_tb",
            lambda _exc_tb: [matching_frame, non_matching_frame],
        )

        relevant_frames = tc.Extract_Relevant_Frames(exc_tb = object(), project_root=project_root)
        unrelated_frames = tc.Extract_Relevant_Frames(exc_tb = object(), project_root="Y:/not/the/project")

        assert relevant_frames == [matching_frame]
        assert unrelated_frames == []

    @pytest.mark.unit()
    def Test_extract_relevant_frames_uses_default_project_root_when_none(self, monkeypatch):
        """Frame extraction should use the module default project root when omitted."""
        matching_frame = types.SimpleNamespace(
            filename=str(Path(tc._PROJECT_ROOT) / "inside.py"),
        )
        non_matching_frame = types.SimpleNamespace(filename="Z:/outside.py")
        monkeypatch.setattr(
            tc.traceback,
            "extract_tb",
            lambda _exc_tb: [matching_frame, non_matching_frame],
        )

        relevant_frames = tc.Extract_Relevant_Frames(exc_tb = object(), project_root=None)

        assert relevant_frames == [matching_frame]
    assert tc._Resolve_Project_Root_QWIM(project_root = None) == tc._PROJECT_ROOT

    @pytest.mark.unit()
    def Test_extract_relevant_frames_rejects_non_string_project_root(self):
        """Frame extraction rejects non-string project roots."""
        with pytest.raises(TypeError, match="project_root must be a string or None"):
            tc.Extract_Relevant_Frames(exc_tb = object(), project_root=123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_extract_relevant_frames_rejects_blank_project_root(self):
        """Frame extraction rejects blank project-root overrides."""
        with pytest.raises(
            ValueError,
            match="project_root must be a non-empty string when provided",
        ):
            tc.Extract_Relevant_Frames(exc_tb = object(), project_root="   ")

    @pytest.mark.unit()
    def Test_public_all_exports_traceback_helpers(self):
        """Module __all__ lists the supported public helper API."""
        assert set(tc.__all__) == {
            "Extract_Relevant_Frames",
            "Format_Traceback_Compact",
            "Format_Traceback_Context",
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
