from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization._optport_hierarchical import (
    calc_optimalportfolios_tracking_error_minimization,
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


@pytest.fixture()
def benchmark_returns_small() -> pl.DataFrame:
    """Return a minimal deterministic benchmark frame for wrapper validation tests.

    Returns
    -------
    pl.DataFrame
        Small Polars DataFrame with one ``Date`` column and one benchmark
        return column.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "SPY": [0.008, 0.004, 0.011, 0.002],
        }
    )


@pytest.mark.unit()
class Class_Test_Optimalportfolios_Tracking_Error_Is_Long_Only_Validation:
    """Focused validation tests for the tracking-error is-long-only boundary."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "invalid_is_long_only",
        [
            pytest.param("False", id="string_false"),
            pytest.param(1, id="integer_one"),
            pytest.param(None, id="none"),
        ],
    )
    def Test_Invalid_Is_Long_Only_Raises(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
        invalid_is_long_only: object,
    ) -> None:
        """Invalid is-long-only values should raise at the public boundary."""

        with pytest.raises(Exception_Validation_Input, match="is_long_only"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = returns_data_small,
                benchmark_returns = benchmark_returns_small,
                is_long_only=invalid_is_long_only,
            )