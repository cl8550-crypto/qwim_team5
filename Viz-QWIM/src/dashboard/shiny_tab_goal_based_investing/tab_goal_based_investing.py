# """Top-level Goal-Based Investing tab for the QWIM Dashboard."""

# from __future__ import annotations

# from typing import Any

# from shiny import module, ui

# from .subtab_goal_based_investing_assessment import (
#     subtab_goal_based_investing_assessment_server,
#     subtab_goal_based_investing_assessment_ui,
# )
# from .subtab_goal_based_investing_profile import (
#     subtab_goal_based_investing_profile_server,
#     subtab_goal_based_investing_profile_ui,
# )


# @module.ui
# def tab_goal_based_investing_ui(
#     *,
#     data_utils: dict[str, Any],
#     data_inputs: dict[str, Any],
# ) -> Any:  # pragma: no cover
#     """Create the internal navigation for the Goal-Based Investing model."""
#     return ui.navset_tab(
#         ui.nav_panel(
#             "Goal Profile",
#             subtab_goal_based_investing_profile_ui(
#                 "ID_tab_goal_based_investing_subtab_profile",
#                 data_utils=data_utils,
#                 data_inputs=data_inputs,
#             ),
#         ),
#         ui.nav_panel(
#             "Assessment",
#             subtab_goal_based_investing_assessment_ui(
#                 "ID_tab_goal_based_investing_subtab_assessment",
#                 data_utils=data_utils,
#                 data_inputs=data_inputs,
#             ),
#         ),
#         id="ID_tab_goal_based_investing_tabs_all",
#     )


# @module.server
# def tab_goal_based_investing_server(
#     input: Any,
#     output: Any,
#     session: Any,
#     data_utils: dict[str, Any],
#     data_inputs: dict[str, Any],
#     reactives_shiny: dict[str, Any],
# ) -> dict[str, Any]:  # pragma: no cover
#     """Initialise the Goal Profile and Assessment subtab servers."""
#     profile_server = subtab_goal_based_investing_profile_server(
#         id="ID_tab_goal_based_investing_subtab_profile",
#         data_utils=data_utils,
#         data_inputs=data_inputs,
#         reactives_shiny=reactives_shiny,
#     )
#     assessment_server = subtab_goal_based_investing_assessment_server(
#         id="ID_tab_goal_based_investing_subtab_assessment",
#         data_utils=data_utils,
#         data_inputs=data_inputs,
#         reactives_shiny=reactives_shiny,
#     )

#     return {
#         "Goal_Profile_Server": profile_server,
#         "Assessment_Server": assessment_server,
#     }


# Tab_Goal_Based_Investing = tab_goal_based_investing_ui
"""Top-level Goal-Based Investing tab for the QWIM Dashboard."""

from __future__ import annotations

from typing import Any

from shiny import module, ui

from .subtab_goal_based_investing_assessment import (
    subtab_goal_based_investing_assessment_server,
    subtab_goal_based_investing_assessment_ui,
)
from .subtab_goal_based_investing_cash_flow import (
    subtab_goal_based_investing_cash_flow_server,
    subtab_goal_based_investing_cash_flow_ui,
)
from .subtab_goal_based_investing_policy import (
    subtab_goal_based_investing_policy_server,
    subtab_goal_based_investing_policy_ui,
)
from .subtab_goal_based_investing_profile import (
    subtab_goal_based_investing_profile_server,
    subtab_goal_based_investing_profile_ui,
)


@module.ui
def tab_goal_based_investing_ui(
    *,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
) -> Any:  # pragma: no cover
    """Create the internal navigation for the Goal-Based Investing model."""
    return ui.navset_tab(
        ui.nav_panel(
            "Set Up Your Goal",
            subtab_goal_based_investing_profile_ui(
                "ID_tab_goal_based_investing_subtab_profile",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Your Plan",
            subtab_goal_based_investing_assessment_ui(
                "ID_tab_goal_based_investing_subtab_assessment",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Risk Policy",
            subtab_goal_based_investing_policy_ui(
                "ID_tab_goal_based_investing_subtab_policy",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Retirement Cash Flow",
            subtab_goal_based_investing_cash_flow_ui(
                "ID_tab_goal_based_investing_subtab_cash_flow",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        id="ID_tab_goal_based_investing_tabs_all",
    )


@module.server
def tab_goal_based_investing_server(
    input: Any,
    output: Any,
    session: Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> dict[str, Any]:  # pragma: no cover
    """Initialise all four client-facing Goal-Based Investing subtabs."""
    profile_server = subtab_goal_based_investing_profile_server(
        id="ID_tab_goal_based_investing_subtab_profile",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    assessment_server = subtab_goal_based_investing_assessment_server(
        id="ID_tab_goal_based_investing_subtab_assessment",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    policy_server = subtab_goal_based_investing_policy_server(
        id="ID_tab_goal_based_investing_subtab_policy",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )
    cash_flow_server = subtab_goal_based_investing_cash_flow_server(
        id="ID_tab_goal_based_investing_subtab_cash_flow",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    return {
        "Goal_Profile_Server": profile_server,
        "Assessment_Server": assessment_server,
        "Policy_Server": policy_server,
        "Cash_Flow_Server": cash_flow_server,
    }


Tab_Goal_Based_Investing = tab_goal_based_investing_ui