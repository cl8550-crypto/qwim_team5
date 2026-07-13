"""Private docstring helpers for API reference generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _scan_docstring_section_headings(*, docstring: str) -> set[str]:
    """Collect NumPy-style section headings from a raw docstring."""
    section_headings: set[str] = set()
    lines = docstring.splitlines()

    for current_line, next_line in zip(lines, lines[1:]):
        current_stripped = current_line.strip()
        next_stripped = next_line.strip()
        if current_stripped and set(next_stripped) == {"-"} and len(next_stripped) >= 3:
            section_headings.add(current_stripped.lower())

    return section_headings


def _check_docstring_sections_impl(
    *, docstring: str, has_params: bool, has_return_annotation: bool) -> dict[str, bool]:
    """Check whether a NumPy docstring contains required sections."""
    section_headings = _scan_docstring_section_headings(docstring = docstring)
    missing_parameters = has_params and "parameters" not in section_headings
    missing_returns = has_return_annotation and "returns" not in section_headings

    return {
        "missing_parameters": missing_parameters,
        "missing_returns": missing_returns,
    }


def _inventory_strict_docstrings_impl(
    *, root_directory: Path, exclude_patterns: tuple[str, ...] | None, ast_module: Any, discover_python_files_func: Any, check_module_docstring_func: Any, check_object_docstrings_func: Any, check_docstring_sections_func: Any) -> list[dict[str, Any]]:
    """Inventory documentation gaps using the injected public dependencies."""
    python_files = discover_python_files_func(
        root_directory=root_directory,
        exclude_patterns=exclude_patterns,
        include_init_files=True,
    )

    all_issues: list[dict[str, Any]] = []

    for source_file in python_files:
        file_str = str(source_file)

        if not check_module_docstring_func(file_path=source_file):
            all_issues.append(
                {
                    "file": file_str,
                    "line": 1,
                    "kind": "module",
                    "name": file_str,
                    "issue": "missing_docstring",
                },
            )

        missing_objects = check_object_docstrings_func(file_path=source_file)
        for entry in missing_objects:
            if entry["object_type"] == "module":
                continue
            all_issues.append(
                {
                    "file": file_str,
                    "line": entry["line"],
                    "kind": entry["object_type"],
                    "name": entry["name"],
                    "issue": "missing_docstring",
                },
            )

        try:
            source_text = source_file.read_text(encoding="utf-8")
            tree = ast_module.parse(source_text, filename=file_str)
        except (OSError, SyntaxError):
            continue

        for node in ast_module.walk(tree):
            if not isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
                continue

            raw_docstring = ast_module.get_docstring(node)
            if not raw_docstring:
                continue

            arg_names = [
                arg.arg for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs
            ]
            if node.args.vararg:
                arg_names.append(node.args.vararg.arg)
            if node.args.kwarg:
                arg_names.append(node.args.kwarg.arg)

            non_self_args = [arg_name for arg_name in arg_names if arg_name not in ("self", "cls")]
            needs_params = len(non_self_args) > 0

            has_return = False
            if node.returns is not None and not (
                isinstance(node.returns, ast_module.Constant) and node.returns.value is None
            ):
                has_return = True

            issues = check_docstring_sections_func(
                docstring=raw_docstring,
                has_params=needs_params,
                has_return_annotation=has_return,
            )
            func_kind = (
                "async_function" if isinstance(node, ast_module.AsyncFunctionDef) else "function"
            )

            if issues["missing_parameters"]:
                all_issues.append(
                    {
                        "file": file_str,
                        "line": node.lineno,
                        "kind": func_kind,
                        "name": node.name,
                        "issue": "missing_parameters_section",
                    },
                )

            if issues["missing_returns"]:
                all_issues.append(
                    {
                        "file": file_str,
                        "line": node.lineno,
                        "kind": func_kind,
                        "name": node.name,
                        "issue": "missing_returns_section",
                    },
                )

    return sorted(all_issues, key=lambda entry: (entry["file"], entry["line"]))