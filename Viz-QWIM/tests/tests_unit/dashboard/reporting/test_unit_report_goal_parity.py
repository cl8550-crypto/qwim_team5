"""Unit tests for the Goal Parity report data/plot export functions."""

from __future__ import annotations

import json

import pytest

from src.dashboard.reporting._report_data_export_goal_parity import (
    export_inputs_goal_parity_impl_QWIM,
    export_outputs_goal_parity_impl_QWIM,
)
from src.dashboard.reporting._report_plot_goal_parity import (
    build_plotnine_goal_parity_goal_powers,
    build_plotnine_goal_parity_weights,
    export_plot_goal_parity_goal_powers,
    export_plot_goal_parity_weights,
)
from src.models.goal_parity.utils_goal_parity import GOALS


class Test_Export_Inputs_Goal_Parity:
    def test_writes_valid_json_with_no_reactives(self) -> None:
        path = export_inputs_goal_parity_impl_QWIM(reactives_shiny=None)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["risk_profile"] == "Moderate"
        assert data["strategic_horizon_years"] == 30.0

    def test_barrier_and_tolerance_complement(self) -> None:
        path = export_inputs_goal_parity_impl_QWIM(reactives_shiny=None)
        data = json.loads(path.read_text())
        assert data["loss_barrier_b"] + data["loss_tolerance"] == pytest.approx(1.0)


class Test_Export_Outputs_Goal_Parity:
    def test_writes_valid_json_with_no_reactives(self) -> None:
        path = export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["solver_success"] is True
        assert set(data["goal_powers"]) == set(GOALS)

    def test_goal_powers_sum_to_one(self) -> None:
        path = export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)
        data = json.loads(path.read_text())
        assert sum(data["goal_powers"].values()) == pytest.approx(1.0, abs=1e-6)

    def test_top_weights_sum_close_to_one(self) -> None:
        path = export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)
        data = json.loads(path.read_text())
        total = sum(row["weight"] for row in data["top_weights"])
        assert total > 0.9  # top_weights excludes sub-1% positions

    def test_rebalancing_keys_present(self) -> None:
        path = export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)
        data = json.loads(path.read_text())
        assert set(data["rebalancing"]) == {
            "traded", "num_trades", "turnover", "goal_powers_before", "goal_powers_after",
        }


class Test_Build_Plots:
    def test_weights_chart_builds_from_valid_data(self) -> None:
        plot = build_plotnine_goal_parity_weights(
            top_weights=[{"ticker": "AGG", "weight": 0.35}, {"ticker": "TIP", "weight": 0.30}],
        )
        assert plot is not None

    def test_weights_chart_none_on_empty_data(self) -> None:
        assert build_plotnine_goal_parity_weights(top_weights=[]) is None

    def test_goal_powers_chart_builds_from_valid_data(self) -> None:
        plot = build_plotnine_goal_parity_goal_powers(
            goal_powers={"Liquidity": 0.3, "Income": 0.3, "Preservation": 0.1, "Growth": 0.3},
        )
        assert plot is not None

    def test_goal_powers_chart_none_on_empty_data(self) -> None:
        assert build_plotnine_goal_parity_goal_powers(goal_powers={}) is None


class Test_Export_Plots:
    def test_export_weights_plot_creates_svg(self) -> None:
        export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)  # ensure JSON exists
        path = export_plot_goal_parity_weights(reactives_shiny=None)
        assert path is not None
        assert path.exists()
        assert path.suffix == ".svg"

    def test_export_goal_powers_plot_creates_svg(self) -> None:
        export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)  # ensure JSON exists
        path = export_plot_goal_parity_goal_powers(reactives_shiny=None)
        assert path is not None
        assert path.exists()
        assert path.suffix == ".svg"
