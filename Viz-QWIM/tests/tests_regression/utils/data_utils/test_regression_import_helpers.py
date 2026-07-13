"""Regression tests for _import_helpers validation and normalization behavior."""

from __future__ import annotations

import sys

import pytest

from src.utils.data_utils._import_helpers import try_import_module


class Class_Test_Regression_Import_Helpers:
    """Regression baselines for try_import_module behavior."""

    @pytest.mark.regression()
    def Test_blank_module_name_message_baseline(self) -> None:
        """Blank-name error message remains stable."""
        with pytest.raises(ValueError) as error_info:
            try_import_module(module_name = "   ")

        assert str(error_info.value) == "module_name must be a non-empty string"

    @pytest.mark.regression()
    def Test_non_string_module_name_message_baseline(self) -> None:
        """Non-string name TypeError message remains stable."""
        with pytest.raises(TypeError) as error_info:
            try_import_module(module_name = 123)  # type: ignore[arg-type]

        assert str(error_info.value) == "module_name must be a string"

    @pytest.mark.regression()
    def Test_non_callable_importer_message_baseline(self) -> None:
        """Non-callable importer TypeError message remains stable."""
        with pytest.raises(TypeError) as error_info:
            try_import_module(module_name = "os", _importer="bad")  # type: ignore[arg-type]

        assert str(error_info.value) == "_importer must be callable"

    @pytest.mark.regression()
    def Test_normalized_name_forwarded_baseline(self) -> None:
        """Whitespace-normalized names are forwarded unchanged to importer."""
        received: list[str] = []

        def _recording_importer(module_name: str):
            received.append(module_name)
            return sys

        result = try_import_module(module_name = "  sys  ", _importer=_recording_importer)

        assert result is sys
        assert received == ["sys"]