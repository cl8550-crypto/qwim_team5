"""Behave steps for platform_utils feature."""

from __future__ import annotations

import io
import sys
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch for exception_custom compatibility
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.custom_exceptions_errors_loggers.platform_utils import (
        get_platform,
        is_linux,
        is_macos,
        is_windows,
        seed_uname_cache_for_windows,
    )
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"platform_utils could not be imported: {_import_error_message}"
        )


def _make_fake_platform_module(*, uname_cache=None):
    """Return a lightweight stand-in for the platform module."""
    fake_uname = namedtuple(
        "Fake_Uname", ["system", "node", "release", "version", "machine"]
    )
    return SimpleNamespace(_uname_cache=uname_cache, uname_result=fake_uname)


@given("the platform_utils module is importable")
def step_platform_utils_importable(context):
    """Verify platform_utils loaded successfully."""
    _require_imports()
    context.result = None
    context.raised = None
    context.fake_platform = None
    context.windows_machine = None
    context.predicate_results = None


@when('I call platform_utils get_platform with whitespace around "linux"')
def step_call_get_platform_with_whitespace_linux(context):
    """Call get_platform with a whitespace-wrapped Linux seed."""
    _require_imports()
    context.result = get_platform(_sys_platform="  linux  ")
    context.raised = None


@when("I call platform_utils get_platform with a blank seed")
def step_call_get_platform_with_blank_seed(context):
    """Call get_platform with a blank platform seed."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = get_platform(_sys_platform="   ")
    except ValueError as exc:
        context.raised = exc


@when("I call platform_utils get_platform with a non-string seed")
def step_call_get_platform_with_non_string_seed(context):
    """Call get_platform with a non-string seed."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        context.result = get_platform(_sys_platform=123)  # type: ignore[arg-type]
    except TypeError as exc:
        context.raised = exc


@when('I evaluate platform_utils predicates for seed "linux"')
def step_evaluate_platform_predicates_linux(context):
    """Evaluate all platform predicates for a Linux seed."""
    _require_imports()
    context.predicate_results = {
        "windows": is_windows(_sys_platform="linux"),
        "linux": is_linux(_sys_platform="linux"),
        "macos": is_macos(_sys_platform="linux"),
    }


@when('I seed the platform_utils uname cache for Windows architecture "X86"')
def step_seed_windows_cache_x86(context):
    """Seed a fake platform module for a Windows X86 environment."""
    _require_imports()
    context.fake_platform = _make_fake_platform_module()
    context.result = seed_uname_cache_for_windows(
        _sys_platform="win32",
        _environ={"PROCESSOR_ARCHITECTURE": "X86", "COMPUTERNAME": "PC1"},
        _platform_module=context.fake_platform,
    )
    context.windows_machine = context.fake_platform._uname_cache.machine


@when('I seed the platform_utils uname cache for non-Windows platform "darwin"')
def step_seed_non_windows_cache(context):
    """Seed a fake platform module for a non-Windows platform and capture the result."""
    _require_imports()
    context.fake_platform = _make_fake_platform_module()
    context.result = seed_uname_cache_for_windows(
        _sys_platform="darwin",
        _platform_module=context.fake_platform,
    )


@then('the normalized platform result is "{platform_name}"')
def step_normalized_platform_result(context, platform_name):
    """Assert the normalized platform string."""
    assert context.result == platform_name, (
        f"Expected normalized platform {platform_name!r}, got {context.result!r}"
    )


@then("a platform_utils ValueError is raised")
def step_platform_utils_value_error(context):
    """Assert the previous step raised ValueError."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )


@then("a platform_utils TypeError is raised")
def step_platform_utils_type_error(context):
    """Assert the previous step raised TypeError."""
    assert isinstance(context.raised, TypeError), (
        f"Expected TypeError, got {type(context.raised)}: {context.raised}"
    )


@then("only the linux predicate is true")
def step_only_linux_predicate_is_true(context):
    """Assert Linux is the only true predicate."""
    assert context.predicate_results == {
        "windows": False,
        "linux": True,
        "macos": False,
    }, f"Unexpected predicate results: {context.predicate_results!r}"


@then('the seeded machine is "{machine_name}"')
def step_seeded_machine_is(context, machine_name):
    """Assert the Windows cache seed produced the expected machine string."""
    assert context.result == machine_name, (
        f"Expected seed result {machine_name!r}, got {context.result!r}"
    )
    assert context.windows_machine == machine_name, (
        f"Expected cached machine {machine_name!r}, got {context.windows_machine!r}"
    )


@then("the platform_utils cache seed result is None")
def step_cache_seed_result_is_none(context):
    """Assert non-Windows cache seeding is a no-op."""
    assert context.result is None, f"Expected None, got {context.result!r}"
    assert context.fake_platform._uname_cache is None, (
        f"Expected no cache seed, got {context.fake_platform._uname_cache!r}"
    )