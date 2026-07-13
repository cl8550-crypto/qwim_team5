"""Utility functions for client tab operations.

Provides validation, data processing, and formatting functions specifically
for client-related dashboard operations including personal info, assets, and goals.
"""

from __future__ import annotations

import contextlib
import locale

from typing import Any

from shiny import reactive

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._utils_tab_clients_sync import (
    _apply_partner_blanking,
    _blank_partner_section,
    _parse_currency_string,
    sync_user_inputs_shiny_from_extracted_worksheet,
)


_logger = get_logger(name = __name__)


# Set locale for currency formatting to ensure consistent display
# across different system configurations
try:
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
except locale.Error:  # pragma: no cover
    # Fallback for systems without UTF-8 support
    with contextlib.suppress(locale.Error):
        # Use system default if US locale unavailable
        locale.setlocale(locale.LC_ALL, "en_US")

# Import data access utilities
try:
    from src.dashboard.shiny_utils.reactives_shiny import get_value_from_reactives_shiny

    DATA_UTILS_AVAILABLE = True
    _logger.debug("reactives_shiny utilities imported successfully in utils_tab_clients")
except ImportError as import_error:  # pragma: no cover
    _logger.warning(
        "reactives_shiny utilities import failed in utils_tab_clients: %s",
        import_error,
    )
    DATA_UTILS_AVAILABLE = False

    # Fallback function for defensive programming
    def get_value_from_reactives_shiny(
        *, reactives_shiny: dict, key_name: str, key_category: str) -> None:
        """Fallback getter used when reactives_shiny utilities are unavailable."""
        _logger.warning("Fallback: Unable to retrieve %s from %s", key_name, key_category)
        return


def format_currency_display(*, amount_value: Any) -> str | None:
    """Format a numeric amount as whole-dollar currency and reject booleans."""
    if amount_value is None:
        return "$0"

    if isinstance(amount_value, bool):
        raise Exception_Validation_Input(
            f"Invalid amount for currency formatting: {amount_value}",
        )

    try:
        amount_value = float(amount_value)
        return f"${amount_value:,.0f}"
    except (ValueError, TypeError):
        raise Exception_Validation_Input(f"Invalid amount for currency formatting: {amount_value}")


def validate_financial_amount(*, amount_value: Any) -> Any:
    """Validate a non-negative financial amount and reject booleans."""
    if amount_value is None:
        return 0.0

    if isinstance(amount_value, bool):
        raise Exception_Validation_Input(f"Invalid financial amount: {amount_value}")

    try:
        amount_value = float(amount_value)
        if amount_value < 0:
            raise Exception_Validation_Input("Financial amount cannot be negative")
        return amount_value
    except (ValueError, TypeError) as exc_error:
        if "negative" in str(exc_error):
            raise exc_error  # pragma: no cover
        raise Exception_Validation_Input(f"Invalid financial amount: {amount_value}")


def _coerce_dashboard_financial_value(*, amount_value: Any) -> float:
    """Coerce dashboard financial inputs while keeping booleans on the default path."""
    if isinstance(amount_value, bool):
        return 0.0

    return validate_financial_amount(amount_value = amount_value)


def validate_age_range(
    *, age_value: int | str | None, minimum_age: int | None = None, maximum_age: int | None = None, age_type_description: str = "Age", min_age: int | None = None, max_age: int | None = None) -> int:
    """Validate an age against the supported min/max parameter aliases."""
    # Resolve parameter name aliases
    eff_min = minimum_age if minimum_age is not None else min_age
    eff_max = maximum_age if maximum_age is not None else max_age

    if eff_min is None:
        raise Exception_Validation_Input("min_age or minimum_age must be provided")
    if eff_max is None:
        raise Exception_Validation_Input("max_age or maximum_age must be provided")

    if age_value is None:
        raise Exception_Validation_Input(f"{age_type_description} cannot be empty")

    if isinstance(age_value, bool):
        raise Exception_Validation_Input(f"Invalid {age_type_description}: {age_value}")

    try:
        age_value = int(age_value)
        if age_value < eff_min or age_value > eff_max:
            raise Exception_Validation_Input(
                f"{age_type_description} must be between {eff_min} and {eff_max}",
            )
        return age_value
    except (ValueError, TypeError) as exc_error:
        if "between" in str(exc_error):
            raise exc_error  # pragma: no cover
        raise Exception_Validation_Input(f"Invalid {age_type_description}: {age_value}")


