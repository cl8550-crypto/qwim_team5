"""Private renderer registration helpers for the client summary subtab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shiny import reactive, render, ui

from src.dashboard.shiny_tab_clients import _subtab_summary_data as summary_data
from src.dashboard.shiny_utils.utils_visuals import (
    create_enhanced_summary_table_multi_column,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


if TYPE_CHECKING:
    import polars as pl



def register_clients_summary_server_outputs(
    *, _input_events: Any, output: Any, reactives_shiny: dict[str, Any]) -> None:
    """Register the client summary renderers and shared reactive updates."""

    @reactive.calc
    def calc_table_summary_clients_assets() -> pl.DataFrame:
        """Return the reactive assets summary dataframe."""
        return summary_data.calc_table_summary_clients_assets(
            reactives_shiny=reactives_shiny,
        )


    @reactive.calc
    def calc_table_summary_clients_personal_info() -> pl.DataFrame:
        """Return the reactive personal-information summary dataframe."""
        return summary_data.calc_table_summary_clients_personal_info(
            reactives_shiny=reactives_shiny,
        )


    @reactive.calc
    def calc_table_summary_clients_goals() -> pl.DataFrame:
        """Return the reactive goals summary dataframe."""
        return summary_data.calc_table_summary_clients_goals(
            reactives_shiny=reactives_shiny,
        )


    @reactive.calc
    def calc_table_summary_clients_income() -> pl.DataFrame:
        """Return the reactive income summary dataframe."""
        return summary_data.calc_table_summary_clients_income(
            reactives_shiny=reactives_shiny,
        )


    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_summary_table_personal_info():
        """Generate personal information summary table using great-tables with reactive dependencies."""
        try:
            reactive.invalidate_later(0.5)
        except RuntimeError:
            pass
        data_Personal_Info_DF = calc_table_summary_clients_personal_info()

        if data_Personal_Info_DF is None:
            error_message = "data_Personal_Info_DF is None from reactive calculation"
            return ui.div(
                ui.div(
                    ui.h5("Personal Info Table Generation Error", class_="text-danger"),
                    ui.p(error_message, class_="text-muted"),
                    ui.p(
                        "Please check that personal information has been entered in the Personal Info tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Information Category</th>
                                <th>Primary client</th>
                                <th>Partner client</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="3" class="text-center text-muted">Error loading personal information data</td></tr>
                        </tbody>
                    </table>
                </div>
                """),
            )

        if data_Personal_Info_DF.height == 0:
            error_message = "data_Personal_Info_DF is empty from reactive calculation"
            return ui.div(
                ui.div(
                    ui.h5("Personal Info Table Generation Error", class_="text-danger"),
                    ui.p(error_message, class_="text-muted"),
                    ui.p(
                        "Please check that personal information has been entered in the Personal Info tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Information Category</th>
                                <th>Primary client</th>
                                <th>Partner client</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="3" class="text-center text-muted">Error loading personal information data</td></tr>
                        </tbody>
                    </table>
                </div>
                """),
            )

        try:
            data_Personal_Info_DF = summary_data.normalize_data_personal_info_summary(
                data_personal_info_df = data_Personal_Info_DF,
            )
        except (ValueError, Exception_Validation_Input):
            return ui.div(
                ui.div(
                    ui.h5("Personal Info Table Generation Error", class_="text-danger"),
                    ui.p(
                        "Primary client column is missing from personal information data.",
                        class_="text-muted",
                    ),
                    ui.p(
                        "Please check that personal information has been entered in the Personal Info tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
            )

        primary_values = data_Personal_Info_DF.select("Client Primary").to_series().to_list()
        partner_values = data_Personal_Info_DF.select("Client Partner").to_series().to_list()
        has_meaningful_data = any(
            value_item not in ["Not Provided", "Not Specified", "0 years", "0"]
            for value_item in primary_values + partner_values
        )

        if not has_meaningful_data:
            return ui.div(
                ui.p(
                    "No personal information has been entered yet. Please visit the Personal Info tab to input values.",
                    class_="text-muted text-center mt-3",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Information Category</th>
                                <th>Primary client</th>
                                <th>Partner client</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Name</td>
                                <td class="text-muted">Not Provided</td>
                                <td class="text-muted">Not Provided</td>
                            </tr>
                            <tr>
                                <td>Current Age</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>Retirement Age</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>Income Starting Age</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>Marital Status</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>Gender</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>Risk Tolerance</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>State</td>
                                <td class="text-muted">Not Specified</td>
                                <td class="text-muted">Not Specified</td>
                            </tr>
                            <tr>
                                <td>ZIP Code</td>
                                <td class="text-muted">Not Provided</td>
                                <td class="text-muted">Not Provided</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """),
                class_="mt-3",
            )

        table_Personal_Info = create_enhanced_summary_table_multi_column(
            dataframe_input=data_Personal_Info_DF,
            table_title="Personal Information Summary",
            table_subtitle="Comprehensive demographic and personal details for both clients",
            table_theme="professional",
            table_width="100%",
        )

        if table_Personal_Info is None:
            def format_value_fallback(*, value: Any) -> Any:
                """Format value for fallback table display."""
                return str(value) if value else "Not Provided"

            info_categories = (
                data_Personal_Info_DF.select("Field Name").to_series().to_list()
            )
            primary_values = data_Personal_Info_DF.select("Client Primary").to_series().to_list()
            partner_values = data_Personal_Info_DF.select("Client Partner").to_series().to_list()

            table_rows = [
                f"""
                    <tr>
                        <td>{format_value_fallback(value = info_categories[idx])}</td>
                        <td>{format_value_fallback(value = primary_values[idx])}</td>
                        <td>{format_value_fallback(value = partner_values[idx])}</td>
                    </tr>
                """
                for idx in range(len(info_categories))
            ]

            return ui.div(
                ui.h5("Personal Information Summary", class_="text-center mb-3"),
                ui.p(
                    "Comprehensive demographic and personal details for both clients",
                    class_="text-muted text-center mb-3",
                ),
                ui.HTML(f"""
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Information Category</th>
                                <th>Primary client</th>
                                <th>Partner client</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(table_rows)}
                        </tbody>
                    </table>
                </div>
                """),
                ui.p(
                    "Note: Using fallback table format due to enhanced table creation issue.",
                    class_="text-muted small mt-2",
                ),
                class_="mt-3",
            )

        return ui.HTML(table_Personal_Info.as_raw_html())


    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_summary_table_assets():
        """Generate financial assets summary table using great-tables with reactive dependencies."""
        try:
            reactive.invalidate_later(0.5)
        except RuntimeError:
            pass
        try:
            data_Assets_DF = calc_table_summary_clients_assets()

            if data_Assets_DF is None:
                raise Exception_Validation_Input("data_Assets_DF is None from reactive calculation")

            if data_Assets_DF.height == 0:
                raise Exception_Validation_Input(
                    "data_Assets_DF is empty from reactive calculation",
                )

            try:
                _currency_cols_assets = [
                    col
                    for col in ["Client Primary", "Client Partner", "Combined Total"]
                    if col in data_Assets_DF.columns
                ]
                Assets_Table = create_enhanced_summary_table_multi_column(
                    dataframe_input=data_Assets_DF,
                    table_title="Financial Assets Summary",
                    table_subtitle="Current asset values organized by tax treatment and client",
                    currency_columns=_currency_cols_assets,
                    table_theme="professional",
                    table_width="100%",
                )

                if Assets_Table is None:
                    raise Exception_Validation_Input(
                        "Failed to create Assets_Table using enhanced function",
                    )

                return ui.HTML(Assets_Table.as_raw_html())

            except Exception as table_error:
                def format_currency_fallback(*, amount: Any) -> str | None:
                    """Format currency for fallback table."""
                    try:
                        return f"${amount:,.0f}" if amount != 0 else "$0"
                    except (ValueError, TypeError):
                        return "$0"

                try:
                    asset_categories = data_Assets_DF.select("Field Name").to_series().to_list()
                    primary_values = data_Assets_DF.select("Client Primary").to_series().to_list()
                    partner_values = data_Assets_DF.select("Client Partner").to_series().to_list()
                    combined_values = data_Assets_DF.select("Combined Total").to_series().to_list()

                    table_rows = []
                    for idx in range(len(asset_categories)):
                        row_class = "table-info fw-bold" if "Total" in asset_categories[idx] else ""
                        table_rows.append(f"""
                            <tr class="{row_class}">
                                <td>{asset_categories[idx]}</td>
                                <td class="text-end">{format_currency_fallback(amount = primary_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = partner_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = combined_values[idx])}</td>
                            </tr>
                        """)

                    return ui.div(
                        ui.h5("Financial Assets Summary", class_="text-center mb-3"),
                        ui.p(
                            "Current asset values organized by tax treatment and client",
                            class_="text-muted text-center mb-3",
                        ),
                        ui.HTML(f"""
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Asset Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join(table_rows)}
                                </tbody>
                            </table>
                        </div>
                        """),
                        class_="mt-3",
                    )

                except Exception as fallback_error:
                    return ui.div(
                        ui.div(
                            ui.h5("Assets Table - Data Processing Error", class_="text-warning"),
                            ui.p(
                                f"Enhanced table error: {table_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                f"Fallback error: {fallback_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                "Please check that asset values have been entered in the Assets tab.",
                                class_="text-info",
                            ),
                            class_="alert alert-warning",
                        ),
                        ui.HTML("""
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Asset Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td colspan="4" class="text-center text-muted">Unable to load assets data</td></tr>
                                </tbody>
                            </table>
                        </div>
                        """),
                    )

        except Exception as exc_error:
            error_message = (
                f"Error generating assets table: {type(exc_error).__name__}: {exc_error!s}"
            )
            return ui.div(
                ui.div(
                    ui.h5("Assets Table Generation Error", class_="text-danger"),
                    ui.p(error_message, class_="text-muted"),
                    ui.p(
                        "Please check that asset values have been entered in the Assets tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Asset Category</th>
                                <th>client Primary</th>
                                <th>client Partner</th>
                                <th>Combined Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="4" class="text-center text-muted">Error loading assets data</td></tr>
                        </tbody>
                    </table>
                </div>
                """),
            )


    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_summary_table_goals():
        """Generate financial goals summary table using great-tables with reactive dependencies."""
        try:
            reactive.invalidate_later(0.5)
        except RuntimeError:
            pass
        try:
            data_Goals_DF = calc_table_summary_clients_goals()

            if data_Goals_DF is None:
                raise Exception_Validation_Input("data_Goals_DF is None from reactive calculation")

            if data_Goals_DF.height == 0:
                raise Exception_Validation_Input("data_Goals_DF is empty from reactive calculation")

            try:
                _currency_cols_goals = [
                    col
                    for col in ["Client Primary", "Client Partner", "Combined Total"]
                    if col in data_Goals_DF.columns
                ]
                table_Goals = create_enhanced_summary_table_multi_column(
                    dataframe_input=data_Goals_DF,
                    table_title="Financial Goals Summary",
                    table_subtitle="Annual goal targets organized by priority level and importance",
                    currency_columns=_currency_cols_goals,
                    table_theme="professional",
                    table_width="100%",
                )

                if table_Goals is None:
                    raise Exception_Validation_Input(
                        "Failed to create table_Goals using enhanced function",
                    )

                return ui.HTML(table_Goals.as_raw_html())

            except Exception as table_error:
                def format_currency_fallback(*, amount: Any) -> str | None:
                    """Format currency for fallback table."""
                    try:
                        return f"${amount:,.0f}" if amount != 0 else "$0"
                    except (ValueError, TypeError):
                        return "$0"

                try:
                    goal_categories = data_Goals_DF.select("Field Name").to_series().to_list()
                    primary_values = data_Goals_DF.select("Client Primary").to_series().to_list()
                    partner_values = data_Goals_DF.select("Client Partner").to_series().to_list()
                    combined_values = data_Goals_DF.select("Combined Total").to_series().to_list()

                    table_rows = []
                    for idx in range(len(goal_categories)):
                        row_class = "table-info fw-bold" if "Total" in goal_categories[idx] else ""
                        table_rows.append(f"""
                            <tr class="{row_class}">
                                <td>{goal_categories[idx]}</td>
                                <td class="text-end">{format_currency_fallback(amount = primary_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = partner_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = combined_values[idx])}</td>
                            </tr>
                        """)

                    return ui.div(
                        ui.h5("Financial Goals Summary", class_="text-center mb-3"),
                        ui.p(
                            "Annual goal targets organized by priority level and importance",
                            class_="text-muted text-center mb-3",
                        ),
                        ui.HTML(f"""
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Goal Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join(table_rows)}
                                </tbody>
                            </table>
                        </div>
                        """),
                        class_="mt-3",
                    )

                except Exception as fallback_error:
                    return ui.div(
                        ui.div(
                            ui.h5("Goals Table - Data Processing Error", class_="text-warning"),
                            ui.p(
                                f"Enhanced table error: {table_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                f"Fallback error: {fallback_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                "Please check that goal values have been entered in the Goals tab.",
                                class_="text-info",
                            ),
                            class_="alert alert-warning",
                        ),
                        ui.HTML("""
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Goal Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td colspan="4" class="text-center text-muted">Unable to load goals data</td></tr>
                                </tbody>
                            </table>
                        </div>
                        """),
                    )

        except Exception as exc_error:
            error_message = (
                f"Error generating goals table: {type(exc_error).__name__}: {exc_error!s}"
            )
            return ui.div(
                ui.div(
                    ui.h5("Goals Table Generation Error", class_="text-danger"),
                    ui.p(error_message, class_="text-muted"),
                    ui.p(
                        "Please check that goal values have been entered in the Goals tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Goal Category</th>
                                <th>client Primary</th>
                                <th>client Partner</th>
                                <th>Combined Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="4" class="text-center text-muted">Error loading goals data</td></tr>
                        </tbody>
                    </table>
                </div>
                """),
            )


    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_summary_table_income():
        """Generate income sources summary table using great-tables with reactive dependencies."""
        try:
            reactive.invalidate_later(0.5)
        except RuntimeError:
            pass
        try:
            data_Income_DF = calc_table_summary_clients_income()

            if data_Income_DF is None:
                raise Exception_Validation_Input("data_Income_DF is None from reactive calculation")

            if data_Income_DF.height == 0:
                raise Exception_Validation_Input(
                    "data_Income_DF is empty from reactive calculation",
                )

            try:
                _currency_cols_income = [
                    col
                    for col in ["Client Primary", "Client Partner", "Combined Total"]
                    if col in data_Income_DF.columns
                ]
                Income_Table = create_enhanced_summary_table_multi_column(
                    dataframe_input=data_Income_DF,
                    table_title="Income Sources Summary",
                    table_subtitle="Annual income projections from all sources for retirement planning",
                    currency_columns=_currency_cols_income,
                    table_theme="professional",
                    table_width="100%",
                )

                if Income_Table is None:
                    raise Exception_Validation_Input(
                        "Failed to create Income_Table using enhanced function",
                    )

                return ui.HTML(Income_Table.as_raw_html())

            except Exception as table_error:
                def format_currency_fallback(*, amount: Any) -> str | None:
                    """Format currency for fallback table."""
                    try:
                        return f"${amount:,.0f}" if amount != 0 else "$0"
                    except (ValueError, TypeError):
                        return "$0"

                try:
                    income_categories = (
                        data_Income_DF.select("Field Name").to_series().to_list()
                    )
                    primary_values = data_Income_DF.select("Client Primary").to_series().to_list()
                    partner_values = data_Income_DF.select("Client Partner").to_series().to_list()
                    combined_values = data_Income_DF.select("Combined Total").to_series().to_list()

                    table_rows = []
                    for idx in range(len(income_categories)):
                        row_class = (
                            "table-info fw-bold" if "Total" in income_categories[idx] else ""
                        )
                        table_rows.append(f"""
                            <tr class="{row_class}">
                                <td>{income_categories[idx]}</td>
                                <td class="text-end">{format_currency_fallback(amount = primary_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = partner_values[idx])}</td>
                                <td class="text-end">{format_currency_fallback(amount = combined_values[idx])}</td>
                            </tr>
                        """)

                    return ui.div(
                        ui.h5("Income Sources Summary", class_="text-center mb-3"),
                        ui.p(
                            "Annual income projections from all sources for retirement planning",
                            class_="text-muted text-center mb-3",
                        ),
                        ui.HTML(f"""
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Income Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join(table_rows)}
                                </tbody>
                            </table>
                        </div>
                        """),
                        class_="mt-3",
                    )

                except Exception as fallback_error:
                    return ui.div(
                        ui.div(
                            ui.h5("Income Table - Data Processing Error", class_="text-warning"),
                            ui.p(
                                f"Enhanced table error: {table_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                f"Fallback error: {fallback_error!s}",
                                class_="text-muted small",
                            ),
                            ui.p(
                                "Please check that income values have been entered in the Income tab.",
                                class_="text-info",
                            ),
                            class_="alert alert-warning",
                        ),
                        ui.HTML("""
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Income Category</th>
                                        <th>client Primary</th>
                                        <th>client Partner</th>
                                        <th>Combined Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td colspan="4" class="text-center text-muted">Unable to load income data</td></tr>
                                </tbody>
                            </table>
                        </div>
                        """),
                    )

        except Exception as exc_error:
            error_message = (
                f"Error generating income table: {type(exc_error).__name__}: {exc_error!s}"
            )
            return ui.div(
                ui.div(
                    ui.h5("Income Table Generation Error", class_="text-danger"),
                    ui.p(error_message, class_="text-muted"),
                    ui.p(
                        "Please check that income values have been entered in the Income tab.",
                        class_="text-info",
                    ),
                    class_="alert alert-warning",
                ),
                ui.HTML("""
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Income Category</th>
                                <th>client Primary</th>
                                <th>client Partner</th>
                                <th>Combined Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="4" class="text-center text-muted">Error loading income data</td></tr>
                        </tbody>
                    </table>
                </div>
                """),
            )


    @reactive.effect
    def observer_update_shared_reactives_shiny_summary() -> None:
        """Update shared reactive values for cross-module communication."""
        data_Assets_DF = calc_table_summary_clients_assets()
        table_Assets = create_enhanced_summary_table_multi_column(
            dataframe_input=data_Assets_DF,
            table_title="Financial Assets Summary",
            table_subtitle="Current asset values organized by tax treatment and client",
            currency_columns=[
                col
                for col in ["Client Primary", "Client Partner", "Combined Total"]
                if col in data_Assets_DF.columns
            ],
            table_theme="professional",
            table_width="100%",
        )

        data_Income_DF = calc_table_summary_clients_income()
        table_Income = create_enhanced_summary_table_multi_column(
            dataframe_input=data_Income_DF,
            table_title="Income Sources Summary",
            table_subtitle="Annual income projections from all sources for retirement planning",
            currency_columns=[
                col
                for col in ["Client Primary", "Client Partner", "Combined Total"]
                if col in data_Income_DF.columns
            ],
            table_theme="professional",
            table_width="100%",
        )

        data_Personal_Info_DF = calc_table_summary_clients_personal_info()
        table_Personal_Info = create_enhanced_summary_table_multi_column(
            dataframe_input=data_Personal_Info_DF,
            table_title="Personal Information Summary",
            table_subtitle="Comprehensive demographic and personal details for both clients",
            table_theme="professional",
            table_width="100%",
        )

        data_Goals_DF = calc_table_summary_clients_goals()
        table_Goals = create_enhanced_summary_table_multi_column(
            dataframe_input=data_Goals_DF,
            table_title="Financial Goals Summary",
            table_subtitle="Annual goal targets organized by priority level and importance",
            currency_columns=[
                col
                for col in ["Client Primary", "Client Partner", "Combined Total"]
                if col in data_Goals_DF.columns
            ],
            table_theme="professional",
            table_width="100%",
        )

        if reactives_shiny and isinstance(reactives_shiny, dict):
            visual_objects_category = reactives_shiny.get("Visual_Objects_Shiny")
            inner_variables_category = reactives_shiny.get("Inner_Variables_Shiny")

            if visual_objects_category and isinstance(visual_objects_category, dict):
                visual_objects_mapping = {
                    "Table_Assets": table_Assets,
                    "Table_Personal_Info": table_Personal_Info,
                    "Table_Goals": table_Goals,
                    "Table_Income": table_Income,
                }

                for reactive_key, current_value in visual_objects_mapping.items():
                    if reactive_key in visual_objects_category:
                        reactive_var = visual_objects_category[reactive_key]
                        if reactive_var is not None and hasattr(reactive_var, "set"):
                            reactive_var.set(current_value)

            if inner_variables_category and isinstance(inner_variables_category, dict):
                inner_variables_mapping = {
                    "Data_Assets_DF": data_Assets_DF,
                    "Data_Personal_Info_DF": data_Personal_Info_DF,
                    "Data_Goals_DF": data_Goals_DF,
                    "Data_Income_DF": data_Income_DF,
                }

                for reactive_key, current_value in inner_variables_mapping.items():
                    if reactive_key in inner_variables_category:
                        reactive_var = inner_variables_category[reactive_key]
                        if reactive_var is not None and hasattr(reactive_var, "set"):
                            reactive_var.set(current_value)
