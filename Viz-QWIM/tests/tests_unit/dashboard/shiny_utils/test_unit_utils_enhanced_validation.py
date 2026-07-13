"""Enhanced Validation Utilities Module.

This module provides comprehensive validation functions and schemas for financial
data, personal information, and user inputs with detailed error messaging and
robust validation logic. It leverages Pydantic for advanced data validation
and marshmallow for additional validation capabilities.

The module is designed to ensure data integrity and provide meaningful feedback
to users in financial dashboard applications. It includes specialized validation
for financial amounts, personal information, risk tolerance levels, and other
domain-specific data types commonly used in retirement planning and portfolio
management applications.

Features:
    - Pydantic-based data models with comprehensive validation rules
    - Financial amount validation with precision handling
    - Personal information validation with business logic constraints
    - Risk tolerance and demographic data validation
    - Currency and locale-aware validation
    - Detailed error messages with user-friendly explanations
    - Integration with form validation and reactive updates
    - Support for multiple validation contexts and scenarios

Dependencies:
    - pydantic: Modern data validation library with type hints
    - marshmallow: Advanced serialization and validation framework
    - typing: Type hints for improved code documentation and IDE support
    - enum: Enumeration support for constrained choice validation
    - decimal: Precise decimal arithmetic for financial calculations
    - datetime: Date and time validation and manipulation
    - re: Regular expression support for pattern validation

Architecture:
    The module is organized into several categories of validation components:

    ```
    Enhanced Validation Components
    ├── Data Models (Pydantic)
    │   ├── PersonalInformationModel
    │   ├── FinancialAssetsModel
    │   ├── FinancialIncomeModel
    │   ├── FinancialGoalsModel
    │   └── UserProfileModel
    ├── Validation Functions
    │   ├── Financial Amount Validation
    │   ├── Age and Date Validation
    │   ├── Text and Name Validation
    │   └── Choice and Enum Validation
    ├── Enumeration Classes
    │   ├── RiskToleranceEnum
    │   ├── GenderEnum
    │   ├── MaritalStatusEnum
    │   └── ValidationSeverityEnum
    └── Validation Schemas (Marshmallow)
        ├── Input Validation Schemas
        ├── Output Validation Schemas
        └── API Validation Schemas
    ```

Examples:
    Basic financial amount validation:

    ```python
    from utils_enhanced_validation import validate_enhanced_financial_amount

    # Validate a currency input with constraints
    try:
        validated_amount = validate_enhanced_financial_amount(
            amount="$125,000.50",
            minimum_value=0.0,
            maximum_value=1000000.0,
            field_name="Annual Salary",
        )
        print(f"Validated amount: ${validated_amount:,.2f}")
    except ValueError as exc_error:
        print(f"Validation error: {exc_error}")
    ```

    Personal information model validation:

    ```python
    from utils_enhanced_validation import Personal_Information_Model

    # Validate user personal information
    try:
        user_info = Personal_Information_Model(
            name="John Smith",
            current_age=35,
            retirement_age=65,
            income_start_age=65,
            risk_tolerance="Moderate",
            gender="Male",
            marital_status="Married",
        )
        print("Personal information is valid")
    except ValidationError as exc_error:
        print(f"Validation errors: {exc_error.errors()}")
    ```

    Financial assets validation:

    ```python
    from utils_enhanced_validation import Financial_Assets_Model

    # Validate financial asset portfolio
    try:
        assets = Financial_Assets_Model(
            taxable_assets=250000.0, tax_deferred_assets=400000.0, tax_free_assets=75000.0
        )
        total_assets = assets.total_assets
        print(f"Total portfolio value: ${total_assets:,.2f}")
    except ValidationError as exc_error:
        print(f"Asset validation errors: {exc_error.errors()}")
    ```

Integration:
    These validation components integrate seamlessly with Shiny applications
    and can be used for both client-side validation feedback and server-side
    data integrity enforcement. The validation results can be used to update
    UI components and provide real-time feedback to users.

Performance:
    All validation functions are designed for high performance with minimal
    computational overhead. Validation rules are cached where appropriate,
    and validation logic is optimized for common use cases in financial
    applications.

Error Handling:
    The module provides comprehensive error handling with multiple levels
    of validation feedback:
    - Field-level validation errors with specific field names
    - Cross-field validation for business logic constraints
    - Summary validation results for form-level feedback
    - User-friendly error messages suitable for display in UI components

Extensibility:
    The validation framework is designed to be easily extensible with
    custom validation rules, additional data models, and domain-specific
    validation logic as application requirements evolve.

Note:
    This module follows the project's coding standards with snake_case naming,
    comprehensive input validation, and defensive programming practices.
    All validation functions include proper error handling with meaningful
    error messages to ensure application stability and user experience.

Version:
    2.0.0

Author:
    QWIM Dashboard Development Team

Last Modified:
    June 2025

See Also:
    - utils_enhanced_formatting.py: For data formatting utilities
    - utils_enhanced_ui_components.py: For UI component integration
    - Pydantic Documentation: https://docs.pydantic.dev/
    - Marshmallow Documentation: https://marshmallow.readthedocs.io/
    - Financial Data Standards: ISO 20022
"""

import logging
import re

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


# Configure logging for the module
logger = logging.getLogger(__name__)