def _coerce_dashboard_age_default(
    *, age_value: Any, default_age: int) -> Any:
    """Keep dashboard age defaults stable when reactive values are boolean."""
    if isinstance(age_value, bool):
        return default_age

    return age_value or default_age


def validate_string_input(
    *, input_value: str | None, field_description: str = "Field") -> str:
    """Validate that a required string input is present and trimmed."""
    if input_value is None or str(input_value).strip() == "":
        raise Exception_Validation_Input(f"{field_description} cannot be empty")

    return str(input_value).strip()


def get_investor_data_from_dashboard(
    *, reactives_shiny: dict) -> tuple[dict, dict, dict, dict]:
    """Extract personal, asset, goal, and income dictionaries from dashboard reactives."""
    try:
        _logger.debug("Starting comprehensive investor data retrieval from dashboard")

        # Input validation with early returns
        if not reactives_shiny or not isinstance(reactives_shiny, dict):
            Error_Message = "Invalid reactives_shiny structure - must be a non-empty dictionary"
            _logger.error("Input validation error: %s", Error_Message)
            raise Exception_Validation_Input(Error_Message)

        # Configuration validation - check if data utilities are available
        if not DATA_UTILS_AVAILABLE:  # pragma: no cover
            Error_Message = "Data utilities not available - reactives_shiny module failed to import"
            _logger.error("Configuration error: %s", Error_Message)
            raise Exception_Configuration(Error_Message)

        # Business logic validation - check if User_Inputs_Shiny category exists
        if "User_Inputs_Shiny" not in reactives_shiny:
            Error_Message = f"User_Inputs_Shiny category not found in reactives_shiny. Available categories: {list(reactives_shiny.keys())}"
            _logger.error("Key error: %s", Error_Message)
            raise KeyError(Error_Message)

        _logger.debug("Retrieving primary investor personal information...")
        # Primary Investor Personal Information
        primary_personal_info = get_investor_primary_personal_info(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving partner investor personal information...")
        # Partner Investor Personal Information
        partner_personal_info = get_investor_partner_personal_info(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving primary investor assets...")
        # Primary Investor Assets
        primary_assets = get_investor_primary_assets(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving partner investor assets...")
        # Partner Investor Assets
        partner_assets = get_investor_partner_assets(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving primary investor goals...")
        # Primary Investor Goals
        primary_goals = get_investor_primary_goals(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving partner investor goals...")
        # Partner Investor Goals
        partner_goals = get_investor_partner_goals(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving primary investor income...")
        # Primary Investor Income
        primary_income = get_investor_primary_income(reactives_shiny = reactives_shiny)

        _logger.debug("Retrieving partner investor income...")
        # Partner Investor Income
        partner_income = get_investor_partner_income(reactives_shiny = reactives_shiny)

        _logger.debug("Calculating totals and combined values...")
        # Calculate totals with defensive programming
        _calculate_individual_totals(
            primary_assets = primary_assets,
            partner_assets = partner_assets,
            primary_goals = primary_goals,
            partner_goals = partner_goals,
            primary_income = primary_income,
            partner_income = partner_income,
        )

        # Calculate combined totals
        combined_assets = _calculate_combined_assets(primary_assets = primary_assets, partner_assets = partner_assets)
        combined_goals = _calculate_combined_goals(primary_goals = primary_goals, partner_goals = partner_goals)
        combined_income = _calculate_combined_income(primary_income = primary_income, partner_income = partner_income)

        # Structure the data for return
        personal_info_data = {
            "primary": primary_personal_info,
            "partner": partner_personal_info,
        }

        assets_data = {
            "primary": primary_assets,
            "partner": partner_assets,
            "combined": combined_assets,
        }

        goals_data = {
            "primary": primary_goals,
            "partner": partner_goals,
            "combined": combined_goals,
        }

        income_data = {
            "primary": primary_income,
            "partner": partner_income,
            "combined": combined_income,
        }

        _logger.debug("Successfully retrieved comprehensive investor data from dashboard")
        _logger.debug("Primary investor: %s", primary_personal_info["name"])
        _logger.debug("Partner investor: %s", partner_personal_info["name"])
        _logger.debug("Primary total assets: $%s", f"{primary_assets['total']:,.0f}")
        _logger.debug("Partner total assets: $%s", f"{partner_assets['total']:,.0f}")
        _logger.debug("Combined total assets: $%s", f"{combined_assets['total']:,.0f}")
        _logger.debug("Primary total goals: $%s", f"{primary_goals['total']:,.0f}")
        _logger.debug("Partner total goals: $%s", f"{partner_goals['total']:,.0f}")
        _logger.debug("Combined total goals: $%s", f"{combined_goals['total']:,.0f}")
        _logger.debug("Primary total income: $%s", f"{primary_income['total']:,.0f}")
        _logger.debug("Partner total income: $%s", f"{partner_income['total']:,.0f}")
        _logger.debug("Combined total income: $%s", f"{combined_income['total']:,.0f}")

        return personal_info_data, assets_data, goals_data, income_data

    except (ValueError, RuntimeError, KeyError) as known_error:
        # Re-raise known errors with context
        _logger.opt(exception=True).error(
            "Known error during investor data retrieval: {}",
            known_error,
        )
        raise known_error

    except Exception as data_error:
        Error_Message = (
            f"Unexpected error occurred during comprehensive investor data retrieval: {data_error}"
        )
        _logger.opt(exception=True).error(
            "Unexpected error during comprehensive investor data retrieval: {}",
            Error_Message,
        )
        raise Exception_Configuration(Error_Message) from data_error


def get_investor_primary_personal_info(*, reactives_shiny: dict) -> dict:
    """
    Retrieve primary client personal information from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Primary client personal information
    """
    age_current = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current",
        key_category="User_Inputs_Shiny",
    )
    age_retirement = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement",
        key_category="User_Inputs_Shiny",
    )
    age_income_starting = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting",
        key_category="User_Inputs_Shiny",
    )

    return {
        "name": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name",
            key_category="User_Inputs_Shiny",
        )
        or "Primary Client",
        "age_current": _coerce_dashboard_age_default(age_value = age_current, default_age = 35),
        "age_retirement": _coerce_dashboard_age_default(age_value = age_retirement, default_age = 65),
        "age_income_starting": _coerce_dashboard_age_default(age_value = age_income_starting, default_age = 65),
        "status_marital": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Status_Marital",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "gender": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Gender",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "tolerance_risk": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Tolerance_Risk",
            key_category="User_Inputs_Shiny",
        )
        or "Moderate",
        "state": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_State",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "code_zip": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Code_Zip",
            key_category="User_Inputs_Shiny",
        )
        or "00000",
    }


