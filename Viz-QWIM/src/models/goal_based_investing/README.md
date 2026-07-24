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
