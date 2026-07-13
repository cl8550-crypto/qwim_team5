"""Package facade for long-term-care insurance models.

The LTC package re-exports the shared LTC base types together with the three
supported product chassis: traditional LTC, hybrid life LTC, and hybrid
annuity LTC.

Version
-------
0.1.0 (2026-05-30)
"""

from __future__ import annotations

from .insurance_LTC_base import (
    Benefit_Period,
    Care_Setting,
    Elimination_Period,
    Inflation_Protection,
    Insurance_LTC_Base,
    Insurance_LTC_Type,
    Premium_Frequency_LTC,
)
from .insurance_LTC_hybrid_annuity import (
    Annuity_Type_Hybrid,
    Insurance_LTC_Hybrid_Annuity,
    LTC_Multiplier,
    Surrender_Schedule_Type,
)
from .insurance_LTC_hybrid_life import (
    Extension_Of_Benefits,
    Insurance_LTC_Hybrid_Life,
    Premium_Structure_Hybrid_Life,
    Return_Of_Premium_Type,
)
from .insurance_LTC_traditional import (
    Gender_LTC,
    Health_Class_LTC,
    Insurance_LTC_Traditional,
    Non_Forfeiture_Option,
)


__all__ = [
    "Annuity_Type_Hybrid",
    "Benefit_Period",
    "Care_Setting",
    "Elimination_Period",
    "Extension_Of_Benefits",
    "Gender_LTC",
    "Health_Class_LTC",
    "Inflation_Protection",
    "Insurance_LTC_Base",
    "Insurance_LTC_Hybrid_Annuity",
    "Insurance_LTC_Hybrid_Life",
    "Insurance_LTC_Traditional",
    "Insurance_LTC_Type",
    "LTC_Multiplier",
    "Non_Forfeiture_Option",
    "Premium_Frequency_LTC",
    "Premium_Structure_Hybrid_Life",
    "Return_Of_Premium_Type",
    "Surrender_Schedule_Type",
]
