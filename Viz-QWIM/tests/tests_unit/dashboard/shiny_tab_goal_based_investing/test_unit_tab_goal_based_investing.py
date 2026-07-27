"""Unit tests for the goal-based investing dashboard tab."""

from __future__ import annotations

import pytest

from src.dashboard.shiny_tab_goal_based_investing._goal_based_investing_state import (
    build_goal_assessment_state,
    format_currency,
)
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


@pytest.mark.unit()
def Test_Goal_Assessment_State_Contains_Terminal_Assessment_And_Progress() -> None:
    """A profile produces a terminal assessment and one value for every year."""
    profile = {
        "Goal_Name": "Retirement",
        "Target_Amount": 150_000.0,
        "Current_Amount": 100_000.0,
        "Years_To_Goal": 10,
        "Annual_Contribution": 0.0,
        "Annual_Return_Percent": 5.0,
    }

    result_state = build_goal_assessment_state(profile=profile)

    assert result_state["Assessment"].projected_amount == pytest.approx(162_889.4627)
    assert result_state["Years"] == list(range(11))
    assert result_state["Annual_Progress"][0] == 100_000.0
    assert result_state["Annual_Progress"][-1] == pytest.approx(162_889.4627)


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("amount", "expected"),
    [(0.0, "$0"), (1_234_567.8, "$1,234,568")],
)
def Test_Format_Currency_Uses_Dashboard_Rounding(*, amount: float, expected: str) -> None:
    """Dashboard currency values are rounded to whole dollars for readability."""
    assert format_currency(amount=amount) == expected
