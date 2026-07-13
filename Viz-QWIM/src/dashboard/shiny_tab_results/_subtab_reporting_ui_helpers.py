from __future__ import annotations

import contextlib
import datetime
import os
import shutil

from datetime import UTC
from typing import Any

from shiny import ui


def build_subtab_reporting_ui_impl_QWIM(
    *, data_utils: dict, data_inputs: dict) -> Any:
    """Build the reporting subtab UI."""
    current_date_string = datetime.datetime.now(UTC).strftime("%Y%m%d")
    default_filename = f"Report-QWIM-{current_date_string}.pdf"

    return ui.div(
        ui.div(
            ui.h3("📊 QWIM PDF Report Generation", class_="text-primary mb-4"),
            ui.p(
                "Generate comprehensive PDF reports with portfolio analysis and investor information using the Typst typesetting system.",
                class_="text-muted mb-4",
            ),
            ui.p(
                "📥 Reports will be generated and made available for download to your workstation.",
                class_="text-info mb-4 small",
            ),
            class_="text-center",
        ),
        # --- PDF Generation card (moved to top, right below intro) ---
        ui.div(
            ui.h5("📄 PDF Generation", class_="text-primary mb-3"),
            ui.div(
                ui.input_action_button(
                    "input_ID_tab_portfolios_subtab_reporting_btn_generate_pdf",
                    "📄 Generate PDF Report for Download",
                    class_="btn-primary btn-lg mb-3",
                    style="min-width: 350px; padding: 20px 40px; font-size: 18px;",
                ),
                class_="text-center mb-4",
            ),
            ui.div(
                ui.output_ui("output_ID_tab_portfolios_subtab_reporting_ui_pdf_progress"),
                class_="mb-3",
            ),
            ui.div(
                ui.output_ui("output_ID_tab_portfolios_subtab_reporting_ui_download_section"),
                class_="text-center mb-4",
            ),
            class_="card card-body bg-light mb-4",
        ),
        ui.div(
            ui.output_text_verbatim("output_ID_tab_portfolios_subtab_reporting_text_pdf_status"),
            class_="text-center mb-4",
        ),
        ui.div(
            ui.div(
                ui.input_text(
                    "input_ID_tab_portfolios_subtab_reporting_text_report_title",
                    "Report Title:",
                    value="QWIM Report",
                    placeholder="Enter report title...",
                    width="100%",
                ),
                class_="mb-3",
            ),
            ui.div(
                ui.h5("📋 Report Sections", class_="text-primary mb-2"),
                ui.p(
                    "Select which sections to include in the generated PDF report. "
                    "Client Information is always included.",
                    class_="text-muted small mb-3",
                ),
                ui.div(
                    ui.row(
                        ui.column(
                            6,
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_advisor_info",
                                "Advisor Information",
                                value=True,
                            ),
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_analysis",
                                "Portfolio Performance Analysis",
                                value=True,
                            ),
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_comparison",
                                "Portfolio vs Benchmark Comparison",
                                value=True,
                            ),
                        ),
                        ui.column(
                            6,
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_weights_analysis",
                                "Portfolio Weights Analysis",
                                value=True,
                            ),
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_skfolio_optimization",
                                "Portfolio Optimization (skfolio)",
                                value=False,
                            ),
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_optimalportfolios_optimization",
                                "Portfolio Optimization (OptimalPortfolios)",
                                value=False,
                            ),
                            ui.input_checkbox(
                                "input_ID_tab_results_subtab_reporting_checkbox_include_simulation",
                                "Monte Carlo Simulation",
                                value=True,
                            ),
                        ),
                    ),
                    class_="border rounded p-3 bg-white mb-3",
                ),
                ui.row(
                    ui.column(
                        6,
                        ui.input_select(
                            "input_ID_tab_portfolios_subtab_reporting_select_chart_resolution",
                            "Chart Resolution:",
                            choices={
                                "medium": "Medium (Fast)",
                                "high": "High (Recommended)",
                                "ultra": "Ultra (Slow)",
                            },
                            selected="high",
                        ),
                    ),
                ),
                class_="mb-4",
            ),
            class_="card card-body bg-light mb-4",
        ),
        ui.div(
            ui.div(
                ui.h5("� PDF Download Filename", class_="text-primary mb-3"),
                ui.div(
                    ui.input_text(
                        "input_ID_tab_portfolios_subtab_reporting_text_download_filename",
                        "PDF Download Filename:",
                        value=default_filename,
                        placeholder="Enter secure PDF filename with .pdf extension...",
                        width="100%",
                    ),
                    class_="mb-3",
                ),
                ui.div(
                    ui.output_text_verbatim(
                        "output_ID_tab_portfolios_subtab_reporting_text_filename_validation",
                    ),
                    class_="small text-muted border rounded p-2 bg-light",
                ),
                class_="card card-body bg-light",
            ),
            class_="mb-4",
        ),
        ui.div(
            ui.div(
                ui.h6("🔒 Security Information", class_="text-warning mb-2"),
                ui.tags.ul(
                    ui.tags.li("Filename will be sanitized for security"),
                    ui.tags.li(
                        "Only letters, numbers, spaces, dots, hyphens, underscores and parentheses allowed",
                    ),
                    ui.tags.li("Maximum filename length: 200 characters"),
                    ui.tags.li("Reports will be generated on cloud and available for download"),
                    ui.tags.li("No directory paths - filename only"),
                    class_="small text-muted",
                ),
                class_="alert alert-warning small",
            ),
            class_="mb-3",
        ),
        ui.div(
            ui.div(
                ui.h5("📋 Report Information"),
                ui.tags.ul(
                    ui.tags.li("📁 Reports generated on Posit Connect Cloud"),
                    ui.tags.li("📄 Default filename pattern: Report-QWIM-YYYYMMDD.pdf"),
                    ui.tags.li("📊 Includes data from Portfolios and Investors tabs"),
                    ui.tags.li(
                        "📄 Typst: Professional typography with mathematical notation support",
                    ),
                    ui.tags.li("📈 Polars DataFrames integration for enhanced performance"),
                    ui.tags.li("📥 Secure download delivery to your workstation"),
                    ui.tags.li(
                        "🎯 Data sources: Data_Personal_Info_DF, Data_Assets_DF, Data_Goals_DF, Data_Income_DF",
                    ),
                    ui.tags.li("🔒 Filename sanitization for security protection"),
                ),
                class_="card card-body bg-light",
            ),
            class_="mt-4",
        ),
        ui.div(
            ui.div(
                ui.h6("🔧 System Status"),
                ui.div(
                    f"📊 report_QWIM module: {'✅ Available' if data_utils.get('REPORT_QWIM_AVAILABLE', False) else '❌ Not Available'}",
                    ui.br(),
                    f"📝 typst runtime: {'✅ Available' if data_utils.get('TYPST_AVAILABLE', False) else '❌ Not Available'}",
                    ui.br(),
                    f"🔄 reactives_shiny utils: {'✅ Available' if data_utils.get('DATA_UTILS_AVAILABLE', False) else '❌ Not Available'}",
                    ui.br(),
                    "☁️ Deployment: Posit Connect Cloud",
                    ui.br(),
                    "🔒 Security: Filename sanitization enabled",
                    ui.br(),
                    f"🕒 Status updated: {datetime.datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
                    class_="small text-muted",
                ),
                class_="card card-body border-info",
            ),
            class_="mt-3",
        ),
    )


