"""Goal Parity subtab: Overview & Guide (landing page).

Static, client-facing introduction shown as the first Goal Parity subtab:
why the goal-based approach can hold an edge over a conventional benchmark
across market regimes, and a step-by-step guide through the four pipeline
subtabs so users work them in the intended order.

Layout: hero header with the four goal chips, a card grid for the five
advantages, a numbered vertical stepper for the usage guide, and a warning
callout for common mistakes. All styling is scoped under ``.gpg-`` classes
so it cannot leak into other tabs.
"""

from __future__ import annotations

from typing import Any

from shiny import module, ui

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


# --- Content -----------------------------------------------------------------

_GOAL_CHIPS: list[tuple[str, str, str]] = [
    ("Liquidity", "Cash you can reach quickly", "#2563eb"),
    ("Income", "Regular, dependable payments", "#0f766e"),
    ("Preservation", "Protecting what you've saved", "#b45309"),
    ("Growth", "Building wealth long term", "#b91c1c"),
]

_ADVANTAGES: list[tuple[str, str]] = [
    (
        "Diversified across goals, not just assets",
        "Explicit *Liquidity*, *Income*, *Preservation*, and *Growth* sleeves "
        "mean part of the portfolio is designed for every market environment. "
        "A 60/40 benchmark has no explicit defense in regimes where stocks and "
        "bonds fall together (e.g. the 2022 inflation shock) — here, the "
        "defensive sleeves are sized in advance, not improvised after the "
        "drawdown.",
    ),
    (
        "Regime-aware risk inputs",
        "Volatilities are EWMA-weighted — recent observations count more — and "
        "adjusted for (Winsorized) downside skew. When the market shifts into "
        "a stressed regime, risk estimates adapt within weeks instead of being "
        "diluted by decades of calm history.",
    ),
    (
        "Assets classified by behavior, not by label",
        "Each asset's goal scores come from option-style payoff triggers "
        "(including a first-passage probability of breaching the loss "
        "barrier), so an asset that looks like \"Growth\" in calm regimes but "
        "loses its Preservation power under stress is scored accordingly.",
    ),
    (
        "A personal loss barrier",
        "The investor's risk profile maps to a risk-aversion parameter η and "
        "a *substantial-loss* barrier b(η). The optimization explicitly "
        "controls the probability of crossing *your* barrier — bear-regime "
        "risk is managed against your own tolerance, not a one-size-fits-all "
        "volatility target.",
    ),
    (
        "Disciplined, cost-aware rebalancing",
        "Trades happen only when a goal gap exceeds the tolerance ε *and* the "
        "gap-reduction per unit transaction cost clears a threshold, within a "
        "turnover budget. During noisy regime transitions this avoids whipsaw "
        "over-trading while still realigning decisively when drift is real.",
    ),
]

