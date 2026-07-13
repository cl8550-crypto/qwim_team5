"""Regression tests for utils_client validation functions.

Snapshots are structured validation outputs stored as Polars DataFrames
in Parquet format (no PDF byte-hashing).

Usage
-----
    # Generate baselines:
    REGENERATE_BASELINES=1 pytest tests/tests_regression/clients_QWIM/ -q

    # Assert no regression:
    pytest tests/tests_regression/clients_QWIM/ -q -m regression
"""

from __future__ import annotations

import os

import polars as pl
import pytest

from src.clients_QWIM.utils_client import (
    build_checkbox_fields_by_section,
    validate_extracted_client_data,
    validate_required_advisor_info_section,
    worksheet_has_client_partner,
)

from .conftest import (
    _assert_frames_approx_equal,
    _make_data_with_invalid_fields,
    _make_single_client_data,
    load_baseline,
    save_baseline,
)


REGENERATE = os.getenv("REGENERATE_BASELINES", "0") == "1"


# ===========================================================================
# validate_extracted_client_data — valid data
# ===========================================================================


class Class_Test_Regression_Validate_Valid_Data:
    """Regression tests for validate_extracted_client_data with valid input."""

    @pytest.mark.regression()
    def Test_Valid_Single_Client_Returns_No_Warnings(
        self, valid_single_client_data
    ) -> None:
        """Valid single-client data produces zero warnings snapshot."""
        is_valid, warnings = validate_extracted_client_data(extracted_data = valid_single_client_data)

        df = pl.DataFrame(
            {
                "is_valid": [is_valid],
                "num_warnings": [len(warnings)],
            }
        )

        if REGENERATE:
            save_baseline(df, "validate_valid_single_summary.parquet")
            return

        baseline = load_baseline("validate_valid_single_summary.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Valid_Single_Client_Warning_List(
        self, valid_single_client_data
    ) -> None:
        """Warning messages list matches empty-list baseline for valid data."""
        _is_valid, warnings = validate_extracted_client_data(extracted_data = valid_single_client_data)

        df = pl.DataFrame({"warnings": warnings if warnings else [""]})

        if REGENERATE:
            save_baseline(df, "validate_valid_single_warnings.parquet")
            return

        baseline = load_baseline("validate_valid_single_warnings.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# validate_extracted_client_data — invalid data
# ===========================================================================


class Class_Test_Regression_Validate_Invalid_Data:
    """Regression tests for validate_extracted_client_data with invalid input."""

    @pytest.mark.regression()
    def Test_Invalid_Fields_Returns_Warnings(
        self, invalid_fields_data
    ) -> None:
        """Invalid-field data produces known warning set snapshot."""
        is_valid, warnings = validate_extracted_client_data(extracted_data = invalid_fields_data)

        df = pl.DataFrame(
            {
                "is_valid": [is_valid],
                "num_warnings": [len(warnings)],
            }
        )

        if REGENERATE:
            save_baseline(df, "validate_invalid_summary.parquet")
            return

        baseline = load_baseline("validate_invalid_summary.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Invalid_Fields_Warning_Messages(
        self, invalid_fields_data
    ) -> None:
        """Individual warning messages match baseline for invalid data."""
        _is_valid, warnings = validate_extracted_client_data(extracted_data = invalid_fields_data)

        df = pl.DataFrame({"warnings": sorted(warnings)})

        if REGENERATE:
            save_baseline(df, "validate_invalid_warnings.parquet")
            return

        baseline = load_baseline("validate_invalid_warnings.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# validate_required_advisor_info_section
# ===========================================================================


class Class_Test_Regression_Advisor_Info_Validation:
    """Regression tests for validate_required_advisor_info_section."""

    @pytest.mark.regression()
    def Test_Valid_Advisor_Info_Returns_Empty_List(
        self, valid_single_client_data
    ) -> None:
        """No missing/invalid advisor fields produces empty-list snapshot."""
        messages = validate_required_advisor_info_section(extracted_data = valid_single_client_data)

        df = pl.DataFrame({"messages": messages if messages else [""]})

        if REGENERATE:
            save_baseline(df, "advisor_info_valid_messages.parquet")
            return

        baseline = load_baseline("advisor_info_valid_messages.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Missing_Email_Returns_Message(self) -> None:
        """Missing email field produces expected snapshot."""
        data = _make_single_client_data()
        data["Advisor_Info"]["email"] = ""

        messages = validate_required_advisor_info_section(extracted_data = data)
        df = pl.DataFrame({"messages": sorted(messages)})

        if REGENERATE:
            save_baseline(df, "advisor_info_missing_email.parquet")
            return

        baseline = load_baseline("advisor_info_missing_email.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# build_checkbox_fields_by_section
# ===========================================================================


class Class_Test_Regression_Checkbox_Fields:
    """Regression test for build_checkbox_fields_by_section output structure."""

    @pytest.mark.regression()
    def Test_Checkbox_Fields_Snapshot(self) -> None:
        """build_checkbox_fields_by_section output matches baseline."""
        result = build_checkbox_fields_by_section()

        # Serialize: rows of (section_name, checkbox_key)
        rows = sorted(
            (section, key)
            for section, keys in result.items()
            for key in keys
        )
        df = pl.DataFrame(
            {
                "section": [r[0] for r in rows],
                "checkbox_key": [r[1] for r in rows],
            }
        )

        if REGENERATE:
            save_baseline(df, "checkbox_fields_by_section.parquet")
            return

        baseline = load_baseline("checkbox_fields_by_section.parquet")
        _assert_frames_approx_equal(df, baseline)


# ===========================================================================
# worksheet_has_client_partner
# ===========================================================================


class Class_Test_Regression_Worksheet_Has_Partner:
    """Regression tests for worksheet_has_client_partner."""

    @pytest.mark.regression()
    def Test_Single_Client_Returns_False(
        self, valid_single_client_data
    ) -> None:
        """Single-client worksheet correctly identified as no-partner."""
        result = worksheet_has_client_partner(extracted_data = valid_single_client_data)
        df = pl.DataFrame({"has_partner": [result]})

        if REGENERATE:
            save_baseline(df, "worksheet_has_partner_single.parquet")
            return

        baseline = load_baseline("worksheet_has_partner_single.parquet")
        _assert_frames_approx_equal(df, baseline)

    @pytest.mark.regression()
    def Test_Couple_Data_Returns_True(self) -> None:
        """Couple worksheet correctly identified as has-partner."""
        data = _make_single_client_data()
        data["Personal_Info"]["client_partner"]["name"] = "Jane Doe"

        result = worksheet_has_client_partner(extracted_data = data)
        df = pl.DataFrame({"has_partner": [result]})

        if REGENERATE:
            save_baseline(df, "worksheet_has_partner_couple.parquet")
            return

        baseline = load_baseline("worksheet_has_partner_couple.parquet")
        _assert_frames_approx_equal(df, baseline)
