"""Public compatibility facade for enhanced dashboard validation.

This module preserves the historical import surface while delegating the
implementation to smaller private modules. The split keeps the public API
stable and brings the file under the project line-count limit.
"""

from __future__ import annotations

from ._enhanced_validation_models import Financial_Assets_Model, Personal_Information_Model
from ._enhanced_validation_types import (
    Financial_Validation_Config,
    Gender_Enum,
    Marital_Status_Enum,
    Risk_Tolerance_Enum,
    Validation_Severity_Enum,
)
from ._enhanced_validation_validators import (
    configure_enhanced_validation_module,
    get_validation_configuration,
    validate_and_constrain_numeric_value,
    validate_enhanced_age_value,
    validate_enhanced_financial_amount,
    validate_enhanced_name_value,
    validate_enhanced_percentage_value,
)


__all__ = [
    "configure_enhanced_validation_module",
    "Financial_Assets_Model",
    "Financial_Validation_Config",
    "Gender_Enum",
    "get_validation_configuration",
    "Marital_Status_Enum",
    "Personal_Information_Model",
    "Risk_Tolerance_Enum",
    "validate_and_constrain_numeric_value",
    "validate_enhanced_age_value",
    "validate_enhanced_financial_amount",
    "validate_enhanced_name_value",
    "validate_enhanced_percentage_value",
    "Validation_Severity_Enum",
]


# Preserve the legacy public module identity for runtime introspection and docs.
for exported_symbol in (
    configure_enhanced_validation_module,
    Financial_Assets_Model,
    Financial_Validation_Config,
    Gender_Enum,
    get_validation_configuration,
    Marital_Status_Enum,
    Personal_Information_Model,
    Risk_Tolerance_Enum,
    validate_and_constrain_numeric_value,
    validate_enhanced_age_value,
    validate_enhanced_financial_amount,
    validate_enhanced_name_value,
    validate_enhanced_percentage_value,
    Validation_Severity_Enum,
):
    exported_symbol.__module__ = __name__

del exported_symbol