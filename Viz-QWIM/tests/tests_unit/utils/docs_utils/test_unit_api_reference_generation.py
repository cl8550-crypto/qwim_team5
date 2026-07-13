"""Unit tests for src.utils.docs_utils.api_reference_generation.

Tests cover every public function in the module, targeting ≥ 90 % line
coverage and 100 % branch coverage.  All branches exercised include the
normal path, edge cases (empty inputs, unusual file structures), and
error paths (invalid paths, unparseable files).

All tests use ``tmp_path`` for file system interaction so they are
hermetic and do not depend on the state of the real workspace.
"""

from __future__ import annotations

import pytest


# ==============================================================================
# Class_Test_Discover_Python_Files
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Discover_Python_Files:
    """Tests for discover_python_files."""

    @pytest.mark.unit()
    def Test_returns_sorted_py_files(self, tmp_path):
        """Return a sorted list of .py files when the directory is non-empty."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "b_module.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "a_module.py").write_text("x = 1", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c_module.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path)

        assert result == sorted(result)
        names = [p.name for p in result]
        assert "a_module.py" in names
        assert "b_module.py" in names
        assert "c_module.py" in names

    @pytest.mark.unit()
    def Test_excludes_init_by_default(self, tmp_path):
        """__init__.py files are excluded when include_init_files is False."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "real_module.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path)

        names = [p.name for p in result]
        assert "__init__.py" not in names
        assert "real_module.py" in names

    @pytest.mark.unit()
    def Test_includes_init_when_requested(self, tmp_path):
        """__init__.py files appear when include_init_files=True."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "module.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path, include_init_files=True)

        names = [p.name for p in result]
        assert "__init__.py" in names

    @pytest.mark.unit()
    def Test_excludes_pycache_directories(self, tmp_path):
        """Files inside __pycache__ are excluded."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "real.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path)

        assert all("__pycache__" not in str(p) for p in result)

    @pytest.mark.unit()
    def Test_excludes_glob_patterns(self, tmp_path):
        """Files matching glob-style exclude patterns are excluded."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        egg_dir = tmp_path / "mypackage.egg-info"
        egg_dir.mkdir()
        (egg_dir / "PKG-INFO.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "module.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path)

        assert all(".egg-info" not in str(p) for p in result)

    @pytest.mark.unit()
    def Test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Return an empty list when root_directory does not exist."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        result = discover_python_files(root_directory = tmp_path / "nonexistent")

        assert result == []

    @pytest.mark.unit()
    def Test_custom_exclude_patterns(self, tmp_path):
        """Custom exclude patterns are applied instead of defaults."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        secret = tmp_path / "secret_dir"
        secret.mkdir()
        (secret / "hidden.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "visible.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = tmp_path, exclude_patterns=("secret_dir",))

        names = [p.name for p in result]
        assert "hidden.py" not in names
        assert "visible.py" in names

    @pytest.mark.unit()
    def Test_accepts_string_root_directory(self, tmp_path):
        """A str root_directory is coerced to a Path object without error."""
        from src.utils.docs_utils.api_reference_generation import discover_python_files

        (tmp_path / "mod.py").write_text("x = 1", encoding="utf-8")

        result = discover_python_files(root_directory = str(tmp_path))

        assert len(result) == 1
        assert result[0].name == "mod.py"


