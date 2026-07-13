"""Pydantic models for enhanced dashboard validation.

This private module contains the data models re-exported by
:mod:`src.dashboard.shiny_utils.utils_enhanced_validation`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)

from ._enhanced_validation_types import (
    Financial_Validation_Config,
    Gender_Enum,
    Marital_Status_Enum,
    Risk_Tolerance_Enum,
)
from ._enhanced_validation_validators import (
    validate_enhanced_financial_amount,
    validate_enhanced_name_value,
)


class Personal_Information_Model(BaseModel):
    """Enhanced Pydantic model for comprehensive personal information validation.

    This model provides robust validation for user personal information with
    business logic constraints and cross-field validation. It ensures data
    integrity for financial planning calculations and user profile management.
    """

    name: str = Field(
        ...,
        min_length=Financial_Validation_Config.NAME_MIN_LENGTH,
        max_length=Financial_Validation_Config.NAME_MAX_LENGTH,
        description="Full name of the user",
    )
    current_age: int = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_AGE,
        le=Financial_Validation_Config.MAXIMUM_AGE,
        description="Current age in years",
    )
    retirement_age: int = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_RETIREMENT_AGE,
        le=Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE,
        description="Planned retirement age",
    )
    income_start_age: int = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_RETIREMENT_AGE,
        le=Financial_Validation_Config.MAXIMUM_RETIREMENT_AGE,
        description="Age when retirement income begins",
    )
    risk_tolerance: Risk_Tolerance_Enum = Field(
        ...,
        description="Investment risk tolerance level",
    )
    gender: Gender_Enum = Field(
        ...,
        description="Gender identification for actuarial calculations",
    )
    marital_status: Marital_Status_Enum = Field(
        ...,
        description="Marital status for tax and benefit planning",
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, name_value: Any) -> Any:
        """Validate name format using enhanced name validation."""
        return validate_enhanced_name_value(
            name=name_value,
            field_name="Name",
            allow_special_characters=True,
        )

    @field_validator("retirement_age")
    @classmethod
    def validate_retirement_age_logic(cls, retirement_age_value: Any, info: Any) -> Any:
        """Validate that retirement age is greater than current age."""
        if (
            info.data.get("current_age") is not None
            and retirement_age_value <= info.data["current_age"]
        ):
            raise Exception_Validation_Input("Retirement age must be greater than current age")
        return retirement_age_value

    @field_validator("income_start_age")
    @classmethod
    def validate_income_start_age_logic(cls, income_start_age_value: Any, info: Any) -> Any:
        """Validate that income start age is logical relative to retirement age."""
        retirement_age = info.data.get("retirement_age")
        if (
            retirement_age is not None
            and income_start_age_value < retirement_age
            and income_start_age_value < retirement_age - 5
        ):
            raise Exception_Validation_Input(
                "Income start age is significantly before retirement age. "
                "This may affect Social Security and pension benefits.",
            )
        return income_start_age_value

    @model_validator(mode="after")
    def validate_age_consistency(self) -> Any:
        """Validate overall age consistency across all age fields."""
        current_age = self.current_age
        retirement_age = self.retirement_age
        income_start_age = self.income_start_age

        if all([current_age, retirement_age, income_start_age]):  # pragma: no branch
            planning_horizon = retirement_age - current_age
            if planning_horizon < 1:  # pragma: no cover
                raise Exception_Validation_Input(
                    "Planning horizon must be at least 1 year",
                )  # pragma: no cover
            if planning_horizon > 50:
                raise Exception_Validation_Input("Planning horizon cannot exceed 50 years")

            if income_start_age > retirement_age + 10:
                raise Exception_Validation_Input(
                    "Income start age cannot be more than 10 years after retirement age",
                )

        return self

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra="forbid",
    )


class Financial_Assets_Model(BaseModel):
    """Enhanced Pydantic model for comprehensive financial assets validation."""

    taxable_assets: float = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT,
        le=Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT,
        description="Taxable investment assets",
    )
    tax_deferred_assets: float = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT,
        le=Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT,
        description="Tax-deferred retirement assets",
    )
    tax_free_assets: float = Field(
        ...,
        ge=Financial_Validation_Config.MINIMUM_FINANCIAL_AMOUNT,
        le=Financial_Validation_Config.MAXIMUM_FINANCIAL_AMOUNT,
        description="Tax-free investment assets",
    )

    @field_validator("taxable_assets", "tax_deferred_assets", "tax_free_assets", mode="before")
    @classmethod
    def validate_numeric_inputs(cls, asset_value: Any) -> Any:
        """Validate that all asset values are non-negative numbers."""
        if asset_value is None:
            return 0.0

        if isinstance(asset_value, bool):
            raise Exception_Validation_Input("Asset values must be valid numbers")

        if isinstance(asset_value, str):
            try:
                return validate_enhanced_financial_amount(
                    amount=asset_value,
                    minimum_value=0.0,
                    field_name="Asset value",
                )
            except ValueError as exc_error:  # pragma: no cover
                raise Exception_Validation_Input(
                    f"Invalid asset amount: {exc_error}",
                ) from exc_error  # pragma: no cover

        try:
            numeric_value = float(asset_value)
            if numeric_value < 0:
                raise Exception_Validation_Input("Asset values cannot be negative")
            return numeric_value
        except (ValueError, TypeError) as exc_error:
            raise Exception_Validation_Input("Asset values must be valid numbers") from exc_error

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
    def validate_portfolio_balance(self) -> Any:
        """Validate overall portfolio balance and provide recommendations."""
        taxable = self.taxable_assets
        tax_deferred = self.tax_deferred_assets
        tax_free = self.tax_free_assets

        total = taxable + tax_deferred + tax_free

        if total > 0:
            max_concentration = max(taxable, tax_deferred, tax_free) / total
            if max_concentration > 0.95:
                raise Exception_Validation_Input(
                    "Portfolio is too concentrated in one account type. "
                    "Consider diversifying across taxable, tax-deferred, and tax-free accounts.",
                )

        return self

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra="forbid",
    )


__all__ = [
    "Financial_Assets_Model",
    "Personal_Information_Model",
]