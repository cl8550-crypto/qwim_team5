"""Integration tests for _import_helpers module."""

from __future__ import annotations

from types import ModuleType

import pytest

from src.utils.data_utils._import_helpers import try_import_module


class Class_Test_Integration_Import_Helpers:
    """Integration tests for real import behavior and validation boundaries."""

    @pytest.mark.integration()
    def Test_imports_standard_library_modules(self) -> None:
        """Known standard-library modules resolve to module objects."""
        for module_name in ["os", "sys", "json"]:
            result = try_import_module(module_name = module_name)
            assert result is not None
            assert isinstance(result, ModuleType)
            assert result.__name__ == module_name

    @pytest.mark.integration()
    def Test_whitespace_module_name_is_normalized(self) -> None:
        """Whitespace around a valid name is stripped before import."""
        result = try_import_module(module_name = "  json  ")
        assert result is not None
        assert result.__name__ == "json"

    @pytest.mark.integration()
    def Test_missing_module_returns_none(self) -> None:
        """Missing modules return None instead of raising ImportError."""
        result = try_import_module(module_name = "_qwim_missing_module_xyz_9876")
        assert result is None

    @pytest.mark.integration()
    def Test_invalid_inputs_raise_boundary_errors(self) -> None:
        """Invalid boundaries raise deterministic TypeError/ValueError."""
        with pytest.raises(TypeError, match="module_name must be a string"):
            try_import_module(module_name = 42)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="non-empty string"):
            try_import_module(module_name = "   ")

        with pytest.raises(TypeError, match="_importer must be callable"):
            try_import_module(module_name = "os", _importer="not-callable")  # type: ignore[arg-type]