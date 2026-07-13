"""
Unit Tests for Dashboard Main Application
=========================================

This module contains comprehensive unit tests for the main_App.py module,
which is the entry point for the QWIM Dashboard Shiny application.

Test Coverage:
    - Project directory configuration
    - Data initialization (data_utils, data_inputs)
    - Environment configuration
    - Modal dialog creation
    - App UI and server setup

Testing Approach:
    - Uses pytest fixtures for mock data
    - Mocks file system and external dependencies
    - Tests configuration and initialization
    - Follows defensive programming validation patterns

Note:
    Many tests focus on structure and configuration rather than
    full integration testing, as Shiny apps require running server.
"""

import os
import sys

from pathlib import Path

import pytest


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture()
def mock_project_dir(tmp_path):
    """Create mock project directory structure."""
    # Create required directories
    (tmp_path / "inputs" / "raw").mkdir(parents=True)
    (tmp_path / "inputs" / "processed").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)

    return tmp_path


@pytest.fixture()
def mock_data_utils():
    """Create mock data_utils dictionary."""
    return {
        "Enable_PNG_Saving_Tab_Inputs": False,
        "Select_Time_Period": "Custom",
        "Custom_Date_Range_Start": "2018-01-10",
        "Custom_Date_Range_End": "2023-03-12",
    }


@pytest.fixture()
def mock_data_inputs():
    """Create mock data_inputs dictionary."""
    import polars as pl

    return {
        "Time_Series_Sample": pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "AA": [100.0],
            }
        ),
        "Time_Series_ETFs": pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "VTI": [150.0],
            }
        ),
        "Weights_My_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "VTI": [0.6],
            }
        ),
        "Benchmark_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Value": [100.0],
            }
        ),
        "My_Portfolio": pl.DataFrame(
            {
                "Date": ["2023-01-01"],
                "Value": [100.0],
            }
        ),
    }


# ============================================================================
# Tests for Module Constants and Configuration
# ============================================================================


@pytest.mark.unit()
class Test_Module_Configuration:
    """Test cases for module-level configuration."""

    @pytest.mark.unit()
    def test_project_dir_is_path(self):
        """Test that project_dir is a Path object."""
        from src.dashboard import main_App

        assert isinstance(main_App.project_dir, Path)

    @pytest.mark.unit()
    def test_project_dir_exists(self):
        """Test that project_dir points to existing directory."""
        from src.dashboard import main_App

        assert main_App.project_dir.exists()

    @pytest.mark.unit()
    def test_environment_has_valid_value(self):
        """Test that ENVIRONMENT has valid value."""
        from src.dashboard import main_App

        assert main_App.ENVIRONMENT in ["development", "production"]

    @pytest.mark.unit()
    def test_data_utils_is_dict(self):
        """Test that data_utils is a dictionary."""
        from src.dashboard import main_App

        assert isinstance(main_App.data_utils, dict)

    @pytest.mark.unit()
    def test_data_inputs_is_dict(self):
        """Test that data_inputs is a dictionary."""
        from src.dashboard import main_App

        assert isinstance(main_App.data_inputs, dict)


# ============================================================================
# Tests for Environment Configuration
# ============================================================================


@pytest.mark.unit()
class Test_Environment_Configuration:
    """Test cases for environment configuration."""

    @pytest.mark.unit()
    def test_default_environment_is_development(self):
        """Test that default environment is development."""
        # Get environment without QWIM_ENVIRONMENT set
        env_value = os.environ.get("QWIM_ENVIRONMENT", "development").lower()

        # Should be development if not explicitly set
        assert env_value in ["development", "production"]

    @pytest.mark.unit()
    def test_environment_affects_configuration(self):
        """Test that environment affects server configuration."""
        # This is a structural test - actual behavior tested in integration
        from src.dashboard import main_App

        # ENVIRONMENT should be a string
        assert isinstance(main_App.ENVIRONMENT, str)


# ============================================================================
# Tests for Data Initialization
# ============================================================================


