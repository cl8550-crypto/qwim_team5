"""4x4 asset map coordinates for visualization (Roadmap Sec 3.7).

[Verify against PDF]: the source paper's exact (x, y) linear combination
extracted with corrupted subscripts. This implementation uses the two option
triggers' weighted shares, which places cash (fully liquid, default-resilient)
at the origin as the Roadmap requires:

    x = EPV_I share + EPV_G share   (default-exposed / "return ON capital" axis)
    y = EPV_P share + EPV_G share   (illiquid / long-horizon axis)

Re-check against the paper's "Asset Map" exhibit before final report figures.
"""

from __future__ import annotations

from src.models.goal_parity._goalparity_decomposition import GoalShares


def asset_map_coordinates(goal_shares: GoalShares) -> tuple[float, float]:
    """Map one asset's goal shares to a point (x, y) in [0, 1]^2 (Sec 3.7)."""
    shares = goal_shares.shares
    x = shares["Income"] + shares["Growth"]
    y = shares["Preservation"] + shares["Growth"]
    return (float(min(1.0, max(0.0, x))), float(min(1.0, max(0.0, y))))
