"""Goal Profile inputs for the Goal-Based Investing dashboard tab."""

from __future__ import annotations

from typing import Any

from shiny import module, reactive, render, ui

from src.models.goal_based_investing import Goal_Based_Investing_Baseline
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

from ._goal_based_investing_state import (
    build_goal_assessment_state,
    get_goal_based_investing_state,
)


@module.ui
def subtab_goal_based_investing_profile_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the goal details and planning-assumptions input form."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Goal Profile"),
        ui.p("Enter one financial goal and the assumptions used to assess it."),
        ui.layout_columns(
            ui.card(
                ui.card_header("Goal details"),
                ui.card_body(
                    ui.input_text("input_goal_name", "Goal name", value="Retirement"),
                    ui.input_numeric(
                        "input_target_amount",
                        "Target amount ($)",
                        value=1_000_000,
                        min=0.01,
                        step=1_000,
                    ),
                    ui.input_numeric(
                        "input_current_amount",
                        "Current amount ($)",
                        value=250_000,
                        min=0,
                        step=1_000,
                    ),
                    ui.input_numeric(
                        "input_years_to_goal",
                        "Years to goal",
                        value=20,
                        min=0,
                        step=1,
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
                    ui.input_numeric(
                        "input_annual_return",
                        "Expected annual return (%)",
                        value=5.0,
                        min=-99.99,
                        step=0.1,
                    ),
                    ui.input_action_button(
                        "input_assess_goal",
                        "Assess goal",
                        class_="btn-primary mt-3",
                    ),
                    ui.output_ui("output_profile_status"),
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
    """Validate profile inputs and publish a deterministic goal assessment."""
    del session, data_utils, data_inputs
    state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

    @reactive.effect
    @reactive.event(input.input_assess_goal)
    def assess_goal() -> None:
        """Assess the saved profile only when the user selects the action button."""
        profile = {
            "Goal_Name": input.input_goal_name(),
            "Target_Amount": input.input_target_amount(),
            "Current_Amount": input.input_current_amount(),
            "Years_To_Goal": int(input.input_years_to_goal()),
            "Annual_Contribution": input.input_annual_contribution(),
            "Annual_Return_Percent": input.input_annual_return(),
        }
        try:
            Goal_Based_Investing_Baseline(
                goal_name=profile["Goal_Name"],
                target_amount=profile["Target_Amount"],
                current_amount=profile["Current_Amount"],
                years_to_goal=profile["Years_To_Goal"],
                annual_contribution=profile["Annual_Contribution"],
            ).project_amount(annual_return=float(profile["Annual_Return_Percent"]) / 100.0)
            state_values["Profile"].set(profile)
            state_values["Assessment"].set(build_goal_assessment_state(profile=profile))
            state_values["Error"].set(None)
        except (Exception_Validation_Input, TypeError, ValueError) as error:
            state_values["Assessment"].set(None)
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


Subtab_Goal_Based_Investing_Profile = subtab_goal_based_investing_profile_ui
