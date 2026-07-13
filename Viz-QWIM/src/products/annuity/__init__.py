"""Package facade for annuity product models and shared enums.

The annuity package exposes the concrete annuity classes together with the
shared annuity enums that are imported throughout the product test surface.

Exports
-------
Annuity_Base
    Abstract base class for annuity products.
Annuity_Payout_Option
    Shared payout-structure enumeration.
Annuity_Type
    Shared annuity-type enumeration.
Annuity_SPIA
    Single Premium Immediate Annuity model.
Annuity_DIA
    Deferred Income Annuity model.
Annuity_FIA
    Fixed Indexed Annuity model.
Annuity_VA
    Variable Annuity model.
Annuity_RILA
    Registered Index-Linked Annuity model.
Crediting_Strategy
    RILA crediting-strategy enumeration.
Protection_Type
    RILA downside-protection enumeration.

Version
-------
0.1.0 (2026-05-30)
"""

from __future__ import annotations

from .annuity_base import Annuity_Base, Annuity_Payout_Option, Annuity_Type
from .annuity_DIA import Annuity_DIA
from .annuity_FIA import Annuity_FIA
from .annuity_RILA import Annuity_RILA, Crediting_Strategy, Protection_Type
from .annuity_SPIA import Annuity_SPIA
from .annuity_VA import Annuity_VA


__all__ = [
    "Annuity_Base",
    "Annuity_DIA",
    "Annuity_FIA",
    "Annuity_Payout_Option",
    "Annuity_RILA",
    "Annuity_SPIA",
    "Annuity_Type",
    "Annuity_VA",
    "Crediting_Strategy",
    "Protection_Type",
]
