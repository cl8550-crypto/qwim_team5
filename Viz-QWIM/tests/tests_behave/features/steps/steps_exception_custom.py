"""Behave step definitions for exception_custom feature.

Covers:
  - Exception_Custom core construction (message, severity)
    - Output formats (str, To_Dict, To_JSON)
  - Domain-specific exceptions (Exception_Validation_Input, Exception_Configuration,
    Exception_Calculation, Exception_Timeout)
  - Lightweight root hierarchy (Exception_QWIM_Error, Exception_Data_Validation_Error,
    Exception_Config_Error)
    - Global handler utilities (Install_Exception_Handler, Capture_Exception,
        Handle_Exceptions)

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import io
import json
import pickle
import sys
from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch — exception_custom accesses sys.stderr.buffer at import
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Calculation,
        Exception_Config_Error,
        Exception_Configuration,
        Exception_Custom,
        Exception_Data_Validation_Error,
        Exception_QWIM_Error,
        Exception_Severity,
        Exception_Timeout,
        Exception_Validation_Input,
        _Mask_Sensitive_Data,
        Capture_Exception,
        Global_Exception_Handler,
        Handle_Exceptions,
        Install_Exception_Handler,
        Restore_Exception_Handler,
    )
except Exception as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"exception_custom modules could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Given steps
# ===========================================================================


@given("the exception_custom module is importable")
def step_given_exception_custom_importable(context) -> None:
    """Verify the module loaded successfully."""
    _require_imports()
    context.exception = None
    context.exc_class = None
    context.result = None


# ===========================================================================
# When steps — Exception_Custom construction
# ===========================================================================


@when('I create an Exception_Custom with message "{message}"')
def step_create_exception_custom(context, message: str) -> None:
    """Create an Exception_Custom with the given message."""
    _require_imports()
    context.exception = Exception_Custom(message)


@when('I create a severity-tagged Exception_Custom with message "{message}" severity "{severity}"')
def step_create_exception_custom_with_severity(
    context,
    message: str,
    severity: str,
) -> None:
    """Create an Exception_Custom with message and severity."""
    _require_imports()
    sev = Exception_Severity[severity]
    context.exception = Exception_Custom(message, severity=sev)


@when(
    'I pickle and unpickle an Exception_Custom with message "{message}" and context key "{context_key}"'
)
def step_pickle_roundtrip_exception_custom(
    context,
    message: str,
    context_key: str,
) -> None:
    """Round-trip Exception_Custom through pickle and store the restored instance."""
    _require_imports()
    original = Exception_Custom(message, context={context_key: "present"})
    context.exception = pickle.loads(pickle.dumps(original))


# ===========================================================================
# When steps — domain exceptions
# ===========================================================================


@when('I instantiate an Exception_Validation_Input with message "{message}"')
def step_instantiate_validation_input(context, message: str) -> None:
    """Instantiate Exception_Validation_Input."""
    _require_imports()
    context.exception = Exception_Validation_Input(message)


@when('I instantiate an Exception_Configuration with message "{message}"')
def step_instantiate_configuration(context, message: str) -> None:
    """Instantiate Exception_Configuration."""
    _require_imports()
    context.exception = Exception_Configuration(message)


@when('I instantiate an Exception_Calculation with message "{message}"')
def step_instantiate_calculation(context, message: str) -> None:
    """Instantiate Exception_Calculation."""
    _require_imports()
    context.exception = Exception_Calculation(message)


@when('I instantiate an Exception_Timeout with message "{message}"')
def step_instantiate_timeout(context, message: str) -> None:
    """Instantiate Exception_Timeout."""
    _require_imports()
    context.exception = Exception_Timeout(message)


# ===========================================================================
# When steps — lightweight hierarchy inspection
# ===========================================================================


@when("I inspect the Exception_QWIM_Error class")
def step_inspect_qwim_error(context) -> None:
    """Store the Exception_QWIM_Error class for inspection."""
    _require_imports()
    context.exc_class = Exception_QWIM_Error


@when("I inspect the Exception_Data_Validation_Error class")
def step_inspect_data_validation_error(context) -> None:
    """Store the Exception_Data_Validation_Error class for inspection."""
    _require_imports()
    context.exc_class = Exception_Data_Validation_Error


@when("I inspect the Exception_Config_Error class")
def step_inspect_config_error(context) -> None:
    """Store the Exception_Config_Error class for inspection."""
    _require_imports()
    context.exc_class = Exception_Config_Error


@when('I raise an Exception_Data_Validation_Error with field "{field}" and value "{value}"')
def step_raise_data_validation_error(
    context,
    field: str,
    value: str,
) -> None:
    """Raise an Exception_Data_Validation_Error and capture it."""
    _require_imports()
    context.exception = Exception_Data_Validation_Error(
        f"Validation failed for {field}",
        field=field,
        value=value,
    )


@when("I mask exception context data with non-string keys")
def step_mask_exception_context_non_string_keys(context) -> None:
    """Mask a context dictionary that includes non-string keys."""
    _require_imports()
    context.result = _Mask_Sensitive_Data(
        data = {123: "ok", "nested": {456: "still ok", "password": "secret"}}
    )


# ===========================================================================
# When steps — global handlers
# ===========================================================================


@when("I call Install_Exception_Handler")
def step_call_install_exception_handler(context) -> None:
    """Install the custom global exception handler."""
    _require_imports()
    Install_Exception_Handler()
    context.handler_installed = True


@when("I use Capture_Exception to run code that raises a ValueError")
def step_use_capture_exception(context) -> None:
    """Run code inside Capture_Exception that raises ValueError."""
    _require_imports()
    with Capture_Exception(reraise=False):
        raise ValueError("Suppressed error")
    context.suppressed = True


@when("I apply Handle_Exceptions decorator to a function that raises RuntimeError")
def step_apply_handle_exceptions(context) -> None:
    """Decorate a function and call it."""
    _require_imports()

    @Handle_Exceptions()
    def _failing_func() -> None:
        raise RuntimeError("Wrapped error")

    context.decorated_func = _failing_func


# ===========================================================================
# Then steps
# ===========================================================================


@then('the exception message should be "{expected_message}"')
def step_exception_message(context, expected_message: str) -> None:
    """Assert the exception message matches."""
    assert context.exception is not None, "No exception was created"
    assert context.exception.Message == expected_message, (
        f"Expected message={expected_message!r}, got {context.exception.Message!r}"
    )


@then('the exception severity should be "{expected_severity}"')
def step_exception_severity(context, expected_severity: str) -> None:
    """Assert the exception severity matches."""
    assert context.exception is not None, "No exception was created"
    assert context.exception.Severity.name == expected_severity, (
        f"Expected severity={expected_severity}, got {context.exception.Severity.name}"
    )


@then("the exception should be an instance of Exception")
def step_is_exception_instance(context) -> None:
    """Assert the exception is an instance of Exception."""
    assert isinstance(context.exception, Exception)


@then("it should be an instance of Exception_Custom")
def step_is_exception_custom_instance(context) -> None:
    """Assert the exception is an Exception_Custom instance."""
    assert isinstance(context.exception, Exception_Custom), (
        f"Expected Exception_Custom instance, got {type(context.exception)}"
    )


@then('the string representation should contain "{text}"')
def step_str_contains(context, text: str) -> None:
    """Assert str(exception) contains the given text."""
    assert text in str(context.exception), (
        f"Expected {text!r} in str(exception)={str(context.exception)!r}"
    )


@then('To_Dict should return a dict containing key "{key}"')
def step_to_dict_has_key(context, key: str) -> None:
    """Assert To_Dict() returns a dict with the given key."""
    result = context.exception.To_Dict()
    assert isinstance(result, dict), f"To_Dict() returned {type(result)}, expected dict"
    assert key in result, f"Key {key!r} not found in To_Dict() result: {list(result.keys())}"


@then("To_JSON should produce valid JSON")
def step_to_json_valid(context) -> None:
    """Assert To_JSON() produces parseable JSON."""
    json_str = context.exception.To_JSON()
    try:
        json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"To_JSON() did not produce valid JSON: {exc}") from exc


@then('the JSON should contain key "{key}"')
def step_json_has_key(context, key: str) -> None:
    """Assert the JSON output contains the given key."""
    json_str = context.exception.To_JSON()
    parsed = json.loads(json_str)
    assert key in parsed, f"Key {key!r} not found in JSON output: {list(parsed.keys())}"


@then("the pickled exception detail should be an empty dict")
def step_pickled_exception_detail_empty(context) -> None:
    """Assert a round-tripped Exception_Custom still exposes detail == {}."""
    assert context.exception.detail == {}, (
        f"Expected empty detail dict, got {context.exception.detail!r}"
    )


@then('the pickled exception user context should contain key "{key}"')
def step_pickled_exception_user_context_key(context, key: str) -> None:
    """Assert a round-tripped Exception_Custom kept its user context payload."""
    assert key in context.exception._user_context, (
        f"Expected key {key!r} in user context, got {context.exception._user_context!r}"
    )


@then("it should be a subclass of Exception")
def step_is_exception_subclass(context) -> None:
    """Assert the stored class is a subclass of Exception."""
    assert issubclass(context.exc_class, Exception), (
        f"{context.exc_class.__name__} is not a subclass of Exception"
    )


@then("it should be a subclass of Exception_QWIM_Error")
def step_is_qwim_error_subclass(context) -> None:
    """Assert the stored class is a subclass of Exception_QWIM_Error."""
    assert issubclass(context.exc_class, Exception_QWIM_Error), (
        f"{context.exc_class.__name__} is not a subclass of Exception_QWIM_Error"
    )


@then('the exception detail should contain key "{key}"')
def step_exception_detail_has_key(context, key: str) -> None:
    """Assert the exception's detail dict contains the given key."""
    assert context.exception is not None, "No exception was created"
    detail = context.exception.detail
    assert detail is not None, "exception.detail is None"
    assert key in detail, f"Key {key!r} not found in detail: {list(detail.keys())}"


