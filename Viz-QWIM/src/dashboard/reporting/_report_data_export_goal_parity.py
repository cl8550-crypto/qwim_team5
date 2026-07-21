"""Goal Parity data export for the QWIM client report.

Mirrors the Simulation subtab's export pattern (see
``_report_data_export_exports.export_inputs_simulation_impl_QWIM`` /
``export_outputs_simulation_impl_QWIM``) but the Goal Parity model does not
depend on cached reactive DataFrames -- it recomputes the pipeline directly
from the Clients-tab investor profile, exactly as the dashboard's
``shiny_tab_goal_parity`` subtabs do.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.models.goal_parity import InvestorProfile
from src.models.goal_parity.utils_goal_parity import GOALS


def _get_public_report_data_export_module_QWIM() -> Any:
    from src.dashboard.reporting import report_data_export

    return report_data_export


def _build_investor_profile_QWIM(*, reactives_shiny: dict | None) -> InvestorProfile:
    """Build the InvestorProfile from the Clients-tab primary record, same
    fallback path as ``subtab_goal_parity_profile.py``."""
    if reactives_shiny:
        try:
            from src.dashboard.shiny_utils.utils_tab_clients import (
                get_investor_primary_personal_info,
            )

            record = get_investor_primary_personal_info(reactives_shiny=reactives_shiny)
            if record:
                return InvestorProfile.from_client_record(record)
        except Exception:  # noqa: BLE001 — report export tolerates missing/partial reactive state
            pass
    return InvestorProfile(T=30.0, risk_profile="Moderate")


def export_inputs_goal_parity_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Export the Goal Parity investor profile to ``inputs_goal_parity.json``."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Goal_Parity_Inputs",
    )
    if not data:
        profile = _build_investor_profile_QWIM(reactives_shiny=reactives_shiny)
        data = {
            "strategic_horizon_years": profile.T,
            "rebalancing_frequency_months": profile.tau_months,
            "risk_profile": profile.risk_profile,
            "risk_aversion_eta": profile.eta,
            "loss_barrier_b": profile.b,
            "loss_tolerance": profile.loss_tolerance,
        }

    out_path = public_module._INPUTS_JSON_DIR / "inputs_goal_parity.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path


def export_outputs_goal_parity_impl_QWIM(
    *, reactives_shiny: dict | None) -> Path:
    """Run the Goal Parity pipeline and export results to ``outputs_goal_parity.json``."""
    public_module = _get_public_report_data_export_module_QWIM()
    data: dict[str, Any] = public_module._get_data_results_value(
        reactives_shiny = reactives_shiny,
        subtab_key = "Goal_Parity_Outputs",
    )
    if not data:
        try:
            from src.dashboard.shiny_tab_goal_parity._tab_goal_parity_pipeline import (
                decompose_universe,
                run_rebalance_demo,
                run_strategic,
            )

            profile = _build_investor_profile_QWIM(reactives_shiny=reactives_shiny)
            pipeline = decompose_universe(profile)
            strategic = run_strategic(pipeline, mode="balanced")
            rebalance = run_rebalance_demo(pipeline, strategic)

            top_weights = sorted(
                (
                    {"ticker": t, "weight": float(w)}
                    for t, w in zip(strategic.tickers, strategic.weights)
                    if w > 0.01
                ),
                key=lambda row: -row["weight"],
            )

            data = {
                "mode": strategic.mode,
                "solver_success": bool(strategic.success),
                "expected_return": float(strategic.expected_return),
                "goal_powers": {goal: float(strategic.goal_powers[goal]) for goal in GOALS},
                "top_weights": top_weights,
                "rebalancing": {
                    "traded": bool(rebalance.traded),
                    "num_trades": len(rebalance.trades),
                    "turnover": float(rebalance.turnover),
                    "goal_powers_before": {g: float(rebalance.goal_powers_before[g]) for g in GOALS},
                    "goal_powers_after": {g: float(rebalance.goal_powers_after[g]) for g in GOALS},
                },
            }
        except Exception as exc:  # noqa: BLE001 — report export must not crash the PDF pipeline
            public_module._logger.warning("Goal Parity output export failed: %s", exc)
            data = {
                "mode": "balanced",
                "solver_success": False,
                "expected_return": 0.0,
                "goal_powers": {goal: 0.25 for goal in GOALS},
                "top_weights": [],
                "rebalancing": {
                    "traded": False,
                    "num_trades": 0,
                    "turnover": 0.0,
                    "goal_powers_before": {goal: 0.25 for goal in GOALS},
                    "goal_powers_after": {goal: 0.25 for goal in GOALS},
                },
            }

    out_path = public_module._OUTPUTS_JSON_DIR / "outputs_goal_parity.json"
    public_module._write_json(file_path = out_path, data = data)
    return out_path
