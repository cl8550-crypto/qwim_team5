"""API reference documentation generation utilities for QWIM projects.

This module provides pure functions for discovering Python modules,
mapping file paths to module names and documentation paths, building
navigation models, generating ``SUMMARY.md`` content for
``mkdocs-literate-nav``, and inventorying objects that are missing
NumPy-style docstrings.

All functions are pure or read-only (no writes to the file system) and
import **no project-specific modules**, making them safe to use during
``properdocs build`` without triggering Shiny, reactive, or other heavy
import-time side effects.

Constants
---------
DEFAULT_EXCLUDE_PATTERNS
    Directory and file-name fragments excluded by default during discovery
    (e.g. ``__pycache__``, ``.venv``, ``temp``, ``htmlcov``, ``site``).
API_DOC_PREFIX
    Top-level directory prefix for generated API documentation pages.

Functions
---------
discover_python_files
    Discover all Python source files under a root directory.
path_to_module_name
    Convert a Python file path to an importable dotted module name.
module_name_to_doc_path
    Convert a dotted module name to a generated documentation path.
build_path_to_module_mapping
    Build a mapping from file paths to module names for many files at once.
build_module_to_doc_mapping
    Build a mapping from module names to documentation paths.
build_navigation_tree
    Build a nested navigation tree from a list of generated doc paths.
build_api_reference_file_mapping
    Build the full generated API reference file set and page contents.
generate_summary_md
    Generate ``SUMMARY.md`` content for ``mkdocs-literate-nav``.
generate_api_page_content
    Generate a ``mkdocstrings`` directive Markdown page for one module.
check_module_docstring
    Check whether a Python file has a non-empty module-level docstring.
check_object_docstrings
    Return all objects in a Python file that are missing docstrings.
inventory_missing_docstrings
    Inventory every object missing docstrings under a root directory.
check_docstring_sections
    Check whether a NumPy docstring contains required sections.
inventory_strict_docstrings
    Stricter inventory: checks module docstrings, object docstrings, and
    section completeness (``Parameters``, ``Returns``) where required.

Examples
--------
>>> from pathlib import Path
>>> from src.utils.docs_utils.api_reference_generation import (
...     discover_python_files,
...     build_path_to_module_mapping,
...     build_module_to_doc_mapping,
...     build_navigation_tree,
...     generate_summary_md,
... )
>>> workspace = Path(".")
>>> files = discover_python_files(workspace / "src")
>>> path_map = build_path_to_module_mapping(files, workspace)
>>> doc_map = build_module_to_doc_mapping(list(path_map.values()))
>>> tree = build_navigation_tree(list(doc_map.values()))
>>> summary = generate_summary_md(tree)
"""

from __future__ import annotations

import ast

from pathlib import Path
from typing import Any

from ._api_reference_generation_docstrings import (
    _check_docstring_sections_impl,
    _inventory_strict_docstrings_impl,
)


# ==============================================================================
# Constants
# ==============================================================================

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ty_cache",
    "htmlcov",
    "site",
    "node_modules",
    "*.egg-info",
    "temp",
)

API_DOC_PREFIX: str = "api"


def _validate_api_prefix_QWIM(
    *, api_prefix: str) -> str:
    """Validate and normalize the API docs top-level prefix.

    Parameters
    ----------
    api_prefix : str
        Top-level generated docs prefix (for example ``"api"``).

    Returns
    -------
    str
        Validated prefix.

    Raises
    ------
    ValueError
        If *api_prefix* is empty, contains only whitespace, or includes
        path separators.
    """
    if not isinstance(api_prefix, str) or not api_prefix.strip():
        raise ValueError("api_prefix must be a non-empty string")

    normalized_prefix = api_prefix.strip()
    if "/" in normalized_prefix or "\\" in normalized_prefix:
        raise ValueError("api_prefix must be a single path segment without slashes")

    return normalized_prefix


# ==============================================================================
# File Discovery
# ==============================================================================


