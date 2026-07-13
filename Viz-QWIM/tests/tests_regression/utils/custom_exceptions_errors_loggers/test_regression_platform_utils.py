"""Regression tests for platform_utils validation and mapping behavior."""

from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace

import pytest

from src.utils.custom_exceptions_errors_loggers.platform_utils import (
    get_platform,
    seed_uname_cache_for_windows,
)


def _make_fake_platform_module(*, uname_cache=None):
    """Return a lightweight stand-in for the platform module."""
    fake_uname = namedtuple(
        "Fake_Uname", ["system", "node", "release", "version", "machine"]
    )
    return SimpleNamespace(_uname_cache=uname_cache, uname_result=fake_uname)


class Class_Test_Regression_Platform_Utils:
    """Regression baselines for platform_utils public behavior."""

    @pytest.mark.regression()
    def Test_non_string_seed_error_message_baseline(self) -> None:
        """TypeError text for non-string seeds should remain stable."""
        with pytest.raises(TypeError) as error_info:
            get_platform(_sys_platform=123)  # type: ignore[arg-type]

        assert str(error_info.value) == "_sys_platform must be a string or None"

    @pytest.mark.regression()
    def Test_blank_seed_error_message_baseline(self) -> None:
        """ValueError text for blank seeds should remain stable."""
        with pytest.raises(ValueError) as error_info:
            get_platform(_sys_platform="   ")

        assert str(error_info.value) == "_sys_platform must be a non-empty string when provided"

    @pytest.mark.regression()
    def Test_architecture_precedence_baseline(self) -> None:
        """PROCESSOR_ARCHITEW6432 should continue to take precedence."""
        fake_platform = _make_fake_platform_module()

        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={
                "PROCESSOR_ARCHITEW6432": "ARM64",
                "PROCESSOR_ARCHITECTURE": "X86",
            },
            _platform_module=fake_platform,
        )

        assert result == "ARM64"
        assert fake_platform._uname_cache.machine == "ARM64"

    @pytest.mark.regression()
    def Test_unknown_architecture_passthrough_baseline(self) -> None:
        """Unknown architecture strings should keep passthrough behavior."""
        fake_platform = _make_fake_platform_module()

        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "RISCV64"},
            _platform_module=fake_platform,
        )

        assert result == "RISCV64"
        assert fake_platform._uname_cache.machine == "RISCV64"