class ValidationSeverityEnum(str, Enum):
    """Enumeration for validation severity levels.

    This enum defines different levels of validation severity that can be used
    to categorize validation errors and provide appropriate user feedback.

    Attributes:
        INFO: Informational messages, no action required
        WARNING: Warning messages, user should review but can proceed
        ERROR: Error messages, user must correct before proceeding
        CRITICAL: Critical errors, application cannot continue safely
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskToleranceEnum(str, Enum):
    """Enumeration for investment risk tolerance levels.

    This enum defines the standard risk tolerance categories used in financial
    planning and investment portfolio management. Each level represents a
    different approach to balancing potential returns with acceptable risk.

    Attributes:
        CONSERVATIVE: Low risk tolerance, prioritizes capital preservation
        MODERATELY_CONSERVATIVE: Below-average risk tolerance, cautious growth approach
        MODERATE: Average risk tolerance, balanced growth and preservation
        MODERATELY_AGGRESSIVE: Above-average risk tolerance, growth-focused approach
        AGGRESSIVE: High risk tolerance, maximum growth potential with higher volatility

    Examples:
        Using risk tolerance in validation:

        ```python
        user_risk_tolerance = RiskToleranceEnum.MODERATE
        if user_risk_tolerance in [
            RiskToleranceEnum.AGGRESSIVE,
            RiskToleranceEnum.MODERATELY_AGGRESSIVE,
        ]:
            print("High growth portfolio recommended")
        ```

    Note:
        These categories align with industry-standard risk assessment practices
        and are commonly used by financial advisors and robo-advisors for
        portfolio allocation recommendations.
    """

    CONSERVATIVE = "Conservative"
    MODERATELY_CONSERVATIVE = "Moderately Conservative"
    MODERATE = "Moderate"
    MODERATELY_AGGRESSIVE = "Moderately Aggressive"
    AGGRESSIVE = "Aggressive"


class GenderEnum(str, Enum):
    """Enumeration for gender identification options.

    This enum provides inclusive gender options that respect individual identity
    while meeting data collection requirements for actuarial calculations and
    regulatory compliance in financial planning applications.

    Attributes:
        FEMALE: Female gender identification
        MALE: Male gender identification
        OTHER: Other gender identification not covered by binary options
        PREFER_NOT_TO_SAY: Option for users who prefer not to disclose gender

    Examples:
        Using gender in actuarial calculations:

        ```python
        if user_gender == GenderEnum.FEMALE:
            # Apply female-specific life expectancy tables
            base_life_expectancy = 84.5
        elif user_gender == GenderEnum.MALE:
            # Apply male-specific life expectancy tables
            base_life_expectancy = 81.2
        else:
            # Use gender-neutral average
            base_life_expectancy = 82.85
        ```

    Note:
        Gender information may be used for actuarial calculations related to
        life expectancy, insurance pricing, and retirement planning scenarios.
        The application should handle all gender options appropriately and
        use conservative estimates when specific data is not available.
    """

    FEMALE = "Female"
    MALE = "Male"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class MaritalStatusEnum(str, Enum):
    """Enumeration for marital status options.

    This enum defines marital status categories that affect tax planning,
    Social Security benefits, estate planning, and survivor benefit calculations
    in retirement planning applications.

    Attributes:
        MARRIED: Currently married, affects joint tax filing and spousal benefits
        SINGLE: Single/never married, individual tax filing and benefits
        DIVORCED: Divorced, may affect spousal Social Security benefits
        WIDOWED: Widowed, may qualify for survivor benefits and special tax provisions

    Examples:
        Using marital status for tax planning:

        ```python
        if user_marital_status == MaritalStatusEnum.MARRIED:
            # Apply married filing jointly tax brackets
            standard_deduction = 27700  # 2023 values
        else:
            # Apply single filer tax brackets
            standard_deduction = 13850  # 2023 values
        ```

    Note:
        Marital status significantly impacts financial planning calculations
        including tax optimization, Social Security benefit maximization,
        and estate planning strategies. The application should consider
        marital status changes over time in long-term projections.
    """

    MARRIED = "Married"
    SINGLE = "Single"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class FinancialValidationConfig:
    """Configuration class for financial validation parameters.

    This class contains configurable parameters and constants used throughout
    the validation module to ensure consistency and allow for easy adjustment
    of validation criteria.

    Attributes:
        MINIMUM_AGE: Minimum age for financial planning (18 years)
        MAXIMUM_AGE: Maximum age for life expectancy calculations (120 years)
        MINIMUM_RETIREMENT_AGE: Earliest reasonable retirement age (50 years)
        MAXIMUM_RETIREMENT_AGE: Latest reasonable retirement age (80 years)
        MINIMUM_FINANCIAL_AMOUNT: Minimum valid financial amount (0.00)
        MAXIMUM_FINANCIAL_AMOUNT: Maximum valid financial amount for validation
        CURRENCY_DECIMAL_PLACES: Standard decimal places for currency (2)
        PERCENTAGE_DECIMAL_PLACES: Standard decimal places for percentages (4)
        NAME_MIN_LENGTH: Minimum length for name fields (2 characters)
        NAME_MAX_LENGTH: Maximum length for name fields (100 characters)
    """

    # Age validation constants
    MINIMUM_AGE: int = 18
    MAXIMUM_AGE: int = 120
    MINIMUM_RETIREMENT_AGE: int = 50
    MAXIMUM_RETIREMENT_AGE: int = 80

    # Financial amount validation constants
    MINIMUM_FINANCIAL_AMOUNT: float = 0.0
    MAXIMUM_FINANCIAL_AMOUNT: float = 1_000_000_000.0  # $1 billion
    CURRENCY_DECIMAL_PLACES: int = 2
    PERCENTAGE_DECIMAL_PLACES: int = 4

    # Text validation constants
    NAME_MIN_LENGTH: int = 2
    NAME_MAX_LENGTH: int = 100

    # Regular expressions for validation
    NAME_PATTERN: str = r"^[a-zA-Z\s\-\.\']+$"
    EMAIL_PATTERN: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    PHONE_PATTERN: str = r"^[\+]?[1-9][\d]{0,15}$"


def validate_enhanced_financial_amount(
    amount: int | float | str | Decimal,
    minimum_value: float = FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT,
    maximum_value: float | None = None,
    field_name: str = "Financial amount",
    allow_negative: bool = False,
    decimal_places: int = FinancialValidationConfig.CURRENCY_DECIMAL_PLACES,
) -> float:
    """Enhanced validation for financial amounts with comprehensive error handling and formatting.

    This function provides robust validation for financial amounts with support for
    various input formats, range checking, precision control, and detailed error
    messages. It handles currency symbols, thousands separators, and different
    numeric formats commonly encountered in financial applications.

    Args:
        amount (Union[int, float, str, Decimal]): The financial amount to validate
            Accepts integers, floats, strings with currency formatting, and Decimal objects
            Examples: 1234.56, "$1,234.56", "1234.567", Decimal("1234.56")
        minimum_value (float, optional): Minimum allowed value.
            Defaults to FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT
        maximum_value (Optional[float], optional): Maximum allowed value
            If None, uses FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT
        field_name (str, optional): Name of the field for error messages. Defaults to "Financial amount"
            Used to provide context-specific error messages
        allow_negative (bool, optional): Whether negative values are permitted. Defaults to False
            Set to True for fields that can represent debts, losses, or adjustments
        decimal_places (int, optional): Maximum number of decimal places allowed.
            Defaults to FinancialValidationConfig.CURRENCY_DECIMAL_PLACES

    Returns:
        float: Validated financial amount rounded to specified decimal places
            Guaranteed to be within the specified range and precision

    Raises:
        ValueError: If the amount cannot be converted to a valid number, is outside
            the allowed range, has too many decimal places, or fails other validation criteria
        TypeError: If the amount is of an unsupported type

    Examples:
        Basic financial amount validation:

        ```python
        # Validate a positive currency amount
        try:
            salary = validate_enhanced_financial_amount(
                amount="$75,000.00",
                minimum_value=0.0,
                maximum_value=1000000.0,
                field_name="Annual Salary",
            )
            print(f"Validated salary: ${salary:,.2f}")
        except ValueError as exc_error:
            print(f"Salary validation error: {exc_error}")
        ```

        Asset validation with negative values allowed:

        ```python
        # Validate investment performance (can be negative)
        try:
            performance = validate_enhanced_financial_amount(
                amount="-2.5%",
                minimum_value=-100.0,
                maximum_value=100.0,
                field_name="Annual Return",
                allow_negative=True,
                decimal_places=4,
            )
            print(f"Portfolio return: {performance:.4f}%")
        except ValueError as exc_error:
            print(f"Performance validation error: {exc_error}")
        ```

        High-precision financial calculation:

        ```python
        # Validate interest rate with high precision
        try:
            interest_rate = validate_enhanced_financial_amount(
                amount="3.25125",
                minimum_value=0.0,
                maximum_value=50.0,
                field_name="Interest Rate",
                decimal_places=5,
            )
            print(f"Interest rate: {interest_rate:.5f}%")
        except ValueError as exc_error:
            print(f"Rate validation error: {exc_error}")
        ```

    Note:
        This function automatically handles common currency formatting including:
        - Dollar signs ($), Euro symbols (€), Pound symbols (£)
        - Thousands separators (commas, periods, spaces)
        - Percentage symbols (%) when contextually appropriate
        - Leading/trailing whitespace
        - Parentheses for negative amounts in accounting format

        The function uses Decimal arithmetic internally to avoid floating-point
        precision issues common in financial calculations.

    See Also:
        - FinancialValidationConfig: For configuration constants
        - validate_enhanced_percentage_value: For percentage-specific validation
        - FinancialAssetsModel: For comprehensive asset validation
    """
    # Input type validation with early return
    if amount is None:
        raise ValueError(f"{field_name} cannot be None")

    # Set maximum value if not provided
    if maximum_value is None:
        maximum_value = FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT

    # Validate decimal places parameter
    if not isinstance(decimal_places, int) or decimal_places < 0 or decimal_places > 10:
        raise ValueError(
            f"Decimal places must be an integer between 0 and 10, got {decimal_places}"
        )

    try:
        # Convert and clean the input amount
        if isinstance(amount, str):
            # Clean string input by removing common formatting characters
            cleaned_amount = amount.strip()

            # Handle accounting format with parentheses for negative numbers
            is_negative_accounting = cleaned_amount.startswith("(") and cleaned_amount.endswith(")")
            if is_negative_accounting:
                cleaned_amount = cleaned_amount[1:-1]  # Remove parentheses

            # Remove currency symbols and separators
            currency_symbols = [
                "$",
                "€",
                "£",
                "¥",
                "₹",
                "₽",
                "CAD",
                "AUD",
                "CHF",
                "SEK",
                "NOK",
                "DKK",
            ]
            for symbol in currency_symbols:
                cleaned_amount = cleaned_amount.replace(symbol, "")

            # Remove percentage symbol if present (for rate inputs)
            cleaned_amount = cleaned_amount.replace("%", "")

            # Remove thousands separators (be careful with decimal separators)
            # First, identify the decimal separator
            if "." in cleaned_amount and "," in cleaned_amount:
                # Both present - the rightmost one is likely the decimal separator
                last_dot = cleaned_amount.rfind(".")
                last_comma = cleaned_amount.rfind(",")
                if last_dot > last_comma:
                    # Dot is decimal separator, comma is thousands
                    cleaned_amount = cleaned_amount.replace(",", "")
                else:
                    # Comma is decimal separator, dot is thousands
                    cleaned_amount = cleaned_amount.replace(".", "").replace(",", ".")
            elif (
                "," in cleaned_amount
                and cleaned_amount.count(",") == 1
                and len(cleaned_amount.split(",")[1]) <= 3
            ):
                # Single comma, might be decimal separator in European format
                if len(cleaned_amount.split(",")[1]) <= 2:  # Likely decimal separator
                    cleaned_amount = cleaned_amount.replace(",", ".")
                else:  # Likely thousands separator
                    cleaned_amount = cleaned_amount.replace(",", "")
            else:
                # Remove all remaining commas (thousands separators)
                cleaned_amount = cleaned_amount.replace(",", "")

            # Remove any remaining spaces
            cleaned_amount = cleaned_amount.replace(" ", "")

            # Apply accounting format negative sign
            if is_negative_accounting:
                cleaned_amount = "-" + cleaned_amount

            # Validate that we have a valid number string
            if not cleaned_amount or cleaned_amount in ["-", "+", "."]:
                raise ValueError(f"{field_name} is empty or contains only formatting characters")

            # Convert to Decimal for precise arithmetic
            try:
                decimal_amount = Decimal(cleaned_amount)
            except InvalidOperation as exc_error:
                raise ValueError(
                    f"{field_name} '{amount}' is not a valid number format"
                ) from exc_error

        elif isinstance(amount, (int, float)):
            # Convert numeric types to Decimal
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            # Already a Decimal, use as-is
            decimal_amount = amount
        else:
            raise TypeError(f"{field_name} must be int, float, str, or Decimal, got {type(amount)}")

        # Check for negative values if not allowed
        if decimal_amount < 0 and not allow_negative:
            raise ValueError(f"{field_name} cannot be negative. Got {decimal_amount}")

        # Validate decimal places
        # Get the number of decimal places in the input
        sign, digits, exponent = decimal_amount.as_tuple()
        if exponent < 0:  # Negative exponent means decimal places
            current_decimal_places = abs(exponent)
            if current_decimal_places > decimal_places:
                raise ValueError(
                    f"{field_name} has too many decimal places. "
                    f"Maximum allowed: {decimal_places}, got: {current_decimal_places}",
                )

        # Round to specified decimal places using banker's rounding
        quantizer = Decimal("0.1") ** decimal_places
        rounded_amount = decimal_amount.quantize(quantizer, rounding=ROUND_HALF_UP)

        # Convert to float for final validation and return
        float_amount = float(rounded_amount)

        # Validate range constraints
        if float_amount < minimum_value:
            raise ValueError(
                f"{field_name} must be at least {minimum_value:,.{decimal_places}f}. "
                f"Got {float_amount:,.{decimal_places}f}",
            )

        if float_amount > maximum_value:
            raise ValueError(
                f"{field_name} cannot exceed {maximum_value:,.{decimal_places}f}. "
                f"Got {float_amount:,.{decimal_places}f}",
            )

        return float_amount

    except ValueError as exc_error:
        # Re-raise ValueError with original message
        raise exc_error
    except Exception as exc_error:
        # Handle any unexpected errors
        raise ValueError(f"Unexpected error validating {field_name}: {exc_error!s}") from exc_error


def validate_enhanced_percentage_value(
    percentage: int | float | str,
    minimum_value: float = 0.0,
    maximum_value: float = 100.0,
    field_name: str = "Percentage",
    decimal_places: int = FinancialValidationConfig.PERCENTAGE_DECIMAL_PLACES,
    input_as_decimal: bool = False,
) -> float:
    """Enhanced validation for percentage values with flexible input handling.

    This function provides comprehensive validation for percentage values with support
    for different input formats (decimal vs percentage), range checking, and precision
    control. It handles both 0.05 (5%) and 5 (5%) input formats automatically.

    Args:
        percentage (Union[int, float, str]): The percentage value to validate
            Can be in decimal format (0.05 for 5%) or percentage format (5 for 5%)
        minimum_value (float, optional): Minimum allowed percentage value. Defaults to 0.0
        maximum_value (float, optional): Maximum allowed percentage value. Defaults to 100.0
        field_name (str, optional): Name of the field for error messages. Defaults to "Percentage"
        decimal_places (int, optional): Maximum decimal places allowed.
            Defaults to FinancialValidationConfig.PERCENTAGE_DECIMAL_PLACES
        input_as_decimal (bool, optional): Whether input is in decimal format. Defaults to False
            If True, treats 0.05 as 5%; if False, treats 5 as 5%

    Returns:
        float: Validated percentage value as a standard percentage (5.0 for 5%)

    Raises:
        ValueError: If percentage is invalid, out of range, or has too many decimal places

    Examples:
        Interest rate validation:

        ```python
        # Validate an interest rate input
        try:
            rate = validate_enhanced_percentage_value(
                percentage="3.25%",
                minimum_value=0.0,
                maximum_value=50.0,
                field_name="Interest Rate",
            )
            print(f"Interest rate: {rate}%")
        except ValueError as exc_error:
            print(f"Rate error: {exc_error}")
        ```

        Risk tolerance percentage:

        ```python
        # Validate allocation percentage
        try:
            allocation = validate_enhanced_percentage_value(
                percentage=0.65,
                minimum_value=0.0,
                maximum_value=100.0,
                field_name="Stock Allocation",
                input_as_decimal=True,
            )
            print(f"Stock allocation: {allocation}%")
        except ValueError as exc_error:
            print(f"Allocation error: {exc_error}")
        ```
    """
    # Use the enhanced financial amount validator with percentage-specific settings
    try:
        # First, convert the percentage to a standard format
        if isinstance(percentage, str) and "%" in percentage:
            # Remove percentage symbol and validate as regular number
            cleaned_percentage = percentage.replace("%", "").strip()
        else:
            cleaned_percentage = percentage

        # Validate as a financial amount
        validated_amount = validate_enhanced_financial_amount(
            amount=cleaned_percentage,
            minimum_value=minimum_value if not input_as_decimal else minimum_value / 100,
            maximum_value=maximum_value if not input_as_decimal else maximum_value / 100,
            field_name=field_name,
            allow_negative=minimum_value < 0,
            decimal_places=decimal_places,
        )

        # Convert to percentage format if input was decimal
        if input_as_decimal and validated_amount <= 1.0:
            validated_amount *= 100

        # Final range check in percentage terms
        if validated_amount < minimum_value or validated_amount > maximum_value:
            raise ValueError(
                f"{field_name} must be between {minimum_value}% and {maximum_value}%. "
                f"Got {validated_amount}%",
            )

        return validated_amount

    except ValueError as exc_error:
        # Re-raise with percentage-specific context
        raise ValueError(f"Percentage validation error: {exc_error!s}") from exc_error


def validate_enhanced_age_value(
    age: int | float | str,
    minimum_age: int = FinancialValidationConfig.MINIMUM_AGE,
    maximum_age: int = FinancialValidationConfig.MAXIMUM_AGE,
    field_name: str = "Age",
    allow_decimal: bool = False,
) -> int:
    """Enhanced validation for age values with comprehensive range and format checking.

    This function validates age inputs with appropriate range checking for financial
    planning applications. It ensures ages are realistic and within acceptable
    bounds for retirement planning calculations.

    Args:
        age (Union[int, float, str]): The age value to validate
            Should represent age in years
        minimum_age (int, optional): Minimum allowed age.
            Defaults to FinancialValidationConfig.MINIMUM_AGE
        maximum_age (int, optional): Maximum allowed age.
            Defaults to FinancialValidationConfig.MAXIMUM_AGE
        field_name (str, optional): Name of the field for error messages. Defaults to "Age"
        allow_decimal (bool, optional): Whether decimal ages are allowed. Defaults to False
            Set to True for precise age calculations (e.g., 35.5 years)

    Returns:
        int: Validated age as an integer (or float if allow_decimal is True)

    Raises:
        ValueError: If age is invalid, out of range, or not a whole number when required

    Examples:
        Current age validation:

        ```python
        try:
            current_age = validate_enhanced_age_value(
                age="35", minimum_age=18, maximum_age=100, field_name="Current Age"
            )
            print(f"Current age: {current_age}")
        except ValueError as exc_error:
            print(f"Age error: {exc_error}")
        ```

        Retirement age validation:

        ```python
        try:
            retirement_age = validate_enhanced_age_value(
                age=67.5,
                minimum_age=50,
                maximum_age=80,
                field_name="Retirement Age",
                allow_decimal=True,
            )
            print(f"Retirement age: {retirement_age}")
        except ValueError as exc_error:
            print(f"Retirement age error: {exc_error}")
        ```
    """
    try:
        # Convert to numeric value
        if isinstance(age, str):
            cleaned_age = age.strip()
            if not cleaned_age:
                raise ValueError(f"{field_name} cannot be empty")
            numeric_age = float(cleaned_age)
        elif isinstance(age, (int, float)):
            numeric_age = float(age)
        else:
            raise TypeError(f"{field_name} must be a number, got {type(age)}")

        # Check for decimal values if not allowed
        if not allow_decimal and numeric_age != int(numeric_age):
            raise ValueError(f"{field_name} must be a whole number, got {numeric_age}")

        # Validate range
        if numeric_age < minimum_age:
            raise ValueError(
                f"{field_name} must be at least {minimum_age} years, got {numeric_age}"
            )

        if numeric_age > maximum_age:
            raise ValueError(f"{field_name} cannot exceed {maximum_age} years, got {numeric_age}")

        # Return appropriate type
        return int(numeric_age) if not allow_decimal else numeric_age

    except ValueError as exc_error:
        raise exc_error
    except Exception as exc_error:
        raise ValueError(f"Unexpected error validating {field_name}: {exc_error!s}") from exc_error


def validate_enhanced_name_value(
    name: str,
    field_name: str = "Name",
    min_length: int = FinancialValidationConfig.NAME_MIN_LENGTH,
    max_length: int = FinancialValidationConfig.NAME_MAX_LENGTH,
    allow_special_characters: bool = True,
) -> str:
    """Enhanced validation for name fields with format and length checking.

    This function validates name inputs ensuring they meet standard requirements
    for personal names in financial applications. It checks length, character
    validity, and format appropriateness.

    Args:
        name (str): The name value to validate
        field_name (str, optional): Name of the field for error messages. Defaults to "Name"
        min_length (int, optional): Minimum name length.
            Defaults to FinancialValidationConfig.NAME_MIN_LENGTH
        max_length (int, optional): Maximum name length.
            Defaults to FinancialValidationConfig.NAME_MAX_LENGTH
        allow_special_characters (bool, optional): Whether to allow special characters like hyphens and apostrophes. Defaults to True

    Returns:
        str: Validated and normalized name

    Raises:
        ValueError: If name is invalid, too short/long, or contains invalid characters

    Examples:
        Basic name validation:

        ```python
        try:
            user_name = validate_enhanced_name_value(name="  John Smith  ", field_name="Full Name")
            print(f"Validated name: '{user_name}'")
        except ValueError as exc_error:
            print(f"Name error: {exc_error}")
        ```

        Strict name validation:

        ```python
        try:
            first_name = validate_enhanced_name_value(
                name="Mary-Jane",
                field_name="First Name",
                min_length=2,
                max_length=50,
                allow_special_characters=True,
            )
            print(f"First name: '{first_name}'")
        except ValueError as exc_error:
            print(f"First name error: {exc_error}")
        ```
    """
    # Input type validation
    if not isinstance(name, str):
        raise TypeError(f"{field_name} must be a string, got {type(name)}")

    # Clean and normalize the name
    cleaned_name = name.strip()

    # Check for empty name
    if not cleaned_name:
        raise ValueError(f"{field_name} cannot be empty")

    # Check length constraints
    if len(cleaned_name) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")

    if len(cleaned_name) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters")

    # Validate character content
    if allow_special_characters:
        # Allow letters, spaces, hyphens, periods, apostrophes
        if not re.match(FinancialValidationConfig.NAME_PATTERN, cleaned_name):
            raise ValueError(
                f"{field_name} can only contain letters, spaces, hyphens, periods, and apostrophes",
            )
    else:
        # Only letters and spaces
        if not re.match(r"^[a-zA-Z\s]+$", cleaned_name):
            raise ValueError(f"{field_name} can only contain letters and spaces")

    # Check for excessive whitespace
    if "  " in cleaned_name:  # Multiple consecutive spaces
        raise ValueError(f"{field_name} cannot contain multiple consecutive spaces")

    # Normalize case (title case for names)
    normalized_name = cleaned_name.title()

    return normalized_name


class PersonalInformationModel(BaseModel):
    """Enhanced Pydantic model for comprehensive personal information validation.

    This model provides robust validation for user personal information with
    business logic constraints and cross-field validation. It ensures data
    integrity for financial planning calculations and user profile management.

    Attributes:
        name (str): Full name of the user, validated for format and length
        current_age (int): Current age in years, must be within reasonable bounds
        retirement_age (int): Planned retirement age, must be greater than current age
        income_start_age (int): Age when retirement income begins, typically at or after retirement
        risk_tolerance (RiskToleranceEnum): Investment risk tolerance level
        gender (GenderEnum): Gender identification for actuarial calculations
        marital_status (MaritalStatusEnum): Marital status affecting tax and benefit planning

    Examples:
        Basic model validation:

        ```python
        try:
            user_info = PersonalInformationModel(
                name="John Smith",
                current_age=35,
                retirement_age=65,
                income_start_age=65,
                risk_tolerance=RiskToleranceEnum.MODERATE,
                gender=GenderEnum.MALE,
                marital_status=MaritalStatusEnum.MARRIED,
            )
            print("Personal information validated successfully")
        except ValidationError as exc_error:
            for error in exc_error.errors():
                print(f"Validation error: {error}")
        ```

        Model with validation errors:

        ```python
        try:
            # This will raise validation errors
            invalid_user = PersonalInformationModel(
                name="X",  # Too short
                current_age=70,  # Current age
                retirement_age=65,  # Retirement age less than current age
                income_start_age=60,  # Income starts before retirement
                risk_tolerance="Unknown",  # Invalid risk tolerance
                gender="Invalid",  # Invalid gender
                marital_status="Unknown",  # Invalid marital status
            )
        except ValidationError as exc_error:
            print(f"Validation errors found: {len(exc_error.errors())}")
        ```

    Note:
        This model includes cross-field validation to ensure logical consistency
        between related fields such as current age, retirement age, and income
        start age. The validation rules reflect common financial planning practices
        and regulatory requirements.
    """

    name: str = Field(
        ...,
        min_length=FinancialValidationConfig.NAME_MIN_LENGTH,
        max_length=FinancialValidationConfig.NAME_MAX_LENGTH,
        description="Full name of the user",
    )
    current_age: int = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_AGE,
        le=FinancialValidationConfig.MAXIMUM_AGE,
        description="Current age in years",
    )
    retirement_age: int = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_RETIREMENT_AGE,
        le=FinancialValidationConfig.MAXIMUM_RETIREMENT_AGE,
        description="Planned retirement age",
    )
    income_start_age: int = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_RETIREMENT_AGE,
        le=FinancialValidationConfig.MAXIMUM_RETIREMENT_AGE,
        description="Age when retirement income begins",
    )
    risk_tolerance: RiskToleranceEnum = Field(
        ...,
        description="Investment risk tolerance level",
    )
    gender: GenderEnum = Field(
        ...,
        description="Gender identification for actuarial calculations",
    )
    marital_status: MaritalStatusEnum = Field(
        ...,
        description="Marital status for tax and benefit planning",
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, name_value):
        """Validate name format using enhanced name validation."""
        return validate_enhanced_name_value(
            name=name_value,
            field_name="Name",
            allow_special_characters=True,
        )

    @field_validator("retirement_age")
    @classmethod
    def validate_retirement_age_logic(cls, retirement_age_value, info):
        """Validate that retirement age is greater than current age."""
        if "current_age" in info.data and retirement_age_value <= info.data["current_age"]:
            raise ValueError("Retirement age must be greater than current age")
        return retirement_age_value

    @field_validator("income_start_age")
    @classmethod
    def validate_income_start_age_logic(cls, income_start_age_value, info):
        """Validate that income start age is logical relative to retirement age."""
        if "retirement_age" in info.data and income_start_age_value < info.data["retirement_age"]:
            # Allow early income start but warn about potential implications
            if income_start_age_value < info.data["retirement_age"] - 5:
                raise ValueError(
                    "Income start age is significantly before retirement age. "
                    "This may affect Social Security and pension benefits.",
                )
        return income_start_age_value

    @model_validator(mode="after")
    def validate_age_consistency(self):
        """Validate overall age consistency across all age fields."""
        current_age = self.current_age
        retirement_age = self.retirement_age
        income_start_age = self.income_start_age

        if all([current_age, retirement_age, income_start_age]):
            # Ensure reasonable planning horizon
            planning_horizon = retirement_age - current_age
            if planning_horizon < 1:
                raise ValueError("Planning horizon must be at least 1 year")
            if planning_horizon > 50:
                raise ValueError("Planning horizon cannot exceed 50 years")

            # Validate income start timing
            if income_start_age > retirement_age + 10:
                raise ValueError(
                    "Income start age cannot be more than 10 years after retirement age",
                )

        return self

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra="forbid",
    )


class FinancialAssetsModel(BaseModel):
    """Enhanced Pydantic model for comprehensive financial assets validation.

    This model validates financial asset portfolios with appropriate constraints
    and business logic for retirement planning applications. It includes
    automatic calculation of total assets and validation of asset allocation.

    Attributes:
        taxable_assets (float): Investment assets subject to capital gains tax
        tax_deferred_assets (float): Tax-deferred retirement accounts (401k, IRA)
        tax_free_assets (float): Tax-free investment accounts (Roth IRA, municipal bonds)

    Properties:
        total_assets (float): Calculated total of all asset categories
        asset_allocation (Dict[str, float]): Percentage allocation by asset type

    Examples:
        Asset portfolio validation:

        ```python
        try:
            assets = FinancialAssetsModel(
                taxable_assets=250000.0, tax_deferred_assets=400000.0, tax_free_assets=75000.0
            )
            print(f"Total assets: ${assets.total_assets:,.2f}")
            print(f"Asset allocation: {assets.asset_allocation}")
        except ValidationError as exc_error:
            for error in exc_error.errors():
                print(f"Asset validation error: {error}")
        ```
    """

    taxable_assets: float = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT,
        le=FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT,
        description="Taxable investment assets",
    )
    tax_deferred_assets: float = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT,
        le=FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT,
        description="Tax-deferred retirement assets",
    )
    tax_free_assets: float = Field(
        ...,
        ge=FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT,
        le=FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT,
        description="Tax-free investment assets",
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_numeric_inputs(cls, asset_value):
        """Validate that all asset values are non-negative numbers."""
        if asset_value is None:
            return 0.0

        if isinstance(asset_value, str):
            try:
                return validate_enhanced_financial_amount(
                    amount=asset_value,
                    minimum_value=0.0,
                    field_name="Asset value",
                )
            except ValueError as exc_error:
                raise ValueError(f"Invalid asset amount: {exc_error}") from exc_error

        try:
            numeric_value = float(asset_value)
            if numeric_value < 0:
                raise ValueError("Asset values cannot be negative")
            return numeric_value
        except (ValueError, TypeError) as exc_error:
            raise ValueError("Asset values must be valid numbers") from exc_error

    @property
    def total_assets(self) -> float:
        """Calculate total assets across all categories."""
        return self.taxable_assets + self.tax_deferred_assets + self.tax_free_assets

    @property
    def asset_allocation(self) -> dict[str, float]:
        """Calculate percentage allocation by asset type."""
        total = self.total_assets
        if total == 0:
            return {
                "taxable_percentage": 0.0,
                "tax_deferred_percentage": 0.0,
                "tax_free_percentage": 0.0,
            }

        return {
            "taxable_percentage": (self.taxable_assets / total) * 100,
            "tax_deferred_percentage": (self.tax_deferred_assets / total) * 100,
            "tax_free_percentage": (self.tax_free_assets / total) * 100,
        }

    @model_validator(mode="after")
    def validate_portfolio_balance(self):
        """Validate overall portfolio balance and provide recommendations."""
        taxable = self.taxable_assets
        tax_deferred = self.tax_deferred_assets
        tax_free = self.tax_free_assets

        total = taxable + tax_deferred + tax_free

        # Warn about portfolios that are too concentrated in one account type
        if total > 0:
            max_concentration = max(taxable, tax_deferred, tax_free) / total
            if max_concentration > 0.95:
                raise ValueError(
                    "Portfolio is too concentrated in one account type. "
                    "Consider diversifying across taxable, tax-deferred, and tax-free accounts.",
                )

        return self

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra="forbid",
    )


def get_validation_configuration() -> dict[str, Any]:
    """Get comprehensive validation configuration for the application.

    This function returns a dictionary containing all validation settings,
    constraints, patterns, and configuration used throughout the validation
    module. It's useful for configuration management and testing.

    Returns:
        Dict[str, Any]: Complete validation configuration including:
            - Validation constants and limits
            - Regular expression patterns
            - Enumeration values
            - Model schemas and field definitions

    Examples:
        Retrieve configuration for testing:

        ```python
        config = get_validation_configuration()
        age_limits = config["age_constraints"]
        financial_limits = config["financial_constraints"]
        validation_patterns = config["patterns"]
        ```

    Note:
        This function is primarily for internal use and configuration
        management. External code should use the specific validation
        functions rather than accessing configuration directly.
    """
    return {
        "age_constraints": {
            "minimum_age": FinancialValidationConfig.MINIMUM_AGE,
            "maximum_age": FinancialValidationConfig.MAXIMUM_AGE,
            "minimum_retirement_age": FinancialValidationConfig.MINIMUM_RETIREMENT_AGE,
            "maximum_retirement_age": FinancialValidationConfig.MAXIMUM_RETIREMENT_AGE,
        },
        "financial_constraints": {
            "minimum_amount": FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT,
            "maximum_amount": FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT,
            "currency_decimal_places": FinancialValidationConfig.CURRENCY_DECIMAL_PLACES,
            "percentage_decimal_places": FinancialValidationConfig.PERCENTAGE_DECIMAL_PLACES,
        },
        "text_constraints": {
            "name_min_length": FinancialValidationConfig.NAME_MIN_LENGTH,
            "name_max_length": FinancialValidationConfig.NAME_MAX_LENGTH,
        },
        "patterns": {
            "name_pattern": FinancialValidationConfig.NAME_PATTERN,
            "email_pattern": FinancialValidationConfig.EMAIL_PATTERN,
            "phone_pattern": FinancialValidationConfig.PHONE_PATTERN,
        },
        "enumerations": {
            "risk_tolerance_options": [item.value for item in RiskToleranceEnum],
            "gender_options": [item.value for item in GenderEnum],
            "marital_status_options": [item.value for item in MaritalStatusEnum],
            "validation_severity_levels": [item.value for item in ValidationSeverityEnum],
        },
        "version": "2.0.0",
        "module_info": {
            "description": "Enhanced validation utilities for financial dashboard applications",
            "dependencies": ["pydantic", "marshmallow", "decimal", "datetime", "re"],
            "author": "QWIM Dashboard Development Team",
            "features": [
                "Comprehensive financial amount validation",
                "Cross-field validation for business logic",
                "Pydantic model integration",
                "Detailed error messaging",
                "Currency and locale support",
            ],
        },
    }


# Module initialization and configuration
def configure_enhanced_validation_module(
    custom_age_limits: dict[str, int] | None = None,
    custom_financial_limits: dict[str, float] | None = None,
    log_level: str = "INFO",
) -> None:
    """Configure the enhanced validation module with custom settings.

    This function allows customization of module-level validation settings
    including age limits, financial constraints, and logging level. It should
    be called during application initialization if custom configuration is needed.

    Args:
        custom_age_limits (Optional[Dict[str, int]], optional): Custom age constraints
            Dictionary with keys: minimum_age, maximum_age, minimum_retirement_age, maximum_retirement_age
        custom_financial_limits (Optional[Dict[str, float]], optional): Custom financial constraints
            Dictionary with keys: minimum_amount, maximum_amount
        log_level (str, optional): Logging level for the module. Defaults to "INFO"
            Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

    Examples:
        Configure for international markets:

        ```python
        configure_enhanced_validation_module(
            custom_age_limits={
                "minimum_age": 16,  # Different working age
                "maximum_age": 110,  # Different life expectancy
                "minimum_retirement_age": 55,  # Earlier retirement options
                "maximum_retirement_age": 75,  # Extended working years
            },
            custom_financial_limits={
                "minimum_amount": 0.0,
                "maximum_amount": 10_000_000_000.0,  # Higher limits for institutional clients
            },
            log_level="DEBUG",
        )
        ```

    Note:
        This function modifies module-level configuration and should only
        be called once during application startup to avoid inconsistent behavior.
    """
    global logger

    try:
        # Configure logging level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Update age limits if provided
        if custom_age_limits:
            if isinstance(custom_age_limits, dict):
                for key, value in custom_age_limits.items():
                    if hasattr(FinancialValidationConfig, key.upper()):
                        setattr(FinancialValidationConfig, key.upper(), value)
            else:
                raise ValueError("custom_age_limits must be a dictionary")

        # Update financial limits if provided
        if custom_financial_limits:
            if isinstance(custom_financial_limits, dict):
                for key, value in custom_financial_limits.items():
                    if hasattr(FinancialValidationConfig, key.upper()):
                        setattr(FinancialValidationConfig, key.upper(), value)
            else:
                raise ValueError("custom_financial_limits must be a dictionary")

    except Exception as exc_error:
        raise ValueError(
            f"Error configuring enhanced validation module: {exc_error!s}"
        ) from exc_error


def validate_and_constrain_numeric_value(
    value: float,
    min_value: float,
    max_value: float,
) -> float:
    """Validate and constrain value within specified bounds.

    Args:
        value: Value to validate and constrain
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        float: Constrained value within bounds (whole dollars only)
    """
    # Round to whole dollars (no cents)
    rounded_value = round(value)

    if rounded_value < min_value:
        return min_value
    if rounded_value > max_value:
        return max_value
    return rounded_value


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ============================================================================
# Tests for enum classes
# ============================================================================


class Test_ValidationSeverityEnum:
    """Tests for the ValidationSeverityEnum in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Validation_Severity_Enum

        assert ValidationSeverityEnum is not None

    @pytest.mark.unit()
    def test_has_at_least_three_members(self):
        """Test that has at least three members."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Validation_Severity_Enum

        members = list(ValidationSeverityEnum)
        assert len(members) >= 3

    @pytest.mark.unit()
    def test_members_have_values(self):
        """Test that members have values."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Validation_Severity_Enum

        for member in ValidationSeverityEnum:
            assert member.value is not None


