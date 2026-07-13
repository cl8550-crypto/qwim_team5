"""Validation utilities for the reactives_shiny dictionary structure.

This module provides functions that validate the shared reactive state dictionary
(``reactives_shiny``) and its sub-structures.  Every other ``reactives_*`` module
depends on this one.
"""

from __future__ import annotations

from typing import Any

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)

#: Required top-level categories in the ``reactives_shiny`` dictionary.
REQUIRED_CATEGORIES: list[str] = [
    "User_Inputs_Shiny",
    "Inner_Variables_Shiny",
    "Triggers_Shiny",
    "Visual_Objects_Shiny",
    "Data_Clients",
    "Data_Results",
    "Advisor_Info",
]


def validate_data_utils_parameter(*, data_utils: Any) -> Any:
    """Validate data_utils parameter using defensive programming."""
    # Input validation with early returns
    if data_utils is None:
        return False, "data_utils parameter cannot be None"

    # Configuration validation
    if not isinstance(data_utils, dict):
        return False, f"data_utils must be a dictionary, got {type(data_utils).__name__}"

    return True, ""


def validate_reactives_shiny_structure(*, reactives_shiny: Any) -> Any:
    """Validate reactives_shiny dictionary structure using defensive programming."""
    # Input validation with early returns
    if reactives_shiny is None:
        return False, "reactives_shiny dictionary cannot be None"

    if not isinstance(reactives_shiny, dict):
        return False, f"reactives_shiny must be a dictionary, got {type(reactives_shiny).__name__}"

    # Configuration validation - check required categories (excluding Advisor_Info which is optional
    # at validation time because it may be lazily initialized by the Setup tab)
    categories_to_check = [cat for cat in REQUIRED_CATEGORIES if cat != "Advisor_Info"]

    for category_name in categories_to_check:
        if category_name not in reactives_shiny:
            available_categories = list(reactives_shiny.keys())
            return (
                False,
                f"Required category '{category_name}' not found. Available: {available_categories}",
            )

        # Business logic validation - ensure each category is a dictionary
        if not isinstance(reactives_shiny[category_name], dict):
            return (
                False,
                f"Category '{category_name}' must be a dictionary, got {type(reactives_shiny[category_name]).__name__}",
            )

    return True, ""


def validate_reactive_key_access(*, category_dict: Any, key_name: Any, category_name: Any) -> Any:
    """Validate reactive key access using defensive programming."""
    # Input validation with early returns
    if category_dict is None:
        return False, f"Category '{category_name}' is None"

    if not isinstance(category_dict, dict):
        return (
            False,
            f"Category '{category_name}' is not a dictionary, got {type(category_dict).__name__}",
        )

    if key_name is None:
        return False, "key_name cannot be None"

    if not isinstance(key_name, str):
        return False, f"key_name must be string, got {type(key_name).__name__}"

    # Configuration validation
    if len(key_name.strip()) == 0:
        return False, "key_name cannot be empty string"

    # Business logic validation
    if key_name not in category_dict:
        available_keys = list(category_dict.keys())
        return (
            False,
            f"Key '{key_name}' not found in category '{category_name}'. Available keys: {available_keys}",
        )

    return True, ""


def validate_category_name(*, category_name: Any) -> Any:
    """Validate category name using defensive programming."""
    # Input validation with early returns
    if category_name is None:
        return False, "category_name cannot be None"

    if not isinstance(category_name, str):
        return False, f"category_name must be string, got {type(category_name).__name__}"

    # Configuration validation
    if len(category_name.strip()) == 0:
        return False, "category_name cannot be empty string"

    # Business logic validation
    if category_name not in REQUIRED_CATEGORIES:
        return False, f"Invalid category '{category_name}'. Valid categories: {REQUIRED_CATEGORIES}"

    return True, ""
