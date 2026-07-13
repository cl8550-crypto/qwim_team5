from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization._optport_hierarchical import (
    calc_optimalportfolios_tracking_error_minimization,
)
from src.portfolios.portfolio_QWIM import Portfolio_QWIM
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
    """Return a minimal deterministic benchmark frame for alignment tests.

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
class Class_Test_Optimalportfolios_Tracking_Error_Date_Alignment:
    """Focused tests for tracking-error benchmark date alignment."""

    @pytest.mark.unit()
    def Test_Reordered_Benchmark_Dates_Are_Aligned(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """Benchmark rows with matching dates in different order should still work."""

        benchmark_returns_reordered = benchmark_returns_small.reverse()

        portfolio_result = calc_optimalportfolios_tracking_error_minimization(
            returns_data = returns_data_small,
            benchmark_returns = benchmark_returns_reordered,
        )

        assert isinstance(portfolio_result, Portfolio_QWIM)

    @pytest.mark.unit()
    def Test_Mismatched_Benchmark_Dates_Raise(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """Benchmark rows with different dates should raise at the public boundary."""

        benchmark_returns_mismatched = benchmark_returns_small.with_columns(
            pl.Series(
                "Date",
                ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            )
        )

        with pytest.raises(Exception_Validation_Input, match="matching Date values"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = returns_data_small,
                benchmark_returns = benchmark_returns_mismatched,
            )

    @pytest.mark.unit()
    def Test_Length_Mismatched_Benchmark_Raises(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """A benchmark with a different row count should be rejected."""

        benchmark_returns_short = benchmark_returns_small.head(3)

        with pytest.raises(Exception_Validation_Input, match="same length"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = returns_data_small,
                benchmark_returns = benchmark_returns_short,
            )

    @pytest.mark.unit()
    def Test_Multi_Column_Benchmark_Raises(
        self,
        returns_data_small: pl.DataFrame,
    ) -> None:
        """A benchmark with more than one asset column should be rejected."""

        benchmark_returns_multi = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
                "SPY": [0.008, 0.004, 0.011, 0.002],
                "AGG": [0.004, 0.002, 0.003, 0.001],
            }
        )

        with pytest.raises(Exception_Validation_Input, match="exactly one asset column"):
            calc_optimalportfolios_tracking_error_minimization(
                returns_data = returns_data_small,
                benchmark_returns = benchmark_returns_multi,
            )