@then("the masked exception context should preserve non-string keys and mask password values")
def step_masked_exception_context_non_string_keys(context) -> None:
    """Assert masking preserved numeric keys and masked password fields."""
    assert context.result[123] == "ok"
    assert context.result["nested"][456] == "still ok"
    assert context.result["nested"]["password"] == "***MASKED***"


@then("sys.excepthook should be Global_Exception_Handler")
def step_excepthook_is_global_handler(context) -> None:
    """Assert sys.excepthook points to our Global_Exception_Handler."""
    assert sys.excepthook is Global_Exception_Handler, (
        f"sys.excepthook is {sys.excepthook}, expected Global_Exception_Handler"
    )


@then("I restore the original exception handler")
def step_restore_handler(context) -> None:
    """Restore the original sys.excepthook."""
    Restore_Exception_Handler()


@then("the context manager should suppress the exception")
def step_context_manager_suppresses(context) -> None:
    """Assert the exception was suppressed (i.e., we reached this step)."""
    assert context.suppressed is True, "Exception was not suppressed"


@then("the function should raise Exception_Custom instead")
def step_function_raises_exception_custom(context) -> None:
    """Assert the decorated function raises Exception_Custom."""
    raised = False
    try:
        context.decorated_func()
    except Exception_Custom:
        raised = True
    assert raised, "Expected Exception_Custom to be raised by decorated function"
