"""Life-insurance product subtab facade for the QWIM dashboard."""

from __future__ import annotations

import typing

from typing import Any

from shiny import module, reactive, ui

from src.dashboard.shiny_tab_products._subtab_insurance_life_ui import (
    _DEATH_BENEFIT_OPTION_CHOICES,
    _PAYMENT_FREQUENCY_CHOICES,
    _SURVIVOR_CHASSIS_CHOICES,
    _TERM_TYPE_CHOICES,
    _UL_VARIANT_CHOICES,
    _UNDERWRITING_CLASS_CHOICES,
    create_survivor_life_ui_impl_QWIM,
    create_term_life_ui_impl_QWIM,
    create_universal_life_ui_impl_QWIM,
    create_variable_life_ui_impl_QWIM,
    create_whole_life_ui_impl_QWIM,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)


def _create_whole_life_ui() -> Any:
    """Build the input form for a Whole Life Insurance policy."""
    return create_whole_life_ui_impl_QWIM()


def _create_term_life_ui() -> Any:
    """Build the input form for a Term Life Insurance policy."""
    return create_term_life_ui_impl_QWIM()


def _create_universal_life_ui() -> Any:
    """Build the input form for a Universal Life Insurance policy."""
    return create_universal_life_ui_impl_QWIM()


def _create_variable_life_ui() -> Any:
    """Build the input form for a Variable Life Insurance policy."""
    return create_variable_life_ui_impl_QWIM()


def _create_survivor_life_ui() -> Any:
    """Build the input form for a Survivor (Second-to-Die) Life policy."""
    return create_survivor_life_ui_impl_QWIM()


# ======================================================================
# Module UI
# ======================================================================


@module.ui
def subtab_insurance_life_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:
    """Create the Life Insurance subtab UI with five sub-subtabs.

    Parameters
    ----------
    data_utils : dict[str, Any]
        Utility functions and configuration data.
    data_inputs : dict[str, Any]
        Default input values and validation rules.

    Returns
    -------
    ui.div
        Complete Life Insurance subtab UI with five nav-panels.
    """
    return ui.div(
        ui.h3("Life Insurance Products", class_="text-center mb-4"),
        ui.p(
            "Select a life insurance type and enter the corresponding parameters.",
            class_="text-muted text-center mb-3",
        ),
        ui.navset_tab(
            ui.nav_panel("Whole Life", _create_whole_life_ui()),
            ui.nav_panel("Term Life", _create_term_life_ui()),
            ui.nav_panel("Universal Life", _create_universal_life_ui()),
            ui.nav_panel("Variable Life", _create_variable_life_ui()),
            ui.nav_panel("Survivor Life", _create_survivor_life_ui()),
            id="ID_tab_products_subtab_insurance_life_tabs_all",
        ),
    )


# ======================================================================
# Module Server
# ======================================================================


