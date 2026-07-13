"""Public reporting facade and reactive-state export helpers.

Provides utilities for reporting (such as PDF reports generated in Shiny dashboard)
and for saving and retrieving client input data within the Shiny reactives data
structure (``reactives_shiny["Data_Clients"]``), as well as subtab results data
within ``reactives_shiny["Data_Results"]``.

The public module keeps the long-lived import surface stable while delegating
client-info JSON assembly to ``_utils_reporting_client_info`` and the
``Data_Results`` plus SVG-export helpers to ``_utils_reporting_results``.

The ``Data_Clients`` category in the reactives_shiny structure has the following
nested layout::

    {
        "Single_Or_Couple": reactive.Value("Single" | "Couple"),
        "Client_Primary": {
            "Personal_Info": reactive.Value(pl.DataFrame | None),
            "Assets": reactive.Value(pl.DataFrame | None),
            "Goals": reactive.Value(pl.DataFrame | None),
            "Income": reactive.Value(pl.DataFrame | None),
        },
        "Client_Partner": {
            "Personal_Info": reactive.Value(pl.DataFrame | None),
            "Assets": reactive.Value(pl.DataFrame | None),
            "Goals": reactive.Value(pl.DataFrame | None),
            "Income": reactive.Value(pl.DataFrame | None),
        },
        "Clients_Combined": {
            "Assets": reactive.Value(pl.DataFrame | None),
            "Goals": reactive.Value(pl.DataFrame | None),
            "Income": reactive.Value(pl.DataFrame | None),
        },
    }

The ``Data_Results`` category in the reactives_shiny structure has the following
flat layout (one reactive.Value per subtab/direction combination)::

    {
        "Portfolio_Analysis_Inputs": reactive.Value(None),
        "Portfolio_Analysis_Outputs": reactive.Value(None),
        "Portfolio_Comparison_Inputs": reactive.Value(None),
        "Portfolio_Comparison_Outputs": reactive.Value(None),
        "Weights_Analysis_Inputs": reactive.Value(None),
        "Weights_Analysis_Outputs": reactive.Value(None),
        "Portfolio_Optimization_Skfolio_Inputs": reactive.Value(None),
        "Portfolio_Optimization_Skfolio_Outputs": reactive.Value(None),
        "Portfolio_Optimization_OptimalPortfolios_Inputs": reactive.Value(None),
        "Portfolio_Optimization_OptimalPortfolios_Outputs": reactive.Value(None),
        "Portfolio_Simulation_Inputs": reactive.Value(None),
        "Portfolio_Simulation_Outputs": reactive.Value(None),
    }
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from src.dashboard.shiny_utils._utils_reporting_client_info import (
    build_client_info_json_from_reactives,
)
from src.dashboard.shiny_utils._utils_reporting_results import (
    VALID_RESULTS_SUBTAB_KEYS,
    _OUTPUTS_IMAGES_DIR,
    _VISUAL_OBJECT_SVG_FILENAMES,
    _coerce_results_value_to_json,
    build_results_data_json_from_reactives,
    export_visual_objects_to_svg,
    get_results_data_from_reactives,
    save_portfolio_analysis_inputs_to_reactives,
    save_portfolio_analysis_outputs_to_reactives,
    save_portfolio_comparison_inputs_to_reactives,
    save_portfolio_comparison_outputs_to_reactives,
    save_portfolio_optimization_optimalportfolios_inputs_to_reactives,
    save_portfolio_optimization_optimalportfolios_outputs_to_reactives,
    save_portfolio_optimization_skfolio_inputs_to_reactives,
    save_portfolio_optimization_skfolio_outputs_to_reactives,
    save_portfolio_simulation_inputs_to_reactives,
    save_portfolio_simulation_outputs_to_reactives,
    save_results_data_to_reactives,
    save_weights_analysis_inputs_to_reactives,
    save_weights_analysis_outputs_to_reactives,
    validate_data_results_in_reactives,
    validate_results_subtab_key,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)

#: Valid client levels within the Data_Clients structure
VALID_CLIENT_LEVELS: frozenset[str] = frozenset(
    ["Client_Primary", "Client_Partner", "Clients_Combined"],
)

#: Valid data categories for a single client (primary or partner)
VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT: frozenset[str] = frozenset(
    ["Personal_Info", "Assets", "Goals", "Income"],
)

#: Valid data categories for combined client data (no Personal_Info)
VALID_CLIENT_DATA_CATEGORIES_COMBINED: frozenset[str] = frozenset(
    ["Assets", "Goals", "Income"],
)

#: Allowed values for the Single_Or_Couple indicator
VALID_SINGLE_OR_COUPLE_VALUES: frozenset[str] = frozenset(["Single", "Couple"])


def validate_data_clients_in_reactives(*, reactives_shiny: Any) -> tuple[bool, str]:
    """Validate that the Data_Clients category exists and has the required structure.

    Checks that ``reactives_shiny["Data_Clients"]`` is present, is a dictionary,
    contains ``Single_Or_Couple`` and the three sub-level keys (``Client_Primary``,
    ``Client_Partner``, ``Clients_Combined``), each of which is itself a dictionary.

    Args:
        reactives_shiny: Dictionary containing reactive values organized by category.

    Returns
    -------
        tuple[bool, str]: ``(True, "")`` when the structure is valid, or
        ``(False, error_message)`` with a descriptive error message otherwise.
    """
    # Input validation with early returns
    if reactives_shiny is None:
        return False, "reactives_shiny dictionary cannot be None"

    if not isinstance(reactives_shiny, dict):
        return (
            False,
            f"reactives_shiny must be a dictionary, got {type(reactives_shiny).__name__}",
        )

    # Configuration validation - Data_Clients category must exist
    if "Data_Clients" not in reactives_shiny:
        available_categories = list(reactives_shiny.keys())
        return (
            False,
            f"'Data_Clients' category not found in reactives_shiny. "
            f"Available categories: {available_categories}",
        )

    data_clients = reactives_shiny["Data_Clients"]

    if not isinstance(data_clients, dict):
        return (
            False,
            f"'Data_Clients' must be a dictionary, got {type(data_clients).__name__}",
        )

    # Business logic validation - Single_Or_Couple must exist
    if "Single_Or_Couple" not in data_clients:
        available_keys = list(data_clients.keys())
        return (
            False,
            f"'Single_Or_Couple' key not found in Data_Clients. Available keys: {available_keys}",
        )

    # Business logic validation - sub-level dicts must exist and be dicts
    required_sub_levels = ["Client_Primary", "Client_Partner", "Clients_Combined"]
    for sub_level_name in required_sub_levels:
        if sub_level_name not in data_clients:
            available_keys = list(data_clients.keys())
            return (
                False,
                f"Sub-level '{sub_level_name}' not found in Data_Clients. "
                f"Available keys: {available_keys}",
            )
        if not isinstance(data_clients[sub_level_name], dict):
            return (
                False,
                f"Sub-level '{sub_level_name}' in Data_Clients must be a dictionary, "
                f"got {type(data_clients[sub_level_name]).__name__}",
            )

    return True, ""


def validate_client_level_name(*, client_level: Any) -> tuple[bool, str]:
    """Validate that the provided client level name is one of the allowed sub-levels.

    The allowed sub-levels mirror the three keys inside ``Data_Clients``:
    ``"Client_Primary"``, ``"Client_Partner"``, and ``"Clients_Combined"``.

    Args:
        client_level: The client level name to validate.

    Returns
    -------
        tuple[bool, str]: ``(True, "")`` when valid, or
        ``(False, error_message)`` when invalid.
    """
    # Input validation with early returns
    if client_level is None:
        return False, "client_level cannot be None"

    if not isinstance(client_level, str):
        return False, f"client_level must be a string, got {type(client_level).__name__}"

    if len(client_level.strip()) == 0:
        return False, "client_level cannot be an empty string"

    # Business logic validation
    if client_level not in VALID_CLIENT_LEVELS:
        return (
            False,
            f"Invalid client_level '{client_level}'. Valid levels: {sorted(VALID_CLIENT_LEVELS)}",
        )

    return True, ""


def validate_client_data_category_name(
    *, data_category: Any, client_level: Any = None) -> tuple[bool, str]:
    """Validate that the data category is allowed for the given client level.

    ``"Personal_Info"`` is only valid for ``"Client_Primary"`` and
    ``"Client_Partner"``, not for ``"Clients_Combined"``.

    Args:
        data_category: The data category name to validate (e.g. ``"Personal_Info"``,
            ``"Assets"``, ``"Goals"``, ``"Income"``).
        client_level: Optional client level used to apply level-specific
            category restrictions.  When ``None`` the broader set of all
            categories is accepted.

    Returns
    -------
        tuple[bool, str]: ``(True, "")`` when valid, or
        ``(False, error_message)`` when invalid.
    """
    # Input validation with early returns
    if data_category is None:
        return False, "data_category cannot be None"

    if not isinstance(data_category, str):
        return False, f"data_category must be a string, got {type(data_category).__name__}"

    if len(data_category.strip()) == 0:
        return False, "data_category cannot be an empty string"

    # Business logic validation - apply level-specific restrictions
    if client_level == "Clients_Combined":
        if data_category not in VALID_CLIENT_DATA_CATEGORIES_COMBINED:
            return (
                False,
                f"Invalid data_category '{data_category}' for 'Clients_Combined'. "
                f"Valid categories: {sorted(VALID_CLIENT_DATA_CATEGORIES_COMBINED)}",
            )
    else:
        # For Client_Primary, Client_Partner, or unknown level use the full set
        all_valid = VALID_CLIENT_DATA_CATEGORIES_PER_CLIENT | VALID_CLIENT_DATA_CATEGORIES_COMBINED
        if data_category not in all_valid:
            return (
                False,
                f"Invalid data_category '{data_category}'. Valid categories: {sorted(all_valid)}",
            )

    return True, ""


def get_single_or_couple_from_reactives(*, reactives_shiny: Any) -> str:
    """Retrieve the Single_Or_Couple indicator from the reactives data structure.

    Reads ``reactives_shiny["Data_Clients"]["Single_Or_Couple"]`` and returns its
    current value (either ``"Single"`` or ``"Couple"``).

    Args:
        reactives_shiny: Dictionary containing reactive values organized by category.

    Returns
    -------
        str: ``"Single"`` when the household has only a primary client, or
        ``"Couple"`` when it includes both a primary and a partner client.

    Raises
    ------
        ValueError: If the reactives structure is invalid or the reactive value is missing.
        RuntimeError: If the reactive value cannot be retrieved.
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_clients_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Clients structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Business logic validation - retrieve Single_Or_Couple reactive
    reactive_single_or_couple = reactives_shiny["Data_Clients"]["Single_Or_Couple"]

    if reactive_single_or_couple is None:
        error_message = (
            "Reactive variable 'Single_Or_Couple' in Data_Clients is None - "
            "it was not properly initialized"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if not hasattr(reactive_single_or_couple, "get"):
        error_message = (
            f"Reactive variable 'Single_Or_Couple' in Data_Clients does not have a 'get' method. "
            f"Object type: {type(reactive_single_or_couple).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Only use try-except for unpredictable reactive access
    try:
        value = reactive_single_or_couple.get()
        _logger.debug(
            "Retrieved Single_Or_Couple from reactives",
            extra={"single_or_couple": value},
        )
        return value if value is not None else "Single"

    except Exception as exc:
        error_message = f"Unexpected error retrieving 'Single_Or_Couple' from Data_Clients: {exc}"
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def update_single_or_couple_in_reactives(
    *, reactives_shiny: Any, single_or_couple: Any) -> dict:
    """Update the Single_Or_Couple indicator in the reactives data structure.

    Sets ``reactives_shiny["Data_Clients"]["Single_Or_Couple"]`` to the provided
    value, which must be either ``"Single"`` or ``"Couple"``.

    Args:
        reactives_shiny: Dictionary containing reactive values organized by category.
        single_or_couple: New value to store.  Must be ``"Single"`` or ``"Couple"``.

    Returns
    -------
        dict: The updated reactives_shiny dictionary.

    Raises
    ------
        ValueError: If the reactives structure or the provided value is invalid.
        RuntimeError: If the reactive value cannot be updated.
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_clients_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Clients structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if single_or_couple is None:
        error_message = "single_or_couple value cannot be None"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if not isinstance(single_or_couple, str):
        error_message = f"single_or_couple must be a string, got {type(single_or_couple).__name__}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Business logic validation - must be "Single" or "Couple"
    if single_or_couple not in VALID_SINGLE_OR_COUPLE_VALUES:
        error_message = (
            f"Invalid single_or_couple value '{single_or_couple}'. "
            f"Valid values: {sorted(VALID_SINGLE_OR_COUPLE_VALUES)}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    reactive_single_or_couple = reactives_shiny["Data_Clients"]["Single_Or_Couple"]

    if not hasattr(reactive_single_or_couple, "set"):
        error_message = (
            f"Reactive variable 'Single_Or_Couple' does not have a 'set' method. "
            f"Object type: {type(reactive_single_or_couple).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Only use try-except for unpredictable reactive access
    try:
        reactive_single_or_couple.set(single_or_couple)
        _logger.debug(
            "Updated Single_Or_Couple in reactives",
            extra={"single_or_couple": single_or_couple},
        )
        return reactives_shiny

    except Exception as exc:
        error_message = (
            f"Unexpected error updating 'Single_Or_Couple' to '{single_or_couple}': {exc}"
        )
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def get_client_data_from_reactives(
    *, reactives_shiny: Any, client_level: Any, data_category: Any) -> pl.DataFrame | None:
    """Retrieve client input data stored at a specific level and category in reactives.

    Accesses ``reactives_shiny["Data_Clients"][client_level][data_category]`` and
    returns the current reactive value (a Polars DataFrame or ``None``).

    Args:
        reactives_shiny: Dictionary containing reactive values organized by category.
        client_level: Sub-level key.  One of ``"Client_Primary"``,
            ``"Client_Partner"``, or ``"Clients_Combined"``.
        data_category: Data category key.  One of ``"Personal_Info"``, ``"Assets"``,
            ``"Goals"``, ``"Income"`` (``"Personal_Info"`` is not valid for
            ``"Clients_Combined"``).

    Returns
    -------
        pl.DataFrame | None: The stored Polars DataFrame, or ``None`` when no data
        has been saved yet for the given level / category combination.

    Raises
    ------
        ValueError: If the reactives structure, client_level, or data_category is invalid.
        KeyError: If the requested key is not found inside the sub-level dictionary.
        RuntimeError: If the reactive value cannot be retrieved.
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_clients_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Clients structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_client_level_name(client_level = client_level)
    if not validation_result:
        error_message = f"Client level validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_client_data_category_name(
        data_category = data_category,
        client_level = client_level,
    )
    if not validation_result:
        error_message = f"Data category validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Configuration validation - sub-level dict must contain requested category
    sub_level_dict = reactives_shiny["Data_Clients"][client_level]

    if data_category not in sub_level_dict:
        available_categories = list(sub_level_dict.keys())
        error_message = (
            f"Data category '{data_category}' not found in Data_Clients['{client_level}']. "
            f"Available categories: {available_categories}"
        )
        _logger.error(error_message)
        raise KeyError(error_message)

    reactive_variable = sub_level_dict[data_category]

    # Business logic validation
    if reactive_variable is None:
        error_message = (
            f"Reactive variable at Data_Clients['{client_level}']['{data_category}'] is None - "
            f"it was not properly initialized"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if not hasattr(reactive_variable, "get"):
        error_message = (
            f"Reactive variable at Data_Clients['{client_level}']['{data_category}'] "
            f"does not have a 'get' method. "
            f"Object type: {type(reactive_variable).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Only use try-except for unpredictable reactive access
    try:
        retrieved_value = reactive_variable.get()
        _logger.debug(
            "Retrieved client data from reactives",
            extra={
                "client_level": client_level,
                "data_category": data_category,
                "value_type": type(retrieved_value).__name__,
            },
        )
        return retrieved_value

    except Exception as exc:
        error_message = (
            f"Unexpected error retrieving Data_Clients['{client_level}']['{data_category}']: {exc}"
        )
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def save_client_data_to_reactives(
    *, reactives_shiny: Any, client_level: Any, data_category: Any, data_value: Any) -> dict:
    """Save client input data to a specific level and category in the reactives structure.

    Sets ``reactives_shiny["Data_Clients"][client_level][data_category]`` to the
    provided Polars DataFrame (or ``None`` to clear a previously stored value).

    Args:
        reactives_shiny: Dictionary containing reactive values organized by category.
        client_level: Sub-level key.  One of ``"Client_Primary"``,
            ``"Client_Partner"``, or ``"Clients_Combined"``.
        data_category: Data category key.  One of ``"Personal_Info"``, ``"Assets"``,
            ``"Goals"``, ``"Income"`` (``"Personal_Info"`` is not valid for
            ``"Clients_Combined"``).
        data_value: Polars DataFrame to store, or ``None`` to clear the entry.

    Returns
    -------
        dict: The updated reactives_shiny dictionary.

    Raises
    ------
        ValueError: If the reactives structure, client_level, data_category, or
            data_value type is invalid.
        KeyError: If the requested key is not found inside the sub-level dictionary.
        RuntimeError: If the reactive value cannot be updated.
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_clients_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Clients structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_client_level_name(client_level = client_level)
    if not validation_result:
        error_message = f"Client level validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_client_data_category_name(
        data_category = data_category,
        client_level = client_level,
    )
    if not validation_result:
        error_message = f"Data category validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Business logic validation - data_value must be a pl.DataFrame or None
    if data_value is not None and not isinstance(data_value, pl.DataFrame):
        error_message = (
            f"data_value must be a Polars DataFrame or None, got {type(data_value).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Configuration validation - sub-level dict must contain requested category
    sub_level_dict = reactives_shiny["Data_Clients"][client_level]

    if data_category not in sub_level_dict:  # pragma: no cover
        available_categories = list(sub_level_dict.keys())
        error_message = (
            f"Data category '{data_category}' not found in Data_Clients['{client_level}']. "
            f"Available categories: {available_categories}"
        )
        _logger.error(error_message)
        raise KeyError(error_message)

    reactive_variable = sub_level_dict[data_category]

    if reactive_variable is None:
        error_message = (
            f"Reactive variable at Data_Clients['{client_level}']['{data_category}'] is None - "
            f"it was not properly initialized"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if not hasattr(reactive_variable, "set"):
        error_message = (
            f"Reactive variable at Data_Clients['{client_level}']['{data_category}'] "
            f"does not have a 'set' method. "
            f"Object type: {type(reactive_variable).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Only use try-except for unpredictable reactive access
    try:
        reactive_variable.set(data_value)
        value_shape = data_value.shape if data_value is not None else None
        _logger.debug(
            "Saved client data to reactives",
            extra={
                "client_level": client_level,
                "data_category": data_category,
                "data_shape": str(value_shape),
            },
        )
        return reactives_shiny

    except Exception as exc:
        error_message = (
            f"Unexpected error saving data to "
            f"Data_Clients['{client_level}']['{data_category}']: {exc}"
        )
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def save_client_personal_info_to_reactives(
    *, reactives_shiny: Any, client_level: Any, data_personal_info: Any) -> dict:
    """Save personal information data for a client to the reactives structure.

    Convenience wrapper around :func:`save_client_data_to_reactives` that fixes
    ``data_category`` to ``"Personal_Info"``.  Valid only for ``"Client_Primary"``
    and ``"Client_Partner"`` (not ``"Clients_Combined"``).

    Parameters
    ----------
    reactives_shiny : Any
        Dictionary containing reactive values organized by category.
    client_level : Any
        Sub-level key. Must be ``"Client_Primary"`` or ``"Client_Partner"``;
        ``"Clients_Combined"`` is not accepted.
    data_personal_info : Any
        Polars DataFrame containing personal-information fields, or ``None``
        to clear the entry.

    Returns
    -------
    dict
        The updated ``reactives_shiny`` dictionary.

    Raises
    ------
    ValueError
        If ``client_level`` is ``"Clients_Combined"`` or any other validation
        fails. See :func:`save_client_data_to_reactives`.
    RuntimeError
        If the reactive value cannot be updated.
    """
    # Business logic validation - Personal_Info is not valid for Clients_Combined
    if client_level == "Clients_Combined":
        error_message = (
            "'Personal_Info' data category is not valid for 'Clients_Combined'. "
            "Use 'Client_Primary' or 'Client_Partner' instead."
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    return save_client_data_to_reactives(
        reactives_shiny = reactives_shiny,
        client_level = client_level,
        data_category = "Personal_Info",
        data_value = data_personal_info,
    )


def save_client_assets_to_reactives(
    *, reactives_shiny: Any, client_level: Any, data_assets: Any) -> dict:
    """Save assets data for a client (or the combined household) to the reactives structure.

    Convenience wrapper around :func:`save_client_data_to_reactives` that fixes
    ``data_category`` to ``"Assets"``.  Valid for all three client levels.

    Parameters
    ----------
    reactives_shiny : Any
        Dictionary containing reactive values organized by category.
    client_level : Any
        Sub-level key. One of ``"Client_Primary"``, ``"Client_Partner"``, or
        ``"Clients_Combined"``.
    data_assets : Any
        Polars DataFrame containing asset information, or ``None`` to clear
        the entry.

    Returns
    -------
    dict
        The updated ``reactives_shiny`` dictionary.

    Raises
    ------
    ValueError
        If any validation fails. See :func:`save_client_data_to_reactives`.
    RuntimeError
        If the reactive value cannot be updated.
    """
    return save_client_data_to_reactives(
        reactives_shiny = reactives_shiny,
        client_level = client_level,
        data_category = "Assets",
        data_value = data_assets,
    )


def save_client_goals_to_reactives(
    *, reactives_shiny: Any, client_level: Any, data_goals: Any) -> dict:
    """Save goals data for a client (or the combined household) to the reactives structure.

    Convenience wrapper around :func:`save_client_data_to_reactives` that fixes
    ``data_category`` to ``"Goals"``.  Valid for all three client levels.

    Parameters
    ----------
    reactives_shiny : Any
        Dictionary containing reactive values organized by category.
    client_level : Any
        Sub-level key. One of ``"Client_Primary"``, ``"Client_Partner"``, or
        ``"Clients_Combined"``.
    data_goals : Any
        Polars DataFrame containing goal information, or ``None`` to clear the
        entry.

    Returns
    -------
    dict
        The updated ``reactives_shiny`` dictionary.

    Raises
    ------
    ValueError
        If any validation fails. See :func:`save_client_data_to_reactives`.
    RuntimeError
        If the reactive value cannot be updated.
    """
    return save_client_data_to_reactives(
        reactives_shiny = reactives_shiny,
        client_level = client_level,
        data_category = "Goals",
        data_value = data_goals,
    )


def save_client_income_to_reactives(
    *, reactives_shiny: Any, client_level: Any, data_income: Any) -> dict:
    """Save income data for a client (or the combined household) to the reactives structure.

    Convenience wrapper around :func:`save_client_data_to_reactives` that fixes
    ``data_category`` to ``"Income"``.  Valid for all three client levels.

    Parameters
    ----------
    reactives_shiny : Any
        Dictionary containing reactive values organized by category.
    client_level : Any
        Sub-level key. One of ``"Client_Primary"``, ``"Client_Partner"``, or
        ``"Clients_Combined"``.
    data_income : Any
        Polars DataFrame containing income information, or ``None`` to clear
        the entry.

    Returns
    -------
    dict
        The updated ``reactives_shiny`` dictionary.

    Raises
    ------
    ValueError
        If any validation fails. See :func:`save_client_data_to_reactives`.
    RuntimeError
        If the reactive value cannot be updated.
    """
    return save_client_data_to_reactives(
        reactives_shiny = reactives_shiny,
        client_level = client_level,
        data_category = "Income",
        data_value = data_income,
    )


def save_clients_combined_data_to_reactives(
    *, reactives_shiny: Any, data_category: Any, data_value: Any) -> dict:
    """Save combined household data to the Clients_Combined sub-level in the reactives structure.

    Convenience wrapper around :func:`save_client_data_to_reactives` that fixes
    ``client_level`` to ``"Clients_Combined"``.  Only ``"Assets"``, ``"Goals"``,
    and ``"Income"`` are accepted as ``data_category`` values (``"Personal_Info"``
    is not valid at the combined level).

    Parameters
    ----------
    reactives_shiny : Any
        Dictionary containing reactive values organized by category.
    data_category : Any
        Data category key. One of ``"Assets"``, ``"Goals"``, or ``"Income"``.
    data_value : Any
        Polars DataFrame containing the combined data, or ``None`` to clear
        the entry.

    Returns
    -------
    dict
        The updated ``reactives_shiny`` dictionary.

    Raises
    ------
    ValueError
        If ``data_category`` is ``"Personal_Info"`` or any other validation
        fails. See :func:`save_client_data_to_reactives`.
    RuntimeError
        If the reactive value cannot be updated.
    """
    return save_client_data_to_reactives(
        reactives_shiny = reactives_shiny,
        client_level = "Clients_Combined",
        data_category = data_category,
        data_value = data_value,
    )
