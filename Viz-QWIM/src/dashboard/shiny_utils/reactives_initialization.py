"""Initialization utilities for the reactives_shiny dictionary.

This module creates the full ``reactives_shiny`` dictionary and each of its
seven sub-categories (User_Inputs_Shiny, Inner_Variables_Shiny,
Triggers_Shiny, Visual_Objects_Shiny, Data_Clients, Data_Results,
Advisor_Info).
"""

from __future__ import annotations

from typing import Any

from shiny import reactive

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from .reactives_validation import validate_data_utils_parameter


#: Module-level logger instance
_logger = get_logger(name = __name__)


def create_reactive_value_safely(*, initial_value: Any = None) -> Any:
    """Create a reactive value safely using defensive programming."""
    # Only use try-except for reactive.Value creation that might fail unpredictably
    try:
        return reactive.Value(initial_value)
    except Exception:  # pragma: no cover
        return None


def initialize_reactives_shiny(*, data_utils: Any) -> Any:
    """Initialize all reactive values for the Shiny dashboard using defensive programming.

    Args:
        data_utils: Initial data for reactive value initialization

    Returns
    -------
        dict: Dictionary containing organized reactive values by category

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Initialize each category using helper functions
    reactive_user_inputs = initialize_reactive_user_inputs(data_utils = data_utils)
    reactive_inner_variables = initialize_reactive_inner_variables(data_utils = data_utils)
    reactive_triggers = initialize_reactive_triggers(data_utils = data_utils)
    reactive_visual_objects = initialize_reactive_visual_objects(data_utils = data_utils)
    reactive_data_clients = initialize_reactive_data_clients(data_utils = data_utils)
    reactive_data_results = initialize_reactive_data_results(data_utils = data_utils)
    reactive_advisor_info = initialize_reactive_advisor_info(data_utils = data_utils)

    # Business logic validation - create organized structure
    return {
        "User_Inputs_Shiny": reactive_user_inputs,
        "Inner_Variables_Shiny": reactive_inner_variables,
        "Triggers_Shiny": reactive_triggers,
        "Visual_Objects_Shiny": reactive_visual_objects,
        "Data_Clients": reactive_data_clients,
        "Data_Results": reactive_data_results,
        "Advisor_Info": reactive_advisor_info,
    }


def initialize_reactive_user_inputs(*, data_utils: Any) -> Any:
    """Initialize values for User_Inputs_Shiny category in the reactives_shiny structures using defensive programming."""
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - define reactive inputs mapping to all subtab modules
    reactive_inputs_config = {
        "Input_Tab_Portfolios_Subtab_Comparison_Time_Period": None,
        "Input_Tab_Portfolios_Subtab_Comparison_Date_Range": None,
        "Input_Tab_Portfolios_Subtab_Comparison_Viz_Type": None,
        "Input_Tab_Portfolios_Subtab_Comparison_Show_Diff": None,
        "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_Time_Period": None,
        "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_Date_Range": None,
        "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_Type": None,
        "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_Rolling_Window": None,
        "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_Include_Benchmark": None,
        # ------------------------------------------------------------------
        # Analysis inclusion flags for Personal Info subtab
        # Maps to: input_ID_tab_clients_subtab_clients_personal_info_include_*
        # ------------------------------------------------------------------
        "Input_Tab_clients_Subtab_clients_Personal_Info_Include_Primary_In_Analysis": True,
        "Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis": False,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Status_Marital": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Gender": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Tolerance_Risk": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_State": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Code_Zip": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Status_Marital": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Gender": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Tolerance_Risk": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_State": None,
        "Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Code_Zip": None,
        "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable": 0.0,
        "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Deferred": 0.0,
        "Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Free": 0.0,
        "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable": 0.0,
        "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred": 0.0,
        "Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Important": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Aspirational": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Essential": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Important": 0.0,
        "Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Aspirational": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Annuity_Existing": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Other": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Social_Security": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Pension": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Annuity_Existing": 0.0,
        "Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other": 0.0,
        # ------------------------------------------------------------------
        # Weights Analysis subtab
        # Maps to: input_ID_tab_portfolios_subtab_weights_analysis_*
        # ------------------------------------------------------------------
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Time_Period": None,
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Date_Range": None,
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Viz_Type": None,
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Show_Pct": None,
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Sort_Components": None,
        "Input_Tab_Portfolios_Subtab_Weights_Analysis_Select_All_Components": None,
        # ------------------------------------------------------------------
        # Skfolio Portfolio Optimization subtab
        # Maps to: input_ID_tab_portfolios_subtab_skfolio_*
        # ------------------------------------------------------------------
        "Input_Tab_Portfolios_Subtab_Skfolio_Method1_Category": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method1_Type": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method1_Objective": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method1_Risk_Aversion": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method2_Category": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method2_Type": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method2_Objective": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Method2_Risk_Aversion": None,
        "Input_Tab_Portfolios_Subtab_Skfolio_Time_Period": None,
        # ------------------------------------------------------------------
        # Portfolio Simulation subtab
        # Maps to: input_ID_tab_results_subtab_simulation_*
        # ------------------------------------------------------------------
        "Input_Tab_Results_Subtab_Simulation_Distribution_Type": None,
        "Input_Tab_Results_Subtab_Simulation_Rng_Type": None,
        "Input_Tab_Results_Subtab_Simulation_Num_Scenarios": None,
        "Input_Tab_Results_Subtab_Simulation_Num_Days": None,
        "Input_Tab_Results_Subtab_Simulation_Seed": None,
        "Input_Tab_Results_Subtab_Simulation_Initial_Value": None,
        "Input_Tab_Results_Subtab_Simulation_Degrees_Of_Freedom": None,
        "Input_Tab_Results_Subtab_Simulation_Start_Date": None,
        "Input_Tab_Results_Subtab_Simulation_Select_All_Components": None,
        # ------------------------------------------------------------------
        # PDF Report Reporting subtab — section-control flags
        # Maps to: input_ID_tab_results_subtab_reporting_checkbox_include_*
        # ------------------------------------------------------------------
        "Input_Tab_Results_Subtab_Reporting_Include_Advisor_Info": True,
        "Input_Tab_Results_Subtab_Reporting_Include_Portfolio_Analysis": True,
        "Input_Tab_Results_Subtab_Reporting_Include_Portfolio_Comparison": True,
        "Input_Tab_Results_Subtab_Reporting_Include_Weights_Analysis": True,
        "Input_Tab_Results_Subtab_Reporting_Include_Skfolio_Optimization": False,
        "Input_Tab_Results_Subtab_Reporting_Include_Simulation": True,
        # ------------------------------------------------------------------
        # Computation subtab — computation type per computation subtab
        # Maps to: input_ID_tab_setup_subtab_computation_*_computation_type
        # ------------------------------------------------------------------
        "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Computation_Type": "joblib",
        "Input_Tab_Setup_Subtab_Computation_Skfolio_Optimization_Computation_Type": "joblib",
        "Input_Tab_Setup_Subtab_Computation_OptimalPortfolios_Optimization_Computation_Type": "joblib",
        "Input_Tab_Setup_Subtab_Computation_Simulation_Computation_Type": "joblib",
        # ------------------------------------------------------------------
        # Computation subtab — Developer / Debug options per computation subtab
        # Maps to: input_ID_tab_setup_subtab_computation_*_logger_display / _execution_thread_mode / _profiler
        # ------------------------------------------------------------------
        "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Logger_Display": "no_display",
        "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Execution_Thread_Mode": "background",
        "Input_Tab_Setup_Subtab_Computation_Portfolio_Comparison_Profiler": "none",
        "Input_Tab_Setup_Subtab_Computation_Skfolio_Optimization_Logger_Display": "no_display",
        "Input_Tab_Setup_Subtab_Computation_Skfolio_Optimization_Execution_Thread_Mode": "background",
        "Input_Tab_Setup_Subtab_Computation_Skfolio_Optimization_Profiler": "none",
        "Input_Tab_Setup_Subtab_Computation_OptimalPortfolios_Optimization_Logger_Display": "no_display",
        "Input_Tab_Setup_Subtab_Computation_OptimalPortfolios_Optimization_Execution_Thread_Mode": "background",
        "Input_Tab_Setup_Subtab_Computation_OptimalPortfolios_Optimization_Profiler": "none",
        "Input_Tab_Setup_Subtab_Computation_Simulation_Logger_Display": "no_display",
        "Input_Tab_Setup_Subtab_Computation_Simulation_Execution_Thread_Mode": "background",
        "Input_Tab_Setup_Subtab_Computation_Simulation_Profiler": "none",
    }

    # Business logic validation - create reactive values safely
    reactive_user_inputs = {}
    for reactive_key_name, initial_value in reactive_inputs_config.items():
        reactive_user_inputs[reactive_key_name] = create_reactive_value_safely(initial_value = initial_value)

    return reactive_user_inputs


def initialize_reactive_inner_variables(*, data_utils: Any) -> Any:
    """Initialize reactive values for Inner_Variables_Shiny category in the reactives_shiny structures using defensive programming.

    Args:
        data_utils: Additional data for reactive value initialization

    Returns
    -------
        dict: Dictionary containing reactive values for Inner_Variables_Shiny category in the reactives_shiny structures.

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - define inner variables
    inner_variables_config = {
        "Data_Personal_Info_DF": None,
        "Data_Assets_DF": None,
        "Data_Goals_DF": None,
        "Data_Income_DF": None,
        # Simulation results — populated by subtab_simulation server
        "Simulation_Results": None,
        "Simulation_Stats": None,
        "Simulation_Compare_Results": None,
        "Simulation_Last_Run_Meta": None,
    }

    # Business logic validation - create reactive values safely
    reactive_inner_variables = {}
    for variable_key_name, initial_value in inner_variables_config.items():
        reactive_inner_variables[variable_key_name] = create_reactive_value_safely(initial_value = initial_value)

    return reactive_inner_variables


