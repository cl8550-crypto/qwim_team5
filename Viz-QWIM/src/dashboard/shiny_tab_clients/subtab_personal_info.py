"""Personal-info subtab UI and server logic with source-visible public hooks."""

from __future__ import annotations

import typing

from typing import Any

import polars as pl

from shiny import module, reactive, render, ui

from src.dashboard.shiny_tab_clients._subtab_personal_info_tables import (
    STATE_CHOICES_QWIM,
    render_personal_info_table_main_impl_QWIM,
    render_personal_info_table_test_impl_QWIM,
)

# Import enhanced UI components following project standards
from src.dashboard.shiny_utils.reactives_shiny import (
    create_reactive_value_safely,
    safe_get_value_from_shiny_input_numeric,
    safe_get_value_from_shiny_input_text,
)
from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
    create_enhanced_card_section,
    create_enhanced_numeric_input,
    create_enhanced_select_input,
    create_enhanced_text_input,
)
from src.dashboard.shiny_utils.utils_reporting import update_single_or_couple_in_reactives
from src.dashboard.shiny_utils.utils_visuals import (
    create_enhanced_summary_table_multi_column,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)


def _coerce_personal_info_worksheet_numeric_int_or_default(
    *, raw_value: Any, default_value: int = 0) -> int:
    """Coerce worksheet personal-info numerics while keeping booleans on the default path."""
    if isinstance(raw_value, bool):
        return default_value

    if raw_value == 0 or raw_value == "":
        return default_value

    return int(float(str(raw_value)))


