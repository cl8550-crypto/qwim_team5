"""Regression tests for _exception_core pickle reconstruction."""

from __future__ import annotations

import pickle

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Custom,
)


class Class_Test_Regression_Exception_Core:
    """Regression baselines for Exception_Custom pickle round-trips."""

    @pytest.mark.regression()
    def Test_exception_custom_pickle_detail_baseline(self) -> None:
        """Round-tripped Exception_Custom should retain the base detail contract."""
        original = Exception_Custom("pickle me", context={"k": "v"})

        restored = pickle.loads(pickle.dumps(original))

        assert restored.detail == {}

    @pytest.mark.regression()
    def Test_exception_custom_pickle_user_context_baseline(self) -> None:
        """Round-tripped Exception_Custom should retain its user context payload."""
        original = Exception_Custom("pickle me", context={"k": "v"})

        restored = pickle.loads(pickle.dumps(original))

        assert restored._user_context == {"k": "v"}