"""Goal Parity plot builders and exporters, mirroring ``_report_plot_allocation``.

Reads the already-exported ``outputs_goal_parity.json`` (written by
``export_outputs_goal_parity`` earlier in the report pipeline) rather than
recomputing the pipeline a second time; falls back to a fresh compute if the
JSON is missing so the module also works standalone.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import pandas as pd  # pandas-boundary: plotnine requires pandas DataFrame input.

from plotnine import aes, element_text, geom_col, ggplot, labs, theme

from src.dashboard.reporting._report_plot_returns import (
    _IMAGES_DIR,
    _PALETTE,
    _QWIM_THEME,
    _create_placeholder_svg,
    _save_plot,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)

_REPORTING_DIR = Path(__file__).resolve().parent
_OUTPUTS_GOAL_PARITY_JSON = _REPORTING_DIR / "outputs_json" / "outputs_goal_parity.json"

#: Goal Parity Balanced target (Roadmap Sec 3.5): all four goals at 25%.
_THETA_BALANCED: dict[str, float] = {
    "Liquidity": 0.25, "Income": 0.25, "Preservation": 0.25, "Growth": 0.25,
}


def _load_goal_parity_outputs() -> dict[str, Any]:
    """Read outputs_goal_parity.json, falling back to a fresh compute."""
    if _OUTPUTS_GOAL_PARITY_JSON.exists():
        try:
            return json.loads(_OUTPUTS_GOAL_PARITY_JSON.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 — report boundary, fall through to recompute
            _logger.warning("Could not read outputs_goal_parity.json: %s", exc)
    from src.dashboard.reporting._report_data_export_goal_parity import (
        export_outputs_goal_parity_impl_QWIM,
    )

    path = export_outputs_goal_parity_impl_QWIM(reactives_shiny=None)
    return json.loads(path.read_text(encoding="utf-8"))


def build_plotnine_goal_parity_weights(
    *, top_weights: list[dict[str, Any]]) -> Any:
    """Build a bar chart of the strategic portfolio's top weights."""
    try:
        if not top_weights:
            return None
        df = pd.DataFrame(top_weights).sort_values("weight", ascending=False).reset_index(drop=True)
        return (
            ggplot(df, aes(x="ticker", y="weight", fill="ticker"))
            + geom_col(show_legend=False)
            + labs(title="Goal Parity Strategic Weights", x="Asset", y="Weight")
            + _QWIM_THEME
            + theme(axis_text_x=element_text(angle=45, hjust=1))
        )
    except Exception as exc:  # noqa: BLE001 — report boundary tolerates plotting failures.
        _logger.warning("build_plotnine_goal_parity_weights: %s", exc)
        return None


def build_plotnine_goal_parity_goal_powers(
    *, goal_powers: dict[str, float]) -> Any:
    """Build a grouped bar chart of achieved vs. target (25%) goal powers."""
    try:
        if not goal_powers:
            return None
        goals = list(_THETA_BALANCED)
        df = pd.DataFrame(
            {
                "goal": goals * 2,
                "power": [goal_powers.get(g, 0.0) for g in goals]
                + [_THETA_BALANCED[g] for g in goals],
                "series": ["Achieved"] * len(goals) + ["Target (25%)"] * len(goals),
            },
        )
        return (
            ggplot(df, aes(x="goal", y="power", fill="series"))
            + geom_col(position="dodge")
            + labs(title="Goal Powers: Achieved vs. Target", x="Goal", y="Power")
            + _QWIM_THEME
        )
    except Exception as exc:  # noqa: BLE001 — report boundary tolerates plotting failures.
        _logger.warning("build_plotnine_goal_parity_goal_powers: %s", exc)
        return None


def export_plot_goal_parity_weights(
    *, reactives_shiny: dict | None) -> Path | None:
    """Export the Goal Parity weights bar chart to SVG."""
    del reactives_shiny  # data comes from the already-exported outputs JSON
    try:
        outputs = _load_goal_parity_outputs()
        plot = build_plotnine_goal_parity_weights(top_weights=outputs.get("top_weights", []))
        if plot is None:
            return None
        return _save_plot(plot=plot, filename="chart_goal_parity_weights.svg")
    except Exception as exc:  # noqa: BLE001 — report boundary tolerates plotting failures.
        _logger.warning("export_plot_goal_parity_weights: %s", exc)
        return None


def export_plot_goal_parity_goal_powers(
    *, reactives_shiny: dict | None) -> Path | None:
    """Export the Goal Parity goal-powers bar chart to SVG."""
    del reactives_shiny  # data comes from the already-exported outputs JSON
    try:
        outputs = _load_goal_parity_outputs()
        plot = build_plotnine_goal_parity_goal_powers(goal_powers=outputs.get("goal_powers", {}))
        if plot is None:
            return None
        return _save_plot(plot=plot, filename="chart_goal_parity_goal_powers.svg")
    except Exception as exc:  # noqa: BLE001 — report boundary tolerates plotting failures.
        _logger.warning("export_plot_goal_parity_goal_powers: %s", exc)
        return None