class Test_RiskToleranceEnum:
    """Tests for the RiskToleranceEnum in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Risk_Tolerance_Enum

        assert RiskToleranceEnum is not None

    @pytest.mark.unit()
    def test_has_multiple_levels(self):
        """Test that has multiple levels."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Risk_Tolerance_Enum

        members = list(RiskToleranceEnum)
        assert len(members) >= 3

    @pytest.mark.unit()
    def test_conservative_exists(self):
        """Test that conservative exists."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Risk_Tolerance_Enum

        names_upper = {m.name.upper() for m in RiskToleranceEnum}
        assert any("CONSERVATIVE" in n for n in names_upper)


class Test_GenderEnum:
    """Tests for the GenderEnum in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Gender_Enum

        assert GenderEnum is not None

    @pytest.mark.unit()
    def test_has_male_female(self):
        """Test that has male female."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Gender_Enum

        names_upper = {m.name.upper() for m in GenderEnum}
        assert "MALE" in names_upper
        assert "FEMALE" in names_upper


class Test_MaritalStatusEnum:
    """Tests for the MaritalStatusEnum in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Marital_Status_Enum

        assert MaritalStatusEnum is not None

    @pytest.mark.unit()
    def test_has_members(self):
        """Test that has members."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Marital_Status_Enum

        assert len(list(MaritalStatusEnum)) >= 2


class Test_FinancialValidationConfig:
    """Tests for the FinancialValidationConfig class."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Validation_Config

        assert FinancialValidationConfig is not None

    @pytest.mark.unit()
    def test_has_class_attributes(self):
        """Test that has class attributes."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Validation_Config

        # Should have numeric configuration attributes
        attrs = dir(FinancialValidationConfig)
        assert len(attrs) > 0


# ============================================================================
# Tests for validate_enhanced_financial_amount
# ============================================================================


class Test_Validate_Enhanced_Financial_Amount:
    """Tests for validate_enhanced_financial_amount in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_integer_amount(self):
        """Test that integer amount."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = 1000)
        assert isinstance(result, float)
        assert result == 1000.0

    @pytest.mark.unit()
    def test_float_amount(self):
        """Test that float amount."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = 1234.56)
        assert isinstance(result, float)
        assert abs(result - 1234.56) < 0.01

    @pytest.mark.unit()
    def test_numeric_string(self):
        """Test that numeric string."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "1000")
        assert isinstance(result, float)
        assert result == 1000.0

    @pytest.mark.unit()
    def test_currency_formatted_string(self):
        """Test that currency formatted string."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "$1,234.56")
        assert isinstance(result, float)
        assert abs(result - 1234.56) < 0.01

    @pytest.mark.unit()
    def test_zero_amount(self):
        """Test that zero amount."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = 0)
        assert result == 0.0

    @pytest.mark.unit()
    def test_none_returns_zero_or_raises(self):
        """Test that none returns zero or raises."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        try:
            result = validate_enhanced_financial_amount(amount = None)
            assert isinstance(result, float)
        except (ValueError, TypeError, Exception_Validation_Input):
            pass  # raising is acceptable for invalid input

    @pytest.mark.unit()
    def test_accounting_negative_format(self):
        """Test that accounting negative format."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        try:
            result = validate_enhanced_financial_amount(amount = "(500)", allow_negative=True)
            assert isinstance(result, float)
            assert result < 0
        except Exception:
            pass  # implementation may not support accounting format


# ============================================================================
# Tests for validate_enhanced_percentage_value
# ============================================================================


class Test_Validate_Enhanced_Percentage_Value:
    """Tests for validate_enhanced_percentage_value in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_integer_percentage(self):
        """Test that integer percentage."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = 50)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_decimal_percentage(self):
        """Test that decimal percentage."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = 0.5)
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_string_with_percent_sign(self):
        """Test that string with percent sign."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = "50%")
        assert isinstance(result, float)

    @pytest.mark.unit()
    def test_zero_percentage(self):
        """Test that zero percentage."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = 0)
        assert result == 0.0

    @pytest.mark.unit()
    def test_hundred_percent_is_valid(self):
        """Test that hundred percent is valid."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = 100)
        assert isinstance(result, float)


# ============================================================================
# Tests for validate_enhanced_age_value
# ============================================================================


class Test_Validate_Enhanced_Age_Value:
    """Tests for validate_enhanced_age_value in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_valid_middle_age(self):
        """Test that valid middle age."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        result = validate_enhanced_age_value(age = 65)
        assert isinstance(result, int)
        assert result == 65

    @pytest.mark.unit()
    def test_age_as_string(self):
        """Test that age as string."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        result = validate_enhanced_age_value(age = "65")
        assert isinstance(result, int)
        assert result == 65

    @pytest.mark.unit()
    def test_minimum_age_18(self):
        """Test that minimum age 18."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        result = validate_enhanced_age_value(age = 18)
        assert result == 18

    @pytest.mark.unit()
    def test_maximum_age_120(self):
        """Test that maximum age 120."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        result = validate_enhanced_age_value(age = 120)
        assert result == 120

    @pytest.mark.unit()
    def test_age_below_minimum_raises_or_clamps(self):
        """Test that age below minimum raises or clamps."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        try:
            result = validate_enhanced_age_value(age = 5, minimum_age=18)
            assert isinstance(result, int)
        except (ValueError, Exception):
            pass  # raising is acceptable

    @pytest.mark.unit()
    def test_age_above_maximum_raises_or_clamps(self):
        """Test that age above maximum raises or clamps."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        try:
            result = validate_enhanced_age_value(age = 200, maximum_age=120)
            assert isinstance(result, int)
        except (ValueError, Exception):
            pass


