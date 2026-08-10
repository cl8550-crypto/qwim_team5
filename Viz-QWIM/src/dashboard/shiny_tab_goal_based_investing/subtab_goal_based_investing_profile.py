"""Goal Profile inputs for the Goal-Based Investing dashboard tab."""

from __future__ import annotations

from typing import Any

import numpy as np

from shiny import module, reactive, render, ui

from src.models.goal_based_investing import (
    build_client_financial_plan,
    load_predefined_cvar_policies,
    normalize_risk_profile,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (
    find_cleaned_data_dir,
    load_monthly_market_panel,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

from ._goal_based_investing_state import (
    build_goal_assessment_state,
    build_goal_profile_from_client_data,
    get_goal_based_investing_state,
)


DEMO_PERSONAL_INFO = {
    "name": "Demo Client",
    "age_current": 60,
    "age_retirement": 65,
    "age_income_starting": 65,
    "tolerance_risk": "Moderate",
}
DEMO_ASSETS = {
    "taxable": 300_000.0,
    "tax_deferred": 350_000.0,
    "tax_free": 100_000.0,
}
DEMO_GOALS = {
    "essential": 55_000.0,
    "important": 10_000.0,
    "aspirational": 5_000.0,
}
DEMO_INCOME = {
    "social_security": 24_000.0,
    "pension": 14_000.0,
    "annuity_existing": 0.0,
    "other": 0.0,
}


def _predefined_cvar_policies() -> tuple[dict, Any]:
    """Load fixed policies and the matching history used for scenario returns."""
    market_panel = load_monthly_market_panel(find_cleaned_data_dir())
    policies = load_predefined_cvar_policies()
    assets = list(next(iter(policies.values())).weights)
    asset_returns = market_panel.loc[:, assets]
    return policies, asset_returns


@module.ui
def subtab_goal_based_investing_profile_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the goal details and planning-assumptions input form."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Goal-Based Assessment Setup"),
        ui.p(
            "A ready-to-run Moderate-risk retirement example is loaded automatically. "
            "Use Clients-tab values or edit the planning assumptions, then select Assess goal.",
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Goal details"),
                ui.card_body(
                    ui.input_text("input_goal_name", "Goal name", value="Retirement"),
                    ui.input_numeric(
                        "input_target_amount",
                        "Target retirement portfolio value ($)",
                        value=1_150_000,
                        min=0.01,
                        step=1_000,
                    ),
                    ui.input_action_button(
                        "input_load_reported_assets",
                        "Use reported primary-client assets",
                        class_="btn-outline-secondary",
                    ),
                    ui.input_action_button(
                        "input_load_demo_client",
                        "Load ready-to-run demo client",
                        class_="btn-outline-secondary ms-2",
                    ),
                    ui.input_numeric(
                        "input_plan_assets_confirmed",
                        "Plan assets confirmed ($)",
                        value=750_000,
                        min=0.01,
                        step=1_000,
                    ),
                ),
            ),
            ui.card(
                ui.card_header("Planning assumptions"),
                ui.card_body(
                    ui.input_numeric(
                        "input_annual_contribution",
                        "Annual contribution ($)",
                        value=20_000,
                        min=0,
                        step=1_000,
                    ),
                    ui.input_action_button(
                        "input_assess_goal",
                        "Assess goal",
                        class_="btn-primary mt-3",
                    ),
                    ui.output_ui("output_profile_status"),
                    ui.output_ui("output_client_data_summary"),
                ),
            ),
            col_widths=(6, 6),
        ),
    )