def discover_python_files(
    *, root_directory: Path, exclude_patterns: tuple[str, ...] | None = None, include_init_files: bool = False) -> list[Path]:
    """Discover all Python source files under a root directory.

    Parameters
    ----------
    root_directory : Path
        Root directory to search recursively for Python files.
    exclude_patterns : tuple[str, ...] | None, optional
        Directory or file-name fragments to exclude from discovery.
        If ``None``, :data:`DEFAULT_EXCLUDE_PATTERNS` is used.
    include_init_files : bool, optional
        When ``False`` (default), ``__init__.py`` files are excluded
        because they typically only contain re-exports and their
        package-level API is documented via the parent package name.

    Returns
    -------
    list[Path]
        Sorted list of discovered Python file paths.

    Notes
    -----
    This function reads the file system but does not modify it.
    Output is deterministic for a given directory state.

    Examples
    --------
    >>> from pathlib import Path
    >>> files = discover_python_files(Path("src"))
    >>> all(p.suffix == ".py" for p in files)
    True
    """
    if not isinstance(root_directory, Path):
        root_directory = Path(root_directory)

    patterns = exclude_patterns if exclude_patterns is not None else DEFAULT_EXCLUDE_PATTERNS

    def _is_excluded(*, candidate: Path) -> bool:
        """Return True if *candidate* matches any exclusion pattern."""
        for part in candidate.parts:
            for pattern in patterns:
                if pattern.startswith("*"):
                    if part.endswith(pattern[1:]):
                        return True
                elif part == pattern:
                    return True
        return False

    discovered = [
        candidate
        for candidate in root_directory.rglob("*.py")
        if (include_init_files or candidate.name != "__init__.py") and not _is_excluded(candidate = candidate)
    ]
    return sorted(discovered)


def path_to_module_name(
    *, file_path: Path | str, source_root: Path | str) -> str:
    """Convert a Python file path to an importable dotted module name."""
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if not isinstance(source_root, Path):
        source_root = Path(source_root)

    try:
        relative = file_path.relative_to(source_root)
    except ValueError:
        raise ValueError(
            f"file_path {file_path!r} is not under source_root {source_root!r}",
        ) from None

    parts = list(relative.parts)

    if not parts[-1].endswith(".py"):
        raise ValueError(f"file_path {file_path!r} is not a Python (.py) file")

    # Strip the .py extension from the last segment
    parts[-1] = parts[-1][:-3]

    # __init__ files represent the parent package
    if parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        raise ValueError(
            f"file_path {file_path!r} resolves to an empty module name relative to {source_root!r}",
        )

    return ".".join(parts)


def module_name_to_doc_path(
    *, module_name: str, api_prefix: str = API_DOC_PREFIX) -> str:
    """Convert a dotted module name to the generated documentation path.

    Parameters
    ----------
    module_name : str
        Dotted module name such as
        ``src.utils.docs_utils.api_reference_generation``.
    api_prefix : str, optional
        Top-level prefix for all generated API documentation files.
        Defaults to :data:`API_DOC_PREFIX` (``"api"``).

    Returns
    -------
    str
        Forward-slash documentation path suitable for use in
        ``mkdocs_gen_files.open()``, such as
        ``api/src/utils/docs_utils/api_reference_generation.md``.

    Raises
    ------
    ValueError
        If *module_name* is empty or *api_prefix* is invalid.

    Examples
    --------
    >>> module_name_to_doc_path("src.utils.docs_utils.api_reference_generation")
    'api/src/utils/docs_utils/api_reference_generation.md'

    >>> module_name_to_doc_path("src.utils", api_prefix="reference")
    'reference/src/utils.md'
    """
    if not module_name:
        raise ValueError("module_name must not be empty")

    normalized_prefix = _validate_api_prefix_QWIM(api_prefix = api_prefix)

    segments = module_name.split(".")
    return normalized_prefix + "/" + "/".join(segments) + ".md"


# ==============================================================================
# Bulk Mapping Builders
# ==============================================================================


def build_path_to_module_mapping(
    *, python_files: list[Path], source_root: Path) -> dict[Path, str]:
    """Build a mapping from file paths to dotted module names.

    Parameters
    ----------
    python_files : list[Path]
        Python file paths to process.
    source_root : Path
        Root directory used to compute each module name.

    Returns
    -------
    dict[Path, str]
        Sorted dictionary mapping file paths to dotted module names.
        Files for which a module name cannot be computed are silently
        excluded.

    Notes
    -----
    Pure function: does not modify any of its inputs.

    Examples
    --------
    >>> from pathlib import Path
    >>> mapping = build_path_to_module_mapping(
    ...     [Path("src/utils/docs_utils/api_reference_generation.py")],
    ...     Path("."),
    ... )
    >>> list(mapping.values())
    ['src.utils.docs_utils.api_reference_generation']
    """
    result: dict[Path, str] = {}

    for item_path in python_files:
        try:
            module_name = path_to_module_name(file_path = item_path, source_root = source_root)
            result[item_path] = module_name
        except ValueError:
            pass  # Skip unmappable files

    return dict(sorted(result.items()))


