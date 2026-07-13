"""Private data-building helpers for the client summary subtab."""

from __future__ import annotations

from typing import Any

import polars as pl

from src.dashboard.shiny_utils.reactives_shiny import get_value_from_reactives_shiny
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


def _format_zip_code(
    *, value_zip: Any) -> str:
    """Format a ZIP code value as a 5-digit integer string.

    Parameters
    ----------
    value_zip : Any
        Raw ZIP code value, which may be int, float, str, or None.

    Returns
    -------
    str
        Zero-padded 5-digit string, e.g. ``"28934"`` or ``"10026"``.
    """
    try:
        if value_zip is None:
            return ""
        zip_int = int(float(str(value_zip).replace(",", "").replace("$", "").strip()))
        return f"{zip_int:05d}"
    except (ValueError, TypeError):
        return str(value_zip) if value_zip else ""


def normalize_data_personal_info_summary(
    *, data_personal_info_df: pl.DataFrame) -> pl.DataFrame:
    """Normalize personal-info summary columns for display and reporting.

    Accepts both legacy column names (``Primary_client`` / ``Partner_client``)
    and the current table-builder names (``client_Primary`` / ``client_Partner``).
    When no partner column is present, the output is padded with ``"Not Provided"``
    so single-client flows render without errors.
    """
    primary_column_name = None
    if "Client Primary" in data_personal_info_df.columns:
        primary_column_name = "Client Primary"
    elif "Client Primary" in data_personal_info_df.columns:
        primary_column_name = "Client Primary"

    if primary_column_name is None:
        raise Exception_Validation_Input(
            "Primary client column is missing from personal information data.",
        )

    partner_column_name = None
    if "Client Partner" in data_personal_info_df.columns:
        partner_column_name = "Client Partner"
    elif "Client Partner" in data_personal_info_df.columns:
        partner_column_name = "Client Partner"

    return data_personal_info_df.select(
        pl.col("Field Name").alias("Field Name"),
        pl.col(primary_column_name).alias("Client Primary"),
        (
            pl.col(partner_column_name)
            if partner_column_name is not None
            else pl.lit("Not Provided")
        ).alias("Client Partner"),
    )



