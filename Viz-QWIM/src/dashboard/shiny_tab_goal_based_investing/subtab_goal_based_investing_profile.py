"""Goal Profile inputs for the Goal-Based Investing dashboard tab."""

from __future__ import annotations

from typing import Any

import numpy as np

from shiny import module, reactive, render, ui

from src.models.goal_based_investing import (
    Goal_Based_Investing_Baseline,
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
    build_multistage_preview_state,
    get_goal_based_investing_state,
)


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
            "Primary-client retirement assessment. Client data, risk policy, and retirement horizon "
            "are read from the Clients tab.",
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Goal details"),
                ui.card_body(
                    ui.input_text("input_goal_name", "Goal name", value="Retirement"),
                    ui.input_numeric(
                        "input_target_amount",
                        "Target retirement portfolio value ($)",
                        value=1_000_000,
                        min=0.01,
                        step=1_000,
                    ),
                    ui.input_action_button(
                        "input_load_reported_assets",
                        "Use reported primary-client assets",
                        class_="btn-outline-secondary",
                    ),
                    ui.input_numeric(
                        "input_plan_assets_confirmed",
                        "Plan assets confirmed ($)",
                        value=0,
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
        """Retrieve only the primary client's existing Dashboard records."""
        from src.dashboard.shiny_utils.utils_tab_clients import (
            get_investor_primary_assets,
            get_investor_primary_goals,
            get_investor_primary_income,
            get_investor_primary_personal_info,
        )
        return (
            get_investor_primary_personal_info(reactives_shiny=reactives_shiny),
            get_investor_primary_assets(reactives_shiny=reactives_shiny),
            get_investor_primary_goals(reactives_shiny=reactives_shiny),
            get_investor_primary_income(reactives_shiny=reactives_shiny),
        )

    def _portfolio_policy_for_client(*, risk_profile: str) -> tuple[Any, np.ndarray]:
        """Select one cached CVaR policy and its historical portfolio returns."""
        policies, asset_returns = _predefined_cvar_policies()
        selected_policy = policies[normalize_risk_profile(risk_profile)]
        portfolio_returns = asset_returns.loc[:, list(selected_policy.weights)].to_numpy() @ np.array(
            [selected_policy.weights[asset] for asset in selected_policy.weights],
        )
        return selected_policy, portfolio_returns

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
    @reactive.event(input.input_assess_goal)
    def assess_goal() -> None:
        """Assess the saved profile only when the user selects the action button."""
        manual_profile = {
            "Goal_Name": input.input_goal_name(),
            "Target_Amount": input.input_target_amount(),
            "Current_Amount": 0.0,
            "Years_To_Goal": 0,
            "Annual_Contribution": input.input_annual_contribution(),
            "Annual_Return_Percent": 0.0,
        }
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
                raise ValueError("Enter the positive amount of reported assets allocated to this plan")
            if confirmed_assets > profile["Reported_Assets"]:
                raise ValueError("Plan assets confirmed cannot exceed reported primary-client assets")
            profile["Current_Amount"] = confirmed_assets
            profile["Confirmed_Plan_Assets"] = confirmed_assets
            policy, portfolio_returns = _portfolio_policy_for_client(
                risk_profile=profile["Risk_Profile"],
            )
            profile["Portfolio_Policy"] = policy
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
            multistage_preview = build_multistage_preview_state(
                financial_plan=financial_plan,
                policy=policy,
                asset_returns=_predefined_cvar_policies()[1],
            )
            profile["Financial_Plan"] = financial_plan
            Goal_Based_Investing_Baseline(
                goal_name=profile["Goal_Name"],
                target_amount=profile["Target_Amount"],
                current_amount=profile["Current_Amount"],
                years_to_goal=profile["Years_To_Goal"],
                annual_contribution=profile["Annual_Contribution"],
            ).project_amount(annual_return=float(profile["Annual_Return_Percent"]) / 100.0)
            state_values["Profile"].set(profile)
            state_values["Financial_Plan"].set(financial_plan)
            state_values["Multistage_Preview"].set(multistage_preview)
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
            state_values["Multistage_Preview"].set(None)
            state_values["Error"].set(str(error))

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
