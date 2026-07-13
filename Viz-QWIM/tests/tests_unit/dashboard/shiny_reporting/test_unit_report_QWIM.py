"""
Unit Tests for QWIM PDF Report Generation
=========================================

This module contains unit tests for the report_QWIM.py module,
which provides PDF report generation for the QWIM Dashboard.

Test Coverage:
    - safe_is_finite_value: Safe finiteness checking

Note:
    Tests for ``create_qwim_styles_for_pdf_report`` (ReportLab-based styles)
    are skipped because ReportLab was removed from the project. The module now
    uses the Typst typesetting pipeline exclusively.
"""

import numpy as np
import pytest


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def sample_numeric_values():
    """Sample numeric values for testing."""
    return {
        "positive_int": 42,
        "negative_int": -17,
        "positive_float": 3.14159,
        "negative_float": -2.71828,
        "zero": 0,
        "zero_float": 0.0,
        "large_number": 1e15,
        "small_number": 1e-15,
    }


@pytest.fixture()
def sample_non_finite_values():
    """Sample non-finite values for testing."""
    return {
        "positive_inf": float("inf"),
        "negative_inf": float("-inf"),
        "nan": float("nan"),
        "np_nan": np.nan,
        "np_inf": np.inf,
        "np_neginf": -np.inf,
    }


# ============================================================================
# Tests for safe_is_finite_value
# ============================================================================


@pytest.mark.unit()
class Test_Safe_Is_Finite_Value:
    """Test cases for safe_is_finite_value function."""

    @pytest.mark.unit()
    def test_returns_true_for_positive_integer(self, sample_numeric_values):
        """Test returns True for positive integer."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["positive_int"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_negative_integer(self, sample_numeric_values):
        """Test returns True for negative integer."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["negative_int"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_positive_float(self, sample_numeric_values):
        """Test returns True for positive float."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["positive_float"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_negative_float(self, sample_numeric_values):
        """Test returns True for negative float."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["negative_float"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_zero(self, sample_numeric_values):
        """Test returns True for zero."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["zero"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_zero_float(self, sample_numeric_values):
        """Test returns True for zero float."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["zero_float"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_large_number(self, sample_numeric_values):
        """Test returns True for large number."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["large_number"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_small_number(self, sample_numeric_values):
        """Test returns True for small number."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_numeric_values["small_number"])

        assert result is True

    @pytest.mark.unit()
    def test_returns_false_for_positive_infinity(self, sample_non_finite_values):
        """Test returns False for positive infinity."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_non_finite_values["positive_inf"])

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_negative_infinity(self, sample_non_finite_values):
        """Test returns False for negative infinity."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_non_finite_values["negative_inf"])

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_nan(self, sample_non_finite_values):
        """Test returns False for NaN."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_non_finite_values["nan"])

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_numpy_nan(self, sample_non_finite_values):
        """Test returns False for numpy NaN."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_non_finite_values["np_nan"])

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_numpy_inf(self, sample_non_finite_values):
        """Test returns False for numpy infinity."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = sample_non_finite_values["np_inf"])

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_none(self):
        """Test returns False for None."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = None)

        assert result is False

    @pytest.mark.unit()
    def test_returns_false_for_string(self):
        """Test returns False for string."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = "42")

        assert result is False

    @pytest.mark.unit()
    def test_handles_list_input(self):
        """Test handles list input gracefully."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        try:
            result = safe_is_finite_value(value = [1, 2, 3])
            assert result is True or result is False
        except ValueError:
            pass  # acceptable  ambiguous array comparison

    @pytest.mark.unit()
    def test_returns_false_for_dict(self):
        """Test returns False for dict."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = {"value": 42})

        assert result is False

    @pytest.mark.unit()
    def test_returns_true_for_numpy_int(self):
        """Test returns True for numpy integer types."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = np.int64(42))

        assert result is True

    @pytest.mark.unit()
    def test_returns_true_for_numpy_float(self):
        """Test returns True for numpy float types."""
        from src.dashboard.reporting.report_QWIM import safe_is_finite_value

        result = safe_is_finite_value(value = np.float64(3.14))

        assert result is True



# ============================================================================
# Tests for safe_polars_column_access
# ============================================================================


