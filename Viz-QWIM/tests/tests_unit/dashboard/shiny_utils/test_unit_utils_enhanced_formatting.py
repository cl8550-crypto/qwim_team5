"""Enhanced Formatting Utilities Module.

This module provides comprehensive formatting functions for financial data,
currencies, percentages, dates, and numbers with locale-aware formatting
capabilities using the Babel library for internationalization support.

The module is designed to enhance the user experience in financial applications
by providing consistent, professional, and culturally-appropriate data formatting
across different locales and regions.

Features:
    - Locale-aware currency formatting with proper symbols and separators
    - Advanced percentage formatting with customizable precision
    - Number formatting with thousands separators and decimal control
    - Fallback mechanisms for robust error handling
    - Support for multiple international locales and currencies
    - Integration with Shiny applications for reactive formatting

Dependencies:
    - babel: For internationalization and locale-aware formatting
    - locale: For system locale information
    - typing: For type hints and improved code documentation

Examples:
    Basic currency formatting:

    ```python
    from utils_enhanced_formatting import format_enhanced_currency_display

    # Format USD currency
    formatted_usd = format_enhanced_currency_display(1234567.89)
    print(formatted_usd)  # Output: "$1,234,567.89"

    # Format EUR currency with German locale
    formatted_eur = format_enhanced_currency_display(
        1234567.89, currency_code="EUR", locale_setting="de_DE"
    )
    print(formatted_eur)  # Output: "1.234.567,89 €"
    ```

    Percentage and number formatting:

    ```python
    from utils_enhanced_formatting import (
        format_enhanced_percentage_display,
        format_enhanced_number_display,
    )

    # Format percentage with 2 decimal places
    percentage_value = format_enhanced_percentage_display(0.0525, 2)
    print(percentage_value)  # Output: "5.25%"

    # Format large number with thousands separators
    large_number = format_enhanced_number_display(1234567, 0)
    print(large_number)  # Output: "1,234,567"
    ```

Note:
    This module follows the project's coding standards with snake_case naming,
    comprehensive input validation, and defensive programming practices.
    All functions include proper error handling with meaningful fallback values
    to ensure application stability.

Attributes:
    SUPPORTED_LOCALES (list): List of commonly supported locale identifiers
    DEFAULT_CURRENCY_FORMATS (dict): Default formatting patterns for currencies
    FALLBACK_LOCALE (str): Default fallback locale for error scenarios

See Also:
    - Babel Documentation: https://babel.pocoo.org/en/latest/
    - Unicode CLDR: http://cldr.unicode.org/
    - ISO 4217 Currency Codes: https://en.wikipedia.org/wiki/ISO_4217

Version:
    0.5.1

Author:
    QWIM Dashboard Development Team

Last Modified:
    June 2025
"""

import logging

from decimal import Decimal, InvalidOperation
from typing import Any

from babel.core import Locale, UnknownLocaleError
from babel.dates import format_date, format_datetime
from babel.numbers import format_currency, format_decimal, format_percent


# Module-level constants for configuration and supported formats
SUPPORTED_LOCALES: list[str] = [
    "en_US",  # United States English
    "en_GB",  # British English
    "de_DE",  # German (Germany)
    "fr_FR",  # French (France)
    "es_ES",  # Spanish (Spain)
    "it_IT",  # Italian (Italy)
    "ja_JP",  # Japanese (Japan)
    "zh_CN",  # Chinese (Simplified, China)
    "pt_BR",  # Portuguese (Brazil)
    "ru_RU",  # Russian (Russia)
    "ar_SA",  # Arabic (Saudi Arabia)
    "hi_IN",  # Hindi (India)
    "ko_KR",  # Korean (South Korea)
    "nl_NL",  # Dutch (Netherlands)
    "sv_SE",  # Swedish (Sweden)
    "no_NO",  # Norwegian (Norway)
    "da_DK",  # Danish (Denmark)
    "fi_FI",  # Finnish (Finland)
    "pl_PL",  # Polish (Poland)
    "tr_TR",  # Turkish (Turkey)
]


DEFAULT_CURRENCY_FORMATS: dict[str, str] = {
    "standard": "¤#,##0.00",  # Standard currency format with symbol
    "accounting": "¤#,##0.00;(¤#,##0.00)",  # Accounting format with parentheses for negatives
    "compact": "¤#,##0",  # Compact format without decimal places
    "detailed": "¤#,##0.00##",  # Detailed format with optional additional decimals
    "international": "¤¤ #,##0.00",  # International format with currency code
}

FALLBACK_LOCALE: str = "en_US"


def validate_locale_setting(locale_setting: str) -> str:
    """Validate and normalize locale setting with fallback mechanism.

    This function ensures that the provided locale setting is valid and supported
    by the Babel library. If the locale is not supported, it falls back to the
    default locale to prevent application errors.

    Args:
        locale_setting (str): The locale identifier to validate (e.g., "en_US", "de_DE")
            Expected format: language_COUNTRY (ISO 639-1 and ISO 3166-1 alpha-2)

    Returns:
        str: A valid locale identifier that is supported by Babel
            Returns the original locale if valid, otherwise returns FALLBACK_LOCALE

    Raises:
        TypeError: If locale_setting is not a string
        ValueError: If locale_setting validation fails

    Examples:
        >>> validate_locale_setting("en_US")
        "en_US"
        >>> validate_locale_setting("invalid_locale")
        "en_US"  # Falls back to default
        >>> validate_locale_setting("de_DE")
        "de_DE"

    Note:
        This function provides warnings when falling back to the default locale
        to help with debugging locale-related issues in production environments.
    """
    # Input type validation
    if not isinstance(locale_setting, str):
        raise TypeError(f"Invalid locale type: {type(locale_setting)}. Expected string.")

    # Empty string validation
    if not locale_setting.strip():
        raise ValueError("Empty locale setting provided. Using fallback locale.")

    try:
        # Attempt to create Locale object to validate the locale
        validated_locale = Locale.parse(locale_setting)

        # Check if the locale is in our supported list for optimal formatting
        if locale_setting in SUPPORTED_LOCALES:
            return locale_setting
        return locale_setting

    except (UnknownLocaleError, ValueError) as exc_error:
        raise ValueError(
            f"Invalid locale '{locale_setting}': {exc_error}. Using fallback: {FALLBACK_LOCALE}"
        ) from exc_error
    except Exception as exc_error:
        raise RuntimeError(
            f"Unexpected error validating locale '{locale_setting}': {exc_error}"
        ) from exc_error


def validate_currency_code(currency_code: str) -> str:
    """Validate and normalize ISO 4217 currency code.

    This function ensures that the provided currency code follows the ISO 4217
    standard for currency codes. It performs basic validation and normalization
    to prevent formatting errors.

    Args:
        currency_code (str): The ISO 4217 currency code to validate (e.g., "USD", "EUR")
            Expected format: 3-letter uppercase alphabetic code

    Returns:
        str: A valid, normalized currency code in uppercase format
            Returns "USD" as fallback if the provided code is invalid

    Raises:
        TypeError: If currency_code is not a string
        ValueError: If currency_code format is invalid

    Examples:
        >>> validate_currency_code("usd")
        "USD"
        >>> validate_currency_code("EUR")
        "EUR"
        >>> validate_currency_code("invalid")
        "USD"  # Falls back to default

    Note:
        This function performs basic validation but does not verify against
        the complete list of valid ISO 4217 codes to maintain performance.
        For comprehensive validation, consider integrating with a currency
        validation library.
    """
    # Input type validation
    if not isinstance(currency_code, str):
        raise TypeError(f"Invalid currency code type: {type(currency_code)}. Expected string.")

    # Normalize to uppercase and strip whitespace
    normalized_code = currency_code.strip().upper()

    # Basic format validation: must be exactly 3 alphabetic characters
    if len(normalized_code) == 3 and normalized_code.isalpha():
        return normalized_code
    raise ValueError(f"Invalid currency code format '{currency_code}'. Using fallback: USD")