def get_investor_partner_personal_info(*, reactives_shiny: dict) -> dict:
    """
    Retrieve partner client personal information from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Partner client personal information
    """
    age_current = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current",
        key_category="User_Inputs_Shiny",
    )
    age_retirement = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement",
        key_category="User_Inputs_Shiny",
    )
    age_income_starting = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting",
        key_category="User_Inputs_Shiny",
    )

    return {
        "name": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name",
            key_category="User_Inputs_Shiny",
        )
        or "Partner Client",
        "age_current": _coerce_dashboard_age_default(age_value = age_current, default_age = 33),
        "age_retirement": _coerce_dashboard_age_default(age_value = age_retirement, default_age = 65),
        "age_income_starting": _coerce_dashboard_age_default(age_value = age_income_starting, default_age = 65),
        "status_marital": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Status_Marital",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "gender": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Gender",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "tolerance_risk": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Tolerance_Risk",
            key_category="User_Inputs_Shiny",
        )
        or "Moderate",
        "state": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_State",
            key_category="User_Inputs_Shiny",
        )
        or "Not Specified",
        "code_zip": get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Code_Zip",
            key_category="User_Inputs_Shiny",
        )
        or "00000",
    }


def get_investor_primary_assets(*, reactives_shiny: dict) -> dict:
    """
    Retrieve primary investor assets from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Primary investor assets by category
    """
    return {
        "taxable": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "tax_deferred": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Deferred",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "tax_free": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Free",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


def get_investor_partner_assets(*, reactives_shiny: dict) -> dict:
    """
    Retrieve partner investor assets from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Partner investor assets by category
    """
    return {
        "taxable": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "tax_deferred": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "tax_free": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


def get_investor_primary_goals(*, reactives_shiny: dict) -> dict:
    """
    Retrieve primary investor goals from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Primary investor goals by priority level
    """
    return {
        "essential": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "important": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Important",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "aspirational": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Aspirational",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


def get_investor_partner_goals(*, reactives_shiny: dict) -> dict:
    """
    Retrieve partner investor goals from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Partner investor goals by priority level
    """
    return {
        "essential": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Essential",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "important": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Important",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "aspirational": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Aspirational",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


def get_investor_primary_income(*, reactives_shiny: dict) -> dict:
    """
    Retrieve primary investor income from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Primary investor income by source category
    """
    return {
        "social_security": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "pension": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "annuity_existing": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Annuity_Existing",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "other": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Other",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


def get_investor_partner_income(*, reactives_shiny: dict) -> dict:
    """
    Retrieve partner investor income from dashboard inputs.

    Args:
        reactives_shiny (dict): Reactive values structure

    Returns
    -------
        dict: Partner investor income by source category
    """
    return {
        "social_security": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Social_Security",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "pension": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Pension",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "annuity_existing": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Annuity_Existing",
                key_category="User_Inputs_Shiny",
            ),
        ),
        "other": _coerce_dashboard_financial_value(
            amount_value = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other",
                key_category="User_Inputs_Shiny",
            ),
        ),
    }


# Observer functions for reactive behavior in the dashboard
@reactive.effect
def observer_get_investor_primary_personal_info() -> None:
    """Observer for primary investor personal information changes."""


@reactive.effect
def observer_get_investor_partner_personal_info() -> None:
    """Observer for partner investor personal information changes."""


@reactive.effect
def observer_get_investor_primary_assets() -> None:
    """Observer for primary investor assets changes."""


@reactive.effect
def observer_get_investor_partner_assets() -> None:
    """Observer for partner investor assets changes."""


@reactive.effect
def observer_get_investor_primary_goals() -> None:
    """Observer for primary investor goals changes."""


@reactive.effect
def observer_get_investor_partner_goals() -> None:
    """Observer for partner investor goals changes."""


@reactive.effect
def observer_get_investor_primary_income() -> None:
    """Observer for primary investor income changes."""


@reactive.effect
def observer_get_investor_partner_income() -> None:
    """Observer for partner investor income changes."""


def _calculate_individual_totals(
    *, primary_assets: dict, partner_assets: dict, primary_goals: dict, partner_goals: dict, primary_income: dict, partner_income: dict) -> None:
    """
    Calculate individual totals for assets, goals, and income.

    Args:
        primary_assets (dict): Primary investor assets
        partner_assets (dict): Partner investor assets
        primary_goals (dict): Primary investor goals
        partner_goals (dict): Partner investor goals
        primary_income (dict): Primary investor income
        partner_income (dict): Partner investor income
    """
    try:
        # Asset totals
        primary_assets["total"] = (
            primary_assets["taxable"] + primary_assets["tax_deferred"] + primary_assets["tax_free"]
        )
        partner_assets["total"] = (
            partner_assets["taxable"] + partner_assets["tax_deferred"] + partner_assets["tax_free"]
        )

        # Goals totals
        primary_goals["total"] = (
            primary_goals["essential"] + primary_goals["important"] + primary_goals["aspirational"]
        )
        partner_goals["total"] = (
            partner_goals["essential"] + partner_goals["important"] + partner_goals["aspirational"]
        )

        # Income totals
        primary_income["total"] = (
            primary_income["social_security"]
            + primary_income["pension"]
            + primary_income["annuity_existing"]
            + primary_income["other"]
        )
        partner_income["total"] = (
            partner_income["social_security"]
            + partner_income["pension"]
            + partner_income["annuity_existing"]
            + partner_income["other"]
        )

    except (TypeError, ValueError) as calculation_error:  # pragma: no cover
        _logger.opt(exception=True).warning(
            "Error calculating: {}",
            calculation_error,
        )
        # Set defaults for defensive programming
        primary_assets["total"] = 0.0
        partner_assets["total"] = 0.0
        primary_goals["total"] = 0.0
        partner_goals["total"] = 0.0
        primary_income["total"] = 0.0
        partner_income["total"] = 0.0


def _calculate_combined_assets(
    *, primary_assets: dict, partner_assets: dict) -> dict:
    """
    Calculate combined assets for both investors.

    Args:
        primary_assets (dict): Primary investor assets
        partner_assets (dict): Partner investor assets

    Returns
    -------
        dict: Combined assets by category
    """
    try:
        combined_assets = {
            "taxable": primary_assets["taxable"] + partner_assets["taxable"],
            "tax_deferred": primary_assets["tax_deferred"] + partner_assets["tax_deferred"],
            "tax_free": primary_assets["tax_free"] + partner_assets["tax_free"],
        }
        combined_assets["total"] = (
            combined_assets["taxable"]
            + combined_assets["tax_deferred"]
            + combined_assets["tax_free"]
        )
        return combined_assets
    except (TypeError, ValueError) as calculation_error:  # pragma: no cover
        _logger.opt(exception=True).warning(
            "Error calculating: {}",
            calculation_error,
        )
        return {"taxable": 0.0, "tax_deferred": 0.0, "tax_free": 0.0, "total": 0.0}


def _calculate_combined_goals(
    *, primary_goals: dict, partner_goals: dict) -> dict:
    """
    Calculate combined goals for both investors.

    Args:
        primary_goals (dict): Primary investor goals
        partner_goals (dict): Partner investor goals

    Returns
    -------
        dict: Combined goals by priority level
    """
    try:
        combined_goals = {
            "essential": primary_goals["essential"] + partner_goals["essential"],
            "important": primary_goals["important"] + partner_goals["important"],
            "aspirational": primary_goals["aspirational"] + partner_goals["aspirational"],
        }
        combined_goals["total"] = (
            combined_goals["essential"]
            + combined_goals["important"]
            + combined_goals["aspirational"]
        )
        return combined_goals
    except (TypeError, ValueError) as calculation_error:  # pragma: no cover
        _logger.opt(exception=True).warning(
            "Error calculating: {}",
            calculation_error,
        )
        return {"essential": 0.0, "important": 0.0, "aspirational": 0.0, "total": 0.0}


def _calculate_combined_income(
    *, primary_income: dict, partner_income: dict) -> dict:
    """
    Calculate combined income for both investors.

    Args:
        primary_income (dict): Primary investor income
        partner_income (dict): Partner investor income

    Returns
    -------
        dict: Combined income by source category
    """
    try:
        combined_income = {
            "social_security": primary_income["social_security"]
            + partner_income["social_security"],
            "pension": primary_income["pension"] + partner_income["pension"],
            "annuity_existing": primary_income["annuity_existing"]
            + partner_income["annuity_existing"],
            "other": primary_income["other"] + partner_income["other"],
        }
        combined_income["total"] = (
            combined_income["social_security"]
            + combined_income["pension"]
            + combined_income["annuity_existing"]
            + combined_income["other"]
        )
        return combined_income
    except (TypeError, ValueError) as calculation_error:  # pragma: no cover
        _logger.opt(exception=True).warning(
            "Error calculating: {}",
            calculation_error,
        )
        return {
            "social_security": 0.0,
            "pension": 0.0,
            "annuity_existing": 0.0,
            "other": 0.0,
            "total": 0.0,
        }


