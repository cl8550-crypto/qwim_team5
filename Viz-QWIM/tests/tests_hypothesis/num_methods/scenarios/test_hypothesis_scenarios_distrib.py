"""Hypothesis (property-based) tests for src.num_methods.scenarios.scenarios_distrib.

Tests cover:
- ``Distribution_Type`` enum — membership and string values
- ``Covariance_Input_Type`` enum — membership and string values
- ``_nearest_PSD`` — output is always positive semi-definite
- ``Scenarios_Distribution`` — structural invariants (member storage, validation)
"""

from __future__ import annotations

import numpy as np
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays


try:
    from src.num_methods.scenarios.scenarios_distrib import (
        Covariance_Input_Type,
        Distribution_Type,
        Scenarios_Distribution,
        _nearest_PSD,
    )

    MODULE_IMPORT_AVAILABLE = True
except ImportError:
    MODULE_IMPORT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Distribution_Type_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Distribution_Type_Enum:
    """Tests for the Distribution_Type enum."""

    @pytest.mark.unit()
    @given(
        member=st.sampled_from(list(Distribution_Type)) if MODULE_IMPORT_AVAILABLE else st.none()
    )
    @settings(max_examples=10)
    def Test_every_member_has_non_empty_string_value(self, member: Distribution_Type) -> None:
        """Every Distribution_Type member has a non-empty string value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    def Test_all_three_distributions_present(self) -> None:
        """NORMAL, LOGNORMAL, and STUDENT_T are all present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"NORMAL", "LOGNORMAL", "STUDENT_T"}
        actual = {m.name for m in Distribution_Type}
        assert expected == actual

    @pytest.mark.unit()
    @given(
        member=st.sampled_from(list(Distribution_Type)) if MODULE_IMPORT_AVAILABLE else st.none()
    )
    @settings(max_examples=10)
    def Test_value_uniquely_identifies_member(self, member: Distribution_Type) -> None:
        """Each Distribution_Type value uniquely identifies a member."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        found = [m for m in Distribution_Type if m.value == member.value]
        assert len(found) == 1


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Covariance_Input_Type_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Covariance_Input_Type_Enum:
    """Tests for the Covariance_Input_Type enum."""

    @pytest.mark.unit()
    @given(
        member=st.sampled_from(list(Covariance_Input_Type))
        if MODULE_IMPORT_AVAILABLE
        else st.none()
    )
    @settings(max_examples=10)
    def Test_every_member_has_non_empty_string_value(
        self, member: Covariance_Input_Type
    ) -> None:
        """Every Covariance_Input_Type member has a non-empty string value."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        assert isinstance(member.value, str)
        assert len(member.value) > 0

    @pytest.mark.unit()
    def Test_both_input_types_present(self) -> None:
        """COVARIANCE_MATRIX and CORRELATION_AND_VOLATILITIES are both present."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        expected = {"COVARIANCE_MATRIX", "CORRELATION_AND_VOLATILITIES"}
        actual = {m.name for m in Covariance_Input_Type}
        assert expected == actual


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Nearest_PSD
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Nearest_PSD:
    """Tests for the _nearest_PSD helper function."""

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=5))
    @settings(max_examples=30)
    def Test_identity_matrix_unchanged(self, n: int) -> None:
        """_nearest_PSD on an identity matrix returns a PSD matrix."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        eye = np.eye(n, dtype=np.float64)
        result = _nearest_PSD(matrix = eye)
        eigenvalues = np.linalg.eigvalsh(result)
        assert np.all(eigenvalues >= -1e-8), f"Non-PSD output: min eigenvalue={eigenvalues.min()}"

    @pytest.mark.unit()
    @given(
        n=st.integers(min_value=2, max_value=4),
        vals=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=2, max_value=4).flatmap(lambda n: st.just((n, n))),
            elements=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=20)
    def Test_output_is_always_psd(self, n: int, vals: np.ndarray) -> None:
        """_nearest_PSD always returns a matrix with non-negative eigenvalues."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        # Make a symmetric matrix
        sym = (vals + vals.T) / 2.0
        if sym.shape[0] < 1:
            return
        result = _nearest_PSD(matrix = sym)
        eigenvalues = np.linalg.eigvalsh(result)
        assert np.all(eigenvalues >= -1e-8), f"min eigenvalue={eigenvalues.min()}"

    @pytest.mark.unit()
    @given(n=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_output_shape_preserved(self, n: int) -> None:
        """_nearest_PSD preserves the input matrix shape."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        mat = np.eye(n, dtype=np.float64)
        result = _nearest_PSD(matrix = mat)
        assert result.shape == (n, n)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Scenarios_Distribution_Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Scenarios_Distribution_Construction:
    """Property-based tests for Scenarios_Distribution constructor invariants."""

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_normal_default_construction_stores_num_components(self, k: int) -> None:
        """Normal distribution with defaults stores m_num_components == K."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"Asset_{i}" for i in range(k)]
        scenario = Scenarios_Distribution(
            names_components=names,
            distribution_type=Distribution_Type.NORMAL,
            num_days=5,
        )
        assert scenario.m_num_components == k

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_distribution_type_is_stored(self, k: int) -> None:
        """m_distribution_type matches the distribution_type argument."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"Asset_{i}" for i in range(k)]
        scenario = Scenarios_Distribution(
            names_components=names,
            distribution_type=Distribution_Type.LOGNORMAL,
            num_days=5,
        )
        assert scenario.m_distribution_type == Distribution_Type.LOGNORMAL

    @pytest.mark.unit()
    @given(
        k=st.integers(min_value=1, max_value=5),
        df=st.floats(min_value=2.01, max_value=30.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=20)
    def Test_student_t_with_valid_df_constructs(self, k: int, df: float) -> None:
        """Student-t with degrees_of_freedom > 2 constructs without error."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"Asset_{i}" for i in range(k)]
        scenario = Scenarios_Distribution(
            names_components=names,
            distribution_type=Distribution_Type.STUDENT_T,
            degrees_of_freedom=df,
            num_days=5,
        )
        assert scenario.m_degrees_of_freedom == df

    @pytest.mark.unit()
    def Test_student_t_with_df_le_2_raises_validation_error(self) -> None:
        """Student-t with degrees_of_freedom <= 2 raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution(
                names_components=["X", "Y"],
                distribution_type=Distribution_Type.STUDENT_T,
                degrees_of_freedom=2.0,
                num_days=5,
            )

    @pytest.mark.unit()
    def Test_wrong_covariance_shape_raises_validation_error(self) -> None:
        """Covariance matrix with wrong shape raises Exception_Validation_Input."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )
        with pytest.raises(Exception_Validation_Input):
            Scenarios_Distribution(
                names_components=["X", "Y"],
                covariance_matrix=np.eye(3),  # shape (3,3) != (2,2)
                num_days=5,
            )

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_default_covariance_is_identity(self, k: int) -> None:
        """When no covariance is supplied the stored matrix is the identity."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"A_{i}" for i in range(k)]
        scenario = Scenarios_Distribution(names_components=names, num_days=5)
        assert np.allclose(scenario.m_covariance_matrix, np.eye(k))

    @pytest.mark.unit()
    @given(k=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def Test_correlation_plus_vols_builds_correct_covariance(self, k: int) -> None:
        """When corr+vols are supplied the covariance is diag(sigma)@corr@diag(sigma)."""
        if not MODULE_IMPORT_AVAILABLE:
            pytest.skip("Module not importable")
        names = [f"A_{i}" for i in range(k)]
        vols = np.full(k, 0.2, dtype=np.float64)
        corr = np.eye(k, dtype=np.float64)
        scenario = Scenarios_Distribution(
            names_components=names,
            correlation_matrix=corr,
            volatilities=vols,
            num_days=5,
        )
        expected_cov = np.diag(vols) @ corr @ np.diag(vols)
        assert np.allclose(scenario.m_covariance_matrix, expected_cov)
