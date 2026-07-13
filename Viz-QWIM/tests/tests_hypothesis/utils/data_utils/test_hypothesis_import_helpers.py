"""Hypothesis tests for _import_helpers module.

Tests cover invariants for :func:`try_import_module` around successful
imports, normalization, and strict input validation.
"""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


class Class_Test_Hypothesis_Import_Helpers:
    """Property-based tests for try_import_module."""

    @pytest.mark.unit()
    @given(
        module_name=st.sampled_from(["os", "sys", "json", "math"]),
        left_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
        right_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
    )
    @settings(max_examples=40)
    def Test_whitespace_wrapped_valid_modules_import_successfully(
        self,
        module_name: str,
        left_ws: str,
        right_ws: str,
    ) -> None:
        """Whitespace wrappers do not prevent import of valid modules."""
        from src.utils.data_utils._import_helpers import try_import_module

        result = try_import_module(module_name = f"{left_ws}{module_name}{right_ws}")

        assert result is not None
        assert result.__name__ == module_name

    @pytest.mark.unit()
    @given(blank_name=st.sampled_from(["", " ", "\t", "\n", "  \t  "]))
    @settings(max_examples=20)
    def Test_blank_module_names_raise_value_error(self, blank_name: str) -> None:
        """Blank module names always raise ValueError."""
        from src.utils.data_utils._import_helpers import try_import_module

        with pytest.raises(ValueError, match="non-empty string"):
            try_import_module(module_name = blank_name)

    @pytest.mark.unit()
    @given(
        module_name=st.from_regex(r"_qwim_hyp_fake_[a-z0-9_]{1,12}", fullmatch=True),
    )
    @settings(max_examples=30)
    def Test_nonexistent_modules_return_none(self, module_name: str) -> None:
        """Definitely missing module names return None."""
        from src.utils.data_utils._import_helpers import try_import_module

        assert try_import_module(module_name = module_name) is None

    @pytest.mark.unit()
    @given(
        bad_value=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers(), max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=3), st.integers(), max_size=2),
        )
    )
    @settings(max_examples=30)
    def Test_non_string_module_names_raise_type_error(self, bad_value: object) -> None:
        """Non-string module names always raise TypeError."""
        from src.utils.data_utils._import_helpers import try_import_module

        with pytest.raises(TypeError, match="module_name must be a string"):
            try_import_module(module_name = bad_value)  # type: ignore[arg-type]