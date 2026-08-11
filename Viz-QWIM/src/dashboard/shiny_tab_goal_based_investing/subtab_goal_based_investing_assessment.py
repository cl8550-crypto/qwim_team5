# """Deterministic assessment results for the Goal-Based Investing dashboard tab."""

# from __future__ import annotations

# from typing import Any

# from shiny import module, render, ui

# from ._goal_based_investing_state import format_currency, get_goal_based_investing_state


# def _create_metric_card(*, label: str, value: str) -> Any:
#     """Create one compact result card for a key goal-planning metric."""
#     return ui.card(
#         ui.card_header(label),
#         ui.card_body(ui.h4(value, class_="mb-0")),
#         class_="h-100",
#     )


# @module.ui
# def subtab_goal_based_investing_assessment_ui(
#     *,
#     data_utils: dict[str, Any],
#     data_inputs: dict[str, Any],
# ) -> Any:  # pragma: no cover
#     """Create the deterministic assessment result layout."""
#     del data_utils, data_inputs
#     return ui.page_fluid(
#         ui.h3("Assessment"),
#         ui.output_ui("output_assessment_status"),
#         ui.layout_columns(
#             ui.output_ui("output_target_amount"),
#             ui.output_ui("output_projected_amount"),
#             ui.output_ui("output_funding_ratio"),
#             ui.output_ui("output_shortfall_surplus"),
#             col_widths=(3, 3, 3, 3),
#         ),
#         ui.card(
#             ui.card_header("Goal progress"),
#             ui.card_body(ui.output_plot("output_goal_progress")),
#             class_="mt-3",
#         ),
#         ui.card(
#             ui.card_header("Assumptions and results"),
#             ui.card_body(ui.output_ui("output_assessment_summary")),
#             class_="mt-3",
#         ),
#         ui.card(
#             ui.card_header("Selected risk policy"),
#             ui.card_body(ui.output_ui("output_policy_allocation")),
#             class_="mt-3",
#         ),
#         ui.card(
#             ui.card_header("Small multistage allocation preview"),
#             ui.card_body(ui.output_ui("output_multistage_preview")),
#             class_="mt-3",
#         ),
#     )


# @module.server
# def subtab_goal_based_investing_assessment_server(
#     input: Any,
#     output: Any,
#     session: Any,
#     data_utils: dict[str, Any],
#     data_inputs: dict[str, Any],
#     reactives_shiny: dict[str, Any],
# ) -> None:  # pragma: no cover
#     """Render the latest saved deterministic goal assessment."""
#     del input, session, data_utils, data_inputs
#     state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

#     def get_assessment_state() -> dict[str, Any] | None:
#         """Return the latest result only when Profile has completed an assessment."""
#         return state_values["Assessment"]()

#     def get_metric_or_prompt(*, label: str, value: str | None = None) -> Any:
#         """Return a metric card or a neutral prompt before an assessment exists."""
#         return _create_metric_card(label=label, value=value or "--")

#     @output
#     @render.ui
#     def output_assessment_status() -> Any:
#         """Render a clear funded-status summary or an initial prompt."""
#         validation_error = state_values["Error"]()
#         if validation_error is not None:
#             return ui.div(validation_error, class_="alert alert-danger")

#         result_state = get_assessment_state()
#         if result_state is None:
#             return ui.div("Complete Goal Profile and select Assess goal to see results.", class_="alert alert-info")

#         assessment = result_state["Assessment"]
#         status = "On track" if assessment.is_funded else "Shortfall identified"
#         status_class = "alert alert-success" if assessment.is_funded else "alert alert-warning"
#         message = (
#             f"{assessment.goal_name}: {status}. Projected value is "
#             f"{format_currency(amount=assessment.projected_amount)} against a target of "
#             f"{format_currency(amount=assessment.target_amount)}."
#         )
#         if assessment.success_probability is not None:
#             message += f" Historical-bootstrap goal success probability: {assessment.success_probability:.1%}."
#         return ui.div(message, class_=status_class)

