"""Unit tests for platform_utils â€” 100% line + branch coverage.

Every branch in :mod:`src.utils.custom_exceptions_errors_loggers.platform_utils`
is exercised by injecting known ``_sys_platform`` strings instead of relying on
the real ``sys.platform`` value.  This makes the suite deterministic on both
Windows (CI and dev) and Linux (Posit Connect deployment).

Test class / function naming follows project conventions:
- ``Class_Test_`` prefix for classes
- ``Test_`` prefix for test functions
"""

from __future__ import annotations

import sys

import pytest


# ======================================================================
# get_platform
# ======================================================================


@pytest.mark.unit()
class Class_Test_Get_Platform:
    """Tests for :func:`platform_utils.get_platform`."""

    def Test_returns_win32_when_seeded(self) -> None:
        """Seeding 'win32' must be returned verbatim."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform="win32") == "win32"

    def Test_returns_linux_when_seeded(self) -> None:
        """Seeding 'linux' must be returned verbatim."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform="linux") == "linux"

    def Test_returns_darwin_when_seeded(self) -> None:
        """Seeding 'darwin' must be returned verbatim."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform="darwin") == "darwin"

    def Test_raises_value_error_when_seeded_empty(self) -> None:
        """Blank platform seeds are rejected with ValueError."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        with pytest.raises(
            ValueError, match="_sys_platform must be a non-empty string when provided"
        ):
            get_platform(_sys_platform="")

    def Test_strips_whitespace_from_seeded_platform(self) -> None:
        """Whitespace around a seed must be normalized before use."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform="  linux  ") == "linux"

    def Test_raises_type_error_for_non_string_seed(self) -> None:
        """Non-string seeds are rejected with TypeError."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        with pytest.raises(TypeError, match="_sys_platform must be a string or None"):
            get_platform(_sys_platform=123)  # type: ignore[arg-type]

    def Test_no_seed_returns_real_sys_platform(self) -> None:
        """Without a seed the function must delegate to ``sys.platform``."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform() == sys.platform

    def Test_none_seed_returns_real_sys_platform(self) -> None:
        """Explicitly passing ``None`` must behave the same as omitting the arg."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform=None) == sys.platform


# ======================================================================
# is_windows
# ======================================================================


@pytest.mark.unit()
class Class_Test_Is_Windows:
    """Tests for :func:`platform_utils.is_windows`."""

    def Test_returns_true_when_seeded_win32(self) -> None:
        """Seeding 'win32' must return True."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        assert is_windows(_sys_platform="win32") is True

    def Test_returns_false_when_seeded_linux(self) -> None:
        """Seeding 'linux' must return False."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        assert is_windows(_sys_platform="linux") is False

    def Test_returns_false_when_seeded_darwin(self) -> None:
        """Seeding 'darwin' must return False."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        assert is_windows(_sys_platform="darwin") is False

    def Test_returns_false_when_seeded_linux2(self) -> None:
        """'linux2' (older Python builds) must not be treated as Windows."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        assert is_windows(_sys_platform="linux2") is False

    def Test_no_seed_matches_real_platform(self) -> None:
        """Without a seed the result must reflect the actual platform."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        expected = sys.platform == "win32"
        assert is_windows() is expected

    def Test_none_seed_matches_real_platform(self) -> None:
        """Explicitly passing None must behave the same as omitting the arg."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_windows

        expected = sys.platform == "win32"
        assert is_windows(_sys_platform=None) is expected


# ======================================================================
# is_linux
# ======================================================================


