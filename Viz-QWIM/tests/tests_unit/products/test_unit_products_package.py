"""Unit tests for product package facades.

Tests cover package-level importability for the root ``src.products`` package
and the annuity package facade, plus a small re-export check for the annuity
package symbols that are imported throughout the test suite.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-30)
"""

from __future__ import annotations

import pytest


@pytest.mark.unit()
class Class_Test_Products_Package_Facades:
    """Tests for package-level import and re-export behaviour."""

    @pytest.mark.unit()
    def Test_Products_Package_Importable(self) -> None:
        """The root products package should import successfully."""
        import src.products  # noqa: F401

    @pytest.mark.unit()
    def Test_Annuity_Package_Importable(self) -> None:
        """The annuity package facade should import successfully."""
        import src.products.annuity  # noqa: F401

    @pytest.mark.unit()
    def Test_Annuity_Package_Re_Exports_RILA_Symbols(self) -> None:
        """The annuity package facade should expose the main RILA symbols."""
        from src.products.annuity import (
            Annuity_RILA,
            Crediting_Strategy,
            Protection_Type,
        )

        assert Annuity_RILA.__name__ == "Annuity_RILA"
        assert Crediting_Strategy.CAP.value == "Cap"
        assert Protection_Type.BUFFER.value == "Buffer"