# ==============================================================================
# Class_Test_Path_To_Module_Name
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Path_To_Module_Name:
    """Tests for path_to_module_name."""

    @pytest.mark.unit()
    def Test_converts_regular_module(self, tmp_path):
        """Regular .py file maps to dotted module name relative to root."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        root = tmp_path
        file_path = root / "src" / "utils" / "foo.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("x = 1", encoding="utf-8")

        result = path_to_module_name(file_path = file_path, source_root = root)

        assert result == "src.utils.foo"

    @pytest.mark.unit()
    def Test_strips_init_suffix(self, tmp_path):
        """__init__.py maps to the parent package name (no __init__ suffix)."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        root = tmp_path
        file_path = root / "src" / "utils" / "__init__.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("", encoding="utf-8")

        result = path_to_module_name(file_path = file_path, source_root = root)

        assert result == "src.utils"

    @pytest.mark.unit()
    def Test_raises_when_file_not_under_root(self, tmp_path):
        """ValueError is raised when file_path is not under source_root."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        other_root = tmp_path / "other"
        other_root.mkdir()
        file_path = tmp_path / "module.py"
        file_path.write_text("x = 1", encoding="utf-8")

        with pytest.raises(ValueError, match="not under source_root"):
            path_to_module_name(file_path = file_path, source_root = other_root)

    @pytest.mark.unit()
    def Test_raises_for_non_py_file(self, tmp_path):
        """ValueError is raised for files that do not have a .py extension."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        root = tmp_path
        txt_file = root / "notes.txt"
        txt_file.write_text("text", encoding="utf-8")

        with pytest.raises(ValueError, match="not a Python"):
            path_to_module_name(file_path = txt_file, source_root = root)

    @pytest.mark.unit()
    def Test_raises_for_bare_init_directly_under_root(self, tmp_path):
        """ValueError is raised when __init__.py directly under source_root."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        init_file = tmp_path / "__init__.py"
        init_file.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="empty module name"):
            path_to_module_name(file_path = init_file, source_root = tmp_path)

    @pytest.mark.unit()
    def Test_accepts_string_paths(self, tmp_path):
        """Strings are accepted in place of Path objects."""
        from src.utils.docs_utils.api_reference_generation import path_to_module_name

        file_path = tmp_path / "mymod.py"
        file_path.write_text("x = 1", encoding="utf-8")

        result = path_to_module_name(file_path = str(file_path), source_root = str(tmp_path))

        assert result == "mymod"


# ==============================================================================
# Class_Test_Module_Name_To_Doc_Path
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Module_Name_To_Doc_Path:
    """Tests for module_name_to_doc_path."""

    @pytest.mark.unit()
    def Test_standard_module(self):
        """Dotted module name becomes api/<path>.md."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = "src.utils.docs_utils.api_reference_generation")

        assert result == "api/src/utils/docs_utils/api_reference_generation.md"

    @pytest.mark.unit()
    def Test_custom_prefix(self):
        """Custom api_prefix replaces the default 'api' prefix."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = "src.utils", api_prefix="reference")

        assert result == "reference/src/utils.md"

    @pytest.mark.unit()
    def Test_raises_for_empty_module_name(self):
        """ValueError is raised when module_name is an empty string."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        with pytest.raises(ValueError, match="must not be empty"):
            module_name_to_doc_path(module_name = "")

    @pytest.mark.unit()
    def Test_raises_for_empty_api_prefix(self):
        """ValueError is raised when api_prefix is empty or whitespace."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        with pytest.raises(ValueError, match="api_prefix must be a non-empty string"):
            module_name_to_doc_path(module_name = "src.utils", api_prefix="   ")

    @pytest.mark.unit()
    def Test_raises_for_api_prefix_with_separator(self):
        """api_prefix must be a single segment without slashes."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        with pytest.raises(ValueError, match="without slashes"):
            module_name_to_doc_path(module_name = "src.utils", api_prefix="bad/prefix")

    @pytest.mark.unit()
    def Test_single_segment_module(self):
        """A module name without dots maps to api/<name>.md."""
        from src.utils.docs_utils.api_reference_generation import module_name_to_doc_path

        result = module_name_to_doc_path(module_name = "conftest")

        assert result == "api/conftest.md"


# ==============================================================================
# Class_Test_Build_Path_To_Module_Mapping
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Build_Path_To_Module_Mapping:
    """Tests for build_path_to_module_mapping."""

    @pytest.mark.unit()
    def Test_maps_files_to_module_names(self, tmp_path):
        """Returns a dict mapping each file path to its module name."""
        from src.utils.docs_utils.api_reference_generation import build_path_to_module_mapping

        root = tmp_path
        file_a = root / "pkg" / "a.py"
        file_a.parent.mkdir()
        file_a.write_text("x = 1", encoding="utf-8")

        mapping = build_path_to_module_mapping(python_files = [file_a], source_root = root)

        assert mapping[file_a] == "pkg.a"

    @pytest.mark.unit()
    def Test_silently_skips_unmappable_files(self, tmp_path):
        """Files outside source_root are silently excluded from the result."""
        from src.utils.docs_utils.api_reference_generation import build_path_to_module_mapping

        root = tmp_path / "project"
        root.mkdir()
        valid_file = root / "module.py"
        valid_file.write_text("x = 1", encoding="utf-8")
        # This file is not under root
        external = tmp_path / "external.py"
        external.write_text("x = 1", encoding="utf-8")

        mapping = build_path_to_module_mapping(python_files = [valid_file, external], source_root = root)

        assert valid_file in mapping
        assert external not in mapping

    @pytest.mark.unit()
    def Test_returns_sorted_result(self, tmp_path):
        """The returned dictionary keys are in sorted order."""
        from src.utils.docs_utils.api_reference_generation import build_path_to_module_mapping

        root = tmp_path
        files = []
        for name in ["z_mod.py", "a_mod.py", "m_mod.py"]:
            f = root / name
            f.write_text("x = 1", encoding="utf-8")
            files.append(f)

        mapping = build_path_to_module_mapping(python_files = files, source_root = root)

        assert list(mapping.keys()) == sorted(mapping.keys())


