"""Generate the two concise Part 2 tests for the GBI capstone report."""

from __future__ import annotations

import sys

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.shiny_tab_goal_based_investing._goal_based_investing_state import (  # noqa: E402
    build_goal_assessment_state,
)
from src.models.goal_based_investing import (  # noqa: E402
    build_client_financial_plan,
    load_predefined_cvar_policies,
)
from src.models.goal_based_investing.portfolio_performance import (  # noqa: E402
    calculate_portfolio_performance,
)
from src.models.goal_based_investing.rolling_policy_backtest import (  # noqa: E402
    MODERATE_BENCHMARK_WEIGHTS,
    SIX_ETF_ASSETS,
    backtest_fixed_cvar_policies,
    backtest_fixed_weight_benchmark,
    backtest_rolling_cvar_policies,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (  # noqa: E402
    find_cleaned_data_dir,
    load_monthly_market_panel,
)


REPORT_DIR = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "part2_testing"
FIGURE_DIR = REPORT_DIR / "figures"


def _write(name: str, contents: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / name).write_text(contents, encoding="utf-8")


def _performance(returns: pd.Series, name: str) -> Any:
    return calculate_portfolio_performance(
        pd.DataFrame({"portfolio": returns}),
        weights={"portfolio": 1.0},
        profile=name,
    )


def _save(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_DIR / (stem + ".pdf"), bbox_inches="tight")
    figure.savefig(FIGURE_DIR / (stem + ".png"), bbox_inches="tight", dpi=220)
    plt.close(figure)


def _historical_test(panel: pd.DataFrame) -> None:
    rolling_36 = backtest_rolling_cvar_policies(panel, lookback_months=36)["Moderate"]
    fixed_36 = backtest_fixed_cvar_policies(panel, lookback_months=36)["Moderate"]
    benchmark_36 = backtest_fixed_weight_benchmark(
        panel,
        weights_by_asset=MODERATE_BENCHMARK_WEIGHTS,
        lookback_months=36,
        name="Moderate benchmark",
    )
    rolling_48 = backtest_rolling_cvar_policies(panel, lookback_months=48)["Moderate"]
    entries = (
        ("36m rolling baseline", _performance(rolling_36.monthly_returns, "36m rolling"), 59),
        ("36m frozen policy", _performance(fixed_36.monthly_returns, "36m frozen"), 59),
        ("36m 50/50 benchmark", _performance(benchmark_36.monthly_returns, "36m benchmark"), 59),
        ("48m rolling sensitivity", _performance(rolling_48.monthly_returns, "48m rolling"), 47),
    )
    rows = "\n".join(
        f"{name} & {item.annualized_return:.2%} & {item.annualized_volatility:.2%} & {item.sharpe_ratio:.2f} & {item.maximum_drawdown:.2%} & {item.expected_shortfall_95:.2%} & {months} \\\\"
        for name, item, months in entries
    )
    _write(
        "gbi_historical_robustness.tex",
        "\\begin{table}[htbp]\n\\centering\n\\footnotesize\n"
        "\\caption{Test 1: Moderate-policy historical walk-forward performance and robustness.}\n"
        "\\label{tab:gbi-historical-robustness}\n\\begin{tabular}{lrrrrrr}\n\\toprule\n"
        "Strategy & Ann. return & Ann. vol. & Sharpe & Max drawdown & ES (95\\%) & Months \\\\\n\\midrule\n"
        + rows
        + "\n\\bottomrule\n\\end{tabular}\n\\vspace{2pt}\n\\begin{minipage}{0.96\\linewidth}\n\\footnotesize\n"
        "Notes: The 36-month rolling policy is the baseline. The first three rows use the same 59 out-of-sample months, quarterly rebalancing and 10bp one-way transaction costs. The 48-month row is a window-length sensitivity with 47 out-of-sample months. Sharpe assumes a zero risk-free rate.\n\\end{minipage}\n\\end{table}\n",
    )


def _client_test(panel: pd.DataFrame) -> None:
    scenarios = (
        ("Base client", "Moderate", 750_000.0, 25_000.0, 55_000.0),
        ("Conservative risk", "Conservative", 750_000.0, 25_000.0, 55_000.0),
        ("Assets -20\\%", "Moderate", 600_000.0, 25_000.0, 55_000.0),
        ("Contribution \\$15k", "Moderate", 750_000.0, 15_000.0, 55_000.0),
        ("Essential expenses +\\$15k", "Moderate", 750_000.0, 25_000.0, 70_000.0),
    )
    policies = load_predefined_cvar_policies()
    records = []
    for name, risk, assets, contribution, essential in scenarios:
        weights = policies[risk].weights
        returns = panel.loc[:, list(weights)].dot(np.asarray(list(weights.values())))
        state = build_goal_assessment_state(
            profile={
                "Goal_Name": "Retirement", "Target_Amount": 1_150_000.0,
                "Current_Amount": assets, "Years_To_Goal": 5,
                "Annual_Contribution": contribution, "Annual_Return_Percent": 0.0,
            },
            portfolio_monthly_returns=returns.to_numpy(),
        )
        plan = build_client_financial_plan(
            risk_profile=risk, confirmed_plan_assets=assets, current_age=60,
            retirement_age=65, income_start_age=65, annual_contribution=contribution,
            annual_goals={"essential": essential, "important": 10_000.0, "aspirational": 5_000.0},
            annual_income={"social_security": 26_000.0, "pension": 12_000.0, "annuity_existing": 0.0, "other": 0.0},
            horizon_periods=8,
        )
        assessment = state["Assessment"]
        records.append((name, risk, assets, contribution, plan.annual_retirement_gap, assessment))
    rows = "\n".join(
        (
            "{} & {} & \\$" + "{:,.0f} & \\$" + "{:,.0f} & \\$" + "{:,.0f} & \\$"
            + "{:,.0f} & {:.1%} & {:.1%} \\\\"
        ).format(
            name, risk, assets, contribution, gap, assessment.projected_amount,
            assessment.funding_ratio, assessment.success_probability,
        )
        for name, risk, assets, contribution, gap, assessment in records
    )
    _write(
        "gbi_client_sensitivity.tex",
        "\\begin{table}[htbp]\n\\centering\n\\scriptsize\n"
        "\\caption{Test 2: client-input sensitivity for the illustrative retirement plan.}\n"
        "\\label{tab:gbi-client-sensitivity}\n\\begin{tabular}{llrrrrrr}\n\\toprule\n"
        "Scenario & Risk & Assets & Contribution & Retirement gap & Projected wealth & Funding & Success \\\\\n\\midrule\n"
        + rows
        + "\n\\bottomrule\n\\end{tabular}\n\\vspace{2pt}\n\\begin{minipage}{0.97\\linewidth}\n\\scriptsize\n"
        "Notes: All scenarios retain a five-year horizon and a \\$1.15 million target. The expense scenario changes the staged retirement cash-flow gap; the current terminal-wealth bootstrap does not yet deduct retirement spending, so its success probability remains unchanged.\n\\end{minipage}\n\\end{table}\n",
    )
    figure, axis = plt.subplots(figsize=(6.6, 3.5))
    labels = ("Base", "Conservative", "Assets -20%", "Contribution $15k")
    values = [assessment.success_probability * 100 for _, _, _, _, _, assessment in records[:4]]
    bars = axis.bar(labels, values, color=("white", "0.75", "0.50", "0.25"), edgecolor="black")
    for bar, value, hatch in zip(bars, values, ("//", "\\\\", "..", "xx"), strict=True):
        bar.set_hatch(hatch)
        axis.text(bar.get_x() + bar.get_width() / 2, value + 1.2, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)
    axis.set(title="Test 2: goal success probability by client scenario", ylabel="Success probability (%)", ylim=(0, 105))
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    _save(figure, "gbi_client_sensitivity_success_probability")


def main() -> None:
    panel = load_monthly_market_panel(find_cleaned_data_dir(PROJECT_ROOT)).loc[
        "2018-06-01":"2026-05-31", list(SIX_ETF_ASSETS),
    ]
    _historical_test(panel)
    _client_test(panel)
    _write(
        "gbi_part2_testing.tex",
        """\\subsection{Model tests}
\\label{sec:gbi-tests}

\\subsubsection{Test 1: Historical walk-forward performance and robustness}
The 36-month trailing-window rolling CVaR policy is the research baseline. It is evaluated on realized monthly returns after quarterly re-optimization with 10bp one-way transaction costs. A fixed Moderate 50/50 benchmark and a frozen policy use the same out-of-sample months. A 48-month rolling result is included only as a window-length sensitivity.

\\input{part2_testing/gbi_historical_robustness.tex}

\\subsubsection{Test 2: Client-input sensitivity}
This test checks whether personalization inputs create observable changes in the policy recommendation or financial-plan result. The risk scenario changes the selected policy; asset and contribution scenarios change the terminal-wealth assessment; the expense scenario changes the retirement cash-flow gap and priority schedule.

\\input{part2_testing/gbi_client_sensitivity.tex}

\\begin{figure}[htbp]
  \\centering
  \\includegraphics[width=0.82\\linewidth]{part2_testing/figures/gbi_client_sensitivity_success_probability.pdf}
  \\caption{Historical-bootstrap goal success probability under selected client-input scenarios.}
  \\label{fig:gbi-client-sensitivity}
\\end{figure}
""",
    )
    print(f"Wrote Part 2 testing artifacts to {REPORT_DIR}")


if __name__ == "__main__":
    main()
