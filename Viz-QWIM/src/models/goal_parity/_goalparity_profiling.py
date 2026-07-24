"""InvestorProfile: Step 1 investor profiling (Roadmap Sec 3.1, Sec 4.1).

Implementation status: T and risk profile are NOT elicited by this module —
they come from the dashboard's existing Clients tab (advisor-built), via the
``tolerance_risk`` and ``age_current``/``age_retirement`` fields
(src/clients_QWIM/_client_constants.py). This module only converts those
fields into the quantitative inputs (eta, barrier b) the pipeline needs.
The optional LLM conversational layer described in the Model Proposal is an
enhancement on top of this, not a prerequisite.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.goal_parity.utils_goal_parity import (
    DEFAULT_TAU_MONTHS,
    RISK_PROFILE_TO_ETA,
    eta_to_barrier,
    normalize_risk_profile,
)


@dataclass(frozen=True)
class InvestorProfile:
    """Holds T, tau, risk profile -> eta -> barrier b (Roadmap Sec 7)."""

    T: float  # strategic horizon in years
    tau_months: int = DEFAULT_TAU_MONTHS
    risk_profile: str = "Moderate"

    def __post_init__(self) -> None:
        if self.T <= 0:
            raise ValueError(f"Strategic horizon T must be positive, got {self.T}")
        if self.tau_months <= 0:
            raise ValueError(f"tau_months must be positive, got {self.tau_months}")
        object.__setattr__(self, "risk_profile", normalize_risk_profile(self.risk_profile))

    @property
    def eta(self) -> int:
        """Power-utility risk aversion from the categorical lookup (Sec 3.1)."""
        return RISK_PROFILE_TO_ETA[self.risk_profile]

    @property
    def b(self) -> float:
        """"Substantial loss" barrier b(eta) (Sec 3.1)."""
        return eta_to_barrier(self.eta)

    @property
    def loss_tolerance(self) -> float:
        """1 - b: the fraction of capital the investor can tolerate losing."""
        return 1.0 - self.b

    @property
    def tau_years(self) -> float:
        return self.tau_months / 12.0

    @classmethod
    def from_client_record(cls, client: dict) -> "InvestorProfile":
        """Build a profile from a Clients-tab record.

        T = age_retirement - age_current (floored at 1 year);
        risk_profile = the client's ``tolerance_risk`` field.
        """
        age_current = int(client.get("age_current") or 35)
        age_retirement = int(client.get("age_retirement") or 65)
        horizon = max(1, age_retirement - age_current)
        risk = client.get("tolerance_risk") or "Moderate"
        try:
            risk = normalize_risk_profile(risk)
        except ValueError:
            risk = "Moderate"
        return cls(T=float(horizon), risk_profile=risk)
