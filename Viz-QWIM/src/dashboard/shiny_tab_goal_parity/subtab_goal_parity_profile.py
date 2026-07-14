"""Goal Parity subtab: Investor Profile (Step 1, Roadmap Sec 3.1).

Reads T and risk profile from the dashboard's Clients tab (advisor-built,
``tolerance_risk`` + ``age_current``/``age_retirement``) when "Use Clients tab
inputs" is checked, with manual overrides otherwise. The server returns a
reactive InvestorProfile consumed by the other Goal Parity subtabs.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from shiny import module, reactive, render, ui

from src.models.goal_parity import InvestorProfile
from src.models.goal_parity.utils_goal_parity import RISK_PROFILE_TO_ETA
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)

_RISK_CHOICES = list(RISK_PROFILE_TO_ETA)


@module.ui
def subtab_goal_parity_profile_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    return ui.div(
        ui.h3("Investor Profile (Step 1)"),
        ui.markdown(
            "Maps the client's categorical risk profile to the power-utility "
            "risk aversion η and the *substantial loss* barrier b(η) = η^(1/(1−η)) "
            "(Cron & Golts 2022), and derives the strategic horizon T from "
            "current vs. retirement age."
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_checkbox("input_use_clients_tab", "Use Clients tab inputs", value=True),
                ui.input_select(
                    "input_risk_profile",
                    "Risk profile (manual override)",
                    choices=_RISK_CHOICES,
                    selected="Moderate",
                ),
                ui.input_numeric("input_horizon", "Strategic horizon T (years)", value=25, min=1, max=60),
                ui.input_select(
                    "input_tau_months",
                    "Rebalancing frequency τ",
                    choices={"1": "Monthly", "3": "Quarterly", "6": "Semi-annual (default)", "12": "Annual"},
                    selected="6",
                ),
                width=320,
            ),
            ui.output_table("output_profile_table"),
            ui.output_text("output_profile_source"),
        ),
    )


@module.server
def subtab_goal_parity_profile_server(  # pragma: no cover
    input: Any,
    output: Any,
    session: Any,
    *,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
):
    del output, session, data_utils, data_inputs

    def _client_record() -> dict | None:
        """Primary client's fields from the shared reactives (Clients tab)."""
        try:
            from src.dashboard.shiny_utils.utils_tab_clients import (
                get_investor_primary_personal_info,
            )

            return get_investor_primary_personal_info(reactives_shiny=reactives_shiny)
        except Exception:  # noqa: BLE001 — any failure falls back to manual inputs
            _logger.debug("Clients-tab inputs unavailable; using manual profile inputs")
            return None

    @reactive.calc
    def profile() -> InvestorProfile:
        record = _client_record() if input.input_use_clients_tab() else None
        if record is not None:
            return InvestorProfile.from_client_record(record)
        horizon = float(input.input_horizon() or 25)
        return InvestorProfile(
            T=max(1.0, horizon),
            tau_months=int(input.input_tau_months() or 6),
            risk_profile=input.input_risk_profile() or "Moderate",
        )

    @render.table
    def output_profile_table() -> pd.DataFrame:
        p = profile()
        return pd.DataFrame(
            {
                "Parameter": [
                    "Strategic horizon T (years)",
                    "Rebalancing frequency τ (months)",
                    "Risk profile",
                    "Risk aversion η",
                    "Loss barrier b(η)",
                    "Loss tolerance 1 − b",
                ],
                "Value": [
                    f"{p.T:.0f}",
                    f"{p.tau_months}",
                    p.risk_profile,
                    f"{p.eta}",
                    f"{p.b:.3f}",
                    f"{p.loss_tolerance:.1%}",
                ],
            }
        )

    @render.text
    def output_profile_source() -> str:
        if input.input_use_clients_tab():
            return (
                "Source: Clients tab (tolerance_risk, age_current/age_retirement). "
                "Uncheck to override manually."
            )
        return "Source: manual overrides in this sidebar."

    return profile
