"""Hypothesis tests for _exception_core pickle reconstruction."""

from __future__ import annotations

import pickle

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Custom,
    Exception_Format,
    Exception_Severity,
)


_TEXT_STRATEGY = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=40,
)


class Class_Test_Hypothesis_Exception_Core:
    """Property-based tests for Exception_Custom pickle round-trips."""

    @pytest.mark.unit()
    @given(
        message=_TEXT_STRATEGY,
        user_context=st.dictionaries(
            keys=st.text(min_size=1, max_size=8),
            values=st.one_of(st.none(), st.booleans(), st.integers(), _TEXT_STRATEGY),
            max_size=4,
        ),
    )
    @settings(max_examples=30)
    def Test_pickle_roundtrip_preserves_detail_contract(
        self,
        message: str,
        user_context: dict[str, object],
    ) -> None:
        """Pickle round-trips should preserve message, user context, and empty detail."""
        original = Exception_Custom(
            message,
            context=user_context,
            exception_format=Exception_Format.JSON,
            severity=Exception_Severity.WARNING,
        )

        restored = pickle.loads(pickle.dumps(original))

        assert restored.Message == message
        assert restored.detail == {}
        assert restored._user_context == user_context
        assert restored.Exception_Format_Value == Exception_Format.JSON
        assert restored.Severity == Exception_Severity.WARNING