"""Shared constants and closed-form helpers for the Goal Parity model.

Implements Technical Roadmap Sec 2 (notation), Sec 3.1 (risk aversion and the
"substantial loss" barrier) and Sec 3.5 (Goal Parity Balanced targets), per
Cron & Golts (2022), "4x4 Asset Allocation" (SSRN 3949919).
"""

from __future__ import annotations

import math


#: The four universal goals, in canonical order (Roadmap Sec 2).
GOALS: tuple[str, ...] = ("Liquidity", "Income", "Preservation", "Growth")

#: Goal Parity Balanced targets: all four goals equally powered (Roadmap Sec 3.5).
THETA_BALANCED: dict[str, float] = {
    "Liquidity": 0.25,
    "Income": 0.25,
    "Preservation": 0.25,
    "Growth": 0.25,
}

#: Categorical risk profile -> eta lookup (Roadmap Sec 3.1). Keys match the
#: dashboard's VALID_RISK_TOLERANCE labels (src/clients_QWIM/_client_constants.py);
#: every eta value is a literal row of the paper's Exhibit [Risk Aversion].
RISK_PROFILE_TO_ETA: dict[str, int] = {
    "Aggressive": 1,
    "Moderate Aggressive": 8,
    "Moderate": 20,
    "Moderate Conservative": 50,
    "Conservative": 200,
}

#: Project default tactical rebalancing frequency (Proposal Step 1 note).
DEFAULT_TAU_MONTHS: int = 6

#: Paper's illustrative one-year liquidity strike k1 (Roadmap Sec 3.4).
DEFAULT_LIQUIDITY_STRIKE_K1: float = 0.985


def normalize_risk_profile(label: str) -> str:
    """Map proposal-style labels ("Moderately Aggressive") onto the dashboard's
    VALID_RISK_TOLERANCE labels ("Moderate Aggressive")."""
    cleaned = " ".join(str(label).strip().split())
    cleaned = cleaned.replace("Moderately", "Moderate")
    matches = {k.lower(): k for k in RISK_PROFILE_TO_ETA}
    key = matches.get(cleaned.lower())
    if key is None:
        raise ValueError(
            f"Unknown risk profile {label!r}; expected one of {sorted(RISK_PROFILE_TO_ETA)}"
        )
    return key


def eta_to_barrier(eta: float) -> float:
    """Closed-form "substantial loss" barrier b(eta) (Roadmap Sec 3.1).

    Solving u(b) = -1 for the power utility u(c) = (c^(1-eta) - 1)/(1-eta)
    gives b(eta) = eta^(1/(1-eta)); the log-utility limit is b(1) = 1/e.
    Verified against every row of the paper's Exhibit [Risk Aversion].
    """
    if eta <= 0:
        raise ValueError(f"eta must be positive, got {eta}")
    if math.isclose(eta, 1.0):
        return math.exp(-1.0)
    return float(eta ** (1.0 / (1.0 - eta)))


def risk_profile_to_barrier(label: str) -> float:
    """Convenience: categorical risk profile -> barrier b via the eta lookup."""
    return eta_to_barrier(RISK_PROFILE_TO_ETA[normalize_risk_profile(label)])
