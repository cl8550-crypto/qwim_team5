"""Assessment subtab for Goal-Based Investing."""

from __future__ import annotations

from typing import Any

from shiny import module, ui


@module.ui
def subtab_goal_based_investing_assessment_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the placeholder for deterministic goal-assessment results."""
    del data_utils, data_inputs
    return ui.page_fluid(
        ui.h3("Assessment"),
        ui.p("Funding results will be displayed here after the goal is assessed."),
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
    """Reserve server scope for the goal-assessment result rendering."""
    del input, output, session, data_utils, data_inputs, reactives_shiny


Subtab_Goal_Based_Investing_Assessment = subtab_goal_based_investing_assessment_ui
