# Goal-based investing baseline

`Goal_Based_Investing_Baseline` evaluates a single financial goal before
portfolio construction.  It compounds the current balance and end-of-year
contributions using an annual return assumption, then reports the projected
amount, funding ratio, shortfall or surplus, and funded status.

For Monte Carlo or other external scenario engines, pass one terminal value
per scenario to `assess_terminal_values`.  The resulting
`success_probability` is the fraction of scenarios meeting the target.

```python
from src.models.goal_based_investing import Goal_Based_Investing_Baseline

goal = Goal_Based_Investing_Baseline(
    goal_name="Retirement",
    target_amount=1_000_000,
    current_amount=500_000,
    years_to_goal=10,
    annual_contribution=20_000,
)
assessment = goal.assess(annual_return=0.05)
```

The model is deliberately a planning baseline: it does not optimise asset
weights, infer returns, model taxes, or rebalance a portfolio.

## Research core: multistage goal postponement

`model_goal_postponement.py` implements the small-tree, exact multistage
stochastic mixed-integer program in Bae et al. (2024). At every scenario-tree
node it rebalances a long-only portfolio after returns are observed, pays
selected all-or-nothing goals, and maximises expected goal utility. A
postponable goal can be completed only once on a path; its cost inflation and
utility time preference are both measured from a fixed reference stage.

`scenario_tree_goal_based_investing.py` turns the cleaned daily data into
monthly simple returns and makes a historical-bootstrap tree. The Version 1
investable universe is normally `BIL, XLK, XLP, AGG, TIP, GLD`. VIX and CPI
are regime/calibration features, not investable tree returns. CPI is lagged by
one month to avoid a simple release-timing look-ahead error.

The exact model is intentionally for short, low-branching trees: five return
periods and two branches yields 63 nodes. Larger dashboard cases need explicit
scenario reduction or SDDiP, not an oversized deterministic-equivalent solve.
