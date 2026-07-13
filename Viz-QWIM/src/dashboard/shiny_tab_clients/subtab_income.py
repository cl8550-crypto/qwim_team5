"""Income subtab UI and server logic with source-visible public Shiny hooks."""

from __future__ import annotations

import typing

from typing import Any

import polars as pl

from shiny import module, reactive, render, ui

# Import enhanced UI components following project standards
from src.dashboard.shiny_utils.reactives_shiny import (
    create_reactive_value_safely,
    get_value_from_shiny_input_numeric,
)
from src.dashboard.shiny_utils.utils_enhanced_formatting import (
    extract_numeric_from_currency_string,
    format_currency_value,
)
from src.dashboard.shiny_utils.utils_enhanced_ui_components import (
    ComponentVariant,
    create_enhanced_card_section,
    create_enhanced_numeric_input,
    create_enhanced_summary_display,
)
from src.dashboard.shiny_utils.utils_enhanced_validation import (
    validate_and_constrain_numeric_value,
)
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


def _coerce_income_worksheet_amount_int_or_default(
    *, raw_value: Any, default_value: int = 0) -> int:
    """Coerce worksheet income amounts while keeping booleans on the default path."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    if str(raw_value).strip() == "":
        return default_value

    return int(float(str(raw_value).replace(",", "")))


# Update string identifiers to conform to coding standards
@module.ui
def subtab_clients_income_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:  # pragma: no cover
    """Create the income subtab UI for primary and partner client inputs."""
    try:
        return ui.div(
            # Main section header
            ui.h3("Income Information", class_="text-center mb-4"),
            # Primary and Partner client sections in responsive layout
            ui.row(
                # Primary client Income Section
                ui.column(
                    6,
                    create_enhanced_card_section(
                        title="Primary client Income",
                        content=[
                            # Social Security Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security",
                                label_text="Social Security Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual Social Security benefits received",
                                tooltip_text="Enter annual Social Security income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Pension Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_primary_income_pension",
                                label_text="Pension Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual pension income from retirement plans",
                                tooltip_text="Enter annual pension income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Existing Annuity Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing",
                                label_text="Existing Annuity Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual income from existing annuity contracts",
                                tooltip_text="Enter existing annuity income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Other Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_primary_income_other",
                                label_text="Other Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual income from other sources not listed above",
                                tooltip_text="Enter other income sources",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                        ],
                        icon_class="fas fa-dollar-sign",
                        card_class="h-100 shadow-sm border-primary",
                    ),
                ),
                # Partner client Income Section
                ui.column(
                    6,
                    create_enhanced_card_section(
                        title="Partner client Income",
                        content=[
                            # Social Security Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security",
                                label_text="Social Security Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual Social Security benefits received",
                                tooltip_text="Enter annual Social Security income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Pension Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_partner_income_pension",
                                label_text="Pension Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual pension income from retirement plans",
                                tooltip_text="Enter annual pension income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Existing Annuity Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing",
                                label_text="Existing Annuity Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual income from existing annuity contracts",
                                tooltip_text="Enter existing annuity income",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                            # Other Income Input - Updated identifier following coding standards
                            create_enhanced_numeric_input(
                                input_ID="input_ID_tab_clients_subtab_clients_income_client_partner_income_other",
                                label_text="Other Income",
                                min_value=0,
                                max_value=5000000,
                                step_size=100,
                                default_value=0,
                                currency_format=True,
                                prefix_symbol="$",
                                # help_text="Annual income from other sources not listed above",
                                tooltip_text="Enter other income sources",
                                required_field=False,
                                disabled_state=False,
                                input_width="100%",
                            ),
                        ],
                        icon_class="fas fa-money-bill-wave",
                        card_class="h-100 shadow-sm border-info",
                    ),
                ),
            ),
            # Income Summary Section - Updated identifiers following coding standards
            ui.row(
                # Total Income for client Primary (leftmost)
                ui.column(
                    4,
                    create_enhanced_summary_display(
                        summary_id="output_ID_tab_clients_subtab_clients_income_client_primary_total",
                        title="Total Income for client Primary",
                        icon_class="fas fa-calculator",
                        background_class="bg-light",
                        border_variant=ComponentVariant.SUCCESS,
                    ),
                ),
                # Combined Total Income (middle)
                ui.column(
                    4,
                    create_enhanced_summary_display(
                        summary_id="output_ID_tab_clients_subtab_clients_income_combined_total",
                        title="Combined Total Income",
                        icon_class="fas fa-coins",
                        background_class="bg-success",
                        text_class="text-white",
                        border_variant=ComponentVariant.SUCCESS,
                    ),
                ),
                # Total Income for client Partner (rightmost)
                ui.column(
                    4,
                    create_enhanced_summary_display(
                        summary_id="output_ID_tab_clients_subtab_clients_income_client_partner_total",
                        title="Total Income for client Partner",
                        icon_class="fas fa-calculator",
                        background_class="bg-light",
                        border_variant=ComponentVariant.INFO,
                    ),
                ),
            ),
            ui.row(
                ui.column(
                    12,
                    ui.card(
                        ui.card_header(ui.h4("client Income Overview", class_="text-center")),
                        ui.card_body(
                            ui.div(
                                ui.output_ui(
                                    "output_ID_tab_clients_subtab_clients_income_table_main",
                                ),
                                style="min-height: 300px; border: 1px dashed #ccc; padding: 10px;",
                            ),
                            class_="text-center",
                        ),
                    ),
                ),
            ),
            # Add custom CSS to ensure inputs are fully interactive
            ui.tags.style("""
            /* Ensure all numeric inputs are fully editable */
            input[type="number"] {
                pointer-events: auto !important;
                user-select: text !important;
                background-color: #ffffff !important;
                opacity: 1 !important;
                cursor: text !important;
            }

            /* Ensure input containers are interactive */
            .form-group {
                pointer-events: auto !important;
            }

            /* Style focused inputs */
            input[type="number"]:focus {
                border-color: #86b7fe !important;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
                outline: 0 !important;
            }

            /* Ensure input labels are properly styled */
            .form-label {
                pointer-events: none;
                user-select: none;
                cursor: default;
            }

            /* Enhanced styling for currency inputs */
            .currency-input input[type="number"] {
                text-align: right;
                font-weight: 500;
            }

            /* Card styling enhancements */
            .card {
                transition: box-shadow 0.15s ease-in-out;
            }

            .card:hover {
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
            }
            """),
        )

    except Exception as exc_error:
        error_message = f"Unexpected error creating income subtab UI: {exc_error}"
        raise Exception_Configuration(error_message) from exc_error


@module.server
def subtab_clients_income_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Run reactive income formatting, totals, tables, and shared-state updates."""

    def _sync_currency_input_display(
        *, input_reactive: Any, input_id: str) -> None:
        """Normalize one income input to the module's currency display format."""
        try:
            current_value = input_reactive()
            if current_value is None:
                return

            current_str = str(current_value).strip()
            if not current_str:
                return

            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 5000000)
            formatted_value = format_currency_value(amount = constrained_value)
            if current_str != formatted_value:
                ui.update_text(input_id, value=formatted_value)
        except Exception:
            pass

    def _calculate_income_total_display(*, input_ids: tuple[str, ...]) -> str:
        """Return a formatted total for the supplied income input identifiers."""
        try:
            total_value = sum(get_value_from_shiny_input_numeric(input_reactive_object = input[input_id]) for input_id in input_ids)
            return format_currency_value(amount = total_value)
        except Exception as exc_error:
            return f"Error: {exc_error!s}"

    # Reactive observers for currency formatting with proper input/display separation - Updated identifiers following coding standards
    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security,
        ignore_none=True,
    )
    def observer_update_primary_social_security_formatting() -> None:
        """Update currency formatting for primary social security income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_primary_income_pension,
        ignore_none=True,
    )
    def observer_update_primary_pension_formatting() -> None:
        """Update currency formatting for primary pension income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_primary_income_pension,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_primary_income_pension",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing,
        ignore_none=True,
    )
    def observer_update_primary_existing_annuity_formatting() -> None:
        """Update currency formatting for primary existing annuity income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_primary_income_other,
        ignore_none=True,
    )
    def observer_update_primary_other_formatting() -> None:
        """Update currency formatting for primary other income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_primary_income_other,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_primary_income_other",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security,
        ignore_none=True,
    )
    def observer_update_partner_social_security_formatting() -> None:
        """Update currency formatting for partner social security income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_partner_income_pension,
        ignore_none=True,
    )
    def observer_update_partner_pension_formatting() -> None:
        """Update currency formatting for partner pension income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_partner_income_pension,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_partner_income_pension",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing,
        ignore_none=True,
    )
    def observer_update_partner_existing_annuity_formatting() -> None:
        """Update currency formatting for partner existing annuity income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing",
        )

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_income_client_partner_income_other,
        ignore_none=True,
    )
    def observer_update_partner_other_formatting() -> None:
        """Update currency formatting for partner other income input."""
        _sync_currency_input_display(
            input_reactive = input.input_ID_tab_clients_subtab_clients_income_client_partner_income_other,
            input_id = "input_ID_tab_clients_subtab_clients_income_client_partner_income_other",
        )

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_income_client_primary_total():
        """Calculate and display the total income for the primary client."""
        return _calculate_income_total_display(
            input_ids = (
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_pension",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_other",
            ),
        )

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_income_client_partner_total():
        """Calculate and display the total income for the partner client."""
        return _calculate_income_total_display(
            input_ids = (
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_pension",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_other",
            ),
        )

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_income_combined_total():
        """Calculate and display the combined total income for both clients."""
        return _calculate_income_total_display(
            input_ids = (
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_pension",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing",
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_other",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_pension",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing",
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_other",
            ),
        )

    @reactive.calc
    def calc_table_clients_income_main() -> pl.DataFrame:
        """Generate the main income summary table with explicit reactive dependencies."""
        try:
            # Input validation with early returns and explicit reactive dependencies
            # Access reactive values using proper Shiny input access patterns

            # Primary client income information with proper reactive dependencies
            value_Primary_Social_Security = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security"
                ],
            )
            value_Primary_Pension = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_primary_income_pension"],
            )
            value_Primary_Annuity = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing"
                ],
            )
            value_Primary_Other = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_primary_income_other"],
            )

            # Partner client income information with proper reactive dependencies
            value_Partner_Social_Security = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security"
                ],
            )
            value_Partner_Pension = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_partner_income_pension"],
            )
            value_Partner_Annuity = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing"
                ],
            )
            value_Partner_Other = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_partner_income_other"],
            )

            # Configuration validation - ensure all values are non-negative
            value_Primary_Social_Security = max(0.0, value_Primary_Social_Security)
            value_Primary_Pension = max(0.0, value_Primary_Pension)
            value_Primary_Annuity = max(0.0, value_Primary_Annuity)
            value_Primary_Other = max(0.0, value_Primary_Other)
            value_Partner_Social_Security = max(0.0, value_Partner_Social_Security)
            value_Partner_Pension = max(0.0, value_Partner_Pension)
            value_Partner_Annuity = max(0.0, value_Partner_Annuity)
            value_Partner_Other = max(0.0, value_Partner_Other)

            # Business logic validation - calculate totals
            value_Primary_Total = (
                value_Primary_Social_Security
                + value_Primary_Pension
                + value_Primary_Annuity
                + value_Primary_Other
            )
            value_Partner_Total = (
                value_Partner_Social_Security
                + value_Partner_Pension
                + value_Partner_Annuity
                + value_Partner_Other
            )

            # Calculate combined totals
            value_Combined_Social_Security = (
                value_Primary_Social_Security + value_Partner_Social_Security
            )
            value_Combined_Pension = value_Primary_Pension + value_Partner_Pension
            value_Combined_Annuity = value_Primary_Annuity + value_Partner_Annuity
            value_Combined_Other = value_Primary_Other + value_Partner_Other
            value_Combined_Total = value_Primary_Total + value_Partner_Total

            # Create polars dataframe with four columns using coding standards naming
            Income_Data = pl.DataFrame(
                {
                    "Income_Category": [
                        "Social Security",
                        "Pension Income",
                        "Existing Annuity",
                        "Other Income",
                        "Total Income",
                    ],
                    "client_Primary": [
                        value_Primary_Social_Security,
                        value_Primary_Pension,
                        value_Primary_Annuity,
                        value_Primary_Other,
                        value_Primary_Total,
                    ],
                    "client_Partner": [
                        value_Partner_Social_Security,
                        value_Partner_Pension,
                        value_Partner_Annuity,
                        value_Partner_Other,
                        value_Partner_Total,
                    ],
                    "Combined_Total": [
                        value_Combined_Social_Security,
                        value_Combined_Pension,
                        value_Combined_Annuity,
                        value_Combined_Other,
                        value_Combined_Total,
                    ],
                },
            )

            # Configuration validation - verify dataframe was created successfully
            if Income_Data is None or Income_Data.height == 0:
                raise Exception_Validation_Input("Failed to create Income_Data dataframe")

            # Return Income_Data with proper reactive dependencies established
            return Income_Data

        except Exception:
            # Log error for debugging but return fallback dataframe
            # Note: Logging not imported to keep module lightweight
            # Suppress exception info since we're returning a safe fallback

            # Return fallback empty dataframe following coding standards naming
            return pl.DataFrame(
                {
                    "Income_Category": ["Error"],
                    "client_Primary": [0.0],
                    "client_Partner": [0.0],
                    "Combined_Total": [0.0],
                },
            )

    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_income_table_main():
        """Generate income sources summary table using great-tables with reactive dependencies."""
        try:
            # Input validation with early returns - get reactive data from calculation
            data_Income_DF = calc_table_clients_income_main()

            # Configuration validation - ensure dataframe exists and has data
            if data_Income_DF is None:
                raise Exception_Validation_Input("data_Income_DF is None from reactive calculation")

            if data_Income_DF.height == 0:
                raise Exception_Validation_Input(
                    "data_Income_DF is empty from reactive calculation",
                )

            # Try to create the enhanced table
            try:
                table_Income = create_enhanced_summary_table_multi_column(
                    dataframe_input=data_Income_DF,
                    table_title="Income Sources Summary",
                    table_subtitle="Annual income projections from all sources for retirement planning",
                    currency_columns=["client_Primary", "client_Partner", "Combined_Total"],
                    table_theme="professional",
                    table_width="100%",
                )

                # Configuration validation - verify table was created successfully
                if table_Income is None:
                    raise Exception_Validation_Input(
                        "Failed to create table_Income using enhanced function",
                    )

                # Return the GT table as HTML
                return ui.HTML(table_Income.as_raw_html())

            except Exception as table_error:
                # Fallback to simple HTML table if enhanced table creation fails
                def format_currency_fallback(*, amount: Any) -> str | None:
                    """Format currency for fallback table."""
                    try:
                        return f"${amount:,.0f}" if amount != 0 else "$0"
                    except (ValueError, TypeError):
                        return "$0"

                # Extract values safely from the dataframe
                try:
                    income_categories = (
                        data_Income_DF.select("Income_Category").to_series().to_list()
                    )
                    primary_values = data_Income_DF.select("client_Primary").to_series().to_list()
                    partner_values = data_Income_DF.select("client_Partner").to_series().to_list()
                    combined_values = data_Income_DF.select("Combined_Total").to_series().to_list()

                    # Generate table rows
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
                    # Ultimate fallback if even simple table generation fails
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
            # Enhanced error handling with comprehensive error information
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
    def observer_update_shared_reactives_shiny_income() -> None:
        """Update shared reactive values for cross-module communication.

        This reactive effect automatically updates the shared reactives_shiny structure
        whenever any income input values change, ensuring that other modules (like the
        Summary tab) can access the current income values for calculations and displays.

        Reactive Dependencies:
            - input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security
            - input_ID_tab_clients_subtab_clients_income_client_primary_income_pension
            - input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing
            - input_ID_tab_clients_subtab_clients_income_client_primary_income_other
            - input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security
            - input_ID_tab_clients_subtab_clients_income_client_partner_income_pension
            - input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing
            - input_ID_tab_clients_subtab_clients_income_client_partner_income_other

        Updates:
            Updates the User_Inputs_Shiny category in reactives_shiny with current
            income values for cross-module communication and summary calculations.

        Error Handling:
            Uses defensive programming with comprehensive error handling to ensure
            the application continues to function even if reactive updates fail.
        """
        # Get all current income values using the safe input access pattern
        primary_social_security = get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_social_security"
            ],
        )
        primary_pension = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_primary_income_pension"],
        )
        primary_annuity_existing = get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_income_client_primary_income_annuity_existing"
            ],
        )
        primary_other = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_primary_income_other"],
        )

        partner_social_security = get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_social_security"
            ],
        )
        partner_pension = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_partner_income_pension"],
        )
        partner_annuity_existing = get_value_from_shiny_input_numeric(
            input_reactive_object = input[
                "input_ID_tab_clients_subtab_clients_income_client_partner_income_annuity_existing"
            ],
        )
        partner_other = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_income_client_partner_income_other"],
        )

        # Update shared reactive values if available
        if reactives_shiny and isinstance(reactives_shiny, dict):
            user_inputs_category = reactives_shiny.get("User_Inputs_Shiny")
            if user_inputs_category and isinstance(user_inputs_category, dict):
                # Store all income values in the shared reactive structure
                # Following the naming convention from reactives_shiny.py
                income_mapping = {
                    "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security": primary_social_security,
                    "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension": primary_pension,
                    "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Annuity_Existing": primary_annuity_existing,
                    "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Other": primary_other,
                    "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Social_Security": partner_social_security,
                    "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Pension": partner_pension,
                    "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Annuity_Existing": partner_annuity_existing,
                    "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other": partner_other,
                }

                # Update each reactive value safely using defensive programming
                for reactive_key, current_value in income_mapping.items():
                    if reactive_key in user_inputs_category:
                        reactive_var = user_inputs_category[reactive_key]
                        if reactive_var is not None and hasattr(reactive_var, "set"):
                            reactive_var.set(current_value)

    # -----------------------------------------------------------------------
    # Populate from uploaded worksheet PDF
    # -----------------------------------------------------------------------
    # The observer depends directly on Extracted_Worksheet_Data rather than
    # on Trigger_Populate_From_Worksheet so that it fires even when this
    # subtab is hidden at the moment the PDF is uploaded.  ui.update_* calls
    # are buffered by the browser and applied when the widget enters the DOM.
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # Populate from uploaded worksheet PDF
    # -----------------------------------------------------------------------
    # Using @reactive.poll because @reactive.effect inside @module.server
    # does NOT re-execute when reactive.Value changes.
    # -----------------------------------------------------------------------

    def _poll_extracted_worksheet_for_income():
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return None
        try:
            return rv_data.get()
        except Exception:
            return None

    @reactive.poll(_poll_extracted_worksheet_for_income, interval_secs=0.5)
    def _poll_income_data():
        return _poll_extracted_worksheet_for_income()

    @reactive.effect
    def observer_populate_income_from_worksheet() -> None:  # pragma: no cover
        """Populate income inputs from extracted worksheet PDF data.

        Uses :func:`map_income_worksheet_to_inputs` for pure mapping logic;
        this observer only dispatches ``ui.update_text`` calls.
        """
        data = _poll_income_data()
        _logger.warning("income_populate: FIRED | data_is_dict=%s", isinstance(data, dict))
        if not isinstance(data, dict):
            return
        section = data.get("Income", {})
        if not isinstance(section, dict):
            _logger.warning("income_populate: Income section missing")
            return

        _logger.warning("income_populate: processing | section keys=%s", list(section.keys()))

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_income_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_income_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            _logger.warning("income_populate: %s mapped count=%s", client_role, len(mapped))
            for input_id, value in mapped.items():
                ui.update_text(input_id, value = value)

        _logger.warning(
            "Income inputs populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "income"},
        )

    # ------------------------------------------------------------------
    # Deferred populate — re-runs when the subtab becomes visible.
    # ------------------------------------------------------------------
    @reactive.effect
    def observer_deferred_populate_income() -> None:  # pragma: no cover
        """Re-populate income inputs when the subtab becomes visible."""
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return
        data = rv_data.get()
        if not isinstance(data, dict):
            return
        section = data.get("Income", {})
        if not isinstance(section, dict):
            return

        triggers = reactives_shiny.get("Triggers_Shiny", {})
        trigger_rv = triggers.get("Trigger_Populate_From_Worksheet")
        if trigger_rv is not None:
            trigger_rv.get()

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_income_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_income_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            for input_id, value in mapped.items():
                ui.update_text(input_id, value = value)

        _logger.info(
            "Income inputs deferred-populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "income", "deferred": True},
        )
