"""Behave steps for traceback_custom feature."""

from __future__ import annotations

import io
import sys
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
    from src.utils.custom_exceptions_errors_loggers import traceback_custom as tc
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"traceback_custom could not be imported: {_import_error_message}"
        )


@given("the traceback_custom module is importable")
def step_traceback_custom_importable(context):
    """Verify traceback_custom loaded successfully."""
    _require_imports()
    context.result = None
    context.raised = None
    context.relevant_frames = None


@when("I call traceback_custom compact formatting without a traceback")
def step_compact_format_without_traceback(context):
    """Call compact formatting with no traceback object."""
    _require_imports()
    context.result = tc.Format_Traceback_Compact(exc_type = ValueError, exc_value = ValueError("behave compact"), exc_tb = None)
    context.raised = None


@when("I call traceback_custom context formatting with negative context_lines")
def step_context_format_with_negative_context_lines(context):
    """Call context formatting with an invalid negative context width."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        tc.Format_Traceback_Context(exc_type = ValueError, exc_value = ValueError("behave context"), exc_tb = None, context_lines=-1)
    except ValueError as exc:
        context.raised = exc


@when("I call traceback_custom Extract_Relevant_Frames with a blank project_root")
def step_extract_frames_blank_project_root(context):
    """Call Extract_Relevant_Frames with a blank project-root override."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        tc.Extract_Relevant_Frames(exc_tb = object(), project_root="   ")
    except ValueError as exc:
        context.raised = exc


@when("I call traceback_custom Extract_Relevant_Frames with a non-string project_root")
def step_extract_frames_non_string_project_root(context):
    """Call Extract_Relevant_Frames with a non-string project-root override."""
    _require_imports()
    context.result = None
    context.raised = None
    try:
        tc.Extract_Relevant_Frames(exc_tb = object(), project_root=123)  # type: ignore[arg-type]
    except TypeError as exc:
        context.raised = exc


@when("I call traceback_custom Extract_Relevant_Frames with normalized project_root")
def step_extract_frames_normalized_project_root(context):
    """Call Extract_Relevant_Frames with a whitespace-wrapped project root."""
    _require_imports()
    project_root = str(Path(__file__).resolve().parent)
    matching_frame = SimpleNamespace(filename=str(Path(project_root) / "inside.py"))
    non_matching_frame = SimpleNamespace(filename="Z:/outside.py")

    original_extract_tb = tc.traceback.extract_tb
    tc.traceback.extract_tb = lambda _exc_tb: [matching_frame, non_matching_frame]
    try:
        context.relevant_frames = tc.Extract_Relevant_Frames(
            exc_tb = object(),
            project_root=f"  {project_root}  ",
        )
    finally:
        tc.traceback.extract_tb = original_extract_tb


@then('the traceback_custom result is "{expected_text}"')
def step_traceback_custom_result_is(context, expected_text):
    """Assert the previous step produced the expected result text."""
    assert context.result == expected_text, (
        f"Expected result {expected_text!r}, got {context.result!r}"
    )


@then("a traceback_custom ValueError is raised")
def step_traceback_custom_value_error(context):
    """Assert the previous step raised ValueError."""
    assert isinstance(context.raised, ValueError), (
        f"Expected ValueError, got {type(context.raised)}: {context.raised}"
    )


@then("a traceback_custom TypeError is raised")
def step_traceback_custom_type_error(context):
    """Assert the previous step raised TypeError."""
    assert isinstance(context.raised, TypeError), (
        f"Expected TypeError, got {type(context.raised)}: {context.raised}"
    )


@then("only traceback_custom frames under the project root are returned")
def step_only_project_root_frames_returned(context):
    """Assert only frames under the normalized root were kept."""
    assert context.relevant_frames is not None, "Expected relevant frames to be captured"
    assert len(context.relevant_frames) == 1, (
        f"Expected one relevant frame, got {context.relevant_frames!r}"
    )
    assert context.relevant_frames[0].filename.endswith("inside.py"), (
        f"Unexpected frame list: {context.relevant_frames!r}"
    )