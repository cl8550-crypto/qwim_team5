"""Goal Parity subtab: Overview & Guide (landing page).

Static, client-facing introduction shown as the first Goal Parity subtab:
why the goal-based approach can hold an edge over a conventional benchmark
across market regimes, and a step-by-step guide through the four pipeline
subtabs so users work them in the intended order.
"""

from __future__ import annotations

from typing import Any

from shiny import module, ui

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name=__name__)


_WHY_MARKDOWN = """
A conventional benchmark (e.g. a 60/40 stock/bond mix) is built around a
single objective — market growth — and implicitly bets that one regime
persists. The Goal Parity approach (Cron & Golts 2022; Golts & Jones 2023)
is built differently, and each difference matters most exactly when the
market changes regime:

**1. Diversified across goals, not just assets.** The portfolio holds
explicit *Liquidity*, *Income*, *Preservation*, and *Growth* sleeves, so
some part of it is designed for every market environment. A 60/40 benchmark
has no explicit defense in regimes where stocks and bonds fall together
(e.g. the 2022 inflation shock); here, the Preservation and Liquidity
sleeves are sized in advance, not improvised after the drawdown.

**2. Regime-aware risk inputs.** Volatilities are EWMA-weighted — recent
observations count more — and adjusted for (Winsorized) downside skew.
When the market shifts into a stressed regime, risk estimates adapt within
weeks instead of being diluted by decades of calm history, and assets with
crash-prone return distributions are penalized before capital is allocated.

**3. Assets classified by behavior, not by label.** Each asset's goal
scores come from option-style payoff triggers (including a first-passage
probability of breaching the investor's loss barrier), so an asset that
looks like "Growth" in calm regimes but loses its Preservation power under
stress is scored accordingly. Static asset-class labels can't see that.

**4. A personal loss barrier, not a market-average one.** The investor's
risk profile maps to a risk-aversion parameter η and a *substantial-loss*
barrier b(η). The optimization explicitly controls the probability of
crossing *your* barrier — bear-regime risk is managed against your own
tolerance rather than a one-size-fits-all volatility target.

**5. Disciplined, cost-aware rebalancing.** Trades happen only when a goal
gap exceeds the tolerance ε *and* the gap-reduction per unit transaction
cost clears a threshold, within a turnover budget. During noisy regime
transitions this avoids the whipsaw over-trading that erodes benchmark-
tracking strategies, while still realigning decisively when drift is real.
"""

_HOW_MARKDOWN = """
Work the subtabs **left to right** — each step feeds the next. If you skip
ahead, later steps quietly use default settings instead of yours.

**Step 1 — Investor Profile** *(tell the model who you are)*

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

**Step 2 — 4×4 Asset Map** *(choose what the model can invest in)*

- Tick the boxes for the investments you want considered. Keeping the full
  default list selected is a good starting point.
- The map shows how each investment supports the four goals — one asset
  can serve several goals at once (e.g. part Income, part Preservation).
- **Keep the universe broad:** every goal needs at least a few supporting
  assets. If a later step flags a goal as *structurally scarce*, come back
  here and re-add tickers rather than fighting the optimizer.

**Step 3 — Strategic Optimization** *(build your target portfolio)*

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

**Step 4 — Tactical Rebalancing** *(see how the portfolio stays on track)*

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

---

**Common mistakes to avoid**

- Jumping straight to Optimization or Rebalancing — the results then
  reflect the *default* Moderate profile, not your client's.
- Leaving "Use Clients tab inputs" checked when the Clients tab is empty
  or stale — always check the "Source:" line in Step 1.
- Setting a horizon T shorter than the client's actual timeline, which
  understates how much Growth the plan can safely carry.
- Ignoring the solver-failure or scarce-goal warnings in Step 3 — they
  qualify every number shown downstream.
- Comparing rebalancing trades across different drift seeds and
  concluding the model is unstable — each seed is a different scenario.
"""


@module.ui
def subtab_goal_parity_guide_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]
) -> Any:  # pragma: no cover
    del data_utils, data_inputs
    return ui.div(
        ui.h3("Overview & Guide"),
        ui.markdown(
            "Start here: what the Goal Parity model does differently from a "
            "conventional benchmark, and how to work through the subtabs "
            "step by step."
        ),
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Why Goal Parity vs. a conventional benchmark"),
                ui.markdown(_WHY_MARKDOWN),
            ),
            ui.card(
                ui.card_header("How to use this tab — step by step"),
                ui.markdown(_HOW_MARKDOWN),
            ),
            width=1 / 2,
        ),
    )
