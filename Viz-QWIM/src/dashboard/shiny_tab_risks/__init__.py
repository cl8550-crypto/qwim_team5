"""Risks tab package for the QWIM Dashboard.

This package contains the Shiny module components for the Risks &
Metrics tab, including risk-model selection and results display.
"""

from __future__ import annotations

from .subtab_risks_markets import (
    SubTab_Risks_Markets,  # ty: ignore[unresolved-import]  # pyright: ignore[reportAttributeAccessIssue]  # pyrefly: ignore[missing-module-attribute]
)
from .tab_risks import (
    Tab_Risks,  # ty: ignore[unresolved-import]  # pyright: ignore[reportAttributeAccessIssue]  # pyrefly: ignore[missing-module-attribute]
)


__all__ = ["SubTab_Risks_Markets", "Tab_Risks"]
