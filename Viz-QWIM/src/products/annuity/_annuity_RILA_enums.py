"""RILA-specific enumeration types.

Extracted into a private module so that both ``annuity_RILA`` and the
calculation-mixin modules can import them without creating circular
dependencies.

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-28)
"""

from __future__ import annotations

from aenum import Enum


class Protection_Type(Enum):
    """Downside protection mechanism for a RILA segment.

    Attributes
    ----------
    BUFFER : str
        Buffer protection — the insurer absorbs the first *B* % of index
        losses.  Losses beyond the buffer are borne by the contract holder.
    FLOOR : str
        Floor protection — the maximum loss is capped at the floor level.
        Losses up to the floor are borne by the contract holder; the insurer
        absorbs losses beyond the floor.
    """

    BUFFER = "Buffer"
    FLOOR = "Floor"


class Crediting_Strategy(Enum):
    """Index-return crediting strategy for a RILA segment.

    Attributes
    ----------
    CAP : str
        Cap strategy — the credited rate is the lesser of the index return
        and the cap rate (upside limited, downside protected).
    PERFORMANCE_TRIGGER : str
        Performance-trigger strategy — a fixed rate is credited whenever
        the index return is non-negative, regardless of magnitude.
    PARTICIPATION_RATE : str
        Participation-rate strategy — the credited rate is a fixed
        percentage of the index return, subject to a cap.
    """

    CAP = "Cap"
    PERFORMANCE_TRIGGER = "Performance Trigger"
    PARTICIPATION_RATE = "Participation Rate"
