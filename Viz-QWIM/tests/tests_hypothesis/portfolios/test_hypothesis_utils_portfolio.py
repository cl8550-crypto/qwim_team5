"""Hypothesis property-based tests for utils_portfolio module.

Property tests verify structural invariants of the pure utility functions in
``utils_portfolio``:

- ``suggest_component_matches``: case-insensitive lookup into ETF columns.
- ``create_sample_portfolio_weights``: weights from in-memory ETF DataFrames.
- ``create_benchmark_portfolio_values``: benchmark derivation preserves row count.
- ``ensure_path_exists``: idempotent directory creation.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math
import tempfile
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.portfolios.utils_portfolio import (
    create_benchmark_portfolio_values,
    create_sample_portfolio_weights,
    ensure_path_exists,
    suggest_component_matches,
)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_strategy_ticker = st.text(
    alphabet=st.characters(whitelist_categories=("Lu",)),
    min_size=1,
    max_size=5,
)

_strategy_lowercase_ticker = st.text(
    alphabet=st.characters(whitelist_categories=("Ll",)),
    min_size=1,
    max_size=5,
)

_WINDOWS_RESERVED_PATH_NAMES = {
    "AUX",
    "CON",
    "NUL",
    "PRN",
    *(f"COM{idx_port}" for idx_port in range(1, 10)),
    *(f"LPT{idx_port}" for idx_port in range(1, 10)),
}

_strategy_safe_path_part = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=8,
).filter(lambda value_text: value_text.upper() not in _WINDOWS_RESERVED_PATH_NAMES)

_strategy_unique_tickers = st.lists(
    _strategy_ticker,
    min_size=1,
    max_size=8,
    unique=True,
).filter(lambda lst: all(len(t) > 0 for t in lst))


def _strategy_etf_dataframe(
    min_tickers: int = 1,
    max_tickers: int = 4,
    min_rows: int = 10,
    max_rows: int = 60,
):
    """Strategy that produces a polars DataFrame with Date + asset-price columns."""
    return st.builds(
        _build_etf_dataframe,
        tickers=st.lists(
            _strategy_ticker,
            min_size=min_tickers,
            max_size=max_tickers,
            unique=True,
        ).filter(lambda lst: all(len(t) > 0 for t in lst)),
        n_rows=st.integers(min_value=min_rows, max_value=max_rows),
        start_offset_days=st.integers(min_value=0, max_value=365),
    )


def _build_etf_dataframe(
    tickers: list[str],
    n_rows: int,
    start_offset_days: int,
) -> pl.DataFrame:
    """Construct a minimal ETF DataFrame with a Date column and float price columns."""
    start = date(2020, 1, 1) + timedelta(days=start_offset_days)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(n_rows)]
    data: dict[str, object] = {"Date": dates}
    for ticker in tickers:
        # Deterministic prices: base + row_index so they are strictly > 0
        data[ticker] = [float(100 + i) for i in range(n_rows)]
    return pl.DataFrame(data)


def _strategy_portfolio_values_dataframe(
    min_rows: int = 3,
    max_rows: int = 40,
):
    """Strategy producing a DataFrame with Date and Portfolio_Value columns."""
    return st.builds(
        _build_portfolio_values,
        n_rows=st.integers(min_value=min_rows, max_value=max_rows),
        initial_value=st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    )


def _build_portfolio_values(n_rows: int, initial_value: float) -> pl.DataFrame:
    start = date(2021, 1, 1)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(n_rows)]
    # Simple upward ramp so no zero or negative values
    values = [initial_value + float(i) for i in range(n_rows)]
    return pl.DataFrame({"Date": dates, "Portfolio_Value": values})


# ===========================================================================
# suggest_component_matches
# ===========================================================================


class Class_Test_Hypothesis_Suggest_Component_Matches:
    """Property tests for ``suggest_component_matches``."""

    @pytest.mark.unit()
    @given(
        tickers=_strategy_unique_tickers,
    )
    @settings(max_examples=200)
    def Test_exact_match_always_found(self, tickers: list[str]) -> None:
        """An uppercase ticker is found when it is in the ETF columns list."""
        assume(len(tickers) >= 1)
        components = tickers[:1]
        etf_columns = list(tickers)
        result = suggest_component_matches(components = components, etf_columns = etf_columns)
        # The component is in etf_columns exactly → must appear in suggestions
        comp = components[0]
        assert comp in result
        assert comp in result[comp]

    @pytest.mark.unit()
    @given(
        tickers=_strategy_unique_tickers,
        extra=_strategy_unique_tickers,
    )
    @settings(max_examples=150)
    def Test_date_key_never_in_result(
        self,
        tickers: list[str],
        extra: list[str],
    ) -> None:
        """'Date' is always filtered from components before matching."""
        components = ["Date"] + tickers
        etf_columns = ["Date"] + extra
        result = suggest_component_matches(components = components, etf_columns = etf_columns)
        assert "Date" not in result

    @pytest.mark.unit()
    @given(
        tickers=_strategy_unique_tickers,
        etf_extra=_strategy_unique_tickers,
    )
    @settings(max_examples=150)
    def Test_all_suggestion_values_are_subsets_of_etf_columns(
        self,
        tickers: list[str],
        etf_extra: list[str],
    ) -> None:
        """Every suggested match is drawn from the ``etf_columns`` argument."""
        all_etf = list({*tickers, *etf_extra})
        result = suggest_component_matches(components = tickers, etf_columns = all_etf)
        for component, matches in result.items():
            for match in matches:
                assert match in all_etf, (
                    f"Suggestion {match!r} for {component!r} is not in etf_columns"
                )

    @pytest.mark.unit()
    @given(
        components=st.lists(_strategy_ticker, min_size=0, max_size=5),
    )
    @settings(max_examples=100)
    def Test_empty_etf_columns_returns_empty_dict(
        self,
        components: list[str],
    ) -> None:
        """No matches possible against an empty ETF column list."""
        result = suggest_component_matches(components = components, etf_columns = [])
        assert result == {}

    @pytest.mark.unit()
    @given(
        etf_columns=_strategy_unique_tickers,
    )
    @settings(max_examples=100)
    def Test_empty_components_returns_empty_dict(
        self,
        etf_columns: list[str],
    ) -> None:
        """No components to match → empty result."""
        result = suggest_component_matches(components = [], etf_columns = etf_columns)
        assert result == {}


# ===========================================================================
# create_sample_portfolio_weights
# ===========================================================================


class Class_Test_Hypothesis_Create_Sample_Portfolio_Weights:
    """Property tests for ``create_sample_portfolio_weights``."""

    @pytest.mark.unit()
    @given(etf_df=_strategy_etf_dataframe(min_rows=14, max_rows=60))
    @settings(max_examples=100)
    def Test_output_has_date_column(self, etf_df: pl.DataFrame) -> None:
        """Output DataFrame always contains a 'Date' column."""
        result = create_sample_portfolio_weights(etf_data = etf_df)
        assert "Date" in result.columns

    @pytest.mark.unit()
    @given(etf_df=_strategy_etf_dataframe(min_rows=14, max_rows=60))
    @settings(max_examples=100)
    def Test_output_columns_match_asset_columns(self, etf_df: pl.DataFrame) -> None:
        """Non-Date columns in output match the non-Date columns in input."""
        asset_cols = [c for c in etf_df.columns if c != "Date"]
        result = create_sample_portfolio_weights(etf_data = etf_df)
        result_asset_cols = [c for c in result.columns if c != "Date"]
        assert sorted(result_asset_cols) == sorted(asset_cols)

    @pytest.mark.unit()
    @given(etf_df=_strategy_etf_dataframe(min_rows=14, max_rows=60))
    @settings(max_examples=100)
    def Test_weights_sum_to_one_per_row(self, etf_df: pl.DataFrame) -> None:
        """Every row's non-Date weights sum to approximately 1.0."""
        result = create_sample_portfolio_weights(etf_data = etf_df)
        asset_cols = [c for c in result.columns if c != "Date"]
        for row_idx in range(result.height):
            row_sum = sum(result[col][row_idx] for col in asset_cols)
            assert math.isclose(row_sum, 1.0, rel_tol=1e-6, abs_tol=1e-9), (
                f"Row {row_idx} weights sum to {row_sum}, expected 1.0"
            )

    @pytest.mark.unit()
    @given(etf_df=_strategy_etf_dataframe(min_rows=14, max_rows=60))
    @settings(max_examples=100)
    def Test_output_rows_not_exceed_input_rows(self, etf_df: pl.DataFrame) -> None:
        """Rebalancing produces at most as many rows as there are input dates."""
        result = create_sample_portfolio_weights(etf_data = etf_df)
        assert result.height <= etf_df.height