@pytest.mark.unit()
class Class_Test_Is_Linux:
    """Tests for :func:`platform_utils.is_linux`."""

    def Test_returns_true_when_seeded_linux(self) -> None:
        """'linux' must be recognised as Linux."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_linux

        assert is_linux(_sys_platform="linux") is True

    def Test_returns_true_when_seeded_linux2(self) -> None:
        """'linux2' (older builds) must also be recognised as Linux."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_linux

        assert is_linux(_sys_platform="linux2") is True

    def Test_returns_false_when_seeded_win32(self) -> None:
        """Windows must not be recognised as Linux."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_linux

        assert is_linux(_sys_platform="win32") is False

    def Test_returns_false_when_seeded_darwin(self) -> None:
        """macOS must not be recognised as Linux."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_linux

        assert is_linux(_sys_platform="darwin") is False

    def Test_no_seed_matches_real_platform(self) -> None:
        """Without a seed the result must reflect the actual platform."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_linux

        expected = sys.platform.startswith("linux")
        assert is_linux() is expected


# ======================================================================
# is_macos
# ======================================================================


@pytest.mark.unit()
class Class_Test_Is_Macos:
    """Tests for :func:`platform_utils.is_macos`."""

    def Test_returns_true_when_seeded_darwin(self) -> None:
        """'darwin' must be recognised as macOS."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_macos

        assert is_macos(_sys_platform="darwin") is True

    def Test_returns_false_when_seeded_win32(self) -> None:
        """Windows must not be recognised as macOS."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_macos

        assert is_macos(_sys_platform="win32") is False

    def Test_returns_false_when_seeded_linux(self) -> None:
        """Linux must not be recognised as macOS."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_macos

        assert is_macos(_sys_platform="linux") is False

    def Test_no_seed_matches_real_platform(self) -> None:
        """Without a seed the result must reflect the actual platform."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import is_macos

        expected = sys.platform == "darwin"
        assert is_macos() is expected


# ======================================================================
# Parametric cross-function consistency
# ======================================================================


@pytest.mark.unit()
class Class_Test_Platform_Utils_Consistency:
    """Cross-function invariants that must hold regardless of platform."""

    @pytest.mark.parametrize(
        "platform_str",
        ["win32", "linux", "linux2", "darwin", "freebsd13"],
    )
    def Test_exactly_one_or_zero_platform_fns_return_true(
        self, platform_str: str
    ) -> None:
        """At most one of is_windows/is_linux/is_macos should be True for any platform."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            is_linux,
            is_macos,
            is_windows,
        )

        results = [
            is_windows(_sys_platform=platform_str),
            is_linux(_sys_platform=platform_str),
            is_macos(_sys_platform=platform_str),
        ]
        assert sum(results) <= 1, (
            f"Multiple platform functions returned True for {platform_str!r}: {results}"
        )

    @pytest.mark.parametrize(
        "platform_str",
        ["win32", "linux", "darwin"],
    )
    def Test_get_platform_round_trips(self, platform_str: str) -> None:
        """get_platform(_sys_platform=X) must equal X."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform=platform_str) == platform_str

    def Test_invalid_seed_type_is_rejected_consistently(self) -> None:
        """All public platform predicates should reject non-string seeds."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            get_platform,
            is_linux,
            is_macos,
            is_windows,
        )

        for function_under_test in [get_platform, is_windows, is_linux, is_macos]:
            with pytest.raises(TypeError, match="_sys_platform must be a string or None"):
                function_under_test(_sys_platform=object())  # type: ignore[arg-type]

    def Test_blank_seed_is_rejected_consistently(self) -> None:
        """All public platform predicates should reject blank seeds."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            get_platform,
            is_linux,
            is_macos,
            is_windows,
        )

        for function_under_test in [get_platform, is_windows, is_linux, is_macos]:
            with pytest.raises(
                ValueError,
                match="_sys_platform must be a non-empty string when provided",
            ):
                function_under_test(_sys_platform="   ")


# ======================================================================
# seed_uname_cache_for_windows
# ======================================================================


def _make_fake_platform_module(*, uname_cache=None):
    """Build a stand-in for the :mod:`platform` module.

    The returned object exposes the two attributes consumed by
    :func:`seed_uname_cache_for_windows`: a mutable ``_uname_cache`` slot and a
    ``uname_result`` factory.  Using a fake avoids mutating the real
    interpreter-global :mod:`platform` state inside unit tests.
    """
    from collections import namedtuple
    from types import SimpleNamespace

    Fake_Uname = namedtuple(
        "Fake_Uname", ["system", "node", "release", "version", "machine"]
    )
    return SimpleNamespace(_uname_cache=uname_cache, uname_result=Fake_Uname)


@pytest.mark.unit()
class Class_Test_Seed_Uname_Cache_For_Windows:
    """Tests for :func:`platform_utils.seed_uname_cache_for_windows`."""

    def Test_no_op_on_linux_returns_none(self) -> None:
        """On Linux the function must be a no-op and return None."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="linux",
            _platform_module=fake_platform,
        )
        assert result is None
        assert fake_platform._uname_cache is None

    def Test_no_op_on_macos_returns_none(self) -> None:
        """On macOS the function must be a no-op and return None."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="darwin",
            _platform_module=fake_platform,
        )
        assert result is None

    def Test_already_seeded_cache_is_left_untouched(self) -> None:
        """A populated cache must not be overwritten when ``_force`` is False."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        sentinel = object()
        fake_platform = _make_fake_platform_module(uname_cache=sentinel)
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _platform_module=fake_platform,
        )
        assert result is None
        assert fake_platform._uname_cache is sentinel

    def Test_force_reseeds_even_when_cache_present(self) -> None:
        """``_force=True`` must re-seed even if the cache is already populated."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module(uname_cache=object())
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "AMD64", "COMPUTERNAME": "PC1"},
            _platform_module=fake_platform,
            _force=True,
        )
        assert result == "AMD64"
        assert fake_platform._uname_cache.machine == "AMD64"
        assert fake_platform._uname_cache.node == "PC1"

    def Test_architew6432_takes_precedence(self) -> None:
        """``PROCESSOR_ARCHITEW6432`` must win over ``PROCESSOR_ARCHITECTURE``."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

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

    def Test_falls_back_to_processor_architecture(self) -> None:
        """With no ARCHITEW6432, ``PROCESSOR_ARCHITECTURE`` must be used."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "X86"},
            _platform_module=fake_platform,
        )
        assert result == "x86"
        assert fake_platform._uname_cache.machine == "x86"

    def Test_defaults_to_amd64_when_no_env(self) -> None:
        """With an empty environment the machine must default to ``AMD64``."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={},
            _platform_module=fake_platform,
        )
        assert result == "AMD64"
        assert fake_platform._uname_cache.node == "localhost"

    def Test_unknown_architecture_is_passed_through(self) -> None:
        """An unmapped architecture string must be returned unchanged."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "RISCV64"},
            _platform_module=fake_platform,
        )
        assert result == "RISCV64"
        assert fake_platform._uname_cache.machine == "RISCV64"

    def Test_lowercase_architecture_is_normalised(self) -> None:
        """A lowercase architecture must be upper-cased before mapping."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        result = seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "amd64"},
            _platform_module=fake_platform,
        )
        assert result == "AMD64"

    def Test_seeded_uname_result_has_windows_system(self) -> None:
        """The seeded uname_result must report ``system='Windows'``."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        fake_platform = _make_fake_platform_module()
        seed_uname_cache_for_windows(
            _sys_platform="win32",
            _environ={"PROCESSOR_ARCHITECTURE": "AMD64"},
            _platform_module=fake_platform,
        )
        assert fake_platform._uname_cache.system == "Windows"
        assert fake_platform._uname_cache.release == ""
        assert fake_platform._uname_cache.version == ""

    def Test_default_platform_module_no_op_on_linux(self) -> None:
        """Omitting ``_platform_module`` on Linux must still be a safe no-op."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            seed_uname_cache_for_windows,
        )

        # Exercises the default ``_platform_module=platform`` branch without
        # mutating real state (the Linux seam guarantees an early return).
        assert seed_uname_cache_for_windows(_sys_platform="linux") is None
