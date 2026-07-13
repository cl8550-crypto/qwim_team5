"""Enumerations and constants for enhanced dashboard validation.

This private module centralizes the public enum types and configuration
constants re-exported by :mod:`src.dashboard.shiny_utils.utils_enhanced_validation`.
"""

from __future__ import annotations

from aenum import StrEnum  # type: ignore[misc]


class Validation_Severity_Enum(StrEnum):
    """Enumeration for validation severity levels.

    This enum defines different levels of validation severity that can be used
    to categorize validation errors and provide appropriate user feedback.

    Attributes
    ----------
        INFO: Informational messages, no action required
        WARNING: Warning messages, user should review but can proceed
        ERROR: Error messages, user must correct before proceeding
        CRITICAL: Critical errors, application cannot continue safely
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Risk_Tolerance_Enum(StrEnum):
    """Enumeration for investment risk tolerance levels.

    This enum defines the standard risk tolerance categories used in financial
    planning and investment portfolio management. Each level represents a
    different approach to balancing potential returns with acceptable risk.

    Attributes
    ----------
        CONSERVATIVE: Low risk tolerance, prioritizes capital preservation
        MODERATELY_CONSERVATIVE: Below-average risk tolerance, cautious growth approach
        MODERATE: Average risk tolerance, balanced growth and preservation
        MODERATELY_AGGRESSIVE: Above-average risk tolerance, growth-focused approach
        AGGRESSIVE: High risk tolerance, maximum growth potential with higher volatility

    Examples
    --------
        Using risk tolerance in validation:

        ```python
        user_risk_tolerance = Risk_Tolerance_Enum.MODERATE
        if user_risk_tolerance in [
            Risk_Tolerance_Enum.AGGRESSIVE,
            Risk_Tolerance_Enum.MODERATELY_AGGRESSIVE,
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


class Gender_Enum(StrEnum):
    """Enumeration for gender identification options.

    This enum provides inclusive gender options that respect individual identity
    while meeting data collection requirements for actuarial calculations and
    regulatory compliance in financial planning applications.

    Attributes
    ----------
        FEMALE: Female gender identification
        MALE: Male gender identification
        OTHER: Other gender identification not covered by binary options
        PREFER_NOT_TO_SAY: Option for users who prefer not to disclose gender
    """

    FEMALE = "Female"
    MALE = "Male"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class Marital_Status_Enum(StrEnum):
    """Enumeration for marital status options.

    This enum defines standard marital status categories relevant for financial
    planning, tax calculations, benefit determinations, and estate planning.

    Attributes
    ----------
        SINGLE: Not married
        MARRIED: Currently married
        DIVORCED: Legally divorced
        WIDOWED: Spouse is deceased
        SEPARATED: Legally separated but not divorced
    """

    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"
    SEPARATED = "Separated"


class Financial_Validation_Config:
    """Configuration constants for financial validation logic.

    This class contains all configurable constants used throughout the enhanced
    validation module, including financial limits, age constraints, string
    length limits, and regular expression patterns.
    """

    MINIMUM_AGE = 18
    MAXIMUM_AGE = 120
    MINIMUM_RETIREMENT_AGE = 50
    MAXIMUM_RETIREMENT_AGE = 80

    MINIMUM_FINANCIAL_AMOUNT = 0.0
    MAXIMUM_FINANCIAL_AMOUNT = 1_000_000_000.0
    CURRENCY_DECIMAL_PLACES = 2
    PERCENTAGE_DECIMAL_PLACES = 4

    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 100
    NAME_PATTERN = r"^[a-zA-Z\s\-\.\']+$"
    EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    PHONE_PATTERN = r"^[\+]?[1-9][\d]{0,15}$"


__all__ = [
    "Financial_Validation_Config",
    "Gender_Enum",
    "Marital_Status_Enum",
    "Risk_Tolerance_Enum",
    "Validation_Severity_Enum",
]