def initialize_reactive_triggers(*, data_utils: Any) -> Any:
    """Initialize reactive values for Triggers_Shiny category in the reactives_shiny structures using defensive programming.

    Args:
        data_utils: Additional data for reactive value initialization

    Returns
    -------
        dict: Dictionary containing reactive values for Triggers_Shiny category in the reactives_shiny structures.

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - define triggers
    triggers_config = {"Temp_Trigger_One": None}

    # Business logic validation - create reactive values safely
    reactive_triggers = {}
    for trigger_key_name, initial_value in triggers_config.items():
        reactive_triggers[trigger_key_name] = create_reactive_value_safely(initial_value = initial_value)

    return reactive_triggers


def initialize_reactive_visual_objects(*, data_utils: Any) -> Any:
    """Initialize reactive values for Visual_Objects_Shiny category in the reactives_shiny structures using defensive programming.

    Args:
        data_utils: Additional data for reactive value initialization

    Returns
    -------
        dict: Dictionary containing reactive values for Visual_Objects_Shiny category in the reactives_shiny structures.

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - define visual objects (plotnine figures — saved as SVGs for PDF report)
    visual_objects_config = {
        "Chart_Weights_Analysis_Portfolio_Weight_Distribution_Over_Time": None,
        "Chart_Weights_Analysis_Portfolio_Current_Composition": None,
        "Chart_Portfolio_Analysis_Returns_Distribution": None,
        "Chart_Portfolio_Comparison_Portfolio_vs_Benchmark": None,
        "Chart_skfolio_Optimization_Portfolio_Weights_Comparison": None,
        "Chart_skfolio_Optimization_Comparison_Portfolio_Performance": None,
        "Chart_Simulation_Portfolio_Value_Fan_Chart": None,
        "Chart_Simulation_Terminal_Value_Distribution": None,
    }

    # Business logic validation - create reactive values safely
    reactive_visual_objects = {}
    for visual_key_name, initial_value in visual_objects_config.items():
        reactive_visual_objects[visual_key_name] = create_reactive_value_safely(initial_value = initial_value)

    return reactive_visual_objects