@pytest.mark.unit()
class Test_Safe_Polars_Column_Access:
    """Tests for safe_polars_column_access function."""

    @pytest.fixture()
    def numeric_df(self):
        """Small numeric DataFrame for column-access tests."""
        import polars as pl  # noqa: PLC0415
        return pl.DataFrame({"val": [10, 20, 30], "cat": ["a", "b", "c"]})

    @pytest.mark.unit()
    def test_returns_default_when_dataframe_is_none(self):
        """Returns default_value when polars_DF is None."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = None, column_name = "val", default_value=-1)
        assert result == -1

    @pytest.mark.unit()
    def test_returns_default_for_empty_dataframe(self):
        """Returns default_value when DataFrame is empty."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = pl.DataFrame(), column_name = "val", default_value=-1)
        assert result == -1

    @pytest.mark.unit()
    def test_returns_default_when_column_missing(self, numeric_df):
        """Returns default_value when column does not exist."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "missing_col", default_value=99)
        assert result == 99

    @pytest.mark.unit()
    def test_sum_operation_on_numeric_column(self, numeric_df):
        """sum operation returns correct total."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "val", operation="sum")
        assert result == 60

    @pytest.mark.unit()
    def test_mean_operation_on_numeric_column(self, numeric_df):
        """mean operation returns correct average."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "val", operation="mean")
        assert result == 20.0

    @pytest.mark.unit()
    def test_n_unique_operation(self, numeric_df):
        """n_unique operation counts distinct values."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "cat", operation="n_unique")
        assert result == 3

    @pytest.mark.unit()
    def test_first_operation(self, numeric_df):
        """first operation returns first element."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "val", operation="first")
        assert result == 10

    @pytest.mark.unit()
    def test_count_operation(self, numeric_df):
        """count operation returns row count."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "val", operation="count")
        assert result == 3

    @pytest.mark.unit()
    def test_unknown_operation_returns_default(self, numeric_df):
        """Unknown operation string returns default_value."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "val", operation="median", default_value=-7)
        assert result == -7

    @pytest.mark.unit()
    def test_sum_on_string_column_returns_default(self, numeric_df):
        """sum on a non-numeric column returns default_value."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "cat", operation="sum", default_value=-5)
        assert result == -5

    @pytest.mark.unit()
    def test_mean_on_string_column_returns_default(self, numeric_df):
        """mean on a non-numeric column returns default_value."""
        from src.dashboard.reporting.report_QWIM import safe_polars_column_access
        result = safe_polars_column_access(polars_DF = numeric_df, column_name = "cat", operation="mean", default_value=-5)
        assert result == -5


# ============================================================================
# Tests for validate_polars_DF
# ============================================================================


