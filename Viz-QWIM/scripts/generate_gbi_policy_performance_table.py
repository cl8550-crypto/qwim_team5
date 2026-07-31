"""Generate the Overleaf-ready performance table for the five GBI policies."""

from __future__ import annotations

import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "performance"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.goal_based_investing import load_predefined_cvar_policies  # noqa: E402
from src.models.goal_based_investing.portfolio_performance import (  # noqa: E402
    build_policy_performance_table,
    write_performance_latex_table,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (  # noqa: E402
    find_cleaned_data_dir,
    load_monthly_market_panel,
)


def main() -> None:
    """Create a report artifact using the same ETF data as the GBI policies."""
    project_root = PROJECT_ROOT
    market_panel = load_monthly_market_panel(find_cleaned_data_dir(project_root))
    policy_returns = market_panel.loc["2018-06-01":"2026-05-31", ["BIL", "XLK", "XLP", "AGG", "TIP", "GLD"]]
    table = build_policy_performance_table(policy_returns, policies=load_predefined_cvar_policies())
    output = write_performance_latex_table(
        table,
        REPORT_DIR / "gbi_policy_performance.tex",
        caption="In-sample historical performance of the fixed Goal-Based Investing policies (June 2018--May 2026).",
        label="tab:gbi-policy-performance",
    )
    print(table.to_string(
        index=False,
        formatters=dict.fromkeys(
            ("Annualized return", "Annualized volatility", "Maximum drawdown", "Historical ES (95%)"),
            "{:.2%}".format,
        ),
    ))
    print(f"\\nWrote {output}")


if __name__ == "__main__":
    main()
