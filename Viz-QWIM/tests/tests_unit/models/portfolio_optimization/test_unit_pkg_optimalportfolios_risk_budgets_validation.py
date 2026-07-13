from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from src.models.portfolio_optimization._optport_convex import (
    calc_optimalportfolios_budgeted_risk_contribution,
)
from src.models.portfolio_optimization._optport_validators import (
    _validate_risk_budgets,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.fixture()
def returns_data_small() -> pl.DataFrame:
    """Return a minimal deterministic returns frame for wrapper validation tests.

    Returns
    -------
    pl.DataFrame
        Small Polars DataFrame with one ``Date`` column and three numeric
        asset-return columns.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "AAPL": [0.01, -0.005, 0.02, 0.011],
            "MSFT": [0.015, 0.01, -0.01, 0.003],
            "GOOG": [0.005, 0.02, 0.015, -0.004],
        }
    )


@pytest.mark.unit()
class Class_Test_Optimalportfolios_Risk_Budgets_Validation:
    """Focused validation tests for the risk-budgets public boundary."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "invalid_risk_budgets",
        [
            pytest.param(
                {"AAPL": True, "MSFT": 0.0, "GOOG": 0.0},
                id="dict_bool_value",
            ),
            pytest.param(
                {"AAPL": 0.4, "MSFT": 0.3, "GOOG": 0.3, "SPY": 0.0},
                id="dict_unexpected_asset",
            ),
            pytest.param(
                np.array([[0.5, 0.25, 0.25]]),
                id="non_1d_array",
            ),
            pytest.param(np.array([-0.2, 0.6, 0.6]), id="negative_value"),
            pytest.param(np.array([0.5, np.nan, 0.5]), id="nan_value"),
            pytest.param(["0.5", "0.25", "0.25"], id="string_values"),
        ],
    )
    def Test_Invalid_Risk_Budgets_Raises(
        self,
        returns_data_small: pl.DataFrame,
        invalid_risk_budgets: object,
    ) -> None:
        """Invalid risk budgets should raise at the public wrapper boundary."""

        with pytest.raises(Exception_Validation_Input, match="risk_budgets"):
            calc_optimalportfolios_budgeted_risk_contribution(
                returns_data = returns_data_small,
                risk_budgets=invalid_risk_budgets,
            )

    @pytest.mark.unit()
    def Test_Validate_Risk_Budgets_Rejects_Non_1d_Array(self) -> None:
        """The validator should reject non-1D array inputs before scalar coercion."""

        with pytest.raises(Exception_Validation_Input, match="risk_budgets"):
            _validate_risk_budgets(
                risk_budgets_input = np.array([[0.5, 0.25, 0.25]]),
                asset_names = ["AAPL", "MSFT", "GOOG"],
            )