@module.server
def subtab_goal_based_investing_profile_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Validate primary-client inputs and publish a policy-scenario assessment."""
    del session, data_utils, data_inputs
    state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

    def _client_dashboard_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Retrieve primary-client records, falling back to a runnable demo."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            get_investor_primary_assets,
            get_investor_primary_goals,
            get_investor_primary_income,
            get_investor_primary_personal_info,
        )
        records = (
            get_investor_primary_personal_info(reactives_shiny=reactives_shiny),
            get_investor_primary_assets(reactives_shiny=reactives_shiny),
            get_investor_primary_goals(reactives_shiny=reactives_shiny),
            get_investor_primary_income(reactives_shiny=reactives_shiny),
        )
        personal_info, assets, goals, income = records
        if sum(
            float(value)
            for value in assets.values()
            if value is not None and str(value).strip() != ""
        ) > 0:
            return records
        return DEMO_PERSONAL_INFO, DEMO_ASSETS, DEMO_GOALS, DEMO_INCOME

    def _portfolio_policy_for_client(*, risk_profile: str) -> tuple[Any, np.ndarray]:
        """Select one cached CVaR policy and its historical portfolio returns."""
        policies, asset_returns = _predefined_cvar_policies()
        selected_policy = policies[normalize_risk_profile(risk_profile)]
        portfolio_returns = asset_returns.loc[:, list(selected_policy.weights)].mul(
            np.array([selected_policy.weights[asset] for asset in selected_policy.weights]),
            axis=1,
        ).sum(axis=1)
        return selected_policy, portfolio_returns

    def _build_manual_profile() -> dict[str, Any]:
        """Read the editable Profile controls into the model's input contract."""
        return {
            "Goal_Name": input.input_goal_name(),
            "Target_Amount": input.input_target_amount(),
            "Current_Amount": 0.0,
            "Years_To_Goal": 0,
            "Annual_Contribution": input.input_annual_contribution(),
            "Annual_Return_Percent": 0.0,
        }

    def _run_assessment(*, manual_profile: dict[str, Any]) -> None:
        """Build a client-aware profile and publish all core dashboard state."""
        try:
            personal_info, assets, goals, income = _client_dashboard_data()
            profile = build_goal_profile_from_client_data(
                manual_profile=manual_profile,
                personal_info=personal_info,
                assets=assets,
                goals=goals,
                income=income,
            )
            profile["Reported_Assets"] = profile["Current_Amount"]
            confirmed_assets = float(input.input_plan_assets_confirmed())
            if confirmed_assets <= 0:
                raise ValueError("Enter a positive amount of assets allocated to this plan")
            if confirmed_assets > profile["Reported_Assets"]:
                raise ValueError("Plan assets confirmed cannot exceed reported primary-client assets")
            profile["Current_Amount"] = confirmed_assets
            profile["Confirmed_Plan_Assets"] = confirmed_assets
            policy, portfolio_returns = _portfolio_policy_for_client(
                risk_profile=profile["Risk_Profile"],
            )
            profile["Portfolio_Policy"] = policy
            profile["Portfolio_Monthly_Returns"] = portfolio_returns
            profile["Portfolio_Expected_Shortfall"] = policy.expected_shortfall
            profile["Return_Source"] = "Historical bootstrap of selected versioned CVaR policy"
            financial_plan = build_client_financial_plan(
                risk_profile=profile["Risk_Profile"],
                confirmed_plan_assets=confirmed_assets,
                current_age=int(personal_info["age_current"]),
                retirement_age=int(personal_info["age_retirement"]),
                income_start_age=int(personal_info["age_income_starting"]),
                annual_contribution=float(profile["Annual_Contribution"]),
                annual_goals=goals,
                annual_income=income,
                horizon_periods=max(1, int(profile["Years_To_Goal"]) + 1),
            )
            profile["Financial_Plan"] = financial_plan
            state_values["Profile"].set(profile)
            state_values["Financial_Plan"].set(financial_plan)
            state_values["Multistage_Preview"].set(None)
            state_values["Assessment"].set(
                build_goal_assessment_state(
                    profile=profile,
                    portfolio_monthly_returns=portfolio_returns,
                ),
            )
            state_values["Error"].set(None)
        except (Exception_Validation_Input, FileNotFoundError, TypeError, ValueError) as error:
            state_values["Assessment"].set(None)
            state_values["Financial_Plan"].set(None)
            state_values["Error"].set(str(error))

    @reactive.effect
    @reactive.event(input.input_load_reported_assets)
    def load_reported_assets() -> None:
        """Offer reported assets as a convenient, still user-confirmed plan amount."""
        _, assets, _, _ = _client_dashboard_data()
        ui.update_numeric(
            "input_plan_assets_confirmed",
            value=sum(float(amount) for amount in assets.values()),
        )

    @reactive.effect
    @reactive.event(input.input_load_demo_client)
    def load_demo_client() -> None:
        """Restore the documented demo values for a client-ready first run."""
        ui.update_text("input_goal_name", value="Retirement")
        ui.update_numeric("input_target_amount", value=1_150_000)
        ui.update_numeric("input_plan_assets_confirmed", value=750_000)
        ui.update_numeric("input_annual_contribution", value=25_000)

    @reactive.effect
    @reactive.event(input.input_assess_goal)
    def assess_goal() -> None:
        """Assess the saved profile only when the user selects the action button."""
        _run_assessment(manual_profile=_build_manual_profile())

    @reactive.effect
    def initialize_demo_assessment() -> None:
        """Publish a visible default result as soon as the dashboard opens."""
        if state_values["Assessment"]() is None and state_values["Error"]() is None:
            _run_assessment(
                manual_profile={
                    "Goal_Name": "Retirement",
                    "Target_Amount": 1_150_000.0,
                    "Current_Amount": 0.0,
                    "Years_To_Goal": 0,
                    "Annual_Contribution": 25_000.0,
                    "Annual_Return_Percent": 0.0,
                },
            )

    @output
    @render.ui
    def output_profile_status() -> Any:
        """Render the saved-profile or validation status beneath the action button."""
        validation_error = state_values["Error"]()
        if validation_error is not None:
            return ui.div(validation_error, class_="alert alert-danger mt-3")
        if state_values["Assessment"]() is not None:
            return ui.div("Assessment updated. Open the Assessment tab to view results.", class_="alert alert-success mt-3")
        return None

    @output
    @render.ui
    def output_client_data_summary() -> Any:
        """Show exactly which Clients-tab fields informed the saved profile."""
        profile = state_values["Profile"]()
        if profile is None:
            return None
        return ui.div(
            ui.strong(f"Clients Dashboard: {profile['Client_Name']} · {profile['Risk_Profile']}"),
            ui.br(),
            f"Reported assets: ${profile['Reported_Assets']:,.0f}; confirmed plan assets: ${profile['Confirmed_Plan_Assets']:,.0f}; horizon: {profile['Years_To_Goal']} years.",
            ui.br(),
            f"Annual goal needs: ${profile['Annual_Goal_Needs']:,.0f}; guaranteed income: ${profile['Annual_Guaranteed_Income']:,.0f}; gap: ${profile['Annual_Retirement_Gap']:,.0f}.",
            ui.br(),
            f"Selected CVaR policy: {profile['Portfolio_Policy'].profile}; historical 95% expected shortfall: {profile['Portfolio_Expected_Shortfall']:.2%}.",
            class_="alert alert-info mt-3",
        )


Subtab_Goal_Based_Investing_Profile = subtab_goal_based_investing_profile_ui
