"""Custom exception classes for QWIM projects.

============================================

Public façade — re-exports every symbol from the three private sub-modules:

- :mod:`._exception_types_lightweight` — platform patches, constants, enums,
    data-classes, helper functions, ``Exception_QWIM_Error``, and lightweight typed
  subclasses.
- :mod:`._exception_core` — :class:`Exception_Custom` (rich-traceback core).
- :mod:`._exception_handlers` — 17 domain ``Exception_*`` classes, global
    handler utilities, :func:`Capture_Exception`, and :func:`Handle_Exceptions`.

Features
--------
- Multiple Exception Formats: Supports simple, complex, traceback, and custom modes
- Automatic Context Capture: Extracts filename, function, line number, and more
- Rich Formatting: Supports JSON, rich table output, and structured logging
- Thread-Safe: Uses locking to ensure safe exception handling
- Variable Inspection: Displays local variables in traceback frames

Root Exception
--------------
Exception_QWIM_Error
    Root for all QWIM project exceptions — catch-all for boundary handlers.

Lightweight Typed Subclasses (use in inner-layer code)
-------------------------------------------------------
Exception_Data_Validation_Error
    Input/data fails a validation check at a system boundary.
Exception_Config_Error
    Required configuration key missing or invalid.
Exception_External_Service_Error
    Third-party service (yfinance, HTTP, database) failure.
Exception_Serialization_Error
    msgspec / JSON / parquet encode-decode failure.

Classes
-------
Exception_Format
    Enum defining exception output formats.
Exception_Context
    Dataclass capturing exception context information.
Exception_Custom
    Enhanced base exception class with rich traceback support
    (inherits from Exception_QWIM_Error).

Domain-Specific Exceptions
--------------------------
Exception_Validation_Input
    Raised when input validation fails.
Exception_Invalid_Input
    Raised when input is invalid or malformed.
Exception_Configuration
    Raised for configuration-related errors.
Exception_Data_Not_Found
    Raised when required data is missing.
Exception_Not_Found
    Raised when a requested resource is not found.
Exception_Calculation
    Raised for calculation/computation failures.
Exception_Portfolio
    Raised for portfolio-related errors.
Exception_Client
    Raised for client data errors.
Exception_Database
    Raised for database operation failures.
Exception_API
    Raised for API communication failures.
Exception_Authentication
    Raised for authentication failures.
Exception_Authorization
    Raised for authorization/permission failures.
Exception_File_Operation
    Raised for file I/O failures.
Exception_Timeout
    Raised when operations exceed time limits.
Exception_Security_Violation
    Raised for security policy violations.
Exception_Insufficient_Holdings
    Raised when portfolio has insufficient holdings.
Exception_Invalid_Transaction
    Raised when a transaction is invalid.

Aliases
-------
Exception_Validation
    Alias for Exception_Validation_Input.

Example
-------
>>> from src.utils.custom_exceptions_errors_loggers.exception_custom import (
...     Exception_Custom,
...     Exception_Validation_Input,
...     Exception_Format,
...     Exception_Invalid_Input,
...     Exception_Not_Found,
...     Exception_QWIM_Error,
...     Exception_Data_Validation_Error,
... )
>>>
>>> # Simple exception
>>> raise Exception_Validation_Input("Invalid portfolio weight")
>>>
>>> # Lightweight typed exception (no rich-traceback overhead)
>>> raise Exception_Data_Validation_Error(
...     "weight must be in [0, 1]",
...     field="w_equity",
...     value=1.5,
... )
>>>
>>> # Exception with context
>>> raise Exception_Custom(
...     message="Calculation failed",
...     exception_format=Exception_Format.RICH_TRACEBACK,
...     context={"portfolio_id": "PORT_001", "operation": "optimize"},
... )
>>>
>>> # Resource not found
>>> raise Exception_Not_Found(
...     "Portfolio not found",
...     resource_type="Portfolio",
...     resource_id="PORT_001",
... )

Notes
-----
- All exceptions are thread-safe and can be used in multi-threaded applications
- Rich traceback requires terminal support for ANSI colors
- JSON format is suitable for structured logging and API responses
- Use aenum instead of built-in Enum per project coding standards
- Use lightweight subclasses (Exception_Data_Validation_Error,
    Exception_Config_Error, etc.) in
  hot paths where the full Exception_Custom machinery is not needed

Author: QWIM Team
Version: 0.7.0
Last Updated: 2026-05-20
"""