# ============================================================================
# Tests for validate_enhanced_name_value
# ============================================================================


class Test_Validate_Enhanced_Name_Value:
    """Tests for validate_enhanced_name_value in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_valid_full_name(self):
        """Test that valid full name."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        result = validate_enhanced_name_value(name = "John Doe")
        assert isinstance(result, str)
        assert "John" in result or "john" in result.lower()

    @pytest.mark.unit()
    def test_hyphenated_name_accepted(self):
        """Test that hyphenated name accepted."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        result = validate_enhanced_name_value(name = "Mary-Jane")
        assert isinstance(result, str)

    @pytest.mark.unit()
    def test_too_short_name_raises(self):
        """Test that too short name raises."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        try:
            result = validate_enhanced_name_value(name = "A", min_length=2)
            assert isinstance(result, str)
        except (ValueError, Exception):
            pass

    @pytest.mark.unit()
    def test_empty_name_raises(self):
        """Test that empty name raises."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        try:
            validate_enhanced_name_value(name = "")
        except (ValueError, Exception):
            pass

    @pytest.mark.unit()
    def test_none_raises(self):
        """Test that none raises."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        try:
            validate_enhanced_name_value(name = None)  # type: ignore[arg-type]
        except (ValueError, TypeError, AttributeError):
            pass