@module.ui
def subtab_clients_personal_info_ui(  # pragma: no cover
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:
    """Create the personal-info UI for primary and partner client inputs."""
    try:
        # Define common choice dictionaries for select inputs
        State_Choices = STATE_CHOICES_QWIM

        Marital_Status_Choices = {
            "single": "Single",
            "married": "Married",
            "divorced": "Divorced",
            "widowed": "Widowed",
            "separated": "Separated",
            "domestic_partnership": "Domestic Partnership",
        }

        return ui.div(
            # Main section header
            ui.h3("Personal Information", class_="text-center mb-4"),
            # Primary and Partner client sections in responsive layout
            ui.row(
                # Primary client Personal Information Section
                ui.column(
                    6,
                    create_enhanced_card_section(
                        title="Primary client Information",
                        content=[
                            # Include Primary in Analysis checkbox (always True — shown for
                            # informational purposes; styling disables user interaction)
                            ui.div(
                                ui.input_checkbox(
                                    "input_ID_tab_clients_subtab_clients_personal_info_include_primary_in_analysis",
                                    "Include Client Primary in Analysis?",
                                    value=True,
                                ),
                                style="pointer-events: none; opacity: 0.85;",
                            ),
                            # Name Input (combined first and last name)
                            create_enhanced_text_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_name",
                                label_text="Name",
                                default_value="Anne Smith",
                                placeholder_text="Enter full name",
                                # help_text="Full name as it appears on official documents",
                                tooltip_text="Enter full name for client primary",
                                required_field=True,
                                max_length=100,
                            ),
                            # Current Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current",
                                label_text="Current Age",
                                min_value=18,
                                max_value=100,
                                step_size=1,
                                default_value=60,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Current age in years",
                                tooltip_text="Enter current age for client primary",
                                required_field=True,
                                input_width="100%",
                            ),
                            # Retirement Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement",
                                label_text="Retirement Age",
                                min_value=50,
                                max_value=80,
                                step_size=1,
                                default_value=65,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Planned retirement age",
                                tooltip_text="Enter planned retirement age for client primary",
                                required_field=True,
                                input_width="100%",
                            ),
                            # Income Starting Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting",
                                label_text="Income Starting Age",
                                min_value=16,
                                max_value=70,
                                step_size=1,
                                default_value=65,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Age when income started or will start",
                                tooltip_text="Enter age when client primary will start receiving income from retirement portfolio",
                                required_field=True,
                                input_width="100%",
                            ),
                            # Marital Status Select - Updated identifier following coding standards
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_status_marital",
                                label_text="Marital Status",
                                choices=Marital_Status_Choices,
                                default_selection="married",
                                # help_text="Current marital status for tax and legal purposes",
                                tooltip_text="Select current marital status for client primary",
                                required_field=True,
                            ),
                            # Gender Select
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_gender",
                                label_text="Gender",
                                choices={
                                    "male": "Male",
                                    "female": "Female",
                                    "other": "Other",
                                    "prefer_not_to_say": "Prefer Not to Say",
                                },
                                default_selection="female",
                                # help_text="Gender for demographic purposes",
                                tooltip_text="Select gender for client primary",
                                required_field=False,
                            ),
                            # Risk Tolerance Select - Updated identifier following coding standards
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_tolerance_risk",
                                label_text="Risk Tolerance",
                                choices={
                                    "conservative": "Conservative",
                                    "moderate_conservative": "Moderate Conservative",
                                    "moderate": "Moderate",
                                    "moderate_aggressive": "Moderate Aggressive",
                                    "aggressive": "Aggressive",
                                },
                                default_selection="moderate",
                                # help_text="Investment risk tolerance level",
                                tooltip_text="Select risk tolerance for client primary",
                                required_field=True,
                            ),
                            # State Select
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_state",
                                label_text="State",
                                choices=State_Choices,
                                default_selection="",
                                # help_text="State of residence",
                                tooltip_text="Select state of residence for client primary",
                                required_field=True,
                            ),
                            # ZIP Code Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_primary_code_zip",
                                label_text="ZIP Code",
                                min_value=1000,
                                max_value=99999,
                                step_size=1,
                                default_value=12345,
                                currency_format=False,
                                # help_text="5-digit ZIP code",
                                tooltip_text="Enter ZIP code for client primary",
                                required_field=True,
                                input_width="100%",
                            ),
                        ],
                        icon_class="fas fa-user",
                        card_class="h-100 shadow-sm border-primary",
                    ),
                ),
                # Partner client Personal Information Section
                ui.column(
                    6,
                    create_enhanced_card_section(
                        title="Partner client Information",
                        content=[
                            # Include Partner in Analysis checkbox (default False; set to True when
                            # PDF has non-empty partner name)
                            ui.input_checkbox(
                                "input_ID_tab_clients_subtab_clients_personal_info_include_partner_in_analysis",
                                "Include Client Partner in Analysis?",
                                value=False,
                            ),
                            # Name Input (combined first and last name)
                            create_enhanced_text_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_name",
                                label_text="Name",
                                default_value="William Smith",
                                placeholder_text="Enter full name",
                                # help_text="Full name as it appears on official documents",
                                tooltip_text="Enter full name for client partner",
                                required_field=False,
                                max_length=100,
                            ),
                            # Current Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_current",
                                label_text="Current Age",
                                min_value=18,
                                max_value=100,
                                step_size=1,
                                default_value=60,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Current age in years",
                                tooltip_text="Enter current age for client partner",
                                required_field=False,
                                input_width="100%",
                            ),
                            # Retirement Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_retirement",
                                label_text="Retirement Age",
                                min_value=50,
                                max_value=80,
                                step_size=1,
                                default_value=65,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Planned retirement age",
                                tooltip_text="Enter planned retirement age for client partner",
                                required_field=False,
                                input_width="100%",
                            ),
                            # Income Starting Age Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_income_starting",
                                label_text="Income Starting Age",
                                min_value=16,
                                max_value=70,
                                step_size=1,
                                default_value=65,
                                currency_format=False,
                                suffix_symbol=" years",
                                # help_text="Age when income started or will start",
                                tooltip_text="Enter age when client partner will start receiving income from retirement portfolio",
                                required_field=False,
                                input_width="100%",
                            ),
                            # Marital Status Select - Updated identifier following coding standards
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_status_marital",
                                label_text="Marital Status",
                                choices=Marital_Status_Choices,
                                default_selection="married",
                                # help_text="Current marital status for tax and legal purposes",
                                tooltip_text="Select current marital status for client partner",
                                required_field=False,
                            ),
                            # Gender Select
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_gender",
                                label_text="Gender",
                                choices={
                                    "male": "Male",
                                    "female": "Female",
                                    "other": "Other",
                                    "prefer_not_to_say": "Prefer Not to Say",
                                },
                                default_selection="male",  # THE FIX: Changed from "Male" to "male"
                                # help_text="Gender for demographic purposes",
                                tooltip_text="Select gender for client partner",
                                required_field=False,
                            ),
                            # Risk Tolerance Select - Updated identifier following coding standards
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_tolerance_risk",
                                label_text="Risk Tolerance",
                                choices={
                                    "conservative": "Conservative",
                                    "moderate_conservative": "Moderate Conservative",
                                    "moderate": "Moderate",
                                    "moderate_aggressive": "Moderate Aggressive",
                                    "aggressive": "Aggressive",
                                },
                                default_selection="moderate",
                                # help_text="Investment risk tolerance level",
                                tooltip_text="Select risk tolerance for client partner",
                                required_field=False,
                            ),
                            # State Select
                            create_enhanced_select_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_state",
                                label_text="State",
                                choices=State_Choices,
                                default_selection="",
                                # help_text="State of residence",
                                tooltip_text="Select state of residence for client partner",
                                required_field=False,
                            ),
                            # ZIP Code Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_personal_info_client_partner_code_zip",
                                label_text="ZIP Code",
                                min_value=1000,
                                max_value=99999,
                                step_size=1,
                                default_value=12345,
                                currency_format=False,
                                # help_text="5-digit ZIP code",
                                tooltip_text="Enter ZIP code for client partner",
                                required_field=False,
                                input_width="100%",
                            ),
                        ],
                        icon_class="fas fa-user-friends",
                        card_class="h-100 shadow-sm border-info",
                    ),
                ),
            ),
            ui.row(
                ui.column(
                    12,
                    ui.card(
                        ui.card_header(ui.h4("Test table", class_="text-center")),
                        ui.card_body(
                            ui.output_ui(
                                "output_ID_tab_clients_subtab_clients_personal_info_table_test",
                            ),
                            class_="text-center",
                        ),
                    ),
                ),
            ),
            ui.row(
                ui.column(
                    12,
                    ui.card(
                        ui.card_header(
                            ui.h4("client Personal Information Overview", class_="text-center"),
                        ),
                        ui.card_body(
                            ui.div(
                                ui.output_ui(
                                    "output_ID_tab_clients_subtab_clients_personal_info_table_main",
                                ),
                                style="min-height: 300px; border: 1px dashed #ccc; padding: 10px;",
                            ),
                            class_="text-center",
                        ),
                    ),
                ),
            ),
            # Add custom CSS for enhanced styling with reduced vertical spacing
            ui.tags.style("""
            /* Enhanced styling for personal information forms with 50% reduced spacing */
            .form-group {
                margin-bottom: 0.75rem !important;
            }

            .text-primary {
                color: #0d6efd !important;
            }

            .text-info {
                color: #0dcaf0 !important;
            }

            /* Input field styling */
            .form-control {
                border-radius: 0.375rem;
                border: 1px solid #ced4da;
                transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
            }

            .form-control:focus {
                border-color: #86b7fe;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }

            /* Required field indicators */
            .required::after {
                content: " *";
                color: #dc3545;
            }

            /* Section dividers with reduced spacing */
            hr {
                margin: 0.75rem 0;
                opacity: 0.3;
            }

            /* Card styling enhancements */
            .card {
                transition: box-shadow 0.15s ease-in-out;
            }

            .card:hover {
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
            }

            /* Reduce spacing between section headers and inputs by 50% */
            .mb-3 {
                margin-bottom: 0.75rem !important;
            }

            /* Additional spacing reductions for compact layout */
            .card-body {
                padding: 1rem !important;
            }

            h5.mb-3 {
                margin-bottom: 0.5rem !important;
            }
            """),
        )

    except (TypeError, ValueError, AttributeError) as exc_error:
        error_message = f"Unexpected error creating personal info subtab UI: {exc_error}"
        raise Exception_Configuration(error_message) from exc_error


