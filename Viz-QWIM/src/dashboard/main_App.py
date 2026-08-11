# <<<<<<< HEAD
# """Main Shiny application entry point for the QWIM dashboard.

# This module wires shared dashboard data, constructs the root UI, and connects
# the top-level server callbacks for the portfolio, client, product, and results
# tabs. Detailed user documentation belongs in the project docs, while this
# docstring stays concise so the runtime module remains below the repository line
# cap.
# """

# # =============================================================================
# # Standard Library Imports
# # =============================================================================

# from __future__ import annotations

# import contextlib
# import sys  # MUST be first import to enable UTF-8 encoding fix


# # CRITICAL: Force UTF-8 encoding for all I/O on Windows BEFORE any other imports
# # This prevents UnicodeEncodeError when logging special characters (❱, ✓, etc.)
# # Must execute before importing os, platform, or any third-party packages
# if sys.platform == "win32":  # pragma: no cover
#     # Import os here only for environment manipulation
#     import os as _os_for_encoding

#     # Set environment variable for subprocess and future operations
#     _os_for_encoding.environ.setdefault("PYTHONIOENCODING", "utf-8")

#     # Force UTF-8 for default encoding
#     if hasattr(sys, "_enablelegacywindowsfsencoding"):
#         # Disable legacy Windows filesystem encoding
#         sys._enablelegacywindowsfsencoding = lambda: None

#     # Reconfigure all existing standard streams to UTF-8
#     if hasattr(sys.stdout, "reconfigure"):
#         with contextlib.suppress(Exception):
#             sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

#     if hasattr(sys.stderr, "reconfigure"):
#         with contextlib.suppress(Exception):
#             sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

#     if hasattr(sys.stdin, "reconfigure"):
#         with contextlib.suppress(Exception):
#             sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

#     # CRITICAL: Disable tbhandler to prevent UnicodeEncodeError
#     # tbhandler uses rich.console which has encoding issues on Windows
#     # We'll use our custom exception handling instead
#     import io

#     # Store original excepthook before any module can replace it
#     _original_excepthook = sys.excepthook

#     def _utf8_safe_excepthook(  # pragma: no cover
#         *, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
#         """Exception hook that safely handles Unicode characters on Windows."""
#         import traceback

#         try:
#             # Try to format exception with UTF-8 safe output
#             lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
#             message = "".join(lines)
#             # Write to stderr with UTF-8 encoding
#             stderr_utf8 = io.TextIOWrapper(
#                 sys.stderr.buffer,
#                 encoding="utf-8",
#                 errors="replace",
#                 line_buffering=True,
#             )
#             stderr_utf8.write(message)
#             stderr_utf8.flush()
#         except Exception:
#             # Fallback: use original hook
#             try:
#                 _original_excepthook(exc_type, exc_value, exc_traceback)
#             except Exception:
#                 # Last resort: basic error message
#                 _logger.error("Unhandled exception: %s: %s", exc_type.__name__, exc_value)

#     # Install our safe exception hook
#     sys.excepthook = _utf8_safe_excepthook

#     # Prevent tbhandler from replacing our excepthook
#     # Monkey patch sys to make excepthook read-only for tbhandler
#     _sys_setattr = sys.__setattr__  # pyright: ignore[reportAttributeAccessIssue]  # pyrefly: ignore[missing-attribute]

#     def _protected_setattr(*, name: str, value: Any) -> Any:  # pragma: no cover
#         """Block tbhandler from overwriting sys.excepthook; allow all other setattr calls."""
#         # Allow our code to set excepthook, but block tbhandler
#         if name == "excepthook":
#             import inspect

#             frame = inspect.currentframe()
#             if frame and frame.f_back:
#                 caller_file = frame.f_back.f_code.co_filename
#                 # Only allow our code to modify excepthook
#                 if "main_App.py" not in caller_file and "tbhandler" in caller_file:
#                     return None  # Silently ignore tbhandler's attempt
#         return _sys_setattr(name, value)

#     # Apply protection (but only for excepthook attribute)
#     # Note: This is a workaround to prevent tbhandler from taking over

# # Now safe to import other standard library modules
# import os  # Operating system interface
# import platform  # Access to underlying platform's identifying data
# import warnings  # Warning control

# from datetime import UTC, datetime  # Date and time handling
# from pathlib import Path  # Object-oriented filesystem paths
# from typing import Any


# # =============================================================================
# # Warning Suppression
# # =============================================================================
# warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")

# # =============================================================================
# # Third-Party Imports
# # =============================================================================
# import shinyswatch  # Bootstrap themes for Shiny applications

# from shiny import App, reactive, ui


# # =============================================================================
# # Project Path Configuration
# # =============================================================================

# #: Root directory of the QWIM Dashboard project
# #: Determined by navigating up from the current file location
# project_dir = Path(__file__).parent.parent.parent

# # Add project root to Python path for module imports
# # This ensures all internal modules can be imported properly
# if str(project_dir) not in sys.path:  # pragma: no cover
#     sys.path.insert(0, str(project_dir))

# # =============================================================================
# # Custom Logging and Exception Handling
# # =============================================================================

# # Custom logging utilities - using loguru-based logger
# # Custom exception classes following project coding standards
# from src.utils.custom_exceptions_errors_loggers.exception_custom import (
#     Exception_Configuration,
#     Exception_Severity,
#     Capture_Exception,
# )
# from src.utils.custom_exceptions_errors_loggers.logger_custom import (
#     Performance_Timer,
#     get_logger,
#     setup_logging,
# )


# # Initialize logging at module level
# setup_logging(
#     log_level="ERROR",
#     environment=os.environ.get("QWIM_ENVIRONMENT", "development"),
#     log_dir=Path(__file__).parent.parent.parent / "logs",
#     enable_console=True,
#     enable_JSON=True,
# )

# #: Module-level logger instance
# _logger = get_logger(name = __name__)

# # =============================================================================
# # Internal Module Imports - Utility Functions
# # =============================================================================

# # Reactive state management utilities
# from src.dashboard.shiny_utils.reactives_shiny import (
#     initialize_reactives_shiny,
# )

# # Data processing and utility functions
# from src.dashboard.shiny_utils.utils_data import (
#     get_data_inputs,
#     get_data_utils,
# )


# # =============================================================================
# # Configuration and Environment Setup
# # =============================================================================

# #: Application environment type (development or production)
# #: Controls server configuration, debug settings, and deployment options
# #:
# #: - development: Local development with debug mode and auto-reload
# #: - production: Production deployment with optimized settings
# ENVIRONMENT: str = os.environ.get("QWIM_ENVIRONMENT", "development").lower()

