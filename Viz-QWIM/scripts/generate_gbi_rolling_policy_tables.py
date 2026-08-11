"""Generate separate Overleaf tables for 36- and 48-month rolling GBI policies."""

from __future__ import annotations

import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "performance"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.goal_based_investing.portfolio_performance import (  # noqa: E402
    write_performance_latex_table,
)
from src.models.goal_based_investing.rolling_policy_backtest import (  # noqa: E402
    SIX_ETF_ASSETS,
    backtest_rolling_cvar_policies,
    rolling_backtest_performance_table,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (  # noqa: E402
    find_cleaned_data_dir,
    load_monthly_market_panel,
)


def main() -> None:
    """Write one reproducible out-of-sample table per requested lookback."""
    panel = load_monthly_market_panel(find_cleaned_data_dir(PROJECT_ROOT)).loc[
        "2018-06-01":"2026-05-31", list(SIX_ETF_ASSETS),
    ]
    for lookback_months in (36, 48):
        results = backtest_rolling_cvar_policies(panel, lookback_months=lookback_months)
        table = rolling_backtest_performance_table(results)
        output = write_performance_latex_table(
            table,
            REPORT_DIR / f"gbi_rolling_policy_performance_{lookback_months}m.tex",
            caption=(
                "Out-of-sample performance of six-ETF rolling CVaR policies "
                f"({lookback_months}-month trailing window)."
            ),
            label=f"tab:gbi-rolling-policy-{lookback_months}m",
            notes=(
                "Monthly walk-forward out-of-sample returns. Policies are re-optimized quarterly "
                f"from the trailing {lookback_months}-month window; 10bp one-way transaction costs are "
                "deducted at each rebalance. Annual return is CAGR; annual volatility and Sharpe use "
                "monthly data scaled by $\\sqrt{12}$. Sharpe assumes a zero risk-free rate. ES is "
                "historical 95\\% expected shortfall."
            ),
        )
        print(f"{lookback_months}-month window\n{table.to_string(index=False)}\nWrote {output}\n")


if __name__ == "__main__":
    main()
