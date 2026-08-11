"""Create black-and-white, Overleaf-ready figures for the GBI research baseline."""

from __future__ import annotations

import sys

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.goal_based_investing.portfolio_performance import (  # noqa: E402
    calculate_portfolio_performance,
    performance_comparison_to_latex,
)
from src.models.goal_based_investing.rolling_policy_backtest import (  # noqa: E402
    MODERATE_BENCHMARK_WEIGHTS,
    SIX_ETF_ASSETS,
    backtest_fixed_weight_benchmark,
    backtest_rolling_cvar_policies,
)
from src.models.goal_based_investing.scenario_tree_goal_based_investing import (  # noqa: E402
    find_cleaned_data_dir,
    load_monthly_market_panel,
)


OUTPUT_DIR = PROJECT_ROOT / "src" / "models" / "goal_based_investing" / "reports" / "research_figures"
PROFILE = "Moderate"
LOOKBACK_MONTHS = 36


def _save(figure: plt.Figure, stem: str) -> None:
    """Save both publication PDF and convenient PNG preview."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_DIR / f"{stem}.pdf", bbox_inches="tight")
    figure.savefig(OUTPUT_DIR / f"{stem}.png", bbox_inches="tight", dpi=220)
    plt.close(figure)


def main() -> None:
    """Create three concise figures from the 36-month rolling baseline."""
    plt.rcParams.update({"font.size": 10, "axes.labelsize": 10, "axes.titlesize": 11})
    panel = load_monthly_market_panel(find_cleaned_data_dir(PROJECT_ROOT)).loc[
        "2018-06-01":"2026-05-31",
        list(SIX_ETF_ASSETS),
    ]
    rolling = backtest_rolling_cvar_policies(panel, lookback_months=LOOKBACK_MONTHS)[PROFILE]
    benchmark = backtest_fixed_weight_benchmark(
        panel,
        weights_by_asset=MODERATE_BENCHMARK_WEIGHTS,
        lookback_months=LOOKBACK_MONTHS,
        name="Moderate 50/50 benchmark",
    )

    wealth = 100 * (1 + np.column_stack((benchmark.monthly_returns, rolling.monthly_returns))).cumprod(
        axis=0,
    )
    figure, axis = plt.subplots(figsize=(6.6, 3.5))
    axis.plot(
        benchmark.monthly_returns.index,
        wealth[:, 0],
        color="0.35",
        linestyle="--",
        linewidth=1.8,
        label="Moderate 50/50 benchmark",
    )
    axis.plot(
        rolling.monthly_returns.index,
        wealth[:, 1],
        color="0.0",
        linewidth=2.0,
        label="36-month rolling policy",
    )
    axis.set(
        title="Moderate policy: normalized out-of-sample wealth",
        ylabel="Portfolio value (base = 100)",
        xlabel="Month",
    )
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    axis.legend(frameon=False, loc="upper left")
    _save(figure, "gbi_moderate_36m_normalized_wealth")

    figure, axis = plt.subplots(figsize=(6.6, 3.5))
    bins = np.histogram_bin_edges(
        np.concatenate((benchmark.monthly_returns, rolling.monthly_returns)), bins=10,
    )
    axis.hist(
        benchmark.monthly_returns * 100,
        bins=bins * 100,
        color="0.75",
        edgecolor="0.2",
        hatch="\\\\",
        alpha=0.8,
        label="Moderate 50/50 benchmark",
    )
    axis.hist(
        rolling.monthly_returns * 100,
        bins=bins * 100,
        color="white",
        edgecolor="black",
        hatch="//",
        alpha=0.95,
        label="36-month rolling policy",
    )
    axis.set(
        title="Moderate policy: monthly return distribution",
        xlabel="Monthly return (%)",
        ylabel="Frequency",
    )
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    axis.legend(frameon=False)
    _save(figure, "gbi_moderate_36m_return_distribution")

    figure, axis = plt.subplots(figsize=(6.6, 3.8))
    greys = ("1.0", "0.85", "0.68", "0.50", "0.32", "0.12")
    weights = rolling.target_weights.loc[:, SIX_ETF_ASSETS]
    axis.stackplot(
        weights.index,
        weights.to_numpy().T * 100,
        labels=SIX_ETF_ASSETS,
        colors=greys,
        edgecolor="0.2",
        linewidth=0.4,
    )
    axis.set(
        title="Moderate policy: quarterly rolling target weights",
        ylabel="Target weight (%)",
        xlabel="Rebalance month",
        ylim=(0, 100),
    )
    axis.grid(axis="y", color="0.85", linewidth=0.7)
    axis.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.19))
    _save(figure, "gbi_moderate_36m_rolling_weights")

    rolling_performance = calculate_portfolio_performance(
        pd.DataFrame({"rolling": rolling.monthly_returns}),
        weights={"rolling": 1.0},
        profile="36-month rolling policy",
    )
    benchmark_performance = calculate_portfolio_performance(
        pd.DataFrame({"benchmark": benchmark.monthly_returns}),
        weights={"benchmark": 1.0},
        profile="Moderate 50/50 benchmark",
    )
    (OUTPUT_DIR / "gbi_moderate_36m_performance_comparison.tex").write_text(
        performance_comparison_to_latex(
            portfolio=rolling_performance,
            benchmark=benchmark_performance,
            caption="Moderate 36-month rolling policy versus a risk-compatible benchmark.",
            label="tab:gbi-moderate-rolling-benchmark",
        ),
        encoding="utf-8",
    )
    latex = r"""% Requires \usepackage{graphicx}
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\linewidth]{research_figures/gbi_moderate_36m_normalized_wealth.pdf}
  \caption{Normalized out-of-sample wealth for the Moderate policy and risk-compatible benchmark. The rolling policy uses only the previous 36 months at each quarterly rebalance.}
  \label{fig:gbi-moderate-wealth}
\end{figure}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\linewidth]{research_figures/gbi_moderate_36m_return_distribution.pdf}
  \caption{Distribution of realized monthly out-of-sample returns for the Moderate policy and benchmark.}
  \label{fig:gbi-moderate-distribution}
\end{figure}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\linewidth]{research_figures/gbi_moderate_36m_rolling_weights.pdf}
  \caption{Quarterly target-weight evolution of the Moderate 36-month rolling policy.}
  \label{fig:gbi-moderate-weights}
\end{figure}
"""
    (OUTPUT_DIR / "gbi_research_figures.tex").write_text(latex, encoding="utf-8")
    print(f"Wrote figures and LaTex snippet to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
