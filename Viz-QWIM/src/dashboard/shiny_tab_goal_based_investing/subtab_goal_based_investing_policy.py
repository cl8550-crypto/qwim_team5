"""Risk-policy comparison view for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

from shiny import module, render, ui

from src.models.goal_based_investing import load_predefined_cvar_policies

from ._goal_based_investing_state import get_goal_based_investing_state


@module.ui
def subtab_goal_based_investing_policy_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the ready-to-view risk-policy comparison page."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Risk Policy"),
        ui.p(
            "The dashboard selects one pre-calibrated CVaR policy from the client's risk profile; "
            "it does not run a live optimizer.",
        ),
        ui.output_ui("output_selected_policy_status"),
        ui.card(
            ui.card_header("Policy allocations by risk profile"),
            ui.card_body(ui.output_plot("output_policy_comparison_chart")),
        ),
        ui.card(
            ui.card_header("Policy risk bands and expected shortfall"),
            ui.card_body(ui.output_ui("output_policy_comparison_table")),
            class_="mt-3",
        ),
    )


@module.server
def subtab_goal_based_investing_policy_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:  # pragma: no cover
    """Render policy information independently of a manual assessment run."""
    del input, session, data_utils, data_inputs
    state_values = get_goal_based_investing_state(reactives_shiny=reactives_shiny)

    @output
    @render.ui
    def output_selected_policy_status() -> Any:
        """Show the policy currently selected by the client or demo profile."""
        profile = state_values["Profile"]()
        if profile is None or "Portfolio_Policy" not in profile:
            return ui.div("Loading the default Moderate-risk policy…", class_="alert alert-info")
        policy = profile["Portfolio_Policy"]
        return ui.div(
            f"Selected policy: {policy.profile}. Historical 95% expected shortfall: "
            f"{policy.expected_shortfall:.2%}.",
            class_="alert alert-success",
        )

    @output
    @render.plot
    def output_policy_comparison_chart() -> Any:
        """Compare all stored risk-policy ETF weights as grouped bars."""
        from matplotlib import pyplot as plt

        policies = load_predefined_cvar_policies()
        profiles = list(policies)
        assets = list(next(iter(policies.values())).weights)
        figure, axis = plt.subplots(figsize=(11, 5))
        bar_width = 0.8 / len(profiles)
        positions = list(range(len(assets)))
        for index, profile_name in enumerate(profiles):
            weights = [policies[profile_name].weights[asset] * 100.0 for asset in assets]
            offsets = [position - 0.4 + bar_width / 2 + index * bar_width for position in positions]
            axis.bar(offsets, weights, width=bar_width, label=profile_name)
        axis.set_xticks(positions, assets)
        axis.set_ylabel("Policy weight (%)")
        axis.set_ylim(0, 100)
        axis.legend(fontsize="small", ncols=2)
        axis.grid(axis="y", alpha=0.25)
        figure.tight_layout()
        return figure

    @output
    @render.ui
    def output_policy_comparison_table() -> Any:
        """Render the client-readable policy risk summary table."""
        policies = load_predefined_cvar_policies()
        rows = [
            ui.tags.tr(
                ui.tags.td(policy.profile),
                ui.tags.td(
                    f"{policy.equity_band.minimum_equity_weight:.0%} - "
                    f"{policy.equity_band.maximum_equity_weight:.0%}",
                ),
                ui.tags.td(f"{policy.expected_shortfall:.2%}"),
            )
            for policy in policies.values()
        ]
        return ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("Risk profile"),
                    ui.tags.th("Permitted equity band"),
                    ui.tags.th("Historical ES (95%)"),
                ),
            ),
            ui.tags.tbody(*rows),
            class_="table table-striped mb-0",
        )


Subtab_Goal_Based_Investing_Policy = subtab_goal_based_investing_policy_ui
