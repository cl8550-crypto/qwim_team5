"""Unit tests for the goal-based investing dashboard tab."""

from __future__ import annotations

import pytest

from src.dashboard.shiny_tab_goal_based_investing.subtab_goal_based_investing_assessment import (
    subtab_goal_based_investing_assessment_server,
    subtab_goal_based_investing_assessment_ui,
)
from src.dashboard.shiny_tab_goal_based_investing.subtab_goal_based_investing_profile import (
    subtab_goal_based_investing_profile_server,
    subtab_goal_based_investing_profile_ui,
)
from src.dashboard.shiny_tab_goal_based_investing.tab_goal_based_investing import (
    Tab_Goal_Based_Investing,
    tab_goal_based_investing_server,
    tab_goal_based_investing_ui,
)


@pytest.mark.unit()
def Test_Tab_Goal_Based_Investing_UI_Is_Callable() -> None:
    """The tab UI entry point is publicly available."""
    assert callable(tab_goal_based_investing_ui)


@pytest.mark.unit()
def Test_Tab_Goal_Based_Investing_Server_Is_Callable() -> None:
    """The tab server entry point is publicly available."""
    assert callable(tab_goal_based_investing_server)


@pytest.mark.unit()
@pytest.mark.parametrize(
    "module_function",
    [
        subtab_goal_based_investing_profile_ui,
        subtab_goal_based_investing_profile_server,
        subtab_goal_based_investing_assessment_ui,
        subtab_goal_based_investing_assessment_server,
    ],
)
def Test_Goal_Based_Investing_Subtab_Entry_Points_Are_Callable(*, module_function: object) -> None:
    """Each subtab exposes a callable UI or server entry point."""
    assert callable(module_function)


@pytest.mark.unit()
def Test_Tab_Goal_Based_Investing_Alias_Is_Consistent() -> None:
    """The compatibility alias resolves to the tab UI function."""
    assert Tab_Goal_Based_Investing is tab_goal_based_investing_ui