_STEPS: list[tuple[str, str, str]] = [
    (
        "Investor Profile",
        "Tell the model who you are",
        """
- **If your advisor has filled in the Clients tab:** leave
  *"Use Clients tab inputs"* checked. Your time horizon and risk comfort
  level are read from there automatically — nothing else to do.
- **If not (or you want to experiment):** uncheck the box, then set three
  things in the sidebar:
  - *Risk profile* — how comfortable you are with ups and downs, from
    Conservative to Aggressive. When unsure, start with Moderate.
  - *Strategic horizon T* — how many years until you need the money
    (e.g. years until retirement). Use your real timeline; a too-short
    horizon makes the portfolio overly cautious.
  - *Rebalancing frequency τ* — how often the portfolio is reviewed.
    Semi-annual is the recommended default.
- **Before moving on, check two things** on the right:
  - The table shows your profile translated into model terms — most
    importantly the *loss tolerance*, the decline you could accept before
    changing course. If that number feels wrong, adjust the risk profile.
  - The *"Source:"* line confirms where inputs came from (Clients tab vs.
    manual). If it says Clients tab but that tab is empty or outdated,
    uncheck the box and enter values manually.
""",
    ),
    (
        "4×4 Asset Map",
        "Choose what the model can invest in",
        """
- Tick the boxes for the investments you want considered. Keeping the full
  default list selected is a good starting point.
- The map shows how each investment supports the four goals — one asset
  can serve several goals at once (e.g. part Income, part Preservation).
- **Keep the universe broad:** every goal needs at least a few supporting
  assets. If a later step flags a goal as *structurally scarce*, come back
  here and re-add tickers rather than fighting the optimizer.
""",
    ),
    (
        "Strategic Optimization",
        "Build your target portfolio",
        """
- Start with **Goal Parity Balanced** (the default): it aims for equal 25%
  support of all four goals. For most clients this is the recommended
  portfolio.
- Choose **Goal Tilted** only if you deliberately want to favor one goal
  (e.g. more Growth for a young saver, more Income near retirement):
  - Pick the goal to favor, then set the *tilt strength* slider — small
    tilts (10–30%) are usually enough.
  - A tilt shifts *priorities* between goals; it is **not** a "more
    return" dial. Pushing it to the maximum concentrates the portfolio
    and gives up diversification.
- **Read any warning banners before trusting the numbers:**
  - *Solver failure* — the shown weights are a best effort; confirm with
    your advisor before acting on them.
  - *Structurally scarce goal* — the chosen investments simply can't
    support that goal much further; fix it in Step 2, not here.
""",
    ),
    (
        "Tactical Rebalancing",
        "See how the portfolio stays on track",
        """
- This step is a **simulation**: it shows what would happen after markets
  move your portfolio away from its targets, and which trades the model
  would make to bring it back.
- Two controls: the *σ slider* sets how large the simulated market move
  is; the *seed* picks which random scenario you see.
- Read the results top to bottom:
  - The summary line: how many trades and how much of the portfolio
    turned over (the model caps this — it will never churn everything).
  - The bar chart: goal support *drifted → after rebalance → target*.
    After rebalancing, the bars should move back toward the target.
  - The trade table: each row is one sell/buy pair, ranked so the most
    goal-restoring, lowest-cost trades come first.
- **Different seeds give different trades — that is expected.** Each seed
  is a different market scenario, not a different answer to the same
  question.
""",
    ),
    (
        "Historical Backtest",
        "See how the model would have done",
        """
- This step replays history **without look-ahead**: the model is trained
  only on data before each date, its portfolio is held for one step, and
  the realized results accumulate — then repeat. What you see is how the
  strategy *would have* performed, next to a classic 60/40 benchmark.
- Four settings in the sidebar (the defaults are sensible — start there):
  - *Backtest date range* — which slice of history to replay.
  - *Training window* — how many years of past data the model learns
    from at each step. Keep it at 2.5 years or more; shorter windows
    make the risk estimates noisy and trigger a warning.
  - *Test window* — the horizon each fold's performance is measured
    over in the fold table.
  - *Step size* — how often the model re-trains and rebalances. Leave
    it equal to your review frequency τ unless you have a reason not to.
- Click **Run backtest** and read the results top to bottom:
  - The chart: growth of $1 for the model vs. the benchmark; dotted
    vertical lines mark each re-training date.
  - The metrics table: return, volatility, Sharpe ratio, and max
    drawdown side by side. Lower drawdown and volatility at a
    reasonable return is the model's goal — it is *not* trying to beat
    the benchmark's raw return.
  - The fold table: per-period results, so you can see *when* the model
    helped (stress periods) and when it lagged (strong bull runs).
- **A red message means the configuration is impossible** (e.g. the date
  range is too short for the training window) — shrink the training
  window or widen the dates.
""",
    ),
]

_MISTAKES: list[str] = [
    "Jumping straight to Optimization or Rebalancing — the results then "
    "reflect the *default* Moderate profile, not your client's.",
    "Leaving \"Use Clients tab inputs\" checked when the Clients tab is "
    "empty or stale — always check the \"Source:\" line in Step 1.",
    "Setting a horizon T shorter than the client's actual timeline, which "
    "understates how much Growth the plan can safely carry.",
    "Ignoring the solver-failure or scarce-goal warnings in Step 3 — they "
    "qualify every number shown downstream.",
    "Comparing rebalancing trades across different drift seeds and "
    "concluding the model is unstable — each seed is a different scenario.",
]


# --- Styling (scoped to this subtab via the .gpg- prefix) --------------------

