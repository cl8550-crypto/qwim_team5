"""Package facade for life-insurance models and shared enums.

The life-insurance package exposes the shared life-insurance base types and the
concrete whole, term, universal, variable, and survivor product models.

Version
-------
0.1.0 (2026-05-30)
"""

from __future__ import annotations

from .insurance_life_base import (
    Death_Benefit_Option,
    Insurance_Life_Base,
    Insurance_Life_Type,
    Premium_Frequency,
    Underwriting_Class,
)
from .insurance_life_survivor import (
    Insurance_Life_Survivor,
    Survivor_Chassis,
)
from .insurance_life_term import (
    Insurance_Life_Term,
    Term_Type,
)
from .insurance_life_universal import (
    Insurance_Life_Universal,
    UL_Variant,
)
from .insurance_life_variable import (
    Insurance_Life_Variable,
    Sub_Account_Type,
)
from .insurance_life_whole import Insurance_Life_Whole


__all__ = [
    # Base & enums
    "Death_Benefit_Option",
    "Insurance_Life_Base",
    "Insurance_Life_Type",
    "Premium_Frequency",
    "Underwriting_Class",
    # Whole life
    "Insurance_Life_Whole",
    # Term life
    "Insurance_Life_Term",
    "Term_Type",
    # Universal life
    "Insurance_Life_Universal",
    "UL_Variant",
    # Variable life
    "Insurance_Life_Variable",
    "Sub_Account_Type",
    # Survivor life
    "Insurance_Life_Survivor",
    "Survivor_Chassis",
]