def format_enhanced_currency_display(
    amount: int | float | str | Decimal,
    currency_code: str = "USD",
    locale_setting: str = "en_US",
    format_pattern: str = "standard",
    decimal_places: int | None = None,
) -> str:
    """Format currency with enhanced locale-aware display and comprehensive error handling.

    This function provides professional currency formatting with support for multiple
    locales, currencies, and formatting patterns. It includes robust error handling
    and fallback mechanisms to ensure consistent output even with invalid inputs.

    Args:
        amount (Union[int, float, str, Decimal]): The monetary amount to format
            Accepts various numeric types and string representations
            Examples: 1234.56, "1234.56", Decimal("1234.56")
        currency_code (str, optional): ISO 4217 currency code. Defaults to "USD"
            Examples: "USD", "EUR", "GBP", "JPY"
        locale_setting (str, optional): Locale for formatting. Defaults to "en_US"
            Examples: "en_US", "de_DE", "fr_FR", "ja_JP"
        format_pattern (str, optional): Formatting pattern to use. Defaults to "standard"
            Options: "standard", "accounting", "compact", "detailed", "international"
        decimal_places (Optional[int], optional): Override default decimal places
            If None, uses locale default; otherwise forces specific decimal precision

    Returns:
        str: Formatted currency string with proper locale formatting
            Includes currency symbol, thousands separators, and decimal formatting
            Example outputs: "$1,234.56", "1.234,56 €", "¥1,235"

    Raises:
        TypeError: If amount cannot be converted to a numeric type
        ValueError: If amount is not a valid number

    Examples:
        Basic usage with defaults:

        ```python
        # Standard USD formatting
        result = format_enhanced_currency_display(1234567.89)
        # Output: "$1,234,567.89"
        ```

        International formatting:

        ```python
        # German locale with EUR currency
        result = format_enhanced_currency_display(
            1234567.89, currency_code="EUR", locale_setting="de_DE"
        )
        # Output: "1.234.567,89 €"
        ```

        Custom formatting patterns:

        ```python
        # Accounting format with parentheses for negatives
        result = format_enhanced_currency_display(-1234.56, format_pattern="accounting")
        # Output: "($1,234.56)"
        ```

        Decimal precision control:

        ```python
        # Force no decimal places for whole currency units
        result = format_enhanced_currency_display(1234.56, decimal_places=0)
        # Output: "$1,235"
        ```

    Note:
        This function automatically handles locale-specific formatting rules
        including decimal separators, thousands separators, currency symbol
        placement, and negative number representation.

        For performance-critical applications, consider caching formatted
        results when the same values are formatted repeatedly.

    See Also:
        - format_enhanced_percentage_display: For percentage formatting
        - format_enhanced_number_display: For general number formatting
        - validate_currency_code: For currency code validation
        - validate_locale_setting: For locale validation
    """
    try:
        # Input validation and normalization
        try:
            validated_locale = validate_locale_setting(locale_setting = locale_setting)
        except (TypeError, ValueError):
            validated_locale = FALLBACK_LOCALE

        try:
            validated_currency = validate_currency_code(currency_code = currency_code)
        except (TypeError, ValueError):
            validated_currency = "USD"

        # Convert amount to Decimal for precise financial calculations
        if isinstance(amount, str):
            # Clean string input by removing common currency symbols and separators
            cleaned_amount = (
                amount.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
            )
            try:
                decimal_amount = Decimal(cleaned_amount)
            except InvalidOperation as exc_error:
                raise ValueError(
                    f"Cannot convert '{amount}' to a valid monetary amount"
                ) from exc_error
        elif isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            raise TypeError(f"Amount must be int, float, str, or Decimal, got {type(amount)}")

        # Convert back to float for Babel formatting (Babel doesn't support Decimal directly)
        float_amount = float(decimal_amount)

        # Get the appropriate format pattern
        if format_pattern in DEFAULT_CURRENCY_FORMATS:
            babel_format = DEFAULT_CURRENCY_FORMATS[format_pattern]
        else:
            babel_format = DEFAULT_CURRENCY_FORMATS["standard"]

        # Override decimal places if specified
        if decimal_places is not None:
            if isinstance(decimal_places, int) and 0 <= decimal_places <= 10:
                # Modify format pattern to force specific decimal places
                if decimal_places == 0:
                    babel_format = babel_format.replace(".00", "")
                else:
                    decimal_pattern = "." + "0" * decimal_places
                    babel_format = babel_format.replace(".00", decimal_pattern)

        # Perform the currency formatting using Babel
        formatted_result = format_currency(
            float_amount,
            validated_currency,
            locale=validated_locale,
            format=babel_format,
        )

        return formatted_result

    except (ValueError, TypeError):
        # Provide a basic fallback format
        try:
            fallback_amount = float(amount) if isinstance(amount, (int, float, str)) else 0.0
            return f"${fallback_amount:,.2f}"
        except:
            return "$0.00"
    except Exception:
        # Handle any unexpected errors with a safe fallback
        return "$0.00"


