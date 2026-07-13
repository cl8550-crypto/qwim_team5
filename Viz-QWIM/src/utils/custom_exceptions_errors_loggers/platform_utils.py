"""Platform detection utilities with a dependency-injection seam for testing.

All public functions accept an optional ``_sys_platform`` parameter that, when
supplied, overrides the real ``sys.platform`` value.  This makes every branch
fully testable without monkey-patching global state.

Author
------
QWIM Team

Version
-------
0.2.0 (2026-05-28)
"""

from __future__ import annotations

import os
import platform
import sys

from collections.abc import Mapping
from types import ModuleType


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


# Maps the Windows ``PROCESSOR_ARCHITECTURE`` family to the canonical machine
# string returned by :func:`platform.machine` for common 64/32-bit targets.
MACHINE_BY_ARCHITECTURE: dict[str, str] = {
    "AMD64": "AMD64",
    "X86": "x86",
    "ARM64": "ARM64",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _validate_sys_platform_QWIM(*, _sys_platform: str | None) -> str | None:
    """Validate and normalize an injected platform override.

    Parameters
    ----------
    _sys_platform : str | None
        Optional injected platform override used by tests and controlled
        call-sites.

    Returns
    -------
    str | None
        Normalized platform string, or ``None`` when no override was provided.

    Raises
    ------
    TypeError
        Raised when ``_sys_platform`` is not ``None`` and not a string.
    ValueError
        Raised when ``_sys_platform`` is blank after trimming whitespace.
    """
    if _sys_platform is None:
        return None

    if not isinstance(_sys_platform, str):
        raise TypeError("_sys_platform must be a string or None")

    normalized_platform = _sys_platform.strip()
    if normalized_platform == "":
        raise ValueError("_sys_platform must be a non-empty string when provided")

    return normalized_platform


def get_platform(*, _sys_platform: str | None = None) -> str:
    """Return the current platform string.

    Parameters
    ----------
    _sys_platform : str | None
        Testability seam.  When provided, this value is returned instead of
        ``sys.platform``.  Pass ``"win32"``, ``"linux"``, ``"darwin"``, etc.

    Returns
    -------
    str
        Platform identifier string (e.g. ``"win32"``, ``"linux"``).
    """
    normalized_platform = _validate_sys_platform_QWIM(_sys_platform = _sys_platform)
    return normalized_platform if normalized_platform is not None else sys.platform


def is_windows(*, _sys_platform: str | None = None) -> bool:
    """Return ``True`` when running on Windows (or when seeded as Windows).

    Parameters
    ----------
    _sys_platform : str | None
        Testability seam — see :func:`get_platform`.

    Returns
    -------
    bool
        ``True`` iff the platform is ``"win32"``.
    """
    return get_platform(_sys_platform=_sys_platform) == "win32"


def is_linux(*, _sys_platform: str | None = None) -> bool:
    """Return ``True`` when running on Linux (or when seeded as Linux).

    Parameters
    ----------
    _sys_platform : str | None
        Testability seam — see :func:`get_platform`.

    Returns
    -------
    bool
        ``True`` iff the platform starts with ``"linux"``.
    """
    return get_platform(_sys_platform=_sys_platform).startswith("linux")


def is_macos(*, _sys_platform: str | None = None) -> bool:
    """Return ``True`` when running on macOS (or when seeded as macOS).

    Parameters
    ----------
    _sys_platform : str | None
        Testability seam — see :func:`get_platform`.

    Returns
    -------
    bool
        ``True`` iff the platform is ``"darwin"``.
    """
    return get_platform(_sys_platform=_sys_platform) == "darwin"


def seed_uname_cache_for_windows(
    *,
    _sys_platform: str | None = None,
    _environ: Mapping[str, str] | None = None,
    _platform_module: ModuleType | None = None,
    _force: bool = False,
) -> str | None:
    """Pre-seed :data:`platform._uname_cache` on Windows to avoid a WMI hang.

    On Python 3.13 / Windows, ``import polars`` calls :func:`platform.machine`
    at module top (``polars/_cpu_check.py``).  In CPython 3.13 that resolves
    through :func:`platform.uname` → :func:`platform.win32_ver` → an internal
    **WMI query**.  When the host's WMI (``Winmgmt``) service is hung or
    degraded the query never returns, so any process that imports ``polars``
    (including ``pytest`` collection) blocks indefinitely with no output.

    Seeding :data:`platform._uname_cache` *before* ``polars`` is imported makes
    :func:`platform.uname`/:func:`platform.machine` return immediately from the
    cache and never touch WMI.  The machine string is derived from the
    ``PROCESSOR_ARCHITEW6432`` / ``PROCESSOR_ARCHITECTURE`` environment
    variables, mirroring what :func:`platform.machine` would otherwise report.

    This function deliberately mutates global state on the ``platform`` module;
    it is a process-bootstrapping side effect (called from test/app entry
    points), not a pure helper.  It is a **no-op on non-Windows platforms** so
    Linux/Posit Connect deployments are unaffected.

    Parameters
    ----------
    _sys_platform : str | None
        Testability seam — see :func:`get_platform`.  When it does not denote
        Windows the function returns ``None`` without side effects.
    _environ : collections.abc.Mapping[str, str] | None
        Environment mapping to read the processor architecture from.  Defaults
        to :data:`os.environ`.  Injected in tests.
    _platform_module : types.ModuleType | None
        The module whose ``_uname_cache`` attribute is seeded.  Defaults to the
        real :mod:`platform` module.  Injected in tests to avoid mutating
        global interpreter state.
    _force : bool
        When ``True`` the cache is (re-)seeded even if it is already populated.
        Defaults to ``False`` so an already-resolved cache is left untouched.

    Returns
    -------
    str | None
        The machine string that was seeded, or ``None`` when the function was
        a no-op (non-Windows, or cache already populated and ``_force`` False).
    """
    if not is_windows(_sys_platform=_sys_platform):
        return None

    target_platform = _platform_module if _platform_module is not None else platform

    existing_cache = getattr(target_platform, "_uname_cache", None)
    if existing_cache is not None and not _force:
        return None

    environ = _environ if _environ is not None else os.environ
    architecture = (
        environ.get("PROCESSOR_ARCHITEW6432")
        or environ.get("PROCESSOR_ARCHITECTURE")
        or "AMD64"
    )
    machine = MACHINE_BY_ARCHITECTURE.get(architecture.upper(), architecture)
    node = environ.get("COMPUTERNAME", "localhost")

    target_platform._uname_cache = target_platform.uname_result(
        system="Windows",
        node=node,
        release="",
        version="",
        machine=machine,
    )
    return machine
