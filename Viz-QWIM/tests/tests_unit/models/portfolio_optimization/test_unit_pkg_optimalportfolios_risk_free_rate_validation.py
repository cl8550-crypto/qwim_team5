from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization._optport_hierarchical import (
    calc_optimalportfolios_maximum_sharpe_ratio,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.fixture()
def returns_data_small() -> pl.DataFrame:
    """Return a minimal deterministic returns frame for Sharpe validation tests.

    Returns
    -------
    pl.DataFrame
        Small Polars DataFrame with a ``Date`` column and three numeric
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
class Class_Test_Optimalportfolios_Risk_Free_Rate_Validation:
    """Focused validation tests for the maximum-Sharpe risk-free-rate boundary."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "invalid_risk_free_rate",
        [
            pytest.param(True, id="bool_true"),
            pytest.param(float("nan"), id="nan"),
            pytest.param(float("inf"), id="inf"),
            pytest.param("0.01", id="string"),
        ],
    )
    def Test_Invalid_Risk_Free_Rate_Raises(
        self,
        returns_data_small: pl.DataFrame,
        invalid_risk_free_rate: object,
    ) -> None:
        """Invalid risk-free-rate values should raise at the public boundary."""

        with pytest.raises(Exception_Validation_Input, match="risk_free_rate"):
            calc_optimalportfolios_maximum_sharpe_ratio(
                returns_data = returns_data_small,
                risk_free_rate=invalid_risk_free_rate,
            )