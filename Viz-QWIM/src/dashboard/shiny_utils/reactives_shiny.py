"""Public facade for split reactive state helpers used by the QWIM dashboard.

This module preserves the historical import surface for dashboard code, tests,
and ProperDocs API pages while delegating implementation to the focused helper
modules ``reactives_validation``, ``reactives_initialization``,
``reactives_access``, and ``reactives_sync``.
"""

from __future__ import annotations

from .reactives_access import (
    get_value_from_reactives_shiny,
    get_value_from_shiny_input_numeric,
    get_value_from_shiny_input_text,
    safe_get_reactive_value,
    safe_get_shiny_input_value,
    safe_get_value_from_shiny_input_numeric,
    safe_get_value_from_shiny_input_text,
    set_value_to_reactives_shiny,
    update_visual_object_in_reactives,
)
from .reactives_initialization import (
    create_reactive_value_safely,
    initialize_reactive_advisor_info,
    initialize_reactive_data_clients,
    initialize_reactive_data_results,
    initialize_reactive_inner_variables,
    initialize_reactive_triggers,
    initialize_reactive_user_inputs,
    initialize_reactive_visual_objects,
    initialize_reactives_shiny,
)
from .reactives_sync import (
    _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP,
    _reactive_key_to_input_id,
    register_client_input_observers,
    register_portfolio_results_observers,
)
from .reactives_validation import (
    REQUIRED_CATEGORIES,
    validate_category_name,
    validate_data_utils_parameter,
    validate_reactive_key_access,
    validate_reactives_shiny_structure,
)


__all__ = [
    "REQUIRED_CATEGORIES",
    "validate_category_name",
    "validate_data_utils_parameter",
    "validate_reactive_key_access",
    "validate_reactives_shiny_structure",
    "create_reactive_value_safely",
    "initialize_reactive_advisor_info",
    "initialize_reactive_data_clients",
    "initialize_reactive_data_results",
    "initialize_reactive_inner_variables",
    "initialize_reactive_triggers",
    "initialize_reactive_user_inputs",
    "initialize_reactive_visual_objects",
    "initialize_reactives_shiny",
    "get_value_from_reactives_shiny",
    "get_value_from_shiny_input_numeric",
    "get_value_from_shiny_input_text",
    "safe_get_reactive_value",
    "safe_get_shiny_input_value",
    "safe_get_value_from_shiny_input_numeric",
    "safe_get_value_from_shiny_input_text",
    "set_value_to_reactives_shiny",
    "update_visual_object_in_reactives",
    "_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP",
    "_reactive_key_to_input_id",
    "register_client_input_observers",
    "register_portfolio_results_observers",
]