def initialize_reactive_data_clients(*, data_utils: Any) -> Any:
    """Initialize nested reactive values for Data_Clients category in the reactives_shiny structures.

    Creates a nested dictionary structure for client data with three sub-levels:
    - ``Client_Primary``: reactive values for personal info, assets, goals, and income of the
      primary client.
    - ``Client_Partner``: reactive values for personal info, assets, goals, and income of the
      partner client.
    - ``Clients_Combined``: reactive values for combined assets, goals, and income of both clients.

    An additional ``Single_Or_Couple`` reactive value indicates whether the household consists of a
    single client (``"Single"``) or a couple with a primary and partner client (``"Couple"``).

    Args:
        data_utils: Additional data for reactive value initialization

    Returns
    -------
        dict: Nested dictionary containing reactive values for Data_Clients category in the
        reactives_shiny structures with the following layout::

            {
                "Single_Or_Couple": reactive.Value("Single"),
                "Client_Primary": {
                    "Personal_Info": reactive.Value(None),
                    "Assets": reactive.Value(None),
                    "Goals": reactive.Value(None),
                    "Income": reactive.Value(None),
                },
                "Client_Partner": {
                    "Personal_Info": reactive.Value(None),
                    "Assets": reactive.Value(None),
                    "Goals": reactive.Value(None),
                    "Income": reactive.Value(None),
                },
                "Clients_Combined": {
                    "Assets": reactive.Value(None),
                    "Goals": reactive.Value(None),
                    "Income": reactive.Value(None),
                },
            }

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - define per-client data categories
    client_data_categories_config = [
        "Personal_Info",
        "Assets",
        "Goals",
        "Income",
    ]

    # Business logic validation - build Client_Primary sub-dict
    reactive_client_primary: dict[str, Any] = {}
    for category_key_name in client_data_categories_config:
        reactive_client_primary[category_key_name] = create_reactive_value_safely(initial_value = None)

    # Business logic validation - build Client_Partner sub-dict
    reactive_client_partner: dict[str, Any] = {}
    for category_key_name in client_data_categories_config:
        reactive_client_partner[category_key_name] = create_reactive_value_safely(initial_value = None)

    # Configuration validation - define combined data categories (no Personal_Info)
    combined_data_categories_config = [
        "Assets",
        "Goals",
        "Income",
    ]

    # Business logic validation - build Clients_Combined sub-dict
    reactive_clients_combined: dict[str, Any] = {}
    for category_key_name in combined_data_categories_config:
        reactive_clients_combined[category_key_name] = create_reactive_value_safely(initial_value = None)

    # Assemble the Data_Clients nested structure
    return {
        "Single_Or_Couple": create_reactive_value_safely(initial_value = "Single"),
        "Client_Primary": reactive_client_primary,
        "Client_Partner": reactive_client_partner,
        "Clients_Combined": reactive_clients_combined,
    }


def initialize_reactive_data_results(*, data_utils: Any) -> Any:
    """Initialize nested reactive values for Data_Results category in the reactives_shiny structures.

    Creates a flat dictionary structure for results data with one reactive.Value per
    subtab/direction combination.  Each entry stores whatever data structure
    (dict, Polars DataFrame, or ``None``) that particular subtab needs to persist
    across reactive cycles.

    Args:
        data_utils: Additional data for reactive value initialization

    Returns
    -------
        dict: Dictionary containing reactive values for the Data_Results category with
        the following layout::

            {
                "Portfolio_Analysis_Inputs": reactive.Value(None),
                "Portfolio_Analysis_Outputs": reactive.Value(None),
                "Portfolio_Comparison_Inputs": reactive.Value(None),
                "Portfolio_Comparison_Outputs": reactive.Value(None),
                "Weights_Analysis_Inputs": reactive.Value(None),
                "Weights_Analysis_Outputs": reactive.Value(None),
                "Portfolio_Optimization_Skfolio_Inputs": reactive.Value(None),
                "Portfolio_Optimization_Skfolio_Outputs": reactive.Value(None),
                "Portfolio_Optimization_OptimalPortfolios_Inputs": reactive.Value(None),
                "Portfolio_Optimization_OptimalPortfolios_Outputs": reactive.Value(None),
                "Portfolio_Simulation_Inputs": reactive.Value(None),
                "Portfolio_Simulation_Outputs": reactive.Value(None),
            }

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - ordered list of all result subtab keys
    results_subtab_keys_config = [
        "Portfolio_Analysis_Inputs",
        "Portfolio_Analysis_Outputs",
        "Portfolio_Comparison_Inputs",
        "Portfolio_Comparison_Outputs",
        "Weights_Analysis_Inputs",
        "Weights_Analysis_Outputs",
        "Portfolio_Optimization_Skfolio_Inputs",
        "Portfolio_Optimization_Skfolio_Outputs",
        "Portfolio_Optimization_OptimalPortfolios_Inputs",
        "Portfolio_Optimization_OptimalPortfolios_Outputs",
        "Portfolio_Simulation_Inputs",
        "Portfolio_Simulation_Outputs",
    ]

    # Business logic validation - build the Data_Results dict
    reactive_data_results: dict[str, Any] = {}
    for subtab_key_name in results_subtab_keys_config:
        reactive_data_results[subtab_key_name] = create_reactive_value_safely(initial_value = None)

    return reactive_data_results


