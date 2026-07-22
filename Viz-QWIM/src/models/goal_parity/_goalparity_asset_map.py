"""GIPL asset map coordinates for visualization (Roadmap Sec 3.7).

Confirmed against Golts & Jones (2023), Appendix B ("GIPL Goal Map"):
    x = epv_p + epv_g = Pi_L   (the "liquitility" / horizontal axis)
    y = epv_i + epv_g = Pi_D   (the "defaultility" / vertical axis)

i.e. an asset's map coordinates are exactly its two option-trigger prices,
not a separate linear combination of goal shares. Cash (Pi_D = Pi_L ~ 0)
plots at the origin; a 50/50 Preservation/Growth split plots at (1, 0.5).
"""

from __future__ import annotations

from src.models.goal_parity._goalparity_decomposition import GoalShares


def asset_map_coordinates(goal_shares: GoalShares) -> tuple[float, float]:
    """Map one asset's option triggers to a point (x, y) in [0, 1]^2 (Appendix B)."""
    x = goal_shares.pi_liquidity
    y = goal_shares.pi_default
    return (float(min(1.0, max(0.0, x))), float(min(1.0, max(0.0, y))))