# ==============================================================================
# Class_Test_Build_Module_To_Doc_Mapping
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Build_Module_To_Doc_Mapping:
    """Tests for build_module_to_doc_mapping."""

    @pytest.mark.unit()
    def Test_maps_module_names_to_doc_paths(self):
        """Each module name maps to the expected doc path."""
        from src.utils.docs_utils.api_reference_generation import build_module_to_doc_mapping

        mapping = build_module_to_doc_mapping(module_names = ["src.utils.foo", "src.utils.bar"])

        assert mapping["src.utils.foo"] == "api/src/utils/foo.md"
        assert mapping["src.utils.bar"] == "api/src/utils/bar.md"

    @pytest.mark.unit()
    def Test_returns_empty_dict_for_empty_input(self):
        """Returns an empty dict when module_names is empty."""
        from src.utils.docs_utils.api_reference_generation import build_module_to_doc_mapping

        result = build_module_to_doc_mapping(module_names = [])

        assert result == {}

    @pytest.mark.unit()
    def Test_skips_empty_string_entries(self):
        """Empty strings in module_names are silently excluded."""
        from src.utils.docs_utils.api_reference_generation import build_module_to_doc_mapping

        mapping = build_module_to_doc_mapping(module_names = ["", "src.utils.foo", ""])

        assert "" not in mapping
        assert "src.utils.foo" in mapping

    @pytest.mark.unit()
    def Test_custom_api_prefix(self):
        """Custom api_prefix is propagated to all doc paths."""
        from src.utils.docs_utils.api_reference_generation import build_module_to_doc_mapping

        mapping = build_module_to_doc_mapping(module_names = ["src.utils.foo"], api_prefix="ref")

        assert mapping["src.utils.foo"] == "ref/src/utils/foo.md"

    @pytest.mark.unit()
    def Test_raises_for_invalid_api_prefix(self):
        """Invalid api_prefix values are rejected consistently."""
        from src.utils.docs_utils.api_reference_generation import build_module_to_doc_mapping

        with pytest.raises(ValueError, match="without slashes"):
            build_module_to_doc_mapping(module_names = ["src.utils.foo"], api_prefix="bad/prefix")


