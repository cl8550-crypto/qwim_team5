"""Property-based tests for Typst utility helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.typst_utils import build_typst_compile_command_QWIM


SAFE_NAME_STRATEGY = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=1,
    max_size=20,
)


class Class_Test_Hypothesis_Typst_Utils:
    """Property-based tests for Typst command construction."""

    @pytest.mark.unit()
    @given(
        input_name=SAFE_NAME_STRATEGY,
        output_name=SAFE_NAME_STRATEGY,
    )
    @settings(max_examples=80)
    def Test_Command_Vector_Always_Has_Four_Elements(
        self,
        input_name: str,
        output_name: str,
    ) -> None:
        """Typst command vectors must always have four ordered elements."""
        command_vector = build_typst_compile_command_QWIM(
            typst_executable_path = None,
            typst_file_path = Path(f"{input_name}.typ"),
            output_pdf_path = Path(f"{output_name}.pdf"),
        )

        assert len(command_vector) == 4
        assert command_vector[0] == "typst"
        assert command_vector[1] == "compile"
        assert command_vector[2].endswith(".typ")
        assert command_vector[3].endswith(".pdf")

    @pytest.mark.unit()
    @given(
        executable_name=SAFE_NAME_STRATEGY,
        input_name=SAFE_NAME_STRATEGY,
        output_name=SAFE_NAME_STRATEGY,
    )
    @settings(max_examples=80)
    def Test_Command_Vector_Preserves_Path_Order(
        self,
        executable_name: str,
        input_name: str,
        output_name: str,
    ) -> None:
        """Resolved executable paths must remain in the first command slot."""
        executable_path = Path(f"{executable_name}.exe")
        input_path = Path(f"{input_name}.typ")
        output_path = Path(f"{output_name}.pdf")

        command_vector = build_typst_compile_command_QWIM(
            typst_executable_path = executable_path,
            typst_file_path = input_path,
            output_pdf_path = output_path,
        )

        assert command_vector[0] == str(executable_path)
        assert command_vector[2] == str(input_path)
        assert command_vector[3] == str(output_path)