# # =============================================================================
# # Data Initialization
# # =============================================================================

# _logger.info(
#     "Initializing QWIM Dashboard data",
#     extra={"environment": ENVIRONMENT, "project_dir": str(project_dir)},
# )

# #: Dictionary containing data utility functions and configurations
# #: Provides access to data processing, validation, and transformation utilities
# data_utils: dict[str, Any] = get_data_utils(project_dir=project_dir)

# #: Dictionary containing all input datasets for the dashboard
# #: Includes portfolio data, benchmark data, weights, and time series information
# data_inputs: dict[str, Any] = get_data_inputs(project_dir=project_dir)

# # Logs directory is created by setup_logging

# # =============================================================================
# # Internal Module Imports - Dashboard Components
# # =============================================================================

# from src.dashboard.shiny_tab_clients.tab_clients import (
#     tab_clients_server,
#     tab_clients_ui,
# )
# from src.dashboard.shiny_tab_goal_based_investing.tab_goal_based_investing import (
#     tab_goal_based_investing_server,
#     tab_goal_based_investing_ui,
# )
# from src.dashboard.shiny_tab_goal_parity.tab_goal_parity import (
#     tab_goal_parity_server,
#     tab_goal_parity_ui,
# )
# from src.dashboard.shiny_tab_overview.tab_overview import (
#     tab_overview_server,
#     tab_overview_ui,
# )
# from src.dashboard.shiny_tab_portfolios.tab_portfolios import (
#     tab_portfolios_server,
#     tab_portfolios_ui,
# )
# from src.dashboard.shiny_tab_products.tab_products import (
#     tab_products_server,
#     tab_products_ui,
# )
# from src.dashboard.shiny_tab_results.tab_results import (
#     tab_results_server,
#     tab_results_ui,
# )
# from src.dashboard.shiny_tab_covariance.tab_covariance import (
#     tab_covariance_server,
#     tab_covariance_ui,
# )
# from src.dashboard.shiny_tab_setup.tab_setup import (
#     tab_setup_server,
#     tab_setup_ui,
# )
# from src.dashboard.shiny_tab_goals.tab_goals import (
#     tab_goals_server,
#     tab_goals_ui,
# )


# _logger.debug("Dashboard components imported successfully")

# # =============================================================================
# # UI Component Functions
# # =============================================================================


# def create_about_modal() -> Any:
#     """
#     Create the About modal dialog with comprehensive application information.

#     This modal provides users with detailed information about the dashboard
#     including features, technology stack, version details, and platform information.

#     ## Modal Content Structure

#     The modal is organized into the following sections:

#     1. **Features**: Core dashboard capabilities and functionality
#     2. **Technology Stack**: Technical components and frameworks used
#     3. **Supported Analysis**: Types of analysis available
#     4. **Version Information**: Technical details about the current deployment

#     ## Returns

#     Returns
#     -------
#         shiny.ui.modal: Configured modal dialog component with comprehensive
#         application information formatted using Bootstrap styling.

#     ## Usage Example

#     ```python
#     # Create and display the modal
#     about_modal = create_about_modal()
#     ui.modal_show(about_modal)
#     ```

#     ## Modal Features

#     - **Responsive Design**: Adapts to different screen sizes
#     - **Easy Close**: Can be dismissed by clicking outside or close button
#     - **Rich Content**: Includes lists, formatted text, and highlighted sections
#     - **Version Info**: Dynamic version and platform information

#     ## Styling

#     Uses Bootstrap classes for consistent appearance:
#     - `bg-light`: Light background for version information section
#     - `p-3`: Padding for content spacing
#     - `rounded`: Rounded corners for modern appearance
#     - `btn-primary`: Primary button styling for close button

#     ## Notes

#     !!! info "Dynamic Content"
#         Version information is generated dynamically based on the current
#         Python environment and platform, ensuring accuracy across deployments.

#     !!! tip "Customization"
#         The modal content can be easily modified to include additional
#         sections or updated feature descriptions as the dashboard evolves.
#     """
#     return ui.modal(
#         # Modal header with application title
#         ui.h3("About QWIM Dashboard"),
#         ui.p(
#             "The QWIM Dashboard is a comprehensive time series analysis tool built with Python and Shiny.",
#         ),
#         # Features section highlighting core capabilities
#         ui.h5("🚀 Features:"),
#         ui.tags.ul(
#             ui.tags.li("Interactive time series visualization with multiple chart types"),
#             ui.tags.li("Dynamic ETF component selection and filtering"),
#             ui.tags.li("Statistical analysis and portfolio weight distribution"),
#             ui.tags.li("Real-time reactive updates and synchronization"),
#             ui.tags.li("Customizable time period selection and analysis"),
#             ui.tags.li("Export capabilities for plots and statistical tables"),
#         ),
#         # Technology stack section with technical details
#         ui.h5("🛠️ Technology Stack:"),
#         ui.tags.ul(
#             ui.tags.li("Python 3.12+ for core functionality"),
#             ui.tags.li("Shiny for Python for interactive dashboard framework"),
#             ui.tags.li("Plotly for interactive and responsive visualizations"),
#             ui.tags.li("Polars for high-performance time series processing"),
#             ui.tags.li("NumPy and Pandas for numerical computations"),
#             ui.tags.li("Bootstrap themes via shinyswatch for responsive design"),
#         ),
#         # Analysis capabilities section
#         ui.h5("📊 Supported Analysis:"),
#         ui.tags.ul(
#             ui.tags.li("Portfolio weight distribution over time"),
#             ui.tags.li("Component-wise statistical analysis"),
#             ui.tags.li("Time period filtering and comparison"),
#             ui.tags.li("Multiple visualization formats (area, line, bar, heatmap)"),
#         ),
#         # Dynamic version information section
#         ui.h5("ℹ️ Version Information:"),
#         ui.div(
#             ui.p("**Dashboard Version:** 0.5.1"),
#             ui.p(f"**Python Version:** {platform.python_version()}"),
#             ui.p(f"**Platform:** {platform.system()} {platform.release()}"),
#             ui.p(f"**Environment:** {ENVIRONMENT.title()}"),
#             class_="bg-light p-3 rounded",  # Bootstrap styling for highlighted section
#         ),
#         # Footer with generation timestamp
#         ui.hr(),
#         ui.p(ui.tags.small(f"Generated on: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")),
#         # Modal configuration
#         title="About QWIM Dashboard",
#         size="l",  # Large modal size for comprehensive content
#         easy_close=True,  # Allow closing by clicking outside modal
#         footer=ui.modal_button("Close", class_="btn-primary"),
#     )