def initialize_reactive_advisor_info(*, data_utils: Any) -> Any:
    """Initialize reactive values for the ``Advisor_Info`` category.

    Creates a flat dictionary with one :class:`reactive.Value` per advisor field.
    The default values correspond to the project-level advisor defaults and are
    used when no worksheet PDF has been uploaded or when the PDF does not contain
    a field.

    Args:
        data_utils: Additional data for reactive value initialization (validated but
            not currently used for advisor defaults).

    Returns
    -------
        dict: Dictionary containing reactive values for the Advisor_Info category with
        the following layout::

            {
                "Name": reactive.Value(""),
                "Credentials": reactive.Value(""),
                "Title": reactive.Value(""),
                "Team": reactive.Value(""),
                "Firm": reactive.Value("QWIM AI Wealth Management"),
                "Email": reactive.Value(""),
                "Address": reactive.Value(""),
                "Phone_Number": reactive.Value(""),
            }

    Raises
    ------
        ValueError: If data_utils is invalid
    """
    # Input validation with early returns
    validation_result, validation_message = validate_data_utils_parameter(data_utils = data_utils)
    if not validation_result:
        raise Exception_Validation_Input(f"Data utils validation failed: {validation_message}")

    # Configuration validation - default advisor field values
    # "Firm" uses the project-level default from _ADVISOR_INFO_DEFAULT_VALUES
    advisor_info_config: dict[str, str] = {
        "Name": "",
        "Credentials": "",
        "Title": "",
        "Team": "",
        "Firm": "QWIM AIWealth Management",
        "Email": "",
        "Address": "",
        "Phone_Number": "",
    }

    # Business logic validation - create reactive values safely
    reactive_advisor_info: dict[str, Any] = {}
    for advisor_key_name, initial_value in advisor_info_config.items():
        reactive_advisor_info[advisor_key_name] = create_reactive_value_safely(initial_value = initial_value)

    return reactive_advisor_info