_GUIDE_CSS = """
.gpg-hero {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 60%, #18bc9c 160%);
  color: #fff;
  border-radius: 12px;
  padding: 1.6rem 1.8rem 1.4rem;
  margin-bottom: 1.4rem;
}
.gpg-hero h3 { color: #fff; margin: 0 0 0.35rem; font-weight: 700; }
.gpg-hero p  { margin: 0 0 1rem; opacity: 0.85; max-width: 60rem; }
.gpg-chips { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.gpg-chip {
  background: rgba(255, 255, 255, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  padding: 0.3rem 0.9rem 0.3rem 0.7rem;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.gpg-chip .gpg-dot {
  width: 0.6rem; height: 0.6rem; border-radius: 50%; display: inline-block;
}
.gpg-chip small { opacity: 0.75; }

.gpg-section-title {
  font-size: 1.15rem; font-weight: 700; color: #2c3e50;
  margin: 1.6rem 0 0.9rem; display: flex; align-items: center; gap: 0.5rem;
}
.gpg-section-title::after {
  content: ""; flex: 1; height: 1px; background: #dee2e6;
}

.gpg-adv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 0.9rem;
}
.gpg-adv-card {
  background: #fff;
  border: 1px solid #e9ecef;
  border-top: 3px solid #18bc9c;
  border-radius: 10px;
  padding: 1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(44, 62, 80, 0.06);
}
.gpg-adv-card h5 {
  font-size: 0.98rem; font-weight: 700; color: #2c3e50;
  margin: 0 0 0.45rem;
}
.gpg-adv-card p { font-size: 0.88rem; color: #555f6b; margin: 0; }

.gpg-step { display: flex; gap: 1rem; }
.gpg-step-rail {
  display: flex; flex-direction: column; align-items: center; flex: 0 0 auto;
}
.gpg-step-num {
  width: 2.1rem; height: 2.1rem; border-radius: 50%;
  background: #2c3e50; color: #fff; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
}
.gpg-step-line { flex: 1; width: 2px; background: #dee2e6; margin: 0.3rem 0; }
.gpg-step:last-of-type .gpg-step-line { display: none; }
.gpg-step-body { flex: 1; padding-bottom: 1.4rem; min-width: 0; }
.gpg-step-card {
  background: #fff; border: 1px solid #e9ecef; border-radius: 10px;
  box-shadow: 0 1px 2px rgba(44, 62, 80, 0.06); overflow: hidden;
}
.gpg-step-head {
  padding: 0.75rem 1.1rem;
  background: #f8f9fa; border-bottom: 1px solid #e9ecef;
  display: flex; align-items: baseline; gap: 0.6rem; flex-wrap: wrap;
}
.gpg-step-head strong { color: #2c3e50; font-size: 1rem; }
.gpg-step-head em { color: #18bc9c; font-size: 0.85rem; font-style: normal; }
.gpg-step-content { padding: 0.9rem 1.1rem 0.2rem; font-size: 0.9rem; color: #495057; }
.gpg-step-content ul { padding-left: 1.15rem; margin-bottom: 0.7rem; }
.gpg-step-content li { margin-bottom: 0.35rem; }
.gpg-step-content li > ul { margin-top: 0.35rem; }

.gpg-mistakes {
  background: #fff8ec;
  border: 1px solid #f2d8a7; border-left: 4px solid #b45309;
  border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;
}
.gpg-mistakes h5 {
  color: #92400e; font-size: 0.98rem; font-weight: 700; margin: 0 0 0.6rem;
}
.gpg-mistakes ul { margin: 0; padding-left: 1.15rem; }
.gpg-mistakes li { font-size: 0.88rem; color: #6b4e16; margin-bottom: 0.35rem; }
"""


def _hero() -> Any:
    chips = [
        ui.span(
            ui.span(class_="gpg-dot", style=f"background:{color}"),
            ui.strong(goal),
            ui.tags.small(f"— {blurb}"),
            class_="gpg-chip",
        )
        for goal, blurb, color in _GOAL_CHIPS
    ]
    return ui.div(
        ui.h3("Goal Parity — Overview & Guide"),
        ui.tags.p(
            "Your portfolio is built around four goals that work together, "
            "instead of a single market benchmark. Start here to see why — "
            "and how to walk through the subtabs step by step."
        ),
        ui.div(*chips, class_="gpg-chips"),
        class_="gpg-hero",
    )


def _advantages() -> Any:
    cards = [
        ui.div(ui.h5(title), ui.markdown(body), class_="gpg-adv-card")
        for title, body in _ADVANTAGES
    ]
    return ui.div(
        ui.div("Why Goal Parity vs. a conventional benchmark", class_="gpg-section-title"),
        ui.div(*cards, class_="gpg-adv-grid"),
    )


def _steps() -> Any:
    steps = [
        ui.div(
            ui.div(
                ui.div(str(i), class_="gpg-step-num"),
                ui.div(class_="gpg-step-line"),
                class_="gpg-step-rail",
            ),
            ui.div(
                ui.div(
                    ui.div(ui.strong(title), ui.tags.em(tagline), class_="gpg-step-head"),
                    ui.div(ui.markdown(body), class_="gpg-step-content"),
                    class_="gpg-step-card",
                ),
                class_="gpg-step-body",
            ),
            class_="gpg-step",
        )
        for i, (title, tagline, body) in enumerate(_STEPS, start=1)
    ]
    return ui.div(
        ui.div("How to use this tab — step by step", class_="gpg-section-title"),
        ui.markdown(
            "Work the subtabs **left to right** — each step feeds the next. "
            "If you skip ahead, later steps quietly use default settings "
            "instead of yours."
        ),
        *steps,
    )


def _mistakes() -> Any:
    return ui.div(
        ui.h5("⚠ Common mistakes to avoid"),
        ui.tags.ul(*[ui.tags.li(ui.markdown(item)) for item in _MISTAKES]),
        class_="gpg-mistakes",
    )


@module.ui
def subtab_goal_parity_guide_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    return ui.div(
        ui.tags.style(_GUIDE_CSS),
        _hero(),
        _advantages(),
        _steps(),
        _mistakes(),
        style="max-width: 1200px; margin: 0 auto; padding-top: 0.8rem;",
    )
