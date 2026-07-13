"""Private summary-table helpers for dashboard visuals."""

from __future__ import annotations

import polars as pl

from great_tables import GT, loc, md, style

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)


def create_enhanced_summary_table_multi_column_impl_QWIM(
    *, dataframe_input: pl.DataFrame, table_title: str = "Summary Table", table_subtitle: str = "", currency_columns: list[str] | None = None, percentage_columns: list[str] | None = None, table_theme: str = "professional", table_width: str = "100%") -> GT:
    """Create a formatted great-tables summary table for multi-column data."""
    if dataframe_input is None:
        raise Exception_Validation_Input("Dataframe input cannot be None")

    if not isinstance(dataframe_input, pl.DataFrame):
        raise TypeError("Input must be a polars DataFrame")

    if dataframe_input.is_empty():
        raise Exception_Validation_Input("Dataframe cannot be empty")

    try:
        pandas_dataframe = dataframe_input.to_pandas()
        table_gt = GT(pandas_dataframe)

        if table_title:
            table_gt = table_gt.tab_header(
                title=md(f"**{table_title}**"),
                subtitle=md(table_subtitle) if table_subtitle else None,
            )

        if currency_columns:
            for currency_column in currency_columns:
                if currency_column in pandas_dataframe.columns:
                    table_gt = table_gt.fmt_currency(
                        columns=[currency_column],
                        currency="USD",
                        decimals=2,
                    )

        if percentage_columns:
            for percentage_column in percentage_columns:
                if percentage_column in pandas_dataframe.columns:
                    table_gt = table_gt.fmt_percent(
                        columns=[percentage_column],
                        decimals=1,
                    )

        if table_theme == "professional":
            table_gt = table_gt.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#f8f9fa",
                heading_title_font_size="18px",
                column_labels_background_color="#e9ecef",
            )
            table_gt = table_gt.tab_style(
                style=style.fill(color="#f8f9fa"),
                locations=loc.body(columns=[pandas_dataframe.columns[0]]),
            ).tab_style(
                style=style.text(weight="bold"),
                locations=loc.body(columns=[pandas_dataframe.columns[0]]),
            )
        elif table_theme == "minimal":
            table_gt = table_gt.tab_options(
                table_width=table_width,
                table_font_size="13px",
            )
        elif table_theme == "enhanced":
            table_gt = table_gt.tab_options(
                table_width=table_width,
                table_font_size="14px",
                heading_background_color="#007bff",
                heading_title_font_size="20px",
                column_labels_background_color="#6c757d",
            )

        return table_gt

    except Exception as exc_error:  # pragma: no cover
        raise Exception_Configuration(
            f"Error creating enhanced summary table: {exc_error!s}",
        ) from exc_error