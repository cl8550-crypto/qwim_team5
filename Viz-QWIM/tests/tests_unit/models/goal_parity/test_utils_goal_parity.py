"""Unit tests for Goal Parity shared constants (Roadmap Sec 3.1)."""

from __future__ import annotations

import math

import pytest

from src.models.goal_parity.utils_goal_parity import (
    GOALS,
    RISK_PROFILE_TO_ETA,
    THETA_BALANCED,
    eta_to_barrier,
    normalize_risk_profile,
    risk_profile_to_barrier,
)


class Test_Eta_To_Barrier:
    """b(eta) = eta^(1/(1-eta)) against the paper's Exhibit [Risk Aversion]."""

    @pytest.mark.parametrize(
        ("eta", "expected_b"),
        [(1, 0.37), (2, 0.50), (3, 0.58), (4, 0.63), (5, 0.67), (6, 0.70),
         (7, 0.72), (8, 0.74), (9, 0.76), (10, 0.77), (20, 0.85), (30, 0.89),
         (50, 0.92), (100, 0.95), (200, 0.97)],
    )
    def test_matches_paper_exhibit(self, eta: int, expected_b: float) -> None:
        assert eta_to_barrier(eta) == pytest.approx(expected_b, abs=0.006)

    def test_log_utility_limit(self) -> None:
        assert eta_to_barrier(1) == pytest.approx(math.exp(-1))
        # continuity: eta slightly away from 1 stays near 1/e
        assert eta_to_barrier(1.0001) == pytest.approx(math.exp(-1), abs=1e-3)

    def test_monotone_increasing_in_eta(self) -> None:
        barriers = [eta_to_barrier(eta) for eta in (1, 2, 5, 10, 50, 200)]
        assert barriers == sorted(barriers)

    def test_rejects_nonpositive_eta(self) -> None:
        with pytest.raises(ValueError):
            eta_to_barrier(0)


class Test_Risk_Profile_Lookup:
    def test_keys_match_dashboard_valid_risk_tolerance(self) -> None:
        assert set(RISK_PROFILE_TO_ETA) == {
            "Conservative", "Moderate Conservative", "Moderate",
            "Moderate Aggressive", "Aggressive",
        }

    def test_normalize_accepts_proposal_style_labels(self) -> None:
        assert normalize_risk_profile("Moderately Aggressive") == "Moderate Aggressive"
        assert normalize_risk_profile("  conservative ") == "Conservative"

    def test_normalize_rejects_unknown(self) -> None:
        with pytest.raises(ValueError):
            normalize_risk_profile("YOLO")

    def test_loss_tolerances_monotone(self) -> None:
        order = ["Aggressive", "Moderate Aggressive", "Moderate",
                 "Moderate Conservative", "Conservative"]
        barriers = [risk_profile_to_barrier(label) for label in order]
        assert barriers == sorted(barriers)  # more conservative -> higher b


class Test_Constants:
    def test_goals_and_theta(self) -> None:
        assert GOALS == ("Liquidity", "Income", "Preservation", "Growth")
        assert sum(THETA_BALANCED.values()) == pytest.approx(1.0)
        assert set(THETA_BALANCED) == set(GOALS)