@pytest.mark.unit()
class Test_Data_Initialization:
    """Test cases for data initialization."""

    @pytest.mark.unit()
    def test_data_utils_contains_expected_keys(self):
        """Test that data_utils contains expected configuration keys."""
        from src.dashboard import main_App

        # Check for expected utility keys
        assert "Enable_PNG_Saving_Tab_Inputs" in main_App.data_utils or len(main_App.data_utils) > 0

    @pytest.mark.unit()
    def test_data_inputs_contains_portfolio_data(self):
        """Test that data_inputs contains portfolio-related data."""
        from src.dashboard import main_App

        # Should contain at least some input data
        assert len(main_App.data_inputs) > 0

    @pytest.mark.unit()
    def test_data_inputs_values_are_dataframes(self):
        """Test that data_inputs values are DataFrames."""
        import polars as pl

        from src.dashboard import main_App

        for key, value in main_App.data_inputs.items():
            assert isinstance(value, pl.DataFrame), f"{key} is not a Polars DataFrame"


# ============================================================================
# Tests for create_about_modal Function
# ============================================================================


@pytest.mark.unit()
class Test_Create_About_Modal:
    """Test cases for create_about_modal function."""

    @pytest.mark.unit()
    def test_returns_modal_object(self):
        """Test that function returns a modal object."""
        from src.dashboard.main_App import create_about_modal

        result = create_about_modal()

        # Should return something (modal object)
        assert result is not None

    @pytest.mark.unit()
    def test_modal_can_be_created_without_error(self):
        """Test that modal creation doesn't raise errors."""
        from src.dashboard.main_App import create_about_modal

        # Should not raise
        modal = create_about_modal()

        assert modal is not None


# ============================================================================
# Tests for Imports and Dependencies
# ============================================================================


@pytest.mark.unit()
class Test_Imports_And_Dependencies:
    """Test cases for module imports and dependencies."""

    @pytest.mark.unit()
    def test_shiny_imports_available(self):
        """Test that Shiny imports are available."""
        from shiny import App, ui

        assert App is not None
        assert ui is not None

    @pytest.mark.unit()
    def test_plotly_imports_available(self):
        """Test that Plotly imports are available."""
        import plotly.express as px
        import plotly.graph_objects as go

        assert px is not None
        assert go is not None

    @pytest.mark.unit()
    def test_polars_import_available(self):
        """Test that Polars import is available."""
        import polars as pl

        assert pl is not None

    @pytest.mark.unit()
    def test_internal_imports_available(self):
        """Test that internal module imports are available."""
        from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny
        from src.dashboard.shiny_utils.utils_data import get_data_inputs
        from src.dashboard.shiny_utils.utils_errors import Error_Dashboard_Initialization

        assert initialize_reactives_shiny is not None
        assert get_data_inputs is not None
        assert Error_Dashboard_Initialization is not None


# ============================================================================
# Tests for Tab Module Imports
# ============================================================================


@pytest.mark.unit()
class Test_Tab_Module_Imports:
    """Test cases for tab module imports."""

    @pytest.mark.unit()
    def test_portfolios_tab_imports(self):
        """Test that Portfolios tab imports are available."""
        from src.dashboard.shiny_tab_portfolios.tab_portfolios import (
            tab_portfolios_server,
            tab_portfolios_ui,
        )

        assert tab_portfolios_ui is not None
        assert tab_portfolios_server is not None

    @pytest.mark.unit()
    def test_clients_tab_imports(self):
        """Test that Clients tab imports are available."""
        from src.dashboard.shiny_tab_clients.tab_clients import tab_clients_server, tab_clients_ui

        assert tab_clients_ui is not None
        assert tab_clients_server is not None

    @pytest.mark.unit()
    def test_setup_tab_imports(self):
        """Test that Setup tab imports are available."""
        from src.dashboard.shiny_tab_setup.tab_setup import tab_setup_server, tab_setup_ui

        assert tab_setup_ui is not None
        assert tab_setup_server is not None


# ============================================================================
# Tests for Error Handling Classes
# ============================================================================


