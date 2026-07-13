"""Unit tests for _import_helpers — 100% line + branch coverage.

Every branch in :mod:`src.utils.data_utils._import_helpers` is exercised by
supplying custom ``_importer`` callables rather than touching ``sys.modules``.
This keeps the test suite isolated and deterministic.

Test class / function naming follows project conventions:
- ``Class_Test_`` prefix for classes
- ``Test_`` prefix for test functions
"""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


# ======================================================================
# try_import_module — success paths
# ======================================================================


@pytest.mark.unit()
class Class_Test_Try_Import_Module_Success:
    """Tests for the success (non-raising) paths of :func:`try_import_module`."""

    def Test_returns_module_when_import_succeeds(self) -> None:
        """Importing a standard-library module must return it (not None)."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "os")
        assert result is not None
        assert isinstance(result, ModuleType)
        assert result.__name__ == "os"

    def Test_returns_same_object_as_sys_modules(self) -> None:
        """The returned module must be the same object already in sys.modules."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "sys")
        assert result is sys

    def Test_custom_importer_used_instead_of_importlib(self) -> None:
        """When ``_importer`` is supplied, it must be called instead of importlib."""
        import os

        from src.utils.data_utils._import_helpers import try_import_module

        called_with: list[str] = []

        def _custom_importer(name: str) -> ModuleType:
            called_with.append(name)
            return os  # return any real module

        result = try_import_module(module_name = "anything", _importer=_custom_importer)
        assert result is os
        assert called_with == ["anything"]

    def Test_standard_importer_returns_polars_when_installed(self) -> None:
        """polars is a project dependency and must be importable."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "polars")
        assert result is not None

    def Test_returns_none_for_nonexistent_module(self) -> None:
        """A module that definitely does not exist must yield None."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "_qwim_does_not_exist_xyz_12345")
        assert result is None

    def Test_none_importer_parameter_falls_back_to_importlib(self) -> None:
        """Explicitly passing ``_importer=None`` must use importlib.import_module."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "os", _importer=None)
        import os

        assert result is os


# ======================================================================
# try_import_module — failure (ImportError) paths
# ======================================================================


@pytest.mark.unit()
class Class_Test_Try_Import_Module_Failure:
    """Tests for the ImportError paths of :func:`try_import_module`."""

    def Test_returns_none_when_importer_raises_import_error(self) -> None:
        """An importer that raises ImportError must cause the function to return None."""
        from src.utils.data_utils._import_helpers import try_import_module

        def _failing_importer(name: str) -> ModuleType:
            raise ImportError(f"forced failure for {name}")

        result = try_import_module(module_name = "some_module", _importer=_failing_importer)
        assert result is None

    def Test_import_error_message_does_not_propagate(self) -> None:
        """No ImportError must escape from try_import_module."""
        from src.utils.data_utils._import_helpers import try_import_module

        def _exploding_importer(name: str) -> ModuleType:
            raise ImportError("boom")

        # Must NOT raise
        result = try_import_module(module_name = "boom_module", _importer=_exploding_importer)
        assert result is None

    def Test_importer_called_with_correct_module_name(self) -> None:
        """The importer must receive the exact module_name string."""
        from src.utils.data_utils._import_helpers import try_import_module

        received: list[str] = []

        def _recording_importer(name: str) -> ModuleType:
            received.append(name)
            raise ImportError

        try_import_module(module_name = "target.module.name", _importer=_recording_importer)
        assert received == ["target.module.name"]

    def Test_standard_path_returns_none_for_bogus_module(self) -> None:
        """Using the default importlib path with a non-existent module returns None."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = "totally_fake_module_abcdef_9876", _importer=None)
        assert result is None

    @pytest.mark.parametrize(
        "module_name",
        [
            "_qwim_fake_1",
            "_qwim_fake_2",
            "does.not.exist.at.all",
        ],
    )
    def Test_multiple_bogus_modules_all_return_none(self, module_name: str) -> None:
        """Every call with a non-existent module name must return None."""
        from src.utils.data_utils._import_helpers import try_import_module

        assert try_import_module(module_name = module_name) is None


# ======================================================================
# try_import_module — non-ImportError exceptions must propagate
# ======================================================================


@pytest.mark.unit()
class Class_Test_Try_Import_Module_Other_Exceptions:
    """Non-ImportError exceptions from the importer must not be silenced."""

    def Test_value_error_propagates(self) -> None:
        """A ValueError from the importer must NOT be caught."""
        from src.utils.data_utils._import_helpers import try_import_module

        def _bad_importer(name: str) -> ModuleType:
            raise ValueError("unexpected error in importer")

        with pytest.raises(ValueError, match="unexpected error"):
            try_import_module(module_name = "any_name", _importer=_bad_importer)

    def Test_runtime_error_propagates(self) -> None:
        """A RuntimeError from the importer must NOT be caught."""
        from src.utils.data_utils._import_helpers import try_import_module

        def _bad_importer(name: str) -> ModuleType:
            raise RuntimeError("runtime boom")

        with pytest.raises(RuntimeError, match="runtime boom"):
            try_import_module(module_name = "any_name", _importer=_bad_importer)


@pytest.mark.unit()
class Class_Test_Try_Import_Module_Input_Validation:
    """Input-validation tests for :func:`try_import_module`."""

    def Test_raises_type_error_for_non_string_module_name(self) -> None:
        """Non-string module names are rejected with TypeError."""
        from src.utils.data_utils._import_helpers import try_import_module

        with pytest.raises(TypeError, match="module_name must be a string"):
            try_import_module(module_name = 123)  # type: ignore[arg-type]

    def Test_raises_value_error_for_blank_module_name(self) -> None:
        """Blank module names are rejected with ValueError."""
        from src.utils.data_utils._import_helpers import try_import_module

        with pytest.raises(ValueError, match="module_name must be a non-empty string"):
            try_import_module(module_name = "   ")

    def Test_strips_surrounding_whitespace_before_import(self) -> None:
        """Leading/trailing whitespace is removed before dispatch to importer."""
        from src.utils.data_utils._import_helpers import try_import_module

        received: list[str] = []

        def _recording_importer(name: str) -> ModuleType:
            received.append(name)
            return sys

        result = try_import_module(module_name = "  sys  ", _importer=_recording_importer)

        assert result is sys
        assert received == ["sys"]

    def Test_raises_type_error_for_non_callable_importer(self) -> None:
        """Non-callable importer objects are rejected with TypeError."""
        from src.utils.data_utils._import_helpers import try_import_module

        with pytest.raises(TypeError, match="_importer must be callable"):
            try_import_module(module_name = "os", _importer="not-callable")  # type: ignore[arg-type]
