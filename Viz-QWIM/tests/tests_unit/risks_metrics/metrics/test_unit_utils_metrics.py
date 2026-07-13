"""Unit tests for src.risks_metrics.metrics and src.risks_metrics.metrics.utils_metrics.

These tests ensure that the package and stub module are importable, which
provides line coverage for the otherwise-never-executed module-level code
(``from __future__ import annotations`` and the module docstring).

Author: QWIM Team
"""

from __future__ import annotations

import importlib

import pytest


class Test_Risks_Metrics_Metrics_Package_Importable:
    """Verify that the risks_metrics.metrics package can be imported."""

    @pytest.mark.unit()
    def test_package_import(self) -> None:
        """src.risks_metrics.metrics is importable without errors."""
        mod = importlib.import_module("src.risks_metrics.metrics")
        assert mod is not None

    @pytest.mark.unit()
    def test_package_has_name(self) -> None:
        """Package __name__ is correct."""
        mod = importlib.import_module("src.risks_metrics.metrics")
        assert mod.__name__ == "src.risks_metrics.metrics"


class Test_Utils_Metrics_Module_Importable:
    """Verify that the utils_metrics stub module is importable."""

    @pytest.mark.unit()
    def test_module_import(self) -> None:
        """src.risks_metrics.metrics.utils_metrics is importable without errors."""
        mod = importlib.import_module("src.risks_metrics.metrics.utils_metrics")
        assert mod is not None

    @pytest.mark.unit()
    def test_module_has_name(self) -> None:
        """Module __name__ is correct."""
        mod = importlib.import_module("src.risks_metrics.metrics.utils_metrics")
        assert mod.__name__ == "src.risks_metrics.metrics.utils_metrics"
