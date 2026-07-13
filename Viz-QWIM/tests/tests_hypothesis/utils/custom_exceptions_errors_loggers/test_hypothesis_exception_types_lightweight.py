"""Hypothesis tests for _exception_types_lightweight masking helpers."""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    _Mask_Sensitive_Data,
)


class Class_Test_Hypothesis_Exception_Types_Lightweight:
    """Property-based tests for lightweight exception helper masking."""

    @pytest.mark.unit()
    @given(
        top_key=st.integers(),
        nested_key=st.integers(),
        top_value=st.text(max_size=20),
        nested_value=st.text(max_size=20),
    )
    @settings(max_examples=35)
    def Test_mask_sensitive_data_preserves_non_string_keys(
        self,
        top_key: int,
        nested_key: int,
        top_value: str,
        nested_value: str,
    ) -> None:
        """Masking should preserve non-string keys while masking sensitive string keys."""
        data = {
            top_key: top_value,
            "nested": {nested_key: nested_value, "password": "secret"},
        }

        result = _Mask_Sensitive_Data(data = data)

        assert result[top_key] == top_value
        assert result["nested"][nested_key] == nested_value
        assert result["nested"]["password"] == "***MASKED***"