#     @output
#     @render.ui
#     def output_target_amount() -> Any:
#         """Render the target amount metric."""
#         result_state = get_assessment_state()
#         value = None if result_state is None else format_currency(amount=result_state["Assessment"].target_amount)
#         return get_metric_or_prompt(label="Target amount", value=value)

#     @output
#     @render.ui
#     def output_projected_amount() -> Any:
#         """Render the projected amount metric."""
#         result_state = get_assessment_state()
#         value = None if result_state is None else format_currency(amount=result_state["Assessment"].projected_amount)
#         return get_metric_or_prompt(label="Projected amount", value=value)

#     @output
#     @render.ui
#     def output_funding_ratio() -> Any:
#         """Render the projected-to-target funding ratio."""
#         result_state = get_assessment_state()
#         value = None if result_state is None else f"{result_state['Assessment'].funding_ratio:.1%}"
#         return get_metric_or_prompt(label="Funding ratio", value=value)

#     @output
#     @render.ui
#     def output_shortfall_surplus() -> Any:
#         """Render the shortfall or surplus metric."""
#         result_state = get_assessment_state()
#         if result_state is None:
#             return get_metric_or_prompt(label="Shortfall / surplus")
#         assessment = result_state["Assessment"]
#         label = "Surplus" if assessment.is_funded else "Shortfall"
#         amount = assessment.surplus_amount if assessment.is_funded else assessment.shortfall_amount
#         return get_metric_or_prompt(label=label, value=format_currency(amount=amount))

#     @output
#     @render.plot
#     def output_goal_progress() -> Any:
#         """Plot annual projected values against the fixed target amount."""
#         result_state = get_assessment_state()
#         if result_state is None:
#             return None

#         from matplotlib import pyplot as plt

#         assessment = result_state["Assessment"]
#         figure, axis = plt.subplots(figsize=(10, 4.5))
#         axis.plot(result_state["Years"], result_state["Annual_Progress"], color="#20c997", linewidth=2.5, label="Projected value")
#         axis.axhline(assessment.target_amount, color="#dc3545", linestyle="--", linewidth=2, label="Target amount")
#         axis.set_xlabel("Years from today")
#         axis.set_ylabel("Value ($)")
#         axis.ticklabel_format(axis="y", style="plain")
#         axis.legend()
#         axis.grid(alpha=0.25)
#         figure.tight_layout()
#         return figure

#     @output
#     @render.ui
#     def output_assessment_summary() -> Any:
#         """Render a compact assumptions and results table."""
#         result_state = get_assessment_state()
#         if result_state is None:
#             return ui.p("No assessment has been run.", class_="text-muted")

#         profile = state_values["Profile"]()
#         assessment = result_state["Assessment"]
#         table_rows = [
#             ("Goal", assessment.goal_name),
#             ("Years to goal", str(profile["Years_To_Goal"])),
#             ("Historical mean annual return (progress path)", f"{profile['Annual_Return_Percent']:.2f}%"),
#             ("Annual contribution", format_currency(amount=profile["Annual_Contribution"])),
#             ("Confirmed plan assets", format_currency(amount=profile["Confirmed_Plan_Assets"])),
#             ("Target amount", format_currency(amount=assessment.target_amount)),
#             ("Projected amount", format_currency(amount=assessment.projected_amount)),
#         ]
#         if assessment.success_probability is not None:
#             table_rows.append(("Goal success probability", f"{assessment.success_probability:.1%}"))
#         if "Portfolio_Policy" in profile:
#             policy = profile["Portfolio_Policy"]
#             table_rows.extend(
#                 [
#                     ("Risk profile", policy.profile),
#                     ("Portfolio 95% expected shortfall", f"{policy.expected_shortfall:.2%}"),
#                 ],
#             )
#         financial_plan = state_values["Financial_Plan"]()
#         if financial_plan is not None:
#             table_rows.extend(
#                 [
#                     ("Retirement spending gap", format_currency(amount=financial_plan.annual_retirement_gap)),
#                     ("Staged cash-flow adapter", "Prepared for multistage model"),
#                 ],
#             )
#         return ui.tags.table(
#             ui.tags.thead(ui.tags.tr(ui.tags.th("Metric"), ui.tags.th("Value"))),
#             ui.tags.tbody(*[ui.tags.tr(ui.tags.td(label), ui.tags.td(value)) for label, value in table_rows]),
#             class_="table table-striped mb-0",
#         )