@pytest.mark.unit()
class Test_Validate_Polars_DF:
    """Tests for validate_polars_DF function."""

    @pytest.mark.unit()
    def test_returns_false_for_none(self):
        """Returns False when input is None."""
        from src.dashboard.reporting.report_QWIM import validate_polars_DF
        assert validate_polars_DF(polars_DF = None) is False

    @pytest.mark.unit()
    def test_returns_false_for_non_dataframe(self):
        """Returns False when input is not a polars DataFrame."""
        from src.dashboard.reporting.report_QWIM import validate_polars_DF
        assert validate_polars_DF(polars_DF = {"a": [1, 2]}) is False

    @pytest.mark.unit()
    def test_returns_false_for_empty_dataframe(self):
        """Returns False when DataFrame has no rows."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import validate_polars_DF
        assert validate_polars_DF(polars_DF = pl.DataFrame()) is False

    @pytest.mark.unit()
    def test_returns_true_for_valid_dataframe(self):
        """Returns True for a non-empty polars DataFrame."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import validate_polars_DF
        df = pl.DataFrame({"x": [1, 2, 3]})
        assert validate_polars_DF(polars_DF = df) is True

    @pytest.mark.unit()
    def test_custom_name_does_not_affect_return_value(self):
        """dataframe_name parameter is cosmetic; return value is unaffected."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import validate_polars_DF
        df = pl.DataFrame({"x": [1]})
        assert validate_polars_DF(polars_DF = df, dataframe_name="My_DF") is True


# ============================================================================
# Tests for create_sample_*_dataframe factory functions
# ============================================================================


@pytest.mark.unit()
class Test_Create_Sample_Dataframes:
    """Tests for the four create_sample_*_dataframe factory functions."""

    @pytest.mark.unit()
    def test_personal_info_returns_polars_dataframe(self):
        """create_sample_personal_info_dataframe returns a polars DataFrame."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import create_sample_personal_info_dataframe
        df = create_sample_personal_info_dataframe()
        assert isinstance(df, pl.DataFrame)

    @pytest.mark.unit()
    def test_personal_info_has_expected_columns(self):
        """create_sample_personal_info_dataframe has required columns."""
        from src.dashboard.reporting.report_QWIM import create_sample_personal_info_dataframe
        df = create_sample_personal_info_dataframe()
        expected = {"Investor_ID", "Investor_Type", "Name_First", "Name_Last",
                    "Age_Current", "Age_Retirement", "State_Residence", "Risk_Tolerance"}
        assert expected.issubset(set(df.columns))

    @pytest.mark.unit()
    def test_personal_info_has_rows(self):
        """create_sample_personal_info_dataframe is non-empty."""
        from src.dashboard.reporting.report_QWIM import create_sample_personal_info_dataframe
        assert create_sample_personal_info_dataframe().height > 0

    @pytest.mark.unit()
    def test_assets_returns_polars_dataframe(self):
        """create_sample_assets_dataframe returns a polars DataFrame."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import create_sample_assets_dataframe
        assert isinstance(create_sample_assets_dataframe(), pl.DataFrame)

    @pytest.mark.unit()
    def test_assets_has_expected_columns(self):
        """create_sample_assets_dataframe has required columns."""
        from src.dashboard.reporting.report_QWIM import create_sample_assets_dataframe
        df = create_sample_assets_dataframe()
        expected = {"Investor_ID", "Asset_Category", "Asset_Value", "Asset_Type", "Institution_Name"}
        assert expected.issubset(set(df.columns))

    @pytest.mark.unit()
    def test_assets_asset_value_is_numeric(self):
        """Asset_Value column contains numeric data."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import create_sample_assets_dataframe
        df = create_sample_assets_dataframe()
        assert df["Asset_Value"].dtype in (pl.Int64, pl.Int32, pl.Float64, pl.Float32)

    @pytest.mark.unit()
    def test_goals_returns_polars_dataframe(self):
        """create_sample_goals_dataframe returns a polars DataFrame."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import create_sample_goals_dataframe
        assert isinstance(create_sample_goals_dataframe(), pl.DataFrame)

    @pytest.mark.unit()
    def test_goals_has_expected_columns(self):
        """create_sample_goals_dataframe has required columns."""
        from src.dashboard.reporting.report_QWIM import create_sample_goals_dataframe
        df = create_sample_goals_dataframe()
        expected = {"Investor_ID", "Goal_Category", "Goal_Amount", "Goal_Priority", "Goal_Timeline"}
        assert expected.issubset(set(df.columns))

    @pytest.mark.unit()
    def test_goals_priorities_are_positive(self):
        """Goal_Priority values are all positive integers."""
        from src.dashboard.reporting.report_QWIM import create_sample_goals_dataframe
        df = create_sample_goals_dataframe()
        assert all(p > 0 for p in df["Goal_Priority"].to_list())

    @pytest.mark.unit()
    def test_income_returns_polars_dataframe(self):
        """create_sample_income_dataframe returns a polars DataFrame."""
        import polars as pl  # noqa: PLC0415
        from src.dashboard.reporting.report_QWIM import create_sample_income_dataframe
        assert isinstance(create_sample_income_dataframe(), pl.DataFrame)

    @pytest.mark.unit()
    def test_income_has_expected_columns(self):
        """create_sample_income_dataframe has required columns."""
        from src.dashboard.reporting.report_QWIM import create_sample_income_dataframe
        df = create_sample_income_dataframe()
        expected = {"Investor_ID", "Income_Category", "Income_Annual", "Income_Start_Age", "Income_End_Age"}
        assert expected.issubset(set(df.columns))

    @pytest.mark.unit()
    def test_income_end_age_greater_than_start_age(self):
        """Income_End_Age is always greater than Income_Start_Age."""
        from src.dashboard.reporting.report_QWIM import create_sample_income_dataframe
        df = create_sample_income_dataframe()
        for start, end in zip(df["Income_Start_Age"].to_list(), df["Income_End_Age"].to_list()):
            assert end > start