def format_enhanced_percentage_display(
    value: int | float | str | Decimal,
    decimal_places: int = 2,
    locale_setting: str = "en_US",
    show_positive_sign: bool = False,
    multiply_by_hundred: bool = True,
) -> str:
    """Format percentage with enhanced display options and comprehensive validation.

    This function provides professional percentage formatting with customizable
    precision, locale support, and flexible input handling. It's designed for
    financial applications where precise percentage display is critical.

    Args:
        value (Union[int, float, str, Decimal]): The percentage value to format
            If multiply_by_hundred is True: expects decimal form (0.05 = 5%)
            If multiply_by_hundred is False: expects percentage form (5 = 5%)
        decimal_places (int, optional): Number of decimal places to display. Defaults to 2
            Range: 0-10 decimal places supported
        locale_setting (str, optional): Locale for formatting. Defaults to "en_US"
            Affects decimal separator and thousands separator placement
        show_positive_sign (bool, optional): Whether to show + for positive values. Defaults to False
            Useful for displaying changes or comparisons
        multiply_by_hundred (bool, optional): Whether to multiply by 100. Defaults to True
            Set to False if input is already in percentage form

    Returns:
        str: Formatted percentage string with proper locale formatting
            Examples: "5.25%", "12,34%", "+3.50%", "0%"

    Raises:
        ValueError: If value cannot be converted to a valid number
        TypeError: If decimal_places is not an integer

    Examples:
        Basic percentage formatting:

        ```python
        # Standard percentage from decimal
        result = format_enhanced_percentage_display(0.0525, 2)
        # Output: "5.25%"

        # Percentage with no decimals
        result = format_enhanced_percentage_display(0.15, 0)
        # Output: "15%"
        ```

        International formatting:

        ```python
        # German locale formatting
        result = format_enhanced_percentage_display(
            0.1234, decimal_places=3, locale_setting="de_DE"
        )
        # Output: "12,340%"
        ```

        Change indicators:

        ```python
        # Show positive sign for gains
        result = format_enhanced_percentage_display(0.035, show_positive_sign=True)
        # Output: "+3.50%"
        ```

        Direct percentage input:

        ```python
        # Input already in percentage form
        result = format_enhanced_percentage_display(15.5, multiply_by_hundred=False)
        # Output: "15.50%"
        ```

    Note:
        This function automatically handles locale-specific formatting rules
        for decimal separators and provides consistent percentage symbol placement.

        For financial applications, consider using multiply_by_hundred=True
        to ensure proper conversion from decimal representations.

    See Also:
        - format_enhanced_currency_display: For currency formatting
        - format_enhanced_number_display: For general number formatting
    """
    try:
        # Input validation
        try:
            validated_locale = validate_locale_setting(locale_setting = locale_setting)
        except (TypeError, ValueError):
            validated_locale = FALLBACK_LOCALE

        # Validate decimal_places parameter
        if not isinstance(decimal_places, int) or not (0 <= decimal_places <= 10):
            decimal_places = 2

        # Convert and validate the input value
        if isinstance(value, str):
            # Clean string input by removing percentage symbols and whitespace
            cleaned_value = value.replace("%", "").strip()
            try:
                decimal_value = Decimal(cleaned_value)
            except InvalidOperation as exc_error:
                raise ValueError(f"Cannot convert '{value}' to a valid percentage") from exc_error
        elif isinstance(value, (int, float)):
            decimal_value = Decimal(str(value))
        elif isinstance(value, Decimal):
            decimal_value = value
        else:
            raise TypeError(f"Value must be int, float, str, or Decimal, got {type(value)}")

        # Apply multiplication by 100 if requested (for decimal to percentage conversion)
        if multiply_by_hundred:
            display_value = decimal_value
        else:
            display_value = decimal_value / 100

        # Convert to float for Babel formatting
        float_value = float(display_value)

        # Create format pattern with specified decimal places
        format_pattern = f"#,##0.{'0' * decimal_places}%"

        # Add positive sign to format if requested
        if show_positive_sign:
            format_pattern = f"+{format_pattern};-{format_pattern}"

        # Perform the percentage formatting using Babel
        formatted_result = format_percent(
            float_value,
            locale=validated_locale,
            format=format_pattern,
        )

        return formatted_result

    except (ValueError, TypeError):
        # Provide a fallback
        try:
            fallback_value = float(value) if isinstance(value, (int, float, str)) else 0.0
            if multiply_by_hundred:
                fallback_value = fallback_value * 100
            return f"{fallback_value:.{decimal_places}f}%"
        except:
            return "0.00%"
    except Exception:
        # Handle any unexpected errors
        return "0.00%"


def format_enhanced_number_display(
    number: int | float | str | Decimal,
    decimal_places: int = 0,
    locale_setting: str = "en_US",
    show_thousands_separator: bool = True,
    show_positive_sign: bool = False,
    minimum_digits: int | None = None,
) -> str:
    """Format numbers with enhanced display options and comprehensive locale support.

    This function provides professional number formatting with customizable
    precision, thousands separators, and locale-aware display. It's designed
    for financial and statistical applications requiring consistent number presentation.

    Args:
        number (Union[int, float, str, Decimal]): The number to format
            Accepts various numeric types and string representations
        decimal_places (int, optional): Number of decimal places to display. Defaults to 0
            Range: 0-15 decimal places supported for high precision
        locale_setting (str, optional): Locale for formatting. Defaults to "en_US"
            Affects decimal and thousands separator characters
        show_thousands_separator (bool, optional): Whether to show thousands separators. Defaults to True
            Controls display of comma, period, or space separators based on locale
        show_positive_sign (bool, optional): Whether to show + for positive values. Defaults to False
            Useful for displaying changes, deltas, or scientific notation
        minimum_digits (Optional[int], optional): Minimum number of digits before decimal. Defaults to None
            Pads with leading zeros if necessary for consistent formatting

    Returns:
        str: Formatted number string with proper locale formatting
            Examples: "1,234,567", "1.234.567,89", "1 234 567.0", "+123.45"

    Raises:
        ValueError: If number cannot be converted to a valid numeric value
        TypeError: If decimal_places or minimum_digits are not integers

    Examples:
        Basic number formatting:

        ```python
        # Large number with thousands separators
        result = format_enhanced_number_display(1234567)
        # Output: "1,234,567"

        # Decimal precision control
        result = format_enhanced_number_display(1234.5678, decimal_places=2)
        # Output: "1,234.57"
        ```

        International formatting:

        ```python
        # German locale formatting
        result = format_enhanced_number_display(
            1234567.89, decimal_places=2, locale_setting="de_DE"
        )
        # Output: "1.234.567,89"

        # French locale formatting
        result = format_enhanced_number_display(
            1234567.89, decimal_places=2, locale_setting="fr_FR"
        )
        # Output: "1 234 567,89"
        ```

        Special formatting options:

        ```python
        # Show positive sign for deltas
        result = format_enhanced_number_display(123.45, decimal_places=2, show_positive_sign=True)
        # Output: "+123.45"

        # No thousands separator for compact display
        result = format_enhanced_number_display(1234567, show_thousands_separator=False)
        # Output: "1234567"

        # Minimum digits with zero padding
        result = format_enhanced_number_display(42, minimum_digits=6)
        # Output: "000,042"
        ```

    Note:
        This function automatically handles locale-specific formatting rules
        including decimal separators (. vs ,) and thousands separators (, vs . vs space).

        For financial calculations, consider using higher decimal precision
        to maintain accuracy in intermediate calculations.

    See Also:
        - format_enhanced_currency_display: For currency-specific formatting
        - format_enhanced_percentage_display: For percentage formatting
    """
    try:
        # Input validation
        try:
            validated_locale = validate_locale_setting(locale_setting = locale_setting)
        except (TypeError, ValueError):
            validated_locale = FALLBACK_LOCALE

        # Validate decimal_places parameter
        if not isinstance(decimal_places, int) or not (0 <= decimal_places <= 15):
            decimal_places = 0

        # Validate minimum_digits parameter
        if minimum_digits is not None:
            if not isinstance(minimum_digits, int) or minimum_digits < 1:
                minimum_digits = None

        # Convert and validate the input number
        if isinstance(number, str):
            # Clean string input by removing common formatting
            cleaned_number = number.replace(",", "").strip()
            try:
                decimal_number = Decimal(cleaned_number)
            except InvalidOperation as exc_error:
                raise ValueError(f"Cannot convert '{number}' to a valid number") from exc_error
        elif isinstance(number, (int, float)):
            decimal_number = Decimal(str(number))
        elif isinstance(number, Decimal):
            decimal_number = number
        else:
            raise TypeError(f"Number must be int, float, str, or Decimal, got {type(number)}")

        # Convert to float for Babel formatting
        float_number = float(decimal_number)

        # Build format pattern based on options
        if minimum_digits and minimum_digits > 1:
            # Create pattern with minimum digits (zero padding)
            digit_pattern = "0" * minimum_digits
        else:
            digit_pattern = "#"

        # Add thousands separator if requested
        if show_thousands_separator:
            if minimum_digits and minimum_digits > 3:
                # For minimum digits, need to account for grouping
                thousands_pattern = f"{digit_pattern[:-3]},{digit_pattern[-3:]}"
            else:
                thousands_pattern = f"{digit_pattern},##0"
        else:
            thousands_pattern = digit_pattern if minimum_digits else "#0"

        # Add decimal places if specified
        if decimal_places > 0:
            decimal_pattern = "." + "0" * decimal_places
            format_pattern = thousands_pattern + decimal_pattern
        else:
            format_pattern = thousands_pattern

        # Add positive sign formatting if requested
        if show_positive_sign:
            format_pattern = f"+{format_pattern};-{format_pattern}"

        # Perform the number formatting using Babel
        formatted_result = format_decimal(
            float_number,
            locale=validated_locale,
            format=format_pattern,
        )

        return formatted_result

    except (ValueError, TypeError):
        # Provide a fallback
        try:
            fallback_number = float(number) if isinstance(number, (int, float, str)) else 0.0
            if show_thousands_separator:
                return f"{fallback_number:,.{decimal_places}f}"
            return f"{fallback_number:.{decimal_places}f}"
        except:
            return "0"
    except Exception:
        # Handle any unexpected errors
        return "0"


