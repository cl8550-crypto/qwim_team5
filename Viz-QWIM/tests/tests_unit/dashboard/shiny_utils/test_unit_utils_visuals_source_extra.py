"""Additional source-facing branch tests for dashboard visual utilities."""

from __future__ import annotations

import datetime as dt

import plotly.graph_objects as go
import polars as pl
import pytest

from great_tables import GT

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


def _portfolio_frame(values: list[float], date_kind: str = "date") -> pl.DataFrame:
    """Build a deterministic Date/Value frame for visual utility tests."""
    base_dates = [dt.date(2024, 1, 1) + dt.timedelta(days=index) for index in range(len(values))]
    if date_kind == "string":
        dates: list[object] = [item.isoformat() for item in base_dates]
    elif date_kind == "datetime":
        dates = [dt.datetime.combine(item, dt.time()) for item in base_dates]
    else:
        dates = base_dates
    return pl.DataFrame({"Date": dates, "Value": values})


@pytest.mark.unit()
class Class_Test_Utils_Visuals_Source_Extra:
    """Cover additional defensive and alternate-format branches."""

    @pytest.mark.unit()
    def Test_Validate_Data_Visuals_Rejects_Boolean_Non_Null_Count(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Selected-series validation should reject boolean non-null counts."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        class _FakeSelection:
            """Mimic a Polars selection whose scalar item resolves to bool."""

            def item(self) -> bool:
                """Return a boolean scalar to exercise the bool-as-number seam."""
                return True

        def _return_bool_count(
            self: pl.DataFrame,
            *_args: object,
            **_kwargs: object,
        ) -> _FakeSelection:
            return _FakeSelection()

        monkeypatch.setattr(pl.DataFrame, "select", _return_bool_count)

        is_valid, message = validate_data_visuals(
            data_frame = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Value": [1.0]}),
            selected_series_list = ["Value"],
        )

        assert is_valid is False
        assert "No valid data" in message

    @pytest.mark.unit()
    def Test_Validate_Data_Visuals_Continues_When_Polars_Select_Fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Selected-series validation should tolerate unexpected Polars failures."""
        from src.dashboard.shiny_utils.utils_visuals import validate_data_visuals

        def _raise_select_error(self: pl.DataFrame, *_args: object, **_kwargs: object) -> pl.DataFrame:
            raise RuntimeError("select failure")

        monkeypatch.setattr(pl.DataFrame, "select", _raise_select_error)

        is_valid, message = validate_data_visuals(
            data_frame = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Value": [1.0]}),
            selected_series_list = ["Value"],
        )

        assert is_valid is False
        assert "No valid data" in message

    @pytest.mark.unit()
    def Test_Create_Error_Figure_Falls_Back_When_Annotation_Fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Plotly annotation failures should return a basic error figure."""
        from src.dashboard.shiny_utils import utils_visuals

        def _raise_annotation_error(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("annotation failure")

        monkeypatch.setattr(go.Figure, "add_annotation", _raise_annotation_error)

        figure = utils_visuals.create_error_figure(message_text = "fallback message")

        assert figure.layout.title.text == "Error: fallback message"
        assert len(figure.layout.annotations) == 0

    @pytest.mark.unit()
    def Test_Create_Error_Figure_Coerces_Non_String_Title_And_Details(self) -> None:
        """Error figure inputs should be string-coerced before rendering."""
        from src.dashboard.shiny_utils.utils_visuals import create_error_figure

        figure = create_error_figure(message_text = "message", title_text=123, details_text=456)  # type: ignore[arg-type]

        assert figure.layout.title.text == "123"
        assert "Details: 456" in [annotation.text for annotation in figure.layout.annotations]

    @pytest.mark.unit()
    def Test_Format_And_Numeric_Conversion_Cover_Failing_Float_Subclass(self) -> None:
        """Float conversion failures should fall back without bubbling exceptions."""
        from src.dashboard.shiny_utils.utils_visuals import (
            format_value_for_display,
            safe_numeric_conversion,
        )

        class FailingFloat(float):
            def __float__(self) -> float:
                raise OverflowError("cannot convert")

        value = FailingFloat(1.25)

        assert format_value_for_display(value_input = value) == str(value)
        assert safe_numeric_conversion(input_value = value) is value

    @pytest.mark.unit()
    def Test_Create_Plot_Portfolios_Comparison_Handles_Zero_Start_Value(self) -> None:
        """A zero initial value should produce the no-valid-series error figure."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        data_frame = _portfolio_frame([0.0, 1.0, 2.0])

        figure = create_plot_portfolios_comparison(
            data_portfolio=data_frame,
            data_benchmark=None,
            period_label=None,
        )

        assert len(figure.data) == 0
        assert "No valid data series" in figure.layout.annotations[0].text

    @pytest.mark.unit()
    def Test_Create_Plot_Portfolios_Comparison_Raises_For_Invalid_Object(self) -> None:
        """Invalid pre-validated inputs should be wrapped in Exception_Configuration."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_portfolios_comparison

        with pytest.raises(Exception_Configuration):
            create_plot_portfolios_comparison(
                data_portfolio={"Date": [], "Value": []},  # type: ignore[arg-type]
                data_benchmark=None,
                period_label="Bad",
            )

    @pytest.mark.unit()
    def Test_Create_Plot_Rolling_Statistics_Covers_No_Data_And_Default_Window(self) -> None:
        """Rolling stats should cover no-data and invalid-window branches."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_rolling_statistics

        no_data_figure = create_plot_rolling_statistics(data_portfolio = None, data_benchmark = None, window_size = 5, period_label = "No Data")
        default_window_figure = create_plot_rolling_statistics(
            data_portfolio=_portfolio_frame([100.0, 101.0, 103.0, 102.0]),
            data_benchmark=None,
            window_size=0,
            period_label=None,
        )
        bool_window_figure = create_plot_rolling_statistics(
            data_portfolio=_portfolio_frame([100.0, 101.0, 103.0, 102.0]),
            data_benchmark=None,
            window_size=True,
            period_label="Boolean Window",
        )

        assert "No portfolio or benchmark data" in no_data_figure.layout.annotations[0].text
        assert "Rolling 30-Day Statistics" in default_window_figure.layout.title.text
        assert "Rolling 30-Day Statistics" in bool_window_figure.layout.title.text

    @pytest.mark.unit()
    def Test_Create_Plot_Rolling_Statistics_Raises_For_Invalid_Object(self) -> None:
        """Invalid rolling-stat input objects should be wrapped consistently."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_rolling_statistics

        with pytest.raises(Exception_Configuration):
            create_plot_rolling_statistics(
                data_portfolio={"Date": [], "Value": []},  # type: ignore[arg-type]
                data_benchmark=None,
                window_size=2,
                period_label="Bad",
            )

    @pytest.mark.unit()
    def Test_Create_Plot_Returns_Distribution_Covers_No_Returns_And_Invalid_Input(self) -> None:
        """Returns distribution should handle one-row and invalid-object branches."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_returns_distribution

        one_row_figure = create_plot_returns_distribution(
            data_portfolio=_portfolio_frame([100.0]),
            data_benchmark=None,
            period_label="One Row",
        )

        assert len(one_row_figure.data) == 0
        assert "No data available" in one_row_figure.layout.title.text

        with pytest.raises(Exception_Configuration):
            create_plot_returns_distribution(
                data_portfolio={"Date": [], "Value": []},  # type: ignore[arg-type]
                data_benchmark=None,
                period_label="Bad",
            )

    @pytest.mark.unit()
    def Test_Create_Plot_Drawdowns_Analysis_Raises_For_Invalid_Object(self) -> None:
        """Invalid drawdown input objects should be wrapped consistently."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_drawdowns_analysis

        with pytest.raises(Exception_Configuration):
            create_plot_drawdowns_analysis(
                data_portfolio={"Date": [], "Value": []},  # type: ignore[arg-type]
                data_benchmark=None,
                period_label="Bad",
            )

    @pytest.mark.unit()
    def Test_Create_Plot_Drawdowns_Analysis_Covers_No_Data_And_Portfolio_Only(self) -> None:
        """Drawdown analysis should cover no-data and portfolio-only branches."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_drawdowns_analysis

        no_data_figure = create_plot_drawdowns_analysis(data_portfolio = None, data_benchmark = None, period_label = "No Data")
        portfolio_figure = create_plot_drawdowns_analysis(
            data_portfolio=_portfolio_frame([100.0, 102.0, 101.0, 105.0]),
            data_benchmark=None,
            period_label=None,
            include_benchmark=False,
        )

        assert "No portfolio or benchmark data" in no_data_figure.layout.annotations[0].text
        assert [trace.name for trace in portfolio_figure.data] == ["Portfolio Drawdowns"]

    @pytest.mark.unit()
    def Test_Calculate_Table_Stats_Basic_Covers_Empty_And_Benchmark_Only(self) -> None:
        """Basic stats should cover empty and benchmark-only data paths."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        empty_table = calculate_table_stats_basic(data_portfolio = pl.DataFrame(), data_benchmark = pl.DataFrame())
        benchmark_table = calculate_table_stats_basic(
            data_portfolio=None,
            data_benchmark=_portfolio_frame([100.0, 101.0, 103.0, 104.0]),
            include_benchmark=True,
        )

        assert empty_table.loc[0, "Metric"] == "No Data"
        assert "Benchmark Daily Mean Return (%)" in benchmark_table["Metric"].to_list()

    @pytest.mark.unit()
    def Test_Calculate_Table_Stats_Basic_Covers_No_Returns_And_Zero_Sharpe(self) -> None:
        """Basic stats should cover no-return and zero-volatility Sharpe branches."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        portfolio_one_row = calculate_table_stats_basic(data_portfolio = _portfolio_frame([100.0]), data_benchmark = None)
        benchmark_one_row = calculate_table_stats_basic(
            data_portfolio = None,
            data_benchmark = _portfolio_frame([100.0]),
            include_benchmark=True,
        )
        constant_returns = calculate_table_stats_basic(
            data_portfolio = _portfolio_frame([100.0, 110.0, 121.0]),
            data_benchmark = _portfolio_frame([100.0, 110.0, 121.0]),
            include_benchmark=True,
        )

        assert portfolio_one_row.loc[0, "Metric"] == "No Data"
        assert benchmark_one_row.loc[0, "Metric"] == "No Data"
        assert "Portfolio Sharpe Ratio" not in constant_returns["Metric"].to_list()
        assert "Benchmark Sharpe Ratio" not in constant_returns["Metric"].to_list()

    @pytest.mark.unit()
    def Test_Calculate_Table_Stats_Basic_Raises_For_Missing_Value_Column(self) -> None:
        """Basic stats should wrap calculation errors from invalid schemas."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_stats_basic

        with pytest.raises(Exception_Configuration):
            calculate_table_stats_basic(
                data_portfolio = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Other": [1.0]}),
                data_benchmark = None,
            )

    @pytest.mark.unit()
    def Test_Calculate_Table_Metrics_Performance_Covers_One_Row_No_Returns(self) -> None:
        """One-row portfolio data should return the N/A no-data table."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_metrics_performance

        table = calculate_table_metrics_performance(data_portfolio = _portfolio_frame([100.0]), data_benchmark = None)

        assert table.loc[0, "Metric"] == "No Data"
        assert table.loc[0, "Value"] == "N/A"

    @pytest.mark.unit()
    def Test_Calculate_Table_Metrics_Performance_Raises_For_Missing_Value_Column(self) -> None:
        """Performance metrics should wrap invalid schema calculation errors."""
        from src.dashboard.shiny_utils.utils_visuals import calculate_table_metrics_performance

        with pytest.raises(Exception_Configuration):
            calculate_table_metrics_performance(
                data_portfolio = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Other": [1.0]}),
                data_benchmark = None,
            )

    @pytest.mark.unit()
    def Test_Create_Plot_Comparison_Portfolios_Covers_String_And_Datetime_Dates(self) -> None:
        """Comparison plots should cover string-date and datetime-date conversions."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_comparison_portfolios

        string_figure = create_plot_comparison_portfolios(
            data_portfolio=_portfolio_frame([100.0, 105.0, 103.0], "string"),
            data_benchmark=None,
            viz_type="pct_change",
            show_diff=True,
            period_label="Strings",
            start_date=dt.date(2024, 1, 1),
            end_date=dt.date(2024, 1, 3),
        )
        datetime_figure = create_plot_comparison_portfolios(
            data_portfolio=None,
            data_benchmark=_portfolio_frame([100.0, 98.0, 101.0], "datetime"),
            viz_type=123,  # type: ignore[arg-type]
            show_diff=False,
            period_label=None,
            start_date=dt.date(2024, 1, 1),
            end_date=dt.date(2024, 1, 3),
        )

        assert [trace.name for trace in string_figure.data] == ["Portfolio"]
        assert [trace.name for trace in datetime_figure.data] == ["Benchmark"]
        assert datetime_figure.layout.yaxis.title.text == "Normalized Value (Base=100)"

    @pytest.mark.unit()
    def Test_Create_Plot_Comparison_Portfolios_Adds_No_Data_Annotation(self) -> None:
        """Invalid Date/Value schemas should yield an annotated empty figure."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_comparison_portfolios

        figure = create_plot_comparison_portfolios(
            data_portfolio=pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Other": [1.0]}),
            data_benchmark=None,
            viz_type="absolute",
            show_diff=False,
            period_label="Invalid",
            start_date=dt.date(2024, 1, 1),
            end_date=dt.date(2024, 1, 1),
        )

        assert len(figure.data) == 0
        assert "No data available" in figure.layout.annotations[0].text

    @pytest.mark.unit()
    def Test_Create_Table_Comparison_Stats_Covers_String_Date_And_One_Row(self) -> None:
        """Comparison stats should cover string dates and len<=1 branches."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_comparison_stats

        table = create_table_comparison_stats(
            data_portfolio=_portfolio_frame([100.0], "string"),
            data_benchmark=_portfolio_frame([100.0, 101.0], "datetime"),
            time_period="five_year",
            start_date=dt.date(2024, 1, 1),
            end_date=dt.date(2024, 1, 2),
        )

        assert isinstance(table, GT)

    @pytest.mark.unit()
    def Test_Create_Table_Summary_Weights_Analysis_Covers_Non_Percentage_And_Invalid_Values(
        self,
    ) -> None:
        """Weights table should cover safe formatting fallbacks and non-percent display."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_summary_weights_analysis

        table = create_table_summary_weights_analysis(
            data_stats = {
                "IVV": {"Latest": None, "Average": "bad", "Min": 0.1, "Max": 0.2, "StdDev": 0.01},
                "AGG": {"Latest": 0.4, "Average": 0.3, "Min": 0.2, "Max": 0.5, "StdDev": 0.02},
                "_period_info": {"period_label": "Unit", "data_points": 2},
            },
            show_pct=False,
        )

        assert isinstance(table, GT)

    @pytest.mark.unit()
    def Test_Create_Table_Summary_Weights_Analysis_Does_Not_Format_Bools_As_Weights(
        self,
    ) -> None:
        """Boolean weight values should stay on the invalid-value display path instead of formatting as percentages."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_summary_weights_analysis

        table = create_table_summary_weights_analysis(
            data_stats = {
                "BOOL": {
                    "Latest": True,
                    "Average": False,
                    "Min": 0.1,
                    "Max": 0.2,
                    "StdDev": 0.01,
                },
                "_period_info": {"period_label": "Bool", "data_points": 1},
            },
            show_pct=True,
        )

        assert table._tbl_data.loc[0, "Latest"] == "-"
        assert table._tbl_data.loc[0, "Average"] == "-"

    @pytest.mark.unit()
    def Test_Create_Enhanced_Summary_Table_Covers_Header_Validation_And_Themes(self) -> None:
        """Enhanced summary tables should validate headers and cover non-enhanced themes."""
        from src.dashboard.shiny_utils.utils_visuals import create_enhanced_summary_table

        data_frame = pl.DataFrame({"Metric": ["A", "B"], "Value": [1.0, 2.0]})

        professional_table = create_enhanced_summary_table(
            dataframe_input = data_frame,
            table_title="Professional",
            table_theme="professional",
        )
        minimal_table = create_enhanced_summary_table(
            dataframe_input = data_frame,
            table_title="Minimal",
            percentage_columns=["Value"],
            table_theme="minimal",
        )
        unknown_theme_table = create_enhanced_summary_table(
            dataframe_input = data_frame,
            table_title="Unknown",
            table_theme="unknown",
        )

        assert isinstance(professional_table, GT)
        assert isinstance(minimal_table, GT)
        assert isinstance(unknown_theme_table, GT)
        with pytest.raises(TypeError):
            create_enhanced_summary_table(dataframe_input = data_frame, column_headers="bad")  # type: ignore[arg-type]
        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table(dataframe_input = data_frame, column_headers=["only one"])

    @pytest.mark.unit()
    def Test_Create_Enhanced_Summary_Table_Multi_Column_Rejects_Invalid_Input(self) -> None:
        """Multi-column enhanced table should reject invalid input types and empty frames."""
        from src.dashboard.shiny_utils.utils_visuals import (
            create_enhanced_summary_table_multi_column,
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table_multi_column(dataframe_input = None)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            create_enhanced_summary_table_multi_column(dataframe_input = {"Metric": ["A"]})  # type: ignore[arg-type]
        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table_multi_column(dataframe_input = pl.DataFrame())

    @pytest.mark.unit()
    def Test_Format_And_Conversion_Cover_Normal_Strings_Na_And_Objects(self) -> None:
        """Formatting helpers should cover normal strings, NA values, and object fallbacks."""
        from src.dashboard.shiny_utils.utils_visuals import (
            format_value_for_display,
            safe_numeric_conversion,
        )

        sentinel = object()

        assert format_value_for_display(value_input = "ready") == "ready"
        assert format_value_for_display(value_input = sentinel) == str(sentinel)
        assert safe_numeric_conversion(input_value = float("nan")) != safe_numeric_conversion(input_value = float("nan"))
        assert safe_numeric_conversion(input_value = sentinel) is sentinel

    @pytest.mark.unit()
    def Test_Prevalidation_False_Flags_Return_Empty_Data_Figures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Plot helpers should honor explicit empty-data validation flags."""
        from src.dashboard.shiny_utils import utils_visuals

        def _empty_validation_flags(**_kwargs: object) -> tuple[bool, bool]:
            return False, False

        monkeypatch.setattr(
            utils_visuals,
            "validate_portfolio_and_benchmark_data_if_not_already_validated",
            _empty_validation_flags,
        )

        data_frame = _portfolio_frame([100.0, 101.0, 102.0])
        start_date = dt.date(2024, 1, 1)
        end_date = dt.date(2024, 1, 3)

        figures = [
            utils_visuals.create_plot_portfolios_comparison(
                data_portfolio = data_frame,
                data_benchmark = None,
                period_label = "Validated",
                data_was_validated=False,
            ),
            utils_visuals.create_plot_rolling_statistics(
                data_portfolio = data_frame,
                data_benchmark = None,
                window_size = 2,
                period_label = "Validated",
                data_was_validated=False,
            ),
            utils_visuals.create_plot_returns_distribution(
                data_portfolio = data_frame,
                data_benchmark = None,
                period_label = "Validated",
                data_was_validated=False,
            ),
            utils_visuals.create_plot_drawdowns_analysis(
                data_portfolio = data_frame,
                data_benchmark = None,
                period_label = "Validated",
                data_was_validated=False,
            ),
            utils_visuals.create_plot_comparison_portfolios(
                data_portfolio = data_frame,
                data_benchmark = None,
                viz_type = "normalized",
                show_diff = False,
                period_label = "Validated",
                start_date = start_date,
                end_date = end_date,
                data_was_validated=False,
            ),
        ]

        assert all("Both portfolio and benchmark" in figure.layout.annotations[0].text for figure in figures)

    @pytest.mark.unit()
    def Test_Portfolio_And_Benchmark_Plots_Cover_Practical_Data_Branches(self) -> None:
        """Plot helpers should cover benchmark, no-return, and full-data branches."""
        from src.dashboard.shiny_utils import utils_visuals

        long_values = [100.0 + index for index in range(40)]
        long_portfolio = _portfolio_frame(long_values)
        long_benchmark = _portfolio_frame([value * 1.01 for value in long_values])
        one_row = _portfolio_frame([100.0])

        comparison = utils_visuals.create_plot_portfolios_comparison(
            data_portfolio=long_portfolio,
            data_benchmark=long_benchmark,
            period_label=123,
        )
        benchmark_zero = utils_visuals.create_plot_portfolios_comparison(
            data_portfolio=None,
            data_benchmark=_portfolio_frame([0.0, 1.0, 2.0]),
            period_label="Zero Benchmark",
        )
        all_null = utils_visuals.create_plot_portfolios_comparison(
            data_portfolio=pl.DataFrame(
                {"Date": [dt.date(2024, 1, 1), dt.date(2024, 1, 2)], "Value": [None, None]},
            ),
            data_benchmark=None,
            period_label="Nulls",
        )
        benchmark_all_null = utils_visuals.create_plot_portfolios_comparison(
            data_portfolio=None,
            data_benchmark=pl.DataFrame(
                {"Date": [dt.date(2024, 1, 1), dt.date(2024, 1, 2)], "Value": [None, None]},
            ),
            period_label="Benchmark Nulls",
        )
        rolling = utils_visuals.create_plot_rolling_statistics(
            data_portfolio = long_portfolio,
            data_benchmark = long_benchmark,
            window_size = 5,
            period_label = "Long",
            include_benchmark=True,
        )
        rolling_benchmark_only = utils_visuals.create_plot_rolling_statistics(
            data_portfolio = None,
            data_benchmark = long_benchmark,
            window_size = 5,
            period_label = "Benchmark Only",
            include_benchmark=True,
        )
        rolling_short_benchmark = utils_visuals.create_plot_rolling_statistics(
            data_portfolio = None,
            data_benchmark = one_row,
            window_size = 5,
            period_label = "Short Benchmark",
            include_benchmark=True,
        )
        returns_none = utils_visuals.create_plot_returns_distribution(data_portfolio = None, data_benchmark = None, period_label = "No Data")
        returns_full = utils_visuals.create_plot_returns_distribution(
            data_portfolio = long_portfolio,
            data_benchmark = long_benchmark,
            period_label = None,
            include_benchmark=True,
        )
        returns_benchmark_only = utils_visuals.create_plot_returns_distribution(
            data_portfolio = None,
            data_benchmark = one_row,
            period_label = "Benchmark Only",
            include_benchmark=True,
        )
        drawdowns = utils_visuals.create_plot_drawdowns_analysis(
            data_portfolio = long_portfolio,
            data_benchmark = long_benchmark,
            period_label = 456,
            include_benchmark=True,
        )
        drawdown_one_row = utils_visuals.create_plot_drawdowns_analysis(
            data_portfolio = one_row,
            data_benchmark = one_row,
            period_label = "One Row",
            include_benchmark=True,
        )
        drawdown_benchmark_only = utils_visuals.create_plot_drawdowns_analysis(
            data_portfolio = None,
            data_benchmark = long_benchmark,
            period_label = "Benchmark Only",
            include_benchmark=True,
        )

        assert [trace.name for trace in comparison.data] == ["Portfolio", "Benchmark"]
        assert "No valid data series" in benchmark_zero.layout.annotations[0].text
        assert "No valid data series" in all_null.layout.annotations[0].text
        assert "No valid data series" in benchmark_all_null.layout.annotations[0].text
        assert [trace.name for trace in rolling.data] == [
            "Portfolio Returns",
            "Portfolio Volatility",
            "Benchmark Returns",
            "Benchmark Volatility",
        ]
        assert [trace.name for trace in rolling_benchmark_only.data] == [
            "Benchmark Returns",
            "Benchmark Volatility",
        ]
        assert len(rolling_short_benchmark.data) == 0
        assert "No portfolio or benchmark data" in returns_none.layout.annotations[0].text
        assert [trace.name for trace in returns_full.data] == ["Portfolio", "Benchmark"]
        assert "No data available" in returns_benchmark_only.layout.title.text
        assert [trace.name for trace in drawdowns.data] == [
            "Portfolio Drawdowns",
            "Benchmark Drawdowns",
        ]
        assert len(drawdown_one_row.data) == 0
        assert [trace.name for trace in drawdown_benchmark_only.data] == ["Benchmark Drawdowns"]

    @pytest.mark.unit()
    def Test_Create_Plot_Comparison_Portfolios_Covers_Date_And_Zero_Variants(self) -> None:
        """Comparison plot variants should cover date coercion and zero-start values."""
        from src.dashboard.shiny_utils.utils_visuals import create_plot_comparison_portfolios

        start_date = dt.date(2024, 1, 1)
        end_date = dt.date(2024, 1, 3)
        no_data = create_plot_comparison_portfolios(
            data_portfolio = None,
            data_benchmark = None,
            viz_type = "normalized",
            show_diff = False,
            period_label = "No Data",
            start_date = start_date,
            end_date = end_date,
        )
        date_zero = create_plot_comparison_portfolios(
            data_portfolio = _portfolio_frame([0.0, 1.0, 2.0], "date"),
            data_benchmark = _portfolio_frame([0.0, 2.0, 4.0], "string"),
            viz_type = "cum_return",
            show_diff = False,
            period_label = "Date Zero",
            start_date = start_date,
            end_date = end_date,
        )
        normalized_zero = create_plot_comparison_portfolios(
            data_portfolio = _portfolio_frame([0.0, 1.0, 2.0], "date"),
            data_benchmark = _portfolio_frame([0.0, 2.0, 4.0], "string"),
            viz_type = "normalized",
            show_diff = False,
            period_label = "Normalized Zero",
            start_date = start_date,
            end_date = end_date,
        )
        datetime_absolute = create_plot_comparison_portfolios(
            data_portfolio = _portfolio_frame([100.0, 102.0, 105.0], "datetime"),
            data_benchmark = _portfolio_frame([100.0, 101.0, 104.0], "date"),
            viz_type = "absolute",
            show_diff = False,
            period_label = "Datetime Absolute",
            start_date = start_date,
            end_date = end_date,
        )
        clean_empty = create_plot_comparison_portfolios(
            data_portfolio = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Value": [None]}),
            data_benchmark = pl.DataFrame({"Date": [dt.date(2024, 1, 1)], "Value": [None]}),
            viz_type = "normalized",
            show_diff = False,
            period_label = "Empty Clean",
            start_date = start_date,
            end_date = end_date,
        )

        assert "No portfolio or benchmark data" in no_data.layout.annotations[0].text
        assert [trace.name for trace in date_zero.data] == ["Portfolio", "Benchmark"]
        assert [trace.name for trace in normalized_zero.data] == ["Portfolio", "Benchmark"]
        assert [trace.name for trace in datetime_absolute.data] == ["Portfolio", "Benchmark"]
        assert "No data available" in clean_empty.layout.annotations[0].text

    @pytest.mark.unit()
    def Test_Create_Table_Comparison_Stats_Covers_Invalid_And_Alternate_Data(self) -> None:
        """Comparison stats should cover invalid schemas and alternate date/stat paths."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_comparison_stats

        start_date = dt.date(2024, 1, 1)
        end_date = dt.date(2024, 1, 3)
        invalid_table = create_table_comparison_stats(
            data_portfolio = pl.DataFrame({"Date": [start_date], "Other": [1.0]}),
            data_benchmark = None,
            time_period = "invalid",
            start_date = start_date,
            end_date = end_date,
        )
        alternate_table = create_table_comparison_stats(
            data_portfolio = _portfolio_frame([100.0, 110.0, 121.0], "datetime"),
            data_benchmark = _portfolio_frame([0.0, 0.0, 0.0], "string"),
            time_period = None,
            start_date = start_date,
            end_date = end_date,
        )
        custom_table = create_table_comparison_stats(
            data_portfolio = _portfolio_frame([100.0, 105.0, 103.0], "date"),
            data_benchmark = _portfolio_frame([100.0], "date"),
            time_period = "custom",
            start_date = start_date,
            end_date = end_date,
        )
        benchmark_only_table = create_table_comparison_stats(
            data_portfolio = None,
            data_benchmark = _portfolio_frame([100.0, 105.0, 103.0], "date"),
            time_period = "benchmark_only",
            start_date = start_date,
            end_date = end_date,
        )
        zero_portfolio_table = create_table_comparison_stats(
            data_portfolio = _portfolio_frame([0.0, 0.0, 0.0], "datetime"),
            data_benchmark = None,
            time_period = "zero_portfolio",
            start_date = start_date,
            end_date = end_date,
        )
        nulls_table = create_table_comparison_stats(
            data_portfolio = pl.DataFrame({"Date": [start_date], "Value": [None]}),
            data_benchmark = pl.DataFrame({"Date": [start_date], "Value": [None]}),
            time_period = "nulls",
            start_date = start_date,
            end_date = end_date,
        )

        assert isinstance(invalid_table, GT)
        assert isinstance(alternate_table, GT)
        assert isinstance(custom_table, GT)
        assert isinstance(benchmark_only_table, GT)
        assert isinstance(zero_portfolio_table, GT)
        assert isinstance(nulls_table, GT)

    @pytest.mark.unit()
    def Test_Create_Table_Comparison_Stats_Treats_Boolean_Values_As_Invalid(self) -> None:
        """Comparison stats should not coerce boolean value columns into numeric metrics."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_comparison_stats

        table = create_table_comparison_stats(
            data_portfolio = pl.DataFrame(
                {
                    "Date": [dt.date(2024, 1, 1), dt.date(2024, 1, 2)],
                    "Value": [True, False],
                },
            ),
            data_benchmark = pl.DataFrame(
                {
                    "Date": [dt.date(2024, 1, 1), dt.date(2024, 1, 2)],
                    "Value": [False, True],
                },
            ),
            time_period = "bool_values",
            start_date = dt.date(2024, 1, 1),
            end_date = dt.date(2024, 1, 2),
        )

        assert isinstance(table, GT)
        assert list(table._tbl_data["Metric"]) == ["Selected Period", "Date Range", "Data Points"]
        assert table._tbl_data.loc[2, "Portfolio"] == "0"
        assert table._tbl_data.loc[2, "Benchmark"] == "0"
        assert table._tbl_data.loc[2, "Difference"] == "0"

    @pytest.mark.unit()
    def Test_Weights_Table_Covers_Nan_And_Float_Format_Fallbacks(self) -> None:
        """Weights tables should cover NA handling and float-format failures."""
        from src.dashboard.shiny_utils.utils_visuals import create_table_summary_weights_analysis

        class FailingFloat(float):
            def __float__(self) -> float:
                raise OverflowError("cannot format")

        table = create_table_summary_weights_analysis(
            data_stats = {
                "NAN": {
                    "Latest": float("nan"),
                    "Average": 0.1,
                    "Min": 0.0,
                    "Max": 0.2,
                    "StdDev": 0.01,
                },
                "BAD": {
                    "Latest": FailingFloat(1.0),
                    "Average": FailingFloat(1.0),
                    "Min": FailingFloat(1.0),
                    "Max": FailingFloat(1.0),
                    "StdDev": FailingFloat(1.0),
                },
                "_period_info": {"period_label": "Fallbacks", "data_points": 3},
            },
            show_pct=True,
        )

        assert isinstance(table, GT)

    @pytest.mark.unit()
    def Test_Enhanced_Tables_Cover_Input_Validation_And_Formatting_Skips(self) -> None:
        """Enhanced tables should cover validation, optional headers, and skipped format columns."""
        from src.dashboard.shiny_utils.utils_visuals import (
            create_enhanced_summary_table,
            create_enhanced_summary_table_multi_column,
        )

        two_column_frame = pl.DataFrame({"Metric": ["A", "B"], "Value": [1.0, 2.0]})
        multi_column_frame = pl.DataFrame(
            {"Metric": ["A", "B"], "Amount": [10.0, 20.0], "Rate": [0.1, 0.2]},
        )

        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table(dataframe_input = None)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            create_enhanced_summary_table(dataframe_input = {"Metric": ["A"]})  # type: ignore[arg-type]
        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table(dataframe_input = pl.DataFrame())
        with pytest.raises(Exception_Validation_Input):
            create_enhanced_summary_table(dataframe_input = multi_column_frame)

        headerless_table = create_enhanced_summary_table(
            dataframe_input = two_column_frame,
            table_title="",
            column_headers=["Name", "Number"],
            currency_columns=["Missing"],
            percentage_columns=["Missing"],
            show_row_numbers=True,
        )
        professional_multi = create_enhanced_summary_table_multi_column(
            dataframe_input = multi_column_frame,
            table_title="Professional",
            currency_columns=["Amount", "Missing"],
            percentage_columns=["Rate", "Missing"],
            table_theme="professional",
        )
        minimal_multi = create_enhanced_summary_table_multi_column(
            dataframe_input = multi_column_frame,
            table_title="",
            table_theme="minimal",
        )
        enhanced_multi = create_enhanced_summary_table_multi_column(
            dataframe_input = multi_column_frame,
            table_title="Enhanced",
            table_theme="enhanced",
        )
        unknown_multi = create_enhanced_summary_table_multi_column(
            dataframe_input = multi_column_frame,
            table_title="Unknown",
            table_theme="unknown",
        )

        assert isinstance(headerless_table, GT)
        assert isinstance(professional_multi, GT)
        assert isinstance(minimal_multi, GT)
        assert isinstance(enhanced_multi, GT)
        assert isinstance(unknown_multi, GT)