@module.server
def subtab_clients_personal_info_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Run reactive personal-info tables, shared-state updates, and worksheet sync."""

    @reactive.calc
    def calc_table_clients_personal_info_main() -> pl.DataFrame:
        """Generate the main personal-information summary table."""
        # Input validation with early returns following coding standards
        # Access reactive values using proper Shiny input access patterns

        # Primary client personal information
        value_Primary_Name = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_name"],
        )
        value_Primary_Current_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current"],
        )
        value_Primary_Retirement_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement"
            ],
        )
        value_Primary_Income_Start_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting"
            ],
        )
        value_Primary_Risk_Tolerance = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_tolerance_risk"
            ],
        )
        value_Primary_Gender = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_gender"],
        )
        value_Primary_Marital_Status = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_status_marital"
            ],
        )
        value_Primary_State = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_state"],
        )
        value_Primary_Zip_Code = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_code_zip"],
        )

        # Determine whether to include partner column
        try:
            include_partner = bool(
                input[
                    "input_ID_tab_clients_subtab_clients_personal_info_include_partner_in_analysis"
                ](),
            )
        except Exception:
            include_partner = False

        # Partner client personal information — safe getters to avoid ValueError on empty input
        value_Partner_Name = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_name"],
            default_value="",
        )
        value_Partner_Current_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_current"],
            default_value=0.0,
        )
        value_Partner_Retirement_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_retirement"
            ],
            default_value=0.0,
        )
        value_Partner_Income_Start_Age = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_income_starting"
            ],
            default_value=0.0,
        )
        value_Partner_Risk_Tolerance = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_tolerance_risk"
            ],
            default_value="",
        )
        value_Partner_Gender = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_gender"],
            default_value="",
        )
        value_Partner_Marital_Status = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_status_marital"
            ],
            default_value="",
        )
        value_Partner_State = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_state"],
            default_value="",
        )
        value_Partner_Zip_Code = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_code_zip"],
            default_value=0.0,
        )

        # Configuration validation - ensure all numeric values are non-negative
        value_Primary_Current_Age = max(0.0, float(value_Primary_Current_Age or 0.0))
        value_Primary_Retirement_Age = max(0.0, float(value_Primary_Retirement_Age or 0.0))
        value_Primary_Income_Start_Age = max(0.0, float(value_Primary_Income_Start_Age or 0.0))
        value_Primary_Zip_Code = max(0.0, float(value_Primary_Zip_Code or 0.0))
        value_Partner_Current_Age = max(0.0, float(value_Partner_Current_Age or 0.0))
        value_Partner_Retirement_Age = max(0.0, float(value_Partner_Retirement_Age or 0.0))
        value_Partner_Income_Start_Age = max(0.0, float(value_Partner_Income_Start_Age or 0.0))
        value_Partner_Zip_Code = max(0.0, float(value_Partner_Zip_Code or 0.0))

        # Apply defaults for text fields that might be empty (but valid)
        value_Primary_Name = str(value_Primary_Name) if value_Primary_Name else "Not provided"
        value_Primary_Risk_Tolerance = (
            str(value_Primary_Risk_Tolerance) if value_Primary_Risk_Tolerance else "Not specified"
        )
        value_Primary_Gender = (
            str(value_Primary_Gender) if value_Primary_Gender else "Not specified"
        )
        value_Primary_Marital_Status = (
            str(value_Primary_Marital_Status) if value_Primary_Marital_Status else "Not specified"
        )
        value_Primary_State = str(value_Primary_State) if value_Primary_State else "Not specified"

        value_Partner_Name = str(value_Partner_Name) if value_Partner_Name else "Not provided"
        value_Partner_Risk_Tolerance = (
            str(value_Partner_Risk_Tolerance) if value_Partner_Risk_Tolerance else "Not specified"
        )
        value_Partner_Gender = (
            str(value_Partner_Gender) if value_Partner_Gender else "Not specified"
        )
        value_Partner_Marital_Status = (
            str(value_Partner_Marital_Status) if value_Partner_Marital_Status else "Not specified"
        )
        value_Partner_State = str(value_Partner_State) if value_Partner_State else "Not specified"

        # Build the row data
        info_categories = [
            "Name",
            "Current Age",
            "Retirement Age",
            "Income Start Age",
            "Risk Tolerance",
            "Gender",
            "Marital Status",
            "State",
            "ZIP Code",
        ]
        primary_col = [
            str(value_Primary_Name),
            f"{int(value_Primary_Current_Age)} years",
            f"{int(value_Primary_Retirement_Age)} years",
            f"{int(value_Primary_Income_Start_Age)} years",
            str(value_Primary_Risk_Tolerance),
            str(value_Primary_Gender),
            str(value_Primary_Marital_Status),
            str(value_Primary_State),
            str(int(value_Primary_Zip_Code)),
        ]

        if include_partner:
            partner_col = [
                str(value_Partner_Name),
                f"{int(value_Partner_Current_Age)} years",
                f"{int(value_Partner_Retirement_Age)} years",
                f"{int(value_Partner_Income_Start_Age)} years",
                str(value_Partner_Risk_Tolerance),
                str(value_Partner_Gender),
                str(value_Partner_Marital_Status),
                str(value_Partner_State),
                str(int(value_Partner_Zip_Code)),
            ]
            data_Personal_Info_DF = pl.DataFrame(
                {
                    "Information_Category": info_categories,
                    "client_Primary": primary_col,
                    "client_Partner": partner_col,
                },
            )
        else:
            data_Personal_Info_DF = pl.DataFrame(
                {
                    "Information_Category": info_categories,
                    "client_Primary": primary_col,
                },
            )

        # Configuration validation - verify dataframe was created successfully
        if data_Personal_Info_DF is None or data_Personal_Info_DF.height == 0:
            raise Exception_Validation_Input("Failed to create data_Personal_Info_DF dataframe")

        # Return data_Personal_Info_DF with proper reactive dependencies established
        return data_Personal_Info_DF

    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_personal_info_table_main():
        """Render the personal-information summary table."""
        return render_personal_info_table_main_impl_QWIM(
            dataframe_provider = calc_table_clients_personal_info_main,
            table_factory=create_enhanced_summary_table_multi_column,
            logger=_logger,
        )

    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_personal_info_table_test():
        """Render the personal-info output test table."""
        return render_personal_info_table_test_impl_QWIM(logger = _logger)

    @reactive.effect
    def observer_update_shared_reactives_shiny_personal_info() -> None:
        """Mirror current personal-info inputs into shared dashboard reactives."""
        # Get all current personal information values using the safe input access pattern
        # Primary client information
        primary_name = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_name"],
        )
        primary_age_current = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_current"],
        )
        primary_age_retirement = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_retirement"
            ],
        )
        primary_age_income_starting = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_age_income_starting"
            ],
        )
        primary_status_marital = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_status_marital"
            ],
        )
        primary_gender = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_gender"],
        )
        primary_tolerance_risk = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_primary_tolerance_risk"
            ],
        )
        primary_state = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_state"],
        )
        primary_code_zip = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_primary_code_zip"],
        )

        # Partner client information — use safe getters so that an absent/empty
        # partner name (single-client PDF) does not raise a ValueError.
        partner_name = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_name"],
            default_value="",
        )
        partner_age_current = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_current"],
            default_value=0.0,
        )
        partner_age_retirement = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_retirement"
            ],
            default_value=0.0,
        )
        partner_age_income_starting = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_age_income_starting"
            ],
            default_value=0.0,
        )
        partner_status_marital = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_status_marital"
            ],
            default_value="",
        )
        partner_gender = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_gender"],
            default_value="",
        )
        partner_tolerance_risk = safe_get_value_from_shiny_input_text(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_personal_info_client_partner_tolerance_risk"
            ],
            default_value="",
        )
        partner_state = safe_get_value_from_shiny_input_text(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_state"],
            default_value="",
        )
        partner_code_zip = safe_get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_personal_info_client_partner_code_zip"],
            default_value=0.0,
        )

        # When partner name is absent treat as single-client case.
        if not partner_name.strip():
            _logger.debug(
                "Partner name is empty — treating as single-client case and updating"
                " Single_Or_Couple reactive to 'Single'.",
            )
            try:
                update_single_or_couple_in_reactives(reactives_shiny = reactives_shiny, single_or_couple = "Single")
            except Exception:
                pass  # Never raise inside a reactive effect — Single_Or_Couple stays at its current value

        # Update shared reactive values if available
        if reactives_shiny and isinstance(reactives_shiny, dict):
            user_inputs_category = reactives_shiny.get("User_Inputs_Shiny")
            if user_inputs_category and isinstance(user_inputs_category, dict):
                # Store all personal information values in the shared reactive structure
                # Following the naming convention from reactives_shiny.py
                personal_info_mapping = {
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": primary_name,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current": primary_age_current,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement": primary_age_retirement,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting": primary_age_income_starting,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Status_Marital": primary_status_marital,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Gender": primary_gender,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Tolerance_Risk": primary_tolerance_risk,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_State": primary_state,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Code_Zip": primary_code_zip,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name": partner_name,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current": partner_age_current,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement": partner_age_retirement,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting": partner_age_income_starting,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Status_Marital": partner_status_marital,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Gender": partner_gender,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Tolerance_Risk": partner_tolerance_risk,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_State": partner_state,
                    "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Code_Zip": partner_code_zip,
                }

                # Add analysis inclusion flags
                try:
                    include_primary = bool(
                        input[
                            "input_ID_tab_clients_subtab_clients_personal_info_include_primary_in_analysis"
                        ](),
                    )
                except Exception:
                    include_primary = True
                try:
                    include_partner = bool(
                        input[
                            "input_ID_tab_clients_subtab_clients_personal_info_include_partner_in_analysis"
                        ](),
                    )
                except Exception:
                    include_partner = bool(partner_name.strip())
                personal_info_mapping[
                    "Input_Tab_clients_Subtab_clients_Personal_Info_Include_Primary_In_Analysis"
                ] = include_primary
                personal_info_mapping[
                    "Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis"
                ] = include_partner

                # Update each reactive value safely using defensive programming
                for reactive_key, current_value in personal_info_mapping.items():
                    if reactive_key in user_inputs_category:
                        reactive_var = user_inputs_category[reactive_key]
                        if reactive_var is not None and hasattr(reactive_var, "set"):
                            reactive_var.set(current_value)

    # -----------------------------------------------------------------------
    # Populate from uploaded worksheet PDF
    # -----------------------------------------------------------------------
    # Using @reactive.poll because @reactive.effect inside @module.server
    # does NOT re-execute when reactive.Value changes.  The poll checks
    # Extracted_Worksheet_Data every 0.5 s and triggers the downstream
    # effect when the data changes.
    # -----------------------------------------------------------------------

    def _poll_extracted_worksheet_for_personal_info():
        """Read Extracted_Worksheet_Data for the Personal Info subtab."""
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return None
        try:
            return rv_data.get()
        except Exception:
            return None

    @reactive.poll(_poll_extracted_worksheet_for_personal_info, interval_secs=0.5)
    def _poll_personal_info_data():
        """Reactive calc that re-evaluates when Extracted_Worksheet_Data changes."""
        return _poll_extracted_worksheet_for_personal_info()

    @reactive.effect
    def observer_populate_personal_info_from_worksheet() -> None:  # pragma: no cover
        """Populate personal-info inputs from extracted worksheet PDF data.

        Uses :func:`map_personal_info_worksheet_to_inputs` for pure mapping
        logic; this observer only dispatches ``ui.update_*`` calls.
        """
        data = _poll_personal_info_data()
        _logger.warning(
            "personal_info_populate: FIRED | data_is_dict=%s",
            isinstance(data, dict),
        )
        if not isinstance(data, dict):
            return
        section = data.get("Personal_Info", {})
        if not isinstance(section, dict):
            _logger.warning("personal_info_populate: Personal_Info section missing")
            return

        _logger.warning(
            "personal_info_populate: processing | section keys=%s",
            list(section.keys()),
        )

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            _ID_INCLUDE_PARTNER,
            map_personal_info_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_personal_info_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            _logger.warning(
                "personal_info_populate: %s mapped count=%s",
                client_role,
                len(mapped),
            )
            for input_id, value in mapped.items():
                if input_id == _ID_INCLUDE_PARTNER:
                    ui.update_checkbox(input_id, value = bool(value))
                elif isinstance(value, bool):
                    ui.update_checkbox(input_id, value = value)
                elif isinstance(value, int | float) and value is not None:
                    ui.update_numeric(input_id, value = int(value))
                elif value is None:
                    ui.update_numeric(input_id, value = 0)
                elif isinstance(value, str) and input_id.endswith("_name"):
                    ui.update_text(input_id, value = value)
                elif isinstance(value, str):
                    ui.update_select(input_id, selected = value)

        _logger.warning(
            "Personal Info inputs populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "personal_info"},
        )

    # ------------------------------------------------------------------
    # Deferred populate — re-runs when the subtab becomes visible so
    # that ui.update_* calls are not lost for widgets that were not in
    # the DOM at upload time.
    # ------------------------------------------------------------------
    @reactive.effect
    def observer_deferred_populate_personal_info() -> None:  # pragma: no cover
        """Re-populate personal-info inputs when the subtab becomes visible.

        Depends on ``Extracted_Worksheet_Data`` so it fires whenever
        the data changes, and also on the trigger counter so it fires
        when the user switches to this subtab after upload.
        """
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return
        data = rv_data.get()
        if not isinstance(data, dict):
            return
        section = data.get("Personal_Info", {})
        if not isinstance(section, dict):
            return

        # Force re-execution when the trigger counter changes
        triggers = reactives_shiny.get("Triggers_Shiny", {})
        trigger_rv = triggers.get("Trigger_Populate_From_Worksheet")
        if trigger_rv is not None:
            trigger_rv.get()  # establish reactive dependency

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            _ID_INCLUDE_PARTNER,
            map_personal_info_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_personal_info_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            for input_id, value in mapped.items():
                if input_id == _ID_INCLUDE_PARTNER:
                    ui.update_checkbox(input_id, value = bool(value))
                elif isinstance(value, bool):
                    ui.update_checkbox(input_id, value = value)
                elif isinstance(value, int | float) and value is not None:
                    ui.update_numeric(input_id, value = int(value))
                elif value is None:
                    ui.update_numeric(input_id, value = 0)
                elif isinstance(value, str) and input_id.endswith("_name"):
                    ui.update_text(input_id, value = value)
                elif isinstance(value, str):
                    ui.update_select(input_id, selected = value)

        _logger.info(
            "Personal Info inputs deferred-populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "personal_info", "deferred": True},
        )