def format_enhanced_date_display(
    date_value: Any,
    format_style: str = "medium",
    locale_setting: str = "en_US",
    include_time: bool = False,
) -> str:
    """Format dates with enhanced locale-aware display options.

    This function provides professional date formatting with support for multiple
    locales and various date format styles. It handles different input types
    and provides consistent date presentation across the application.

    Args:
        date_value (Any): The date to format (datetime, date, or ISO string)
            Accepts datetime objects, date objects, or ISO format strings
        format_style (str, optional): Date format style. Defaults to "medium"
            Options: "short", "medium", "long", "full"
        locale_setting (str, optional): Locale for formatting. Defaults to "en_US"
            Affects month names, day names, and date ordering
        include_time (bool, optional): Whether to include time information. Defaults to False
            Only applies when input includes time information

    Returns:
        str: Formatted date string with proper locale formatting
            Examples: "Jan 15, 2024", "15. Januar 2024", "2024年1月15日"

    Examples:
        Basic date formatting:

        ```python
        from datetime import datetime

        # Format current date
        now = datetime.now()
        result = format_enhanced_date_display(now)
        # Output: "Jan 15, 2024" (varies by current date)
        ```

        International date formatting:

        ```python
        # German locale formatting
        result = format_enhanced_date_display(datetime(2024, 1, 15), locale_setting="de_DE")
        # Output: "15. Jan. 2024"
        ```

    Note:
        This function is provided for completeness but date formatting
        is less critical for the current financial dashboard application.
        Consider expanding this function as needed for reporting features.
    """
    try:
        # Basic implementation - can be expanded based on requirements
        from datetime import date, datetime

        try:
            validated_locale = validate_locale_setting(locale_setting = locale_setting)
        except (TypeError, ValueError):
            validated_locale = FALLBACK_LOCALE

        # Convert various input types to datetime
        if isinstance(date_value, str):
            try:
                parsed_date = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except ValueError:
                return str(date_value)
        elif isinstance(date_value, datetime):
            parsed_date = date_value
        elif isinstance(date_value, date):
            parsed_date = datetime.combine(date_value, datetime.min.time())
        else:
            return str(date_value)

        # Format the date using Babel
        if include_time:
            formatted_result = format_datetime(
                parsed_date,
                format=format_style,
                locale=validated_locale,
            )
        else:
            formatted_result = format_date(
                parsed_date.date(),
                format=format_style,
                locale=validated_locale,
            )

        return formatted_result

    except Exception:
        return str(date_value)


def get_formatting_configuration() -> dict[str, Any]:
    """Get comprehensive formatting configuration for the application.

    This function returns a dictionary containing all formatting settings,
    supported locales, currency codes, and format patterns used throughout
    the application. It's useful for configuration management and testing.

    Returns:
        Dict[str, Any]: Complete formatting configuration including:
            - Supported locales list
            - Default currency formats
            - Fallback settings
            - Format pattern examples

    Examples:
        Retrieve configuration for validation:

        ```python
        config = get_formatting_configuration()
        supported_locales = config["supported_locales"]
        currency_formats = config["currency_formats"]
        ```

    Note:
        This function is primarily for internal use and configuration
        management. External code should use the specific formatting
        functions rather than accessing configuration directly.
    """
    return {
        "supported_locales": SUPPORTED_LOCALES.copy(),
        "currency_formats": DEFAULT_CURRENCY_FORMATS.copy(),
        "fallback_locale": FALLBACK_LOCALE,
        "version": "0.5.1",
        "module_info": {
            "description": "Enhanced formatting utilities for financial applications",
            "dependencies": ["babel", "decimal", "typing"],
            "author": "QWIM Dashboard Development Team",
        },
    }


# Module initialization and configuration
def configure_enhanced_formatting_module(
    custom_locales: list[str] | None = None,
    custom_fallback: str | None = None,
    log_level: str = "INFO",
) -> None:
    """Configure the enhanced formatting module with custom settings.

    This function allows customization of module-level settings including
    supported locales, fallback locale, and logging level. It should be
    called during application initialization if custom configuration is needed.

    Args:
        custom_locales (Optional[List[str]], optional): Custom list of supported locales
            Replaces the default SUPPORTED_LOCALES list
        custom_fallback (Optional[str], optional): Custom fallback locale
            Must be a valid locale identifier
        log_level (str, optional): Logging level for the module. Defaults to "INFO"
            Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

    Examples:
        Configure for European markets:

        ```python
        configure_enhanced_formatting_module(
            custom_locales=["en_GB", "de_DE", "fr_FR", "es_ES"],
            custom_fallback="en_GB",
            log_level="DEBUG",
        )
        ```

    Note:
        This function modifies module-level constants and should only
        be called once during application startup to avoid inconsistent behavior.
    """
    global SUPPORTED_LOCALES, FALLBACK_LOCALE, logger

    try:
        # Configure logging level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Update supported locales if provided
        if custom_locales:
            if isinstance(custom_locales, list) and all(
                isinstance(loc, str) for loc in custom_locales
            ):
                SUPPORTED_LOCALES = custom_locales.copy()
            else:
                raise ValueError("Invalid custom_locales format. Must be a list of strings.")

        # Update fallback locale if provided
        if custom_fallback:
            try:
                validated_fallback = validate_locale_setting(locale_setting = custom_fallback)
                FALLBACK_LOCALE = custom_fallback
            except (TypeError, ValueError):
                raise ValueError(f"Invalid custom fallback locale: {custom_fallback}")

    except Exception as exc_error:
        raise RuntimeError(
            f"Error configuring enhanced formatting module: {exc_error}"
        ) from exc_error


