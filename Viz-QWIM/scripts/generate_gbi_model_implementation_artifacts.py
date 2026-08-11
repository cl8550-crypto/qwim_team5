"""Generate Overleaf-ready Part 1 artifacts for the GBI model implementation."""

from __future__ import annotations

import sys

from itertools import pairwise
from pathlib import Path
from shutil import copyfile

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.shiny_tab_goal_based_investing._goal_based_investing_state import (  # noqa: E402
    build_goal_assessment_state,
)
from src.models.goal_based_investing import load_predefined_cvar_policies  # noqa: E402
from src.models.goal_based_investing.risk_portfolio_policy import (  # noqa: E402
    DEFAULT_RISK_PROFILE_BANDS,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (  # noqa: E402
    find_cleaned_data_dir,
    load_monthly_market_panel,
)


REPORT_DIR = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "model_implementation"
FIGURE_DIR = REPORT_DIR / "figures"


def _write(name: str, contents: str) -> None:
    """Write one text artifact beneath the model-implementation report folder."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / name).write_text(contents, encoding="utf-8")


def _save(figure: plt.Figure, stem: str) -> None:
    """Save a black-and-white vector figure plus PNG preview."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight")
    figure.savefig(FIGURE_DIR / f"{stem}.png", bbox_inches="tight", dpi=220)
    plt.close(figure)


def _generate_workflow_figure() -> None:
    """Draw the client-to-goal-assessment workflow without dashboard screenshots."""
    figure, axis = plt.subplots(figsize=(10.4, 2.8))
    axis.set_axis_off()
    labels = (
        "Client inputs\nrisk, assets, age,\nincome and expenses",
        "Risk-profile policy\nsix ETFs, long-only,\nCVaR constraints",
        "Client plan\nasset allocation,\nhorizon and cash flows",
        "Goal assessment\nterminal wealth,\nfunding and success",
    )
    positions = (0.02, 0.27, 0.52, 0.77)
    for x, label in zip(positions, labels, strict=True):
        axis.add_patch(
            FancyBboxPatch(
                (x, 0.31),
                0.20,
                0.42,
                boxstyle="round,pad=0.015",
                linewidth=1.2,
                edgecolor="black",
                facecolor="0.93",
                transform=axis.transAxes,
            ),
        )
        axis.text(x + 0.10, 0.52, label, ha="center", va="center", fontsize=11, transform=axis.transAxes)
    for current, following in pairwise(positions):
        axis.annotate(
            "",
            xy=(following - 0.01, 0.52),
            xytext=(current + 0.20, 0.52),
            xycoords=axis.transAxes,
            arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "black"},
        )
    _save(figure, "gbi_model_workflow")


