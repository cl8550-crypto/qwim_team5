"""Unit tests for utils_tab_portfolios module.

Tests the validate_portfolio_data function covering all validation branches:
- None input
- Non-DataFrame type input
- Empty DataFrame
- Missing Date column
- Missing Value column (portfolio / benchmark data)
- All-non-numeric Value column
- Mixed numeric / non-numeric Value column (partial → passes)
- Fully valid portfolio data
- Weights data: no component columns
- Weights data: valid with components
- Unrecognised dataset_name (Date present → passes)
"""

from __future__ import annotations

import polars as pl
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_portfolio_df() -> pl.DataFrame:
    """Return a minimal valid 'portfolio data' DataFrame."""
    return pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"], "Value": [100.0, 110.0]})


def _make_valid_benchmark_df() -> pl.DataFrame:
    """Return a minimal valid 'benchmark data' DataFrame."""
    return pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"], "Value": [98.0, 105.0]})


def _make_valid_weights_df() -> pl.DataFrame:
    """Return a minimal valid 'weights data' DataFrame."""
    return pl.DataFrame({"Date": ["2024-01-01"], "VTI": [0.6], "AGG": [0.4]})


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_None_And_Types:
    """Tests for None and wrong-type inputs."""

    @pytest.mark.unit()
    def test_none_returns_false(self):
        """None input yields (False, message containing dataset name)."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=None)

        assert is_valid is False
        assert "portfolio data" in msg.lower()

    @pytest.mark.unit()
    def test_none_custom_dataset_name(self):
        """None input with custom dataset name includes that name in message."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=None, dataset_name="custom data")

        assert is_valid is False
        assert "custom data" in msg.lower()

    @pytest.mark.parametrize(
        "bad_input",
        [
            "a string",
            42,
            3.14,
            ["list"],
            {"key": "value"},
            (1, 2),
            True,
        ],
    )
    @pytest.mark.unit()
    def test_non_dataframe_returns_false(self, bad_input):
        """Non-DataFrame inputs return False with type information."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=bad_input)

        assert is_valid is False
        assert "Invalid" in msg or "invalid" in msg


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Empty:
    """Tests for empty DataFrame."""

    @pytest.mark.unit()
    def test_empty_dataframe_returns_false(self):
        """Empty DataFrame yields (False, message mentioning empty)."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=pl.DataFrame())

        assert is_valid is False
        assert "empty" in msg.lower()

    @pytest.mark.unit()
    def test_empty_dataframe_with_columns_returns_false(self):
        """Empty DataFrame even with proper column names still fails."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": [], "Value": []}).cast({"Value": pl.Float64})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df)

        assert is_valid is False
        assert "empty" in msg.lower()


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Missing_Date:
    """Tests for DataFrames missing the required Date column."""

    @pytest.mark.unit()
    def test_missing_date_column_returns_false(self):
        """DataFrame without 'Date' column returns False."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Value": [100.0, 110.0]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df)

        assert is_valid is False
        assert "Date" in msg

    @pytest.mark.unit()
    def test_wrong_case_date_column_returns_false(self):
        """'date' (lowercase) is not treated as 'Date' — fails validation."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"date": ["2024-01-01"], "Value": [100.0]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df)

        assert is_valid is False
        assert "Date" in msg


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Portfolio_And_Benchmark:
    """Tests for 'portfolio data' and 'benchmark data' dataset names."""

    @pytest.mark.parametrize("dataset_name", ["portfolio data", "benchmark data"])
    @pytest.mark.unit()
    def test_missing_value_column_returns_false(self, dataset_name):
        """DataFrame without 'Value' column returns False for portfolio/benchmark."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"], "Price": [100.0, 110.0]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name=dataset_name)

        assert is_valid is False
        assert "Value" in msg

    @pytest.mark.parametrize("dataset_name", ["portfolio data", "benchmark data"])
    @pytest.mark.unit()
    def test_all_non_numeric_value_column_returns_false(self, dataset_name):
        """DataFrame with all non-numeric Value entries returns False."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"], "Value": ["N/A", "missing"]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name=dataset_name)

        assert is_valid is False
        assert "numeric" in msg.lower()

    @pytest.mark.parametrize("dataset_name", ["portfolio data", "benchmark data"])
    @pytest.mark.unit()
    def test_mixed_numeric_non_numeric_value_returns_true(self, dataset_name):
        """DataFrame with some numeric and some non-numeric Value entries passes."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        # Only fully non-numeric is rejected; partial still passes
        df = pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"], "Value": ["100.0", "N/A"]})

        is_valid, _ = validate_portfolio_data(portfolio_dataframe=df, dataset_name=dataset_name)

        assert is_valid is True

    @pytest.mark.parametrize("dataset_name", ["portfolio data", "benchmark data"])
    @pytest.mark.unit()
    def test_valid_dataframe_returns_true(self, dataset_name):
        """Fully valid DataFrame returns (True, empty string)."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = _make_valid_portfolio_df() if dataset_name == "portfolio data" else _make_valid_benchmark_df()

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name=dataset_name)

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_default_dataset_name_is_portfolio_data(self):
        """Omitting dataset_name uses 'portfolio data' as default."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        # Missing Value column — message should mention "portfolio data"
        df = pl.DataFrame({"Date": ["2024-01-01"], "Price": [100.0]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df)

        assert is_valid is False
        assert "portfolio data" in msg.lower()


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Weights:
    """Tests for 'weights data' dataset name."""

    @pytest.mark.unit()
    def test_no_component_columns_returns_false(self):
        """weights data with only Date column returns False."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2024-01-01", "2024-02-01"]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="weights data")

        assert is_valid is False
        assert "component" in msg.lower()

    @pytest.mark.unit()
    def test_valid_weights_with_components_returns_true(self):
        """Weights DataFrame with component columns returns (True, '')."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = _make_valid_weights_df()

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="weights data")

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_weights_data_does_not_require_value_column(self):
        """Weights data skips the 'Value' column check."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2024-01-01"], "ETF_A": [0.5], "ETF_B": [0.5]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="weights data")

        assert is_valid is True
        assert msg == ""


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Other_Dataset:
    """Tests for unrecognised dataset_name values."""

    @pytest.mark.unit()
    def test_other_dataset_name_only_needs_date_column(self):
        """Unrecognised dataset_name skips Value/component checks; Date suffices."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"Date": ["2024-01-01"], "SomeColumn": [42]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="some other data")

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_other_dataset_name_still_requires_date(self):
        """Unrecognised dataset_name still requires the Date column."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame({"SomeColumn": [42]})

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="some other data")

        assert is_valid is False
        assert "Date" in msg


@pytest.mark.regression()
class Test_Validate_Portfolio_Data_Regression:
    """Regression tests ensuring known-good inputs produce stable outputs."""

    @pytest.mark.unit()
    def test_portfolio_data_all_valid_regression(self):
        """Standard valid portfolio DataFrame must return (True, '')."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        df = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                "Value": [10000.0, 10500.0, 11000.0],
            },
        )

        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="portfolio data")

        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit()
    def test_none_always_returns_false_regression(self):
        """None must always return False, never raise an exception."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        for _ in range(3):
            is_valid, msg = validate_portfolio_data(portfolio_dataframe=None)
            assert is_valid is False
            assert isinstance(msg, str)

    @pytest.mark.unit()
    def test_return_type_always_tuple_of_bool_str(self):
        """Return value must always be (bool, str) in all branches."""
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        cases = [
            (None, "portfolio data"),
            ("bad", "portfolio data"),
            (pl.DataFrame(), "portfolio data"),
            (pl.DataFrame({"Date": ["2024-01-01"], "Value": [100.0]}), "portfolio data"),
            (pl.DataFrame({"Date": ["2024-01-01"]}), "weights data"),
            (pl.DataFrame({"Date": ["2024-01-01"], "VTI": [1.0]}), "weights data"),
        ]

        for df_input, name in cases:
            result = validate_portfolio_data(portfolio_dataframe=df_input, dataset_name=name)
            assert isinstance(result, tuple), f"Expected tuple for ({df_input!r}, {name!r})"
            assert len(result) == 2, f"Expected 2-tuple for ({df_input!r}, {name!r})"
            assert isinstance(result[0], bool), f"First element must be bool for ({df_input!r}, {name!r})"
            assert isinstance(result[1], str), f"Second element must be str for ({df_input!r}, {name!r})"


@pytest.mark.unit()
class Test_Validate_Portfolio_Data_Exception_Path:
    """Tests that trigger the except branch in the numeric validation try/except."""

    @pytest.mark.unit()
    def test_to_numeric_raises_returns_false(self, monkeypatch):
        """When cast raises unexpectedly, function returns (False, error msg)."""
        import polars as _pl
        from src.dashboard.shiny_utils.utils_tab_portfolios import validate_portfolio_data

        # Monkeypatch pl.Series.cast to raise on Float64 cast
        original_cast = _pl.Series.cast

        def _raise_cast(self, dtype, *args, **kwargs):
            if dtype == _pl.Float64:
                raise ValueError("simulated numeric conversion error")
            return original_cast(self, dtype, *args, **kwargs)

        monkeypatch.setattr(_pl.Series, "cast", _raise_cast)

        df = _pl.DataFrame({"Date": ["2024-01-01"], "Value": [100.0]})
        is_valid, msg = validate_portfolio_data(portfolio_dataframe=df, dataset_name="portfolio data")

        assert is_valid is False
        assert "Error validating" in msg or "simulated" in msg