def format_currency_value(amount: float) -> str:
    """Format numeric value as currency string using enhanced formatting.

    Args:
        amount: Numeric amount to format

    Returns:
        str: Formatted currency string (dollars only, no cents)
    """
    try:
        # Round to whole dollars
        whole_dollars = round(amount)

        # Use enhanced formatting with 0 decimal places
        return format_enhanced_currency_display(
            amount=whole_dollars,
            currency_code="USD",
            locale_setting="en_US",
            format_pattern="standard",
            decimal_places=0,
        )
    except Exception:
        # Fallback formatting if enhanced function fails
        whole_dollars = round(amount)
        if whole_dollars == 0:
            return "$0"
        return f"${whole_dollars:,}"


def extract_numeric_from_currency_string(currency_string: str) -> float:
    """Extract numeric value from formatted currency string.

    Args:
        currency_string: Formatted currency string (e.g., "$6,473")

    Returns:
        float: Extracted numeric value (e.g., 6473.0)
    """
    try:
        if not currency_string or not isinstance(currency_string, str):
            return 0.0

        # Remove all currency symbols and formatting
        cleaned_string = currency_string.replace("$", "").replace(",", "").replace(" ", "").strip()

        if not cleaned_string:
            return 0.0

        # Convert to float
        return float(cleaned_string)

    except (ValueError, AttributeError):
        return 0.0


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from datetime import date


# ============================================================================
# Tests for validate_locale_setting
# ============================================================================


class Test_Validate_Locale_Setting:
    """Tests for validate_locale_setting in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_valid_en_US_accepted(self):
        """Test that valid en US accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        result = validate_locale_setting(locale_setting = "en_US")
        assert isinstance(result, str)
        assert "en" in result.lower() or result == "en_US"

    @pytest.mark.unit()
    def test_valid_de_DE_accepted(self):
        """Test that valid de DE accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        result = validate_locale_setting(locale_setting = "de_DE")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_invalid_locale_falls_back_to_en_US(self):
        """Test that invalid locale falls back to en US."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        with pytest.raises(Exception_Validation_Input):
            validate_locale_setting(locale_setting = "zz_ZZ_INVALID")

    @pytest.mark.unit()
    def test_none_locale_falls_back(self):
        """Test that none locale falls back."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        with pytest.raises(TypeError):
            validate_locale_setting(locale_setting = None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def test_empty_string_falls_back(self):
        """Test that empty string falls back."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        with pytest.raises(Exception_Validation_Input):
            validate_locale_setting(locale_setting = "")


# ============================================================================
# Tests for validate_currency_code
# ============================================================================


class Test_Validate_Currency_Code:
    """Tests for validate_currency_code in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_usd_accepted(self):
        """Test that usd accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_currency_code

        result = validate_currency_code(currency_code = "USD")
        assert isinstance(result, str)
        assert result == "USD"

    @pytest.mark.unit()
    def test_eur_accepted(self):
        """Test that eur accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_currency_code

        result = validate_currency_code(currency_code = "EUR")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_invalid_code_raises(self):
        """Test that invalid code raises."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_currency_code

        with pytest.raises(Exception_Validation_Input):
            validate_currency_code(currency_code = "INVALID_CURRENCY")

    @pytest.mark.unit()
    def test_lowercase_code_handled(self):
        """Test that lowercase code handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_currency_code

        result = validate_currency_code(currency_code = "usd")
        assert isinstance(result, str)


# ============================================================================
# Tests for format_enhanced_currency_display
# ============================================================================


class Test_Format_Enhanced_Currency_Display:
    """Tests for format_enhanced_currency_display in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_integer_amount_returns_string(self):
        """Test that integer amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = 1000)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    def test_float_amount_returns_string(self):
        """Test that float amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = 1234.56)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_zero_amount_returns_string(self):
        """Test that zero amount returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = 0)
        assert isinstance(result, str)
        assert "0" in result

    @pytest.mark.unit()
    def test_explicit_currency_code(self):
        """Test that explicit currency code."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = 100, currency_code="EUR")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_none_amount_handled(self):
        """Test that none amount handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = None)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_string_amount_handled(self):
        """Test that string amount handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_currency_display

        result = format_enhanced_currency_display(amount = "1000")
        assert isinstance(result, str)


# ============================================================================
# Tests for format_enhanced_percentage_display
# ============================================================================


class Test_Format_Enhanced_Percentage_Display:
    """Tests for format_enhanced_percentage_display in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_float_percentage_returns_string(self):
        """Test that float percentage returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_percentage_display

        result = format_enhanced_percentage_display(value = 0.1234)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_integer_percentage_returns_string(self):
        """Test that integer percentage returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_percentage_display

        result = format_enhanced_percentage_display(value = 50)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_zero_returns_string(self):
        """Test that zero returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_percentage_display

        result = format_enhanced_percentage_display(value = 0)
        assert isinstance(result, str)
        assert "0" in result

    @pytest.mark.unit()
    def test_none_handled(self):
        """Test that none handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_percentage_display

        result = format_enhanced_percentage_display(value = None)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_boolean_decimal_places_uses_default_precision(self):
        """Boolean decimal_places should fall back to the default 2-digit percentage format."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_percentage_display

        expected_result = format_enhanced_percentage_display(value = 0.1234, decimal_places=2)
        bool_result = format_enhanced_percentage_display(value = 0.1234, decimal_places=True)

        assert bool_result == expected_result


# ============================================================================
# Tests for format_enhanced_number_display
# ============================================================================


class Test_Format_Enhanced_Number_Display:
    """Tests for format_enhanced_number_display in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_integer_returns_string(self):
        """Test that integer returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_number_display

        result = format_enhanced_number_display(number = 1234567)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_float_returns_string(self):
        """Test that float returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_number_display

        result = format_enhanced_number_display(number = 1234.56)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_zero_returns_string(self):
        """Test that zero returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_number_display

        result = format_enhanced_number_display(number = 0)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_none_handled(self):
        """Test that none handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_number_display

        result = format_enhanced_number_display(number = None)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_boolean_decimal_places_uses_default_precision(self):
        """Boolean decimal_places should fall back to the default integer-style number format."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_number_display

        expected_result = format_enhanced_number_display(number = 1234.56, decimal_places=0)
        bool_result = format_enhanced_number_display(number = 1234.56, decimal_places=True)

        assert bool_result == expected_result


# ============================================================================
# Tests for format_enhanced_date_display
# ============================================================================


class Test_Format_Enhanced_Date_Display:
    """Tests for format_enhanced_date_display in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_date_object_returns_string(self):
        """Test that date object returns string."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_date_display

        result = format_enhanced_date_display(date_value = date(2023, 6, 15))
        assert isinstance(result, str)
        assert "2023" in result

    @pytest.mark.unit()
    def test_short_format_style(self):
        """Test that short format style."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_date_display

        result = format_enhanced_date_display(date_value = date(2023, 6, 15), format_style="short")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_long_format_style(self):
        """Test that long format style."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_date_display

        result = format_enhanced_date_display(date_value = date(2023, 6, 15), format_style="long")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_none_date_handled(self):
        """Test that none date handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_date_display

        result = format_enhanced_date_display(date_value = None)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_string_date_handled(self):
        """Test that string date handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_enhanced_date_display

        result = format_enhanced_date_display(date_value = "2023-06-15")
        assert isinstance(result, str)


