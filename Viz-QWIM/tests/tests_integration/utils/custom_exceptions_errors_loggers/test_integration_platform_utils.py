"""Integration tests for platform_utils."""

from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace

import pytest

from src.utils.custom_exceptions_errors_loggers.platform_utils import (
    get_platform,
    is_linux,
    is_macos,
    is_windows,
    seed_uname_cache_for_windows,
)


def _make_fake_platform_module(*, uname_cache=None):
    """Return a lightweight stand-in for the platform module."""
    fake_uname = namedtuple(
        "Fake_Uname", ["system", "node", "release", "version", "machine"]
    )
    return SimpleNamespace(_uname_cache=uname_cache, uname_result=fake_uname)


class Class_Test_Integration_Platform_Utils:
    """Integration coverage for platform_utils public API."""

    @pytest.mark.integration()
    def Test_platform_seed_normalization_flows_through_all_predicates(self) -> None:
        """Whitespace-normalized seeds should drive predicate behavior consistently."""
        assert get_platform(_sys_platform="  linux  ") == "linux"
        assert is_linux(_sys_platform="  linux  ") is True
        assert is_windows(_sys_platform="  linux  ") is False
        assert is_macos(_sys_platform="  linux  ") is False

    @pytest.mark.integration()
    def Test_invalid_platform_seeds_raise_deterministic_errors(self) -> None:
        """Public predicates should reject invalid seeds uniformly."""
        with pytest.raises(TypeError, match="string or None"):
            get_platform(_sys_platform=123)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="non-empty string"):
            is_linux(_sys_platform="   ")

    @pytest.mark.integration()
    def Test_windows_cache_seed_uses_architecture_mapping(self) -> None:
        """Windows cache seeding should map X86 to x86 and stamp the uname cache."""
        fake_platform = _make_fake_platform_module()

        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "X86", "COMPUTERNAME": "PC1"},
            _platform_module=fake_platform,
        )

        assert result == "x86"
        assert fake_platform._uname_cache.machine == "x86"
        assert fake_platform._uname_cache.node == "PC1"

    @pytest.mark.integration()
    def Test_non_windows_seed_is_a_safe_no_op(self) -> None:
        """Non-Windows seeds should leave the target platform module untouched."""
        fake_platform = _make_fake_platform_module()

        result = seed_uname_cache_for_windows(
            _sys_platform="linux",
            _platform_module=fake_platform,
        )

        assert result is None
        assert fake_platform._uname_cache is None