# ==============================================================================
# Class_Test_Build_Navigation_Tree
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Build_Navigation_Tree:
    """Tests for build_navigation_tree."""

    @pytest.mark.unit()
    def Test_empty_input_returns_empty_tree(self):
        """An empty doc_paths list yields an empty dict."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        result = build_navigation_tree(doc_paths = [])

        assert result == {}

    @pytest.mark.unit()
    def Test_single_leaf_path(self):
        """A single path creates the correct nested dict."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        tree = build_navigation_tree(doc_paths = ["api/src/utils/foo.md"])

        assert tree["src"]["utils"]["foo"] == "src/utils/foo.md"

    @pytest.mark.unit()
    def Test_strips_api_prefix(self):
        """The api/ prefix is stripped from leaf values in SUMMARY.md paths."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        tree = build_navigation_tree(doc_paths = ["api/src/bar.md"])

        assert tree["src"]["bar"] == "src/bar.md"

    @pytest.mark.unit()
    def Test_path_without_prefix_kept_as_is(self):
        """Paths not starting with the prefix are kept with their original structure."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        tree = build_navigation_tree(doc_paths = ["other/src/foo.md"], api_prefix="api")

        # 'other' prefix is not stripped; becomes top-level key
        assert "other" in tree

    @pytest.mark.unit()
    def Test_raises_for_invalid_prefix(self):
        """Invalid api_prefix values are rejected before tree generation."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        with pytest.raises(ValueError, match="without slashes"):
            build_navigation_tree(doc_paths = ["api/src/foo.md"], api_prefix="bad/prefix")

    @pytest.mark.unit()
    def Test_normalises_backslashes(self):
        """Windows-style backslashes in paths are normalised to forward slashes."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        tree = build_navigation_tree(doc_paths = ["api\\src\\utils\\foo.md"])

        assert "src" in tree
        assert tree["src"]["utils"]["foo"] == "src/utils/foo.md"

    @pytest.mark.unit()
    def Test_promotes_leaf_to_dir_on_conflict(self):
        """When a name is used as both a leaf and a directory, the leaf is promoted."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        # "utils" first appears as a leaf (api/src/utils.md), then as a directory
        tree = build_navigation_tree(doc_paths = [
            "api/src/utils.md",
            "api/src/utils/sub.md",
        ])

        # "utils" in src should now be a dict (promoted to directory)
        assert isinstance(tree["src"]["utils"], dict)
        # The original leaf is stored under "__leaf__"
        assert tree["src"]["utils"]["__leaf__"] == "src/utils.md"
        assert tree["src"]["utils"]["sub"] == "src/utils/sub.md"

    @pytest.mark.unit()
    def Test_multiple_paths_build_shared_dirs(self):
        """Multiple paths sharing directories create a shared intermediate node."""
        from src.utils.docs_utils.api_reference_generation import build_navigation_tree

        tree = build_navigation_tree(doc_paths = [
            "api/src/utils/a.md",
            "api/src/utils/b.md",
        ])

        assert "a" in tree["src"]["utils"]
        assert "b" in tree["src"]["utils"]


# ==============================================================================
# Class_Test_Build_Api_Reference_File_Mapping
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Build_Api_Reference_File_Mapping:
    """Tests for build_api_reference_file_mapping."""

    @pytest.mark.unit()
    def Test_Builds_Generated_Pages_For_Src_And_Tests(self, tmp_path):
        """Builds module pages plus index and summary for both source roots."""
        from src.utils.docs_utils.api_reference_generation import build_api_reference_file_mapping

        src_module_path = tmp_path / "src" / "pkg" / "module_alpha.py"
        src_module_path.parent.mkdir(parents=True)
        src_module_path.write_text('"""Module alpha."""\n', encoding="utf-8")

        test_module_path = tmp_path / "tests" / "test_beta.py"
        test_module_path.parent.mkdir(parents=True)
        test_module_path.write_text('"""Test beta."""\n', encoding="utf-8")

        mapping = build_api_reference_file_mapping(
            workspace_root=tmp_path,
            index_page_content="# API Reference\n",
        )

        assert "api/index.md" in mapping
        assert "api/SUMMARY.md" in mapping
        assert "api/src/pkg/module_alpha.md" in mapping
        assert "api/tests/test_beta.md" in mapping
        assert mapping["api/src/pkg/module_alpha.md"] == (
            "# module_alpha\n\n::: src.pkg.module_alpha\n"
        )
        assert mapping["api/tests/test_beta.md"] == "# test_beta\n\n::: tests.test_beta\n"
        assert mapping["api/SUMMARY.md"].startswith("* [Overview](index.md)\n")
        assert "* [module_alpha](src/pkg/module_alpha.md)" in mapping["api/SUMMARY.md"]
        assert "* [test_beta](tests/test_beta.md)" in mapping["api/SUMMARY.md"]

    @pytest.mark.unit()
    def Test_Accepts_String_Workspace_And_Empty_Roots(self, tmp_path):
        """String workspace_root inputs return the base generated pages."""
        from src.utils.docs_utils.api_reference_generation import build_api_reference_file_mapping

        mapping = build_api_reference_file_mapping(
            workspace_root=str(tmp_path),
            index_page_content="# API Reference\n",
        )

        assert mapping == {
            "api/SUMMARY.md": "* [Overview](index.md)\n",
            "api/index.md": "# API Reference\n",
        }

    @pytest.mark.unit()
    def Test_Raises_For_Invalid_Prefix(self, tmp_path):
        """Invalid api_prefix values are rejected for full mapping builds."""
        from src.utils.docs_utils.api_reference_generation import build_api_reference_file_mapping

        with pytest.raises(ValueError, match="without slashes"):
            build_api_reference_file_mapping(
                workspace_root=tmp_path,
                index_page_content="# API Reference\n",
                api_prefix="bad/prefix",
            )


# ==============================================================================
# Class_Test_Generate_Summary_Md
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Generate_Summary_Md:
    """Tests for generate_summary_md."""

    @pytest.mark.unit()
    def Test_empty_tree_returns_empty_string(self):
        """An empty nav_tree produces an empty string."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        result = generate_summary_md(nav_tree = {})

        assert result == ""

    @pytest.mark.unit()
    def Test_leaf_node_produces_link(self):
        """A leaf (str value) produces a Markdown link."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"foo": "src/utils/foo.md"}
        result = generate_summary_md(nav_tree = tree)

        assert "* [foo](src/utils/foo.md)" in result

    @pytest.mark.unit()
    def Test_dir_node_produces_section_header(self):
        """A directory node (dict value) produces a plain section header."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"utils": {"foo": "src/utils/foo.md"}}
        result = generate_summary_md(nav_tree = tree)

        assert "* utils" in result
        assert "* [foo](src/utils/foo.md)" in result

    @pytest.mark.unit()
    def Test_skips_dunder_keys(self):
        """Keys beginning with __ (internal markers) are excluded from output."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"__leaf__": "src/utils.md", "real": "src/real.md"}
        result = generate_summary_md(nav_tree = tree)

        assert "__leaf__" not in result
        assert "* [real](src/real.md)" in result

    @pytest.mark.unit()
    def Test_nested_structure_increases_indent(self):
        """Each level of nesting adds additional indentation."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"src": {"utils": {"foo": "src/utils/foo.md"}}}
        result = generate_summary_md(nav_tree = tree, indent_size=4)

        lines = result.split("\n")
        # Top-level has no indent
        top = next(
            line_text
            for line_text in lines
            if "src" in line_text and line_text.strip().startswith("*")
        )
        assert top.startswith("* ")
        # Leaf should be indented two levels
        leaf = next(line_text for line_text in lines if "foo" in line_text)
        assert leaf.startswith(" " * 8)

    @pytest.mark.unit()
    def Test_boolean_indent_size_uses_default_spacing(self):
        """Boolean indent_size values should use the established four-space default."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"src": {"utils": {"foo": "src/utils/foo.md"}}}
        result_bool_indent = generate_summary_md(nav_tree = tree, indent_size=True)
        result_default_indent = generate_summary_md(nav_tree = tree, indent_size=4)

        assert result_bool_indent == result_default_indent

    @pytest.mark.unit()
    def Test_output_is_sorted_by_key(self):
        """Entries within each level are sorted alphabetically."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        tree = {"z": "z.md", "a": "a.md", "m": "m.md"}
        result = generate_summary_md(nav_tree = tree)

        positions = {k: result.index(k) for k in ["a", "m", "z"]}
        assert positions["a"] < positions["m"] < positions["z"]

    @pytest.mark.unit()
    def Test_dir_with_only_dunder_children_produces_no_child_text(self):
        """Directory nodes whose children are all dunder keys emit no sub-list."""
        from src.utils.docs_utils.api_reference_generation import generate_summary_md

        # A directory node with only dunder-prefixed children (all skipped).
        # The 'if child_text:' branch should evaluate to False.
        tree = {"section": {"__leaf__": "section.md"}}
        result = generate_summary_md(nav_tree = tree)

        # The section header appears but no child link is appended.
        assert "* section" in result
        assert "* [__leaf__]" not in result


