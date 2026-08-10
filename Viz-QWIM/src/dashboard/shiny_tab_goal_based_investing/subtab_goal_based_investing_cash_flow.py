"""Retirement cash-flow and goal-priority view for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

from shiny import module, reactive, render, ui

from ._goal_based_investing_state import (
    build_goal_priority_cashflow_state,
    format_currency,
    get_goal_based_investing_state,
)


@module.ui
def subtab_goal_based_investing_cash_flow_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the historical retirement cash-flow result page."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Retirement Cash Flow"),
        ui.p(
            "Historical policy returns are applied to essential, important, and aspirational spending. "
            "Important and aspirational spending may be deferred for up to 12 months.",
        ),
        ui.output_ui("output_cash_flow_status"),
        ui.layout_columns(
            ui.output_ui("output_cash_flow_final_wealth"),
            ui.output_ui("output_cash_flow_essential_rate"),
            ui.output_ui("output_cash_flow_postponable_rate"),
            col_widths=(4, 4, 4),
        ),
        ui.card(
            ui.card_header("Historical retirement wealth path"),
            ui.card_body(ui.output_plot("output_cash_flow_wealth_chart")),
            class_="mt-3",
        ),
        ui.card(
            ui.card_header("Goal-priority payment coverage"),
            ui.card_body(ui.output_plot("output_cash_flow_coverage_chart")),
            class_="mt-3",
        ),
    )


def _metric_card(*, label: str, value: str) -> Any:
    """Create one retirement cash-flow metric card."""
    return ui.card(ui.card_header(label), ui.card_body(ui.h4(value, class_="mb-0")))


@module.server
def subtab_goal_based_investing_cash_flow_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Render the selected policy's historical retirement cash-flow outcomes."""
    del input, session, data_utils, data_inputs
    state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

    @reactive.calc
    def cash_flow_state() -> dict[str, Any] | None:
        """Build cash-flow results whenever the profile changes."""
        profile = state_values["Profile"]()
        return None if profile is None else build_goal_priority_cashflow_state(profile=profile)

    @output
    @render.ui
    def output_cash_flow_status() -> Any:
        """Explain the analysis source or show an error for unavailable state."""
        try:
            result_state = cash_flow_state()
        except ValueError as error:
            return ui.div(str(error), class_="alert alert-warning")
        if result_state is None:
            return ui.div("Loading the ready-to-run demo cash-flow assessment…", class_="alert alert-info")
        return ui.div(
            "Historical scenario only: this shows how the selected policy's observed monthly return path "
            "would have funded the current spending assumptions, not a forecast.",
            class_="alert alert-info",
        )

    @output
    @render.ui
    def output_cash_flow_final_wealth() -> Any:
        """Render ending wealth after historical cash flows."""
        result_state = cash_flow_state()
        value = "--" if result_state is None else format_currency(amount=result_state["Result"].final_wealth)
        return _metric_card(label="Final wealth", value=value)

    @output
    @render.ui
    def output_cash_flow_essential_rate() -> Any:
        """Render the non-postponable essential-goal coverage rate."""
        result_state = cash_flow_state()
        value = "--" if result_state is None else f"{result_state['Payment_Rates']['Essential']:.1%}"
        return _metric_card(label="Essential spending paid", value=value)

    @output
    @render.ui
    def output_cash_flow_postponable_rate() -> Any:
        """Render combined important/aspirational payment coverage."""
        result_state = cash_flow_state()
        if result_state is None:
            return _metric_card(label="Postponable spending paid", value="--")
        rates = result_state["Payment_Rates"]
        return _metric_card(
            label="Postponable spending paid",
            value=f"{(rates['Important'] + rates['Aspirational']) / 2.0:.1%}",
        )

    @output
    @render.plot
    def output_cash_flow_wealth_chart() -> Any:
        """Plot the realised monthly wealth path after priority cash flows."""
        result_state = cash_flow_state()
        if result_state is None:
            return None
        from matplotlib import pyplot as plt

        wealth_path = result_state["Result"].monthly_wealth
        figure, axis = plt.subplots(figsize=(10, 4.5))
        axis.plot(wealth_path.index, wealth_path.values, color="#20c997", linewidth=2)
        axis.fill_between(wealth_path.index, wealth_path.values, alpha=0.16, color="#20c997")
        axis.set_ylabel("Portfolio wealth ($)")
        axis.set_xlabel("Historical month")
        axis.grid(alpha=0.25)
        figure.tight_layout()
        return figure

    @output
    @render.plot
    def output_cash_flow_coverage_chart() -> Any:
        """Plot payment coverage by spending-priority tier."""
        result_state = cash_flow_state()
        if result_state is None:
            return None
        from matplotlib import pyplot as plt

        rates = result_state["Payment_Rates"]
        labels = list(rates)
        values = [rates[label] * 100.0 for label in labels]
        figure, axis = plt.subplots(figsize=(10, 4.5))
        colors = ["#20c997", "#0d6efd", "#fd7e14"]
        axis.bar(labels, values, color=colors)
        axis.set_ylim(0, 100)
        axis.set_ylabel("Payments made (%)")
        axis.grid(axis="y", alpha=0.25)
        figure.tight_layout()
        return figure


Subtab_Goal_Based_Investing_Cash_Flow = subtab_goal_based_investing_cash_flow_ui