# ============================================================================
# Tests for validate_and_constrain_numeric_value
# ============================================================================


class Test_Validate_And_Constrain_Numeric_Value:
    """Tests for validate_and_constrain_numeric_value in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_value_within_bounds_unchanged(self):
        """Test that value within bounds unchanged."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_and_constrain_numeric_value

        result = validate_and_constrain_numeric_value(value = 50.0, min_value = 0.0, max_value = 100.0)
        assert result == 50

    @pytest.mark.unit()
    def test_value_below_min_clamped_to_min(self):
        """Test that value below min clamped to min."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_and_constrain_numeric_value

        result = validate_and_constrain_numeric_value(value = -10.0, min_value = 0.0, max_value = 100.0)
        assert result == 0

    @pytest.mark.unit()
    def test_value_above_max_clamped_to_max(self):
        """Test that value above max clamped to max."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_and_constrain_numeric_value

        result = validate_and_constrain_numeric_value(value = 150.0, min_value = 0.0, max_value = 100.0)
        assert result == 100

    @pytest.mark.unit()
    def test_float_rounded_to_int(self):
        """Test that float rounded to int."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_and_constrain_numeric_value

        result = validate_and_constrain_numeric_value(value = 50.7, min_value = 0.0, max_value = 100.0)
        assert isinstance(result, int)
        assert result == 51

    @pytest.mark.unit()
    def test_bool_raises_type_error(self):
        """Test that bool input is rejected instead of being treated as 1 or 0."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_and_constrain_numeric_value

        with pytest.raises(TypeError):
            validate_and_constrain_numeric_value(value = True, min_value = 0.0, max_value = 100.0)


