"""Integration tests for Annuity_RILA payout and withdrawal workflows.

These tests exercise the real RILA object together with Polars scenario and
inflation data to verify that payout, monthly payout, and withdrawal-rate
paths compose correctly across the public annuity interface.
"""

from __future__ import annotations

import polars as pl
import pytest

from src.products.annuity.annuity_RILA import Annuity_RILA, Protection_Type


class Class_Test_Integration_Annuity_RILA:
    """Integration tests for end-to-end RILA payout flows."""

    @pytest.mark.integration()
    def Test_Scenario_And_Inflation_DataFrames_Feed_Payout_Flow(self) -> None:
        """Scenario and inflation inputs should compose across payout APIs."""
        rila = Annuity_RILA(
            client_age=64,
            annuity_payout_rate=0.05,
            age_income_start=65,
            protection_type=Protection_Type.BUFFER,
            buffer_rate=0.10,
            cap_rate=0.15,
        )
        rila.m_client_age = 66

        scenario_df = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2025-01-01"],
                "S&P 500": [0.10, -0.05],
            },
        )
        inflation_df = pl.DataFrame(
            {
                "Start Date": ["2024-01-01"],
                "End Date": ["2025-01-01"],
                "Inflation Factor": [1.03],
                "Inverse Inflation Factor": [1.0 / 1.03],
            },
        )

        annual_payout = rila.calc_annuity_payout(
            amount_principal=100_000.0,
            obj_scenarios=scenario_df,
        )
        monthly_payout = rila.calc_monthly_payout(
            amount_principal=100_000.0,
            obj_scenarios=scenario_df,
            obj_inflation=inflation_df,
        )
        withdrawal_rates = rila.calc_withdrawal_rates(
            amount_principal=100_000.0,
            obj_scenarios=scenario_df,
            obj_inflation=inflation_df,
        )

        assert annual_payout == pytest.approx(5_500.0)
        assert monthly_payout == pytest.approx(annual_payout / 12.0)
        assert withdrawal_rates.nominal_WR == pytest.approx(annual_payout / 100_000.0)
        assert withdrawal_rates.real_WR == pytest.approx(
            withdrawal_rates.nominal_WR * (1.0 / 1.03),
        )