# ==============================================================================
# Class_Test_Generate_Api_Page_Content
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Generate_Api_Page_Content:
    """Tests for generate_api_page_content."""

    @pytest.mark.unit()
    def Test_contains_mkdocstrings_directive(self):
        """Output contains the ::: autodoc directive for the module."""
        from src.utils.docs_utils.api_reference_generation import generate_api_page_content

        content = generate_api_page_content(module_name = "src.utils.foo")

        assert "::: src.utils.foo" in content

    @pytest.mark.unit()
    def Test_heading_uses_last_segment(self):
        """The H1 heading uses only the final segment of the module name."""
        from src.utils.docs_utils.api_reference_generation import generate_api_page_content

        content = generate_api_page_content(module_name = "src.utils.docs_utils.api_reference_generation")

        assert content.startswith("# api_reference_generation")

    @pytest.mark.unit()
    def Test_single_segment_module_name(self):
        """A module with no dots uses its full name as both heading and directive."""
        from src.utils.docs_utils.api_reference_generation import generate_api_page_content

        content = generate_api_page_content(module_name = "conftest")

        assert "# conftest" in content
        assert "::: conftest" in content


# ==============================================================================
# Class_Test_Check_Module_Docstring
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Check_Module_Docstring:
    """Tests for check_module_docstring."""

    @pytest.mark.unit()
    def Test_returns_true_when_docstring_present(self, tmp_path):
        """Returns True when the module has a non-empty module-level docstring."""
        from src.utils.docs_utils.api_reference_generation import check_module_docstring

        py_file = tmp_path / "with_doc.py"
        py_file.write_text('"""This is a module docstring."""\nx = 1\n', encoding="utf-8")

        assert check_module_docstring(file_path = py_file) is True

    @pytest.mark.unit()
    def Test_returns_false_when_no_docstring(self, tmp_path):
        """Returns False when the module has no docstring."""
        from src.utils.docs_utils.api_reference_generation import check_module_docstring

        py_file = tmp_path / "no_doc.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        assert check_module_docstring(file_path = py_file) is False

    @pytest.mark.unit()
    def Test_returns_false_for_syntax_error(self, tmp_path):
        """Returns False when the file has a SyntaxError."""
        from src.utils.docs_utils.api_reference_generation import check_module_docstring

        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(:\n", encoding="utf-8")

        assert check_module_docstring(file_path = bad_file) is False

    @pytest.mark.unit()
    def Test_returns_false_for_nonexistent_file(self, tmp_path):
        """Returns False when the file does not exist (OSError)."""
        from src.utils.docs_utils.api_reference_generation import check_module_docstring

        assert check_module_docstring(file_path = tmp_path / "ghost.py") is False

    @pytest.mark.unit()
    def Test_accepts_string_path(self, tmp_path):
        """String path is accepted in place of a Path object."""
        from src.utils.docs_utils.api_reference_generation import check_module_docstring

        py_file = tmp_path / "mod.py"
        py_file.write_text('"""Docstring."""\n', encoding="utf-8")

        assert check_module_docstring(file_path = str(py_file)) is True


# ==============================================================================
# Class_Test_Check_Object_Docstrings
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Check_Object_Docstrings:
    """Tests for check_object_docstrings."""

    @pytest.mark.unit()
    def Test_returns_empty_for_fully_documented_file(self, tmp_path):
        """No missing entries when every object has a docstring."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "full.py"
        py_file.write_text(
            '"""Module."""\n\n\ndef my_func():\n    """Function."""\n    pass\n',
            encoding="utf-8",
        )

        result = check_object_docstrings(file_path = py_file)

        assert result == []

    @pytest.mark.unit()
    def Test_reports_missing_module_docstring(self, tmp_path):
        """Returns an entry with object_type='module' when module docstring is absent."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "no_module_doc.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        result = check_object_docstrings(file_path = py_file)

        types = [entry["object_type"] for entry in result]
        assert "module" in types

    @pytest.mark.unit()
    def Test_reports_missing_function_docstring(self, tmp_path):
        """Returns an entry with object_type='function' for undocumented functions."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "no_func_doc.py"
        py_file.write_text(
            '"""Module."""\n\n\ndef undoc():\n    pass\n',
            encoding="utf-8",
        )

        result = check_object_docstrings(file_path = py_file)

        names = [entry["name"] for entry in result]
        assert "undoc" in names

    @pytest.mark.unit()
    def Test_reports_missing_class_docstring(self, tmp_path):
        """Returns an entry with object_type='class' for undocumented classes."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "no_class_doc.py"
        py_file.write_text(
            '"""Module."""\n\n\nclass Foo:\n    pass\n',
            encoding="utf-8",
        )

        result = check_object_docstrings(file_path = py_file)

        names = [entry["name"] for entry in result]
        assert "Foo" in names

    @pytest.mark.unit()
    def Test_reports_private_helpers(self, tmp_path):
        """Private helper functions (underscore-prefixed) are also reported."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "private.py"
        py_file.write_text(
            '"""Module."""\n\n\ndef _helper():\n    pass\n',
            encoding="utf-8",
        )

        result = check_object_docstrings(file_path = py_file)

        names = [entry["name"] for entry in result]
        assert "_helper" in names

    @pytest.mark.unit()
    def Test_returns_empty_for_parse_error(self, tmp_path):
        """Returns an empty list when the file cannot be parsed."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def bad(:\n    pass\n", encoding="utf-8")

        result = check_object_docstrings(file_path = bad_file)

        assert result == []

    @pytest.mark.unit()
    def Test_result_entries_have_required_keys(self, tmp_path):
        """Each result dict contains file, name, object_type, line, has_docstring."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "partial.py"
        py_file.write_text(
            "def no_doc():\n    pass\n",
            encoding="utf-8",
        )

        result = check_object_docstrings(file_path = py_file)

        assert len(result) >= 1
        for entry in result:
            assert "file" in entry
            assert "name" in entry
            assert "object_type" in entry
            assert "line" in entry
            assert "has_docstring" in entry
            assert entry["has_docstring"] is False

    @pytest.mark.unit()
    def Test_accepts_string_path(self, tmp_path):
        """String path is accepted in place of a Path object."""
        from src.utils.docs_utils.api_reference_generation import check_object_docstrings

        py_file = tmp_path / "mod.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        result = check_object_docstrings(file_path = str(py_file))

        assert isinstance(result, list)


# ==============================================================================
# Class_Test_Inventory_Missing_Docstrings
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Inventory_Missing_Docstrings:
    """Tests for inventory_missing_docstrings."""

    @pytest.mark.unit()
    def Test_returns_empty_for_empty_directory(self, tmp_path):
        """Returns an empty list when the root directory has no Python files."""
        from src.utils.docs_utils.api_reference_generation import inventory_missing_docstrings

        result = inventory_missing_docstrings(root_directory = tmp_path)

        assert result == []

    @pytest.mark.unit()
    def Test_includes_init_files(self, tmp_path):
        """__init__.py files are scanned when include_init_files=True (default)."""
        from src.utils.docs_utils.api_reference_generation import inventory_missing_docstrings

        init_file = tmp_path / "__init__.py"
        init_file.write_text("# no docstring\n", encoding="utf-8")

        result = inventory_missing_docstrings(root_directory = tmp_path)

        files_in_result = {entry["file"] for entry in result}
        assert any("__init__.py" in f for f in files_in_result)

    @pytest.mark.unit()
    def Test_results_sorted_by_file_then_line(self, tmp_path):
        """Output is sorted by (file, line) ascending."""
        from src.utils.docs_utils.api_reference_generation import inventory_missing_docstrings

        (tmp_path / "z_mod.py").write_text(
            "def z_func():\n    pass\n",
            encoding="utf-8",
        )
        (tmp_path / "a_mod.py").write_text(
            "def a_func():\n    pass\ndef b_func():\n    pass\n",
            encoding="utf-8",
        )

        result = inventory_missing_docstrings(root_directory = tmp_path)

        pairs = [(e["file"], e["line"]) for e in result]
        assert pairs == sorted(pairs)

    @pytest.mark.unit()
    def Test_custom_exclude_patterns_respected(self, tmp_path):
        """Custom exclude patterns prevent those directories from being scanned."""
        from src.utils.docs_utils.api_reference_generation import inventory_missing_docstrings

        excluded_dir = tmp_path / "skip_me"
        excluded_dir.mkdir()
        (excluded_dir / "hidden.py").write_text("def f(): pass\n", encoding="utf-8")
        (tmp_path / "visible.py").write_text(
            '"""Module."""\n',
            encoding="utf-8",
        )

        result = inventory_missing_docstrings(root_directory = tmp_path, exclude_patterns=("skip_me",))

        files_in_result = {entry["file"] for entry in result}
        assert not any("hidden.py" in f for f in files_in_result)


# ==============================================================================
# Class_Test_Check_Docstring_Sections
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Check_Docstring_Sections:
    """Tests for check_docstring_sections."""

    def Test_no_params_no_return_required_no_issues(self):
        """Docstring with no required sections passes clean."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(
            docstring = "Just a summary.",
            has_params=False,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is False
        assert result["missing_returns"] is False

    def Test_params_required_and_present(self):
        """Parameters section present: no flag raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = "Summary.\n\nParameters\n----------\n    x : int\n        Value.\n"
        result = check_docstring_sections(
            docstring = docstring,
            has_params=True,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is False

    def Test_params_required_but_missing(self):
        """Parameters section absent when required: flag raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(
            docstring = "Summary only.",
            has_params=True,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is True

    def Test_returns_required_and_present(self):
        """Returns section present: no flag raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = "Summary.\n\nReturns\n-------\n    int\n"
        result = check_docstring_sections(
            docstring = docstring,
            has_params=False,
            has_return_annotation=True,
        )

        assert result["missing_returns"] is False

    def Test_returns_required_but_missing(self):
        """Returns section absent when required: flag raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(
            docstring = "Summary only.",
            has_params=False,
            has_return_annotation=True,
        )

        assert result["missing_returns"] is True

    def Test_both_sections_required_and_present(self):
        """Both sections present: no flags raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = (
            "Summary.\n\n"
            "Parameters\n----------\n    x : int\n\n"
            "Returns\n-------\n    int\n"
        )
        result = check_docstring_sections(
            docstring = docstring,
            has_params=True,
            has_return_annotation=True,
        )

        assert result["missing_parameters"] is False
        assert result["missing_returns"] is False

    def Test_both_sections_required_both_missing(self):
        """Both sections absent when required: both flags raised."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        result = check_docstring_sections(
            docstring = "Summary only.",
            has_params=True,
            has_return_annotation=True,
        )

        assert result["missing_parameters"] is True
        assert result["missing_returns"] is True

    def Test_section_heading_case_insensitive(self):
        """Section heading matching is case-insensitive."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = "Summary.\n\nparameters\n----------\n    x : int\n"
        result = check_docstring_sections(
            docstring = docstring,
            has_params=True,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is False

    def Test_dash_line_too_short_not_recognised(self):
        """A dash line of fewer than 3 characters is not a section heading."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = "Summary.\n\nParameters\n--\n    x : int\n"
        result = check_docstring_sections(
            docstring = docstring,
            has_params=True,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is True

    def Test_not_required_but_present_still_passes(self):
        """Extra sections do not cause any issue."""
        from src.utils.docs_utils.api_reference_generation import check_docstring_sections

        docstring = "Summary.\n\nParameters\n----------\n    x : int\n"
        result = check_docstring_sections(
            docstring = docstring,
            has_params=False,
            has_return_annotation=False,
        )

        assert result["missing_parameters"] is False
        assert result["missing_returns"] is False


# ==============================================================================
# Class_Test_Inventory_Strict_Docstrings
# ==============================================================================


@pytest.mark.unit()
class Class_Test_Inventory_Strict_Docstrings:
    """Tests for inventory_strict_docstrings."""

    def Test_empty_directory_returns_empty_list(self, tmp_path):
        """No Python files yields an empty report."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert result == []

    def Test_fully_documented_file_returns_empty(self, tmp_path):
        """A fully documented module with sections returns no issues."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module docstring."""\n\n'
            "from __future__ import annotations\n\n\n"
            "def my_func(x: int) -> int:\n"
            '    """Do something.\n\n'
            "    Parameters\n"
            "    ----------\n"
            "    x : int\n"
            "        Input value.\n\n"
            "    Returns\n"
            "    -------\n"
            "    int\n"
            "        Result.\n"
            '    """\n'
            "    return x + 1\n"
        )
        (tmp_path / "good.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert result == []

    def Test_reports_missing_module_docstring(self, tmp_path):
        """Module without a docstring is flagged with issue=missing_docstring."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        (tmp_path / "nomod.py").write_text("x = 1\n", encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(
            e["issue"] == "missing_docstring" and e["kind"] == "module"
            for e in result
        )

    def Test_reports_missing_function_docstring(self, tmp_path):
        """A function with no docstring is reported."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = '"""Module."""\n\ndef no_doc():\n    pass\n'
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(e["issue"] == "missing_docstring" and e["name"] == "no_doc" for e in result)

    def Test_reports_missing_parameters_section(self, tmp_path):
        """Function with args and docstring but no Parameters section is flagged."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def my_func(x: int) -> None:\n"
            '    """Summary only."""\n'
            "    pass\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(
            e["issue"] == "missing_parameters_section" and e["name"] == "my_func"
            for e in result
        )

    def Test_reports_missing_returns_section(self, tmp_path):
        """Function with return annotation and docstring but no Returns section is flagged."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def compute() -> int:\n"
            '    """Summary only."""\n'
            "    return 42\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(
            e["issue"] == "missing_returns_section" and e["name"] == "compute"
            for e in result
        )

    def Test_no_returns_section_required_for_none_annotation(self, tmp_path):
        """Functions annotated -> None do not require a Returns section."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def side_effect() -> None:\n"
            '    """Do a side effect."""\n'
            "    pass\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert not any(e["issue"] == "missing_returns_section" for e in result)

    def Test_no_params_section_required_for_self_only(self, tmp_path):
        """Methods with only self do not require a Parameters section."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "class Foo:\n"
            '    """A class."""\n\n'
            "    def method(self):\n"
            '        """Does something."""\n'
            "        pass\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert not any(e["issue"] == "missing_parameters_section" for e in result)

    def Test_async_function_missing_sections_flagged(self, tmp_path):
        """Async functions are also inspected for section completeness."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "async def fetch(url: str) -> str:\n"
            '    """Fetch data."""\n'
            "    return url\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        issues = {e["issue"] for e in result if e["name"] == "fetch"}
        assert "missing_parameters_section" in issues
        assert "missing_returns_section" in issues

    def Test_result_entries_have_all_keys(self, tmp_path):
        """Every result entry exposes file, line, kind, name, and issue."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = '"""Module."""\n\ndef f():\n    pass\n'
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        for entry in result:
            assert {"file", "line", "kind", "name", "issue"} <= entry.keys()

    def Test_exclude_patterns_honoured(self, tmp_path):
        """Excluded directories are not scanned."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        skip = tmp_path / "temp"
        skip.mkdir()
        (skip / "hidden.py").write_text("def f(): pass\n", encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path, exclude_patterns=("temp",))

        assert all("hidden.py" not in e["file"] for e in result)

    def Test_results_sorted_by_file_then_line(self, tmp_path):
        """Output is sorted by (file, line) ascending."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def b_func() -> int:\n"
            '    """B."""\n'
            "    return 1\n\n\n"
            "def a_func() -> int:\n"
            '    """A."""\n'
            "    return 2\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        lines = [e["line"] for e in result]
        assert lines == sorted(lines)

    def Test_vararg_and_kwarg_count_as_params(self, tmp_path):
        """*args and **kwargs trigger the Parameters section requirement."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def flexible(*args, **kwargs):\n"
            '    """Summary only."""\n'
            "    pass\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(
            e["issue"] == "missing_parameters_section" and e["name"] == "flexible"
            for e in result
        )

    def Test_kwonly_args_count_as_params(self, tmp_path):
        """Keyword-only arguments also trigger the Parameters section requirement."""
        from src.utils.docs_utils.api_reference_generation import inventory_strict_docstrings

        source = (
            '"""Module."""\n\n\n'
            "def kwonly(*, verbose: bool = False) -> None:\n"
            '    """Summary only."""\n'
            "    pass\n"
        )
        (tmp_path / "mod.py").write_text(source, encoding="utf-8")

        result = inventory_strict_docstrings(root_directory = tmp_path)

        assert any(
            e["issue"] == "missing_parameters_section" and e["name"] == "kwonly"
            for e in result
        )

    def Test_Syntax_Error_During_Strict_Pass_Is_Skipped(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Syntax errors in the strict AST pass should be skipped without raising."""
        from src.utils.docs_utils import api_reference_generation

        source_file = tmp_path / "mod.py"
        source_file.write_text('"""Module."""\n', encoding="utf-8")

        monkeypatch.setattr(
            api_reference_generation,
            "check_module_docstring",
            lambda file_path: True,
        )
        monkeypatch.setattr(
            api_reference_generation,
            "check_object_docstrings",
            lambda file_path: [],
        )

        def _raise_syntax_error(*_args, **_kwargs):
            raise SyntaxError("bad syntax")

        monkeypatch.setattr(api_reference_generation.ast, "parse", _raise_syntax_error)

        result = api_reference_generation.inventory_strict_docstrings(root_directory = tmp_path)

        assert result == []

    def Test_OSError_During_Strict_Pass_Is_Skipped(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Unreadable files in the strict AST pass should be skipped without raising."""
        from pathlib import Path

        from src.utils.docs_utils import api_reference_generation

        source_file = tmp_path / "mod.py"
        source_file.write_text('"""Module."""\n', encoding="utf-8")

        monkeypatch.setattr(
            api_reference_generation,
            "check_module_docstring",
            lambda file_path: True,
        )
        monkeypatch.setattr(
            api_reference_generation,
            "check_object_docstrings",
            lambda file_path: [],
        )

        def _raise_os_error(self, *args, **kwargs):
            raise OSError("unreadable")

        monkeypatch.setattr(Path, "read_text", _raise_os_error)

        result = api_reference_generation.inventory_strict_docstrings(root_directory = tmp_path)

        assert result == []
