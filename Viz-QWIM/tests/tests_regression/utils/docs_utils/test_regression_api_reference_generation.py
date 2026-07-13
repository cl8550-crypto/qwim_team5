"""Regression baselines for API reference generation utilities."""

from __future__ import annotations

import pytest

from src.utils.docs_utils.api_reference_generation import (
    build_api_reference_file_mapping,
    module_name_to_doc_path,
)


class Class_Test_Regression_Api_Reference_Generation:
    """Regression baselines for API doc path generation behavior."""

    @pytest.mark.regression()
    def Test_Custom_Prefix_Path_Baseline(self) -> None:
        """Custom prefixes preserve the expected stable output path shape."""
        result = module_name_to_doc_path(
            module_name = "src.utils.docs_utils.api_reference_generation",
            api_prefix="reference",
        )

        assert result == "reference/src/utils/docs_utils/api_reference_generation.md"

    @pytest.mark.regression()
    def Test_Invalid_Prefix_Message_Baseline(self) -> None:
        """Invalid-prefix validation message remains stable."""
        with pytest.raises(ValueError) as error_info:
            module_name_to_doc_path(module_name = "src.utils.helper", api_prefix="bad/prefix")

        assert str(error_info.value) == (
            "api_prefix must be a single path segment without slashes"
        )

    @pytest.mark.regression()
    def Test_Mapping_Uses_Prefix_Baseline(self, tmp_path) -> None:
        """Generated index and summary keys remain prefixed consistently."""
        mapping = build_api_reference_file_mapping(
            workspace_root=tmp_path,
            index_page_content="# API Reference\n",
            api_prefix="reference",
        )

        assert mapping == {
            "reference/SUMMARY.md": "* [Overview](index.md)\n",
            "reference/index.md": "# API Reference\n",
        }