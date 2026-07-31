"""Reproducible performance reporting for the fixed GBI risk policies.

The Dashboard uses the policies as planning inputs.  This module evaluates
their *historical monthly, monthly-rebalanced* performance for a presentation
or report.  It is intentionally separate from the goal-success bootstrap so
that a historical policy statistic is never presented as a client forecast.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .risk_portfolio_policy import Predefined_Portfolio_Policy


PERIODS_PER_YEAR = 12


@dataclass(frozen=True, slots=True)
class Portfolio_Performance:  # noqa: N801
    """Historical monthly-rebalanced performance statistics for one policy."""

    profile: str
    observations: int
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    maximum_drawdown: float
    expected_shortfall_95: float


def calculate_portfolio_performance(
    monthly_asset_returns: pd.DataFrame,
    *,
    weights: Mapping[str, float],
    risk_free_monthly_returns: pd.Series | None = None,
    profile: str = "Portfolio",
    periods_per_year: int = PERIODS_PER_YEAR,
) -> Portfolio_Performance:
    """Calculate standard statistics from a monthly-rebalanced return series.

    Annualized return is CAGR.  Annualized volatility and Sharpe ratio use the
    sample standard deviation of monthly returns and ``sqrt(12)`` scaling.
    When supplied, the risk-free series is subtracted month-by-month before
    calculating Sharpe; GBI uses the BIL monthly return series for this.
    """
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be positive")
    if not weights:
        raise ValueError("weights must not be empty")
    unknown_assets = set(weights).difference(monthly_asset_returns.columns)
    if unknown_assets:
        raise ValueError(f"weights contain assets absent from returns: {sorted(unknown_assets)}")
    weight_values = np.asarray(list(weights.values()), dtype=float)
    if not np.isfinite(weight_values).all() or (weight_values < 0).any() or not np.isclose(weight_values.sum(), 1.0):
        raise ValueError("weights must be finite, long-only, and sum to one")

    portfolio_returns = monthly_asset_returns.loc[:, list(weights)].astype(float).dropna().dot(pd.Series(weights))
    if len(portfolio_returns) < 2 or not np.isfinite(portfolio_returns.to_numpy()).all() or (portfolio_returns <= -1).any():
        raise ValueError("monthly_asset_returns requires at least two finite returns greater than -100%")
    if risk_free_monthly_returns is None:
        excess_returns = portfolio_returns
    else:
        aligned = pd.concat((portfolio_returns.rename("portfolio"), risk_free_monthly_returns.rename("risk_free")), axis=1).dropna()
        if len(aligned) < 2 or not np.isfinite(aligned.to_numpy()).all():
            raise ValueError("risk_free_monthly_returns must align to at least two finite portfolio observations")
        portfolio_returns = aligned["portfolio"]
        excess_returns = aligned["portfolio"] - aligned["risk_free"]

    cumulative_wealth = (1.0 + portfolio_returns).cumprod()
    annualized_return = float(cumulative_wealth.iloc[-1] ** (periods_per_year / len(portfolio_returns)) - 1.0)
    monthly_volatility = float(portfolio_returns.std(ddof=1))
    annualized_volatility = monthly_volatility * np.sqrt(periods_per_year)
    sharpe_ratio = (
        float(excess_returns.mean() / excess_returns.std(ddof=1) * np.sqrt(periods_per_year))
        if float(excess_returns.std(ddof=1)) > 0
        else float("nan")
    )
    drawdowns = cumulative_wealth / cumulative_wealth.cummax() - 1.0
    expected_shortfall_95 = _historical_expected_shortfall(portfolio_returns, confidence_level=0.95)
    return Portfolio_Performance(
        profile=profile,
        observations=len(portfolio_returns),
        annualized_return=annualized_return,
        annualized_volatility=float(annualized_volatility),
        sharpe_ratio=sharpe_ratio,
        maximum_drawdown=float(drawdowns.min()),
        expected_shortfall_95=expected_shortfall_95,
    )


def build_policy_performance_table(
    monthly_asset_returns: pd.DataFrame,
    *,
    policies: Mapping[str, Predefined_Portfolio_Policy],
    risk_free_asset: str = "BIL",
) -> pd.DataFrame:
    """Return one comparable performance row for every stored GBI policy."""
    if risk_free_asset not in monthly_asset_returns:
        raise ValueError(f"risk_free_asset {risk_free_asset!r} is absent from monthly_asset_returns")
    rows = [
        calculate_portfolio_performance(
            monthly_asset_returns,
            weights=policy.weights,
            risk_free_monthly_returns=monthly_asset_returns[risk_free_asset],
            profile=profile,
        )
        for profile, policy in policies.items()
    ]
    return pd.DataFrame(
        {
            "Risk profile": [row.profile for row in rows],
            "Annualized return": [row.annualized_return for row in rows],
            "Annualized volatility": [row.annualized_volatility for row in rows],
            "Sharpe ratio": [row.sharpe_ratio for row in rows],
            "Maximum drawdown": [row.maximum_drawdown for row in rows],
            "Historical ES (95%)": [row.expected_shortfall_95 for row in rows],
            "Monthly observations": [row.observations for row in rows],
        },
    )


def performance_table_to_latex(
    table: pd.DataFrame,
    *,
    caption: str,
    label: str,
    notes: str | None = None,
) -> str:
    """Format a performance table as a copy-ready ``booktabs`` LaTex table."""
    required_columns = {
        "Risk profile", "Annualized return", "Annualized volatility", "Sharpe ratio",
        "Maximum drawdown", "Historical ES (95%)", "Monthly observations",
    }
    if not required_columns.issubset(table.columns):
        raise ValueError("table is not a GBI policy performance table")
    display = table.loc[:, [
        "Risk profile", "Annualized return", "Annualized volatility", "Sharpe ratio",
        "Maximum drawdown", "Historical ES (95%)", "Monthly observations",
    ]].copy()
    for column in ("Annualized return", "Annualized volatility", "Maximum drawdown", "Historical ES (95%)"):
        display[column] = display[column].map(lambda value: f"{value:.2%}")
    display["Sharpe ratio"] = display["Sharpe ratio"].map(lambda value: "--" if not np.isfinite(value) else f"{value:.2f}")
    display["Monthly observations"] = display["Monthly observations"].astype(int)
    display.columns = ["Risk profile", "Annual return", "Annual vol.", "Sharpe", "Max drawdown", "ES (95%)", "Months"]
    body = display.to_latex(index=False, escape=True, column_format="lrrrrrr")
    default_notes = (
        "Monthly-rebalanced historical performance. Annual return is CAGR; annual volatility and Sharpe use monthly data scaled by $\\sqrt{12}$. Sharpe uses BIL as the monthly risk-free proxy. ES is historical 95\\% expected shortfall. These are historical policy statistics, not return forecasts."
    )
    return (
        "\\begin{table}[htbp]\n\\centering\n\\footnotesize\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        f"{body}"
        "\\vspace{2pt}\n"
        "\\begin{minipage}{0.96\\linewidth}\n\\footnotesize\n"
        f"Notes: {notes or default_notes}\n"
        "\\end{minipage}\n\\end{table}\n"
    )


def write_performance_latex_table(
    table: pd.DataFrame,
    destination: str | Path,
    *,
    caption: str,
    label: str,
    notes: str | None = None,
) -> Path:
    """Write the copy-ready LaTex table and return its location."""
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        performance_table_to_latex(table, caption=caption, label=label, notes=notes),
        encoding="utf-8",
    )
    return output_path


def performance_comparison_to_latex(
    *,
    portfolio: Portfolio_Performance,
    benchmark: Portfolio_Performance,
    caption: str,
    label: str,
) -> str:
    """Render a compact portfolio-versus-benchmark comparison for Overleaf."""
    percent_metrics = (
        ("Annualized return", portfolio.annualized_return, benchmark.annualized_return),
        ("Annualized volatility", portfolio.annualized_volatility, benchmark.annualized_volatility),
        ("Maximum drawdown", portfolio.maximum_drawdown, benchmark.maximum_drawdown),
        ("Historical ES (95\\%)", portfolio.expected_shortfall_95, benchmark.expected_shortfall_95),
    )
    rows = [
        f"{metric} & {value:.2%} & {reference:.2%} & {value - reference:+.2%} \\\\"
        for metric, value, reference in percent_metrics
    ]
    rows.insert(
        2,
        f"Sharpe ratio & {portfolio.sharpe_ratio:.2f} & {benchmark.sharpe_ratio:.2f} & "
        f"{portfolio.sharpe_ratio - benchmark.sharpe_ratio:+.2f} \\\\",
    )
    return (
        "\\begin{table}[htbp]\n\\centering\n\\footnotesize\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        "\\begin{tabular}{lrrr}\n\\toprule\n"
        "Metric & Rolling policy & Benchmark & Difference \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
        "\\vspace{2pt}\n\\begin{minipage}{0.96\\linewidth}\n\\footnotesize\n"
        "Notes: Monthly out-of-sample returns after a 36-month estimation period. Both portfolios rebalance quarterly with 10bp one-way transaction costs. Sharpe assumes a zero risk-free rate. For return and Sharpe, a positive difference favors the rolling policy; for volatility and ES, a negative difference favors it; for maximum drawdown, a positive difference means a smaller loss.\n"
        "\\end{minipage}\n\\end{table}\n"
    )


def _historical_expected_shortfall(returns: pd.Series, *, confidence_level: float) -> float:
    """Return the non-negative mean loss in the worst historical tail."""
    losses = np.sort(-returns.to_numpy(dtype=float))
    observations = max(1, int(np.ceil((1.0 - confidence_level) * len(losses))))
    return float(max(0.0, losses[-observations:].mean()))