#     @output
#     @render.ui
#     def output_policy_allocation() -> Any:
#         """Show the client-selected policy weights and plan-dollar allocations."""
#         profile = state_values["Profile"]()
#         if profile is None or "Portfolio_Policy" not in profile:
#             return ui.p("No risk policy has been selected.", class_="text-muted")
#         policy = profile["Portfolio_Policy"]
#         dollars = policy.dollar_allocations(profile["Confirmed_Plan_Assets"])
#         rows = [
#             ui.tags.tr(
#                 ui.tags.td(asset),
#                 ui.tags.td(f"{weight:.1%}"),
#                 ui.tags.td(format_currency(amount=dollars[asset])),
#             )
#             for asset, weight in policy.weights.items()
#             if weight > 0.0001
#         ]
#         return ui.div(
#             ui.p(
#                 f"{policy.profile} policy · historical 95% expected shortfall: {policy.expected_shortfall:.2%}.",
#             ),
#             ui.tags.table(
#                 ui.tags.thead(
#                     ui.tags.tr(ui.tags.th("ETF"), ui.tags.th("Weight"), ui.tags.th("Plan allocation")),
#                 ),
#                 ui.tags.tbody(*rows),
#                 class_="table table-striped mb-0",
#             ),
#         )

#     @output
#     @render.ui
#     def output_multistage_preview() -> Any:
#         """Show the solved small-tree allocation preview, when available."""
#         preview = state_values["Multistage_Preview"]()
#         if preview is None:
#             return ui.p("No multistage preview has been solved.", class_="text-muted")
#         allocation_rows = [
#             ui.tags.tr(ui.tags.td(asset), ui.tags.td(f"{weight:.1%}"))
#             for asset, weight in preview["Root_Weights"].items()
#         ]
#         shortfall_rows = [
#             ui.tags.tr(ui.tags.td(priority.title()), ui.tags.td(format_currency(amount=amount)))
#             for priority, amount in preview["Expected_Priority_Shortfall"].items()
#         ]
#         return ui.div(
#             ui.p(
#                 f"Solved {preview['Return_Periods']}-period, {preview['Branches']}-branch historical-bootstrap tree "
#                 f"({preview['Scenario_Nodes']} nodes). No P/NP discrete goal is included in this Version 1 preview.",
#             ),
#             ui.p(f"Expected terminal wealth: {format_currency(amount=preview['Expected_Terminal_Wealth'])}."),
#             ui.layout_columns(
#                 ui.tags.table(
#                     ui.tags.thead(ui.tags.tr(ui.tags.th("Root allocation"), ui.tags.th("Weight"))),
#                     ui.tags.tbody(*allocation_rows),
#                     class_="table table-striped mb-0",
#                 ),
#                 ui.tags.table(
#                     ui.tags.thead(ui.tags.tr(ui.tags.th("Expected shortfall"), ui.tags.th("Amount"))),
#                     ui.tags.tbody(*shortfall_rows),
#                     class_="table table-striped mb-0",
#                 ),
#                 col_widths=(6, 6),
#             ),
#         )


# Subtab_Goal_Based_Investing_Assessment = subtab_goal_based_investing_assessment_ui
"""Deterministic assessment results for the Goal-Based Investing dashboard tab."""

from __future__ import annotations

from typing import Any

from shiny import module, render, ui