def build_module_to_doc_mapping(
    *, module_names: list[str], api_prefix: str = API_DOC_PREFIX) -> dict[str, str]:
    """Build a mapping from module names to documentation paths.

    Parameters
    ----------
    module_names : list[str]
        Dotted module names to map.
    api_prefix : str, optional
        Prefix for all generated documentation paths.
        Defaults to :data:`API_DOC_PREFIX`.

    Returns
    -------
    dict[str, str]
        Sorted dictionary mapping dotted module names to forward-slash
        documentation paths.

    Notes
    -----
    Pure function: does not modify any of its inputs.
    Empty strings in *module_names* are silently excluded.

    Raises
    ------
    ValueError
        If *api_prefix* is invalid.

    Examples
    --------
    >>> mapping = build_module_to_doc_mapping(["src.utils.foo", "src.utils.bar"])
    >>> mapping["src.utils.foo"]
    'api/src/utils/foo.md'
    """
    normalized_prefix = _validate_api_prefix_QWIM(api_prefix = api_prefix)

    result: dict[str, str] = {
        item_module: module_name_to_doc_path(module_name = item_module, api_prefix = normalized_prefix)
        for item_module in module_names
        if item_module
    }
    return dict(sorted(result.items()))


# ==============================================================================
# Navigation Tree
# ==============================================================================


def build_navigation_tree(
    *, doc_paths: list[str], api_prefix: str = API_DOC_PREFIX) -> dict[str, Any]:
    """Build a nested navigation tree from a list of generated doc paths.

    The resulting tree maps each path segment to either a ``str`` leaf
    (the relative doc path used in ``SUMMARY.md``) or a ``dict`` sub-tree
    (representing a directory).  When a segment name is used as both a leaf
    and a directory (which occurs when a package ``__init__.py`` has the same
    name as its containing directory), the leaf is moved under the special
    key ``"__leaf__"`` inside the promoted directory dict.

    Parameters
    ----------
    doc_paths : list[str]
        Documentation paths as returned by :func:`module_name_to_doc_path`,
        e.g. ``["api/src/utils/foo.md", "api/tests/test_bar.md"]``.
    api_prefix : str, optional
        Top-level prefix stripped from paths when building relative
        ``SUMMARY.md`` links.  Defaults to :data:`API_DOC_PREFIX`.

    Returns
    -------
    dict[str, Any]
        Nested dict where leaf values are ``str`` relative doc paths and
        interior values are ``dict`` sub-trees.

    Raises
    ------
    ValueError
        If *api_prefix* is invalid.

    Notes
    -----
    Pure function: does not access the file system.
    All path separators in the output are forward slashes.

    Examples
    --------
    >>> tree = build_navigation_tree(["api/src/utils/foo.md"])
    >>> tree["src"]["utils"]["foo"]
    'src/utils/foo.md'
    """
    normalized_prefix = _validate_api_prefix_QWIM(api_prefix = api_prefix)
    tree: dict[str, Any] = {}

    for item_path in sorted(doc_paths):
        # Normalise to forward slashes (Windows safety)
        normalised = item_path.replace("\\", "/")

        # Strip the api_prefix so paths in SUMMARY.md are relative to docs/api/
        prefix_sep = normalized_prefix + "/"
        relative = normalised.removeprefix(prefix_sep)

        parts = relative.split("/")
        current = tree

        # Build intermediate directory nodes
        for item_dir in parts[:-1]:
            if item_dir not in current:
                current[item_dir] = {}
            elif isinstance(current[item_dir], str):
                # Promote a pre-existing leaf to a directory
                current[item_dir] = {"__leaf__": current[item_dir]}
            current = current[item_dir]

        # Insert the leaf
        leaf_raw = parts[-1]
        leaf_key = leaf_raw.removesuffix(".md")
        current[leaf_key] = relative

    return tree


