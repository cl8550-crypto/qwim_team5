"""Hypothesis (property-based) tests for api_reference_generation module.

Tests cover pure-function invariants for the public API:
- ``discover_python_files``: output is sorted, all items are .py Path objects
- ``path_to_module_name``: output is dot-separated, no path separators
- ``module_name_to_doc_path``: output ends in ``.md``, starts with api_prefix
- ``check_docstring_sections``: result keys are present; bool invariants hold

Key invariants tested:
- All file discovery outputs are sorted lists of Path objects
- Module name conversions contain no OS path separators
- Doc path outputs always end with ``.md``
- Section-check results contain expected keys with bool values
- ``has_params=False`` → ``missing_parameters`` is always False
- ``has_return_annotation=False`` → ``missing_returns`` is always False
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Discover_Python_Files
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Discover_Python_Files:
    """Property-based tests for discover_python_files."""

    @pytest.mark.unit()
    @given(include_init=st.booleans())
    @settings(max_examples=20)
    def Test_returns_sorted_list(self, tmp_path: Path, include_init: bool) -> None:
        """Output is always a sorted list of Path objects."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "z_mod.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "a_mod.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path, include_init_files=include_init)

        assert isinstance(result, list)
        assert result == sorted(result)

    @pytest.mark.unit()
    @given(include_init=st.booleans())
    @settings(max_examples=20)
    def Test_all_items_are_py_paths(self, tmp_path: Path, include_init: bool) -> None:
        """Every item in result is a Path with .py suffix."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "mod.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "other.txt").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path, include_init_files=include_init)

        for item in result:
            assert isinstance(item, Path)
            assert item.suffix == ".py"

    @pytest.mark.unit()
    @given(include_init=st.booleans())
    @settings(max_examples=20)
    def Test_empty_dir_returns_empty_list(self, tmp_path: Path, include_init: bool) -> None:
        """Empty directory returns an empty list, not an error."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        result = discover_python_files(root_directory = tmp_path, include_init_files=include_init)

        assert result == []

    @pytest.mark.unit()
    @given(include_init=st.booleans())
    @settings(max_examples=20)
    def Test_pycache_never_in_result(self, tmp_path: Path, include_init: bool) -> None:
        """__pycache__ directory contents are never included."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        pycache = tmp_path / "__pycache__"
        pycache.mkdir(exist_ok=True)
        (pycache / "mod.cpython-313.pyc.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "real.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path, include_init_files=include_init)

        assert all("__pycache__" not in str(p) for p in result)

    @pytest.mark.unit()
    @given(include_init=st.booleans())
    @settings(max_examples=20)
    def Test_nonexistent_dir_returns_empty(self, tmp_path: Path, include_init: bool) -> None:
        """Non-existent root directory returns an empty list."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        missing = tmp_path / "does_not_exist"

        result = discover_python_files(root_directory = missing, include_init_files=include_init)

        assert result == []


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Path_To_Module_Name
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Path_To_Module_Name:
    """Property-based tests for path_to_module_name."""

    @pytest.mark.unit()
    @given(
        parts=st.lists(
            st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True),
            min_size=1,
            max_size=4,
        )
    )
    @settings(max_examples=50)
    def Test_output_is_dot_separated_string(self, tmp_path: Path, parts: list[str]) -> None:
        """Output of path_to_module_name is a dot-separated string."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        sub = tmp_path
        for part in parts[:-1]:
            sub = sub / part
        sub.mkdir(parents=True, exist_ok=True)
        py_file = sub / f"{parts[-1]}.py"
        py_file.write_text("", encoding="utf-8")

        result = path_to_module_name(file_path = py_file, source_root = tmp_path)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "/" not in result
        assert "\\" not in result

    @pytest.mark.unit()
    @given(
        parts=st.lists(
            st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True),
            min_size=1,
            max_size=4,
        )
    )
    @settings(max_examples=50)
    def Test_output_contains_only_dots_and_identifiers(
        self, tmp_path: Path, parts: list[str]
    ) -> None:
        """Module name segments are valid Python identifiers joined by dots."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        sub = tmp_path
        for part in parts[:-1]:
            sub = sub / part
        sub.mkdir(parents=True, exist_ok=True)
        py_file = sub / f"{parts[-1]}.py"
        py_file.write_text("", encoding="utf-8")

        result = path_to_module_name(file_path = py_file, source_root = tmp_path)

        for segment in result.split("."):
            assert segment.isidentifier(), f"Segment {segment!r} is not a valid identifier"


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Module_Name_To_Doc_Path
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Module_Name_To_Doc_Path:
    """Property-based tests for module_name_to_doc_path."""

    @pytest.mark.unit()
    @given(
        module_name=st.from_regex(
            r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,3}", fullmatch=True
        )
    )
    @settings(max_examples=50)
    def Test_output_ends_with_md(self, module_name: str) -> None:
        """Output always ends with .md."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = module_name)

        assert result.endswith(".md")

    @pytest.mark.unit()
    @given(
        module_name=st.from_regex(
            r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,3}", fullmatch=True
        ),
        prefix=st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True),
    )
    @settings(max_examples=50)
    def Test_output_starts_with_prefix(self, module_name: str, prefix: str) -> None:
        """Output path starts with the provided api_prefix."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = module_name, api_prefix=prefix)

        assert result.startswith(prefix + "/") or result == prefix + ".md"

    @pytest.mark.unit()
    @given(
        module_name=st.from_regex(
            r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,3}", fullmatch=True
        )
    )
    @settings(max_examples=50)
    def Test_output_is_string(self, module_name: str) -> None:
        """Output is always a non-empty string."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = module_name)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    @given(
        bad_prefix=st.sampled_from(["", "   ", "bad/prefix", "bad\\prefix"]),
        module_name=st.from_regex(
            r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,3}", fullmatch=True
        ),
    )
    @settings(max_examples=20)
    def Test_invalid_prefix_raises_value_error(self, bad_prefix: str, module_name: str) -> None:
        """Invalid prefixes are rejected consistently."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        with pytest.raises(ValueError):
            module_name_to_doc_path(module_name = module_name, api_prefix=bad_prefix)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Check_Docstring_Sections
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Check_Docstring_Sections:
    """Property-based tests for check_docstring_sections."""

    @pytest.mark.unit()
    @given(
        docstring=st.text(min_size=0, max_size=200),
        has_params=st.booleans(),
        has_return=st.booleans(),
    )
    @settings(max_examples=100)
    def Test_result_has_required_keys(
        self, docstring: str, has_params: bool, has_return: bool
    ) -> None:
        """Result always contains 'missing_parameters' and 'missing_returns' keys."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(docstring = docstring, has_params = has_params, has_return_annotation = has_return)

        assert "missing_parameters" in result
        assert "missing_returns" in result

    @pytest.mark.unit()
    @given(
        docstring=st.text(min_size=0, max_size=200),
        has_params=st.booleans(),
        has_return=st.booleans(),
    )
    @settings(max_examples=100)
    def Test_result_values_are_booleans(
        self, docstring: str, has_params: bool, has_return: bool
    ) -> None:
        """Both result values are always booleans."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(docstring = docstring, has_params = has_params, has_return_annotation = has_return)

        assert isinstance(result["missing_parameters"], bool)
        assert isinstance(result["missing_returns"], bool)

    @pytest.mark.unit()
    @given(docstring=st.text(min_size=0, max_size=200))
    @settings(max_examples=50)
    def Test_no_params_means_not_missing_params(self, docstring: str) -> None:
        """When has_params=False, missing_parameters is always False."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(docstring = docstring, has_params=False, has_return_annotation=True)

        assert result["missing_parameters"] is False

    @pytest.mark.unit()
    @given(docstring=st.text(min_size=0, max_size=200))
    @settings(max_examples=50)
    def Test_no_return_means_not_missing_returns(self, docstring: str) -> None:
        """When has_return_annotation=False, missing_returns is always False."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(docstring = docstring, has_params=True, has_return_annotation=False)

        assert result["missing_returns"] is False

    @pytest.mark.unit()
    @given(docstring=st.text(min_size=0, max_size=200))
    @settings(max_examples=50)
    def Test_both_false_means_both_not_missing(self, docstring: str) -> None:
        """When both flags False, neither section is reported missing."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(
            docstring = docstring, has_params=False, has_return_annotation=False
        )

        assert result["missing_parameters"] is False
        assert result["missing_returns"] is False
