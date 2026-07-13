"""Hypothesis tests for platform_utils."""

from __future__ import annotations

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


class Class_Test_Hypothesis_Platform_Utils:
    """Property-based coverage for platform_utils behavior."""

    @pytest.mark.unit()
    @given(
        platform_name=st.sampled_from(["win32", "linux", "linux2", "darwin", "freebsd13"]),
        left_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
        right_ws=st.from_regex(r"\s{0,3}", fullmatch=True),
    )
    @settings(max_examples=40)
    def Test_get_platform_normalizes_wrapped_platform_names(
        self,
        platform_name: str,
        left_ws: str,
        right_ws: str,
    ) -> None:
        """Whitespace wrappers should not change the normalized platform string."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        assert get_platform(_sys_platform=f"{left_ws}{platform_name}{right_ws}") == platform_name

    @pytest.mark.unit()
    @given(
        platform_name=st.sampled_from(["win32", "linux", "linux2", "darwin", "freebsd13"]),
    )
    @settings(max_examples=25)
    def Test_at_most_one_platform_predicate_is_true(self, platform_name: str) -> None:
        """Normalized platform seeds should satisfy the one-platform invariant."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import (
            is_linux,
            is_macos,
            is_windows,
        )

        results = [
            is_windows(_sys_platform=platform_name),
            is_linux(_sys_platform=platform_name),
            is_macos(_sys_platform=platform_name),
        ]
        assert sum(results) <= 1

    @pytest.mark.unit()
    @given(blank_seed=st.sampled_from(["", " ", "\t", "\n", "  \t  "]))
    @settings(max_examples=20)
    def Test_blank_platform_names_raise_value_error(self, blank_seed: str) -> None:
        """Blank platform seeds are always rejected."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        with pytest.raises(ValueError, match="non-empty string"):
            get_platform(_sys_platform=blank_seed)

    @pytest.mark.unit()
    @given(
        bad_value=st.one_of(
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers(), max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=3), st.integers(), max_size=2),
        )
    )
    @settings(max_examples=30)
    def Test_non_string_platform_names_raise_type_error(self, bad_value: object) -> None:
        """Non-string platform seeds are always rejected."""
        from src.utils.custom_exceptions_errors_loggers.platform_utils import get_platform

        with pytest.raises(TypeError, match="string or None"):
            get_platform(_sys_platform=bad_value)  # type: ignore[arg-type]