def create_typst_report_with_data_impl_QWIM(
    *, typst_template_path: str, output_path: str, personal_info_data: dict, assets_data: dict, goals_data: dict, income_data: dict, reactives_shiny: dict, get_value_from_reactives_shiny: Any, coerce_reporting_flag_or_default: Any, format_currency_for_typst: Any, logger: Any) -> tuple[bool, str]:
    """Create a Typst report by substituting template placeholders."""
    try:
        if not os.path.exists(typst_template_path):
            return False, f"Template file not found: {typst_template_path}"

        template_dir = os.path.dirname(typst_template_path)
        output_dir = os.path.dirname(output_path)
        bibliography_source_path = os.path.join(template_dir, "sample_refs.bib")
        bibliography_target_path = os.path.join(output_dir, "sample_refs.bib")

        if os.path.exists(bibliography_source_path):
            try:
                shutil.copy2(bibliography_source_path, bibliography_target_path)
                logger.debug("Copied bibliography file to: %s", bibliography_target_path)
            except (OSError, shutil.Error) as copy_error:
                logger.warning("Could not copy bibliography file: %s", copy_error)
        else:
            logger.warning("Bibliography file not found at: %s", bibliography_source_path)
            try:
                with open(bibliography_target_path, "w", encoding="utf-8") as empty_bib:
                    empty_bib.write("% Empty bibliography file created automatically\n")
                logger.debug("Created empty bibliography file: %s", bibliography_target_path)
            except OSError as create_error:
                logger.warning("Could not create empty bibliography file: %s", create_error)

        if not personal_info_data or not assets_data:
            logger.warning("Missing personal info or assets data, using fallback template")
            with open(typst_template_path, encoding="utf-8") as template_file:
                template_content = template_file.read()
            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write(template_content)
            return True, "Template copied without data substitutions"

        with open(typst_template_path, encoding="utf-8") as template_file:
            template_content = template_file.read()

        primary_info = personal_info_data.get("primary", {})
        partner_info = personal_info_data.get("partner", {})
        primary_assets = assets_data.get("primary", {})
        partner_assets = assets_data.get("partner", {})
        combined_assets = assets_data.get("combined", {})
        primary_goals = goals_data.get("primary", {})
        partner_goals = goals_data.get("partner", {})
        combined_goals = goals_data.get("combined", {})
        primary_income = income_data.get("primary", {})
        partner_income = income_data.get("partner", {})
        combined_income = income_data.get("combined", {})

        substitutions = {
            "{{PRIMARY_INVESTOR_NAME}}": str(primary_info.get("name", "Primary Investor")),
            "{{PRIMARY_INVESTOR_AGE_CURRENT}}": str(primary_info.get("age_current", "Not Specified")),
            "{{PRIMARY_INVESTOR_AGE_RETIREMENT}}": str(primary_info.get("age_retirement", "Not Specified")),
            "{{PRIMARY_INVESTOR_AGE_INCOME_STARTING}}": str(primary_info.get("age_income_starting", "Not Specified")),
            "{{PRIMARY_INVESTOR_STATUS_MARITAL}}": str(primary_info.get("status_marital", "Not Specified")),
            "{{PRIMARY_INVESTOR_GENDER}}": str(primary_info.get("gender", "Not Specified")),
            "{{PRIMARY_INVESTOR_TOLERANCE_RISK}}": str(primary_info.get("tolerance_risk", "Not Specified")),
            "{{PRIMARY_INVESTOR_STATE}}": str(primary_info.get("state", "Not Specified")),
            "{{PRIMARY_INVESTOR_CODE_ZIP}}": str(primary_info.get("code_zip", "Not Provided")),
            "{{PARTNER_INVESTOR_NAME}}": str(partner_info.get("name", "Partner Investor")),
            "{{PARTNER_INVESTOR_AGE_CURRENT}}": str(partner_info.get("age_current", "Not Specified")),
            "{{PARTNER_INVESTOR_AGE_RETIREMENT}}": str(partner_info.get("age_retirement", "Not Specified")),
            "{{PARTNER_INVESTOR_AGE_INCOME_STARTING}}": str(partner_info.get("age_income_starting", "Not Specified")),
            "{{PARTNER_INVESTOR_STATUS_MARITAL}}": str(partner_info.get("status_marital", "Not Specified")),
            "{{PARTNER_INVESTOR_GENDER}}": str(partner_info.get("gender", "Not Specified")),
            "{{PARTNER_INVESTOR_TOLERANCE_RISK}}": str(partner_info.get("tolerance_risk", "Not Specified")),
            "{{PARTNER_INVESTOR_STATE}}": str(partner_info.get("state", "Not Specified")),
            "{{PARTNER_INVESTOR_CODE_ZIP}}": str(partner_info.get("code_zip", "Not Provided")),
            "{{PRIMARY_TAXABLE_ASSETS}}": format_currency_for_typst(primary_assets.get("taxable", 0)),
            "{{PRIMARY_TAX_DEFERRED_ASSETS}}": format_currency_for_typst(primary_assets.get("tax_deferred", 0)),
            "{{PRIMARY_TAX_FREE_ASSETS}}": format_currency_for_typst(primary_assets.get("tax_free", 0)),
            "{{PRIMARY_TOTAL_ASSETS}}": format_currency_for_typst(primary_assets.get("total", 0)),
            "{{PARTNER_TAXABLE_ASSETS}}": format_currency_for_typst(partner_assets.get("taxable", 0)),
            "{{PARTNER_TAX_DEFERRED_ASSETS}}": format_currency_for_typst(partner_assets.get("tax_deferred", 0)),
            "{{PARTNER_TAX_FREE_ASSETS}}": format_currency_for_typst(partner_assets.get("tax_free", 0)),
            "{{PARTNER_TOTAL_ASSETS}}": format_currency_for_typst(partner_assets.get("total", 0)),
            "{{COMBINED_TAXABLE_ASSETS}}": format_currency_for_typst(combined_assets.get("taxable", 0)),
            "{{COMBINED_TAX_DEFERRED_ASSETS}}": format_currency_for_typst(combined_assets.get("tax_deferred", 0)),
            "{{COMBINED_TAX_FREE_ASSETS}}": format_currency_for_typst(combined_assets.get("tax_free", 0)),
            "{{COMBINED_TOTAL_ASSETS}}": format_currency_for_typst(combined_assets.get("total", 0)),
            "{{PRIMARY_ESSENTIAL_GOALS}}": format_currency_for_typst(primary_goals.get("essential", 0)),
            "{{PRIMARY_IMPORTANT_GOALS}}": format_currency_for_typst(primary_goals.get("important", 0)),
            "{{PRIMARY_ASPIRATIONAL_GOALS}}": format_currency_for_typst(primary_goals.get("aspirational", 0)),
            "{{PRIMARY_TOTAL_GOALS}}": format_currency_for_typst(primary_goals.get("total", 0)),
            "{{PARTNER_ESSENTIAL_GOALS}}": format_currency_for_typst(partner_goals.get("essential", 0)),
            "{{PARTNER_IMPORTANT_GOALS}}": format_currency_for_typst(partner_goals.get("important", 0)),
            "{{PARTNER_ASPIRATIONAL_GOALS}}": format_currency_for_typst(partner_goals.get("aspirational", 0)),
            "{{PARTNER_TOTAL_GOALS}}": format_currency_for_typst(partner_goals.get("total", 0)),
            "{{COMBINED_ESSENTIAL_GOALS}}": format_currency_for_typst(combined_goals.get("essential", 0)),
            "{{COMBINED_IMPORTANT_GOALS}}": format_currency_for_typst(combined_goals.get("important", 0)),
            "{{COMBINED_ASPIRATIONAL_GOALS}}": format_currency_for_typst(combined_goals.get("aspirational", 0)),
            "{{COMBINED_TOTAL_GOALS}}": format_currency_for_typst(combined_goals.get("total", 0)),
            "{{PRIMARY_SOCIAL_SECURITY_INCOME}}": format_currency_for_typst(primary_income.get("social_security", 0)),
            "{{PRIMARY_PENSION_INCOME}}": format_currency_for_typst(primary_income.get("pension", 0)),
            "{{PRIMARY_ANNUITY_EXISTING_INCOME}}": format_currency_for_typst(primary_income.get("annuity_existing", 0)),
            "{{PRIMARY_OTHER_INCOME}}": format_currency_for_typst(primary_income.get("other", 0)),
            "{{PRIMARY_TOTAL_INCOME}}": format_currency_for_typst(primary_income.get("total", 0)),
            "{{PARTNER_SOCIAL_SECURITY_INCOME}}": format_currency_for_typst(partner_income.get("social_security", 0)),
            "{{PARTNER_PENSION_INCOME}}": format_currency_for_typst(partner_income.get("pension", 0)),
            "{{PARTNER_ANNUITY_EXISTING_INCOME}}": format_currency_for_typst(partner_income.get("annuity_existing", 0)),
            "{{PARTNER_OTHER_INCOME}}": format_currency_for_typst(partner_income.get("other", 0)),
            "{{PARTNER_TOTAL_INCOME}}": format_currency_for_typst(partner_income.get("total", 0)),
            "{{COMBINED_SOCIAL_SECURITY_INCOME}}": format_currency_for_typst(combined_income.get("social_security", 0)),
            "{{COMBINED_PENSION_INCOME}}": format_currency_for_typst(combined_income.get("pension", 0)),
            "{{COMBINED_ANNUITY_EXISTING_INCOME}}": format_currency_for_typst(combined_income.get("annuity_existing", 0)),
            "{{COMBINED_OTHER_INCOME}}": format_currency_for_typst(combined_income.get("other", 0)),
            "{{COMBINED_TOTAL_INCOME}}": format_currency_for_typst(combined_income.get("total", 0)),
        }

        try:
            include_partner_raw = get_value_from_reactives_shiny(
                reactives_shiny=reactives_shiny,
                key_name="Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis",
                key_category="User_Inputs_Shiny",
            )
            include_partner = coerce_reporting_flag_or_default(raw_value=include_partner_raw, default_value=True)
        except Exception:
            include_partner = True

        if not include_partner:
            for placeholder_key in list(substitutions.keys()):
                if "PARTNER" in placeholder_key:
                    substitutions[placeholder_key] = ""

        processed_content = template_content
        for placeholder, value in substitutions.items():
            try:
                processed_content = processed_content.replace(placeholder, value)
            except (TypeError, ValueError, KeyError) as substitution_error:
                logger.warning("Error substituting %s: %s", placeholder, substitution_error)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(processed_content)

        logger.debug("Successfully created Typst report with data: %s", output_path)
        return True, "Typst report with data created successfully"
    except Exception as processing_error:
        return False, f"Error processing Typst template: {processing_error}"