from __future__ import annotations

import sys  # noqa: F401

from ._exception_core import (
    Exception_Custom,
    _Reconstruct_Exception,
)
from ._exception_handlers import (
    _ORIGINAL_EXCEPTHOOK,
    Capture_Exception,
    Exception_API,
    Exception_Authentication,
    Exception_Authorization,
    Exception_Calculation,
    Exception_Client,
    Exception_Configuration,
    Exception_Data_Not_Found,
    Exception_Database,
    Exception_File_Operation,
    Exception_Insufficient_Holdings,
    Exception_Invalid_Input,
    Exception_Invalid_Transaction,
    Exception_Not_Found,
    Exception_Portfolio,
    Exception_Security_Violation,
    Exception_Timeout,
    Exception_Validation,
    Exception_Validation_Input,
    Global_Exception_Handler,
    Handle_Exceptions,
    Install_Exception_Handler,
    Restore_Exception_Handler,
)

# ---------------------------------------------------------------------------
# Façade imports — all public symbols re-exported from private sub-modules.
# Callers always import from this module; never import from the private ones.
# ---------------------------------------------------------------------------
from ._exception_types_lightweight import (
    MAX_TRACEBACK_FRAMES,
    MAX_VARIABLE_LENGTH,
    SENSITIVE_FIELDS,
    Exception_Config_Error,
    Exception_Context,
    Exception_Context_Dict,
    Exception_Data_Validation_Error,
    Exception_External_Service_Error,
    Exception_Format,
    Exception_Frame,
    Exception_Frame_List,
    Exception_QWIM_Error,
    Exception_Serialization_Error,
    Exception_Severity,
    Sensitive_Field_Set,
    _Extract_Frames_From_Traceback,
    _Mask_Sensitive_Data,
    _Serialize_For_JSON,
    _Truncate_Value,
)


__all__ = [  # noqa: RUF022
    "MAX_TRACEBACK_FRAMES",
    "MAX_VARIABLE_LENGTH",
    # Constants
    "SENSITIVE_FIELDS",
    "Exception_API",
    "Exception_Authentication",
    "Exception_Authorization",
    "Exception_Calculation",
    "Exception_Client",
    "Exception_Config_Error",
    "Exception_Configuration",
    "Exception_Context",
    # Type aliases
    "Exception_Context_Dict",
    # Main exception class
    "Exception_Custom",
    "Exception_Data_Not_Found",
    "Exception_Data_Validation_Error",
    "Exception_Database",
    "Exception_External_Service_Error",
    "Exception_File_Operation",
    # Enums
    "Exception_Format",
    # Data classes
    "Exception_Frame",
    "Exception_Frame_List",
    "Exception_Insufficient_Holdings",
    # Additional domain exceptions (per coding-instructions-python.md)
    "Exception_Invalid_Input",
    "Exception_Invalid_Transaction",
    "Exception_Not_Found",
    "Exception_Portfolio",
    # Root exception and lightweight typed subclasses (P1 additions)
    "Exception_QWIM_Error",
    "Exception_Security_Violation",
    "Exception_Serialization_Error",
    "Exception_Severity",
    "Exception_Timeout",
    # Aliases (convenience and backward compatibility)
    "Exception_Validation",
    # Domain-specific exceptions
    "Exception_Validation_Input",
    "Sensitive_Field_Set",
    "_Extract_Frames_From_Traceback",
    "_Mask_Sensitive_Data",
    "_ORIGINAL_EXCEPTHOOK",
    "_Reconstruct_Exception",
    "_Serialize_For_JSON",
    "_Truncate_Value",
    # Utilities
    "Capture_Exception",
    "Global_Exception_Handler",
    "Handle_Exceptions",
    # Global Handler
    "Install_Exception_Handler",
    "Restore_Exception_Handler",
]
