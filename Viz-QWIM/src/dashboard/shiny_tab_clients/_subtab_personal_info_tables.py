from __future__ import annotations

from typing import Any, Callable

import polars as pl

from shiny import ui

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


STATE_CHOICES_QWIM = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}


def render_personal_info_table_main_impl_QWIM(
    *, dataframe_provider: Callable[[], pl.DataFrame], table_factory: Any, logger: Any) -> Any:
    """Render the main personal information summary table with fallbacks."""
    try:
        data_personal_info_df = dataframe_provider()
        if data_personal_info_df is None:
            raise Exception_Validation_Input(
                "data_Personal_Info_DF is None from reactive calculation",
            )
        if data_personal_info_df.height == 0:
            raise Exception_Validation_Input(
                "data_Personal_Info_DF is empty from reactive calculation",
            )

        try:
            logger.debug("Creating enhanced table...")
            table_personal_info = table_factory(
                dataframe_input=data_personal_info_df,
                table_title="Personal Information Summary",
                table_subtitle="Comprehensive demographic and personal details for both clients",
                table_theme="professional",
                table_width="100%",
            )
            if table_personal_info is None:
                logger.warning("Enhanced table creation returned None")
                raise Exception_Validation_Input(
                    "Failed to create table_Personal_Info using enhanced function",
                )

            logger.debug(
                "Enhanced table created successfully, type: %s",
                type(table_personal_info),
            )
            table_html = table_personal_info.as_raw_html()
            logger.debug("HTML length: %d", len(table_html))
            return ui.div(
                ui.HTML(table_html),
                class_="table-container mt-3",
                style="width: 100%; overflow-x: auto;",
            )
        except (TypeError, ValueError, AttributeError) as table_error:
            logger.warning("Enhanced table creation failed: %s", table_error)

            def _format_value_fallback(*, value: Any) -> str:
                try:
                    return str(value) if value else "Not provided"
                except (ValueError, TypeError):
                    return "Not provided"

            try:
                logger.debug("Creating fallback table...")
                info_categories = (
                    data_personal_info_df.select("Information_Category").to_series().to_list()
                )
                primary_values = (
                    data_personal_info_df.select("client_Primary").to_series().to_list()
                )
                partner_values = (
                    data_personal_info_df.select("client_Partner").to_series().to_list()
                )
                logger.debug(
                    "Categories: %d, Primary: %d, Partner: %d",
                    len(info_categories),
                    len(primary_values),
                    len(partner_values),
                )

                table_rows = [
                    f"""
                        <tr>
                            <td class=\"text-start\">{_format_value_fallback(value = info_categories[idx])}</td>
                            <td class=\"text-center\">{_format_value_fallback(value = primary_values[idx])}</td>
                            <td class=\"text-center\">{_format_value_fallback(value = partner_values[idx])}</td>
                        </tr>
                    """
                    for idx in range(len(info_categories))
                ]
                logger.debug("Fallback table created successfully")
                return ui.div(
                    ui.h5("Personal Information Summary", class_="text-center mb-3"),
                    ui.p(
                        "Comprehensive demographic and personal details for both clients",
                        class_="text-muted text-center mb-3",
                    ),
                    ui.div(
                        ui.HTML(
                            f"""
                            <div class=\"table-responsive\">
                                <table class=\"table table-striped table-hover table-bordered\">
                                    <thead class=\"table-dark\">
                                        <tr>
                                            <th class=\"text-center\">Information Category</th>
                                            <th class=\"text-center\">client Primary</th>
                                            <th class=\"text-center\">client Partner</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {"".join(table_rows)}
                                    </tbody>
                                </table>
                            </div>
                            """,
                        ),
                        style="width: 100%; overflow-x: auto;",
                    ),
                    class_="mt-3",
                )
            except (TypeError, ValueError, AttributeError, KeyError) as fallback_error:
                logger.warning("Fallback table creation failed: %s", fallback_error)
                return ui.div(
                    ui.div(
                        ui.h5(
                            "Personal Info Table - Data Processing Error",
                            class_="text-warning",
                        ),
                        ui.p(
                            f"Enhanced table error: {table_error!s}",
                            class_="text-muted small",
                        ),
                        ui.p(
                            f"Fallback error: {fallback_error!s}",
                            class_="text-muted small",
                        ),
                        ui.p(
                            "Please check that personal information has been entered in the Personal Info tab.",
                            class_="text-info",
                        ),
                        class_="alert alert-warning",
                    ),
                    ui.div(
                        ui.HTML(
                            """
                            <div class="table-responsive">
                                <table class="table table-striped table-bordered">
                                    <thead class="table-dark">
                                        <tr>
                                            <th class="text-center">Information Category</th>
                                            <th class="text-center">client Primary</th>
                                            <th class="text-center">client Partner</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr><td class="text-start">Name</td><td class="text-center">Anne Smith</td><td class="text-center">William Smith</td></tr>
                                        <tr><td class="text-start">Current Age</td><td class="text-center">60 years</td><td class="text-center">35 years</td></tr>
                                        <tr><td class="text-start">Retirement Age</td><td class="text-center">65 years</td><td class="text-center">65 years</td></tr>
                                        <tr><td class="text-start">Income Start Age</td><td class="text-center">65 years</td><td class="text-center">65 years</td></tr>
                                        <tr><td class="text-start">Risk Tolerance</td><td class="text-center">Moderate</td><td class="text-center">Moderate</td></tr>
                                        <tr><td class="text-start">Gender</td><td class="text-center">Female</td><td class="text-center">Male</td></tr>
                                        <tr><td class="text-start">Marital Status</td><td class="text-center">Married</td><td class="text-center">Married</td></tr>
                                        <tr><td class="text-start">State</td><td class="text-center">Not specified</td><td class="text-center">Not specified</td></tr>
                                        <tr><td class="text-start">ZIP Code</td><td class="text-center">12345</td><td class="text-center">12345</td></tr>
                                    </tbody>
                                </table>
                            </div>
                            """,
                        ),
                        style="width: 100%; overflow-x: auto;",
                    ),
                )
    except (TypeError, ValueError, AttributeError) as exc_error:
        logger.opt(exception=True).error(
            "Major error in table generation: {}",
            exc_error,
        )
        error_message = (
            f"Error generating personal info table: {type(exc_error).__name__}: {exc_error!s}"
        )
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
            ui.div(
                ui.HTML(
                    """
                    <div class="table-responsive">
                        <table class="table table-striped table-bordered">
                            <thead class="table-dark">
                                <tr>
                                    <th class="text-center">Information Category</th>
                                    <th class="text-center">client Primary</th>
                                    <th class="text-center">client Partner</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td colspan="3" class="text-center text-muted">Error loading personal information data</td></tr>
                            </tbody>
                        </table>
                    </div>
                    """,
                ),
                style="width: 100%; overflow-x: auto;",
            ),
        )