def build_api_reference_file_mapping(
    *, workspace_root: Path, index_page_content: str, api_prefix: str = API_DOC_PREFIX) -> dict[str, str]:
    r"""Build every generated API reference file and its Markdown content.

    The returned mapping is suitable for two write targets:

    1. The ProperDocs virtual file system via ``mkdocs_gen_files.open()``.
    2. A transient on-disk mirror under ``docs/api/`` for local inspection.

    Parameters
    ----------
    workspace_root : Path
        Repository root containing the top-level ``src/``, ``tests/``, and
        ``docs/`` directories.
    index_page_content : str
        Markdown content for the generated API landing page.
    api_prefix : str, optional
        Top-level documentation prefix for generated files.  Defaults to
        :data:`API_DOC_PREFIX`.

    Returns
    -------
    dict[str, str]
        Sorted mapping from docs-relative file path to Markdown content.
        Includes one module page per discovered Python file plus
        ``<api_prefix>/index.md`` and ``<api_prefix>/SUMMARY.md``.

    Raises
    ------
    ValueError
        If *api_prefix* is invalid.

    Notes
    -----
    This function reads the file system but does not modify it.
    Output is deterministic for a given repository state.

    Examples
    --------
    >>> from pathlib import Path
    >>> mapping = build_api_reference_file_mapping(
    ...     workspace_root=Path("."),
    ...     index_page_content="# API Reference\n",
    ... )
    >>> "api/index.md" in mapping
    True
    >>> "api/SUMMARY.md" in mapping
    True
    """
    if not isinstance(workspace_root, Path):
        workspace_root = Path(workspace_root)

    normalized_prefix = _validate_api_prefix_QWIM(api_prefix = api_prefix)

    generated_files: dict[str, str] = {}
    all_doc_paths: list[str] = []

    for root_directory in (
        workspace_root / "src",
        workspace_root / "tests",
    ):
        python_files = discover_python_files(root_directory = root_directory)
        path_to_module = build_path_to_module_mapping(
            python_files = python_files,
            source_root = workspace_root,
        )
        for module_name in path_to_module.values():
            doc_path = module_name_to_doc_path(
                module_name = module_name,
                api_prefix=normalized_prefix,
            )
            generated_files[doc_path] = generate_api_page_content(module_name = module_name)
            all_doc_paths.append(doc_path)

    generated_files[f"{normalized_prefix}/index.md"] = index_page_content

    nav_tree = build_navigation_tree(
        doc_paths = all_doc_paths,
        api_prefix=normalized_prefix,
    )
    summary_body = generate_summary_md(nav_tree = nav_tree)
    generated_files[f"{normalized_prefix}/SUMMARY.md"] = (
        "* [Overview](index.md)\n" + summary_body
    )

    return dict(sorted(generated_files.items()))


def generate_summary_md(
    *, nav_tree: dict[str, Any], indent: int = 0, indent_size: int = 4) -> str:
    """Generate ``SUMMARY.md`` content for ``mkdocs-literate-nav``.

    Recursively walks *nav_tree* and produces a nested Markdown unordered
    list.  Leaf nodes produce ``* [name](path)`` links; directory nodes
    produce ``* name`` section headers with indented children.  Keys whose
    names begin with ``"__"`` (internal markers such as ``"__leaf__"``) are
    skipped.

    Parameters
    ----------
    nav_tree : dict[str, Any]
        Nested navigation tree as returned by :func:`build_navigation_tree`.
    indent : int, optional
        Current indentation offset in spaces.  Callers should leave this at
        the default value of ``0``; the function sets it recursively.
    indent_size : int, optional
        Number of additional spaces added per nesting level.  Default is 4.

    Returns
    -------
    str
        Multi-line string containing the ``SUMMARY.md`` content.

    Notes
    -----
    Pure function: does not modify its inputs or access the file system.

    Examples
    --------
    >>> tree = {"src": {"utils": {"foo": "src/utils/foo.md"}}}
    >>> print(generate_summary_md(tree))
    * src
        * utils
            * [foo](src/utils/foo.md)
    """
    if isinstance(indent_size, bool):
        indent_size = 4

    lines: list[str] = []
    spaces = " " * indent

    for item_key in sorted(nav_tree.keys()):
        if item_key.startswith("__"):
            # Skip internal marker keys
            continue

        item_value = nav_tree[item_key]

        if isinstance(item_value, str):
            # Leaf node → clickable link
            lines.append(f"{spaces}* [{item_key}]({item_value})")
        else:
            # Directory node → section header (no link)
            lines.append(f"{spaces}* {item_key}")
            child_text = generate_summary_md(
                nav_tree = item_value,
                indent = indent + indent_size,
                indent_size = indent_size,
            )
            if child_text:
                lines.append(child_text)

    return "\n".join(lines)