def show_info_notification_internal_impl_QWIM(
    *, message: str, set_pdf_status: Any, logger: Any) -> None:
    """Show an informational reporting notification."""
    try:
        logger.info("INFO: %s", message)
        set_pdf_status(message = f"ℹ️ {message}")
        with contextlib.suppress(Exception):
            ui.notification_show(message, type="message", duration=8)
    except Exception as notification_error:
        logger.warning("Notification error: %s", notification_error)


def show_success_notification_internal_impl_QWIM(
    *, message: str, set_pdf_status: Any, logger: Any) -> None:
    """Show a success reporting notification."""
    try:
        logger.info("SUCCESS: %s", message)
        set_pdf_status(message = f"✅ {message}")
        with contextlib.suppress(Exception):
            ui.notification_show(message, type="message", duration=8)
    except Exception as notification_error:
        logger.warning("Notification error: %s", notification_error)


def show_error_notification_internal_impl_QWIM(
    *, message: str, set_pdf_status: Any, logger: Any) -> None:
    """Show an error reporting notification."""
    try:
        logger.error("ERROR: %s", message)
        set_pdf_status(message = f"❌ {message}")
        try:
            lines = message.split("\n")
            modal_body_parts: list[Any] = [
                ui.p(
                    ui.strong("PDF Report Generation Error"),
                    style="color: #b91c1c; font-size: 1.1em;",
                ),
            ]
            for line in lines:
                stripped_line = line.strip()
                if stripped_line:
                    modal_body_parts.append(ui.p(stripped_line))
            modal_body_parts.append(
                ui.p(
                    ui.em(
                        "Go back to the relevant dashboard tabs and ensure all charts and tables display valid data, then regenerate the report.",
                    ),
                    style="margin-top: 1em; color: #374151;",
                ),
            )
            error_modal = ui.modal(
                *modal_body_parts,
                title="❌ Report Generation Failed",
                easy_close=True,
                footer=ui.modal_button("Close", class_="btn-danger"),
            )
            ui.modal_show(error_modal)
        except Exception:
            with contextlib.suppress(Exception):
                ui.notification_show(message, type="error", duration=15)
    except Exception as notification_error:
        logger.warning("Notification error: %s", notification_error)