# #: Pre-created About modal instance for consistent presentation
# #: Avoids recreating the modal on each display request
# about_modal = create_about_modal()


# def create_app_ui() -> Any:
#     """
#     Create the main application user interface.

#     This function defines the primary UI layout using a navbar-based design
#     that provides intuitive navigation and professional appearance.

#     ## UI Architecture

#     The interface follows a hierarchical structure:

#     ```
#     page_navbar (main container)
#     ├── nav_panel (QWIM Portfolios tab)
#     │   └── tab_portfolios_ui (portfolio analysis interface)
#     ├── nav_spacer (flexible spacing)
#     └── nav_control (About button)
#     ```

#     ## Layout Components

#     ### Main Navigation
#     - **Portfolio Tab**: Primary functionality for portfolio analysis
#     - **About Button**: Access to application information and help

#     ### Theme and Styling
#     - **Flatly Theme**: Modern, professional Bootstrap theme via shinyswatch
#     - **Responsive Design**: Adapts to different screen sizes and devices
#     - **Fillable Layout**: Optimizes space usage for data visualization

#     ## Returns

#     Returns
#     -------
#         shiny.ui.page_navbar: Main application UI layout configured with
#         portfolio analysis functionality and navigation components.

#     ## Configuration Details

#     ### Navbar Settings
#     - `title`: Application branding displayed in navigation bar
#     - `theme`: Bootstrap theme for consistent visual appearance
#     - `fillable`: Enables responsive layout optimization
#     - `id`: Unique identifier for reactive navigation tracking

#     ### Component IDs
#     Following project naming conventions:
#     - `ID_tab_portfolios`: Main portfolio analysis tab
#     - `input_ID_show_about`: About button for modal display
#     - `input_ID_navbar_main`: Navigation bar for tab tracking

#     ## Usage Example

#     ```python
#     # Create the main UI
#     app_ui = create_app_ui()

#     # Use in Shiny app
#     app = App(app_ui, app_server)
#     ```

#     ## Extensibility

#     To add new tabs to the dashboard:

#     ```python
#     # Add additional nav_panel entries before nav_spacer
#     (
#         ui.nav_panel(
#             "New Tab Name", new_tab_ui("ID_new_tab", data_utils=data_utils, data_inputs=data_inputs)
#         ),
#     )
#     ```

#     ## Notes

#     !!! info "Theme Selection"
#         The Flatly theme provides a modern, professional appearance suitable
#         for financial and analytical applications.

#     !!! tip "Navigation Pattern"
#         The nav_spacer() pushes the About button to the right side of the
#         navigation bar, following standard web design patterns.

#     !!! warning "ID Conventions"
#         All component IDs follow the project naming standards with descriptive
#         prefixes (input_, output_, ID_) for consistency and maintainability.
#     """
#     return ui.page_navbar(
#         ui.nav_panel(
#             "Overview",
#             tab_overview_ui(
#                 "ID_tab_overview",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),
#         ),
#         ui.nav_panel(
#             "Setup",
#             tab_setup_ui(
#                 "ID_tab_setup",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),
#         ),
#         ui.nav_panel(
#             "Clients",
#             tab_clients_ui(
#                 "ID_tab_clients",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),  # Input datasets for clients
#         ),
#         ui.nav_panel(
#             "Goal-Based Investing",
#             tab_goal_based_investing_ui(
#                 "ID_tab_goal_based_investing",
#                 data_utils=data_utils,
#                 data_inputs=data_inputs,
#             ),
#         ),
#         # portfolio analysis tab
#         ui.nav_panel(
#             "Portfolios",
#             tab_portfolios_ui(
#                 "ID_tab_portfolios",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),  # Input datasets for analysis
#         ),
#         # 2. In create_app_ui(), after the Portfolios nav_panel:
#         ui.nav_panel(
#             " Personalized Goals Investing",
#             tab_goals_ui(
#                 "ID_tab_goals",
#                 data_utils=data_utils,
#                 data_inputs=data_inputs,
#             ),
#         ),
#         # Products tab (annuities, insurance, etc.)
#         ui.nav_panel(
#             "Products",
#             tab_products_ui(
#                 "ID_tab_products",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),  # Input datasets for product analysis
#         ),
#         # Goal Parity tab (individual model: LLM-profiled goal-based allocation)
#         ui.nav_panel(
#             "Goal Parity",
#             tab_goal_parity_ui(
#                 "ID_tab_goal_parity",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),
#         ),
#         # Results tab (reporting, PDF generation, etc.)
#         ui.nav_panel(
#             "Results",
#             tab_results_ui(
#                 "ID_tab_results",
#                 data_utils=data_utils,  # Utility functions and configuration
#                 data_inputs=data_inputs,
#             ),  # Input datasets for results
#         ),
#         # Navigation spacer to push subsequent elements to the right
#         # Creates proper visual separation between main content and utility buttons
#         ui.nav_panel(
#             "Covariance",
#             tab_covariance_ui(
#                 "ID_tab_covariance",
#                 data_utils=data_utils,
#                 data_inputs=data_inputs,
#             ),
#         ),
#         ui.nav_spacer(),
#         # About button in navigation bar for application information
#         # Provides users with help, features overview, and version details
#         ui.nav_control(
#             ui.input_action_button(
#                 "input_ID_show_about",  # Button identifier following naming convention
#                 "About",  # Button label
#                 class_="btn-outline-light me-2",
#             ),  # Bootstrap styling classes
#         ),
#         # Application-level configuration settings
#         title="QWIM Dashboard",  # Application title displayed in browser and navbar
#         theme=shinyswatch.theme.flatly(),  # Modern Bootstrap theme for professional appearance
#         id="input_ID_navbar_main",  # Unique identifier for reactive navigation tracking
#         fillable=True,  # Enable responsive fillable layout for optimal space usage
#     )


# #: Main application UI instance
# #: Created once for use by the Shiny App constructor
# app_ui = create_app_ui()


# # =============================================================================
# # Server Logic Functions
# # =============================================================================


# def app_server(input: Any, output: Any, session: Any) -> None:  # noqa: A002, ARG001  # pragma: no cover
#     """Coordinate top-level reactive state, modal handling, and tab servers.

