"""Regression tests for _exception_types_lightweight masking helpers."""

from __future__ import annotations

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    _Mask_Sensitive_Data,
)


class Class_Test_Regression_Exception_Types_Lightweight:
    """Regression baselines for non-string-key masking behavior."""

    @pytest.mark.regression()
    def Test_non_string_key_masking_baseline(self) -> None:
        """Non-string keys should be preserved exactly while password fields are masked."""
        data = {123: "ok", "nested": {456: "still ok", "password": "secret"}}

        result = _Mask_Sensitive_Data(data = data)

        assert result == {123: "ok", "nested": {456: "still ok", "password": "***MASKED***"}}

    @pytest.mark.regression()
    def Test_non_string_top_level_sensitive_name_string_still_masks(self) -> None:
        """String keys that look sensitive should still be masked beside non-string keys."""
        data = {789: "safe", "token": "abc123"}

        result = _Mask_Sensitive_Data(data = data)

        assert result[789] == "safe"
        assert result["token"] == "***MASKED***"