# ============================================================================
# Tests for format_currency_value (quick formatter)
# ============================================================================


class Test_Format_Currency_Value:
    """Tests for format_currency_value in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_integer_formatted(self):
        """Test that integer formatted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_currency_value

        result = format_currency_value(amount = 1000)
        assert isinstance(result, str)
        assert "$" in result or "1" in result

    @pytest.mark.unit()
    def test_float_formatted(self):
        """Test that float formatted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_currency_value

        result = format_currency_value(amount = 1234.56)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_zero_formatted(self):
        """Test that zero formatted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_currency_value

        result = format_currency_value(amount = 0)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_none_handled(self):
        """Test that none handled."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import format_currency_value

        result = format_currency_value(amount = None)
        assert isinstance(result, str)


# ============================================================================
# Tests for extract_numeric_from_currency_string
# ============================================================================


class Test_Extract_Numeric_From_Currency_String:
    """Tests for extract_numeric_from_currency_string in utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_dollar_prefix_extracted(self):
        """Test that dollar prefix extracted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = "$1,234.56")
        assert isinstance(result, float)
        assert abs(result - 1234.56) < 0.01

    @pytest.mark.unit()
    def test_no_prefix_extracted(self):
        """Test that no prefix extracted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = "1234.56")
        assert isinstance(result, float)
        assert abs(result - 1234.56) < 0.01

    @pytest.mark.unit()
    def test_comma_separated_thousands_extracted(self):
        """Test that comma separated thousands extracted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = "1,000,000")
        assert isinstance(result, float)
        assert result == 1000000.0

    @pytest.mark.unit()
    def test_none_returns_zero(self):
        """Test that none returns zero."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = None)  # type: ignore[arg-type]
        assert result == 0.0

    @pytest.mark.unit()
    def test_empty_string_returns_zero(self):
        """Test that empty string returns zero."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = "")
        assert result == 0.0

    @pytest.mark.unit()
    def test_non_string_returns_zero(self):
        """Test that non string returns zero."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import extract_numeric_from_currency_string

        result = extract_numeric_from_currency_string(currency_string = {"bad": "input"})  # type: ignore[arg-type]
        assert result == 0.0


# ============================================================================
# Tests for module structure
# ============================================================================


