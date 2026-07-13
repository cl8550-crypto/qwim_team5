from __future__ import annotations

from collections.abc import Callable
from typing import Any

import polars as pl
import pytest

from src.models.portfolio_optimization._optport_convex import (
    calc_optimalportfolios_maximum_quadratic_utility,
)
from src.models.portfolio_optimization._optport_hierarchical import (
    calc_optimalportfolios_maximum_cara_gaussian_mixture,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


Calc_Function_Optimalportfolios = Callable[..., Any]


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
class Class_Test_Optimalportfolios_Risk_Aversion_Validation:
    """Focused validation tests for public risk-aversion boundaries."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("calc_function", "function_kwargs"),
        [
            pytest.param(
                calc_optimalportfolios_maximum_quadratic_utility,
                {},
                id="maximum_quadratic_utility",
            ),
            pytest.param(
                calc_optimalportfolios_maximum_cara_gaussian_mixture,
                {},
                id="maximum_cara_gaussian_mixture",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "invalid_risk_aversion",
        [
            pytest.param(True, id="bool_true"),
            pytest.param(float("nan"), id="nan"),
            pytest.param("1.0", id="string"),
        ],
    )
    def Test_Public_Functions_Invalid_Risk_Aversion_Raises(
        self,
        returns_data_small: pl.DataFrame,
        calc_function: Calc_Function_Optimalportfolios,
        function_kwargs: dict[str, Any],
        invalid_risk_aversion: object,
    ) -> None:
        """Public wrappers should reject invalid risk-aversion values early."""

        with pytest.raises(Exception_Validation_Input, match="risk_aversion"):
            calc_function(
                returns_data=returns_data_small,
                risk_aversion=invalid_risk_aversion,
                **function_kwargs,
            )