def calc_table_summary_clients_assets(
    *, reactives_shiny: dict[str, Any]) -> pl.DataFrame:
    """Generate the financial assets summary dataframe."""
    from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger
    _logger_summary = get_logger(name = __name__)
    try:
        value_Primary_Taxable = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Taxable",
            key_category="User_Inputs_Shiny",
        )
        value_Primary_Tax_Deferred = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Deferred",
            key_category="User_Inputs_Shiny",
        )
        value_Primary_Tax_Free = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Primary_Assets_Tax_Free",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Taxable = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Taxable",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Tax_Deferred = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Deferred",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Tax_Free = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Assets_client_Partner_Assets_Tax_Free",
            key_category="User_Inputs_Shiny",
        )

        _logger_summary.info(
            "summary_assets: raw values primary=[%s, %s, %s] partner=[%s, %s, %s]",
            value_Primary_Taxable,
            value_Primary_Tax_Deferred,
            value_Primary_Tax_Free,
            value_Partner_Taxable,
            value_Partner_Tax_Deferred,
            value_Partner_Tax_Free,
        )

        value_Primary_Taxable = int(max(0, value_Primary_Taxable or 0))
        value_Primary_Tax_Deferred = int(max(0, value_Primary_Tax_Deferred or 0))
        value_Primary_Tax_Free = int(max(0, value_Primary_Tax_Free or 0))
        value_Partner_Taxable = int(max(0, value_Partner_Taxable or 0))
        value_Partner_Tax_Deferred = int(max(0, value_Partner_Tax_Deferred or 0))
        value_Partner_Tax_Free = int(max(0, value_Partner_Tax_Free or 0))

        value_Primary_Total = (
            value_Primary_Taxable + value_Primary_Tax_Deferred + value_Primary_Tax_Free
        )
        value_Partner_Total = (
            value_Partner_Taxable + value_Partner_Tax_Deferred + value_Partner_Tax_Free
        )

        value_Combined_Taxable = value_Primary_Taxable + value_Partner_Taxable
        value_Combined_Tax_Deferred = value_Primary_Tax_Deferred + value_Partner_Tax_Deferred
        value_Combined_Tax_Free = value_Primary_Tax_Free + value_Partner_Tax_Free
        value_Combined_Total = value_Primary_Total + value_Partner_Total

        include_partner_raw = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis",
            key_category="User_Inputs_Shiny",
        )
        include_partner = bool(include_partner_raw) if include_partner_raw is not None else False

        asset_categories = [
            "Taxable Assets",
            "Tax Deferred Assets",
            "Tax Free Assets",
            "Total Assets",
        ]
        primary_col = [
            value_Primary_Taxable,
            value_Primary_Tax_Deferred,
            value_Primary_Tax_Free,
            value_Primary_Total,
        ]
        combined_col = [
            value_Combined_Taxable,
            value_Combined_Tax_Deferred,
            value_Combined_Tax_Free,
            value_Combined_Total,
        ]
        if include_partner:
            data_Assets_DF = pl.DataFrame(
                {
                    "Field Name": asset_categories,
                    "Client Primary": primary_col,
                    "Client Partner": [
                        value_Partner_Taxable,
                        value_Partner_Tax_Deferred,
                        value_Partner_Tax_Free,
                        value_Partner_Total,
                    ],
                    "Combined Total": combined_col,
                },
            )
        else:
            data_Assets_DF = pl.DataFrame(
                {
                    "Field Name": asset_categories,
                    "Client Primary": primary_col,
                    "Combined Total": combined_col,
                },
            )

        if data_Assets_DF is None or data_Assets_DF.height == 0:
            raise Exception_Validation_Input("Failed to create data_Assets_DF dataframe")

        return data_Assets_DF

    except Exception as exc_error:
        (f"Error generating assets calculation: {type(exc_error).__name__}: {exc_error!s}")
        return pl.DataFrame(
            {
                "Field Name": ["Error"],
                "Client Primary": [0.0],
                "Combined Total": [0.0],
            },
        )