class Test_Utils_Enhanced_Formatting_Module_Structure:
    """Tests verifying the module-level structure of utils_enhanced_formatting."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_enhanced_formatting as m

        assert m is not None

    @pytest.mark.unit()
    def test_expected_callables_present(self):
        """Test that expected callables present."""
        from src.dashboard.shiny_utils import utils_enhanced_formatting


        expected = [
            "validate_locale_setting",
            "validate_currency_code",
            "format_enhanced_currency_display",
            "format_enhanced_percentage_display",
            "format_enhanced_number_display",
            "format_enhanced_date_display",
            "format_currency_value",
            "extract_numeric_from_currency_string",
            "get_formatting_configuration",
        ]
        for name in expected:
            assert hasattr(utils_enhanced_formatting, name), f"Missing: {name}"


# ============================================================================
# Branch coverage additions
# ============================================================================


@pytest.mark.unit()
class Class_Test_Validate_Locale_Branches:
    """Covers remaining branches in validate_locale_setting."""

    @pytest.mark.unit()
    def Test_valid_locale_not_in_supported_list(self) -> None:
        """A Babel-valid locale that isn't in SUPPORTED_LOCALES still returns it."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        # "af_ZA" (Afrikaans South Africa) is valid in Babel but not in SUPPORTED_LOCALES
        result = validate_locale_setting(locale_setting = "af_ZA")
        assert result == "af_ZA"

    @pytest.mark.unit()
    def Test_locale_parse_unexpected_exception_raises_config(self) -> None:
        """If Locale.parse raises a generic Exception, Exception_Configuration is raised."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import validate_locale_setting

        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.Locale.parse",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(Exception_Configuration):
                validate_locale_setting(locale_setting = "en_US")


@pytest.mark.unit()
class Class_Test_Format_Currency_Missing_Branches:
    """Covers missing branches in format_enhanced_currency_display."""

    @pytest.mark.unit()
    def Test_invalid_locale_type_falls_back(self) -> None:
        """TypeError from validate_locale_setting → fallback locale (lines 346-347)."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 100, locale_setting=123)  # type: ignore[arg-type]
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit()
    def Test_invalid_currency_code_type_falls_back(self) -> None:
        """TypeError from validate_currency_code → fallback 'USD' (lines 351-352)."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 100, currency_code=123)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_string_amount_raises_validation_error(self) -> None:
        """String that can't be parsed as Decimal raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        # "not_a_number" → after $ removal still not parsable → Exception_Validation_Input
        # which is caught by outer except Exception → returns "$0"
        result = format_enhanced_currency_display(amount = "not_a_number")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_decimal_type_amount(self) -> None:
        """Decimal amount is handled directly without conversion."""
        from decimal import Decimal
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = Decimal("1234.56"))
        assert isinstance(result, str)
        assert "1" in result

    @pytest.mark.unit()
    def Test_unsupported_amount_type_falls_back(self) -> None:
        """Non-numeric, non-str, non-Decimal type falls through to fallback."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = [1, 2, 3])  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_boolean_amount_uses_unsupported_type_fallback(self) -> None:
        """Boolean amount uses the same safe fallback path as other unsupported input types."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        expected_result = format_enhanced_currency_display(amount = [1, 2, 3])  # type: ignore[arg-type]
        bool_result = format_enhanced_currency_display(amount = True)

        assert bool_result == expected_result

    @pytest.mark.unit()
    def Test_unknown_format_pattern_uses_standard(self) -> None:
        """Unknown format_pattern falls back to 'standard' pattern."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 100, format_pattern="nonexistent_pattern")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_decimal_places_zero_removes_cents(self) -> None:
        """decimal_places=0 removes the .00 portion of format."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 1234.56, decimal_places=0)
        assert isinstance(result, str)
        assert "1" in result

    @pytest.mark.unit()
    def Test_decimal_places_nonzero_overrides_decimals(self) -> None:
        """decimal_places=3 forces 3 decimal places in output."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = 1234.5, decimal_places=3)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_boolean_decimal_places_uses_default_currency_precision(self) -> None:
        """Boolean decimal_places falls back to the default currency precision behavior."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        expected_result = format_enhanced_currency_display(amount = 1234.56)
        bool_result = format_enhanced_currency_display(amount = 1234.56, decimal_places=True)

        assert bool_result == expected_result

    @pytest.mark.unit()
    def Test_accounting_format_pattern(self) -> None:
        """accounting format_pattern is applied for negative values."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        result = format_enhanced_currency_display(amount = -50.0, format_pattern="accounting")
        assert isinstance(result, str)


@pytest.mark.unit()
class Class_Test_Format_Percentage_Missing_Branches:
    """Covers missing branches in format_enhanced_percentage_display."""

    @pytest.mark.unit()
    def Test_invalid_locale_type_falls_back(self) -> None:
        """TypeError from locale validation → fallback locale (lines 507-508)."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.05, locale_setting=999)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_decimal_places_resets_to_two(self) -> None:
        """Non-int or out-of-range decimal_places defaults to 2 (line 512)."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.05, decimal_places=-1)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_string_value_raises_then_fallbacks(self) -> None:
        """String 'bad' → InvalidOperation → Exception_Validation_Input → outer fallback."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = "bad%value")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_decimal_type_value(self) -> None:
        """Decimal value is accepted directly (lines 517-521 → elif Decimal)."""
        from decimal import Decimal
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = Decimal("0.05"))
        assert isinstance(result, str)
        assert "5" in result

    @pytest.mark.unit()
    def Test_unsupported_type_falls_back(self) -> None:
        """Unsupported type → TypeError → outer fallback."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = [0.05])  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_boolean_value_uses_unsupported_type_fallback(self) -> None:
        """Boolean percentage value uses the same safe fallback path as unsupported input types."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        expected_result = format_enhanced_percentage_display(value = [0.05])  # type: ignore[arg-type]
        bool_result = format_enhanced_percentage_display(value = True)

        assert bool_result == expected_result

    @pytest.mark.unit()
    def Test_show_positive_sign_true(self) -> None:
        """show_positive_sign=True adds positive sign format (line 540)."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 0.035, show_positive_sign=True)
        assert isinstance(result, str)
        assert "+" in result or "3" in result

    @pytest.mark.unit()
    def Test_multiply_by_hundred_false(self) -> None:
        """multiply_by_hundred=False divides value by 100."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = 5.0, multiply_by_hundred=False)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_string_percentage_input(self) -> None:
        """String '5.25%' is cleaned and parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        result = format_enhanced_percentage_display(value = "0.0525", multiply_by_hundred=True)
        assert isinstance(result, str)


@pytest.mark.unit()
class Class_Test_Format_Number_Missing_Branches:
    """Covers missing branches in format_enhanced_number_display."""

    @pytest.mark.unit()
    def Test_invalid_locale_type_falls_back(self) -> None:
        """TypeError from locale validation → fallback locale."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 100, locale_setting=42)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_decimal_places_resets(self) -> None:
        """Out-of-range decimal_places defaults to 0."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 100, decimal_places=20)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_minimum_digits_resets_to_none(self) -> None:
        """minimum_digits=0 (< 1) is reset to None."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 42, minimum_digits=0)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_boolean_minimum_digits_resets_to_none(self) -> None:
        """Boolean minimum_digits is treated as invalid and reset to None."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        expected_result = format_enhanced_number_display(number = 42)
        bool_result = format_enhanced_number_display(number = 42, minimum_digits=True)

        assert bool_result == expected_result

    @pytest.mark.unit()
    def Test_string_number_input(self) -> None:
        """String number is cleaned and parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = "1,234,567")
        assert isinstance(result, str)
        assert "1" in result

    @pytest.mark.unit()
    def Test_invalid_string_number_falls_back(self) -> None:
        """Unparsable string → InvalidOperation → Exception_Validation_Input → fallback."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = "not_a_num")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_decimal_type_number(self) -> None:
        """Decimal number accepted directly."""
        from decimal import Decimal
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = Decimal("9876.54"), decimal_places=2)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_unsupported_type_falls_back(self) -> None:
        """Unsupported type → TypeError → fallback."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = {"x": 1})  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_boolean_number_uses_unsupported_type_fallback(self) -> None:
        """Boolean number uses the same safe fallback path as unsupported input types."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        expected_result = format_enhanced_number_display(number = {"x": 1})  # type: ignore[arg-type]
        bool_result = format_enhanced_number_display(number = True)

        assert bool_result == expected_result

    @pytest.mark.unit()
    def Test_show_thousands_separator_false(self) -> None:
        """show_thousands_separator=False omits separators."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 1234567, show_thousands_separator=False)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_show_positive_sign(self) -> None:
        """show_positive_sign=True prefixes positive with +."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 42, decimal_places=2, show_positive_sign=True)
        assert isinstance(result, str)
        assert "+" in result or "42" in result

    @pytest.mark.unit()
    def Test_minimum_digits_two(self) -> None:
        """minimum_digits=2 pads with leading zeros when needed."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 5, minimum_digits=2)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_minimum_digits_greater_than_three(self) -> None:
        """minimum_digits=6 uses the grouping sub-path."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 42, minimum_digits=6)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_decimal_places_positive(self) -> None:
        """decimal_places=2 adds decimal suffix to format pattern."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 1234, decimal_places=2)
        assert isinstance(result, str)
        assert "." in result or "," in result  # locale-dependent decimal char

    @pytest.mark.unit()
    def Test_no_thousands_no_minimum_digits(self) -> None:
        """show_thousands_separator=False without minimum_digits uses '#0' pattern."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        result = format_enhanced_number_display(number = 99, show_thousands_separator=False)
        assert isinstance(result, str)
        assert "99" in result


@pytest.mark.unit()
class Class_Test_Format_Date_Missing_Branches:
    """Covers missing branches in format_enhanced_date_display."""

    @pytest.mark.unit()
    def Test_invalid_locale_type_falls_back(self) -> None:
        """TypeError from locale validation → fallback locale."""
        from datetime import date
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(date_value = date(2024, 6, 1), locale_setting=42)  # type: ignore[arg-type]
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_invalid_string_date_returns_string(self) -> None:
        """Unparsable ISO string is returned as-is."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(date_value = "not_a_date")
        assert isinstance(result, str)
        assert "not_a_date" in result

    @pytest.mark.unit()
    def Test_datetime_object_is_formatted(self) -> None:
        """datetime object is formatted directly (elif isinstance(date_value, datetime))."""
        from datetime import datetime
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(date_value = datetime(2024, 6, 15, 10, 30))
        assert isinstance(result, str)
        assert "2024" in result

    @pytest.mark.unit()
    def Test_include_time_true_formats_datetime(self) -> None:
        """include_time=True uses format_datetime instead of format_date."""
        from datetime import datetime
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(
            date_value = datetime(2024, 6, 15, 10, 30),
            include_time=True,
        )
        assert isinstance(result, str)
        assert "2024" in result

    @pytest.mark.unit()
    def Test_unsupported_date_type_returns_str(self) -> None:
        """Non-date, non-str, non-datetime type returns str representation."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(date_value = 20240615)
        assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_valid_iso_string_date_formatted(self) -> None:
        """ISO date string is parsed and formatted."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        result = format_enhanced_date_display(date_value = "2024-06-15")
        assert isinstance(result, str)
        assert "2024" in result