# ===========================================================================
# create_benchmark_portfolio_values
# ===========================================================================


class Class_Test_Hypothesis_Create_Benchmark_Portfolio_Values:
    """Property tests for ``create_benchmark_portfolio_values``."""

    @pytest.mark.unit()
    @given(pv_df=_strategy_portfolio_values_dataframe(min_rows=3, max_rows=40))
    @settings(max_examples=150)
    def Test_output_row_count_equals_input(self, pv_df: pl.DataFrame) -> None:
        """Benchmark has exactly as many rows as the source portfolio values."""
        result = create_benchmark_portfolio_values(portfolio_values = pv_df)
        assert result.height == pv_df.height

    @pytest.mark.unit()
    @given(pv_df=_strategy_portfolio_values_dataframe(min_rows=3, max_rows=40))
    @settings(max_examples=150)
    def Test_output_has_date_and_value_columns(self, pv_df: pl.DataFrame) -> None:
        """Output contains 'Date' and 'Value' columns."""
        result = create_benchmark_portfolio_values(portfolio_values = pv_df)
        assert "Date" in result.columns
        assert "Value" in result.columns

    @pytest.mark.unit()
    @given(pv_df=_strategy_portfolio_values_dataframe(min_rows=3, max_rows=40))
    @settings(max_examples=150)
    def Test_first_row_value_preserved(self, pv_df: pl.DataFrame) -> None:
        """The first benchmark value equals the first source portfolio value."""
        result = create_benchmark_portfolio_values(portfolio_values = pv_df)
        first_source = pv_df["Portfolio_Value"][0]
        first_benchmark = result["Value"][0]
        assert math.isclose(first_source, first_benchmark, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(pv_df=_strategy_portfolio_values_dataframe(min_rows=3, max_rows=40))
    @settings(max_examples=150)
    def Test_dates_preserved_in_output(self, pv_df: pl.DataFrame) -> None:
        """Output 'Date' column contains the same values as the input 'Date' column."""
        result = create_benchmark_portfolio_values(portfolio_values = pv_df)
        assert result["Date"].to_list() == pv_df["Date"].to_list()


# ===========================================================================
# ensure_path_exists
# ===========================================================================


class Class_Test_Hypothesis_Ensure_Path_Exists:
    """Property tests for ``ensure_path_exists``."""

    @pytest.mark.unit()
    @given(
        sub_parts=st.lists(
            _strategy_safe_path_part,
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    @settings(max_examples=60)
    def Test_returned_path_exists_after_call(
        self,
        sub_parts: list[str],
    ) -> None:
        """The returned Path object exists on disk after ``ensure_path_exists``."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for part in sub_parts:
                target = target / part
            returned = ensure_path_exists(path = target)
            assert returned.exists()
            assert returned.is_dir()

    @pytest.mark.unit()
    @given(
        sub_parts=st.lists(
            _strategy_safe_path_part,
            min_size=1,
            max_size=2,
            unique=True,
        )
    )
    @settings(max_examples=60)
    def Test_idempotent_second_call_does_not_raise(
        self,
        sub_parts: list[str],
    ) -> None:
        """Calling ``ensure_path_exists`` twice on the same path does not raise."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for part in sub_parts:
                target = target / part
            ensure_path_exists(path = target)
            # Second call must not raise
            returned = ensure_path_exists(path = target)
            assert returned.exists()

    @pytest.mark.unit()
    @given(
        sub_parts=st.lists(
            _strategy_safe_path_part,
            min_size=1,
            max_size=2,
            unique=True,
        )
    )
    @settings(max_examples=60)
    def Test_return_value_is_path_instance(
        self,
        sub_parts: list[str],
    ) -> None:
        """``ensure_path_exists`` returns a ``Path`` instance."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for part in sub_parts:
                target = target / part
            returned = ensure_path_exists(path = target)
            assert isinstance(returned, Path)
