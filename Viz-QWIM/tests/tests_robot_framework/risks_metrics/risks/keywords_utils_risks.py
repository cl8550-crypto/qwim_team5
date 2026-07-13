"""
Robot Framework keyword library for risks_metrics.utils_risks.
==============================================================

Keywords cover:
    - Risk_Measure_Type enum member access by name
    - Category classmethod retrieval (variance, VaR-family, drawdown,
      higher-moment, coherent, convex)
    - Membership verification
    - Subset relationship: coherent ⊆ convex

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-28
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Conditional imports (Robot Framework replaces sys.stderr with StringIO)
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

_original_stderr = sys.stderr
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO())

try:
    from src.risks_metrics.risks.utils_risks import Risk_Measure_Type
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
finally:
    sys.stderr = _original_stderr


def _require_imports() -> None:
    """Raise RuntimeError when required imports are unavailable."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"Required imports not available: {_import_error_message}"
        )


# ===========================================================================
# Keyword: member access
# ===========================================================================


def get_risk_measure_member(member_name: str) -> Risk_Measure_Type:
    """Return the ``Risk_Measure_Type`` member with the given name.

    Arguments:
    - member_name -- exact enum member name (e.g. ``"VARIANCE"``)
    """
    _require_imports()
    return Risk_Measure_Type[member_name]


def verify_member_name(member: Risk_Measure_Type, expected_name: str) -> None:
    """Assert ``member.name == expected_name``."""
    assert member.name == expected_name, (
        f"Expected '{expected_name}', got '{member.name}'"
    )


# ===========================================================================
# Keyword: category retrieval
# ===========================================================================


def get_variance_based_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_variance_based_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_variance_based_measures()


def get_var_family_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_var_family_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_var_family_measures()


def get_drawdown_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_drawdown_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_drawdown_measures()


def get_higher_moment_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_higher_moment_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_higher_moment_measures()


def get_coherent_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_coherent_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_coherent_measures()


def get_convex_category() -> list[Risk_Measure_Type]:
    """Return ``Risk_Measure_Type.get_convex_measures()``."""
    _require_imports()
    return Risk_Measure_Type.get_convex_measures()


# ===========================================================================
# Keyword: assertions
# ===========================================================================


def verify_category_nonempty(category: list) -> None:
    """Assert the category list is not empty."""
    assert len(category) > 0, "Category list must not be empty"


def verify_member_in_category(
    member_name: str, category: list[Risk_Measure_Type]
) -> None:
    """Assert the named member is present in the category list."""
    _require_imports()
    member = Risk_Measure_Type[member_name]
    assert member in category, (
        f"{member_name} not found in category "
        f"[{', '.join(m.name for m in category)}]"
    )


def verify_coherent_subset_of_convex(
    coherent: list[Risk_Measure_Type], convex: list[Risk_Measure_Type]
) -> None:
    """Assert coherent is a subset of convex."""
    coherent_set = set(coherent)
    convex_set = set(convex)
    extra = coherent_set - convex_set
    assert not extra, (
        f"Coherent members not in convex: {[m.name for m in extra]}"
    )
