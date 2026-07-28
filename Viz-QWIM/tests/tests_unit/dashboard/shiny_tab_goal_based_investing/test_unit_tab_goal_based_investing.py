"""Unit tests for the goal-based investing dashboard tab."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.dashboard.shiny_tab_goal_based_investing._goal_based_investing_state import (
    GOAL_FINANCIAL_PLAN_STATE_KEY,
    GOAL_MULTISTAGE_PREVIEW_STATE_KEY,
    build_goal_assessment_state,
    build_goal_profile_from_client_data,
    build_multistage_preview_state,
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
from src.models.goal_based_investing import (
    build_client_financial_plan,
    load_predefined_cvar_policies,
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
def Test_Goal_Based_Investing_Reserves_A_State_Key_For_The_Staged_Financial_Plan() -> None:
    """The Dashboard state contract retains the normalized plan for future MSMIP use."""
    assert GOAL_FINANCIAL_PLAN_STATE_KEY == "Goal_Based_Investing_Financial_Plan"
    assert GOAL_MULTISTAGE_PREVIEW_STATE_KEY == "Goal_Based_Investing_Multistage_Preview"


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
def Test_Client_Dashboard_Data_Maps_Only_Unambiguous_Baseline_Inputs() -> None:
    """Assets and retirement horizon drive the baseline; cash-flow fields remain context."""
    profile = build_goal_profile_from_client_data(
        manual_profile={
            "Goal_Name": "Retirement",
            "Target_Amount": 500_000.0,
            "Current_Amount": 1.0,
            "Years_To_Goal": 1,
            "Annual_Contribution": 12_000.0,
            "Annual_Return_Percent": 5.0,
        },
        personal_info={"name": "Ada", "age_current": 45, "age_retirement": 65, "tolerance_risk": "Moderate"},
        assets={"taxable": 100_000.0, "tax_deferred": 200_000.0, "tax_free": 50_000.0},
        goals={"essential": 40_000.0, "important": 10_000.0, "aspirational": 5_000.0},
        income={"social_security": 20_000.0, "pension": 10_000.0, "annuity_existing": 0.0, "other": 0.0},
    )
    assert profile["Current_Amount"] == 350_000.0
    assert profile["Years_To_Goal"] == 20
    assert profile["Annual_Contribution"] == 12_000.0
    assert profile["Annual_Goal_Needs"] == 55_000.0
    assert profile["Annual_Guaranteed_Income"] == 30_000.0
    assert profile["Annual_Retirement_Gap"] == 25_000.0


@pytest.mark.unit()
def Test_Risk_Policy_Returns_Produce_A_Probabilistic_Goal_Assessment() -> None:
    """Policy scenarios, unlike a manual return, expose a success probability."""
    profile = {
        "Goal_Name": "Retirement",
        "Target_Amount": 120_000.0,
        "Current_Amount": 100_000.0,
        "Years_To_Goal": 1,
        "Annual_Contribution": 0.0,
        "Annual_Return_Percent": 5.0,
    }
    result_state = build_goal_assessment_state(
        profile=profile,
        portfolio_monthly_returns=np.array([0.02, -0.01, 0.01, -0.02]),
    )
    assert result_state["Assessment"].success_probability is not None
    assert 0 <= result_state["Assessment"].success_probability <= 1


@pytest.mark.unit()
def Test_Small_Multistage_Preview_Uses_The_Selected_Client_Risk_Policy() -> None:
    """The dashboard preview solves with policy assets and the client-plan cash flows."""
    policy = load_predefined_cvar_policies()["Moderate"]
    plan = build_client_financial_plan(
        risk_profile="Moderate",
        confirmed_plan_assets=300_000.0,
        current_age=60,
        retirement_age=60,
        income_start_age=60,
        annual_contribution=0.0,
        annual_goals={"essential": 20_000.0, "important": 5_000.0, "aspirational": 1_000.0},
        annual_income={"social_security": 10_000.0, "pension": 0.0, "annuity_existing": 0.0, "other": 0.0},
        horizon_periods=3,
    )
    asset_returns = pd.DataFrame(
        {
            asset: np.linspace(-0.02 + index * 0.001, 0.03 + index * 0.001, 12)
            for index, asset in enumerate(policy.weights)
        },
    )

    preview = build_multistage_preview_state(
        financial_plan=plan,
        policy=policy,
        asset_returns=asset_returns,
    )

    assert preview["Scenario_Nodes"] == 15
    assert preview["Expected_Terminal_Wealth"] > 0
    assert sum(preview["Root_Weights"].values()) == pytest.approx(1.0)
    assert set(preview["Expected_Priority_Shortfall"]) == {"essential", "important", "aspirational"}


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("amount", "expected"),
    [(0.0, "$0"), (1_234_567.8, "$1,234,568")],
)
def Test_Format_Currency_Uses_Dashboard_Rounding(*, amount: float, expected: str) -> None:
    """Dashboard currency values are rounded to whole dollars for readability."""
    assert format_currency(amount=amount) == expected