#     The server initializes shared dashboard state once, wires the main
#     navigation observers, and delegates each major tab to its module server.
#     """
#     # Initialize reactive values for application state management
#     # This creates the centralized state that coordinates all dashboard modules
#     try:
#         reactives_shiny = initialize_reactives_shiny(data_utils=data_utils)
#     except Exception as exc:
#         # Critical error - dashboard cannot function without reactive state
#         custom_exc = Exception_Configuration(
#             "Failed to initialize reactive values",
#             severity=Exception_Severity.CRITICAL,
#             cause=exc,
#             context={"component": "reactives_shiny"},
#         )
#         custom_exc.Log(
#             logger=_logger,
#             level="error",
#         )
#         raise custom_exc from exc

#     # Initialize navigation tracking reactive value
#     # Defaults to the first available tab for consistent user experience
#     current_tab = reactive.value("QWIM Portfolios")

#     @reactive.effect
#     def observer_track_selected_tab() -> None:
#         """
#         Track and update the currently selected navigation tab.

#         This reactive effect monitors changes to the main navigation bar
#         and updates the `current_tab` reactive value accordingly.

#         ## Functionality

#         - Monitors navigation bar state changes
#         - Updates current_tab reactive value
#         - Enables tab-specific functionality and state management
#         - Provides tab context for conditional logic in modules

#         ## Implementation Details

#         Uses `input.input_ID_navbar_main()` to get the currently selected tab
#         and validates the value before updating the reactive state.

#         ## Usage Example

#         ```python
#         # In other reactive contexts, access current tab
#         active_tab = current_tab()
#         if active_tab == "QWIM Portfolios":
#             # Tab-specific logic
#         ```

#         ## Notes

#         !!! info "Validation"
#             Includes input validation to ensure only valid tab names
#             are set in the reactive value.

#         !!! tip "Extension"
#             When adding new tabs, this function automatically tracks
#             them without modification.
#         """
#         selected_tab = input.input_ID_navbar_main()
#         # Validate that a tab was actually selected before updating
#         if selected_tab:
#             current_tab.set(selected_tab)

#     @reactive.effect
#     @reactive.event(input.input_ID_show_about)
#     def observer_show_about_modal() -> None:
#         """
#         Display the About modal dialog when the About button is clicked.

#         This reactive effect responds specifically to clicks on the About button
#         and displays the modal containing application information.

#         ## Event-Driven Pattern

#         Uses `@reactive.event` decorator to respond only to specific button clicks
#         rather than any input change, ensuring the modal only appears when requested.

#         ## Modal Content

#         Displays the pre-created `about_modal` which includes:
#         - Feature overview and capabilities
#         - Technology stack information
#         - Version and platform details
#         - Usage guidance and support information

#         ## User Experience

#         - Modal appears immediately upon button click
#         - Can be dismissed by clicking outside or using the close button
#         - Provides comprehensive application information in accessible format

#         ## Implementation

#         ```python
#         # Button click → Event trigger → Modal display
#         ui.modal_show(about_modal)
#         ```

#         ## Notes

#         !!! info "Event Specificity"
#             The @reactive.event decorator ensures this function only runs
#             when the specific About button is clicked, not on other input changes.

#         !!! tip "Modal Management"
#             The modal is pre-created for performance and consistency,
#             avoiding recreation on each display request.
#         """
#         ui.modal_show(about_modal)

#     # Initialize overview module server
#     tab_overview_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_overview",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for overview
#         reactives_shiny=reactives_shiny,
#     )

#     # Initialize setup module server
#     tab_setup_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_setup",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for setup
#         reactives_shiny=reactives_shiny,
#     )

#     # Initialize clients module server
#     tab_clients_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_clients",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for portfolio analysis
#         reactives_shiny=reactives_shiny,
#     )  # Centralized reactive state for coordination

#     tab_goal_based_investing_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_goal_based_investing",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
#         data_utils=data_utils,
#         data_inputs=data_inputs,
#         reactives_shiny=reactives_shiny,
#     )

#     # Initialize portfolio analysis module server
#     tab_portfolios_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_portfolios",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for portfolio analysis
#         reactives_shiny=reactives_shiny,
#     )  # Centralized reactive state for coordination

#     # Initialize products module server
#     tab_products_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_products",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for product analysis
#         reactives_shiny=reactives_shiny,
#     )  # Centralized reactive state for coordination

#     # Initialize results module server
#     tab_results_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_results",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets for results
#         reactives_shiny=reactives_shiny,
#     )  # Centralized reactive state for coordination

#     # Initialize Goal Parity module server (individual model tab)
#     tab_goal_parity_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
#         id="ID_tab_goal_parity",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
#         data_utils=data_utils,  # Utility functions and configuration settings
#         data_inputs=data_inputs,  # Input datasets (model loads cleaned_data itself)
#         reactives_shiny=reactives_shiny,
#     )  # Reads Clients-tab inputs for investor profiling

#     tab_goals_server(
#         id="ID_tab_goals",
#         data_utils=data_utils,
#         data_inputs=data_inputs,
#         reactives_shiny=reactives_shiny,
#     )

#     tab_covariance_server(
#         id="ID_tab_covariance",
#         data_utils=data_utils,
#         data_inputs=data_inputs,
#         reactives_shiny=reactives_shiny,
#     )


# def app_factory() -> App:
#     """Create a fresh Shiny application instance from the module UI and server."""
#     return App(create_app_ui(), app_server)


# #: Main Shiny application instance combining UI and server functionality.
# #: Created via :func:`app_factory` to keep instantiation logic in one place.
# app = app_factory()


# # =============================================================================
# # Application Entry Point
# # =============================================================================


# def main() -> None:  # pragma: no cover
#     """Start the dashboard with development or production host and port settings.

#     The runtime configuration is driven by `QWIM_ENVIRONMENT`, with structured
#     logging and guarded shutdown paths for startup failures.
#     """
#     # Display comprehensive startup information for monitoring and debugging
#     _logger.info(
#         "Starting QWIM Dashboard",
#         extra={
#             "environment": ENVIRONMENT,
#             "python_version": platform.python_version(),
#             "platform": f"{platform.system()} {platform.release()}",
#             "project_directory": str(project_dir),
#         },
#     )