from ._goal_based_investing_state import format_currency, get_goal_based_investing_state


def _create_metric_card(*, label: str, value: str, tooltip_text: str | None = None) -> Any:
    """Create one compact result card for a key goal-planning metric.

    When ``tooltip_text`` is given, the label carries a small hover tooltip
    so the technical/original term (e.g. "projected amount") stays
    discoverable without being the primary word the user has to parse.
    """
    header: Any = label
    if tooltip_text:
        header = ui.tooltip(
            ui.span(label, " ", ui.tags.i(class_="bi bi-info-circle text-muted"), style="cursor:help;"),
            tooltip_text,
        )
    return ui.card(
        ui.card_header(header),
        ui.card_body(ui.h4(value, class_="mb-0")),
        class_="h-100",
    )


def _how_calculated_details(text: str) -> Any:
    """A collapsed '<details>' block that hides technical explanation by default."""
    return ui.tags.details(
        ui.tags.summary("How is this calculated?", style="cursor:pointer; color:#6c757d;", class_="small"),
        ui.p(text, class_="text-muted small mt-2 mb-0"),
        class_="mt-2",
    )


@module.ui
def subtab_goal_based_investing_assessment_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the deterministic assessment result layout.

    Outcome first, mechanics second: the headline number and plain-language
    status come before the KPI cards, which come before the chart, which
    comes before the technical/mechanical detail (assumptions, risk policy,
    multistage preview) at the bottom of the page.
    """
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Your Plan"),
        ui.card(
            ui.div(
                ui.p("Estimated wealth at your goal date", class_="text-muted mb-1"),
                ui.h2(ui.output_text("output_headline_projected_wealth"), class_="display-5 fw-bold mb-1"),
                ui.output_ui("output_assessment_status"),
                _how_calculated_details(
                    "We project your current confirmed plan assets forward using your annual "
                    "contribution and an assumed annual return, based on your selected risk "
                    "policy's historical performance."
                ),
                class_="text-center py-3",
            ),
        ),
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
            ui.card_header("Historical-bootstrap terminal value distribution"),
            ui.card_body(ui.output_plot("output_terminal_distribution")),
            class_="mt-3",
        ),
        ui.tags.details(
            ui.tags.summary(
                "Details: assumptions, risk policy, and multistage preview",
                style="cursor: pointer;",
                class_="h5 mt-4",
            ),
            ui.card(
                ui.card_header("Assumptions and results"),
                ui.card_body(ui.output_ui("output_assessment_summary")),
                class_="mt-3",
            ),
            ui.card(
                ui.card_header("Selected risk policy"),
                ui.card_body(ui.output_ui("output_policy_allocation")),
                class_="mt-3",
            ),
            ui.card(
                ui.card_header("Small multistage allocation preview"),
                ui.card_body(ui.output_ui("output_multistage_preview")),
                class_="mt-3",
            ),
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

    def get_metric_or_prompt(*, label: str, value: str | None = None, tooltip_text: str | None = None) -> Any:
        """Return a metric card or a neutral prompt before an assessment exists."""
        return _create_metric_card(label=label, value=value or "--", tooltip_text=tooltip_text)

    @output
    @render.text
    def output_headline_projected_wealth() -> Any:
        """Big headline number: projected wealth at the goal date, compactly formatted."""
        result_state = get_assessment_state()
        if result_state is None:
            return "--"
        return format_currency(amount=result_state["Assessment"].projected_amount)

    @output
    @render.ui
    def output_assessment_status() -> Any:
        """Render a clear plan-status summary or an initial prompt."""
        validation_error = state_values["Error"]()
        if validation_error is not None:
            return ui.div(validation_error, class_="alert alert-danger")

        result_state = get_assessment_state()
        if result_state is None:
            return ui.div("Complete your goal details and select Assess goal to see results.", class_="alert alert-info")

        assessment = result_state["Assessment"]
        status = "On track" if assessment.is_funded else "Needs attention"
        status_class = "alert alert-success" if assessment.is_funded else "alert alert-warning"
        message = (
            f"{assessment.goal_name}: {status}, based on thousands of possible market scenarios. "
            f"Your goal is {format_currency(amount=assessment.target_amount)}."
        )
        if assessment.success_probability is not None:
            message += f" Chance of reaching your goal: {assessment.success_probability:.0%}."
        return ui.div(message, class_=status_class)

    @output
    @render.ui
    def output_target_amount() -> Any:
        """Render the target amount metric."""
        result_state = get_assessment_state()
        value = None if result_state is None else format_currency(amount=result_state["Assessment"].target_amount)
        return get_metric_or_prompt(
            label="Your goal",
            value=value,
            tooltip_text="The amount of money you're aiming to have by your goal date. Also called the target amount.",
        )

    @output
    @render.ui
    def output_projected_amount() -> Any:
        """Render the projected amount metric."""
        result_state = get_assessment_state()
        value = None if result_state is None else format_currency(amount=result_state["Assessment"].projected_amount)
        return get_metric_or_prompt(
            label="Projected wealth",
            value=value,
            tooltip_text=(
                "The amount of money you're projected to have by your goal date, based on your "
                "current plan assets, contributions, and assumed return. Also called the projected amount."
            ),
        )

    @output
    @render.ui
    def output_funding_ratio() -> Any:
        """Render the projected-to-target funding ratio."""
        result_state = get_assessment_state()
        value = None if result_state is None else f"{result_state['Assessment'].funding_ratio:.1%}"
        return get_metric_or_prompt(
            label="% of goal funded",
            value=value,
            tooltip_text=(
                "Your projected wealth as a share of your goal -- 100% means you're on pace to fully "
                "fund it. Also called the funding ratio."
            ),
        )

    @output
    @render.ui
    def output_shortfall_surplus() -> Any:
        """Render the shortfall or surplus metric."""
        result_state = get_assessment_state()
        if result_state is None:
            return get_metric_or_prompt(label="Gap to goal")
        assessment = result_state["Assessment"]
        is_surplus = assessment.is_funded
        label = "Cushion above goal" if is_surplus else "Amount short of goal"
        amount = assessment.surplus_amount if is_surplus else assessment.shortfall_amount
        tooltip_text = (
            "How much more than your goal you're projected to have. Also called the surplus."
            if is_surplus
            else "How much less than your goal you're projected to have. Also called the shortfall."
        )
        return get_metric_or_prompt(label=label, value=format_currency(amount=amount), tooltip_text=tooltip_text)

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
    @render.plot
    def output_terminal_distribution() -> Any:
        """Plot the policy-bootstrap range and the client's target amount."""
        result_state = get_assessment_state()
        if result_state is None or result_state["Terminal_Values"] is None:
            return None

        from matplotlib import pyplot as plt

        terminal_values = result_state["Terminal_Values"]
        assessment = result_state["Assessment"]
        figure, axis = plt.subplots(figsize=(10, 4.5))
        axis.hist(terminal_values, bins=35, color="#0d6efd", alpha=0.75)
        axis.axvline(
            assessment.target_amount,
            color="#dc3545",
            linestyle="--",
            linewidth=2,
            label="Target amount",
        )
        axis.axvline(
            assessment.projected_amount,
            color="#20c997",
            linewidth=2,
            label="Median projected value",
        )
        axis.set_xlabel("Terminal portfolio value ($)")
        axis.set_ylabel("Historical-bootstrap scenarios")
        axis.ticklabel_format(axis="x", style="plain")
        axis.legend()
        axis.grid(axis="y", alpha=0.25)
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
            ("Historical mean annual return (progress path)", f"{profile['Annual_Return_Percent']:.2f}%"),
            ("Annual contribution", format_currency(amount=profile["Annual_Contribution"])),
            ("Confirmed plan assets", format_currency(amount=profile["Confirmed_Plan_Assets"])),
            ("Target amount", format_currency(amount=assessment.target_amount)),
            ("Projected amount", format_currency(amount=assessment.projected_amount)),
        ]
        if assessment.success_probability is not None:
            table_rows.append(("Goal success probability", f"{assessment.success_probability:.1%}"))
        if "Portfolio_Policy" in profile:
            policy = profile["Portfolio_Policy"]
            table_rows.extend(
                [
                    ("Risk profile", policy.profile),
                    ("Portfolio 95% expected shortfall", f"{policy.expected_shortfall:.2%}"),
                ],
            )
        financial_plan = state_values["Financial_Plan"]()
        if financial_plan is not None:
            table_rows.extend(
                [
                    ("Retirement spending gap", format_currency(amount=financial_plan.annual_retirement_gap)),
                    ("Staged cash-flow adapter", "Prepared for multistage model"),
                ],
            )
        return ui.tags.table(
            ui.tags.thead(ui.tags.tr(ui.tags.th("Metric"), ui.tags.th("Value"))),
            ui.tags.tbody(*[ui.tags.tr(ui.tags.td(label), ui.tags.td(value)) for label, value in table_rows]),
            class_="table table-striped mb-0",
        )

    @output
    @render.ui
    def output_policy_allocation() -> Any:
        """Show the client-selected policy weights and plan-dollar allocations."""
        profile = state_values["Profile"]()
        if profile is None or "Portfolio_Policy" not in profile:
            return ui.p("No risk policy has been selected.", class_="text-muted")
        policy = profile["Portfolio_Policy"]
        dollars = policy.dollar_allocations(profile["Confirmed_Plan_Assets"])
        rows = [
            ui.tags.tr(
                ui.tags.td(asset),
                ui.tags.td(f"{weight:.1%}"),
                ui.tags.td(format_currency(amount=dollars[asset])),
            )
            for asset, weight in policy.weights.items()
            if weight > 0.0001
        ]
        return ui.div(
            ui.p(
                f"{policy.profile} policy · historical 95% expected shortfall: {policy.expected_shortfall:.2%}.",
            ),
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(ui.tags.th("ETF"), ui.tags.th("Weight"), ui.tags.th("Plan allocation")),
                ),
                ui.tags.tbody(*rows),
                class_="table table-striped mb-0",
            ),
        )

    @output
    @render.ui
    def output_multistage_preview() -> Any:
        """Show the solved small-tree allocation preview, when available."""
        preview = state_values["Multistage_Preview"]()
        if preview is None:
            return ui.p("No multistage preview has been solved.", class_="text-muted")
        allocation_rows = [
            ui.tags.tr(ui.tags.td(asset), ui.tags.td(f"{weight:.1%}"))
            for asset, weight in preview["Root_Weights"].items()
        ]
        shortfall_rows = [
            ui.tags.tr(ui.tags.td(priority.title()), ui.tags.td(format_currency(amount=amount)))
            for priority, amount in preview["Expected_Priority_Shortfall"].items()
        ]
        return ui.div(
            ui.p(
                f"Solved {preview['Return_Periods']}-period, {preview['Branches']}-branch historical-bootstrap tree "
                f"({preview['Scenario_Nodes']} nodes). No P/NP discrete goal is included in this Version 1 preview.",
            ),
            ui.p(f"Expected terminal wealth: {format_currency(amount=preview['Expected_Terminal_Wealth'])}."),
            ui.layout_columns(
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(ui.tags.th("Root allocation"), ui.tags.th("Weight"))),
                    ui.tags.tbody(*allocation_rows),
                    class_="table table-striped mb-0",
                ),
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(ui.tags.th("Expected shortfall"), ui.tags.th("Amount"))),
                    ui.tags.tbody(*shortfall_rows),
                    class_="table table-striped mb-0",
                ),
                col_widths=(6, 6),
            ),
        )


Subtab_Goal_Based_Investing_Assessment = subtab_goal_based_investing_assessment_ui