def calc_table_summary_clients_personal_info(
    *, reactives_shiny: dict[str, Any]) -> pl.DataFrame:
    """Generate the personal-information summary dataframe."""
    from src.dashboard.shiny_utils.reactives_shiny import (
        get_value_from_reactives_shiny as get_value_from_reactives_shiny_runtime,
        validate_reactives_shiny_structure,
    )

    validation_result, validation_message = validate_reactives_shiny_structure(reactives_shiny = reactives_shiny)
    if not validation_result:
        raise Exception_Validation_Input(
            f"Reactives structure validation failed: {validation_message}",
        )

    user_inputs_category = reactives_shiny.get("User_Inputs_Shiny")
    if user_inputs_category is None:
        available_categories = list(reactives_shiny.keys())
        raise KeyError(
            f"User_Inputs_Shiny category not found. Available categories: {available_categories}",
        )

    primary_client_name = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name",
        key_category="User_Inputs_Shiny",
    )
    primary_client_age_current = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Current",
        key_category="User_Inputs_Shiny",
    )
    primary_client_age_retirement = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Retirement",
        key_category="User_Inputs_Shiny",
    )
    primary_client_age_income_starting = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Age_Income_Starting",
        key_category="User_Inputs_Shiny",
    )
    primary_client_status_marital = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Status_Marital",
        key_category="User_Inputs_Shiny",
    )
    primary_client_gender = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Gender",
        key_category="User_Inputs_Shiny",
    )
    primary_client_tolerance_risk = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Tolerance_Risk",
        key_category="User_Inputs_Shiny",
    )
    primary_client_state = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_State",
        key_category="User_Inputs_Shiny",
    )
    primary_client_code_zip = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Code_Zip",
        key_category="User_Inputs_Shiny",
    )
    partner_client_name = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Name",
        key_category="User_Inputs_Shiny",
    )
    partner_client_age_current = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Current",
        key_category="User_Inputs_Shiny",
    )
    partner_client_age_retirement = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Retirement",
        key_category="User_Inputs_Shiny",
    )
    partner_client_age_income_starting = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Age_Income_Starting",
        key_category="User_Inputs_Shiny",
    )
    partner_client_status_marital = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Status_Marital",
        key_category="User_Inputs_Shiny",
    )
    partner_client_gender = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Gender",
        key_category="User_Inputs_Shiny",
    )
    partner_client_tolerance_risk = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Tolerance_Risk",
        key_category="User_Inputs_Shiny",
    )
    partner_client_state = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_State",
        key_category="User_Inputs_Shiny",
    )
    partner_client_code_zip = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_client_Partner_Code_Zip",
        key_category="User_Inputs_Shiny",
    )

    primary_age_current_int = (
        int(primary_client_age_current)
        if primary_client_age_current and not isinstance(primary_client_age_current, bool)
        else 0
    )
    primary_age_retirement_int = (
        int(primary_client_age_retirement)
        if primary_client_age_retirement and not isinstance(primary_client_age_retirement, bool)
        else 0
    )
    primary_age_income_starting_int = (
        int(primary_client_age_income_starting)
        if primary_client_age_income_starting and not isinstance(primary_client_age_income_starting, bool)
        else 0
    )
    partner_age_current_int = (
        int(partner_client_age_current)
        if partner_client_age_current and not isinstance(partner_client_age_current, bool)
        else 0
    )
    partner_age_retirement_int = (
        int(partner_client_age_retirement)
        if partner_client_age_retirement and not isinstance(partner_client_age_retirement, bool)
        else 0
    )
    partner_age_income_starting_int = (
        int(partner_client_age_income_starting)
        if partner_client_age_income_starting
        and not isinstance(partner_client_age_income_starting, bool)
        else 0
    )

    include_partner_raw = get_value_from_reactives_shiny_runtime(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis",
        key_category="User_Inputs_Shiny",
    )
    include_partner = bool(include_partner_raw) if include_partner_raw is not None else False

    info_categories = [
        "Name",
        "Current Age",
        "Retirement Age",
        "Income Starting Age",
        "Marital Status",
        "Gender",
        "Risk Tolerance",
        "State",
        "ZIP Code",
    ]
    primary_col = [
        str(primary_client_name) if primary_client_name else "Not Provided",
        f"{primary_age_current_int} years" if primary_age_current_int > 0 else "Not Specified",
        f"{primary_age_retirement_int} years"
        if primary_age_retirement_int > 0
        else "Not Specified",
        f"{primary_age_income_starting_int} years"
        if primary_age_income_starting_int > 0
        else "Not Specified",
        str(primary_client_status_marital) if primary_client_status_marital else "Not Specified",
        str(primary_client_gender) if primary_client_gender else "Not Specified",
        str(primary_client_tolerance_risk)
        if primary_client_tolerance_risk
        else "Not Specified",
        str(primary_client_state) if primary_client_state else "Not Specified",
        _format_zip_code(value_zip=primary_client_code_zip) if primary_client_code_zip else "Not Provided",
    ]

    if include_partner:
        partner_col = [
            str(partner_client_name) if partner_client_name else "Not Provided",
            f"{partner_age_current_int} years" if partner_age_current_int > 0 else "Not Specified",
            f"{partner_age_retirement_int} years"
            if partner_age_retirement_int > 0
            else "Not Specified",
            f"{partner_age_income_starting_int} years"
            if partner_age_income_starting_int > 0
            else "Not Specified",
            str(partner_client_status_marital) if partner_client_status_marital else "Not Specified",
            str(partner_client_gender) if partner_client_gender else "Not Specified",
            str(partner_client_tolerance_risk)
            if partner_client_tolerance_risk
            else "Not Specified",
            str(partner_client_state) if partner_client_state else "Not Specified",
            _format_zip_code(value_zip=partner_client_code_zip) if partner_client_code_zip else "Not Provided",
        ]
        data_Personal_Info_DF = pl.DataFrame(
            {
                "Field Name": info_categories,
                "Client Primary": primary_col,
                "Client Partner": partner_col,
            },
        )
    else:
        data_Personal_Info_DF = pl.DataFrame(
            {
                "Field Name": info_categories,
                "Client Primary": primary_col,
            },
        )

    expected_columns = ["Field Name", "Client Primary"]
    actual_columns = data_Personal_Info_DF.columns
    if not all(value_column in actual_columns for value_column in expected_columns):
        missing_columns = [
            value_column for value_column in expected_columns if value_column not in actual_columns
        ]
        raise Exception_Validation_Input(
            f"Summary table missing expected columns: {missing_columns}",
        )

    if data_Personal_Info_DF.height == 0:
        raise Exception_Validation_Input(
            "Summary table is empty - no personal information data available",
        )

    return data_Personal_Info_DF



