"""Robot Framework keyword library for exception_custom tests.

Provides thin Python keyword wrappers testing:
  - Exception_Custom construction and attributes
  - Domain exception classes (subclass relationships, message storage)
  - Lightweight root hierarchy (Exception_QWIM_Error and subclasses)
    - Global handler utilities (Install_Exception_Handler, Capture_Exception,
        Handle_Exceptions)
    - Output methods (To_Dict, To_JSON)

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
from typing import Any

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# sys.stderr patch — exception_custom accesses sys.stderr.buffer at import
# ---------------------------------------------------------------------------
_original_stderr = sys.stderr
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO())

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
        Exception_External_Service_Error,
        Exception_QWIM_Error,
        Exception_Serialization_Error,
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
    import logging as _logging
    _logger = _logging.getLogger(__name__)
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: %s", _exc)
finally:
    sys.stderr = _original_stderr


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"exception_custom source modules could not be imported: {_import_error_message}"
        )


# ---------------------------------------------------------------------------
# Keywords — Exception_Custom construction
# ---------------------------------------------------------------------------


def Create_Exception_Custom(message: str) -> "Exception_Custom":
    """Create an Exception_Custom with *message* and return it.

    Robot keyword: ``Create Exception Custom    message``
    """
    _require_imports()
    return Exception_Custom(message)


def Get_Exception_Message(exc: "Exception_Custom") -> str:
    """Return the .Message attribute of *exc*.

    Robot keyword: ``Get Exception Message    ${exc}``
    """
    _require_imports()
    return exc.Message


def Get_Exception_Severity_Name(exc: "Exception_Custom") -> str:
    """Return the name of the exception's severity enum member.

    Robot keyword: ``Get Exception Severity Name    ${exc}``
    """
    _require_imports()
    return exc.Severity.name


# ---------------------------------------------------------------------------
# Keywords — output methods
# ---------------------------------------------------------------------------


def Exception_To_Dict_Has_Key(
    exc: "Exception_Custom",
    key: str,
) -> bool:
    """Return True when *key* is present in ``exc.To_Dict()``.

    Robot keyword: ``Exception To Dict Has Key    ${exc}    message``
    """
    _require_imports()
    result = exc.To_Dict()
    return key in result


def Exception_To_JSON_Is_Valid(exc: "Exception_Custom") -> bool:
    """Return True when ``exc.To_JSON()`` parses as valid JSON.

    Robot keyword: ``Exception To JSON Is Valid    ${exc}``
    """
    _require_imports()
    try:
        json.loads(exc.To_JSON())
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def Pickled_Exception_Custom_Preserves_Base_Detail() -> bool:
    """Return True when a round-tripped Exception_Custom retains detail == {}."""
    _require_imports()
    original = Exception_Custom("pickle test", context={"portfolio": "present"})
    restored = pickle.loads(pickle.dumps(original))
    return restored.detail == {} and restored._user_context == {"portfolio": "present"}


# ---------------------------------------------------------------------------
# Keywords — domain exceptions
# ---------------------------------------------------------------------------


def Create_Exception_Validation_Input(message: str) -> "Exception_Validation_Input":
    """Create an Exception_Validation_Input.

    Robot keyword: ``Create Exception Validation Input    message``
    """
    _require_imports()
    return Exception_Validation_Input(message)


def Create_Exception_Calculation(message: str) -> "Exception_Calculation":
    """Create an Exception_Calculation.

    Robot keyword: ``Create Exception Calculation    message``
    """
    _require_imports()
    return Exception_Calculation(message)


def Create_Exception_Timeout(message: str) -> "Exception_Timeout":
    """Create an Exception_Timeout.

    Robot keyword: ``Create Exception Timeout    message``
    """
    _require_imports()
    return Exception_Timeout(message)


def Create_Exception_Configuration(message: str) -> "Exception_Configuration":
    """Create an Exception_Configuration.

    Robot keyword: ``Create Exception Configuration    message``
    """
    _require_imports()
    return Exception_Configuration(message)


def Is_Exception_Custom_Instance(obj: Any) -> bool:
    """Return True when *obj* is an Exception_Custom instance.

    Robot keyword: ``Is Exception Custom Instance    ${obj}``
    """
    _require_imports()
    return isinstance(obj, Exception_Custom)


# ---------------------------------------------------------------------------
# Keywords — lightweight root hierarchy
# ---------------------------------------------------------------------------


def Exception_QWIM_Error_Is_Exception_Subclass() -> bool:
    """Return True — Exception_QWIM_Error is always a subclass of Exception.

    Robot keyword: ``Exception QWIM Error Is Exception Subclass``
    """
    _require_imports()
    return issubclass(Exception_QWIM_Error, Exception)


def Get_Lightweight_Subclass_Count() -> int:
    """Return the count of lightweight Exception_QWIM_Error subclasses.

    The expected subclasses are: Exception_Data_Validation_Error,
    Exception_Config_Error, Exception_External_Service_Error,
    Exception_Serialization_Error.

    Robot keyword: ``Get Lightweight Subclass Count``
    """
    _require_imports()
    classes = [
        Exception_Data_Validation_Error,
        Exception_Config_Error,
        Exception_External_Service_Error,
        Exception_Serialization_Error,
    ]
    return sum(1 for cls in classes if issubclass(cls, Exception_QWIM_Error))


def Create_Exception_Data_Validation_Error(
    message: str,
    field: str = "value",
) -> "Exception_Data_Validation_Error":
    """Create an Exception_Data_Validation_Error with *field*.

    Robot keyword: ``Create Exception Data Validation Error    message    field``
    """
    _require_imports()
    return Exception_Data_Validation_Error(message, field=field, value=None)


def Exception_Data_Validation_Error_Has_Field(
    exc: "Exception_Data_Validation_Error",
) -> bool:
    """Return True when *exc* exposes a ``field`` attribute.

    Robot keyword: ``Exception Data Validation Error Has Field    ${exc}``
    """
    _require_imports()
    return hasattr(exc, "field")


def Mask_Sensitive_Data_Preserves_Non_String_Keys() -> bool:
    """Return True when masking preserves numeric keys and masks password values."""
    _require_imports()
    result = _Mask_Sensitive_Data(
        data = {123: "ok", "nested": {456: "still ok", "password": "secret"}}
    )
    return (
        result[123] == "ok"
        and result["nested"][456] == "still ok"
        and result["nested"]["password"] == "***MASKED***"
    )


# ---------------------------------------------------------------------------
# Keywords — global handler utilities
# ---------------------------------------------------------------------------


def Install_And_Restore_Exception_Handler() -> bool:
    """Install then restore the global exception handler; return True on success.

    Robot keyword: ``Install And Restore Exception Handler``
    """
    _require_imports()
    Install_Exception_Handler()
    handler_ok = sys.excepthook is Global_Exception_Handler
    Restore_Exception_Handler()
    return handler_ok


def Capture_Exception_Suppresses_Value_Error() -> bool:
    """Return True when Capture_Exception suppresses ValueError.

    Robot keyword: ``Capture Exception Suppresses Value Error``
    """
    _require_imports()
    try:
        with Capture_Exception(reraise=False):
            raise ValueError("Suppressed")
        return True
    except ValueError:
        return False


def Handle_Exceptions_Wraps_Runtime_Error() -> bool:
    """Return True when Handle_Exceptions converts RuntimeError to Exception_Custom.

    Robot keyword: ``Handle Exceptions Wraps Runtime Error``
    """
    _require_imports()

    @Handle_Exceptions()
    def _fail() -> None:
        raise RuntimeError("Wrapped")

    try:
        _fail()
        return False
    except Exception_Custom:
        return True
    except RuntimeError:
        return False


# ---------------------------------------------------------------------------
# Generic assertion helper
# ---------------------------------------------------------------------------


def Boolean_Should_Be_True(value: bool) -> None:
    """Assert *value* is True; raise AssertionError otherwise.

    Robot keyword: ``Boolean Should Be True    ${value}``
    """
    if not value:
        raise AssertionError(f"Expected True, got {value!r}")


def Integer_Should_Equal(
    actual: int,
    expected: int,
) -> None:
    """Assert *actual* == *expected*.

    Robot keyword: ``Integer Should Equal    ${actual}    ${expected}``
    """
    if actual != expected:
        raise AssertionError(f"Expected {expected}, got {actual}")