def _generate_client_artifacts() -> None:
    """Generate the demo-client table and goal-assessment figures."""
    panel = load_monthly_market_panel(find_cleaned_data_dir(PROJECT_ROOT)).loc[
        "2018-06-01":"2026-05-31",
        ["BIL", "XLK", "XLP", "AGG", "TIP", "GLD"],
    ]
    policy = load_predefined_cvar_policies()["Moderate"]
    monthly_returns = panel.loc[:, list(policy.weights)].dot(np.asarray(list(policy.weights.values())))
    profile = {
        "Goal_Name": "Retirement",
        "Target_Amount": 1_150_000.0,
        "Current_Amount": 750_000.0,
        "Years_To_Goal": 5,
        "Annual_Contribution": 25_000.0,
        "Annual_Return_Percent": 0.0,
    }
    state = build_goal_assessment_state(profile=profile, portfolio_monthly_returns=monthly_returns.to_numpy())
    assessment = state["Assessment"]
    _write(
        "gbi_demo_client_goal_assessment.tex",
        rf"""\begin{{table}}[htbp]
\centering
\footnotesize
\caption{{Goal assessment for the illustrative Moderate client.}}
\label{{tab:gbi-demo-goal-assessment}}
\begin{{tabular}}{{lr}}
\toprule
Metric & Value \\
\midrule
Confirmed plan assets & \$750,000 \\
Target retirement wealth & \$1,150,000 \\
Years to retirement & 5 \\
Annual contribution & \$25,000 \\
Selected risk profile & Moderate \\
Mean projected terminal wealth & \${assessment.projected_amount:,.0f} \\
Funding ratio & {assessment.funding_ratio:.1%} \\
Goal success probability & {assessment.success_probability:.1%} \\
Shortfall / surplus & \${assessment.shortfall_amount:,.0f} shortfall \\
\bottomrule
\end{{tabular}}
\vspace{{2pt}}
\begin{{minipage}}{{0.92\linewidth}}
\footnotesize
Notes: The illustrative client has \$750,000 of confirmed plan assets, a five-year horizon and \$25,000 annual contributions. Terminal wealth is evaluated over 2,000 historical-bootstrap monthly-return paths of the selected fixed Moderate policy; it is a scenario analysis, not a forecast.
\end{{minipage}}
\end{{table}}
""",
    )
    figure, axis = plt.subplots(figsize=(6.6, 3.5))
    axis.plot(state["Years"], state["Annual_Progress"], color="black", linewidth=2.1, label="Projected value")
    axis.axhline(assessment.target_amount, color="0.35", linestyle="--", linewidth=1.6, label="Target")
    axis.set(title="Illustrative Moderate client: goal progress", xlabel="Years from today", ylabel="Portfolio value ($)")
    axis.ticklabel_format(axis="y", style="plain")
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    axis.legend(frameon=False)
    _save(figure, "gbi_demo_client_goal_progress")

    rng = np.random.default_rng(17)
    samples = rng.choice(monthly_returns.to_numpy(), size=(2_000, 60), replace=True)
    terminal_values = np.full(2_000, 750_000.0)
    for month in range(60):
        terminal_values = terminal_values * (1 + samples[:, month]) + 25_000 / 12
    figure, axis = plt.subplots(figsize=(6.6, 3.5))
    axis.hist(terminal_values / 1_000_000, bins=24, color="white", edgecolor="black", hatch="//")
    axis.axvline(1.15, color="0.25", linestyle="--", linewidth=1.7, label="Target")
    axis.set(title="Illustrative Moderate client: terminal wealth scenarios", xlabel="Terminal wealth ($ millions)", ylabel="Frequency")
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    axis.legend(frameon=False)
    _save(figure, "gbi_demo_client_terminal_distribution")


