"""Shared Robot Framework keyword library — QWIM project.

Provides thin Python keyword wrappers that are reused by library-level
Robot Framework test suites across all non-dashboard source modules
(``src/utils/``, ``src/num_methods/``, ``src/portfolios/``,
``src/products/``, ``src/models/``, ``src/clients_QWIM/``,
``src/risks_metrics/``).

Browser-level keyword suites for ``src/dashboard/**`` continue to use the
existing Playwright / Browser library pattern and do **not** import from
this module.

Usage in a robot file
---------------------
::

    *** Settings ***
    Library    tests/tests_robot_framework/_keywords/qwim_keywords.py

Version: 1.0.0
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Conditional project imports
# Robot Framework replaces sys.stderr with StringIO; some project modules
# access sys.stderr.buffer at import time.  Temporarily restore a real stream.
# ---------------------------------------------------------------------------

MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

_original_stderr = sys.stderr
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO())

try:
    import polars as pl
    from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger
    from src.utils.custom_exceptions_errors_loggers.exception_custom import Exception_QWIM_Error
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
finally:
    sys.stderr = _original_stderr


# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------

if MODULE_IMPORT_AVAILABLE:
    _logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Generic Robot Framework keywords
# ---------------------------------------------------------------------------


def Module_Is_Available() -> bool:
    """Return ``True`` when all project modules imported successfully.

    Use this keyword as a guard in robot suites::

        *** Test Cases ***
        Guard
            ${ok}=    Module Is Available
            Skip If    not ${ok}    msg=Module import failed
    """
    return MODULE_IMPORT_AVAILABLE


def Get_Import_Error() -> str:
    """Return the import error message string, empty when no error occurred.

    Useful for diagnosing import failures in the Robot Framework log.
    """
    return _import_error_message


def Assert_Polars_Dataframe(
    obj: Any,
    *,
    min_rows: int = 0,
) -> None:
    """Verify that *obj* is a non-empty Polars DataFrame.

    Parameters
    ----------
    obj : Any
        The object to verify.
    min_rows : int
        Minimum required row count.  Defaults to ``0``.

    Raises
    ------
    AssertionError
        When *obj* is not a Polars DataFrame or has fewer rows than
        *min_rows*.
    """
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"Module import unavailable: {_import_error_message}")

    assert isinstance(obj, pl.DataFrame), (
        f"Expected pl.DataFrame, got {type(obj).__name__}"
    )
    assert len(obj) >= min_rows, (
        f"Expected at least {min_rows} rows, got {len(obj)}"
    )


def Assert_Polars_Series(
    obj: Any,
    *,
    expected_dtype: str | None = None,
) -> None:
    """Verify that *obj* is a Polars Series, optionally checking its dtype.

    Parameters
    ----------
    obj : Any
        The object to verify.
    expected_dtype : str or None
        Expected dtype name (e.g. ``"Float64"``, ``"Int32"``).  When
        ``None``, only the Series type is checked.

    Raises
    ------
    AssertionError
        When *obj* is not a Polars Series or the dtype does not match.
    """
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"Module import unavailable: {_import_error_message}")

    assert isinstance(obj, pl.Series), (
        f"Expected pl.Series, got {type(obj).__name__}"
    )
    if expected_dtype is not None:
        actual = str(obj.dtype)
        assert actual == expected_dtype, (
            f"Expected dtype {expected_dtype!r}, got {actual!r}"
        )


def Assert_No_Exception(
    callable_obj: Any,
    /,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Call *callable_obj* and assert it does not raise any exception.

    Returns the return value of the callable so it can be captured in
    robot variables.

    Parameters
    ----------
    callable_obj : Any
        The callable to invoke.
    *args : Any
        Positional arguments forwarded to *callable_obj*.
    **kwargs : Any
        Keyword arguments forwarded to *callable_obj*.

    Returns
    -------
    Any
        Whatever *callable_obj* returns.

    Raises
    ------
    AssertionError
        Wrapping the original exception when *callable_obj* raises.
    """
    try:
        return callable_obj(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"{callable_obj!r} raised {type(exc).__name__}: {exc}"
        ) from exc


def Assert_Raises_QWIM_Error(
    callable_obj: Any,
    /,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Assert that *callable_obj* raises a ``QWIM_Error`` (or subclass).

    Parameters
    ----------
    callable_obj : Any
        The callable to invoke.
    *args : Any
        Positional arguments forwarded to *callable_obj*.
    **kwargs : Any
        Keyword arguments forwarded to *callable_obj*.

    Raises
    ------
    AssertionError
        When *callable_obj* does not raise or raises a non-QWIM_Error.
    """
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"Module import unavailable: {_import_error_message}")

    try:
        callable_obj(*args, **kwargs)
    except Exception_QWIM_Error:
        return
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"Expected QWIM_Error but got {type(exc).__name__}: {exc}"
        ) from exc
    else:
        raise AssertionError(
            f"{callable_obj!r} did not raise QWIM_Error as expected"
        )