def calc_table_summary_clients_goals(
    *, reactives_shiny: dict[str, Any]) -> pl.DataFrame:
    """Generate the financial goals summary dataframe."""
    value_Primary_Essential = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Essential",
        key_category="User_Inputs_Shiny",
    )
    value_Primary_Important = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Important",
        key_category="User_Inputs_Shiny",
    )
    value_Primary_Aspirational = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Primary_Goal_Aspirational",
        key_category="User_Inputs_Shiny",
    )
    value_Partner_Essential = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Essential",
        key_category="User_Inputs_Shiny",
    )
    value_Partner_Important = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Important",
        key_category="User_Inputs_Shiny",
    )
    value_Partner_Aspirational = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Goals_client_Partner_Goal_Aspirational",
        key_category="User_Inputs_Shiny",
    )

    value_Primary_Essential = int(max(0, value_Primary_Essential or 0))
    value_Primary_Important = int(max(0, value_Primary_Important or 0))
    value_Primary_Aspirational = int(max(0, value_Primary_Aspirational or 0))
    value_Partner_Essential = int(max(0, value_Partner_Essential or 0))
    value_Partner_Important = int(max(0, value_Partner_Important or 0))
    value_Partner_Aspirational = int(max(0, value_Partner_Aspirational or 0))

    value_Primary_Total = (
        value_Primary_Essential + value_Primary_Important + value_Primary_Aspirational
    )
    value_Partner_Total = (
        value_Partner_Essential + value_Partner_Important + value_Partner_Aspirational
    )
    value_Combined_Essential = value_Primary_Essential + value_Partner_Essential
    value_Combined_Important = value_Primary_Important + value_Partner_Important
    value_Combined_Aspirational = value_Primary_Aspirational + value_Partner_Aspirational
    value_Combined_Total = value_Primary_Total + value_Partner_Total

    include_partner_raw = get_value_from_reactives_shiny(
        reactives_shiny=reactives_shiny,
        key_name="Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis",
        key_category="User_Inputs_Shiny",
    )
    include_partner = bool(include_partner_raw) if include_partner_raw is not None else False

    goal_categories = [
        "Essential Goals",
        "Important Goals",
        "Aspirational Goals",
        "Total Goals",
    ]
    primary_col = [
        value_Primary_Essential,
        value_Primary_Important,
        value_Primary_Aspirational,
        value_Primary_Total,
    ]
    combined_col = [
        value_Combined_Essential,
        value_Combined_Important,
        value_Combined_Aspirational,
        value_Combined_Total,
    ]
    if include_partner:
        data_Goals_DF = pl.DataFrame(
            {
                "Field Name": goal_categories,
                "Client Primary": primary_col,
                "Client Partner": [
                    value_Partner_Essential,
                    value_Partner_Important,
                    value_Partner_Aspirational,
                    value_Partner_Total,
                ],
                "Combined Total": combined_col,
            },
        )
    else:
        data_Goals_DF = pl.DataFrame(
            {
                "Field Name": goal_categories,
                "Client Primary": primary_col,
                "Combined Total": combined_col,
            },
        )

    if data_Goals_DF is None or data_Goals_DF.height == 0:
        raise Exception_Validation_Input("Failed to create data_Goals_DF dataframe")

    return data_Goals_DF



