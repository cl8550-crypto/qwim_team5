from __future__ import annotations

import pytest

from src.models.portfolio_optimization._optport_builders import _build_constraints
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.mark.unit()
class Test_Build_Constraints_Validation:
    """Focused validation tests for _build_constraints."""

    @pytest.mark.unit()
    def test_false_is_long_only_is_accepted(self) -> None:
        """Explicit False should remain a valid boolean input."""
        constraints = _build_constraints(asset_names = ["AAPL", "MSFT"], is_long_only=False)

        assert type(constraints).__name__ == "Constraints"

    @pytest.mark.unit()
    def test_invalid_is_long_only_raises(self) -> None:
        """Non-boolean is_long_only values should raise validation error."""
        with pytest.raises(Exception_Validation_Input, match="is_long_only"):
            _build_constraints(asset_names = ["AAPL", "MSFT"], is_long_only="True")
