"""Assets subtab UI and server logic with source-visible public Shiny hooks."""

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
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)


# Re-export the private worksheet coercion helper for unit tests that import
# it from this public module. The canonical definition lives in
# ``_subtab_assets_helpers.py``; the function is exposed here so test code
# can target the public facade without reaching into a private module.
from src.dashboard.shiny_tab_clients._subtab_assets_helpers import (  # noqa: E402
    _coerce_assets_worksheet_amount_int_or_default,
)


@module.ui
def subtab_clients_assets_ui(
    *, data_utils: dict[str, Any], data_inputs: dict[str, Any]) -> Any:  # pragma: no cover
    """Create the assets subtab UI for primary and partner client inputs."""
    return ui.div(
        # Main section header
        ui.h3("Asset Information", class_="text-center mb-4"),
        # Primary and Partner client sections in responsive layout
        ui.row(
            # Primary client Assets Section
            ui.column(
                6,
                create_enhanced_card_section(
                    title="Primary client Assets",
                    content=[
                        # Asset Categories
                        ui.h5("Asset Categories", class_="mb-3 text-primary"),
                        # Taxable Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable",
                            label_text="Taxable Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of taxable investment accounts",
                            tooltip_text="Enter taxable asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                        # Tax Deferred Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred",
                            label_text="Tax Deferred Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of tax-deferred accounts (401k, Traditional IRA, etc.)",
                            tooltip_text="Enter tax-deferred asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                        # Tax Free Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free",
                            label_text="Tax Free Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of tax-free accounts (Roth IRA, Roth 401k, etc.)",
                            tooltip_text="Enter tax-free asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                    ],
                    icon_class="fas fa-university",
                    card_class="h-100 shadow-sm border-primary",
                ),
            ),
            # Partner client Assets Section
            ui.column(
                6,
                create_enhanced_card_section(
                    title="Partner client Assets",
                    content=[
                        # Asset Categories
                        ui.h5("Asset Categories", class_="mb-3 text-info"),
                        # Taxable Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable",
                            label_text="Taxable Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of taxable investment accounts",
                            tooltip_text="Enter taxable asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                        # Tax Deferred Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred",
                            label_text="Tax Deferred Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of tax-deferred accounts (401k, Traditional IRA, etc.)",
                            tooltip_text="Enter tax-deferred asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                        # Tax Free Assets Input
                        create_enhanced_numeric_input(
                            input_ID="input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free",
                            label_text="Tax Free Assets",
                            min_value=0,
                            max_value=100000000,
                            step_size=1000,
                            default_value=0,
                            currency_format=True,
                            prefix_symbol="$",
                            # help_text="Total value of tax-free accounts (Roth IRA, Roth 401k, etc.)",
                            tooltip_text="Enter tax-free asset value",
                            required_field=False,
                            disabled_state=False,
                            input_width="100%",
                        ),
                    ],
                    icon_class="fas fa-piggy-bank",
                    card_class="h-100 shadow-sm border-info",
                ),
            ),
        ),
        # Asset Summary Section
        ui.row(
            # Primary client Total Assets (leftmost)
            ui.column(
                4,
                create_enhanced_summary_display(
                    summary_id="output_ID_tab_clients_subtab_clients_assets_client_primary_total",
                    title="Total Assets for client Primary",
                    icon_class="fas fa-calculator",
                    background_class="bg-light",
                    border_variant=ComponentVariant.SUCCESS,
                ),
            ),
            # Combined Assets Total (middle)
            ui.column(
                4,
                create_enhanced_summary_display(
                    summary_id="output_ID_tab_clients_subtab_clients_assets_combined_total",
                    title="Combined Total Assets",
                    icon_class="fas fa-chart-bar",
                    background_class="bg-success",
                    text_class="text-white",
                    border_variant=ComponentVariant.SUCCESS,
                ),
            ),
            # Partner client Total Assets (rightmost)
            ui.column(
                4,
                create_enhanced_summary_display(
                    summary_id="output_ID_tab_clients_subtab_clients_assets_client_partner_total",
                    title="Total Assets for client Partner",
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
                    ui.card_header(ui.h4("client Assets Overview", class_="text-center")),
                    ui.card_body(
                        ui.div(
                            ui.output_ui("output_ID_tab_clients_subtab_clients_assets_table_main"),
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

        /* Remove any disabled styling */
        .disabled {
            opacity: 1 !important;
        }

        .disabled input {
            background-color: #ffffff !important;
            cursor: text !important;
        }
        """),
    )


@module.server
def subtab_clients_assets_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict[str, Any],
    data_inputs: dict[str, Any],
    reactives_shiny: dict[str, Any],
) -> None:
    """Run reactive asset formatting, totals, tables, and shared-state updates."""
    # Reactive observers for currency formatting with proper input/display separation

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable,
        ignore_none=True,
    )
    def observer_update_primary_taxable_assets_formatting() -> None:
        """Update currency formatting for primary taxable assets input."""
        try:
            # Get current raw value directly from input
            current_value = (
                input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable()
            )

            if current_value is None:
                return

            # Convert to string for processing
            current_str = str(current_value).strip()

            # Skip if empty
            if not current_str:
                return

            # Extract numeric value (this is the actual input value we want to preserve)
            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)

            # Validate and constrain
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 100000000)

            # Format for display (this is what the user sees)
            formatted_value = format_currency_value(amount = constrained_value)

            # Only update display if different from current display
            if current_str != formatted_value:
                ui.update_text(
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable",
                    value=formatted_value,
                )

        except Exception:
            # Silently handle errors to prevent disruption
            pass

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred,
        ignore_none=True,
    )
    def observer_update_primary_tax_deferred_assets_formatting() -> None:
        """Update currency formatting for primary tax deferred assets input."""
        try:
            # Get current raw value directly from input
            current_value = input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred()

            if current_value is None:
                return

            # Convert to string for processing
            current_str = str(current_value).strip()

            # Skip if empty
            if not current_str:
                return

            # Extract numeric value (this is the actual input value we want to preserve)
            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)

            # Validate and constrain
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 100000000)

            # Format for display (this is what the user sees)
            formatted_value = format_currency_value(amount = constrained_value)

            # Only update display if different from current display
            if current_str != formatted_value:
                ui.update_text(
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred",
                    value=formatted_value,
                )

        except Exception:
            # Silently handle errors to prevent disruption
            pass

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free,
        ignore_none=True,
    )
    def observer_update_primary_tax_free_assets_formatting() -> None:
        """Update currency formatting for primary tax free assets input."""
        try:
            # Get current raw value directly from input
            current_value = (
                input.input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free()
            )

            if current_value is None:
                return

            # Convert to string for processing
            current_str = str(current_value).strip()

            # Skip if empty
            if not current_str:
                return

            # Extract numeric value (this is the actual input value we want to preserve)
            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)

            # Validate and constrain
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 100000000)

            # Format for display (this is what the user sees)
            formatted_value = format_currency_value(amount = constrained_value)

            # Only update display if different from current display
            if current_str != formatted_value:
                ui.update_text(
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free",
                    value=formatted_value,
                )

        except Exception:
            # Silently handle errors to prevent disruption
            pass

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred,
        ignore_none=True,
    )
    def observer_update_partner_tax_deferred_assets_formatting() -> None:
        """Update currency formatting for partner tax deferred assets input."""
        try:
            # Get current raw value directly from input
            current_value = input.input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred()

            if current_value is None:
                return

            # Convert to string for processing
            current_str = str(current_value).strip()

            # Skip if empty
            if not current_str:
                return

            # Extract numeric value (this is the actual input value we want to preserve)
            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)

            # Validate and constrain
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 100000000)

            # Format for display (this is what the user sees)
            formatted_value = format_currency_value(amount = constrained_value)

            # Only update display if different from current display
            if current_str != formatted_value:
                ui.update_text(
                    "input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred",
                    value=formatted_value,
                )

        except Exception:
            # Silently handle errors to prevent disruption
            pass

    @reactive.effect
    @reactive.event(
        input.input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free,
        ignore_none=True,
    )
    def observer_update_partner_tax_free_assets_formatting() -> None:
        """Update currency formatting for partner tax free assets input."""
        try:
            # Get current raw value directly from input
            current_value = (
                input.input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free()
            )

            if current_value is None:
                return

            # Convert to string for processing
            current_str = str(current_value).strip()

            # Skip if empty
            if not current_str:
                return

            # Extract numeric value (this is the actual input value we want to preserve)
            numeric_value = extract_numeric_from_currency_string(currency_string = current_str)

            # Validate and constrain
            constrained_value = validate_and_constrain_numeric_value(value = numeric_value, min_value = 0, max_value = 100000000)

            # Format for display (this is what the user sees)
            formatted_value = format_currency_value(amount = constrained_value)

            # Only update display if different from current display
            if current_str != formatted_value:
                ui.update_text(
                    "input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free",
                    value=formatted_value,
                )

        except Exception:
            # Silently handle errors to prevent disruption
            pass

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_assets_client_primary_total():
        """Calculate and display the total assets for the primary client."""
        try:
            value_Primary_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"],
            )
            value_Primary_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred"
                ],
            )
            value_Primary_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free"],
            )
            total = max(
                0.0,
                value_Primary_Taxable + value_Primary_Tax_Deferred + value_Primary_Tax_Free,
            )
            return format_currency_value(amount = total)

        except Exception as exc_error:
            return f"Error: {exc_error!s}"

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_assets_client_partner_total():
        """Calculate and display the total assets for the partner client."""
        try:
            value_Partner_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable"],
            )
            value_Partner_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred"
                ],
            )
            value_Partner_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free"],
            )
            total = max(
                0.0,
                value_Partner_Taxable + value_Partner_Tax_Deferred + value_Partner_Tax_Free,
            )
            return format_currency_value(amount = total)

        except Exception as exc_error:
            return f"Error: {exc_error!s}"

    @output
    @render.text
    def output_ID_tab_clients_subtab_clients_assets_combined_total():
        """Calculate and display the combined total assets for both clients."""
        try:
            value_Primary_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"],
            )
            value_Primary_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred"
                ],
            )
            value_Primary_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free"],
            )
            value_Partner_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable"],
            )
            value_Partner_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred"
                ],
            )
            value_Partner_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free"],
            )
            Combined_Total = max(
                0.0,
                value_Primary_Taxable
                + value_Primary_Tax_Deferred
                + value_Primary_Tax_Free
                + value_Partner_Taxable
                + value_Partner_Tax_Deferred
                + value_Partner_Tax_Free,
            )
            return format_currency_value(amount = Combined_Total)

        except Exception as exc_error:
            return f"Error: {exc_error!s}"

    @reactive.effect
    def observer_update_shared_reactives_shiny_assets() -> None:
        """Update shared reactive values for cross-module communication."""
        # Get all current asset values using the safe input access pattern
        primary_taxable = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"],
        )
        primary_tax_deferred = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred"],
        )
        primary_tax_free = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free"],
        )

        partner_taxable = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable"],
        )
        partner_tax_deferred = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred"],
        )
        partner_tax_free = get_value_from_shiny_input_numeric(
            input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free"],
        )

        # Update shared reactive values if available
        if reactives_shiny and isinstance(reactives_shiny, dict):
            user_inputs_category = reactives_shiny.get("User_Inputs_Shiny")
            if user_inputs_category and isinstance(user_inputs_category, dict):
                # Store all asset values in the shared reactive structure
                asset_mapping = {
                    "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": primary_taxable,
                    "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Deferred": primary_tax_deferred,
                    "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Free": primary_tax_free,
                    "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable": partner_taxable,
                    "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred": partner_tax_deferred,
                    "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free": partner_tax_free,
                }

                # Update each reactive value safely
                for reactive_key, current_value in asset_mapping.items():
                    if reactive_key in user_inputs_category:
                        reactive_var = user_inputs_category[reactive_key]
                        if reactive_var is not None and hasattr(reactive_var, "set"):
                            reactive_var.set(current_value)

    # -----------------------------------------------------------------------
    # Populate from uploaded worksheet PDF
    # -----------------------------------------------------------------------
    # Using @reactive.poll because @reactive.effect inside @module.server
    # does NOT re-execute when reactive.Value changes.
    # -----------------------------------------------------------------------

    def _poll_extracted_worksheet_for_assets():
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return None
        try:
            return rv_data.get()
        except Exception:
            return None

    @reactive.poll(_poll_extracted_worksheet_for_assets, interval_secs=0.5)
    def _poll_assets_data():
        return _poll_extracted_worksheet_for_assets()

    @reactive.effect
    def observer_populate_assets_from_worksheet() -> None:  # pragma: no cover
        """Populate assets inputs from extracted worksheet PDF data.

        Uses :func:`map_assets_worksheet_to_inputs` for pure mapping logic;
        this observer only dispatches ``ui.update_text`` calls.
        """
        data = _poll_assets_data()
        _logger.warning("assets_populate: FIRED | data_is_dict=%s", isinstance(data, dict))
        if not isinstance(data, dict):
            return
        section = data.get("Assets", {})
        if not isinstance(section, dict):
            _logger.warning("assets_populate: Assets section missing")
            return

        _logger.warning("assets_populate: processing | section keys=%s", list(section.keys()))

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_assets_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_assets_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            _logger.warning("assets_populate: %s mapped count=%s", client_role, len(mapped))
            for input_id, value in mapped.items():
                ui.update_text(input_id, value = value)

        _logger.warning(
            "Assets inputs populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "assets"},
        )

    # ------------------------------------------------------------------
    # Deferred populate — re-runs when the subtab becomes visible.
    # ------------------------------------------------------------------
    @reactive.effect
    def observer_deferred_populate_assets() -> None:  # pragma: no cover
        """Re-populate assets inputs when the subtab becomes visible."""
        inner_vars = reactives_shiny.get("Inner_Variables_Shiny", {})
        rv_data = inner_vars.get("Extracted_Worksheet_Data")
        if rv_data is None:
            return
        data = rv_data.get()
        if not isinstance(data, dict):
            return
        section = data.get("Assets", {})
        if not isinstance(section, dict):
            return

        triggers = reactives_shiny.get("Triggers_Shiny", {})
        trigger_rv = triggers.get("Trigger_Populate_From_Worksheet")
        if trigger_rv is not None:
            trigger_rv.get()

        from src.dashboard.shiny_utils._utils_tab_clients_populate import (
            map_assets_worksheet_to_inputs,
        )

        for client_role in ("client_primary", "client_partner"):
            mapped = map_assets_worksheet_to_inputs(
                section = section,
                client_role = client_role,
            )
            for input_id, value in mapped.items():
                ui.update_text(input_id, value = value)

        _logger.info(
            "Assets inputs deferred-populated from worksheet PDF",
            extra={"event_type": "worksheet_import", "subtab": "assets", "deferred": True},
        )

    @reactive.calc
    def calc_table_clients_assets_main() -> pl.DataFrame:
        """Generate financial assets summary table with proper reactive dependencies.

        This reactive calculation automatically updates when any of the asset inputs
        change, ensuring the summary table stays synchronized with user inputs.

        Returns
        -------
            pl.DataFrame: Assets data with proper reactive dependencies

        Reactive Dependencies:
            - input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable
            - input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred
            - input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free
            - input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable
            - input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred
            - input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free
        """
        try:
            # Input validation with early returns and explicit reactive dependencies
            # Access reactive values using proper Shiny input access patterns

            # Primary client asset information with proper reactive dependencies
            # Pass the actual reactive input object to the safe function
            value_Primary_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_taxable"],
            )
            value_Primary_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_deferred"
                ],
            )
            value_Primary_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_primary_assets_tax_free"],
            )

            # Partner client asset information with proper reactive dependencies
            value_Partner_Taxable = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_taxable"],
            )
            value_Partner_Tax_Deferred = get_value_from_shiny_input_numeric(
                input_reactive_object = input[
                    "input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_deferred"
                ],
            )
            value_Partner_Tax_Free = get_value_from_shiny_input_numeric(
                input_reactive_object = input["input_ID_tab_clients_subtab_clients_assets_client_partner_assets_tax_free"],
            )

            # Configuration validation - ensure all values are non-negative
            value_Primary_Taxable = max(0.0, value_Primary_Taxable)
            value_Primary_Tax_Deferred = max(0.0, value_Primary_Tax_Deferred)
            value_Primary_Tax_Free = max(0.0, value_Primary_Tax_Free)
            value_Partner_Taxable = max(0.0, value_Partner_Taxable)
            value_Partner_Tax_Deferred = max(0.0, value_Partner_Tax_Deferred)
            value_Partner_Tax_Free = max(0.0, value_Partner_Tax_Free)

            # Business logic validation - calculate totals as sum of taxable categories
            value_Primary_Total = (
                value_Primary_Taxable + value_Primary_Tax_Deferred + value_Primary_Tax_Free
            )
            value_Partner_Total = (
                value_Partner_Taxable + value_Partner_Tax_Deferred + value_Partner_Tax_Free
            )

            # Calculate combined totals
            value_Combined_Taxable = value_Primary_Taxable + value_Partner_Taxable
            value_Combined_Tax_Deferred = value_Primary_Tax_Deferred + value_Partner_Tax_Deferred
            value_Combined_Tax_Free = value_Primary_Tax_Free + value_Partner_Tax_Free
            value_Combined_Total = value_Primary_Total + value_Partner_Total

            # Create polars dataframe with four columns using coding standards naming
            Assets_Data = pl.DataFrame(
                {
                    "Asset_Category": [
                        "Taxable Assets",
                        "Tax Deferred Assets",
                        "Tax Free Assets",
                        "Total Assets",
                    ],
                    "client_Primary": [
                        value_Primary_Taxable,
                        value_Primary_Tax_Deferred,
                        value_Primary_Tax_Free,
                        value_Primary_Total,
                    ],
                    "client_Partner": [
                        value_Partner_Taxable,
                        value_Partner_Tax_Deferred,
                        value_Partner_Tax_Free,
                        value_Partner_Total,
                    ],
                    "Combined_Total": [
                        value_Combined_Taxable,
                        value_Combined_Tax_Deferred,
                        value_Combined_Tax_Free,
                        value_Combined_Total,
                    ],
                },
            )

            # Configuration validation - verify dataframe was created successfully
            if Assets_Data is None or Assets_Data.height == 0:
                raise Exception_Validation_Input("Failed to create Assets_Data dataframe")

            # Return Assets_Data with proper reactive dependencies established
            return Assets_Data

        except Exception:
            # Log error for debugging but return fallback dataframe
            # Note: Logging not imported to keep module lightweight
            # Suppress exception info since we're returning a safe fallback

            # Return fallback empty dataframe following coding standards naming
            return pl.DataFrame(
                {
                    "Asset_Category": ["Error"],
                    "client_Primary": [0.0],
                    "client_Partner": [0.0],
                    "Combined_Total": [0.0],
                },
            )

    @output
    @render.ui
    def output_ID_tab_clients_subtab_clients_assets_table_main():
        """Generate financial assets summary table using great-tables with reactive dependencies."""
        try:
            # Input validation with early returns - get reactive data from calculation
            data_Assets_DF = calc_table_clients_assets_main()

            # Configuration validation - ensure dataframe exists and has data
            if data_Assets_DF is None:
                raise Exception_Validation_Input("data_Assets_DF is None from reactive calculation")

            if data_Assets_DF.height == 0:
                raise Exception_Validation_Input(
                    "data_Assets_DF is empty from reactive calculation",
                )

            # Try to create the enhanced table
            try:
                Assets_Table = create_enhanced_summary_table_multi_column(
                    dataframe_input=data_Assets_DF,
                    table_title="Financial Assets Summary",
                    table_subtitle="Current asset values organized by tax treatment and client",
                    currency_columns=["client_Primary", "client_Partner", "Combined_Total"],
                    table_theme="professional",
                    table_width="100%",
                )

                # Configuration validation - verify table was created successfully
                if Assets_Table is None:
                    raise Exception_Validation_Input(
                        "Failed to create Assets_Table using enhanced function",
                    )

                # Return the GT table as HTML
                return ui.HTML(Assets_Table.as_raw_html())

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
                    asset_categories = data_Assets_DF.select("Asset_Category").to_series().to_list()
                    primary_values = data_Assets_DF.select("client_Primary").to_series().to_list()
                    partner_values = data_Assets_DF.select("client_Partner").to_series().to_list()
                    combined_values = data_Assets_DF.select("Combined_Total").to_series().to_list()

                    # Generate table rows
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
                    # Ultimate fallback if even simple table generation fails
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
            # Enhanced error handling with comprehensive error information
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
