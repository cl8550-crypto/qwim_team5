"""Integration tests for _exception_core pickle reconstruction."""

from __future__ import annotations

import pickle

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Custom,
    Exception_Data_Validation_Error,
    Exception_Format,
    Exception_Severity,
)


class Class_Test_Integration_Exception_Core:
    """Integration coverage for Exception_Custom reconstruction."""

    @pytest.mark.integration()
    def Test_exception_custom_pickle_roundtrip_preserves_base_detail_contract(self) -> None:
        """Round-tripped Exception_Custom instances should still expose detail == {}."""
        original = Exception_Custom(
            "pickle me",
            context={"portfolio": "balanced"},
            exception_format=Exception_Format.JSON,
            severity=Exception_Severity.CRITICAL,
        )

        restored = pickle.loads(pickle.dumps(original))

        assert restored.detail == {}
        assert restored._user_context == {"portfolio": "balanced"}
        assert restored.Exception_Format_Value == Exception_Format.JSON
        assert restored.Severity == Exception_Severity.CRITICAL

    @pytest.mark.integration()
    def Test_data_validation_error_pickle_roundtrip_preserves_detail_payload(self) -> None:
        """Subclass round-trips should continue to preserve their detail payload."""
        original = Exception_Data_Validation_Error(
            "bad input",
            field="weight",
            value=1.5,
        )

        restored = pickle.loads(pickle.dumps(original))

        assert restored.detail == {"field": "weight", "value": 1.5}
        assert restored.field == "weight"
        assert restored.value == 1.5