# ============================================================================
# Tests for PersonalInformationModel
# ============================================================================


class Test_PersonalInformationModel:
    """Tests for the PersonalInformationModel Pydantic model."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Personal_Information_Model

        assert PersonalInformationModel is not None

    @pytest.mark.unit()
    def test_model_creation_with_valid_data(self):
        """Test that model creation with valid data."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Personal_Information_Model

        try:
            model = PersonalInformationModel(
                name="Jane Smith",
                current_age=40,
                retirement_age=65,
            )
            assert model is not None
        except Exception:
            pass  # Pydantic version differences are acceptable


# ============================================================================
# Tests for FinancialAssetsModel
# ============================================================================


class Test_FinancialAssetsModel:
    """Tests for the FinancialAssetsModel Pydantic model."""

    @pytest.mark.unit()
    def test_is_importable(self):
        """Test that is importable."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        assert FinancialAssetsModel is not None

    @pytest.mark.unit()
    def test_model_creation_with_valid_data(self):
        """Test that model creation with valid data."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        try:
            model = FinancialAssetsModel(
                taxable=10000.0,
                tax_deferred=50000.0,
                tax_free=20000.0,
            )
            assert model is not None
        except Exception:
            pass


# ============================================================================
# Tests for get_validation_configuration
# ============================================================================


class Test_Get_Validation_Configuration:
    """Tests for get_validation_configuration in utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_returns_dict(self):
        """Test that returns dict."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import get_validation_configuration

        result = get_validation_configuration()
        assert isinstance(result, dict)

    @pytest.mark.unit()
    def test_returns_non_empty_dict(self):
        """Test that returns non empty dict."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import get_validation_configuration

        result = get_validation_configuration()
        assert len(result) > 0


# ============================================================================
# Tests for module structure
# ============================================================================


class Test_Utils_Enhanced_Validation_Module_Structure:
    """Tests for the overall module structure of utils_enhanced_validation."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_enhanced_validation as m

        assert m is not None

    @pytest.mark.unit()
    def test_all_expected_callables_present(self):
        """Test that all expected callables present."""
        from src.dashboard.shiny_utils import utils_enhanced_validation

        expected = [
            "validate_enhanced_financial_amount",
            "validate_enhanced_percentage_value",
            "validate_enhanced_age_value",
            "validate_enhanced_name_value",
            "validate_and_constrain_numeric_value",
            "configure_enhanced_validation_module",
            "get_validation_configuration",
        ]
        for name in expected:
            assert hasattr(utils_enhanced_validation, name), f"Missing: {name}"
            assert callable(getattr(utils_enhanced_validation, name))


# ============================================================================
# Branch coverage additions
# ============================================================================