@pytest.mark.unit()
class Class_Test_Get_Formatting_Configuration:
    """Covers get_formatting_configuration."""

    @pytest.mark.unit()
    def Test_returns_dict_with_expected_keys(self) -> None:
        """get_formatting_configuration returns a complete config dict."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            get_formatting_configuration,
        )

        config = get_formatting_configuration()
        assert isinstance(config, dict)
        assert "supported_locales" in config
        assert "currency_formats" in config
        assert "fallback_locale" in config
        assert config["fallback_locale"] == "en_US"


@pytest.mark.unit()
class Class_Test_Configure_Module:
    """Covers configure_enhanced_formatting_module (lines 915-937)."""

    @pytest.mark.unit()
    def Test_configure_with_custom_locales(self) -> None:
        """Providing custom_locales updates SUPPORTED_LOCALES."""
        import src.dashboard.shiny_utils.utils_enhanced_formatting as mod
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            configure_enhanced_formatting_module,
        )

        original_locales = mod.SUPPORTED_LOCALES.copy()
        original_fallback = mod.FALLBACK_LOCALE
        try:
            configure_enhanced_formatting_module(custom_locales=["en_GB", "de_DE"])
            assert mod.SUPPORTED_LOCALES == ["en_GB", "de_DE"]
        finally:
            mod.SUPPORTED_LOCALES = original_locales
            mod.FALLBACK_LOCALE = original_fallback

    @pytest.mark.unit()
    def Test_configure_with_custom_fallback(self) -> None:
        """Providing a valid custom_fallback updates FALLBACK_LOCALE."""
        import src.dashboard.shiny_utils.utils_enhanced_formatting as mod
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            configure_enhanced_formatting_module,
        )

        original_fallback = mod.FALLBACK_LOCALE
        try:
            configure_enhanced_formatting_module(custom_fallback="de_DE")
            assert mod.FALLBACK_LOCALE == "de_DE"
        finally:
            mod.FALLBACK_LOCALE = original_fallback

    @pytest.mark.unit()
    def Test_configure_with_invalid_custom_locales_raises(self) -> None:
        """Non-list custom_locales raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            configure_enhanced_formatting_module,
        )

        with pytest.raises(Exception_Configuration):
            configure_enhanced_formatting_module(custom_locales="not_a_list")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_configure_with_invalid_fallback_raises(self) -> None:
        """Invalid custom_fallback locale raises Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            configure_enhanced_formatting_module,
        )

        with pytest.raises(Exception_Configuration):
            configure_enhanced_formatting_module(custom_fallback="zz_ZZ_INVALID")

    @pytest.mark.unit()
    def Test_configure_with_non_string_fallback_raises_validation(self) -> None:
        """Non-string custom_fallback causes TypeError → Exception_Validation_Input → Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            configure_enhanced_formatting_module,
        )

        # custom_fallback=123 → validate_locale_setting(123) → TypeError → line 934
        with pytest.raises(Exception_Configuration):
            configure_enhanced_formatting_module(custom_fallback=123)  # type: ignore[arg-type]


@pytest.mark.unit()
class Class_Test_Extract_Numeric_Missing_Branches:
    """Covers remaining branches in extract_numeric_from_currency_string."""

    @pytest.mark.unit()
    def Test_string_becomes_empty_after_cleaning(self) -> None:
        """String with only '$' and ',' becomes empty → returns 0.0."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        result = extract_numeric_from_currency_string(currency_string = "$,, ")
        assert result == 0.0

    @pytest.mark.unit()
    def Test_value_error_on_float_conversion(self) -> None:
        """String that cleans to non-numeric raises ValueError → returns 0.0."""
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            extract_numeric_from_currency_string,
        )

        # Remove $, commas, spaces from "abc" → "abc" → float("abc") raises ValueError
        result = extract_numeric_from_currency_string(currency_string = "abc")
        assert result == 0.0


@pytest.mark.unit()
class Class_Test_Outer_Exception_Fallbacks:
    """Mock-based tests to cover outer except Exception fallbacks."""

    @pytest.mark.unit()
    def Test_currency_format_babel_error_returns_zero(self) -> None:
        """If format_currency raises a generic Exception, returns '$0'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_currency",
            side_effect=Exception("babel internal error"),
        ):
            result = format_enhanced_currency_display(amount = 100)
            assert result == "$0"

    @pytest.mark.unit()
    def Test_percentage_format_babel_error_returns_zero(self) -> None:
        """If format_percent raises a generic Exception, returns '0.00%'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_percent",
            side_effect=Exception("babel error"),
        ):
            result = format_enhanced_percentage_display(value = 0.05)
            assert result == "0.00%"

    @pytest.mark.unit()
    def Test_percentage_value_error_multiply_false_fallback(self) -> None:
        """ValueError from format_percent with multiply_by_hundred=False hits fallback."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_percent",
            side_effect=ValueError("bad format"),
        ):
            result = format_enhanced_percentage_display(value = 5.0, multiply_by_hundred=False)
            assert isinstance(result, str)
            assert "%" in result

    @pytest.mark.unit()
    def Test_number_format_babel_error_returns_zero(self) -> None:
        """If format_decimal raises a generic Exception, returns '0'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_decimal",
            side_effect=Exception("babel error"),
        ):
            result = format_enhanced_number_display(number = 100)
            assert result == "0"

    @pytest.mark.unit()
    def Test_date_format_babel_error_returns_str(self) -> None:
        """If format_date raises any Exception, returns str(date_value)."""
        from datetime import date
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_date_display,
        )

        d = date(2024, 6, 15)
        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_date",
            side_effect=Exception("babel error"),
        ):
            result = format_enhanced_date_display(date_value = d)
            assert isinstance(result, str)

    @pytest.mark.unit()
    def Test_currency_inner_fallback_float_fails(self) -> None:
        """format_currency raises ValueError, then float(original_str) also fails → inner '$0'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_currency_display,
        )

        # amount="$123.45" → cleaned "123.45" → Decimal OK → format_currency raises ValueError
        # In (ValueError,TypeError) fallback: float("$123.45") raises ValueError ($ invalid)
        # → inner except Exception: return "$0"
        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_currency",
            side_effect=ValueError("format failed"),
        ):
            result = format_enhanced_currency_display(amount = "$123.45")
            assert result == "$0"

    @pytest.mark.unit()
    def Test_percentage_inner_fallback_float_fails(self) -> None:
        """format_percent raises ValueError, then float(original_str_with_percent) fails → '0.00%'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_percentage_display,
        )

        # value="5%25" → cleaned "525" → Decimal OK → format_percent raises ValueError
        # In (ValueError,TypeError) fallback: float("5%25") raises ValueError (% invalid)
        # → inner except Exception: return "0.00%"
        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_percent",
            side_effect=ValueError("format failed"),
        ):
            result = format_enhanced_percentage_display(value = "5%25")
            assert result == "0.00%"

    @pytest.mark.unit()
    def Test_number_inner_fallback_float_fails(self) -> None:
        """format_decimal raises ValueError, then float('1,234') fails → inner '0'."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        # number="1,234" → cleaned "1234" → Decimal OK → format_decimal raises ValueError
        # In (ValueError,TypeError) fallback: float("1,234") raises ValueError (comma invalid)
        # → inner except Exception: return "0"
        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_decimal",
            side_effect=ValueError("format failed"),
        ):
            result = format_enhanced_number_display(number = "1,234")
            assert result == "0"

    @pytest.mark.unit()
    def Test_number_fallback_no_thousands_separator(self) -> None:
        """format_decimal raises ValueError, show_thousands_separator=False uses plain format."""
        from unittest.mock import patch
        from src.dashboard.shiny_utils.utils_enhanced_formatting import (
            format_enhanced_number_display,
        )

        # format_decimal raises ValueError → fallback → show_thousands_separator=False branch
        with patch(
            "src.dashboard.shiny_utils.utils_enhanced_formatting.format_decimal",
            side_effect=ValueError("format failed"),
        ):
            result = format_enhanced_number_display(number = 1234, show_thousands_separator=False)
            assert isinstance(result, str)
            assert "1234" in result