# ==============================================================================
# API Page Content Generation
# ==============================================================================


def generate_api_page_content(
    *, module_name: str) -> str:
    """Generate a ``mkdocstrings`` directive Markdown page for one module.

    Produces a Markdown document containing an H1 heading followed by the
    ``:::`` autodoc directive consumed by ``mkdocstrings[python]`` during
    ``mkdocs build``.

    Parameters
    ----------
    module_name : str
        Dotted module name such as
        ``src.utils.docs_utils.api_reference_generation``.

    Returns
    -------
    str
        Markdown content string ready to be written to the generated doc
        page.

    Notes
    -----
    Pure function: no I/O, no side effects.

    Examples
    --------
    >>> content = generate_api_page_content("src.utils.foo")
    >>> "::: src.utils.foo" in content
    True
    >>> content.startswith("# foo")
    True
    """
    title = module_name.rsplit(".", maxsplit=1)[-1]
    return f"# {title}\n\n::: {module_name}\n"


# ==============================================================================
# AST-Based Docstring Inspection
# ==============================================================================


def check_module_docstring(
    *, file_path: Path) -> bool:
    """Check whether a Python file has a non-empty module-level docstring.

    Parameters
    ----------
    file_path : Path
        Path to the Python source file to inspect.

    Returns
    -------
    bool
        ``True`` if the file parses successfully and has a non-empty
        module-level docstring; ``False`` otherwise (including when the
        file cannot be parsed or read).

    Notes
    -----
    Uses Python's :mod:`ast` module to inspect the file without executing
    it.  This avoids side effects from module-level code such as Shiny
    reactive definitions.

    Examples
    --------
    >>> from pathlib import Path
    >>> check_module_docstring(Path("src/utils/docs_utils/api_reference_generation.py"))
    True
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError, ValueError):
        return False

    return bool(ast.get_docstring(tree))


def check_object_docstrings(
    *, file_path: Path) -> list[dict[str, Any]]:
    """Return all Python objects in a file that are missing docstrings.

    Checks the module itself, every class, every function (including
    async functions), and every method — including private helpers whose
    names begin with ``_``.

    Parameters
    ----------
    file_path : Path
        Path to the Python source file to inspect.

    Returns
    -------
    list[dict[str, Any]]
        List of dicts, one per object that is missing a docstring.
        Each dict contains the keys:

        ``file`` : str
            Absolute or relative path to the source file.
        ``name`` : str
            Name of the object (or the file name for the module).
        ``object_type`` : str
            ``"module"``, ``"class"``, or ``"function"``.
        ``line`` : int
            Line number where the object is defined.
        ``has_docstring`` : bool
            Always ``False`` for entries in this list.

        Returns an empty list when the file cannot be parsed or read.

    Notes
    -----
    Uses Python's :mod:`ast` module.  The AST walk visits nested classes
    and functions, so inner helpers are also reported.

    Examples
    --------
    >>> from pathlib import Path
    >>> missing = check_object_docstrings(Path("src/utils/docs_utils/api_reference_generation.py"))
    >>> missing  # Should be empty — module is fully documented
    []
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError, ValueError):
        return []

    missing: list[dict[str, Any]] = []
    file_str = str(file_path)

    # Check module-level docstring
    if not ast.get_docstring(tree):
        missing.append(
            {
                "file": file_str,
                "name": file_path.name,
                "object_type": "module",
                "line": 1,
                "has_docstring": False,
            },
        )

    # Check all classes and functions recursively
    for item_node in ast.walk(tree):
        if isinstance(
            item_node,
            ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        ) and not ast.get_docstring(item_node):
            obj_type = "class" if isinstance(item_node, ast.ClassDef) else "function"
            missing.append(
                {
                    "file": file_str,
                    "name": item_node.name,
                    "object_type": obj_type,
                    "line": item_node.lineno,
                    "has_docstring": False,
                },
            )

    return missing