#     with Performance_Timer("QWIM Dashboard startup"):
#         host: str = "127.0.0.1"  # default; overridden below
#         port: int = 8080  # default; overridden below
#         try:
#             # Launch application with environment-appropriate configuration
#             if ENVIRONMENT == "production":
#                 # Production configuration optimized for stability and security
#                 host = "0.0.0.0"
#                 port = 8000
#                 _logger.info(
#                     "Production mode",
#                     extra={
#                         "url": f"http://{host}:{port}",
#                         "features": "External access, optimized performance",
#                     },
#                 )
#             else:
#                 # Development configuration optimized for development workflow
#                 host = "127.0.0.1"
#                 port = 8080
#                 _logger.info(
#                     "Development mode",
#                     extra={
#                         "url": f"http://{host}:{port}",
#                         "features": "Stable operation, detailed error messages",
#                     },
#                 )

#             app.run(host=host, port=port, reload=False)

#         except KeyboardInterrupt:
#             _logger.info("Dashboard shutdown requested by user (Ctrl+C)")
#             sys.exit(0)

#         except Exception as exc:
#             # Comprehensive error handling with detailed information
#             with Capture_Exception(context={"startup": True, "environment": ENVIRONMENT}):
#                 custom_exc = Exception_Configuration(
#                     "Failed to start QWIM Dashboard",
#                     severity=Exception_Severity.CRITICAL,
#                     cause=exc,
#                     context={"environment": ENVIRONMENT, "host": host, "port": port},
#                 )
#                 custom_exc.Log(
#                     logger=_logger,
#                     level="error",
#                 )
#                 _logger.error(
#                     "Dashboard startup failed",
#                     extra={
#                         "error": str(exc),
#                         "logs_location": str(project_dir / "logs"),
#                         "python_version_required": "3.11+",
#                     },
#                 )
#             sys.exit(1)  # Exit with error code for process monitoring


# # =============================================================================
# # Application Execution
# # =============================================================================

