"""Setup tab package for the QWIM Dashboard.

This package contains the Shiny module components for the Setup tab,
including advisor info, personal info, assets, income, goals, and
computation-settings subtabs.
"""

from __future__ import annotations

from .subtab_advisor_info import subtab_advisor_info_server, subtab_advisor_info_ui
from .tab_setup import tab_setup_server, tab_setup_ui


__all__ = [
    "subtab_advisor_info_server",
    "subtab_advisor_info_ui",
    "tab_setup_server",
    "tab_setup_ui",
]
