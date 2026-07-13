from __future__ import annotations

import asyncio
import contextlib
import datetime
import os
import shutil

from datetime import UTC
from pathlib import Path
from typing import Any

from src.dashboard.shiny_tab_results._subtab_reporting_ui_helpers import (
    show_error_notification_internal_impl_QWIM,
    show_info_notification_internal_impl_QWIM,
    show_success_notification_internal_impl_QWIM,
)


def register_subtab_reporting_server_bindings_impl_QWIM(
    *, server_context: dict[str, Any]) -> None:
    """Register reporting outputs and observers on the Shiny server facade."""
    input = server_context["input"]
    output = server_context["output"]
    reactive_module = server_context["reactive_module"]
    render_module = server_context["render_module"]
    ui_module = server_context["ui_module"]
    generated_pdf_path = server_context["generated_pdf_path"]
    pdf_status_message = server_context["pdf_status_message"]
    pdf_generation_in_progress = server_context["pdf_generation_in_progress"]
    pdf_generation_progress_pct = server_context["pdf_generation_progress_pct"]
    pdf_generation_progress_label = server_context["pdf_generation_progress_label"]
    pdf_generation_step_current = server_context["pdf_generation_step_current"]
    pdf_generation_step_total = server_context["pdf_generation_step_total"]
    pdf_generation_total_steps = server_context["pdf_generation_total_steps"]
    set_pdf_status = server_context["set_pdf_status"]
    set_pdf_progress = server_context["set_pdf_progress"]
    get_user_id_from_session = server_context["get_user_id_from_session"]
    compile_typst_report_to_pdf = server_context["compile_typst_report_to_pdf"]
    sanitize_filename_for_security = server_context["sanitize_filename_for_security"]
    create_secure_temp_directory = server_context["create_secure_temp_directory"]
    cleanup_temp_files = server_context["cleanup_temp_files"]
    copy_typst_dependencies_to_temp_directory = server_context[
        "copy_typst_dependencies_to_temp_directory"
    ]
    coerce_reporting_flag_or_default = server_context["coerce_reporting_flag_or_default"]
    typst_available = server_context["typst_available"]
    reactives_shiny = server_context["reactives_shiny"]
    export_all_report_data = server_context["export_all_report_data"]
    export_report_config = server_context["export_report_config"]
    export_all_report_plots = server_context["export_all_report_plots"]
    export_visual_objects_to_svg = server_context["export_visual_objects_to_svg"]
    validate_report_data_quality = server_context["validate_report_data_quality"]
    ensure_all_svg_files_exist = server_context["ensure_all_svg_files_exist"]
    logger = server_context["logger"]
    module_file_path = server_context["module_file_path"]

    def show_info_notification_internal(*, message: str) -> None:
        """Show an informational reporting notification."""
        show_info_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=logger,
        )

    def show_success_notification_internal(*, message: str) -> None:
        """Show a success reporting notification."""
        show_success_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=logger,
        )

    def show_error_notification_internal(*, message: str) -> None:
        """Show an error reporting notification."""
        show_error_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=logger,
        )

    @output
    @render_module.text
    def output_ID_tab_portfolios_subtab_reporting_text_pdf_status() -> str:
        """Render the PDF generation status text."""
        return pdf_status_message.get()

    @output
    @render_module.ui
    def output_ID_tab_portfolios_subtab_reporting_ui_pdf_progress():
        """Render the PDF generation progress indicator."""
        if not pdf_generation_in_progress.get():
            return ui_module.div()

        progress_percent = pdf_generation_progress_pct.get()
        progress_label = pdf_generation_progress_label.get()
        current_step = pdf_generation_step_current.get()
        total_steps = pdf_generation_step_total.get()

        return ui_module.div(
            ui_module.div(
                ui_module.tags.div(
                    ui_module.tags.span(
                        class_="spinner-border spinner-border-sm me-2",
                        role="status",
                    ),
                    ui_module.tags.strong(
                        f"Generating PDF... Step {current_step} of {total_steps} ({progress_percent}%)",
                    ),
                    class_="mb-2",
                ),
                ui_module.tags.div(
                    ui_module.tags.div(
                        style=f"width: {progress_percent}%;",
                        class_="progress-bar progress-bar-striped progress-bar-animated",
                        role="progressbar",
                        **{
                            "aria-valuenow": str(progress_percent),
                            "aria-valuemin": "0",
                            "aria-valuemax": "100",
                        },
                    ),
                    class_="progress mb-2",
                    style="height: 18px;",
                ),
                ui_module.tags.small(progress_label, class_="text-muted"),
            ),
            class_="alert alert-info",
        )

    @output
    @render_module.text
    def output_ID_tab_portfolios_subtab_reporting_text_filename_validation() -> str | None:
        """Render the filename validation status."""
        try:
            current_filename = input.input_ID_tab_portfolios_subtab_reporting_text_download_filename()
            if not current_filename:
                return "📄 Enter a filename to validate"

            is_valid, sanitized_name, validation_message = sanitize_filename_for_security(
                filename = current_filename,
            )
            if is_valid:
                if sanitized_name == current_filename:
                    return f"✅ Filename is valid and secure: {sanitized_name}"
                return f"⚠️ Filename will be sanitized to: {sanitized_name}"
            return f"❌ Invalid filename: {validation_message}"
        except Exception as validation_error:
            logger.warning("Error validating filename: %s", validation_error)
            return "❌ Error validating filename"

    @output
    @render_module.ui
    def output_ID_tab_portfolios_subtab_reporting_ui_download_section():
        """Render the PDF download section."""
        try:
            current_pdf_path = generated_pdf_path.get()
            if current_pdf_path and os.path.exists(current_pdf_path):
                pdf_filename = os.path.basename(current_pdf_path)
                return ui_module.div(
                    ui_module.h5("📥 PDF Ready", class_="text-success mb-3"),
                    ui_module.p(
                        f"Report generated successfully: {pdf_filename}",
                        class_="mb-3",
                    ),
                    ui_module.download_button(
                        "btn_download_pdf_report",
                        "📄 Download PDF Report",
                        class_="btn-success btn-lg",
                        style="min-width: 300px; padding: 15px 30px; font-size: 16px;",
                    ),
                    class_="alert alert-success",
                )
            return ui_module.div()
        except Exception as download_ui_error:
            logger.warning("Error rendering download UI: %s", download_ui_error)
            return ui_module.div()

    @output
    @render_module.download(filename=lambda: os.path.basename(generated_pdf_path.get() or "report.pdf"))
    def btn_download_pdf_report():
        """Handle the generated PDF download."""
        try:
            current_pdf_path = generated_pdf_path.get()
            if not current_pdf_path or not os.path.exists(current_pdf_path):
                logger.warning("No PDF file available for download")
                return
            if not os.access(current_pdf_path, os.R_OK):
                logger.warning("PDF file is not readable")
                return
            logger.debug("Initiating PDF download for: %s", current_pdf_path)
            with open(current_pdf_path, "rb") as pdf_file_handle:
                yield pdf_file_handle.read()
        except Exception as download_error:  # pragma: no cover
            logger.opt(exception=True).error("Error handling PDF download: {}", download_error)

    @reactive_module.effect
    def observer_update_shared_reactives_shiny_reporting() -> None:  # pragma: no cover
        """Synchronize report section flags into User_Inputs_Shiny."""
        if reactives_shiny is None or not isinstance(reactives_shiny, dict):
            return
        user_inputs = reactives_shiny.get("User_Inputs_Shiny")
        if not isinstance(user_inputs, dict):
            return

        flag_map = {
            "Input_Tab_Results_Subtab_Reporting_Include_Advisor_Info": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_advisor_info",
                True,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_Portfolio_Analysis": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_analysis",
                True,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_Portfolio_Comparison": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_comparison",
                True,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_Weights_Analysis": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_weights_analysis",
                True,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_Skfolio_Optimization": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_skfolio_optimization",
                False,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_OptimalPortfolios_Optimization": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_optimalportfolios_optimization",
                False,
            ),
            "Input_Tab_Results_Subtab_Reporting_Include_Simulation": (
                "input_ID_tab_results_subtab_reporting_checkbox_include_simulation",
                True,
            ),
        }
        for reactive_key, (input_id, default_value) in flag_map.items():
            try:
                flag_value = getattr(input, input_id)()
                reactive_value = user_inputs.get(reactive_key)
                if reactive_value is not None and hasattr(reactive_value, "set"):
                    reactive_value.set(coerce_reporting_flag_or_default(raw_value=flag_value, default_value=default_value))
            except Exception:
                pass

    @reactive_module.effect
    @reactive_module.event(input.input_ID_tab_portfolios_subtab_reporting_btn_generate_pdf)
    async def observer_generate_pdf_report() -> None:
        """Handle PDF report generation for the reporting subtab (async, non-blocking).

        The observer is ``async`` so that ``await asyncio.sleep(0)`` yields
        control to the Shiny event loop after each progress update, allowing
        the progress bar to render in real-time rather than only after the
        entire generation completes.  The Typst compilation is dispatched via
        :func:`asyncio.to_thread` to avoid blocking the event loop during the
        longest-running step.
        """
        temp_directory: str = ""
        try:
            generated_pdf_path.set(None)
            pdf_generation_in_progress.set(True)
            pdf_generation_step_total.set(pdf_generation_total_steps)
            set_pdf_progress(
                progress_pct = 5,
                progress_label = "Preparing generation workflow",
                step_current=1,
                step_total=pdf_generation_total_steps,
            )
            set_pdf_status(message = "⏳ Generating PDF report...")
            logger.info("QWIM TYPST PDF REPORT GENERATION (CLOUD)")
            set_pdf_progress(progress_pct = 8, progress_label = "Checking Typst runtime availability", step_current=2)
            await asyncio.sleep(0)  # flush progress to client

            if not typst_available:
                error_message = "Typst runtime not available. Please check installation."
                logger.error("PDF generation error: %s", error_message)
                show_error_notification_internal(message = error_message)
                return

            report_title = input.input_ID_tab_portfolios_subtab_reporting_text_report_title()
            if not report_title or len(report_title.strip()) < 3:
                report_title = "QWIM Report"
                logger.debug("Using default report title: %s", report_title)
            else:
                logger.debug("User-specified report title: %s", report_title)
            set_pdf_progress(progress_pct = 14, progress_label = "Validating report title and output filename", step_current=3)

            user_filename = input.input_ID_tab_portfolios_subtab_reporting_text_download_filename()
            if not user_filename or len(user_filename.strip()) == 0:
                current_date_string = datetime.datetime.now(UTC).strftime("%Y%m%d")
                user_filename = f"Report-QWIM-{current_date_string}.pdf"
                logger.debug("Using default filename: %s", user_filename)

            is_valid_filename, sanitized_filename, validation_message = (
                sanitize_filename_for_security(filename = user_filename)
            )
            if not is_valid_filename:
                error_message = f"Invalid filename: {validation_message}"
                logger.error("PDF generation error: %s", error_message)
                show_error_notification_internal(message = error_message)
                return

            logger.debug("Sanitized filename: %s", sanitized_filename)
            set_pdf_progress(progress_pct = 18, progress_label = "Validating inputs and preparing report settings", step_current=3)
            await asyncio.sleep(0)  # flush progress to client

            user_id = get_user_id_from_session()
            include_advisor_info = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_advisor_info(),
                default_value=True,
            )
            include_portfolio_analysis = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_analysis(),
                default_value=True,
            )
            include_portfolio_comparison = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_portfolio_comparison(),
                default_value=True,
            )
            include_weights_analysis = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_weights_analysis(),
                default_value=True,
            )
            include_skfolio_optimization = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_skfolio_optimization(),
                default_value=False,
            )
            include_optimalportfolios_optimization = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_optimalportfolios_optimization(),
                default_value=False,
            )
            include_simulation = coerce_reporting_flag_or_default(raw_value=input.input_ID_tab_results_subtab_reporting_checkbox_include_simulation(),
                default_value=True,
            )
            include_charts = any(
                [
                    include_portfolio_analysis,
                    include_portfolio_comparison,
                    include_weights_analysis,
                    include_skfolio_optimization,
                    include_optimalportfolios_optimization,
                    include_simulation,
                ],
            )
            chart_resolution = (
                input.input_ID_tab_portfolios_subtab_reporting_select_chart_resolution()
            )

            typst_source_path = (
                Path(module_file_path).resolve().parent.parent / "reporting" / "report_QWIM.typ"
            )
            if not typst_source_path.exists():
                error_message = f"Typst source file not found: {typst_source_path}"
                logger.error("PDF generation error: %s", error_message)
                show_error_notification_internal(message = error_message)
                return

            temp_directory = create_secure_temp_directory()
            set_pdf_progress(progress_pct = 24, progress_label = "Created secure temporary workspace", step_current=4)

            temp_typst_path = Path(temp_directory) / "report_QWIM.typ"
            output_pdf_path = Path(temp_directory) / sanitized_filename
            logger.debug(
                "Typst config — Title: %s, User: %s, File: %s, Charts: %s, Res: %s",
                report_title,
                user_id,
                sanitized_filename,
                include_charts,
                chart_resolution,
            )

            show_info_notification_internal(
                message = "Exporting report data and charts from dashboard... Please wait.",
            )
            set_pdf_progress(progress_pct = 30, progress_label = "Exporting report JSON data", step_current=5)

            try:
                export_all_report_data(reactives_shiny = reactives_shiny)
                logger.debug("Exported all report JSON data files")
            except Exception as data_export_error:
                logger.warning(
                    "JSON data export failed (continuing with any existing files): %s",
                    data_export_error,
                )
                logger.warning("JSON data export warning: %s", data_export_error)

            try:
                section_flags = {
                    "include_advisor_info": include_advisor_info,
                    "include_portfolio_analysis": include_portfolio_analysis,
                    "include_portfolio_comparison": include_portfolio_comparison,
                    "include_weights_analysis": include_weights_analysis,
                    "include_skfolio_optimization": include_skfolio_optimization,
                    "include_optimalportfolios_optimization": include_optimalportfolios_optimization,
                    "include_simulation": include_simulation,
                }
                export_report_config(reactives_shiny = reactives_shiny, section_flags = section_flags, report_title = report_title)
                logger.debug("Exported report_config.json with section flags")
            except Exception as config_export_error:
                logger.warning(
                    "report_config.json export failed (continuing): %s",
                    config_export_error,
                )
                logger.warning("report_config.json export warning: %s", config_export_error)

            set_pdf_progress(progress_pct = 40, progress_label = "JSON export completed", step_current=5)
            await asyncio.sleep(0)  # flush progress to client
            set_pdf_progress(progress_pct = 46, progress_label = "Exporting chart files", step_current=6)

            if include_charts:
                try:
                    export_all_report_plots(reactives_shiny = reactives_shiny)
                    logger.debug("Exported plotnine fallback SVG charts")
                except Exception as plot_export_error:
                    logger.warning(
                        "Plotnine chart export failed (continuing): %s",
                        plot_export_error,
                    )
                    logger.warning("Plotnine chart export warning: %s", plot_export_error)
            else:
                logger.debug("Chart export disabled by user input")

            set_pdf_progress(progress_pct = 54, progress_label = "Exporting live dashboard visuals", step_current=7)
            logger.info("Exporting live chart SVGs for report pipeline")
            export_visual_objects_to_svg(reactives_shiny = reactives_shiny)
            await asyncio.sleep(0)  # flush progress to client

            set_pdf_progress(progress_pct = 62, progress_label = "Verifying report image assets", step_current=8)
            svg_status = ensure_all_svg_files_exist()
            placeholder_charts = [
                key.replace("_", " ").title()
                for key, status in svg_status.items()
                if status == "placeholder"
            ]
            data_issues = validate_report_data_quality()
            set_pdf_progress(progress_pct = 70, progress_label = "Running report data quality checks", step_current=9)

            warning_lines: list[str] = []
            if placeholder_charts:
                warning_lines.append(
                    "Charts unavailable (placeholder used): " + ", ".join(placeholder_charts),
                )
            warning_lines.extend(
                f"{section_name}: {issue_text}"
                for section_name, section_issues in data_issues.items()
                for issue_text in section_issues
            )

            if warning_lines:
                combined_warning = (
                    "⚠️ Report data quality warnings:\n• "
                    + "\n• ".join(warning_lines)
                    + "\n\nThe PDF will be generated with placeholder content for "
                    "missing items. To remove placeholders, go back to the "
                    "relevant dashboard tabs and ensure charts/tables display "
                    "valid data, then regenerate the report."
                )
                logger.warning("Report data quality warnings: %s", combined_warning)
                try:
                    warning_body: list[Any] = [
                        ui_module.p(
                            ui_module.strong(
                                "Some report sections have missing or incomplete data:",
                            ),
                            style="color: #b45309; font-size: 1.05em;",
                        ),
                    ]
                    warning_body.extend(
                        ui_module.p(f"• {warning_line}", style="margin: 0.2em 0;")
                        for warning_line in warning_lines
                    )
                    warning_body.append(
                        ui_module.p(
                            ui_module.em(
                                "The PDF will still be generated with placeholder content. "
                                "To remove placeholders, go back to the relevant dashboard "
                                "tabs and ensure charts/tables display valid data, then "
                                "regenerate the report.",
                            ),
                            style="margin-top: 1em; color: #374151;",
                        ),
                    )
                    warn_modal = ui_module.modal(
                        *warning_body,
                        title="⚠️ Report Data Quality Warnings",
                        easy_close=True,
                        footer=ui_module.modal_button("Continue Anyway", class_="btn-warning"),
                    )
                    ui_module.modal_show(warn_modal)
                except Exception:
                    show_info_notification_internal(message = combined_warning)
            set_pdf_progress(progress_pct = 74, progress_label = "Data quality pre-flight completed", step_current=9)
            await asyncio.sleep(0)  # flush progress to client

            template_directory = str(typst_source_path.parent)
            set_pdf_progress(progress_pct = 80, progress_label = "Copying Typst dependencies", step_current=10)
            copy_typst_dependencies_to_temp_directory(template_directory = template_directory, temp_directory = temp_directory)

            shutil.copy2(str(typst_source_path), str(temp_typst_path))
            logger.debug("Copied Typst template to: %s", temp_typst_path)
            set_pdf_progress(progress_pct = 86, progress_label = "Preparing Typst compilation", step_current=10)

            show_info_notification_internal(message = "Compiling Typst report to PDF... Please wait.")
            set_pdf_progress(progress_pct = 92, progress_label = "Compiling PDF with Typst", step_current=11)
            await asyncio.sleep(0)  # flush progress to client before long-running compilation

            # Dispatch Typst compilation to a thread so the Shiny event loop
            # stays responsive and can continue flushing progress updates.
            try:
                compilation_success, compilation_message = await asyncio.to_thread(
                    compile_typst_report_to_pdf,
                    typst_file_path=str(temp_typst_path),
                    output_pdf_path=str(output_pdf_path),
                )
            except Exception as compilation_error:
                error_message = f"Error during Typst compilation: {compilation_error}"
                logger.error("PDF generation error: %s", error_message)
                show_error_notification_internal(message = error_message)
                cleanup_temp_files(temp_directory = temp_directory)
                return

            if compilation_success and output_pdf_path.exists():
                file_size = output_pdf_path.stat().st_size
                success_message_display = (
                    "Typst PDF report generated successfully! Ready for download: "
                    f"{sanitized_filename}"
                )
                logger.info("PDF report success: %s", success_message_display)
                logger.debug("File path: %s", output_pdf_path)
                logger.debug("Status: %s", compilation_message)
                logger.debug("File size: %d bytes", file_size)

                generated_pdf_path.set(str(output_pdf_path))
                set_pdf_progress(progress_pct = 100, progress_label = "PDF generation completed successfully", step_current=12)
                set_pdf_status(message = f"✅ Report generated successfully: {sanitized_filename}")
                show_success_notification_internal(message = "Typst PDF report ready for download!")

                async def _delayed_cleanup_async() -> None:
                    """Wait 5 minutes then remove the temporary PDF directory."""
                    await asyncio.sleep(300)
                    cleanup_temp_files(temp_directory = temp_directory)

                _ = asyncio.create_task(_delayed_cleanup_async())
            else:
                hint_lines: list[str] = [f"Typst PDF compilation failed: {compilation_message}"]
                if placeholder_charts:
                    hint_lines.append(
                        "Charts with placeholder SVGs: " + ", ".join(placeholder_charts),
                    )
                if data_issues:
                    hint_lines.extend(
                        f"  {section_name}: {issue_text}"
                        for section_name, issue_texts in data_issues.items()
                        for issue_text in issue_texts
                    )
                hint_lines.append(
                    "Go back to the relevant dashboard tabs and ensure all charts and tables display valid data, then regenerate the report.",
                )
                error_message = "\n".join(hint_lines)
                logger.error("PDF generation error: %s", error_message)
                set_pdf_progress(progress_pct = 100, progress_label = "PDF generation failed", step_current=12)
                show_error_notification_internal(message = error_message)
                cleanup_temp_files(temp_directory = temp_directory)
        except Exception as exc_error:
            error_message = f"PDF report generation observer error: {exc_error}"
            logger.error("PDF generation error: %s", error_message)
            set_pdf_progress(progress_pct = 100, progress_label = "PDF generation failed", step_current=12)
            show_error_notification_internal(message = error_message)
            with contextlib.suppress(BaseException):
                cleanup_temp_files(temp_directory = temp_directory)
        finally:
            pdf_generation_in_progress.set(False)