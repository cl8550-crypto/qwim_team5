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
Work the subtabs **left to right** — each step feeds the next, and skipping
ahead means later steps silently run on defaults instead of your inputs.

**Step 1 — Investor Profile.** If the Clients tab is filled in, leave
*"Use Clients tab inputs"* checked: horizon and risk profile are read from
there automatically. Otherwise uncheck it and set the risk profile, horizon
T, and rebalancing frequency τ by hand. *Before moving on*, confirm the
table shows the η and loss barrier you expect, and read the "Source:" line
under it — it tells you which inputs are actually being used.

**Step 2 — 4×4 Asset Map.** Choose the investment universe with the ticker
checkboxes. The map shows how each asset splits across the four goals.
Deselecting too many tickers can leave a goal with no support — if you see
a goal flagged as *structurally scarce* later, revisit this step first.

**Step 3 — Strategic Optimization.** *Goal Parity Balanced* (the default)
targets equal 25% power for each goal — start here. *Goal Tilted* lets you
favor one goal via the tilt-strength slider; note a tilt re-weights goal
*priorities*, it is not a return-maximizing dial. Heed the on-screen
warnings: a solver-failure note means the shown weights are a best effort
and should be confirmed before use, and a scarce-goal note means the
universe itself limits that goal, not the optimizer.

**Step 4 — Tactical Rebalancing.** Simulates the portfolio drifting away
from target (the σ slider controls how far, the seed picks the scenario)
and shows the trades the signal-priority rule would execute. Different
seeds produce different drift scenarios and therefore different trades —
that is expected, not an error.

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