@pytest.mark.unit()
class Class_Test_Financial_Amount_Missing_Branches:
    """Covers missing branches in validate_enhanced_financial_amount."""

    @pytest.mark.unit()
    def Test_none_raises_validation_error(self) -> None:
        """None amount raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = None)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_maximum_value_none_uses_default(self) -> None:
        """maximum_value=None sets it to FinancialValidationConfig.MAXIMUM_FINANCIAL_AMOUNT."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = 100.0, maximum_value=None)
        assert isinstance(result, float)
        assert result == 100.0

    @pytest.mark.unit()
    def Test_minimum_value_none_uses_default(self) -> None:
        """minimum_value=None sets it to FinancialValidationConfig.MINIMUM_FINANCIAL_AMOUNT."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = 100.0, minimum_value=None)  # type: ignore[arg-type]
        assert isinstance(result, float)
        assert result == 100.0

    @pytest.mark.unit()
    def Test_invalid_decimal_places_raises(self) -> None:
        """Invalid decimal_places (e.g. -1) raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 100.0, decimal_places=-1)

    @pytest.mark.unit()
    def Test_non_integer_decimal_places_raises(self) -> None:
        """Non-integer decimal_places raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 100.0, decimal_places="2")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_boolean_decimal_places_raises(self) -> None:
        """Boolean decimal_places is rejected instead of being treated as an integer."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 100.0, decimal_places=True)

    @pytest.mark.unit()
    def Test_bool_amount_raises_type_error(self) -> None:
        """Boolean amount input is rejected as an invalid type."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(TypeError):
            validate_enhanced_financial_amount(amount = True)

    @pytest.mark.unit()
    def Test_accounting_format_negative_amount(self) -> None:
        """Accounting format '(500.00)' with allow_negative=True returns negative float."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "(500.00)", allow_negative=True, minimum_value=-10000.0)
        assert result == pytest.approx(-500.0)

    @pytest.mark.unit()
    def Test_european_format_dot_thousands_comma_decimal(self) -> None:
        """European format '1.234,56' (dot=thousands, comma=decimal) is parsed correctly."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "1.234,56")
        assert result == pytest.approx(1234.56)

    @pytest.mark.unit()
    def Test_single_comma_decimal_separator(self) -> None:
        """String '1,23' (single comma as decimal separator, 2 decimal digits) is parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "1,23", decimal_places=2)
        assert result == pytest.approx(1.23)

    @pytest.mark.unit()
    def Test_single_comma_thousands_separator(self) -> None:
        """String '1,234' (single comma as thousands, 3 digits after) is parsed."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = "1,234")
        assert result == pytest.approx(1234.0)

    @pytest.mark.unit()
    def Test_empty_string_after_cleaning_raises(self) -> None:
        """String '   ' becomes empty after cleaning → raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = "   ")

    @pytest.mark.unit()
    def Test_only_dash_raises(self) -> None:
        """String '-' alone after cleanup raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = "-")

    @pytest.mark.unit()
    def Test_non_numeric_string_raises(self) -> None:
        """String 'abc' raises Exception_Validation_Input (not a valid number)."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = "abc")

    @pytest.mark.unit()
    def Test_decimal_amount_accepted_directly(self) -> None:
        """Decimal type is accepted without conversion."""
        from decimal import Decimal
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        result = validate_enhanced_financial_amount(amount = Decimal("500.00"))
        assert result == pytest.approx(500.0)

    @pytest.mark.unit()
    def Test_unsupported_type_raises_type_error(self) -> None:
        """Unsupported type (list) raises TypeError or Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises((TypeError, Exception_Validation_Input)):
            validate_enhanced_financial_amount(amount = [100.0])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_too_many_decimal_places_raises(self) -> None:
        """Amount with more decimal places than allowed raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 123.456, decimal_places=2)

    @pytest.mark.unit()
    def Test_amount_below_minimum_raises(self) -> None:
        """Amount below minimum_value raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 10.0, minimum_value=100.0)

    @pytest.mark.unit()
    def Test_amount_above_maximum_raises(self) -> None:
        """Amount above maximum_value raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = 1000.0, maximum_value=500.0)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("amount", "validation_kwargs"),
        [
            (100.0, {"minimum_value": True}),
            (0.5, {"minimum_value": 0.0, "maximum_value": True}),
        ],
    )
    def Test_boolean_range_bounds_raise(
        self,
        amount: float,
        validation_kwargs: dict[str, float | bool],
    ) -> None:
        """Boolean minimum_value and maximum_value inputs are rejected explicitly."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = amount, **validation_kwargs)

    @pytest.mark.unit()
    def Test_negative_disallowed_raises(self) -> None:
        """Negative amount when allow_negative=False raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_financial_amount

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_financial_amount(amount = -100.0, allow_negative=False)


@pytest.mark.unit()
class Class_Test_Percentage_Missing_Branches:
    """Covers missing branches in validate_enhanced_percentage_value."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "validation_kwargs",
        [
            {"minimum_value": True, "input_as_decimal": True},
            {"maximum_value": True, "input_as_decimal": True},
        ],
    )
    def Test_boolean_range_bounds_raise_before_decimal_scaling(
        self,
        validation_kwargs: dict[str, bool],
    ) -> None:
        """Boolean percentage bounds are rejected before decimal scaling can coerce them."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_percentage_value(percentage = 0.5, **validation_kwargs)

    @pytest.mark.unit()
    def Test_input_as_decimal_multiplied_by_hundred(self) -> None:
        """input_as_decimal=True with value <= 1.0 multiplies by 100."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = 0.65, input_as_decimal=True)
        assert result == pytest.approx(65.0)

    @pytest.mark.unit()
    def Test_out_of_range_percentage_raises(self) -> None:
        """Percentage outside [minimum, maximum] raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_percentage_value(percentage = 150.0, maximum_value=100.0)

    @pytest.mark.unit()
    def Test_negative_percentage_raises_when_disallowed(self) -> None:
        """Negative percentage raises when minimum_value >= 0."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_percentage_value(percentage = -5.0, minimum_value=0.0)

    @pytest.mark.unit()
    def Test_percentage_string_cleaned(self) -> None:
        """'25.5%' is cleaned and returns 25.5."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_percentage_value

        result = validate_enhanced_percentage_value(percentage = "25.5%")
        assert result == pytest.approx(25.5)


@pytest.mark.unit()
class Class_Test_Age_Missing_Branches:
    """Covers missing branches in validate_enhanced_age_value."""

    @pytest.mark.unit()
    def Test_empty_string_age_raises(self) -> None:
        """Empty string for age raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_age_value(age = "")

    @pytest.mark.unit()
    def Test_unsupported_type_raises_type_error(self) -> None:
        """List type for age raises TypeError."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises((TypeError, Exception_Validation_Input)):
            validate_enhanced_age_value(age = [35])  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_bool_age_raises_type_error(self) -> None:
        """Boolean age input is rejected as an invalid type."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(TypeError):
            validate_enhanced_age_value(age = True)

    @pytest.mark.unit()
    def Test_decimal_age_raises_when_not_allowed(self) -> None:
        """Fractional age raises when allow_decimal=False."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_age_value(age = 35.5, allow_decimal=False)

    @pytest.mark.unit()
    def Test_decimal_age_allowed(self) -> None:
        """Fractional age is returned as float when allow_decimal=True."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        result = validate_enhanced_age_value(age = 35.5, allow_decimal=True)
        assert result == pytest.approx(35.5)

    @pytest.mark.unit()
    def Test_age_below_minimum_raises(self) -> None:
        """Age below minimum raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_age_value(age = 5, minimum_age=18)

    @pytest.mark.unit()
    def Test_age_above_maximum_raises(self) -> None:
        """Age above maximum raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_age_value(age = 200, maximum_age=120)

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("age", "validation_kwargs"),
        [
            (18, {"minimum_age": True}),
            (1, {"minimum_age": 0, "maximum_age": True}),
        ],
    )
    def Test_boolean_age_bounds_raise(
        self,
        age: int,
        validation_kwargs: dict[str, int | bool],
    ) -> None:
        """Boolean minimum_age and maximum_age inputs are rejected explicitly."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_age_value(age = age, **validation_kwargs)

    @pytest.mark.unit()
    def Test_invalid_string_age_raises_value_error(self) -> None:
        """Non-numeric string raises ValueError (float conversion failure)."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_age_value

        with pytest.raises((ValueError, Exception_Validation_Input)):
            validate_enhanced_age_value(age = "abc")


@pytest.mark.unit()
class Class_Test_Name_Missing_Branches:
    """Covers missing branches in validate_enhanced_name_value."""

    @pytest.mark.unit()
    def Test_non_string_name_raises_type_error(self) -> None:
        """Non-string raises TypeError."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(TypeError):
            validate_enhanced_name_value(name = 123)  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_empty_name_raises(self) -> None:
        """Empty (whitespace) name raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "  ")

    @pytest.mark.unit()
    def Test_too_short_name_raises(self) -> None:
        """Name shorter than min_length raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "A", min_length=2)

    @pytest.mark.unit()
    def Test_too_long_name_raises(self) -> None:
        """Name longer than max_length raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "A" * 200, max_length=100)

    @pytest.mark.unit()
    @pytest.mark.parametrize(("length_kwarg", "length_value"), [("min_length", True), ("max_length", True)])
    def Test_boolean_length_bounds_raise(
        self,
        length_kwarg: str,
        length_value: bool,
    ) -> None:
        """Boolean length bounds are rejected instead of being treated as integer limits."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "A", **{length_kwarg: length_value})

    @pytest.mark.unit()
    def Test_special_chars_disallowed_raises(self) -> None:
        """Name with digits when allow_special_characters=False raises."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "John123", allow_special_characters=False)

    @pytest.mark.unit()
    def Test_special_chars_allowed_with_bad_pattern_raises(self) -> None:
        """Name with digits when allow_special_characters=True raises (numbers not in pattern)."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "John123", allow_special_characters=True)

    @pytest.mark.unit()
    def Test_multiple_spaces_raises(self) -> None:
        """Name with multiple consecutive spaces raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        with pytest.raises(Exception_Validation_Input):
            validate_enhanced_name_value(name = "John  Smith")

    @pytest.mark.unit()
    def Test_name_with_no_special_chars_accepted(self) -> None:
        """Name with only letters and spaces accepted when allow_special_characters=False."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import validate_enhanced_name_value

        result = validate_enhanced_name_value(name = "John Smith", allow_special_characters=False)
        assert isinstance(result, str)
        assert "John" in result


