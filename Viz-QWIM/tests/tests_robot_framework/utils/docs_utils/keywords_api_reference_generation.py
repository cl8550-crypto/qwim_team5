"""Robot Framework keyword library for api_reference_generation tests.

Keyword wrappers for:
- discover_python_files: file discovery, exclusion, sorting
- path_to_module_name: path-to-dotted-name conversion
- module_name_to_doc_path: dotted-name-to-doc-path construction
- check_docstring_sections: missing-section detection

Author:
    QWIM Development Team

Version:
    0.1.0

Last Modified:
    2026-05-27
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[5]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.utils.docs_utils.api_reference_generation import (
        check_docstring_sections,
        discover_python_files,
        module_name_to_doc_path,
        path_to_module_name,
    )
    import logging as _logging

    _logger = _logging.getLogger(__name__)
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging

    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: %s", _exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"api_reference_generation could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Discovery keywords
# ===========================================================================


def module_is_importable() -> bool:
    """Return True if the api_reference_generation module can be imported."""
    return MODULE_IMPORT_AVAILABLE


def discover_files_in_temp_dir(num_files: int = 2) -> list[str]:
    """Create a temp dir with Python files and return the discovered paths as strings.

    Parameters
    ----------
    num_files : int
        Number of .py files to create (default 2).

    Returns
    -------
    list[str]
        Sorted list of discovered file paths as strings.
    """
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    for idx in range(int(num_files)):
        (tmp / f"mod_{idx}.py").write_text(f"x = {idx}", encoding="utf-8")

    result = discover_python_files(root_directory = tmp)
    return [str(p) for p in result]


def discover_files_count_should_equal(expected: int, num_files: int = 2) -> None:
    """Assert that discover_python_files returns the expected number of files.

    Parameters
    ----------
    expected : int
        Expected number of discovered files.
    num_files : int
        Number of .py files to create (default 2).
    """
    paths = discover_files_in_temp_dir(num_files=num_files)
    actual = len(paths)
    assert actual == int(expected), f"Expected {expected} files, found {actual}: {paths}"


def discover_files_excludes_pycache() -> None:
    """Assert that __pycache__ contents are excluded from discovery."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    pycache = tmp / "__pycache__"
    pycache.mkdir()
    (pycache / "mod.py").write_text("", encoding="utf-8")
    (tmp / "real.py").write_text("", encoding="utf-8")

    result = discover_python_files(root_directory = tmp)
    for item_path in result:
        assert "__pycache__" not in str(item_path), (
            f"__pycache__ path found in result: {item_path}"
        )


def discover_files_excludes_init_by_default() -> None:
    """Assert that __init__.py is excluded by default."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    (tmp / "__init__.py").write_text("", encoding="utf-8")
    (tmp / "real.py").write_text("", encoding="utf-8")

    result = discover_python_files(root_directory = tmp)
    names = [p.name for p in result]
    assert "__init__.py" not in names, f"__init__.py found in result: {names}"


# ===========================================================================
# Module-name conversion keywords
# ===========================================================================


def path_to_module_name_has_no_separators() -> None:
    """Assert that path_to_module_name output contains no OS path separators."""
    _require_imports()
    tmp = Path(tempfile.mkdtemp())
    sub = tmp / "utils"
    sub.mkdir()
    py_file = sub / "helper.py"
    py_file.write_text("", encoding="utf-8")

    result = path_to_module_name(file_path = py_file, source_root = tmp)
    assert "/" not in result, f"Forward slash in module name: {result}"
    assert "\\" not in result, f"Back slash in module name: {result}"


def module_name_to_doc_path_ends_with_md(module_name: str = "src.utils.helper") -> str:
    """Return doc path and assert it ends with .md.

    Parameters
    ----------
    module_name : str
        Dotted module name to convert (default 'src.utils.helper').

    Returns
    -------
    str
        The resulting documentation path.
    """
    _require_imports()
    result = module_name_to_doc_path(module_name = str(module_name))
    assert result.endswith(".md"), f"Expected .md suffix, got: {result}"
    return result


def module_name_to_doc_path_starts_with_prefix(
    prefix: str = "api",
    module_name: str = "src.utils.helper",
) -> None:
    """Assert that the doc path starts with the given prefix.

    Parameters
    ----------
    prefix : str
        Expected path prefix (default 'api').
    module_name : str
        Dotted module name to convert (default 'src.utils.helper').
    """
    _require_imports()
    result = module_name_to_doc_path(module_name = str(module_name), api_prefix=str(prefix))
    assert result.startswith(str(prefix) + "/"), (
        f"Expected prefix {prefix!r}/, got: {result}"
    )


def module_name_to_doc_path_invalid_prefix_raises_value_error(
    module_name: str = "src.utils.helper",
) -> None:
    """Assert that invalid prefixes are rejected by module_name_to_doc_path."""
    _require_imports()
    try:
        module_name_to_doc_path(module_name = str(module_name), api_prefix="bad/prefix")
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised")


# ===========================================================================
# Docstring-section check keywords
# ===========================================================================


def check_sections_no_missing_when_both_present() -> None:
    """Assert both section flags are False when docstring has both sections."""
    _require_imports()
    docstring = (
        "Summary line.\n\nParameters\n----------\n    x : int\n\nReturns\n-------\n    int"
    )
    result = check_docstring_sections(docstring = docstring, has_params=True, has_return_annotation=True)
    assert result["missing_parameters"] is False, "Expected missing_parameters=False"
    assert result["missing_returns"] is False, "Expected missing_returns=False"


def check_sections_missing_when_params_absent() -> None:
    """Assert missing_parameters is True when Parameters section is absent."""
    _require_imports()
    result = check_docstring_sections(
        docstring = "Summary only.", has_params=True, has_return_annotation=False
    )
    assert result["missing_parameters"] is True, "Expected missing_parameters=True"


def check_sections_no_missing_params_when_flag_false() -> None:
    """Assert missing_parameters is False when has_params=False."""
    _require_imports()
    result = check_docstring_sections(
        docstring = "Summary only.", has_params=False, has_return_annotation=True
    )
    assert result["missing_parameters"] is False, "Expected missing_parameters=False"


def check_sections_no_missing_returns_when_flag_false() -> None:
    """Assert missing_returns is False when has_return_annotation=False."""
    _require_imports()
    result = check_docstring_sections(
        docstring = "Summary only.", has_params=True, has_return_annotation=False
    )
    assert result["missing_returns"] is False, "Expected missing_returns=False"