# # Main entry point when script is executed directly
# # This enables both direct execution and programmatic usage
# if __name__ == "__main__":  # pragma: no cover
#     main()
# =======
"""Main Shiny application entry point for the QWIM dashboard.

This module wires shared dashboard data, constructs the root UI, and connects
the top-level server callbacks for the portfolio, client, product, and results
tabs. Detailed user documentation belongs in the project docs, while this
docstring stays concise so the runtime module remains below the repository line
cap.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================

from __future__ import annotations

import contextlib
import sys  # MUST be first import to enable UTF-8 encoding fix


# CRITICAL: Force UTF-8 encoding for all I/O on Windows BEFORE any other imports
# This prevents UnicodeEncodeError when logging special characters (❱, ✓, etc.)
# Must execute before importing os, platform, or any third-party packages
if sys.platform == "win32":  # pragma: no cover
    # Import os here only for environment manipulation
    import os as _os_for_encoding

    # Set environment variable for subprocess and future operations
    _os_for_encoding.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # Force UTF-8 for default encoding
    if hasattr(sys, "_enablelegacywindowsfsencoding"):
        # Disable legacy Windows filesystem encoding
        sys._enablelegacywindowsfsencoding = lambda: None

    # Reconfigure all existing standard streams to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

    if hasattr(sys.stdin, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]

    # CRITICAL: Disable tbhandler to prevent UnicodeEncodeError
    # tbhandler uses rich.console which has encoding issues on Windows
    # We'll use our custom exception handling instead
    import io

    # Store original excepthook before any module can replace it
    _original_excepthook = sys.excepthook

    def _utf8_safe_excepthook(  # pragma: no cover
        *, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        """Exception hook that safely handles Unicode characters on Windows."""
        import traceback

        try:
            # Try to format exception with UTF-8 safe output
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            message = "".join(lines)
            # Write to stderr with UTF-8 encoding
            stderr_utf8 = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            stderr_utf8.write(message)
            stderr_utf8.flush()
        except Exception:
            # Fallback: use original hook
            try:
                _original_excepthook(exc_type, exc_value, exc_traceback)
            except Exception:
                # Last resort: basic error message
                _logger.error("Unhandled exception: %s: %s", exc_type.__name__, exc_value)

    # Install our safe exception hook
    sys.excepthook = _utf8_safe_excepthook

    # Prevent tbhandler from replacing our excepthook
    # Monkey patch sys to make excepthook read-only for tbhandler
    _sys_setattr = sys.__setattr__  # pyright: ignore[reportAttributeAccessIssue]  # pyrefly: ignore[missing-attribute]

    def _protected_setattr(*, name: str, value: Any) -> Any:  # pragma: no cover
        """Block tbhandler from overwriting sys.excepthook; allow all other setattr calls."""
        # Allow our code to set excepthook, but block tbhandler
        if name == "excepthook":
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = frame.f_back.f_code.co_filename
                # Only allow our code to modify excepthook
                if "main_App.py" not in caller_file and "tbhandler" in caller_file:
                    return None  # Silently ignore tbhandler's attempt
        return _sys_setattr(name, value)

    # Apply protection (but only for excepthook attribute)
    # Note: This is a workaround to prevent tbhandler from taking over

# Now safe to import other standard library modules
import os  # Operating system interface
import platform  # Access to underlying platform's identifying data
import warnings  # Warning control

from datetime import UTC, datetime  # Date and time handling
from pathlib import Path  # Object-oriented filesystem paths
from typing import Any


# =============================================================================
# Warning Suppression
# =============================================================================
warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")

# =============================================================================
# Third-Party Imports
# =============================================================================
import shinyswatch  # Bootstrap themes for Shiny applications

from shiny import App, reactive, ui


# =============================================================================
# Project Path Configuration
# =============================================================================

#: Root directory of the QWIM Dashboard project
#: Determined by navigating up from the current file location
project_dir = Path(__file__).parent.parent.parent

# Add project root to Python path for module imports
# This ensures all internal modules can be imported properly
if str(project_dir) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(project_dir))

# =============================================================================
# Custom Logging and Exception Handling
# =============================================================================

# Custom logging utilities - using loguru-based logger
# Custom exception classes following project coding standards
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Severity,
    Capture_Exception,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import (
    Performance_Timer,
    get_logger,
    setup_logging,
)


# Initialize logging at module level
setup_logging(
    log_level="ERROR",
    environment=os.environ.get("QWIM_ENVIRONMENT", "development"),
    log_dir=Path(__file__).parent.parent.parent / "logs",
    enable_console=True,
    enable_JSON=True,
)

#: Module-level logger instance
_logger = get_logger(name = __name__)

# =============================================================================
# Internal Module Imports - Utility Functions
# =============================================================================

# Reactive state management utilities
from src.dashboard.shiny_utils.reactives_shiny import (
    initialize_reactives_shiny,
)

# Data processing and utility functions
from src.dashboard.shiny_utils.utils_data import (
    get_data_inputs,
    get_data_utils,
)


# =============================================================================
# Configuration and Environment Setup
# =============================================================================

#: Application environment type (development or production)
#: Controls server configuration, debug settings, and deployment options
#:
#: - development: Local development with debug mode and auto-reload
#: - production: Production deployment with optimized settings
ENVIRONMENT: str = os.environ.get("QWIM_ENVIRONMENT", "development").lower()

# =============================================================================
# Data Initialization
# =============================================================================

_logger.info(
    "Initializing QWIM Dashboard data",
    extra={"environment": ENVIRONMENT, "project_dir": str(project_dir)},
)

#: Dictionary containing data utility functions and configurations
#: Provides access to data processing, validation, and transformation utilities
data_utils: dict[str, Any] = get_data_utils(project_dir=project_dir)

#: Dictionary containing all input datasets for the dashboard
#: Includes portfolio data, benchmark data, weights, and time series information
data_inputs: dict[str, Any] = get_data_inputs(project_dir=project_dir)

# Logs directory is created by setup_logging

# =============================================================================
# Internal Module Imports - Dashboard Components
# =============================================================================

from src.dashboard.shiny_tab_clients.tab_clients import (
    tab_clients_server,
    tab_clients_ui,
)
from src.dashboard.shiny_tab_goal_based_investing.tab_goal_based_investing import (
    tab_goal_based_investing_server,
    tab_goal_based_investing_ui,
)
from src.dashboard.shiny_tab_goal_parity.tab_goal_parity import (
    tab_goal_parity_server,
    tab_goal_parity_ui,
)
from src.dashboard.shiny_tab_overview.tab_overview import (
    tab_overview_server,
    tab_overview_ui,
)
from src.dashboard.shiny_tab_portfolios.tab_portfolios import (
    tab_portfolios_server,
    tab_portfolios_ui,
)
from src.dashboard.shiny_tab_products.tab_products import (
    tab_products_server,
    tab_products_ui,
)
from src.dashboard.shiny_tab_results.tab_results import (
    tab_results_server,
    tab_results_ui,
)
from src.dashboard.shiny_tab_covariance.tab_covariance import (
    tab_covariance_server,
    tab_covariance_ui,
)
from src.dashboard.shiny_tab_setup.tab_setup import (
    tab_setup_server,
    tab_setup_ui,
)
from src.dashboard.shiny_tab_goals.tab_goals import (
    tab_goals_server,
    tab_goals_ui,
)


_logger.debug("Dashboard components imported successfully")

# =============================================================================
# UI Component Functions
# =============================================================================


def create_about_modal() -> Any:
    """
    Create the About modal dialog with comprehensive application information.

    This modal provides users with detailed information about the dashboard
    including features, technology stack, version details, and platform information.

    ## Modal Content Structure

    The modal is organized into the following sections:

    1. **Features**: Core dashboard capabilities and functionality
    2. **Technology Stack**: Technical components and frameworks used
    3. **Supported Analysis**: Types of analysis available
    4. **Version Information**: Technical details about the current deployment

    ## Returns

    Returns
    -------
        shiny.ui.modal: Configured modal dialog component with comprehensive
        application information formatted using Bootstrap styling.

    ## Usage Example

    ```python
    # Create and display the modal
    about_modal = create_about_modal()
    ui.modal_show(about_modal)
    ```

    ## Modal Features

    - **Responsive Design**: Adapts to different screen sizes
    - **Easy Close**: Can be dismissed by clicking outside or close button
    - **Rich Content**: Includes lists, formatted text, and highlighted sections
    - **Version Info**: Dynamic version and platform information

    ## Styling

    Uses Bootstrap classes for consistent appearance:
    - `bg-light`: Light background for version information section
    - `p-3`: Padding for content spacing
    - `rounded`: Rounded corners for modern appearance
    - `btn-primary`: Primary button styling for close button

    ## Notes

    !!! info "Dynamic Content"
        Version information is generated dynamically based on the current
        Python environment and platform, ensuring accuracy across deployments.

    !!! tip "Customization"
        The modal content can be easily modified to include additional
        sections or updated feature descriptions as the dashboard evolves.
    """
    return ui.modal(
        # Modal header with application title
        ui.h3("About QWIM Dashboard"),
        ui.p(
            "The QWIM Dashboard is a comprehensive time series analysis tool built with Python and Shiny.",
        ),
        # Features section highlighting core capabilities
        ui.h5("🚀 Features:"),
        ui.tags.ul(
            ui.tags.li("Interactive time series visualization with multiple chart types"),
            ui.tags.li("Dynamic ETF component selection and filtering"),
            ui.tags.li("Statistical analysis and portfolio weight distribution"),
            ui.tags.li("Real-time reactive updates and synchronization"),
            ui.tags.li("Customizable time period selection and analysis"),
            ui.tags.li("Export capabilities for plots and statistical tables"),
        ),
        # Technology stack section with technical details
        ui.h5("🛠️ Technology Stack:"),
        ui.tags.ul(
            ui.tags.li("Python 3.12+ for core functionality"),
            ui.tags.li("Shiny for Python for interactive dashboard framework"),
            ui.tags.li("Plotly for interactive and responsive visualizations"),
            ui.tags.li("Polars for high-performance time series processing"),
            ui.tags.li("NumPy and Pandas for numerical computations"),
            ui.tags.li("Bootstrap themes via shinyswatch for responsive design"),
        ),
        # Analysis capabilities section
        ui.h5("📊 Supported Analysis:"),
        ui.tags.ul(
            ui.tags.li("Portfolio weight distribution over time"),
            ui.tags.li("Component-wise statistical analysis"),
            ui.tags.li("Time period filtering and comparison"),
            ui.tags.li("Multiple visualization formats (area, line, bar, heatmap)"),
        ),
        # Dynamic version information section
        ui.h5("ℹ️ Version Information:"),
        ui.div(
            ui.p("**Dashboard Version:** 0.5.1"),
            ui.p(f"**Python Version:** {platform.python_version()}"),
            ui.p(f"**Platform:** {platform.system()} {platform.release()}"),
            ui.p(f"**Environment:** {ENVIRONMENT.title()}"),
            class_="bg-light p-3 rounded",  # Bootstrap styling for highlighted section
        ),
        # Footer with generation timestamp
        ui.hr(),
        ui.p(ui.tags.small(f"Generated on: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")),
        # Modal configuration
        title="About QWIM Dashboard",
        size="l",  # Large modal size for comprehensive content
        easy_close=True,  # Allow closing by clicking outside modal
        footer=ui.modal_button("Close", class_="btn-primary"),
    )


#: Pre-created About modal instance for consistent presentation
#: Avoids recreating the modal on each display request
about_modal = create_about_modal()


def create_app_ui() -> Any:
    """
    Create the main application user interface.

    This function defines the primary UI layout using a navbar-based design
    that provides intuitive navigation and professional appearance.

    ## UI Architecture

    The interface follows a hierarchical structure:

    ```
    page_navbar (main container)
    ├── nav_panel (QWIM Portfolios tab)
    │   └── tab_portfolios_ui (portfolio analysis interface)
    ├── nav_spacer (flexible spacing)
    └── nav_control (About button)
    ```

    ## Layout Components

    ### Main Navigation
    - **Portfolio Tab**: Primary functionality for portfolio analysis
    - **About Button**: Access to application information and help

    ### Theme and Styling
    - **Flatly Theme**: Modern, professional Bootstrap theme via shinyswatch
    - **Responsive Design**: Adapts to different screen sizes and devices
    - **Fillable Layout**: Optimizes space usage for data visualization

    ## Returns

    Returns
    -------
        shiny.ui.page_navbar: Main application UI layout configured with
        portfolio analysis functionality and navigation components.

    ## Configuration Details

    ### Navbar Settings
    - `title`: Application branding displayed in navigation bar
    - `theme`: Bootstrap theme for consistent visual appearance
    - `fillable`: Enables responsive layout optimization
    - `id`: Unique identifier for reactive navigation tracking

    ### Component IDs
    Following project naming conventions:
    - `ID_tab_portfolios`: Main portfolio analysis tab
    - `input_ID_show_about`: About button for modal display
    - `input_ID_navbar_main`: Navigation bar for tab tracking

    ## Usage Example

    ```python
    # Create the main UI
    app_ui = create_app_ui()

    # Use in Shiny app
    app = App(app_ui, app_server)
    ```

    ## Extensibility

    To add new tabs to the dashboard:

    ```python
    # Add additional nav_panel entries before nav_spacer
    (
        ui.nav_panel(
            "New Tab Name", new_tab_ui("ID_new_tab", data_utils=data_utils, data_inputs=data_inputs)
        ),
    )
    ```

    ## Notes

    !!! info "Theme Selection"
        The Flatly theme provides a modern, professional appearance suitable
        for financial and analytical applications.

    !!! tip "Navigation Pattern"
        The nav_spacer() pushes the About button to the right side of the
        navigation bar, following standard web design patterns.

    !!! warning "ID Conventions"
        All component IDs follow the project naming standards with descriptive
        prefixes (input_, output_, ID_) for consistency and maintainability.
    """
    return ui.page_navbar(
        ui.nav_panel(
            "Overview",
            tab_overview_ui(
                "ID_tab_overview",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Setup",
            tab_setup_ui(
                "ID_tab_setup",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_panel(
            "Clients",
            tab_clients_ui(
                "ID_tab_clients",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),  # Input datasets for clients
        ),
        ui.nav_panel(
            "Goal-Based Investing",
            tab_goal_based_investing_ui(
                "ID_tab_goal_based_investing",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        # portfolio analysis tab
        ui.nav_panel(
            "Portfolios",
            tab_portfolios_ui(
                "ID_tab_portfolios",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),  # Input datasets for analysis
        ),
        # 2. In create_app_ui(), after the Portfolios nav_panel:
        ui.nav_panel(
            " Personalized Goals Investing",
            tab_goals_ui(
                "ID_tab_goals",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        # Products tab (annuities, insurance, etc.)
        ui.nav_panel(
            "Products",
            tab_products_ui(
                "ID_tab_products",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),  # Input datasets for product analysis
        ),
        # Goal Parity tab (individual model: LLM-profiled goal-based allocation)
        ui.nav_panel(
            "Goal Parity",
            tab_goal_parity_ui(
                "ID_tab_goal_parity",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),
        ),
        # Results tab (reporting, PDF generation, etc.)
        ui.nav_panel(
            "Results",
            tab_results_ui(
                "ID_tab_results",
                data_utils=data_utils,  # Utility functions and configuration
                data_inputs=data_inputs,
            ),  # Input datasets for results
        ),
        # Navigation spacer to push subsequent elements to the right
        # Creates proper visual separation between main content and utility buttons
        ui.nav_panel(
            "Covariance",
            tab_covariance_ui(
                "ID_tab_covariance",
                data_utils=data_utils,
                data_inputs=data_inputs,
            ),
        ),
        ui.nav_spacer(),
        # About button in navigation bar for application information
        # Provides users with help, features overview, and version details
        ui.nav_control(
            ui.input_action_button(
                "input_ID_show_about",  # Button identifier following naming convention
                "About",  # Button label
                class_="btn-outline-light me-2",
            ),  # Bootstrap styling classes
        ),
        # Application-level configuration settings
        title="QWIM Dashboard",  # Application title displayed in browser and navbar
        theme=shinyswatch.theme.flatly(),  # Modern Bootstrap theme for professional appearance
        id="input_ID_navbar_main",  # Unique identifier for reactive navigation tracking
        fillable=True,  # Enable responsive fillable layout for optimal space usage
    )


#: Main application UI instance
#: Created once for use by the Shiny App constructor
app_ui = create_app_ui()


# =============================================================================
# Server Logic Functions
# =============================================================================


def app_server(input: Any, output: Any, session: Any) -> None:  # noqa: A002, ARG001  # pragma: no cover
    """Coordinate top-level reactive state, modal handling, and tab servers.

    The server initializes shared dashboard state once, wires the main
    navigation observers, and delegates each major tab to its module server.
    """
    # Initialize reactive values for application state management
    # This creates the centralized state that coordinates all dashboard modules
    try:
        reactives_shiny = initialize_reactives_shiny(data_utils=data_utils)
    except Exception as exc:
        # Critical error - dashboard cannot function without reactive state
        custom_exc = Exception_Configuration(
            "Failed to initialize reactive values",
            severity=Exception_Severity.CRITICAL,
            cause=exc,
            context={"component": "reactives_shiny"},
        )
        custom_exc.Log(
            logger=_logger,
            level="error",
        )
        raise custom_exc from exc

    # Initialize navigation tracking reactive value
    # Defaults to the first available tab for consistent user experience
    current_tab = reactive.value("QWIM Portfolios")

    @reactive.effect
    def observer_track_selected_tab() -> None:
        """
        Track and update the currently selected navigation tab.

        This reactive effect monitors changes to the main navigation bar
        and updates the `current_tab` reactive value accordingly.

        ## Functionality

        - Monitors navigation bar state changes
        - Updates current_tab reactive value
        - Enables tab-specific functionality and state management
        - Provides tab context for conditional logic in modules

        ## Implementation Details

        Uses `input.input_ID_navbar_main()` to get the currently selected tab
        and validates the value before updating the reactive state.

        ## Usage Example

        ```python
        # In other reactive contexts, access current tab
        active_tab = current_tab()
        if active_tab == "QWIM Portfolios":
            # Tab-specific logic
        ```

        ## Notes

        !!! info "Validation"
            Includes input validation to ensure only valid tab names
            are set in the reactive value.

        !!! tip "Extension"
            When adding new tabs, this function automatically tracks
            them without modification.
        """
        selected_tab = input.input_ID_navbar_main()
        # Validate that a tab was actually selected before updating
        if selected_tab:
            current_tab.set(selected_tab)

    @reactive.effect
    @reactive.event(input.input_ID_show_about)
    def observer_show_about_modal() -> None:
        """
        Display the About modal dialog when the About button is clicked.

        This reactive effect responds specifically to clicks on the About button
        and displays the modal containing application information.

        ## Event-Driven Pattern

        Uses `@reactive.event` decorator to respond only to specific button clicks
        rather than any input change, ensuring the modal only appears when requested.

        ## Modal Content

        Displays the pre-created `about_modal` which includes:
        - Feature overview and capabilities
        - Technology stack information
        - Version and platform details
        - Usage guidance and support information

        ## User Experience

        - Modal appears immediately upon button click
        - Can be dismissed by clicking outside or using the close button
        - Provides comprehensive application information in accessible format

        ## Implementation

        ```python
        # Button click → Event trigger → Modal display
        ui.modal_show(about_modal)
        ```

        ## Notes

        !!! info "Event Specificity"
            The @reactive.event decorator ensures this function only runs
            when the specific About button is clicked, not on other input changes.

        !!! tip "Modal Management"
            The modal is pre-created for performance and consistency,
            avoiding recreation on each display request.
        """
        ui.modal_show(about_modal)

    # Initialize overview module server
    tab_overview_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_overview",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for overview
        reactives_shiny=reactives_shiny,
    )

    # Initialize setup module server
    tab_setup_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_setup",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for setup
        reactives_shiny=reactives_shiny,
    )

    # Initialize clients module server
    tab_clients_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_clients",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for portfolio analysis
        reactives_shiny=reactives_shiny,
    )  # Centralized reactive state for coordination

    tab_goal_based_investing_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_goal_based_investing",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    # Initialize portfolio analysis module server
    tab_portfolios_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_portfolios",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for portfolio analysis
        reactives_shiny=reactives_shiny,
    )  # Centralized reactive state for coordination

    # Initialize products module server
    tab_products_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_products",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for product analysis
        reactives_shiny=reactives_shiny,
    )  # Centralized reactive state for coordination

    # Initialize results module server
    tab_results_server(  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        id="ID_tab_results",  # pyrefly: ignore[unexpected-keyword,bad-argument-count]  # Unique module identifier following naming convention
        data_utils=data_utils,  # Utility functions and configuration settings
        data_inputs=data_inputs,  # Input datasets for results
        reactives_shiny=reactives_shiny,
    )  # Centralized reactive state for coordination

    # Initialize Goal Parity module server
    tab_goal_parity_server(
        id="ID_tab_goal_parity",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    tab_goals_server(
        id="ID_tab_goals",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

    tab_covariance_server(
        id="ID_tab_covariance",
        data_utils=data_utils,
        data_inputs=data_inputs,
        reactives_shiny=reactives_shiny,
    )

def app_factory() -> App:
    """Create a fresh Shiny application instance from the module UI and server."""
    return App(create_app_ui(), app_server)


#: Main Shiny application instance combining UI and server functionality.
#: Created via :func:`app_factory` to keep instantiation logic in one place.
app = app_factory()


# =============================================================================
# Application Entry Point
# =============================================================================


def main() -> None:  # pragma: no cover
    """Start the dashboard with development or production host and port settings.

    The runtime configuration is driven by `QWIM_ENVIRONMENT`, with structured
    logging and guarded shutdown paths for startup failures.
    """
    # Display comprehensive startup information for monitoring and debugging
    _logger.info(
        "Starting QWIM Dashboard",
        extra={
            "environment": ENVIRONMENT,
            "python_version": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()}",
            "project_directory": str(project_dir),
        },
    )

    with Performance_Timer("QWIM Dashboard startup"):
        host: str = "127.0.0.1"  # default; overridden below
        port: int = 8080  # default; overridden below
        try:
            # Launch application with environment-appropriate configuration
            if ENVIRONMENT == "production":
                # Production configuration optimized for stability and security
                host = "0.0.0.0"
                port = 8000
                _logger.info(
                    "Production mode",
                    extra={
                        "url": f"http://{host}:{port}",
                        "features": "External access, optimized performance",
                    },
                )
            else:
                # Development configuration optimized for development workflow
                host = "127.0.0.1"
                port = 8080
                _logger.info(
                    "Development mode",
                    extra={
                        "url": f"http://{host}:{port}",
                        "features": "Stable operation, detailed error messages",
                    },
                )

            app.run(host=host, port=port, reload=False)

        except KeyboardInterrupt:
            _logger.info("Dashboard shutdown requested by user (Ctrl+C)")
            sys.exit(0)

        except Exception as exc:
            # Comprehensive error handling with detailed information
            with Capture_Exception(context={"startup": True, "environment": ENVIRONMENT}):
                custom_exc = Exception_Configuration(
                    "Failed to start QWIM Dashboard",
                    severity=Exception_Severity.CRITICAL,
                    cause=exc,
                    context={"environment": ENVIRONMENT, "host": host, "port": port},
                )
                custom_exc.Log(
                    logger=_logger,
                    level="error",
                )
                _logger.error(
                    "Dashboard startup failed",
                    extra={
                        "error": str(exc),
                        "logs_location": str(project_dir / "logs"),
                        "python_version_required": "3.11+",
                    },
                )
            sys.exit(1)  # Exit with error code for process monitoring


# =============================================================================
# Application Execution
# =============================================================================

# Main entry point when script is executed directly
# This enables both direct execution and programmatic usage
if __name__ == "__main__":  # pragma: no cover
    main()
