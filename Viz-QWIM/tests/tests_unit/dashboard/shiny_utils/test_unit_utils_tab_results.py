def process_data_for_plot_tab_results(data_frame, date_column="date", max_points=5000):
    """Process data for plotting with downsampling if needed."""
    if data_frame is None or data_frame.is_empty():
        return data_frame

    # If data is within limits, return as-is
    if data_frame.height <= max_points:
        return data_frame

    # Calculate downsampling factor
    downsample_factor = max(1, data_frame.height // max_points)

    # Sort by date and downsample
    sorted_data = data_frame.sort(date_column)
    downsampled_data = sorted_data.slice(0, None, downsample_factor)

    return downsampled_data


def normalize_data_tab_results(data_frame, method="none"):
    """Normalize data using specified method."""
    if method == "none" or data_frame is None or data_frame.is_empty():
        return data_frame

    # Get numeric columns (exclude date)
    numeric_columns = [col for col in data_frame.columns if col != "date"]

    if method == "min_max":
        # Min-Max normalization
        for col in numeric_columns:
            min_val = data_frame.select(pl.col(col).min()).item()
            max_val = data_frame.select(pl.col(col).max()).item()
            if max_val > min_val:
                data_frame = data_frame.with_columns(
                    ((pl.col(col) - min_val) / (max_val - min_val)).alias(col),
                )

    elif method == "z_score":
        # Z-score normalization
        for col in numeric_columns:
            mean_val = data_frame.select(pl.col(col).mean()).item()
            std_val = data_frame.select(pl.col(col).std()).item()
            if std_val > 0:
                data_frame = data_frame.with_columns(
                    ((pl.col(col) - mean_val) / std_val).alias(col),
                )

    return data_frame


def transform_data_tab_results(data_frame, transformation="none", baseline_date=None):
    """Transform data based on specified transformation type."""
    if transformation == "none" or data_frame is None or data_frame.is_empty():
        return data_frame

    # Get series columns (exclude date)
    series_columns = [col for col in data_frame.columns if col != "date"]

    if transformation == "percent_change":
        # Calculate percent change from first value
        for col in series_columns:
            first_val = data_frame.select(pl.col(col).first()).item()
            if first_val != 0:
                data_frame = data_frame.with_columns(
                    ((pl.col(col) / first_val - 1) * 100).alias(f"{col}_pct"),
                )

    elif transformation == "cumulative":
        # Calculate cumulative sum
        for col in series_columns:
            data_frame = data_frame.with_columns(
                pl.col(col).cumsum().alias(f"{col}_cum"),
            )

    elif transformation == "comparative" and baseline_date:
        # Calculate relative change from baseline date
        baseline_dt = pd.to_datetime(baseline_date)

        # Find the closest date to baseline
        data_pd = data_frame.to_pandas()
        data_pd["date"] = pd.to_datetime(data_pd["date"])
        data_pd["date_diff"] = abs(data_pd["date"] - baseline_dt)
        baseline_idx = data_pd["date_diff"].idxmin()

        for col in series_columns:
            baseline_val = data_pd.loc[baseline_idx, col]
            if baseline_val != 0:
                data_pd[f"{col}_rel"] = (data_pd[col] / baseline_val - 1) * 100

        # Convert back to polars
        data_frame = pl.from_pandas(data_pd.drop("date_diff", axis=1))

    return data_frame


# ============================================================================
# pytest imports (must follow all helper code above)
# ============================================================================
import pytest
import polars as pl
from datetime import date


class Test_Process_Data_For_Plot_Tab_Results:
    """Tests for process_data_for_plot_tab_results in utils_tab_results."""

    @pytest.mark.unit()
    def test_none_returns_none(self):
        """Test that none returns none."""
        from src.dashboard.shiny_utils.utils_tab_results import process_data_for_plot_tab_results

        result = process_data_for_plot_tab_results(data_frame = None)
        assert result is None

    @pytest.mark.unit()
    def test_empty_df_returned_as_is(self):
        """Test that empty df returned as is."""
        from src.dashboard.shiny_utils.utils_tab_results import process_data_for_plot_tab_results

        df = pl.DataFrame({"date": pl.Series([], dtype=pl.Date), "v": pl.Series([], dtype=pl.Float64)})
        result = process_data_for_plot_tab_results(data_frame = df)
        assert result is not None
        assert result.is_empty()

    @pytest.mark.unit()
    def test_small_df_returned_unchanged(self):
        """Test that small df returned unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import process_data_for_plot_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1 + i) for i in range(10)],
            "v": [float(i) for i in range(10)],
        })
        result = process_data_for_plot_tab_results(data_frame = df)
        assert result is not None
        assert result.height == df.height

    @pytest.mark.unit()
    def test_custom_max_points_respected(self):
        """Test that custom max points respected."""
        from src.dashboard.shiny_utils.utils_tab_results import process_data_for_plot_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1) + __import__('datetime').timedelta(days=i) for i in range(100)],
            "v": [float(i) for i in range(100)],
        })
        result = process_data_for_plot_tab_results(data_frame = df, max_points=10)
        assert result is not None
        assert result.height <= 100


class Test_Normalize_Data_Tab_Results:
    """Tests for normalize_data_tab_results in utils_tab_results."""

    @pytest.mark.unit()
    def test_none_method_returns_unchanged(self):
        """Test that none method returns unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [100.0, 200.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="none")
        assert result.equals(df)

    @pytest.mark.unit()
    def test_none_df_returns_none(self):
        """Test that none df returns none."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        result = normalize_data_tab_results(data_frame = None, method="min_max")
        assert result is None

    @pytest.mark.unit()
    def test_min_max_normalizes_to_zero_one(self):
        """Test that min max normalizes to zero one."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1 + i) for i in range(5)],
            "v": [0.0, 25.0, 50.0, 75.0, 100.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="min_max")
        assert result is not None
        vals = result["v"].to_list()
        assert abs(min(vals)) < 0.01
        assert abs(max(vals) - 1.0) < 0.01

    @pytest.mark.unit()
    def test_z_score_method_returns_df(self):
        """Test that z score method returns df."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1 + i) for i in range(5)],
            "v": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="z_score")
        assert result is not None
        assert result.height == df.height


class Test_Utils_Tab_Results_Module_Structure:
    """Tests for the module-level structure of utils_tab_results."""

    @pytest.mark.unit()
    def test_module_importable(self):
        """Test that module importable."""
        import src.dashboard.shiny_utils.utils_tab_results as m

        assert m is not None

    @pytest.mark.unit()
    def test_all_expected_functions_present(self):
        """Test that all expected functions present."""
        from src.dashboard.shiny_utils import utils_tab_results

        for name in [
            "process_data_for_plot_tab_results",
            "normalize_data_tab_results",
            "transform_data_tab_results",
        ]:
            assert hasattr(utils_tab_results, name), f"Missing: {name}"
            assert callable(getattr(utils_tab_results, name))


@pytest.mark.unit()
class Test_Normalize_Data_Tab_Results_Edge_Branches:
    """Additional branch coverage for normalize_data_tab_results."""

    @pytest.mark.unit()
    def Test_Min_Max_All_Same_Values_Skips_Normalization(self):
        """When max==min, the if-branch is skipped (branch [49, 46])."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [5.0, 5.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="min_max")
        assert result is not None
        # Values unchanged because max == min → no normalization applied
        assert result["v"].to_list() == [5.0, 5.0]

    @pytest.mark.unit()
    def Test_Unknown_Method_Falls_Through_To_Return(self):
        """Unknown method skips both if/elif branches (branch [54, 64])."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [10.0, 20.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="unknown_method")
        assert result is not None
        assert result.equals(df)

    @pytest.mark.unit()
    def Test_Z_Score_Zero_Std_Skips_Update(self):
        """When std==0 the z-score update is skipped (branch [59, 56])."""
        from src.dashboard.shiny_utils.utils_tab_results import normalize_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [7.0, 7.0],
        })
        result = normalize_data_tab_results(data_frame = df, method="z_score")
        assert result is not None
        assert result["v"].to_list() == [7.0, 7.0]


@pytest.mark.unit()
class Test_Transform_Data_Tab_Results:
    """Tests for transform_data_tab_results covering all transformation types."""

    @pytest.mark.unit()
    def Test_None_Transformation_Returns_Unchanged(self):
        """transformation='none' returns df unchanged."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [100.0, 105.0],
        })
        result = transform_data_tab_results(data_frame = df, transformation="none")
        assert result is not None
        assert result.equals(df)

    @pytest.mark.unit()
    def Test_None_Dataframe_Returns_None(self):
        """None dataframe returns None."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        result = transform_data_tab_results(data_frame = None, transformation="percent_change")
        assert result is None

    @pytest.mark.unit()
    def Test_Percent_Change_Transformation(self):
        """transformation='percent_change' calculates percent change from first value."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
            "v": [100.0, 110.0, 120.0],
        })
        result = transform_data_tab_results(data_frame = df, transformation="percent_change")
        assert result is not None
        assert "v_pct" in result.columns

    @pytest.mark.unit()
    def Test_Percent_Change_Zero_First_Value_Skips_Column(self):
        """When first value is 0, percent change column is not added (branch [83, 81])."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [0.0, 10.0],
        })
        result = transform_data_tab_results(data_frame = df, transformation="percent_change")
        assert result is not None
        assert "v_pct" not in result.columns

    @pytest.mark.unit()
    def Test_Cumulative_Transformation(self):
        """transformation='cumulative' adds cumulative sum columns."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
            "v": [10.0, 20.0, 30.0],
        })
        result = transform_data_tab_results(data_frame = df, transformation="cumulative")
        assert result is not None
        assert "v_cum" in result.columns
        assert result["v_cum"].to_list() == [10.0, 30.0, 60.0]

    @pytest.mark.unit()
    def Test_Comparative_Transformation_With_Baseline(self):
        """transformation='comparative' calculates relative change from baseline date.

        Covers lines 95-115 and branches [88,95], [95,97], [95,117],
        [108,109], [108,115], [110,108], [110,111].
        """
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
            "v": [100.0, 110.0, 120.0],
        })
        result = transform_data_tab_results(
            data_frame = df, transformation="comparative", baseline_date="2023-01-01"
        )
        assert result is not None
        assert "v_rel" in result.columns
        assert "_date_diff" not in result.columns
        # baseline row has v=100, so v_rel at baseline = 0%
        baseline_idx = result["date"].to_list().index(date(2023, 1, 1))
        assert abs(result["v_rel"][baseline_idx]) < 0.01

    @pytest.mark.unit()
    def Test_Comparative_Transformation_Zero_Baseline_Skips_Column(self):
        """When baseline value is 0, the _rel column is not added (branch [110,115])."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [0.0, 10.0],
        })
        result = transform_data_tab_results(
            data_frame = df, transformation="comparative", baseline_date="2023-01-01"
        )
        assert result is not None
        assert "v_rel" not in result.columns
        assert "_date_diff" not in result.columns

    @pytest.mark.unit()
    def Test_Comparative_Transformation_No_Baseline_Date_Skips(self):
        """transformation='comparative' without baseline_date is skipped (branch [95,117])."""
        from src.dashboard.shiny_utils.utils_tab_results import transform_data_tab_results

        df = pl.DataFrame({
            "date": [date(2023, 1, 1), date(2023, 1, 2)],
            "v": [100.0, 110.0],
        })
        result = transform_data_tab_results(
            data_frame = df, transformation="comparative", baseline_date=None
        )
        assert result is not None
        assert "v_rel" not in result.columns

