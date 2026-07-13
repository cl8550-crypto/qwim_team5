"""Private RILA UI builder for the annuities subtab."""

from __future__ import annotations

from typing import Any

from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
    create_enhanced_card_section,
    create_enhanced_numeric_input,
    create_enhanced_select_input,
)


def _create_rila_ui_impl_QWIM(
    *, payment_frequency_choices: dict[str, str], protection_type_choices: dict[str, str], crediting_strategy_choices: dict[str, str]) -> Any:
    """Build the input form for a Registered Index-Linked Annuity (RILA)."""
    return create_enhanced_card_section(
        title="RILA Parameters",
        content=[
            # --- Core parameters ---
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_age_client"),
                label_text="Client Age",
                min_value=18,
                max_value=100,
                step_size=1,
                default_value=55,
                suffix_symbol=" years",
                tooltip_text="Current age of the client",
                required_field=True,
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_rate_payout"),
                label_text="Payout Rate",
                min_value=0.00,
                max_value=1.00,
                step_size=0.005,
                default_value=0.05,
                tooltip_text="Annual payout rate as a decimal (e.g. 0.05 = 5 %)",
                required_field=True,
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_age_income_start"),
                label_text="Income Start Age",
                min_value=50,
                max_value=90,
                step_size=1,
                default_value=65,
                suffix_symbol=" years",
                tooltip_text="Age at which income payments begin",
                required_field=True,
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_term_years"),
                label_text="Term Length",
                min_value=1,
                max_value=10,
                step_size=1,
                default_value=6,
                suffix_symbol=" years",
                tooltip_text="Duration of each crediting term / segment",
                required_field=True,
                input_width="100%",
            ),
            # --- Downside protection ---
            create_enhanced_select_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_protection_type"),
                label_text="Protection Type",
                choices=protection_type_choices,
                default_selection="buffer",
                tooltip_text=(
                    "Buffer: insurer absorbs first N % of loss; "
                    "Floor: maximum loss capped at floor level"
                ),
                required_field=True,
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_buffer_rate"),
                label_text="Buffer Rate",
                min_value=0.00,
                max_value=1.00,
                step_size=0.05,
                default_value=0.10,
                tooltip_text=(
                    "Buffer percentage absorbed by the insurer (e.g. 0.10 = 10 %). "
                    "Applies when Protection Type is Buffer."
                ),
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_floor_rate"),
                label_text="Floor Rate",
                min_value=-1.00,
                max_value=0.00,
                step_size=0.05,
                default_value=-0.10,
                tooltip_text=(
                    "Maximum loss percentage for the contract holder "
                    "(e.g. -0.10 = −10 %). Applies when Protection Type is Floor."
                ),
                input_width="100%",
            ),
            # --- Crediting strategy ---
            create_enhanced_select_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_crediting_strategy"),
                label_text="Crediting Strategy",
                choices=crediting_strategy_choices,
                default_selection="cap",
                tooltip_text=(
                    "Cap: index return capped at max; "
                    "Performance Trigger: fixed rate if index >= 0; "
                    "Participation Rate: fraction of index return"
                ),
                required_field=True,
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_cap_rate"),
                label_text="Cap Rate",
                min_value=0.00,
                max_value=0.50,
                step_size=0.005,
                default_value=0.15,
                tooltip_text="Maximum return credited per term (e.g. 0.15 = 15 %)",
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_participation_rate"),
                label_text="Participation Rate",
                min_value=0.00,
                max_value=3.00,
                step_size=0.05,
                default_value=1.00,
                tooltip_text=(
                    "Fraction of index return credited (e.g. 1.50 = 150 %). "
                    "Applies when Crediting Strategy is Participation Rate."
                ),
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_performance_trigger_rate"),
                label_text="Performance Trigger Rate",
                min_value=0.00,
                max_value=0.30,
                step_size=0.005,
                default_value=0.08,
                tooltip_text=(
                    "Fixed rate credited when the index return is non-negative "
                    "(e.g. 0.08 = 8 %). Applies when Crediting Strategy is "
                    "Performance Trigger."
                ),
                input_width="100%",
            ),
            # --- Charges ---
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_rate_rider_charge"),
                label_text="Rider Charge",
                min_value=0.00,
                max_value=0.05,
                step_size=0.0025,
                default_value=0.00,
                tooltip_text="Annual rider charge for optional benefits (e.g. 0.005 = 0.50 %)",
                input_width="100%",
            ),
            # --- Surrender ---
            create_enhanced_numeric_input(
                input_ID=(
                    "input_ID_tab_products_subtab_annuities_RILA_rate_surrender_charge_initial"
                ),
                label_text="Initial Surrender Charge",
                min_value=0.00,
                max_value=0.20,
                step_size=0.01,
                default_value=0.06,
                tooltip_text="Initial surrender charge rate (e.g. 0.06 = 6 %)",
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=(
                    "input_ID_tab_products_subtab_annuities_RILA_surrender_charge_schedule_years"
                ),
                label_text="Surrender Schedule Years",
                min_value=0,
                max_value=15,
                step_size=1,
                default_value=6,
                suffix_symbol=" years",
                tooltip_text="Number of years for the surrender charge to decline to zero",
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_pct_free_withdrawal"),
                label_text="Free Withdrawal %",
                min_value=0.00,
                max_value=0.20,
                step_size=0.01,
                default_value=0.10,
                tooltip_text="Annual free-withdrawal percentage (e.g. 0.10 = 10 %)",
                input_width="100%",
            ),
            create_enhanced_numeric_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_rate_interim_discount"),
                label_text="Interim Discount Rate",
                min_value=0.00,
                max_value=0.10,
                step_size=0.005,
                default_value=0.02,
                tooltip_text=(
                    "Discount rate used in interim-value (market-value-adjusted) "
                    "calculation (e.g. 0.02 = 2 %)"
                ),
                input_width="100%",
            ),
            # --- Guarantees ---
            create_enhanced_select_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_has_GMDB"),
                label_text="GMDB Included",
                choices={"false": "No", "true": "Yes"},
                default_selection="false",
                tooltip_text="Include Guaranteed Minimum Death Benefit",
            ),
            create_enhanced_select_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_has_return_of_premium_DB"),
                label_text="Return-of-Premium Death Benefit",
                choices={"true": "Yes", "false": "No"},
                default_selection="true",
                tooltip_text=("Whether the death benefit guarantees at least the premium paid"),
            ),
            create_enhanced_select_input(
                input_ID=("input_ID_tab_products_subtab_annuities_RILA_payment_frequency"),
                label_text="Payment Frequency",
                choices=payment_frequency_choices,
                default_selection="12",
                tooltip_text="Number of payments per year",
            ),
        ],
        icon_class="fas fa-shield-alt",
        card_class="shadow-sm border-danger",
    )