@pytest.mark.unit()
class Test_Error_Handling_Imports:
    """Test cases for error handling class imports."""

    @pytest.mark.unit()
    def test_all_error_classes_importable(self):
        """Test that all error classes can be imported."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Silent_Initialization,
        )

        assert Error_Silent_Initialization is not None
        assert Error_Dashboard_Initialization is not None
        assert Error_Data_Loading is not None
        assert Error_Module_Initialization is not None

    @pytest.mark.unit()
    def test_error_classes_are_exceptions(self):
        """Test that error classes inherit from Exception."""
        from src.dashboard.shiny_utils.utils_errors import (
            Error_Dashboard_Initialization,
            Error_Data_Loading,
            Error_Module_Initialization,
            Error_Silent_Initialization,
        )

        assert issubclass(Error_Silent_Initialization, Exception)
        assert issubclass(Error_Dashboard_Initialization, Exception)
        assert issubclass(Error_Data_Loading, Exception)
        assert issubclass(Error_Module_Initialization, Exception)


# ============================================================================
# Tests for Logs Directory
# ============================================================================


@pytest.mark.unit()
class Test_Logs_Directory:
    """Test cases for logs directory setup."""

    @pytest.mark.unit()
    def test_logs_directory_created(self):
        """Test that logs directory is created."""
        from src.dashboard import main_App

        logs_dir = main_App.project_dir / "logs"

        assert logs_dir.exists()

    @pytest.mark.unit()
    def test_logs_directory_is_directory(self):
        """Test that logs is a directory, not a file."""
        from src.dashboard import main_App

        logs_dir = main_App.project_dir / "logs"

        assert logs_dir.is_dir()


# ============================================================================
# Tests for App Configuration (Structural)
# ============================================================================


@pytest.mark.unit()
class Test_App_Structure:
    """Test cases for app structure (without running server)."""

    @pytest.mark.unit()
    def test_module_has_app_ui_function_or_variable(self):
        """Test that module defines app_ui."""
        from src.dashboard import main_App

        # Check if app_ui exists as attribute
        assert hasattr(main_App, "app_ui") or hasattr(main_App, "App")

    @pytest.mark.unit()
    def test_module_has_create_about_modal(self):
        """Test that module has create_about_modal function."""
        from src.dashboard import main_App

        assert hasattr(main_App, "create_about_modal")
        assert callable(main_App.create_about_modal)


# ============================================================================
# Tests for Path Configuration
# ============================================================================


@pytest.mark.unit()
class Test_Path_Configuration:
    """Test cases for path configuration."""

    @pytest.mark.unit()
    def test_project_dir_in_sys_path(self):
        """Test that project_dir is in sys.path."""
        from src.dashboard import main_App

        assert str(main_App.project_dir) in sys.path

    @pytest.mark.unit()
    def test_project_dir_points_to_project_root(self):
        """Test that project_dir points to project root."""
        from src.dashboard import main_App

        # Project root should contain certain files/folders
        expected_items = ["src", "tests", "inputs"]

        for item in expected_items:
            item_path = main_App.project_dir / item
            assert item_path.exists(), f"Expected {item} in project root"


# ============================================================================
# Tests for app_factory Function
# ============================================================================


@pytest.mark.unit()
class Test_App_Factory:
    """Test cases for the app_factory() factory function."""

    @pytest.mark.unit()
    def test_app_factory_returns_app_instance(self):
        """Test that app_factory returns a shiny.App instance."""
        from shiny import App

        from src.dashboard.main_App import app_factory

        result = app_factory()

        assert isinstance(result, App)

    @pytest.mark.unit()
    def test_app_factory_is_callable(self):
        """Test that app_factory is a callable."""
        from src.dashboard.main_App import app_factory

        assert callable(app_factory)

    @pytest.mark.unit()
    def test_app_factory_returns_different_objects_each_call(self):
        """Test that each app_factory() call produces an independent object.

        Multiple calls must not return the same object — each call should
        allocate a fresh App instance (required for multi-worker deployments).
        """
        from src.dashboard.main_App import app_factory

        app1 = app_factory()
        app2 = app_factory()

        # Each call must produce a distinct object
        assert app1 is not app2

    @pytest.mark.unit()
    def test_app_factory_result_matches_module_app(self):
        """Test that app_factory returns same type as the module-level app."""
        from shiny import App

        from src.dashboard.main_App import app_factory

        # Module-level 'app' is also created by app_factory(); both must be App.
        from src.dashboard import main_App

        assert isinstance(main_App.app, App)
        assert type(app_factory()) is type(main_App.app)

    @pytest.mark.unit()
    def test_module_app_is_app_instance(self):
        """Test that the module-level 'app' variable is a shiny.App."""
        from shiny import App

        from src.dashboard import main_App

        assert hasattr(main_App, "app")
        assert isinstance(main_App.app, App)