def inventory_missing_docstrings(
    *, root_directory: Path, exclude_patterns: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """Inventory every Python object missing a docstring under a root directory.

    Combines :func:`discover_python_files` and :func:`check_object_docstrings`
    to produce a full report of documentation gaps.  ``__init__.py`` files
    are included in this scan (``include_init_files=True``) because package
    docstrings should also be validated.

    Parameters
    ----------
    root_directory : Path
        Root directory to search for Python files.
    exclude_patterns : tuple[str, ...] | None, optional
        Patterns to exclude from discovery.  If ``None``, uses
        :data:`DEFAULT_EXCLUDE_PATTERNS`.

    Returns
    -------
    list[dict[str, Any]]
        Combined list of dicts from :func:`check_object_docstrings` for
        every discovered file, sorted first by ``file`` path then by
        ``line`` number.

    Notes
    -----
    This function reads the file system but does not modify it.
    It performs full AST parsing of every file, so it may be slow
    for large repositories.

    Examples
    --------
    >>> from pathlib import Path
    >>> gaps = inventory_missing_docstrings(Path("src/utils/docs_utils"))
    >>> gaps  # Should be empty — this package is fully documented
    []
    """
    python_files = discover_python_files(
        root_directory = root_directory,
        exclude_patterns=exclude_patterns,
        include_init_files=True,
    )

    all_missing: list[dict[str, Any]] = []
    for item_file in python_files:
        all_missing.extend(check_object_docstrings(file_path = item_file))

    return sorted(all_missing, key=lambda entry: (entry["file"], entry["line"]))


# ==============================================================================
# Strict docstring-section checkers (Phase C)
# ==============================================================================


def check_docstring_sections(
    *, docstring: str, has_params: bool, has_return_annotation: bool) -> dict[str, bool]:
    r"""Check whether a NumPy docstring contains required sections.

    A NumPy-style docstring is expected to include a ``Parameters`` section
    whenever the callable has at least one non-``self`` / non-``cls``
    parameter, and a ``Returns`` section whenever the callable has a
    non-``None`` return annotation.

    This function performs a simple line-by-line scan — it does not parse the
    full NumPy section grammar.  Any heading of the form ``<name>\\n---+``
    (i.e. a title followed immediately by a line of dashes) is recognised as
    a section heading.

    Parameters
    ----------
    docstring : str
        The raw docstring text to inspect.
    has_params : bool
        ``True`` when the callable declares at least one non-``self`` /
        non-``cls`` parameter.
    has_return_annotation : bool
        ``True`` when the callable has a return annotation other than
        ``None`` or no annotation at all (caller decides the convention;
        see :func:`inventory_strict_docstrings`).

    Returns
    -------
    dict[str, bool]
        Mapping with keys ``"missing_parameters"`` and
        ``"missing_returns"``.  A value of ``True`` means the section is
        **absent** from the docstring while it **was** required.

    Examples
    --------
    >>> result = check_docstring_sections("Summary only.", True, True)
    >>> result["missing_parameters"]
    True
    >>> result["missing_returns"]
    True
    >>> result = check_docstring_sections(
    ...     "Summary.\\n\\nParameters\\n----------\\n    x : int\\nReturns\\n-------\\n    int",
    ...     True,
    ...     True,
    ... )
    >>> result["missing_parameters"]
    False
    >>> result["missing_returns"]
    False
    """
    lines = docstring.splitlines()
    section_headings: set[str] = set()

    for idx in range(len(lines) - 1):
        current_stripped = lines[idx].strip()
        next_stripped = lines[idx + 1].strip()
        if current_stripped and set(next_stripped) == {"-"} and len(next_stripped) >= 3:
            section_headings.add(current_stripped.lower())

    missing_parameters = has_params and "parameters" not in section_headings
    missing_returns = has_return_annotation and "returns" not in section_headings

    return {
        "missing_parameters": missing_parameters,
        "missing_returns": missing_returns,
    }


def inventory_strict_docstrings(
    *, root_directory: Path, exclude_patterns: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """Inventory module and callable docstring gaps with strict section rules."""
    return _inventory_strict_docstrings_impl(
        root_directory = root_directory,
        exclude_patterns = exclude_patterns,
        ast_module=ast,
        discover_python_files_func=discover_python_files,
        check_module_docstring_func=check_module_docstring,
        check_object_docstrings_func=check_object_docstrings,
        check_docstring_sections_func=check_docstring_sections,
    )