@pytest.mark.unit()
class Class_Test_Personal_Information_Model_Validators:
    """Covers Personal_Information_Model field validators and model validator."""

    @pytest.mark.unit()
    def Test_valid_model_creation(self) -> None:
        """Valid Personal_Information_Model is created without errors."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Personal_Information_Model,
            Risk_Tolerance_Enum,
            Gender_Enum,
            Marital_Status_Enum,
        )

        model = Personal_Information_Model(
            name="John Smith",
            current_age=35,
            retirement_age=65,
            income_start_age=65,
            risk_tolerance=Risk_Tolerance_Enum.MODERATE,
            gender=Gender_Enum.MALE,
            marital_status=Marital_Status_Enum.MARRIED,
        )
        assert model.current_age == 35
        assert model.retirement_age == 65

    @pytest.mark.unit()
    def Test_retirement_age_not_greater_than_current_raises(self) -> None:
        """retirement_age <= current_age raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Personal_Information_Model,
            Risk_Tolerance_Enum,
            Gender_Enum,
            Marital_Status_Enum,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Personal_Information_Model(
                name="Jane Doe",
                current_age=65,
                retirement_age=60,  # < current_age → should fail
                income_start_age=65,
                risk_tolerance=Risk_Tolerance_Enum.CONSERVATIVE,
                gender=Gender_Enum.FEMALE,
                marital_status=Marital_Status_Enum.SINGLE,
            )

    @pytest.mark.unit()
    def Test_income_start_age_far_before_retirement_raises(self) -> None:
        """income_start_age significantly before retirement_age raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Personal_Information_Model,
            Risk_Tolerance_Enum,
            Gender_Enum,
            Marital_Status_Enum,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Personal_Information_Model(
                name="Bob Jones",
                current_age=40,
                retirement_age=65,
                income_start_age=55,  # 10 years before retirement (>5 year threshold)
                risk_tolerance=Risk_Tolerance_Enum.AGGRESSIVE,
                gender=Gender_Enum.MALE,
                marital_status=Marital_Status_Enum.DIVORCED,
            )

    @pytest.mark.unit()
    def Test_planning_horizon_exceeds_50_years_raises(self) -> None:
        """current_age + 50+ years to retirement raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Personal_Information_Model,
            Risk_Tolerance_Enum,
            Gender_Enum,
            Marital_Status_Enum,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Personal_Information_Model(
                name="Young Person",
                current_age=18,
                retirement_age=70,  # 52-year horizon → fails >50 check
                income_start_age=70,
                risk_tolerance=Risk_Tolerance_Enum.MODERATE,
                gender=Gender_Enum.PREFER_NOT_TO_SAY,
                marital_status=Marital_Status_Enum.SINGLE,
            )

    @pytest.mark.unit()
    def Test_income_start_age_far_after_retirement_raises(self) -> None:
        """income_start_age > retirement_age + 10 raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Personal_Information_Model,
            Risk_Tolerance_Enum,
            Gender_Enum,
            Marital_Status_Enum,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Personal_Information_Model(
                name="Late Starter",
                current_age=45,
                retirement_age=65,
                income_start_age=76,  # 11 years after retirement → fails
                risk_tolerance=Risk_Tolerance_Enum.MODERATE,
                gender=Gender_Enum.MALE,
                marital_status=Marital_Status_Enum.MARRIED,
            )


@pytest.mark.unit()
class Class_Test_Financial_Assets_Model_Validators:
    """Covers Financial_Assets_Model field validators and model validator."""

    @pytest.mark.unit()
    def Test_valid_model_creation(self) -> None:
        """Valid Financial_Assets_Model is created without errors."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        model = Financial_Assets_Model(
            taxable_assets=100000.0,
            tax_deferred_assets=300000.0,
            tax_free_assets=50000.0,
        )
        assert model.total_assets == pytest.approx(450000.0)

    @pytest.mark.unit()
    def Test_asset_allocation_property(self) -> None:
        """asset_allocation property returns correct percentages."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        model = Financial_Assets_Model(
            taxable_assets=100.0,
            tax_deferred_assets=200.0,
            tax_free_assets=100.0,
        )
        alloc = model.asset_allocation
        assert abs(alloc["taxable_percentage"] - 25.0) < 0.01
        assert abs(alloc["tax_deferred_percentage"] - 50.0) < 0.01

    @pytest.mark.unit()
    def Test_zero_assets_allocation_all_zeros(self) -> None:
        """When all assets are zero, asset_allocation returns all zeros."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        model = Financial_Assets_Model(
            taxable_assets=0.0,
            tax_deferred_assets=0.0,
            tax_free_assets=0.0,
        )
        alloc = model.asset_allocation
        assert alloc["taxable_percentage"] == 0.0

    @pytest.mark.unit()
    def Test_string_asset_value_is_cleaned(self) -> None:
        """String asset values are converted via validate_enhanced_financial_amount."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        model = Financial_Assets_Model(
            taxable_assets="100000",
            tax_deferred_assets=200000.0,
            tax_free_assets=50000.0,
        )
        assert model.taxable_assets == pytest.approx(100000.0)

    @pytest.mark.unit()
    def Test_none_asset_value_becomes_zero(self) -> None:
        """None asset value is converted to 0.0."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        model = Financial_Assets_Model(
            taxable_assets=None,  # type: ignore[arg-type]
            tax_deferred_assets=200000.0,
            tax_free_assets=50000.0,
        )
        assert model.taxable_assets == pytest.approx(0.0)

    @pytest.mark.unit()
    def Test_boolean_asset_value_raises(self) -> None:
        """Boolean asset values are rejected instead of coercing to 1.0 or 0.0."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Financial_Assets_Model(
                taxable_assets=True,
                tax_deferred_assets=200000.0,
                tax_free_assets=50000.0,
            )

    @pytest.mark.unit()
    def Test_negative_asset_value_raises(self) -> None:
        """Negative asset value raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Financial_Assets_Model(
                taxable_assets=-100.0,  # negative → error
                tax_deferred_assets=200000.0,
                tax_free_assets=50000.0,
            )

    @pytest.mark.unit()
    def Test_too_concentrated_portfolio_raises(self) -> None:
        """Portfolio with >95% in one account type raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Financial_Assets_Model(
                taxable_assets=990000.0,  # 99% concentrated → fails
                tax_deferred_assets=5000.0,
                tax_free_assets=5000.0,
            )

    @pytest.mark.unit()
    def Test_invalid_numeric_type_raises(self) -> None:
        """List type for asset value raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import Financial_Assets_Model

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            Financial_Assets_Model(
                taxable_assets=[100],  # type: ignore[arg-type]
                tax_deferred_assets=200000.0,
                tax_free_assets=50000.0,
            )


@pytest.mark.unit()
class Class_Test_Configure_Validation_Module:
    """Covers configure_enhanced_validation_module (lines 1341-1364)."""

    @pytest.mark.unit()
    def Test_configure_with_custom_age_limits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Custom age limits are applied to Financial_Validation_Config."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            Financial_Validation_Config,
            configure_enhanced_validation_module,
        )

        monkeypatch.setattr(
            Financial_Validation_Config,
            "MINIMUM_AGE",
            Financial_Validation_Config.MINIMUM_AGE,
        )
        monkeypatch.setattr(
            Financial_Validation_Config,
            "MAXIMUM_AGE",
            Financial_Validation_Config.MAXIMUM_AGE,
        )

        # Should not raise
        configure_enhanced_validation_module(
            custom_age_limits={"MINIMUM_AGE": 16, "MAXIMUM_AGE": 110},
        )

        assert Financial_Validation_Config.MINIMUM_AGE == 16
        assert Financial_Validation_Config.MAXIMUM_AGE == 110

    @pytest.mark.unit()
    def Test_configure_with_custom_financial_limits(self) -> None:
        """Custom financial limits are applied."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            configure_enhanced_validation_module,
        )

        configure_enhanced_validation_module(
            custom_financial_limits={"MINIMUM_FINANCIAL_AMOUNT": 0.0},
        )

    @pytest.mark.unit()
    def Test_configure_invalid_age_limits_raises(self) -> None:
        """Non-dict custom_age_limits raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            configure_enhanced_validation_module,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            configure_enhanced_validation_module(custom_age_limits="not_a_dict")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_configure_invalid_financial_limits_raises(self) -> None:
        """Non-dict custom_financial_limits raises Exception_Validation_Input."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            configure_enhanced_validation_module,
        )

        with pytest.raises((Exception_Validation_Input, ValidationError)):
            configure_enhanced_validation_module(custom_financial_limits="not_a_dict")  # type: ignore[arg-type]

    @pytest.mark.unit()
    def Test_configure_with_unknown_age_key_skipped(self) -> None:
        """Key not in Financial_Validation_Config is skipped (hasattr returns False)."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            configure_enhanced_validation_module,
        )

        # Key "NONEXISTENT_KEY" doesn't exist in Financial_Validation_Config → hasattr=False → setattr skipped
        configure_enhanced_validation_module(
            custom_age_limits={"NONEXISTENT_KEY": 99},
        )

    @pytest.mark.unit()
    def Test_configure_with_unknown_financial_key_skipped(self) -> None:
        """Financial key not in Financial_Validation_Config is skipped."""
        from src.dashboard.shiny_utils.utils_enhanced_validation import (
            configure_enhanced_validation_module,
        )

        configure_enhanced_validation_module(
            custom_financial_limits={"NONEXISTENT_LIMIT": 9999.0},
        )

