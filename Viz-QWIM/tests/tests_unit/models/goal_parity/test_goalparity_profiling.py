"""Unit tests for InvestorProfile (Step 1, Roadmap Sec 3.1)."""

from __future__ import annotations

import pytest

from src.models.goal_parity import InvestorProfile


class Test_From_Client_Record:
    def test_maps_dashboard_fields(self) -> None:
        profile = InvestorProfile.from_client_record(
            {"tolerance_risk": "Moderate Aggressive", "age_current": 40, "age_retirement": 65}
        )
        assert profile.T == 25
        assert profile.risk_profile == "Moderate Aggressive"
        assert profile.eta == 8
        assert profile.b == pytest.approx(0.74, abs=0.006)

    def test_horizon_floored_at_one_year(self) -> None:
        profile = InvestorProfile.from_client_record(
            {"tolerance_risk": "Moderate", "age_current": 70, "age_retirement": 65}
        )
        assert profile.T == 1

    def test_missing_fields_fall_back_to_defaults(self) -> None:
        profile = InvestorProfile.from_client_record({})
        assert profile.T == 30  # 65 - 35 defaults
        assert profile.risk_profile == "Moderate"

    def test_unknown_risk_label_falls_back_to_moderate(self) -> None:
        profile = InvestorProfile.from_client_record({"tolerance_risk": "Bananas"})
        assert profile.risk_profile == "Moderate"


class Test_Invariants:
    def test_rejects_nonpositive_horizon(self) -> None:
        with pytest.raises(ValueError):
            InvestorProfile(T=0)

    def test_loss_tolerance_complements_barrier(self) -> None:
        profile = InvestorProfile(T=10, risk_profile="Conservative")
        assert profile.loss_tolerance == pytest.approx(1 - profile.b)

    def test_tau_years(self) -> None:
        assert InvestorProfile(T=10, tau_months=6).tau_years == pytest.approx(0.5)

    def test_normalizes_proposal_style_label(self) -> None:
        assert InvestorProfile(T=10, risk_profile="Moderately Conservative").eta == 50