def main() -> None:
    """Generate the tables, figures, and assembled Part 1 implementation section."""
    rolling_table = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "performance" / "gbi_rolling_policy_performance_36m.tex"
    if not rolling_table.is_file():
        raise FileNotFoundError("Generate the 36-month rolling-policy table before the Part 1 artifacts")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    copyfile(rolling_table, REPORT_DIR / rolling_table.name)
    _write(
        "gbi_client_input_mapping.tex",
        r"""\begin{table}[htbp]
\centering
\footnotesize
\caption{Client-data fields used in Goal-Based Investing Version 1.}
\label{tab:gbi-client-inputs}
\begin{tabular}{lp{0.55\linewidth}}
\toprule
Client field & Model use \\
\midrule
Risk tolerance & Selects one of five predefined risk-profile policies and its equity-risk band. \\
Taxable, tax-deferred and tax-free assets & Reported assets; the client confirms the amount allocated to the plan, which scales ETF dollar allocations. \\
Current age and retirement age & Define the retirement horizon and staged planning schedule. \\
Annual contribution & Pre-retirement contribution cash flow. \\
Social Security, pension, annuity and other income & Retirement-stage guaranteed-income cash flows, separate from invested wealth. \\
Essential, important and aspirational expenses & Priority spending schedules with descending shortfall protection. \\
\bottomrule
\end{tabular}
\end{table}
""",
    )
    _write(
        "gbi_etf_universe.tex",
        r"""\begin{table}[htbp]
\centering
\footnotesize
\caption{Six-ETF strategic universe used by the GBI policies.}
\label{tab:gbi-etf-universe}
\begin{tabular}{lll}
\toprule
ETF & Asset role & Purpose in the policy \\
\midrule
BIL & Cash proxy & Liquidity and low-volatility allocation. \\
XLK & Equity sector & Technology equity exposure. \\
XLP & Equity sector & Defensive consumer-staples equity exposure. \\
AGG & Aggregate bonds & Core nominal bond exposure. \\
TIP & Inflation-linked bonds & Inflation-sensitive defensive exposure. \\
GLD & Gold & Diversifying real-asset exposure. \\
\bottomrule
\end{tabular}
\end{table}
""",
    )
    band_rows = "\n".join(
        f"{band.profile} & {band.minimum_equity_weight:.0%} & {band.maximum_equity_weight:.0%} \\\\"
        for band in DEFAULT_RISK_PROFILE_BANDS
    )
    _write(
        "gbi_risk_bands.tex",
        "\\begin{table}[htbp]\n\\centering\n\\footnotesize\n"
        "\\caption{Risk-profile equity-allocation bands.}\n\\label{tab:gbi-risk-bands}\n"
        "\\begin{tabular}{lrr}\n\\toprule\nRisk profile & Minimum equity & Maximum equity \\\\\n\\midrule\n"
        + band_rows
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n",
    )
    _generate_workflow_figure()
    _generate_client_artifacts()
    _write(
        "gbi_model_implementation.tex",
        r"""\subsection{Goal-Based Investing model implementation}
\label{sec:gbi-model}

QWIM Version 1 is an explainable, client-driven retirement-planning workflow. It does not claim to forecast market returns or to provide online portfolio optimization. Instead, a client risk-tolerance category selects a predefined six-ETF policy, while confirmed plan assets translate that policy into dollar allocations. Figure~\ref{fig:gbi-workflow} summarizes the implementation pipeline.

\input{model_implementation/gbi_client_input_mapping.tex}
\input{model_implementation/gbi_etf_universe.tex}
\input{model_implementation/gbi_risk_bands.tex}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.98\linewidth]{model_implementation/figures/gbi_model_workflow.pdf}
  \caption{Client-data-to-goal-assessment workflow in GBI Version 1.}
  \label{fig:gbi-workflow}
\end{figure}

\subsubsection{Policy construction and historical evaluation}
Each policy is long-only and fully invested. The offline CVaR construction minimizes historical 95\% expected shortfall subject to the client risk-profile equity band and ETF caps. For research evaluation, the rolling baseline re-estimates policy weights from the preceding 36 monthly observations and applies them over the next quarter without future information. The evaluation includes 10bp one-way trading costs at quarterly rebalances. The Dashboard itself retains a versioned static policy so that it does not optimize separately for each client.

\input{model_implementation/gbi_rolling_policy_performance_36m.tex}

\paragraph{Interpretation and limitations.}
The rolling results are historical out-of-sample statistics, not forecasts or investment guarantees. The 95\% expected-shortfall estimate is based on a limited number of extreme monthly observations, and the 36-month window is a transparent research baseline rather than a claim of universal superiority. Client-level success probabilities are historical-bootstrap scenario frequencies and should be interpreted together with funding ratio and shortfall.

\subsubsection{Client goal assessment}
The selected policy is combined with confirmed plan assets, retirement horizon, annual contributions, income and priority spending. Goal success is evaluated over 2,000 historical-bootstrap terminal-wealth scenarios. The illustrative client results are reported in Table~\ref{tab:gbi-demo-goal-assessment}.

\input{model_implementation/gbi_demo_client_goal_assessment.tex}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\linewidth]{model_implementation/figures/gbi_demo_client_goal_progress.pdf}
  \caption{Projected goal-progress path for the illustrative Moderate client.}
  \label{fig:gbi-demo-progress}
\end{figure}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\linewidth]{model_implementation/figures/gbi_demo_client_terminal_distribution.pdf}
  \caption{Historical-bootstrap terminal-wealth distribution for the illustrative Moderate client.}
  \label{fig:gbi-demo-terminal}
\end{figure}
""",
    )
    print(f"Wrote Overleaf-ready Part 1 artifacts to {REPORT_DIR}")


if __name__ == "__main__":
    main()
