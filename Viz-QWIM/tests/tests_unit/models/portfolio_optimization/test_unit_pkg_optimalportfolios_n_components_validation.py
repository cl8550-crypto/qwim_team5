from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization._optport_hierarchical import (
    calc_optimalportfolios_maximum_cara_gaussian_mixture,
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
class Class_Test_Optimalportfolios_N_Components_Validation:
    """Focused validation tests for the CARA-GMM n-components boundary."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "invalid_n_components",
        [
            pytest.param(True, id="bool_true"),
            pytest.param(0, id="zero"),
            pytest.param(-1, id="negative_one"),
            pytest.param(2.5, id="float"),
            pytest.param(float("nan"), id="nan"),
            pytest.param("2", id="string"),
        ],
    )
    def Test_Invalid_N_Components_Raises(
        self,
        returns_data_small: pl.DataFrame,
        invalid_n_components: object,
    ) -> None:
        """Invalid n-components values should raise at the public boundary."""

        with pytest.raises(Exception_Validation_Input, match="n_components"):
            calc_optimalportfolios_maximum_cara_gaussian_mixture(
                returns_data = returns_data_small,
                n_components=invalid_n_components,
            )