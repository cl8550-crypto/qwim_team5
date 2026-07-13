"""Hypothesis (property-based) tests for src.num_methods.scenarios.scenarios_CMA.

Tests cover:
- ``Asset_Class_Tier`` enum — membership and integer values
- ``CMA_Source`` enum — membership and string values
- ``Scenarios_CMA`` — structural invariants (array shapes, member storage)
"""

from __future__ import annotations

import numpy as np
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st


try:
    from src.num_methods.scenarios.scenarios_CMA import (
        Asset_Class_Tier,
        CMA_Source,
        Scenarios_CMA,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cma_inputs(k: int) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Return valid (names, returns, vols, corr) for K asset classes."""
    names = [f"Asset_{i}" for i in range(k)]
    returns = np.full(k, 0.07, dtype=np.float64)
    vols = np.full(k, 0.15, dtype=np.float64)
    corr = np.eye(k, dtype=np.float64)
    return names, returns, vols, corr


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Asset_Class_Tier_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Asset_Class_Tier_Enum:
    """Tests for the Asset_Class_Tier enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Asset_Class_Tier)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=10)
    def Test_every_member_has_non_negative_int_value(self, member: Asset_Class_Tier) -> None:
        """Every Asset_Class_Tier member has a non-negative integer value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, int)
        assert member.value >= 0

    @pytest.mark.unit()
    def Test_all_three_tiers_present(self) -> None:
        """TIER_0, TIER_1, TIER_2 are all present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"TIER_0", "TIER_1", "TIER_2"}
        actual = {m.name for m in Asset_Class_Tier}
        assert expected == actual

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(Asset_Class_Tier)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=10)
    def Test_value_is_unique_per_member(self, member: Asset_Class_Tier) -> None:
        """Each Asset_Class_Tier value uniquely identifies a member."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        found = [m for m in Asset_Class_Tier if m.value == member.value]
        assert len(found) == 1


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_CMA_Source_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_CMA_Source_Enum:
    """Tests for the CMA_Source enum."""

    @pytest.mark.unit()
    @given(member=st.sampled_from(list(CMA_Source)) if MODULE_IMPORT_AVAILABLE else st.none())
    @settings(max_examples=10)
    def Test_every_member_has_non_empty_string_value(self, member: CMA_Source) -> None:
        """Every CMA_Source member has a non-empty string value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    def Test_both_sources_present(self) -> None:
        """SPREADSHEET and MANUAL are both present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"SPREADSHEET", "MANUAL"}
        actual = {m.name for m in CMA_Source}
        assert expected == actual


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Scenarios_CMA_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Scenarios_CMA_Construction:
    """Property-based tests for Scenarios_CMA constructor invariants."""

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=6))
    @settings(max_examples=20)
    def Test_num_components_matches_k(self, k: int) -> None:
        """m_num_components equals the number of asset classes supplied."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names, returns, vols, corr = _make_cma_inputs(k)
        scenario = Scenarios_CMA(
            names_asset_classes=names,
            expected_returns_annual=returns,
            expected_vols_annual=vols,
            correlation_matrix=corr,
            num_days=5,
        )
        assert scenario.m_num_components == k

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=6))
    @settings(max_examples=20)
    def Test_covariance_matrix_annual_shape(self, k: int) -> None:
        """m_covariance_matrix_annual has shape (K, K)."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names, returns, vols, corr = _make_cma_inputs(k)
        scenario = Scenarios_CMA(
            names_asset_classes=names,
            expected_returns_annual=returns,
            expected_vols_annual=vols,
            correlation_matrix=corr,
            num_days=5,
        )
        assert scenario.m_covariance_matrix_annual.shape == (k, k)

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=6))
    @settings(max_examples=20)
    def Test_covariance_matrix_annual_is_symmetric(self, k: int) -> None:
        """m_covariance_matrix_annual is symmetric."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names, returns, vols, corr = _make_cma_inputs(k)
        scenario = Scenarios_CMA(
            names_asset_classes=names,
            expected_returns_annual=returns,
            expected_vols_annual=vols,
            correlation_matrix=corr,
            num_days=5,
        )
        mat = scenario.m_covariance_matrix_annual
        assert np.allclose(mat, mat.T, atol=1e-10)

    @pytest.mark.unit()
    def Test_wrong_returns_shape_raises_validation_error(self) -> None:
        """expected_returns_annual with wrong shape raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        names = ["A", "B", "C"]
        with pytest.raises(Exception_Validation_Input):
            Scenarios_CMA(
                names_asset_classes=names,
                expected_returns_annual=np.array([0.07, 0.05]),  # shape (2,) != (3,)
                expected_vols_annual=np.full(3, 0.15),
                correlation_matrix=np.eye(3),
                num_days=5,
            )

    @pytest.mark.unit()
    def Test_wrong_vols_shape_raises_validation_error(self) -> None:
        """expected_vols_annual with wrong shape raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        names = ["A", "B"]
        with pytest.raises(Exception_Validation_Input):
            Scenarios_CMA(
                names_asset_classes=names,
                expected_returns_annual=np.full(2, 0.07),
                expected_vols_annual=np.array([0.15]),  # shape (1,) != (2,)
                correlation_matrix=np.eye(2),
                num_days=5,
            )

    @pytest.mark.unit()
    def Test_wrong_correlation_shape_raises_validation_error(self) -> None:
        """correlation_matrix with wrong shape raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        names = ["A", "B"]
        with pytest.raises(Exception_Validation_Input):
            Scenarios_CMA(
                names_asset_classes=names,
                expected_returns_annual=np.full(2, 0.07),
                expected_vols_annual=np.full(2, 0.15),
                correlation_matrix=np.eye(3),  # shape (3,3) != (2,2)
                num_days=5,
            )

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=6))
    @settings(max_examples=15)
    def Test_source_stored_correctly(self, k: int) -> None:
        """m_source matches the source argument passed to constructor."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names, returns, vols, corr = _make_cma_inputs(k)
        scenario = Scenarios_CMA(
            names_asset_classes=names,
            expected_returns_annual=returns,
            expected_vols_annual=vols,
            correlation_matrix=corr,
            source=CMA_Source.SPREADSHEET,
            num_days=5,
        )
        assert scenario.m_source == CMA_Source.SPREADSHEET
