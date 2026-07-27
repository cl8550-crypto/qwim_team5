"""Deterministic assessment results for the Goal-Based Investing dashboard tab."""

from __future__ import annotations

from typing import Any

from shiny import module, render, ui

from ._goal_based_investing_state import format_currency, get_goal_based_investing_state


def _create_metric_card(*, label: str, value: str) -> Any:
    """Create one compact result card for a key goal-planning metric."""
    return ui.card(
        ui.card_header(label),
        ui.card_body(ui.h4(value, class_="mb-0")),
        class_="h-100",
    )


@module.ui
def subtab_goal_based_investing_assessment_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the deterministic assessment result layout."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Assessment"),
        ui.output_ui("output_assessment_status"),
        ui.layout_columns(
            ui.output_ui("output_target_amount"),
            ui.output_ui("output_projected_amount"),
            ui.output_ui("output_funding_ratio"),
            ui.output_ui("output_shortfall_surplus"),
            col_widths=(3, 3, 3, 3),
        ),
        ui.card(
            ui.card_header("Goal progress"),
            ui.card_body(ui.output_plot("output_goal_progress")),
            class_="mt-3",
        ),
        ui.card(
            ui.card_header("Assumptions and results"),
            ui.card_body(ui.output_ui("output_assessment_summary")),
            class_="mt-3",
        ),
    )


@module.server
def subtab_goal_based_investing_assessment_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Render the latest saved deterministic goal assessment."""
    del input, session, data_utils, data_inputs
    state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

    def get_assessment_state() -> dict[str, Any] | None:
        """Return the latest result only when Profile has completed an assessment."""
        return state_values["Assessment"]()

    def get_metric_or_prompt(*, label: str, value: str | None = None) -> Any:
        """Return a metric card or a neutral prompt before an assessment exists."""
        return _create_metric_card(label=label, value=value or "--")

    @output
    @render.ui
    def output_assessment_status() -> Any:
        """Render a clear funded-status summary or an initial prompt."""
        validation_error = state_values["Error"]()
        if validation_error is not None:
            return ui.div(validation_error, class_="alert alert-danger")

        result_state = get_assessment_state()
        if result_state is None:
            return ui.div("Complete Goal Profile and select Assess goal to see results.", class_="alert alert-info")

        assessment = result_state["Assessment"]
        status = "On track" if assessment.is_funded else "Shortfall identified"
        status_class = "alert alert-success" if assessment.is_funded else "alert alert-warning"
        message = (
            f"{assessment.goal_name}: {status}. Projected value is "
            f"{format_currency(amount=assessment.projected_amount)} against a target of "
            f"{format_currency(amount=assessment.target_amount)}."
        )
        return ui.div(message, class_=status_class)

    @output
    @render.ui
    def output_target_amount() -> Any:
        """Render the target amount metric."""
        result_state = get_assessment_state()
        value = None if result_state is None else format_currency(amount=result_state["Assessment"].target_amount)
        return get_metric_or_prompt(label="Target amount", value=value)

    @output
    @render.ui
    def output_projected_amount() -> Any:
        """Render the projected amount metric."""
        result_state = get_assessment_state()
        value = None if result_state is None else format_currency(amount=result_state["Assessment"].projected_amount)
        return get_metric_or_prompt(label="Projected amount", value=value)

    @output
    @render.ui
    def output_funding_ratio() -> Any:
        """Render the projected-to-target funding ratio."""
        result_state = get_assessment_state()
        value = None if result_state is None else f"{result_state['Assessment'].funding_ratio:.1%}"
        return get_metric_or_prompt(label="Funding ratio", value=value)

    @output
    @render.ui
    def output_shortfall_surplus() -> Any:
        """Render the shortfall or surplus metric."""
        result_state = get_assessment_state()
        if result_state is None:
            return get_metric_or_prompt(label="Shortfall / surplus")
        assessment = result_state["Assessment"]
        label = "Surplus" if assessment.is_funded else "Shortfall"
        amount = assessment.surplus_amount if assessment.is_funded else assessment.shortfall_amount
        return get_metric_or_prompt(label=label, value=format_currency(amount=amount))

    @output
    @render.plot
    def output_goal_progress() -> Any:
        """Plot annual projected values against the fixed target amount."""
        result_state = get_assessment_state()
        if result_state is None:
            return None

        from matplotlib import pyplot as plt

        assessment = result_state["Assessment"]
        figure, axis = plt.subplots(figsize=(10, 4.5))
        axis.plot(result_state["Years"], result_state["Annual_Progress"], color="#20c997", linewidth=2.5, label="Projected value")
        axis.axhline(assessment.target_amount, color="#dc3545", linestyle="--", linewidth=2, label="Target amount")
        axis.set_xlabel("Years from today")
        axis.set_ylabel("Value ($)")
        axis.ticklabel_format(axis="y", style="plain")
        axis.legend()
        axis.grid(alpha=0.25)
        figure.tight_layout()
        return figure

    @output
    @render.ui
    def output_assessment_summary() -> Any:
        """Render a compact assumptions and results table."""
        result_state = get_assessment_state()
        if result_state is None:
            return ui.p("No assessment has been run.", class_="text-muted")

        profile = state_values["Profile"]()
        assessment = result_state["Assessment"]
        table_rows = [
            ("Goal", assessment.goal_name),
            ("Years to goal", str(profile["Years_To_Goal"])),
            ("Expected annual return", f"{profile['Annual_Return_Percent']:.2f}%"),
            ("Annual contribution", format_currency(amount=profile["Annual_Contribution"])),
            ("Target amount", format_currency(amount=assessment.target_amount)),
            ("Projected amount", format_currency(amount=assessment.projected_amount)),
        ]
        return ui.tags.table(
            ui.tags.thead(ui.tags.tr(ui.tags.th("Metric"), ui.tags.th("Value"))),
            ui.tags.tbody(*[ui.tags.tr(ui.tags.td(label), ui.tags.td(value)) for label, value in table_rows]),
            class_="table table-striped mb-0",
        )


Subtab_Goal_Based_Investing_Assessment = subtab_goal_based_investing_assessment_ui
