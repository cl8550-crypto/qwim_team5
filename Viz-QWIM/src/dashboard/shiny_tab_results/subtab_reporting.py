"""PDF Report Generation Module for QWIM Dashboard.

Provides PDF report generation functionality using report_QWIM.py and the
Typst report_QWIM.typ template.  Generates comprehensive reports with
portfolio analysis and investor information.

Features
--------
* User-specified filename with secure file download
* Secure file path sanitization for cloud deployment
* Default save to outputs/reports folder with default filename pattern
* Professional PDF reports via Typst typesetting system
* Integration with reactives_shiny data structure
* Dynamic data integration from dashboard inputs
* Polars DataFrames support (Data_Personal_Info_DF, Data_Assets_DF,
  Data_Goals_DF, Data_Income_DF)

Security Features
-----------------
* Path sanitization to prevent directory traversal attacks
* Filename validation to prevent malicious file operations
* Secure temporary file handling for cloud environments
* Download-based file delivery for Posit Connect Cloud

Dependencies
-----------
* shiny: UI framework
* report_QWIM: Custom PDF generation module (Typst pipeline)
* typst: Typst compilation system
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
import tempfile
import typing

from datetime import UTC
from pathlib import Path
from typing import Any

from shiny import module, reactive, render, ui

from src.dashboard.shiny_tab_results._subtab_reporting_ui_helpers import (
    build_subtab_reporting_ui_impl_QWIM,
    create_typst_report_with_data_impl_QWIM,
    show_error_notification_internal_impl_QWIM,
    show_info_notification_internal_impl_QWIM,
    show_success_notification_internal_impl_QWIM,
)
from src.dashboard.shiny_tab_results._subtab_reporting_server_bindings import (
    register_subtab_reporting_server_bindings_impl_QWIM,
)
from src.utils.typst_utils import (
    compile_typst_document_to_pdf_QWIM,
    resolve_typst_executable_path_QWIM,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


#: Module-level logger instance
_logger = get_logger(name = __name__)


def _coerce_pdf_progress_int_or_default(
    *, raw_value: Any, default_value: int) -> int:
    """Convert PDF progress counters to ``int`` while rejecting booleans."""
    if raw_value is None or isinstance(raw_value, bool):
        return default_value

    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default_value


def _format_currency_for_typst(*, amount: Any) -> str:
    """Format Typst currency substitutions while rejecting boolean inputs."""
    if amount is None or isinstance(amount, bool):
        return "\\$0"

    try:
        return f"\\${float(amount):,.0f}"
    except (ValueError, TypeError):
        return "\\$0"


def _coerce_reporting_flag_or_default(
    *, raw_value: Any, default_value: bool) -> bool:
    """Return a reporting include-flag while rejecting non-boolean inputs."""
    if isinstance(raw_value, bool):
        return raw_value

    return default_value


# Import PDF report generation module
try:
    from src.dashboard.reporting.report_QWIM import generate_report_PDF  # noqa: F401

    REPORT_QWIM_AVAILABLE = True
    _logger.info("report_QWIM module imported successfully")
except ImportError as import_error:  # pragma: no cover
    _logger.warning("report_QWIM module import failed: %s", import_error)
    REPORT_QWIM_AVAILABLE = False

# Import Typst compilation functionality
try:
    import typst as _typst

    _logger.info("typst module imported successfully")
except ImportError as import_error:  # pragma: no cover
    _logger.warning("typst module import failed: %s", import_error)
    _typst = None

_TYPST_MODULE = _typst
_TYPST_CLI_PATH = resolve_typst_executable_path_QWIM()
TYPST_AVAILABLE = _TYPST_MODULE is not None or _TYPST_CLI_PATH is not None

if _TYPST_MODULE is None and _TYPST_CLI_PATH is not None:
    _logger.info("typst CLI discovered at: %s", _TYPST_CLI_PATH)

# Import data access utilities
try:
    from src.dashboard.reporting.report_data_export import (
        export_all_report_data,
        export_report_config,
        validate_report_data_quality,
    )
    from src.dashboard.reporting.report_plot_export import (
        ensure_all_svg_files_exist,
        export_all_report_plots,
    )
    from src.dashboard.shiny_utils.reactives_shiny import get_value_from_reactives_shiny
    from src.dashboard.shiny_utils.utils_reporting import export_visual_objects_to_svg
    from src.dashboard.shiny_utils.utils_tab_clients import get_investor_data_from_dashboard

    DATA_UTILS_AVAILABLE = True
    _logger.info("reactives_shiny and utils_tab_clients utilities imported successfully")
except ImportError as import_error:  # pragma: no cover
    _logger.warning("Data utilities import failed: %s", import_error)
    DATA_UTILS_AVAILABLE = False

    def export_all_report_data(
        *, reactives_shiny: typing.Any) -> dict:  # type: ignore[misc]
        """Fallback: report data export unavailable."""
        _logger.warning("Fallback: export_all_report_data not available")
        return {}

    def export_report_config(
        *, reactives_shiny: typing.Any, section_flags: dict, report_title: str = "") -> None:  # type: ignore[misc]
        """Fallback: report_config.json export unavailable."""
        _logger.warning("Fallback: export_report_config not available")

    def export_all_report_plots(
        *, reactives_shiny: typing.Any) -> dict:  # type: ignore[misc]
        """Fallback: report plot export unavailable."""
        _logger.warning("Fallback: export_all_report_plots not available")
        return {}

    def export_visual_objects_to_svg(
        *, reactives_shiny: typing.Any, output_dir: typing.Any = None) -> dict:  # type: ignore[misc]
        """Fallback: SVG export unavailable."""
        _logger.warning("Fallback: export_visual_objects_to_svg not available")
        return {}

    def validate_report_data_quality() -> dict:  # type: ignore[misc]
        """Fallback: data quality validation unavailable."""
        return {}

    def ensure_all_svg_files_exist() -> dict:  # type: ignore[misc]
        """Fallback: SVG existence check unavailable."""
        return {}

    # Fallback function for defensive programming
    def get_value_from_reactives_shiny(
        *, reactives_shiny: dict, key_name: str, key_category: str) -> typing.Any | None:
        """
        Fallback function when reactives_shiny utilities are not available.

        Args:
            reactives_shiny (dict): Reactive values structure
            key_name (str): Key name to retrieve
            key_category (str): Key category

        Returns
        -------
            Optional[typing.Any]: None as fallback
        """
        _logger.warning("Fallback: Unable to retrieve %s from %s", key_name, key_category)
        return None

    def get_investor_data_from_dashboard(
        *, reactives_shiny: dict) -> tuple[dict, dict, dict, dict]:
        """
        Fallback function when utils_tab_investors is not available.

        Args:
            reactives_shiny (dict): Reactive values structure

        Returns
        -------
            Tuple[dict, dict, dict, dict]: Fallback data structures with realistic values
        """
        _logger.warning(
            "Fallback: utils_tab_investors not available, generating fallback investor data",
        )

        # Generate realistic fallback data for demonstration purposes
        fallback_personal_info = {
            "primary": {
                "name": "Primary Investor",
                "age_current": 35,
                "age_retirement": 65,
                "age_income_starting": 67,
                "status_marital": "Married",
                "gender": "Not Specified",
                "tolerance_risk": "Moderate",
                "state": "Not Specified",
                "code_zip": "00000",
            },
            "partner": {
                "name": "Partner Investor",
                "age_current": 33,
                "age_retirement": 65,
                "age_income_starting": 67,
                "status_marital": "Married",
                "gender": "Not Specified",
                "tolerance_risk": "Moderate",
                "state": "Not Specified",
                "code_zip": "00000",
            },
        }

        fallback_assets_data = {
            "primary": {
                "taxable": 100000.0,
                "tax_deferred": 200000.0,
                "tax_free": 50000.0,
                "total": 350000.0,
            },
            "partner": {
                "taxable": 75000.0,
                "tax_deferred": 150000.0,
                "tax_free": 25000.0,
                "total": 250000.0,
            },
            "combined": {
                "taxable": 175000.0,
                "tax_deferred": 350000.0,
                "tax_free": 75000.0,
                "total": 600000.0,
            },
        }

        fallback_goals_data = {
            "primary": {
                "essential": 50000.0,
                "important": 25000.0,
                "aspirational": 15000.0,
                "total": 90000.0,
            },
            "partner": {
                "essential": 45000.0,
                "important": 20000.0,
                "aspirational": 10000.0,
                "total": 75000.0,
            },
            "combined": {
                "essential": 95000.0,
                "important": 45000.0,
                "aspirational": 25000.0,
                "total": 165000.0,
            },
        }

        fallback_income_data = {
            "primary": {
                "social_security": 30000.0,
                "pension": 25000.0,
                "annuity_existing": 15000.0,
                "other": 10000.0,
                "total": 80000.0,
            },
            "partner": {
                "social_security": 25000.0,
                "pension": 20000.0,
                "annuity_existing": 10000.0,
                "other": 5000.0,
                "total": 60000.0,
            },
            "combined": {
                "social_security": 55000.0,
                "pension": 45000.0,
                "annuity_existing": 25000.0,
                "other": 15000.0,
                "total": 140000.0,
            },
        }

        _logger.debug("Generated comprehensive fallback investor data successfully")
        return (
            fallback_personal_info,
            fallback_assets_data,
            fallback_goals_data,
            fallback_income_data,
        )


# Security constants for file path validation
ALLOWED_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._\-\s()]+\.pdf$")
MAX_FILENAME_LENGTH = 200
FORBIDDEN_FILENAME_PARTS = [
    "..",
    "./",
    "\\",
    "//",
    "~",
    "$",
    "%",
    "&",
    "*",
    "?",
    "<",
    ">",
    "|",
    '"',
    "'",
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
]


# ---------------------------------------------------------------------------
# Module-level utility functions (pure helpers, no Shiny context needed)
# ---------------------------------------------------------------------------


def _compile_typst_report_to_pdf_QWIM(
    *, typst_file_path: str | Path, output_pdf_path: str | Path) -> tuple[bool, str]:
    """Compile a Typst report to PDF using the shared Typst utility.

    Parameters
    ----------
    typst_file_path : str | pathlib.Path
        Path to the Typst source file.
    output_pdf_path : str | pathlib.Path
        Path where the compiled PDF should be written.

    Returns
    -------
    tuple[bool, str]
        Success flag and status message.
    """
    try:
        typst_source_path = Path(typst_file_path)
        output_pdf = Path(output_pdf_path)

        if not typst_source_path.exists():
            return False, f"Typst source file not found: {typst_source_path}"

        if not TYPST_AVAILABLE:
            return False, "Typst runtime not available for compilation"

        return compile_typst_document_to_pdf_QWIM(
            typst_file_path = typst_source_path,
            output_pdf_path = output_pdf,
            _typst_module=_TYPST_MODULE,
        )
    except Exception as compilation_error:
        return False, f"Typst compilation error: {compilation_error}"


def sanitize_filename_for_security(
    *, filename: str) -> tuple[bool, str, str]:
    """Sanitize filename for security following QWIM standards.

    Parameters
    ----------
    filename : str
        User-provided filename to sanitize.

    Returns
    -------
    tuple[bool, str, str]
        ``(is_valid, sanitized_filename, error_message)``
    """
    # Input validation with early returns
    if not filename or len(filename.strip()) == 0:
        return False, "", "Filename cannot be empty"

    Original_Filename = filename.strip()

    # Configuration validation - check length
    if len(Original_Filename) > MAX_FILENAME_LENGTH:
        return False, "", f"Filename too long (maximum {MAX_FILENAME_LENGTH} characters)"

    if len(Original_Filename) < 5:  # Minimum: "a.pdf"
        return False, "", "Filename too short (minimum 5 characters including .pdf)"

    # Business logic validation - check extension
    if not Original_Filename.lower().endswith(".pdf"):
        return False, "", "Filename must end with .pdf extension"

    # Defensive programming - check for forbidden patterns
    Filename_Upper = Original_Filename.upper()
    for Forbidden_Part in FORBIDDEN_FILENAME_PARTS:
        if Forbidden_Part in Filename_Upper:
            return False, "", f"Filename contains forbidden pattern: {Forbidden_Part}"

    # Security validation - check against allowed pattern
    if not ALLOWED_FILENAME_PATTERN.match(Original_Filename):  # pragma: no cover
        return (
            False,
            "",
            "Filename contains invalid characters. Only letters, numbers, spaces, dots, hyphens, underscores and parentheses allowed",
        )

    # Additional security checks
    if Original_Filename.startswith((".", "-")):
        return False, "", "Filename cannot start with dot or hyphen"

    if ".." in Original_Filename:  # pragma: no cover
        return False, "", "Filename cannot contain double dots"

    # Create sanitized version
    Sanitized_Filename = re.sub(r"[^\w\s.\-()]+", "", Original_Filename)
    Sanitized_Filename = re.sub(r"\s+", " ", Sanitized_Filename).strip()

    # Ensure it still ends with .pdf after sanitization
    if not Sanitized_Filename.lower().endswith(".pdf"):  # pragma: no cover
        Sanitized_Filename += ".pdf"

    return True, Sanitized_Filename, "Filename is valid and secure"


def create_secure_temp_directory() -> str:
    """Create secure temporary directory for PDF generation.

    Returns
    -------
    str
        Path to secure temporary directory.
    """
    try:
        Temp_Dir = tempfile.mkdtemp(prefix="qwim_reports_", suffix="_secure")

        if not os.path.exists(Temp_Dir):  # pragma: no cover
            raise Exception_Configuration("Failed to create temporary directory")

        if not os.access(Temp_Dir, os.W_OK):  # pragma: no cover
            raise Exception_Configuration("Temporary directory is not writable")

        return Temp_Dir

    except Exception:  # pragma: no cover
        return tempfile.gettempdir()


def cleanup_temp_files(
    *, temp_directory: str) -> None:
    """Clean up temporary files securely.

    Parameters
    ----------
    temp_directory : str
        Temporary directory to clean up.
    """
    try:
        if not temp_directory or not os.path.exists(temp_directory):
            return

        if (
            not temp_directory.startswith(tempfile.gettempdir())
            and "qwim_reports" not in temp_directory
        ):
            return

        shutil.rmtree(temp_directory, ignore_errors=True)

    except Exception:  # pragma: no cover
        pass


@module.ui
def subtab_reporting_ui(  # pragma: no cover
    *, data_utils: dict, data_inputs: dict) -> Any:
    """Create the reporting UI facade."""
    status_flags = {
        "REPORT_QWIM_AVAILABLE": REPORT_QWIM_AVAILABLE,
        "TYPST_AVAILABLE": TYPST_AVAILABLE,
        "DATA_UTILS_AVAILABLE": DATA_UTILS_AVAILABLE,
    }
    return build_subtab_reporting_ui_impl_QWIM(data_utils = status_flags, data_inputs = data_inputs)


@module.server
def subtab_reporting_server(  # pragma: no cover
    input: typing.Any,
    output: typing.Any,
    session: typing.Any,
    data_utils: dict,
    data_inputs: dict,
    reactives_shiny: dict,
) -> None:
    """Server logic for PDF report generation using Typst report_QWIM.typ with secure download delivery."""
    PDF_GENERATION_TOTAL_STEPS = 12

    # Reactive value to store the generated PDF file path
    generated_pdf_path: reactive.Value[str | None] = reactive.Value(None)
    pdf_status_message: reactive.Value[str] = reactive.Value(
        "Ready to generate PDF reports for download",
    )
    initial_pdf_generation_in_progress = False
    pdf_generation_in_progress: reactive.Value[bool] = reactive.Value(
        initial_pdf_generation_in_progress,
    )
    pdf_generation_progress_pct: reactive.Value[int] = reactive.Value(0)
    pdf_generation_progress_label: reactive.Value[str] = reactive.Value("Waiting to start")
    pdf_generation_step_current: reactive.Value[int] = reactive.Value(0)
    pdf_generation_step_total: reactive.Value[int] = reactive.Value(PDF_GENERATION_TOTAL_STEPS)

    def set_pdf_status(*, message: str) -> None:
        """Set PDF status message shown in reporting UI."""
        pdf_status_message.set(message)

    def set_pdf_progress(
        *, progress_pct: int, progress_label: str, step_current: int | None = None, step_total: int | None = None) -> None:
        """Update PDF generation progress values for dashboard progress bar."""
        Safe_Progress = max(0, min(100, _coerce_pdf_progress_int_or_default(raw_value = progress_pct, default_value = 0)))
        pdf_generation_progress_pct.set(Safe_Progress)
        pdf_generation_progress_label.set(progress_label)
        if step_total is not None:
            Safe_Total = max(
                1,
                _coerce_pdf_progress_int_or_default(raw_value = step_total, default_value = PDF_GENERATION_TOTAL_STEPS),
            )
            pdf_generation_step_total.set(Safe_Total)
        if step_current is not None:
            Safe_Current = max(
                0,
                min(
                    _coerce_pdf_progress_int_or_default(raw_value = step_current, default_value = 0),
                    pdf_generation_step_total.get(),
                ),
            )
            pdf_generation_step_current.set(Safe_Current)

    def get_user_id_from_session() -> str:
        """
        Get user ID from Shiny session or generate default following QWIM standards.

        Returns
        -------
            str: User identifier for PDF generation
        """
        try:
            # Configuration validation - try to get user ID from session
            if hasattr(session, "user_id") and session.user_id:
                User_ID = str(session.user_id)
                _logger.debug("User ID from session.user_id: %s", User_ID)
                return User_ID
            if hasattr(session, "get") and callable(session.get):
                Session_User_ID = session.get("user_id")
                if Session_User_ID:
                    User_ID = str(Session_User_ID)
                    _logger.debug("User ID from session.get(): %s", User_ID)
                    return User_ID
            elif hasattr(session, "user") and session.user:
                User_ID = str(session.user)
                _logger.debug("User ID from session.user: %s", User_ID)
                return User_ID

            # Business logic validation - generate default user ID with timestamp
            Timestamp_String = datetime.datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            Default_User_ID = f"qwim_user_{Timestamp_String}"
            _logger.debug("Generated default User ID: %s", Default_User_ID)
            return Default_User_ID

        except Exception as session_error:
            _logger.warning("Session user ID error: %s", session_error)
            # Defensive programming - fallback to timestamp-based ID
            Timestamp_String = datetime.datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            Fallback_User_ID = f"fallback_user_{Timestamp_String}"
            _logger.debug("Fallback User ID: %s", Fallback_User_ID)
            return Fallback_User_ID

    def create_typst_report_with_data(
        *, typst_template_path: str, output_path: str, personal_info_data: dict, assets_data: dict, goals_data: dict, income_data: dict) -> tuple[bool, str]:
        """Create a Typst report by substituting template placeholders."""
        return create_typst_report_with_data_impl_QWIM(
            typst_template_path = typst_template_path,
            output_path = output_path,
            personal_info_data = personal_info_data,
            assets_data = assets_data,
            goals_data = goals_data,
            income_data = income_data,
            reactives_shiny=reactives_shiny,
            get_value_from_reactives_shiny=get_value_from_reactives_shiny,
            coerce_reporting_flag_or_default=_coerce_reporting_flag_or_default,
            format_currency_for_typst=_format_currency_for_typst,
            logger=_logger,
        )

    def copy_typst_dependencies_to_temp_directory(
        *, template_directory: str, temp_directory: str) -> None:
        """
        Copy Typst template dependencies to temporary directory following QWIM standards.

        Args:
            template_directory (str): Source template directory
            temp_directory (str): Target temporary directory
        """
        try:
            # Input validation with early returns
            if not os.path.exists(template_directory):
                _logger.warning("Template directory not found: %s", template_directory)
                return

            if not os.path.exists(temp_directory):
                _logger.warning("Temporary directory not found: %s", temp_directory)
                return

            Template_Dir_Path = Path(template_directory)
            Temp_Dir_Path = Path(temp_directory)

            # Copy consolidated JSON data files required by report_QWIM.typ (R6 structure)
            Root_JSON_Files = [
                "data_clients.json",
                "data_results.json",
                "report_config.json",
                # Legacy files retained for backward compatibility
                "client_info.json",
                "report_metadata.json",
            ]
            for Json_Name in Root_JSON_Files:
                Source_Json = Template_Dir_Path / Json_Name
                if Source_Json.exists():
                    shutil.copy2(Source_Json, Temp_Dir_Path / Json_Name)
                    _logger.debug("Copied JSON data file: %s", Json_Name)
                else:
                    _logger.debug("Optional JSON file not found: %s", Json_Name)

            # Copy JSON subdirectories (legacy, kept for compatibility)
            Json_Subdirs = ["inputs_json", "outputs_json"]
            for Subdir_Name in Json_Subdirs:
                Source_Subdir = Template_Dir_Path / Subdir_Name
                if Source_Subdir.is_dir():
                    Dest_Subdir = Temp_Dir_Path / Subdir_Name
                    Dest_Subdir.mkdir(exist_ok=True)
                    for Json_File in Source_Subdir.iterdir():
                        if Json_File.is_file():
                            shutil.copy2(Json_File, Dest_Subdir / Json_File.name)
                    _logger.debug("Copied JSON subdirectory: %s/", Subdir_Name)
                else:
                    _logger.debug("JSON subdirectory not found: %s/", Subdir_Name)

            # Copy outputs_images subdirectory (SVGs used by report_QWIM.typ)
            Source_Images_Dir = Template_Dir_Path / "outputs_images"
            if Source_Images_Dir.is_dir():
                Dest_Images_Dir = Temp_Dir_Path / "outputs_images"
                Dest_Images_Dir.mkdir(exist_ok=True)
                for Img_File in Source_Images_Dir.iterdir():
                    if Img_File.is_file():
                        shutil.copy2(Img_File, Dest_Images_Dir / Img_File.name)
                _logger.debug("Copied outputs_images/ directory")
            else:
                _logger.debug("outputs_images/ directory not found")

            # Configuration validation - list of root-level file dependencies to copy
            Dependencies_To_Copy = [
                "sample_refs.bib",
                "*.png",
                "*.jpg",
                "*.jpeg",
                # Typst utility modules imported by report_QWIM.typ via relative paths
                # (utils_reporting.typ, utils_colors.typ, utils_fonts.typ, etc.)
                "*.typ",
            ]

            # Business logic validation - copy each dependency type
            for Dependency_Pattern in Dependencies_To_Copy:
                try:
                    if "*" in Dependency_Pattern:
                        # Handle wildcard patterns
                        import glob

                        Pattern_Path = os.path.join(template_directory, Dependency_Pattern)
                        Matching_Files = glob.glob(Pattern_Path)

                        for Source_File in Matching_Files:
                            if os.path.isfile(Source_File):
                                Target_File = os.path.join(
                                    temp_directory,
                                    os.path.basename(Source_File),
                                )
                                shutil.copy2(Source_File, Target_File)
                                _logger.debug(
                                    "Copied dependency: %s",
                                    os.path.basename(Source_File),
                                )
                    else:
                        # Handle specific files
                        Source_File = os.path.join(template_directory, Dependency_Pattern)
                        if os.path.exists(Source_File):
                            Target_File = os.path.join(temp_directory, Dependency_Pattern)
                            shutil.copy2(Source_File, Target_File)
                            _logger.debug("Copied dependency: %s", Dependency_Pattern)
                        else:
                            _logger.debug("Optional dependency not found: %s", Dependency_Pattern)

                            # Create empty .bib file if it's the bibliography
                            if Dependency_Pattern == "sample_refs.bib":
                                Empty_Bib_Path = os.path.join(temp_directory, Dependency_Pattern)
                                with open(Empty_Bib_Path, "w", encoding="utf-8") as empty_bib:
                                    empty_bib.write(
                                        "% Empty bibliography file created automatically\n",
                                    )
                                _logger.debug("Created empty bibliography: %s", Dependency_Pattern)

                except Exception as copy_error:
                    _logger.warning(
                        "Error copying dependency %s: %s",
                        Dependency_Pattern,
                        copy_error,
                    )
                    continue

        except Exception as dependencies_error:
            _logger.warning("Error copying Typst dependencies: %s", dependencies_error)

    def show_info_notification_internal(*, message: str) -> None:
        """Show an informational reporting notification."""
        show_info_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=_logger,
        )

    def show_success_notification_internal(*, message: str) -> None:
        """Show a success reporting notification."""
        show_success_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=_logger,
        )

    def show_error_notification_internal(*, message: str) -> None:
        """Show an error reporting notification."""
        show_error_notification_internal_impl_QWIM(
            message = message,
            set_pdf_status=set_pdf_status,
            logger=_logger,
        )

    def compile_typst_report_to_pdf(
        *, typst_file_path: str, output_pdf_path: str) -> tuple[bool, str]:
        """Compile a Typst report to PDF using the shared Typst utility."""
        return _compile_typst_report_to_pdf_QWIM(
            typst_file_path = typst_file_path,
            output_pdf_path = output_pdf_path,
        )

    register_subtab_reporting_server_bindings_impl_QWIM(
        server_context = {
            "input": input,
            "output": output,
            "reactive_module": reactive,
            "render_module": render,
            "ui_module": ui,
            "generated_pdf_path": generated_pdf_path,
            "pdf_status_message": pdf_status_message,
            "pdf_generation_in_progress": pdf_generation_in_progress,
            "pdf_generation_progress_pct": pdf_generation_progress_pct,
            "pdf_generation_progress_label": pdf_generation_progress_label,
            "pdf_generation_step_current": pdf_generation_step_current,
            "pdf_generation_step_total": pdf_generation_step_total,
            "pdf_generation_total_steps": PDF_GENERATION_TOTAL_STEPS,
            "set_pdf_status": set_pdf_status,
            "set_pdf_progress": set_pdf_progress,
            "get_user_id_from_session": get_user_id_from_session,
            "compile_typst_report_to_pdf": compile_typst_report_to_pdf,
            "sanitize_filename_for_security": sanitize_filename_for_security,
            "create_secure_temp_directory": create_secure_temp_directory,
            "cleanup_temp_files": cleanup_temp_files,
            "copy_typst_dependencies_to_temp_directory": copy_typst_dependencies_to_temp_directory,
            "coerce_reporting_flag_or_default": _coerce_reporting_flag_or_default,
            "typst_available": TYPST_AVAILABLE,
            "reactives_shiny": reactives_shiny,
            "export_all_report_data": export_all_report_data,
            "export_report_config": export_report_config,
            "export_all_report_plots": export_all_report_plots,
            "export_visual_objects_to_svg": export_visual_objects_to_svg,
            "validate_report_data_quality": validate_report_data_quality,
            "ensure_all_svg_files_exist": ensure_all_svg_files_exist,
            "logger": _logger,
            "module_file_path": __file__,
        },
    )
