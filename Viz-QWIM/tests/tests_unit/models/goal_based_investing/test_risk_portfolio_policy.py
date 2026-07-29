"""Tests for offline CVaR predefined portfolio policies."""

from __future__ import annotations

import pandas as pd
import pytest

from src.models.goal_based_investing.risk_portfolio_policy import (
    DEFAULT_RISK_PROFILE_BANDS,
    Predefined_Portfolio_Policy,
    build_cvar_policies,
    load_predefined_cvar_policies,
    normalize_risk_profile,
)


@pytest.fixture()
def monthly_returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "BIL": [0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002],
            "AGG": [0.010, 0.005, -0.010, 0.008, -0.004, 0.006, 0.003, -0.002],
            "XLK": [0.080, -0.120, 0.060, -0.070, 0.090, -0.040, 0.030, -0.020],
            "XLP": [0.030, -0.050, 0.025, -0.030, 0.040, -0.020, 0.015, -0.010],
        },
    )


def test_build_cvar_policies_respects_each_profile_equity_band(monthly_returns: pd.DataFrame) -> None:
    policies = build_cvar_policies(
        monthly_returns,
        equity_assets=("XLK", "XLP"),
        max_weight={"XLK": 0.50, "XLP": 0.50, "AGG": 0.70},
    )
    assert list(policies) == [band.profile for band in DEFAULT_RISK_PROFILE_BANDS]
    for band in DEFAULT_RISK_PROFILE_BANDS:
        policy = policies[band.profile]
        equity_weight = policy.weights["XLK"] + policy.weights["XLP"]
        assert sum(policy.weights.values()) == pytest.approx(1.0)
        assert band.minimum_equity_weight - 1e-6 <= equity_weight <= band.maximum_equity_weight + 1e-6
        assert policy.expected_shortfall >= 0


def test_risk_profile_normalization_accepts_client_contract_labels_only() -> None:
    assert normalize_risk_profile("Moderate Conservative") == "Moderate Conservative"
    assert normalize_risk_profile(" Moderate ") == "Moderate"
    assert normalize_risk_profile("moderate") == "Moderate"
    assert normalize_risk_profile("moderate_conservative") == "Moderate Conservative"
    with pytest.raises(ValueError, match="Unknown risk profile"):
        normalize_risk_profile("Moderately Aggressive")


def test_policy_scales_to_confirmed_investable_wealth() -> None:
    policy = Predefined_Portfolio_Policy(
        profile="Moderate",
        weights={"BIL": 0.20, "XLK": 0.80},
        expected_shortfall=0.05,
        confidence_level=0.95,
        equity_band=DEFAULT_RISK_PROFILE_BANDS[2],
    )
    assert policy.dollar_allocations(10_000) == {"BIL": 2_000, "XLK": 8_000}


def test_versioned_predefined_policy_table_covers_every_client_risk_profile() -> None:
    policies = load_predefined_cvar_policies()
    assert set(policies) == {band.profile for band in DEFAULT_RISK_PROFILE_BANDS}
    assert policies["Moderate"].weights["AGG"] == pytest.approx(0.20)
