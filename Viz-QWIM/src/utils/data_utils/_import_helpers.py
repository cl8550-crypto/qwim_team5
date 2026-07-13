"""Module-import helpers with a dependency-injection seam for testing.

Provides :func:`try_import_module`, a wrapper around ``importlib.import_module``
that returns ``None`` on ``ImportError`` instead of raising.  The optional
``_importer`` parameter lets tests exercise the failure branch without
touching ``sys.modules``.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-17)
"""

from __future__ import annotations

import importlib

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _validate_module_name_QWIM(
    *, module_name: str) -> str:
    """Validate and normalize a module name input.

    Parameters
    ----------
    module_name : str
        Module name supplied by the caller.

    Returns
    -------
    str
        Normalized module name with surrounding whitespace removed.

    Raises
    ------
    TypeError
        If *module_name* is not a string.
    ValueError
        If *module_name* is empty after normalization.
    """
    if not isinstance(module_name, str):
        raise TypeError("module_name must be a string")

    normalized_name = module_name.strip()
    if not normalized_name:
        raise ValueError("module_name must be a non-empty string")

    return normalized_name


def _resolve_importer_callable_QWIM(
    *, importer_callable: Callable[[str], ModuleType] | None) -> Callable[[str], ModuleType]:
    """Resolve and validate the importer callable used by try_import_module.

    Parameters
    ----------
    importer_callable : Callable[[str], ModuleType] | None
        Optional importer function supplied by the caller.

    Returns
    -------
    Callable[[str], ModuleType]
        Valid callable importer.

    Raises
    ------
    TypeError
        If *importer_callable* is provided but is not callable.
    """
    if importer_callable is None:
        return importlib.import_module

    if not callable(importer_callable):
        raise TypeError("_importer must be callable")

    return importer_callable


def try_import_module(
    *, module_name: str, _importer: Callable[[str], ModuleType] | None = None) -> ModuleType | None:
    """Attempt to import *module_name*; return ``None`` on ``ImportError``.

    This is a safer alternative to bare ``try: import X / except ImportError``
    patterns scattered across the codebase.  The ``_importer`` parameter is a
    testability seam: in tests pass a callable that raises ``ImportError`` to
    exercise the failure branch without modifying ``sys.modules``.

    Parameters
    ----------
    module_name : str
        Fully qualified module name to import (e.g. ``"anyio"``).
        Must be a non-empty string after surrounding whitespace is stripped.
    _importer : Callable[[str], ModuleType] | None
        Testability seam.  When provided, called instead of
        ``importlib.import_module``.  Must accept a single string argument and
        either return a module or raise ``ImportError``.

    Returns
    -------
    ModuleType | None
        The imported module, or ``None`` when import fails.

    Raises
    ------
    TypeError
        If *module_name* is not a string, or if ``_importer`` is provided
        and is not callable.
    ValueError
        If *module_name* is empty after whitespace normalization.

    Notes
    -----
    Exceptions other than :class:`ImportError` raised by the importer are
    intentionally propagated to the caller.

    Examples
    --------
    Normal usage — returns the module or ``None``:

    >>> anyio = try_import_module("anyio")
    >>> if anyio is not None:
    ...     print("anyio is available")

    Test usage — inject a failing importer to cover the ``None`` branch:

    >>> def _fail(name):
    ...     raise ImportError(f"forced: {name}")
    >>> assert try_import_module("anyio", _importer=_fail) is None
    """
    normalized_module_name = _validate_module_name_QWIM(module_name = module_name)
    loader = _resolve_importer_callable_QWIM(importer_callable = _importer)

    try:
        return loader(normalized_module_name)
    except ImportError:
        return None