def render_personal_info_table_test_impl_QWIM(*, logger: Any) -> Any:
    """Render the personal-info output test table."""
    logger.debug("Personal Info test table function called")
    try:
        test_content = ui.div(
            ui.div(
                ui.h5("Test Table - Personal Info Subtab", class_="text-primary mb-3"),
                ui.p(
                    "This is a test table to verify output rendering functionality.",
                    class_="text-muted mb-3",
                ),
                class_="text-center",
            ),
            ui.div(
                ui.HTML(
                    """
                    <div class="table-responsive">
                        <table class="table table-striped table-hover table-bordered">
                            <thead class="table-dark">
                                <tr>
                                    <th class="text-center">Test Category</th>
                                    <th class="text-center">Test Value</th>
                                    <th class="text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="text-start">Output Function</td>
                                    <td class="text-center">Working</td>
                                    <td class="text-center"><span class="badge bg-success">&#10003; Active</span></td>
                                </tr>
                                <tr>
                                    <td class="text-start">UI Rendering</td>
                                    <td class="text-center">Functional</td>
                                    <td class="text-center"><span class="badge bg-success">&#10003; Active</span></td>
                                </tr>
                                <tr>
                                    <td class="text-start">Module Integration</td>
                                    <td class="text-center">Connected</td>
                                    <td class="text-center"><span class="badge bg-success">&#10003; Active</span></td>
                                </tr>
                                <tr>
                                    <td class="text-start">Personal Info Subtab</td>
                                    <td class="text-center">Operational</td>
                                    <td class="text-center"><span class="badge bg-info">&#8505; Ready</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    """,
                ),
                class_="mt-3",
            ),
            ui.div(
                ui.p(
                    "If you can see this content, the output function is working correctly.",
                    class_="text-success small text-center mt-3",
                ),
                ui.p(
                    "Module: subtab_clients_personal_info | Function: output_table_test",
                    class_="text-muted small text-center",
                ),
                class_="border-top pt-2 mt-3",
            ),
            class_="test-table-container p-3",
            style="background-color: #f8f9fa; border-radius: 0.375rem; border: 1px solid #dee2e6;",
        )
        logger.debug("Test table content created successfully")
        return test_content
    except (TypeError, ValueError, AttributeError) as exc_error:
        logger.warning("Error creating test table content: %s", exc_error)
        return ui.div(
            ui.div(
                ui.h5("Test Table - Error", class_="text-warning"),
                ui.p(f"Error creating test content: {exc_error!s}", class_="text-muted"),
                class_="alert alert-warning text-center",
            ),
            ui.div(
                "Fallback test content - If you see this, the output function is executing but encountered an error.",
                class_="text-center p-3 bg-light border rounded",
            ),
        )