@module.server
def subtab_insurance_life_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Server logic for the Life Insurance subtab.

    Stores user-entered life insurance parameters into the shared reactive
    state dictionary so that downstream modules (results, reporting) can
    consume them.

    Parameters
    ----------
    input : typing.Any
        Shiny input object with reactive values from the insurance forms.
    output : typing.Any
        Shiny output object (unused for now — reserved for future renders).
    session : typing.Any
        Shiny session object.
    data_utils : dict[str, Any]
        Utility functions and configuration data.
    data_inputs : dict[str, Any]
        Default input values and validation rules.
    reactives_shiny : dict[str, Any]
        Shared reactive state dictionary for cross-module communication.
    """
    _logger.info("Initializing Life Insurance subtab server")

    # ------------------------------------------------------------------
    # Reactive calculations — gather Whole Life inputs
    # ------------------------------------------------------------------

    @reactive.calc
    def calc_whole_life_params() -> dict[str, Any]:
        """Collect Whole Life input values into a dictionary."""
        _pfx = "input_ID_tab_products_subtab_insurance_life_whole_life"
        return {
            "insured_age": getattr(input, f"{_pfx}_insured_age")(),
            "face_amount": getattr(input, f"{_pfx}_face_amount")(),
            "rate_guaranteed_interest": getattr(
                input,
                f"{_pfx}_rate_guaranteed_interest",
            )(),
            "cash_value": getattr(input, f"{_pfx}_cash_value")(),
            "is_participating": getattr(
                input,
                f"{_pfx}_is_participating",
            )(),
            "rate_dividend": getattr(input, f"{_pfx}_rate_dividend")(),
            "paid_up_additions": getattr(
                input,
                f"{_pfx}_paid_up_additions",
            )(),
            "rate_loan_interest": getattr(
                input,
                f"{_pfx}_rate_loan_interest",
            )(),
            "amount_loan_outstanding": getattr(
                input,
                f"{_pfx}_amount_loan_outstanding",
            )(),
            "premium_paying_years": getattr(
                input,
                f"{_pfx}_premium_paying_years",
            )(),
            "rate_cost_of_insurance": getattr(
                input,
                f"{_pfx}_rate_cost_of_insurance",
            )(),
            "death_benefit_option": getattr(
                input,
                f"{_pfx}_death_benefit_option",
            )(),
            "underwriting_class": getattr(
                input,
                f"{_pfx}_underwriting_class",
            )(),
            "is_smoker": getattr(input, f"{_pfx}_is_smoker")(),
            "payment_frequency": getattr(
                input,
                f"{_pfx}_payment_frequency",
            )(),
        }

    # ------------------------------------------------------------------
    # Reactive calculations — gather Term Life inputs
    # ------------------------------------------------------------------

    @reactive.calc
    def calc_term_life_params() -> dict[str, Any]:
        """Collect Term Life input values into a dictionary."""
        _pfx = "input_ID_tab_products_subtab_insurance_life_term_life"
        return {
            "insured_age": getattr(input, f"{_pfx}_insured_age")(),
            "face_amount": getattr(input, f"{_pfx}_face_amount")(),
            "term_years": getattr(input, f"{_pfx}_term_years")(),
            "term_type": getattr(input, f"{_pfx}_term_type")(),
            "is_convertible": getattr(
                input,
                f"{_pfx}_is_convertible",
            )(),
            "conversion_deadline_year": getattr(
                input,
                f"{_pfx}_conversion_deadline_year",
            )(),
            "is_renewable": getattr(input, f"{_pfx}_is_renewable")(),
            "has_return_of_premium": getattr(
                input,
                f"{_pfx}_has_return_of_premium",
            )(),
            "rate_cost_of_insurance": getattr(
                input,
                f"{_pfx}_rate_cost_of_insurance",
            )(),
            "underwriting_class": getattr(
                input,
                f"{_pfx}_underwriting_class",
            )(),
            "is_smoker": getattr(input, f"{_pfx}_is_smoker")(),
            "payment_frequency": getattr(
                input,
                f"{_pfx}_payment_frequency",
            )(),
        }

    # ------------------------------------------------------------------
    # Reactive calculations — gather Universal Life inputs
    # ------------------------------------------------------------------

    @reactive.calc
    def calc_universal_life_params() -> dict[str, Any]:
        """Collect Universal Life input values into a dictionary."""
        _pfx = "input_ID_tab_products_subtab_insurance_life_universal_life"
        return {
            "insured_age": getattr(input, f"{_pfx}_insured_age")(),
            "face_amount": getattr(input, f"{_pfx}_face_amount")(),
            "ul_variant": getattr(input, f"{_pfx}_ul_variant")(),
            "rate_crediting_current": getattr(
                input,
                f"{_pfx}_rate_crediting_current",
            )(),
            "rate_crediting_guaranteed": getattr(
                input,
                f"{_pfx}_rate_crediting_guaranteed",
            )(),
            "rate_cap": getattr(input, f"{_pfx}_rate_cap")(),
            "rate_floor": getattr(input, f"{_pfx}_rate_floor")(),
            "participation_rate": getattr(
                input,
                f"{_pfx}_participation_rate",
            )(),
            "cash_value": getattr(input, f"{_pfx}_cash_value")(),
            "rate_COI": getattr(input, f"{_pfx}_rate_COI")(),
            "rate_expense_charge": getattr(
                input,
                f"{_pfx}_rate_expense_charge",
            )(),
            "target_premium": getattr(
                input,
                f"{_pfx}_target_premium",
            )(),
            "minimum_premium": getattr(
                input,
                f"{_pfx}_minimum_premium",
            )(),
            "rate_surrender_charge": getattr(
                input,
                f"{_pfx}_rate_surrender_charge",
            )(),
            "surrender_charge_years": getattr(
                input,
                f"{_pfx}_surrender_charge_years",
            )(),
            "has_no_lapse_guarantee": getattr(
                input,
                f"{_pfx}_has_no_lapse_guarantee",
            )(),
            "nlg_guarantee_years": getattr(
                input,
                f"{_pfx}_nlg_guarantee_years",
            )(),
            "death_benefit_option": getattr(
                input,
                f"{_pfx}_death_benefit_option",
            )(),
            "amount_loan_outstanding": getattr(
                input,
                f"{_pfx}_amount_loan_outstanding",
            )(),
            "rate_loan_interest": getattr(
                input,
                f"{_pfx}_rate_loan_interest",
            )(),
            "underwriting_class": getattr(
                input,
                f"{_pfx}_underwriting_class",
            )(),
            "is_smoker": getattr(input, f"{_pfx}_is_smoker")(),
            "payment_frequency": getattr(
                input,
                f"{_pfx}_payment_frequency",
            )(),
        }

    # ------------------------------------------------------------------
    # Reactive calculations — gather Variable Life inputs
    # ------------------------------------------------------------------

    @reactive.calc
    def calc_variable_life_params() -> dict[str, Any]:
        """Collect Variable Life input values into a dictionary."""
        _pfx = "input_ID_tab_products_subtab_insurance_life_variable_life"
        return {
            "insured_age": getattr(input, f"{_pfx}_insured_age")(),
            "face_amount": getattr(input, f"{_pfx}_face_amount")(),
            "cash_value": getattr(input, f"{_pfx}_cash_value")(),
            "rate_ME_charge": getattr(
                input,
                f"{_pfx}_rate_ME_charge",
            )(),
            "rate_admin_fee": getattr(
                input,
                f"{_pfx}_rate_admin_fee",
            )(),
            "rate_investment_management": getattr(
                input,
                f"{_pfx}_rate_investment_management",
            )(),
            "rate_COI": getattr(input, f"{_pfx}_rate_COI")(),
            "rate_surrender_charge": getattr(
                input,
                f"{_pfx}_rate_surrender_charge",
            )(),
            "surrender_charge_years": getattr(
                input,
                f"{_pfx}_surrender_charge_years",
            )(),
            "death_benefit_option": getattr(
                input,
                f"{_pfx}_death_benefit_option",
            )(),
            "amount_loan_outstanding": getattr(
                input,
                f"{_pfx}_amount_loan_outstanding",
            )(),
            "rate_loan_interest": getattr(
                input,
                f"{_pfx}_rate_loan_interest",
            )(),
            "underwriting_class": getattr(
                input,
                f"{_pfx}_underwriting_class",
            )(),
            "is_smoker": getattr(input, f"{_pfx}_is_smoker")(),
            "payment_frequency": getattr(
                input,
                f"{_pfx}_payment_frequency",
            )(),
        }

    # ------------------------------------------------------------------
    # Reactive calculations — gather Survivor Life inputs
    # ------------------------------------------------------------------

    @reactive.calc
    def calc_survivor_life_params() -> dict[str, Any]:
        """Collect Survivor Life input values into a dictionary."""
        _pfx = "input_ID_tab_products_subtab_insurance_life_survivor_life"
        return {
            "insured_age": getattr(input, f"{_pfx}_insured_age")(),
            "insured_age_second": getattr(
                input,
                f"{_pfx}_insured_age_second",
            )(),
            "face_amount": getattr(input, f"{_pfx}_face_amount")(),
            "chassis": getattr(input, f"{_pfx}_chassis")(),
            "underwriting_class": getattr(
                input,
                f"{_pfx}_underwriting_class",
            )(),
            "underwriting_class_second": getattr(
                input,
                f"{_pfx}_underwriting_class_second",
            )(),
            "is_smoker": getattr(input, f"{_pfx}_is_smoker")(),
            "is_smoker_second": getattr(
                input,
                f"{_pfx}_is_smoker_second",
            )(),
            "first_death_occurred": getattr(
                input,
                f"{_pfx}_first_death_occurred",
            )(),
            "cash_value": getattr(input, f"{_pfx}_cash_value")(),
            "rate_guaranteed_interest": getattr(
                input,
                f"{_pfx}_rate_guaranteed_interest",
            )(),
            "rate_COI_insured_1": getattr(
                input,
                f"{_pfx}_rate_COI_insured_1",
            )(),
            "rate_COI_insured_2": getattr(
                input,
                f"{_pfx}_rate_COI_insured_2",
            )(),
            "death_benefit_option": getattr(
                input,
                f"{_pfx}_death_benefit_option",
            )(),
            "has_split_option": getattr(
                input,
                f"{_pfx}_has_split_option",
            )(),
            "amount_loan_outstanding": getattr(
                input,
                f"{_pfx}_amount_loan_outstanding",
            )(),
            "rate_loan_interest": getattr(
                input,
                f"{_pfx}_rate_loan_interest",
            )(),
            "rate_surrender_charge": getattr(
                input,
                f"{_pfx}_rate_surrender_charge",
            )(),
            "surrender_charge_years": getattr(
                input,
                f"{_pfx}_surrender_charge_years",
            )(),
            "payment_frequency": getattr(
                input,
                f"{_pfx}_payment_frequency",
            )(),
        }

    # ------------------------------------------------------------------
    # Store life insurance parameters into reactives_shiny on change
    # ------------------------------------------------------------------

    @reactive.effect
    def _sync_insurance_life_params_to_reactives() -> None:
        """Push the latest life insurance params into the shared state."""
        if "User_Inputs_Shiny" not in reactives_shiny:
            _logger.warning(
                "reactives_shiny missing 'User_Inputs_Shiny' key",
            )
            return

        user_inputs = reactives_shiny["User_Inputs_Shiny"]

        # Initialise reactive.Value containers on first run
        _keys = [
            "Insurance_Life_Whole_Params",
            "Insurance_Life_Term_Params",
            "Insurance_Life_Universal_Params",
            "Insurance_Life_Variable_Params",
            "Insurance_Life_Survivor_Params",
        ]
        for key in _keys:
            if key not in user_inputs:
                user_inputs[key] = reactive.value(None)

        user_inputs["Insurance_Life_Whole_Params"].set(
            calc_whole_life_params(),
        )
        user_inputs["Insurance_Life_Term_Params"].set(
            calc_term_life_params(),
        )
        user_inputs["Insurance_Life_Universal_Params"].set(
            calc_universal_life_params(),
        )
        user_inputs["Insurance_Life_Variable_Params"].set(
            calc_variable_life_params(),
        )
        user_inputs["Insurance_Life_Survivor_Params"].set(
            calc_survivor_life_params(),
        )
