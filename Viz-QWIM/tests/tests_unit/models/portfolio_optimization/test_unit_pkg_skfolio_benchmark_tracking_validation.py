from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization.pkg_skfolio import (
    calc_skfolio_optimization_convex,
)
from src.portfolios.portfolio_QWIM import Portfolio_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.fixture()
def returns_data_small() -> pl.DataFrame:
    """Return a minimal deterministic returns frame for benchmark-tracking tests.

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
    """Return a minimal deterministic single-column benchmark frame.

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
class Class_Test_Pkg_Skfolio_Benchmark_Tracking_Validation:
    """Focused tests for skfolio benchmark-tracking input validation."""

    @pytest.mark.unit()
    def Test_Reordered_Benchmark_Dates_Are_Aligned(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """A reordered benchmark with matching dates should still produce a portfolio."""

        benchmark_returns_reordered = benchmark_returns_small.reverse()

        portfolio_result = calc_skfolio_optimization_convex(
            returns_data=returns_data_small,
            optimization_type="CONVEX_BENCHMARK_TRACKING",
            benchmark_returns=benchmark_returns_reordered,
            portfolio_name="Benchmark Tracking Reordered",
        )

        assert isinstance(portfolio_result, Portfolio_QWIM)

    @pytest.mark.unit()
    def Test_Mismatched_Benchmark_Dates_Raise(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """A benchmark with non-matching dates should raise at the public boundary."""

        benchmark_returns_mismatched = benchmark_returns_small.with_columns(
            pl.Series(
                "Date",
                ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            )
        )

        with pytest.raises(Exception_Validation_Input, match="matching Date values"):
            calc_skfolio_optimization_convex(
                returns_data=returns_data_small,
                optimization_type="CONVEX_BENCHMARK_TRACKING",
                benchmark_returns=benchmark_returns_mismatched,
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
            calc_skfolio_optimization_convex(
                returns_data=returns_data_small,
                optimization_type="CONVEX_BENCHMARK_TRACKING",
                benchmark_returns=benchmark_returns_short,
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
            calc_skfolio_optimization_convex(
                returns_data=returns_data_small,
                optimization_type="CONVEX_BENCHMARK_TRACKING",
                benchmark_returns=benchmark_returns_multi,
            )

    @pytest.mark.unit()
    def Test_Invalid_Benchmark_Content_Raises(
        self,
        returns_data_small: pl.DataFrame,
        benchmark_returns_small: pl.DataFrame,
    ) -> None:
        """A benchmark with invalid return content should be rejected at validation."""

        benchmark_returns_invalid = benchmark_returns_small.with_columns(
            pl.Series("SPY", [0.008, 0.004, float("nan"), 0.002])
        )

        with pytest.raises(Exception_Validation_Input, match="Invalid benchmark_returns"):
            calc_skfolio_optimization_convex(
                returns_data=returns_data_small,
                optimization_type="CONVEX_BENCHMARK_TRACKING",
                benchmark_returns=benchmark_returns_invalid,
            )