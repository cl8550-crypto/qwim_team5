"""Accessor utilities for the reactives_shiny dictionary.

This module provides functions that read from and write to the shared reactive
state dictionary (``reactives_shiny``), as well as helpers for safely reading
Shiny UI input values.
"""

from __future__ import annotations

from typing import Any

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from shiny.types import SilentException

from .reactives_validation import (
    validate_category_name,
    validate_reactive_key_access,
    validate_reactives_shiny_structure,
)


#: Module-level logger instance
_logger = get_logger(name = __name__)


def safe_get_shiny_input_value(*, input_events: Any, input_identifier: Any) -> Any:
    """Safely get value from Shiny input using defensive programming."""
    # Input validation with early returns
    if input_events is None:
        return None

    if not isinstance(input_identifier, str):
        return None

    if len(input_identifier.strip()) == 0:
        return None

    # Only use try-except for Shiny input access that might fail unpredictably
    try:
        # Check if the input identifier exists as an attribute of input_events
        if hasattr(input_events, input_identifier):
            input_reactive = getattr(input_events, input_identifier)

            # Call the reactive function to get the current value
            if callable(input_reactive):
                return input_reactive()
            return input_reactive
        return None

    except (AttributeError, KeyError, TypeError):
        return None
    except Exception:
        return None


def safe_get_reactive_value(*, reactive_input: Any, default_value: Any = None) -> Any:
    """Safely get a reactive value, falling back to the supplied default."""
    # Input validation with early returns
    if reactive_input is None:
        return default_value

    # Only use try-except for reactive value access that might fail unpredictably
    try:
        Reactive_Value = reactive_input()
        return Reactive_Value if Reactive_Value is not None else default_value
    except Exception:
        return default_value


def safe_get_value_from_shiny_input_text(
    *, input_reactive_object: Any, default_value: str = "") -> str:
    """Safely retrieve a text input value with default fallback behavior."""
    # Input validation with early returns
    if input_reactive_object is None:
        return default_value

    try:
        # Get the reactive value using () to call the reactive function
        raw_value = input_reactive_object()

        # Configuration validation - ensure value exists
        if raw_value is None:
            return default_value

        # Input validation - convert to string and clean
        cleaned_value = raw_value.strip() if isinstance(raw_value, str) else str(raw_value).strip()

        # Return validated value
        return cleaned_value or default_value

    except (AttributeError, RuntimeError, ValueError, TypeError, SilentException):
        # Defensive programming - handle all expected errors
        return default_value


def safe_get_value_from_shiny_input_numeric(
    *, input_reactive_object: Any, default_value: float = 0.0) -> float:
    """Safely retrieve a numeric input value with non-negative default fallback."""
    # Input validation with early returns
    if input_reactive_object is None:
        return default_value

    try:
        # Get the reactive value using () to call the reactive function
        raw_value = input_reactive_object()

        # Configuration validation - ensure value exists
        if raw_value is None:
            return default_value

        # Input validation - handle different value types
        if isinstance(raw_value, bool):
            return default_value

        if isinstance(raw_value, (int, float)):
            return max(0.0, float(raw_value))

        if isinstance(raw_value, str):
            # Extract numeric value from formatted currency string
            cleaned_value = raw_value.replace("$", "").replace(",", "").strip()
            if cleaned_value:
                try:
                    numeric_value = float(cleaned_value)
                    return max(0.0, numeric_value)
                except (ValueError, TypeError):
                    return default_value
            else:
                return default_value

        # Business logic validation - default for unexpected types
        return default_value

    except (AttributeError, RuntimeError, ValueError, TypeError, SilentException):
        # Defensive programming - handle all expected errors
        return default_value