def calc_table_summary_clients_income(
    *, reactives_shiny: dict[str, Any]) -> pl.DataFrame:
    """Generate the income-sources summary dataframe."""
    try:
        value_Primary_Social_Security = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Social_Security",
            key_category="User_Inputs_Shiny",
        )
        value_Primary_Pension = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Pension",
            key_category="User_Inputs_Shiny",
        )
        value_Primary_Annuity = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Annuity_Existing",
            key_category="User_Inputs_Shiny",
        )
        value_Primary_Other = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Primary_Income_Other",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Social_Security = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Social_Security",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Pension = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Pension",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Annuity = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Annuity_Existing",
            key_category="User_Inputs_Shiny",
        )
        value_Partner_Other = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Income_client_Partner_Income_Other",
            key_category="User_Inputs_Shiny",
        )

        value_Primary_Social_Security = int(max(0, value_Primary_Social_Security or 0))
        value_Primary_Pension = int(max(0, value_Primary_Pension or 0))
        value_Primary_Annuity = int(max(0, value_Primary_Annuity or 0))
        value_Primary_Other = int(max(0, value_Primary_Other or 0))
        value_Partner_Social_Security = int(max(0, value_Partner_Social_Security or 0))
        value_Partner_Pension = int(max(0, value_Partner_Pension or 0))
        value_Partner_Annuity = int(max(0, value_Partner_Annuity or 0))
        value_Partner_Other = int(max(0, value_Partner_Other or 0))

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
        value_Combined_Social_Security = (
            value_Primary_Social_Security + value_Partner_Social_Security
        )
        value_Combined_Pension = value_Primary_Pension + value_Partner_Pension
        value_Combined_Annuity = value_Primary_Annuity + value_Partner_Annuity
        value_Combined_Other = value_Primary_Other + value_Partner_Other
        value_Combined_Total = value_Primary_Total + value_Partner_Total

        include_partner_raw = get_value_from_reactives_shiny(
            reactives_shiny=reactives_shiny,
            key_name="Input_Tab_clients_Subtab_clients_Personal_Info_Include_Partner_In_Analysis",
            key_category="User_Inputs_Shiny",
        )
        include_partner = bool(include_partner_raw) if include_partner_raw is not None else False

        income_categories = [
            "Social Security",
            "Pension Income",
            "Existing Annuity",
            "Other Income",
            "Total Income",
        ]
        primary_col = [
            value_Primary_Social_Security,
            value_Primary_Pension,
            value_Primary_Annuity,
            value_Primary_Other,
            value_Primary_Total,
        ]
        combined_col = [
            value_Combined_Social_Security,
            value_Combined_Pension,
            value_Combined_Annuity,
            value_Combined_Other,
            value_Combined_Total,
        ]
        if include_partner:
            data_Income_DF = pl.DataFrame(
                {
                    "Field Name": income_categories,
                    "Client Primary": primary_col,
                    "Client Partner": [
                        value_Partner_Social_Security,
                        value_Partner_Pension,
                        value_Partner_Annuity,
                        value_Partner_Other,
                        value_Partner_Total,
                    ],
                    "Combined Total": combined_col,
                },
            )
        else:
            data_Income_DF = pl.DataFrame(
                {
                    "Field Name": income_categories,
                    "Client Primary": primary_col,
                    "Combined Total": combined_col,
                },
            )

        if data_Income_DF is None or data_Income_DF.height == 0:
            raise Exception_Validation_Input("Failed to create data_Income_DF dataframe")

        return data_Income_DF

    except Exception as exc_error:
        (f"Error generating income calculation: {type(exc_error).__name__}: {exc_error!s}")
        return pl.DataFrame(
            {
                "Field Name": ["Error"],
                "Client Primary": [0.0],
                "Combined Total": [0.0],
            },
        )
