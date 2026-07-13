"""Integration tests for API reference generation utilities."""

from __future__ import annotations

import pytest

from src.utils.docs_utils.api_reference_generation import (
    build_api_reference_file_mapping,
    build_navigation_tree,
    module_name_to_doc_path,
)


class Class_Test_Integration_Api_Reference_Generation:
    """Integration tests for end-to-end API reference generation behavior."""

    @pytest.mark.integration()
    def Test_Custom_Prefix_Is_Applied_End_To_End(self, tmp_path) -> None:
        """A valid custom prefix is applied to generated page and summary paths."""
        source_module_path = tmp_path / "src" / "pkg" / "alpha.py"
        test_module_path = tmp_path / "tests" / "test_beta.py"
        source_module_path.parent.mkdir(parents=True)
        test_module_path.parent.mkdir(parents=True)
        source_module_path.write_text('"""Module alpha."""\n', encoding="utf-8")
        test_module_path.write_text('"""Test beta."""\n', encoding="utf-8")

        mapping = build_api_reference_file_mapping(
            workspace_root=tmp_path,
            index_page_content="# API Reference\n",
            api_prefix="reference",
        )

        assert "reference/index.md" in mapping
        assert "reference/SUMMARY.md" in mapping
        assert "reference/src/pkg/alpha.md" in mapping
        assert "reference/tests/test_beta.md" in mapping

    @pytest.mark.integration()
    def Test_Invalid_Prefix_Raises_Across_Entry_Points(self, tmp_path) -> None:
        """Invalid prefixes are rejected consistently by public path entry points."""
        with pytest.raises(ValueError, match="without slashes"):
            module_name_to_doc_path(module_name = "src.utils.helper", api_prefix="bad/prefix")

        with pytest.raises(ValueError, match="without slashes"):
            build_navigation_tree(doc_paths = ["api/src/utils/helper.md"], api_prefix="bad/prefix")

        with pytest.raises(ValueError, match="without slashes"):
            build_api_reference_file_mapping(
                workspace_root=tmp_path,
                index_page_content="# API Reference\n",
                api_prefix="bad/prefix",
            )