def get_value_from_shiny_input_text(*, input_reactive_object: Any) -> str:
    """Retrieve a text input value and raise explicit validation errors on failure."""
    # Input validation with early returns
    if input_reactive_object is None:
        raise Exception_Validation_Input("input_reactive_object cannot be None")

    # Configuration validation - ensure input object has callable interface
    if not callable(input_reactive_object):
        raise Exception_Validation_Input(
            f"input_reactive_object must be callable, got {type(input_reactive_object).__name__}",
        )

    # Extract reactive input identifier for error reporting using simplified but effective approach
    reactive_input_identifier = "Unknown"
    try:  # pragma: no cover
        # Method 1: Enhanced source code parsing - most reliable for Shiny inputs
        import inspect
        import linecache
        import re

        frame = inspect.currentframe()
        try:
            # Get the calling frame where this function was invoked
            caller_frame = frame.f_back if frame is not None else None
            if caller_frame:
                filename = caller_frame.f_code.co_filename
                line_number = caller_frame.f_lineno

                # Get the actual source code line that called this function
                source_line = linecache.getline(filename, line_number).strip()

                # Enhanced patterns to match various input access styles
                input_patterns = [
                    # Direct input access: input.input_ID_...
                    r"input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Function call with input: get_value_from_shiny_input_text(input.input_ID_...)
                    r"get_value_from_shiny_input_text\s*\(\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Getattr style: getattr(input, 'input_ID_...')
                    r'getattr\s*\(\s*input\s*,\s*["\']?(input_ID_[a-zA-Z0-9_]+)["\']?\s*\)',
                    # Variable assignment: var = input.input_ID_...
                    r"=\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Function parameter: func(input.input_ID_...)
                    r"\(\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                ]

                # Try each pattern to find the identifier
                for pattern in input_patterns:
                    match = re.search(pattern, source_line)
                    if match:
                        reactive_input_identifier = match.group(1)
                        break

                # If not found in current line, check surrounding lines
                if reactive_input_identifier == "Unknown" and line_number > 1:
                    # Check previous lines for multi-line function calls
                    for line_offset in range(1, 4):  # Check 3 lines above
                        prev_line_number = line_number - line_offset
                        if prev_line_number > 0:
                            prev_source_line = linecache.getline(filename, prev_line_number).strip()
                            for pattern in input_patterns:
                                match = re.search(pattern, prev_source_line)
                                if match:
                                    reactive_input_identifier = match.group(1)
                                    break
                            if reactive_input_identifier != "Unknown":
                                break

        finally:
            del frame  # Prevent reference cycles

        # Method 2: Frame variable inspection - backup method
        if reactive_input_identifier == "Unknown":
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back if frame is not None else None
                max_depth = 3  # Limit depth to prevent performance issues
                current_depth = 0

                while (
                    caller_frame
                    and reactive_input_identifier == "Unknown"
                    and current_depth < max_depth
                ):
                    current_depth += 1

                    # Check local variables in the calling frame
                    if caller_frame.f_locals:
                        for var_name, var_value in caller_frame.f_locals.items():
                            # Direct match: variable is our reactive object and has input_ID_ in name
                            if var_value is input_reactive_object and "input_ID_" in str(var_name):
                                reactive_input_identifier = str(var_name)
                                break

                            # Input object inspection: look for input objects
                            if var_name == "input" and hasattr(var_value, "__dict__"):
                                # Check all attributes of the input object
                                try:
                                    for attr_name in dir(var_value):
                                        if attr_name.startswith("input_ID_") and hasattr(
                                            var_value,
                                            attr_name,
                                        ):
                                            attr_obj = getattr(var_value, attr_name)
                                            if attr_obj is input_reactive_object:
                                                reactive_input_identifier = attr_name
                                                break
                                except (AttributeError, TypeError):
                                    pass

                                if reactive_input_identifier != "Unknown":
                                    break

                    # Move up one frame
                    caller_frame = caller_frame.f_back

            finally:
                del frame  # Prevent reference cycles

        # Method 3: Object introspection - check common attributes
        if reactive_input_identifier == "Unknown":
            # Check standard identifier attributes
            identifier_attributes = ["__name__", "_name", "name", "_id", "id", "_key", "key"]
            for attr_name in identifier_attributes:
                if hasattr(input_reactive_object, attr_name):
                    try:
                        attr_value = getattr(input_reactive_object, attr_name)
                        if isinstance(attr_value, str) and "input_ID_" in attr_value:
                            reactive_input_identifier = attr_value
                            break
                    except (AttributeError, TypeError):
                        pass

        # Method 4: String representation analysis
        if reactive_input_identifier == "Unknown":
            try:
                # Check object representation
                obj_repr = repr(input_reactive_object)
                obj_str = str(input_reactive_object)

                # Look for input_ID_ patterns in representations
                combined_text = f"{obj_repr} {obj_str}"
                match = re.search(r"input_ID_[a-zA-Z0-9_]+", combined_text)
                if match:
                    reactive_input_identifier = match.group(0)

            except Exception:
                pass

        # Method 5: Enhanced fallback with more context
        if reactive_input_identifier == "Unknown":
            try:
                obj_type = type(input_reactive_object).__name__
                obj_module = getattr(type(input_reactive_object), "__module__", "unknown")

                # Try to get a more meaningful identifier from the calling context
                frame = inspect.currentframe()
                try:
                    caller_frame = frame.f_back if frame is not None else None
                    if caller_frame and caller_frame.f_code:
                        func_name = caller_frame.f_code.co_name
                        filename = caller_frame.f_code.co_filename
                        line_number = caller_frame.f_lineno

                        # Extract just the filename without path
                        import os

                        base_filename = os.path.basename(filename)

                        reactive_input_identifier = (
                            f"Unknown_input_in_{func_name}_at_{base_filename}:{line_number}"
                        )
                    else:
                        reactive_input_identifier = (
                            f"Unknown_reactive_input_{obj_type}_from_{obj_module}"
                        )
                finally:
                    del frame

            except Exception:
                reactive_input_identifier = "Unknown_reactive_input_object"

    except Exception:  # pragma: no cover  # reason: outer defensive fallback; all inner exception handlers fire first
        # Final fallback if all extraction methods fail
        reactive_input_identifier = "Unknown_reactive_input_object"

    try:
        # Get the reactive value using () to call the reactive function
        raw_value = input_reactive_object()

    except SilentException:
        # Shiny internal — must propagate so the reactive framework can
        # silently defer the effect until the input is available.
        raise
    except (AttributeError, RuntimeError) as exc:
        # Defensive programming - handle reactive access failures
        raise Exception_Configuration(
            f"Failed to retrieve value from reactive input '{reactive_input_identifier}': {exc}",
        ) from exc
    except Exception as exc:
        # Handle any other unexpected errors during reactive access
        raise Exception_Configuration(
            f"Unexpected error accessing reactive input '{reactive_input_identifier}': {exc}",
        ) from exc

    # Configuration validation - ensure value exists
    if raw_value is None:
        raise Exception_Validation_Input(
            f"Retrieved reactive value is None for input '{reactive_input_identifier}' - no text input provided",
        )

    # Business logic validation - convert to string and clean
    try:
        cleaned_value = raw_value.strip() if isinstance(raw_value, str) else str(raw_value).strip()

    except (
        ValueError,
        TypeError,
    ) as exc:  # pragma: no cover  # reason: str() and .strip() raise only in extreme edge cases not reachable via normal Shiny inputs
        # Handle string conversion failures
        raise TypeError(
            f"Cannot convert retrieved value to string for input '{reactive_input_identifier}': {type(raw_value).__name__} - {exc}",
        ) from exc

    # Final validation - ensure we have a non-empty string
    if not cleaned_value:
        raise Exception_Validation_Input(
            f"Text input '{reactive_input_identifier}' is empty or contains only whitespace",
        )

    # Return validated value
    return cleaned_value


def get_value_from_shiny_input_numeric(*, input_reactive_object: Any) -> float:
    """Retrieve a numeric input value and raise explicit validation errors on failure."""
    # Input validation with early returns
    if input_reactive_object is None:
        raise Exception_Validation_Input("input_reactive_object cannot be None")

    # Configuration validation - ensure input object has callable interface
    if not callable(input_reactive_object):
        raise Exception_Validation_Input(
            f"input_reactive_object must be callable, got {type(input_reactive_object).__name__}",
        )

    # Extract reactive input identifier for error reporting using simplified but effective approach
    reactive_input_identifier = "Unknown"
    try:  # pragma: no cover
        # Method 1: Enhanced source code parsing - most reliable for Shiny inputs
        import inspect
        import linecache
        import re

        frame = inspect.currentframe()
        try:
            # Get the calling frame where this function was invoked
            caller_frame = frame.f_back if frame is not None else None
            if caller_frame:
                filename = caller_frame.f_code.co_filename
                line_number = caller_frame.f_lineno

                # Get the actual source code line that called this function
                source_line = linecache.getline(filename, line_number).strip()

                # Enhanced patterns to match various input access styles
                input_patterns = [
                    # Direct input access: input.input_ID_...
                    r"input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Function call with input: get_value_from_shiny_input_numeric(input.input_ID_...)
                    r"get_value_from_shiny_input_numeric\s*\(\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Getattr style: getattr(input, 'input_ID_...')
                    r'getattr\s*\(\s*input\s*,\s*["\']?(input_ID_[a-zA-Z0-9_]+)["\']?\s*\)',
                    # Variable assignment: var = input.input_ID_...
                    r"=\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                    # Function parameter: func(input.input_ID_...)
                    r"\(\s*input\s*\.\s*(input_ID_[a-zA-Z0-9_]+)",
                ]

                # Try each pattern to find the identifier
                for pattern in input_patterns:
                    match = re.search(pattern, source_line)
                    if match:
                        reactive_input_identifier = match.group(1)
                        break

                # If not found in current line, check surrounding lines
                if reactive_input_identifier == "Unknown" and line_number > 1:
                    # Check previous lines for multi-line function calls
                    for line_offset in range(1, 4):  # Check 3 lines above
                        prev_line_number = line_number - line_offset
                        if prev_line_number > 0:
                            prev_source_line = linecache.getline(filename, prev_line_number).strip()
                            for pattern in input_patterns:
                                match = re.search(pattern, prev_source_line)
                                if match:
                                    reactive_input_identifier = match.group(1)
                                    break
                            if reactive_input_identifier != "Unknown":
                                break

        finally:
            del frame  # Prevent reference cycles

        # Method 2: Frame variable inspection - backup method
        if reactive_input_identifier == "Unknown":
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back if frame is not None else None
                max_depth = 3  # Limit depth to prevent performance issues
                current_depth = 0

                while (
                    caller_frame
                    and reactive_input_identifier == "Unknown"
                    and current_depth < max_depth
                ):
                    current_depth += 1

                    # Check local variables in the calling frame
                    if caller_frame.f_locals:
                        for var_name, var_value in caller_frame.f_locals.items():
                            # Direct match: variable is our reactive object and has input_ID_ in name
                            if var_value is input_reactive_object and "input_ID_" in str(var_name):
                                reactive_input_identifier = str(var_name)
                                break

                            # Input object inspection: look for input objects
                            if var_name == "input" and hasattr(var_value, "__dict__"):
                                # Check all attributes of the input object
                                try:
                                    for attr_name in dir(var_value):
                                        if attr_name.startswith("input_ID_") and hasattr(
                                            var_value,
                                            attr_name,
                                        ):
                                            attr_obj = getattr(var_value, attr_name)
                                            if attr_obj is input_reactive_object:
                                                reactive_input_identifier = attr_name
                                                break
                                except (AttributeError, TypeError):
                                    pass

                                if reactive_input_identifier != "Unknown":
                                    break

                    # Move up one frame
                    caller_frame = caller_frame.f_back

            finally:
                del frame  # Prevent reference cycles

        # Method 3: Object introspection - check common attributes
        if reactive_input_identifier == "Unknown":
            # Check standard identifier attributes
            identifier_attributes = ["__name__", "_name", "name", "_id", "id", "_key", "key"]
            for attr_name in identifier_attributes:
                if hasattr(input_reactive_object, attr_name):
                    try:
                        attr_value = getattr(input_reactive_object, attr_name)
                        if isinstance(attr_value, str) and "input_ID_" in attr_value:
                            reactive_input_identifier = attr_value
                            break
                    except (AttributeError, TypeError):
                        pass

        # Method 4: String representation analysis
        if reactive_input_identifier == "Unknown":
            try:
                # Check object representation
                obj_repr = repr(input_reactive_object)
                obj_str = str(input_reactive_object)

                # Look for input_ID_ patterns in representations
                combined_text = f"{obj_repr} {obj_str}"
                match = re.search(r"input_ID_[a-zA-Z0-9_]+", combined_text)
                if match:
                    reactive_input_identifier = match.group(0)

            except Exception:
                pass

        # Method 5: Enhanced fallback with more context
        if reactive_input_identifier == "Unknown":
            try:
                obj_type = type(input_reactive_object).__name__
                obj_module = getattr(type(input_reactive_object), "__module__", "unknown")

                # Try to get a more meaningful identifier from the calling context
                frame = inspect.currentframe()
                try:
                    caller_frame = frame.f_back if frame is not None else None
                    if caller_frame and caller_frame.f_code:
                        func_name = caller_frame.f_code.co_name
                        filename = caller_frame.f_code.co_filename
                        line_number = caller_frame.f_lineno

                        # Extract just the filename without path
                        import os

                        base_filename = os.path.basename(filename)

                        reactive_input_identifier = (
                            f"Unknown_input_in_{func_name}_at_{base_filename}:{line_number}"
                        )
                    else:
                        reactive_input_identifier = (
                            f"Unknown_reactive_input_{obj_type}_from_{obj_module}"
                        )
                finally:
                    del frame

            except Exception:
                reactive_input_identifier = "Unknown_reactive_input_object"

    except Exception:  # pragma: no cover  # reason: outer defensive fallback; all inner exception handlers fire first
        # Final fallback if all extraction methods fail
        reactive_input_identifier = "Unknown_reactive_input_object"

    try:
        # Get the reactive value using () to call the reactive function
        raw_value = input_reactive_object()

    except SilentException:
        # Shiny internal — must propagate so the reactive framework can
        # silently defer the effect until the input is available.
        raise
    except (AttributeError, RuntimeError) as exc:
        # Defensive programming - handle reactive access failures
        raise Exception_Configuration(
            f"Failed to retrieve value from reactive input '{reactive_input_identifier}': {exc}",
        ) from exc
    except Exception as exc:
        # Handle any other unexpected errors during reactive access
        raise Exception_Configuration(
            f"Unexpected error accessing reactive input '{reactive_input_identifier}': {exc}",
        ) from exc

    # Configuration validation - ensure value exists
    if raw_value is None:
        raise Exception_Validation_Input(
            f"Retrieved reactive value is None for input '{reactive_input_identifier}' - no numeric input provided",
        )

    # Business logic validation - handle different value types and convert to float
    if isinstance(raw_value, bool):
        raise TypeError(
            f"Numeric input '{reactive_input_identifier}' has unexpected type: {type(raw_value).__name__} (value: {raw_value})",
        )

    if isinstance(raw_value, (int, float)):
        try:
            numeric_value = float(raw_value)
            # Ensure non-negative value for financial data
            if numeric_value < 0:
                raise Exception_Validation_Input(
                    f"Numeric input '{reactive_input_identifier}' contains negative value: {numeric_value}",
                )
            return numeric_value
        except (ValueError, TypeError) as exc:  # pragma: no cover
            raise TypeError(
                f"Cannot convert numeric value to float for input '{reactive_input_identifier}': {type(raw_value).__name__} - {exc}",
            ) from exc

    elif isinstance(raw_value, str):
        try:
            # Extract numeric value from formatted currency string
            cleaned_value = raw_value.replace("$", "").replace(",", "").strip()

            if not cleaned_value:
                raise Exception_Validation_Input(
                    f"Numeric input '{reactive_input_identifier}' is empty or contains only formatting characters",
                )

            numeric_value = float(cleaned_value)

            # Ensure non-negative value for financial data
            if numeric_value < 0:
                raise Exception_Validation_Input(
                    f"Numeric input '{reactive_input_identifier}' contains negative value: {numeric_value}",
                )

            return numeric_value

        except ValueError as exc:
            # Re-raise ValueError with context
            if "negative value" in str(exc):  # pragma: no cover
                raise exc  # pragma: no cover
            raise Exception_Validation_Input(
                f"Cannot parse numeric value from string for input '{reactive_input_identifier}': '{raw_value}' - {exc}",
            ) from exc
        except (
            TypeError,
            AttributeError,
        ) as exc:  # pragma: no cover  # reason: defensive handler; numeric conversion errors already caught by preceding ValueError handler
            raise TypeError(
                f"Cannot process string value for input '{reactive_input_identifier}': {type(raw_value).__name__} - {exc}",
            ) from exc

    else:
        # Handle unexpected types
        raise TypeError(
            f"Numeric input '{reactive_input_identifier}' has unexpected type: {type(raw_value).__name__} (value: {raw_value})",
        )


def get_value_from_reactives_shiny(*, reactives_shiny: Any, key_name: Any, key_category: Any) -> Any:
    """Get a value from a named category within the shared reactives dictionary."""
    # Input validation with early returns - validate key_name first for better error messages
    if key_name is None:
        raise Exception_Validation_Input("key_name cannot be None")

    if not isinstance(key_name, str):
        raise Exception_Validation_Input(
            f"key_name must be string, got {type(key_name).__name__}: '{key_name}'",
        )

    if len(key_name.strip()) == 0:
        raise Exception_Validation_Input(f"key_name cannot be empty string: '{key_name}'")

    # Clean key_name for consistent processing
    key_name_cleaned = key_name.strip()

    # Validate key_category with enhanced error messages
    if key_category is None:
        raise Exception_Validation_Input(
            f"key_category cannot be None (searching for key_name: '{key_name_cleaned}')",
        )

    if not isinstance(key_category, str):
        raise Exception_Validation_Input(
            f"key_category must be string, got {type(key_category).__name__}: '{key_category}' (searching for key_name: '{key_name_cleaned}')",
        )

    if len(key_category.strip()) == 0:
        raise Exception_Validation_Input(
            f"key_category cannot be empty string: '{key_category}' (searching for key_name: '{key_name_cleaned}')",
        )

    # Clean key_category for consistent processing
    key_category_cleaned = key_category.strip()

    # Validate reactives_shiny structure with enhanced error messages
    if reactives_shiny is None:
        raise Exception_Validation_Input(
            f"reactives_shiny dictionary cannot be None (searching for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}')",
        )

    if not isinstance(reactives_shiny, dict):
        raise Exception_Validation_Input(
            f"reactives_shiny must be a dictionary, got {type(reactives_shiny).__name__} (searching for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}')",
        )

    # Configuration validation - check required categories with enhanced error messages
    required_categories = [
        "User_Inputs_Shiny",
        "Inner_Variables_Shiny",
        "Triggers_Shiny",
        "Visual_Objects_Shiny",
        "Data_Clients",
    ]

    # Validate that key_category is a valid category
    if key_category_cleaned not in required_categories:
        raise Exception_Validation_Input(
            f"Invalid key_category: '{key_category_cleaned}'. Valid categories: {required_categories} (searching for key_name: '{key_name_cleaned}')",
        )

    # Check that all required categories exist in reactives_shiny
    missing_categories = []
    for category_name in required_categories:
        if category_name not in reactives_shiny:
            missing_categories.append(category_name)
        elif not isinstance(reactives_shiny[category_name], dict):
            raise Exception_Validation_Input(
                f"Category '{category_name}' must be a dictionary, got {type(reactives_shiny[category_name]).__name__} (searching for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}')",
            )

    if missing_categories:
        available_categories = list(reactives_shiny.keys())
        raise Exception_Validation_Input(
            f"Required categories missing from reactives_shiny: {missing_categories}. Available categories: {available_categories} (searching for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}')",
        )

    # Business logic validation - get the specific category
    category_dict = reactives_shiny.get(key_category_cleaned)
    if (
        category_dict is None
    ):  # pragma: no cover  # reason: defensive guard; prior validation ensures key_category_cleaned is always present
        # This should not happen due to above validation, but defensive programming
        available_categories = list(reactives_shiny.keys())
        raise KeyError(
            f"Category '{key_category_cleaned}' not found in reactives_shiny. Available categories: {available_categories} (searching for key_name: '{key_name_cleaned}')",
        )

    # Validate that the specific key exists in the category
    if key_name_cleaned not in category_dict:
        available_keys = list(category_dict.keys())
        if not available_keys:
            raise KeyError(
                f"Key '{key_name_cleaned}' not found in category '{key_category_cleaned}' - category is empty (no keys available)",
            )
        # Provide helpful suggestions if key is similar to existing keys
        similar_keys = [
            key
            for key in available_keys
            if key_name_cleaned.lower() in key.lower() or key.lower() in key_name_cleaned.lower()
        ]
        if similar_keys:
            raise KeyError(
                f"Key '{key_name_cleaned}' not found in category '{key_category_cleaned}'. Available keys: {available_keys}. Similar keys found: {similar_keys}",
            )
        raise KeyError(
            f"Key '{key_name_cleaned}' not found in category '{key_category_cleaned}'. Available keys: {available_keys}",
        )

    # Get the reactive variable safely
    reactive_variable = category_dict[key_name_cleaned]

    # Validate reactive variable exists and is not None
    if reactive_variable is None:
        raise Exception_Validation_Input(
            f"Reactive variable is None for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}' - reactive variable was not properly initialized",
        )

    # Validate that reactive variable has the required 'get' method
    if not hasattr(reactive_variable, "get"):
        available_methods = [
            method for method in dir(reactive_variable) if not method.startswith("_")
        ]
        raise TypeError(
            f"Reactive variable for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}' does not have 'get' method. Object type: {type(reactive_variable).__name__}. Available methods: {available_methods}",
        )

    # Validate that the 'get' method is callable
    if not callable(reactive_variable.get):
        raise TypeError(
            f"Reactive variable 'get' attribute for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}' is not callable. Object type: {type(reactive_variable).__name__}. 'get' type: {type(reactive_variable.get).__name__}",
        )

    # Attempt to retrieve the value with comprehensive error handling
    try:
        retrieved_value = reactive_variable.get()

        # Log successful retrieval for debugging purposes
        _logger.debug(
            "Successfully retrieved value from reactive variable",
            extra={
                "key_name": key_name_cleaned,
                "key_category": key_category_cleaned,
                "value_type": type(retrieved_value).__name__,
            },
        )

        # Return the actual value (including None if that's what was stored)
        return retrieved_value

    except AttributeError as exc:
        # Handle cases where get() method doesn't exist or has issues
        raise Exception_Configuration(
            f"AttributeError accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. Reactive variable type: {type(reactive_variable).__name__}. Error: {exc}",
        ) from exc

    except RuntimeError as exc:
        # Handle Shiny reactive runtime errors (e.g., reactive context issues)
        raise Exception_Configuration(
            f"RuntimeError accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. This may indicate a reactive context issue. Error: {exc}",
        ) from exc

    except ValueError as exc:
        # Handle value-related errors during retrieval
        raise Exception_Configuration(
            f"ValueError accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. Error: {exc}",
        ) from exc

    except TypeError as exc:
        # Handle type-related errors during retrieval
        raise Exception_Configuration(
            f"TypeError accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. Reactive variable type: {type(reactive_variable).__name__}. Error: {exc}",
        ) from exc

    except KeyError as exc:
        # Handle key-related errors during retrieval (though this should be rare for get())
        raise Exception_Configuration(
            f"KeyError accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. Error: {exc}",
        ) from exc

    except Exception as exc:
        # Handle any other unexpected errors with full context
        exc_type = type(exc).__name__
        exc_module = getattr(type(exc), "__module__", "unknown")
        reactive_type = type(reactive_variable).__name__
        reactive_module = getattr(type(reactive_variable), "__module__", "unknown")

        raise Exception_Configuration(
            f"Unexpected {exc_type} error accessing reactive value for key_name: '{key_name_cleaned}' in key_category: '{key_category_cleaned}'. Reactive variable type: {reactive_type} from {reactive_module}. Exception type: {exc_type} from {exc_module}. Error: {exc}",
        ) from exc


def set_value_to_reactives_shiny(
    *, reactives_shiny: Any, key_name: Any, key_category: Any, input_value: Any) -> Any:
    """Set a value within the shared reactives dictionary after validation."""
    # Input validation with early returns
    validation_result, validation_message = validate_reactives_shiny_structure(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Reactives structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_category_name(category_name = key_category)
    if not validation_result:
        error_message = f"Category validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Business logic validation - get category
    category_dict = reactives_shiny.get(key_category)
    if category_dict is None:
        available_categories = list(reactives_shiny.keys())
        error_message = (
            f"Category '{key_category}' not found. Available categories: {available_categories}"
        )
        _logger.error(error_message)
        raise KeyError(error_message)

    # Validate key access
    validation_result, validation_message = validate_reactive_key_access(
        category_dict = category_dict,
        key_name = key_name,
        category_name = key_category,
    )
    if not validation_result:
        error_message = f"Key access validation failed: {validation_message}"
        _logger.error(error_message)
        raise KeyError(error_message)

    # Get the reactive variable safely
    reactive_variable = category_dict[key_name]

    # Defensive programming - safe value setting
    if reactive_variable is None:
        error_message = f"Reactive variable '{key_name}' in category '{key_category}' is None"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if not hasattr(reactive_variable, "set"):
        error_message = f"Reactive variable '{key_name}' in category '{key_category}' does not have 'set' method"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    # Only use try-except for reactive value setting that might fail unpredictably
    try:
        reactive_variable.set(input_value)
        _logger.debug(
            "Set value in reactive variable",
            extra={
                "key_category": key_category,
                "key_name": key_name,
                "input_value": str(input_value),
            },
        )
        return reactives_shiny
    except Exception as exc:
        error_message = f"Unexpected error setting reactive value for key '{key_name}' in category '{key_category}' to '{input_value}': {exc}"
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def update_visual_object_in_reactives(
    *, reactives_shiny: Any, chart_key: str, figure: Any) -> None:
    """Best-effort update of a visual object stored in `Visual_Objects_Shiny`."""
    # Input validation with early returns
    if reactives_shiny is None:
        _logger.debug("update_visual_object_in_reactives: reactives_shiny is None")
        return
    if not isinstance(reactives_shiny, dict):
        _logger.debug(
            "update_visual_object_in_reactives: reactives_shiny is not a dict (%s)",
            type(reactives_shiny).__name__,
        )
        return
    if not chart_key or not isinstance(chart_key, str):
        _logger.debug("update_visual_object_in_reactives: invalid chart_key '%s'", chart_key)
        return
    if figure is None:
        _logger.debug(
            "update_visual_object_in_reactives: figure is None for key '%s'",
            chart_key,
        )
        return

    # Configuration validation
    visual_objects = reactives_shiny.get("Visual_Objects_Shiny")
    if not isinstance(visual_objects, dict):
        _logger.debug(
            "update_visual_object_in_reactives: Visual_Objects_Shiny missing or is not a dict",
        )
        return

    reactive_value = visual_objects.get(chart_key)
    if reactive_value is None:
        _logger.debug(
            "update_visual_object_in_reactives: key '%s' not found in Visual_Objects_Shiny",
            chart_key,
        )
        return
    if not hasattr(reactive_value, "set"):
        _logger.debug(
            "update_visual_object_in_reactives: reactive for '%s' has no .set() method",
            chart_key,
        )
        return

    # Only use try-except for unpredictable reactive .set() operation
    try:
        reactive_value.set(figure)
        _logger.debug(
            "update_visual_object_in_reactives: updated Visual_Objects_Shiny['%s']",
            chart_key,
        )
    except Exception as exc:
        _logger.warning(
            "update_visual_object_in_reactives: could not update '%s': %s",
            chart_key,
            exc,
        )
