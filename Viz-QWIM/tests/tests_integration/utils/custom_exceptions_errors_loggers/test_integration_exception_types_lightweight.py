"""Integration tests for _exception_types_lightweight masking helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    _Mask_Sensitive_Data,
    _Serialize_For_JSON,
)


class Class_Test_Integration_Exception_Types_Lightweight:
    """Integration coverage for masking plus JSON serialization helpers."""

    @pytest.mark.integration()
    def Test_mask_sensitive_data_preserves_non_string_keys_through_json_serialization(
        self,
    ) -> None:
        """Masked data with non-string keys should remain serializable for JSON output."""
        data = {
            101: "kept",
            "nested": {202: Path("portfolio.csv"), "api_key": "token-value"},
        }

        masked = _Mask_Sensitive_Data(data = data)
        payload = json.loads(json.dumps(masked, default=_Serialize_For_JSON))

        assert payload["101"] == "kept"
        assert payload["nested"]["202"] == "portfolio.csv"
        assert payload["nested"]["api_key"] == "***MASKED***"

    @pytest.mark.integration()
    def Test_mask_sensitive_data_handles_nested_mixed_key_types(self) -> None:
        """Nested dictionaries should preserve non-string keys at every level."""
        data = {0: "root", "nested": {1: "child", "password": "secret"}}

        masked = _Mask_Sensitive_Data(data = data)

        assert masked[0] == "root"
        assert masked["nested"][1] == "child"
        assert masked["nested"]["password"] == "***MASKED***"