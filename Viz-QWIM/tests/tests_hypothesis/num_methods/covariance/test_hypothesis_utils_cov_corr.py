"""Hypothesis (property-based) tests for src.num_methods.covariance.utils_cov_corr.

Tests cover:
- ``covariance_estimator`` enum — membership and values
- ``distance_estimator_type`` enum — classification class-methods
- ``covariance_matrix`` — structural invariants (symmetry, PSD, finite values)
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays


from src.num_methods.covariance.utils_cov_corr import (
    Covariance_Estimator,
    Covariance_Matrix,
    Distance_Estimator_Type,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SIMPLE_ESTIMATORS = [
    Covariance_Estimator.EMPIRICAL,
    Covariance_Estimator.LEDOIT_WOLF,
    Covariance_Estimator.ORACLE_APPROXIMATING_SHRINKAGE,
    Covariance_Estimator.SHRUNK_COVARIANCE,
]


def _make_returns_df(
    returns_array: np.ndarray,
    n_assets: int,
) -> pl.DataFrame:
    """Wrap a numpy returns array into a Polars DataFrame with Date column."""
    dates = [f"2024-{(i % 12) + 1:02d}-01" for i in range(len(returns_array))]
    data: dict[str, list] = {"Date": dates}
    for idx_asset in range(n_assets):
        data[f"Asset_{idx_asset:02d}"] = returns_array[:, idx_asset].tolist()
    return pl.DataFrame(data)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Covariance_Estimator_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Covariance_Estimator_Enum:
    """Tests for the covariance_estimator enum."""

    @pytest.mark.unit()
    @given(
        idx_estimator=st.sampled_from(list(Covariance_Estimator)),
    )
    @settings(max_examples=200)
    def Test_enum_member_has_non_empty_value(
        self,
        idx_estimator: Covariance_Estimator,
    ) -> None:
        """Every covariance_estimator member has a non-empty string value."""
        assert isinstance(idx_estimator.value, str)
        assert len(idx_estimator.value) > 0

    @pytest.mark.unit()
    @given(
        idx_estimator=st.sampled_from(list(Covariance_Estimator)),
    )
    @settings(max_examples=200)
    def Test_enum_member_is_unique_value(
        self,
        idx_estimator: Covariance_Estimator,
    ) -> None:
        """Each enum value uniquely identifies the member."""
        found = [e for e in Covariance_Estimator if e.value == idx_estimator.value]
        assert len(found) == 1

    @pytest.mark.unit()
    def Test_all_expected_estimators_present(self) -> None:
        """All ten documented estimators are present in the enum."""
        expected_names = {
            "EMPIRICAL",
            "GERBER",
            "DENOISING",
            "DETONING",
            "EXPONENTIALLY_WEIGHTED",
            "LEDOIT_WOLF",
            "ORACLE_APPROXIMATING_SHRINKAGE",
            "SHRUNK_COVARIANCE",
            "GRAPHICAL_LASSO_CV",
            "IMPLIED_COVARIANCE",
        }
        actual_names = {e.name for e in Covariance_Estimator}
        assert expected_names.issubset(actual_names)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Distance_Estimator_Type_Enum
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Distance_Estimator_Type_Enum:
    """Tests for the distance_estimator_type enum and its classification methods."""

    @pytest.mark.unit()
    @given(
        idx_dist=st.sampled_from(list(Distance_Estimator_Type)),
    )
    @settings(max_examples=200)
    def Test_distance_member_has_non_empty_value(
        self,
        idx_dist: Distance_Estimator_Type,
    ) -> None:
        """Every distance_estimator_type member has a non-empty string value."""
        assert isinstance(idx_dist.value, str)
        assert len(idx_dist.value) > 0

    @pytest.mark.unit()
    def Test_correlation_based_subset_of_all_members(self) -> None:
        """get_correlation_based() returns a subset of all members."""
        all_members = set(Distance_Estimator_Type)
        corr_based = set(Distance_Estimator_Type.get_correlation_based())
        assert corr_based.issubset(all_members)
        assert len(corr_based) == 3

    @pytest.mark.unit()
    def Test_covariance_based_subset_of_all_members(self) -> None:
        """get_covariance_based() returns a subset of all members."""
        all_members = set(Distance_Estimator_Type)
        cov_based = set(Distance_Estimator_Type.get_covariance_based())
        assert cov_based.issubset(all_members)
        assert len(cov_based) == 3

    @pytest.mark.unit()
    def Test_rank_based_subset_of_all_members(self) -> None:
        """get_rank_based() returns a subset of all members."""
        all_members = set(Distance_Estimator_Type)
        rank_based = set(Distance_Estimator_Type.get_rank_based())
        assert rank_based.issubset(all_members)

    @pytest.mark.unit()
    def Test_information_theoretic_subset_of_all_members(self) -> None:
        """get_information_theoretic() returns a subset of all members."""
        all_members = set(Distance_Estimator_Type)
        info_theoretic = set(Distance_Estimator_Type.get_information_theoretic())
        assert info_theoretic.issubset(all_members)
        assert Distance_Estimator_Type.VARIATION_OF_INFORMATION in info_theoretic

    @pytest.mark.unit()
    def Test_corr_and_cov_based_are_disjoint(self) -> None:
        """Correlation-based and covariance-based estimator sets are disjoint."""
        corr_based = set(Distance_Estimator_Type.get_correlation_based())
        cov_based = set(Distance_Estimator_Type.get_covariance_based())
        assert corr_based.isdisjoint(cov_based)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Covariance_Matrix_Invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Covariance_Matrix_Invariants:
    """Tests that covariance_matrix produces structurally valid matrices."""

    @pytest.mark.unit()
    @given(
        n_assets=st.integers(min_value=2, max_value=6),
        n_obs=st.integers(min_value=30, max_value=60),
        estimator=st.sampled_from(_SIMPLE_ESTIMATORS),
    )
    @settings(max_examples=50, deadline=None)
    def Test_matrix_is_symmetric(
        self,
        n_assets: int,
        n_obs: int,
        estimator: Covariance_Estimator,
    ) -> None:
        """Output covariance matrix is symmetric."""
        rng = np.random.default_rng(seed=42)
        returns_array = rng.standard_normal((n_obs, n_assets)) * 0.01
        df_returns = _make_returns_df(returns_array, n_assets)
        cov_obj = Covariance_Matrix(data_returns=df_returns, estimator=estimator)
        mat = cov_obj.m_cov_matrix
        assert np.allclose(mat, mat.T, atol=1e-10)

    @pytest.mark.unit()
    @given(
        n_assets=st.integers(min_value=2, max_value=6),
        n_obs=st.integers(min_value=30, max_value=60),
        estimator=st.sampled_from(_SIMPLE_ESTIMATORS),
    )
    @settings(max_examples=50, deadline=None)
    def Test_diagonal_elements_are_positive(
        self,
        n_assets: int,
        n_obs: int,
        estimator: Covariance_Estimator,
    ) -> None:
        """Diagonal elements of the covariance matrix (variances) are positive."""
        rng = np.random.default_rng(seed=7)
        returns_array = rng.standard_normal((n_obs, n_assets)) * 0.01
        df_returns = _make_returns_df(returns_array, n_assets)
        cov_obj = Covariance_Matrix(data_returns=df_returns, estimator=estimator)
        diag = np.diag(cov_obj.m_cov_matrix)
        assert np.all(diag > 0)

    @pytest.mark.unit()
    @given(
        n_assets=st.integers(min_value=2, max_value=6),
        n_obs=st.integers(min_value=30, max_value=60),
        estimator=st.sampled_from(_SIMPLE_ESTIMATORS),
    )
    @settings(max_examples=50, deadline=None)
    def Test_matrix_has_no_nan_or_inf(
        self,
        n_assets: int,
        n_obs: int,
        estimator: Covariance_Estimator,
    ) -> None:
        """Covariance matrix contains no NaN or infinite values."""
        rng = np.random.default_rng(seed=99)
        returns_array = rng.standard_normal((n_obs, n_assets)) * 0.01
        df_returns = _make_returns_df(returns_array, n_assets)
        cov_obj = Covariance_Matrix(data_returns=df_returns, estimator=estimator)
        assert np.all(np.isfinite(cov_obj.m_cov_matrix))

    @pytest.mark.unit()
    @given(
        n_assets=st.integers(min_value=2, max_value=6),
        n_obs=st.integers(min_value=30, max_value=60),
        estimator=st.sampled_from(_SIMPLE_ESTIMATORS),
    )
    @settings(max_examples=50, deadline=None)
    def Test_matrix_shape_matches_n_assets(
        self,
        n_assets: int,
        n_obs: int,
        estimator: Covariance_Estimator,
    ) -> None:
        """Matrix shape is (n_assets, n_assets) and component count is correct."""
        rng = np.random.default_rng(seed=13)
        returns_array = rng.standard_normal((n_obs, n_assets)) * 0.01
        df_returns = _make_returns_df(returns_array, n_assets)
        cov_obj = Covariance_Matrix(data_returns=df_returns, estimator=estimator)
        assert cov_obj.m_cov_matrix.shape == (n_assets, n_assets)
        assert cov_obj.m_num_components == n_assets
        assert len(cov_obj.m_component_names) == n_assets

    @pytest.mark.unit()
    @given(
        n_assets=st.integers(min_value=2, max_value=6),
        n_obs=st.integers(min_value=30, max_value=60),
        estimator=st.sampled_from(_SIMPLE_ESTIMATORS),
    )
    @settings(max_examples=50, deadline=None)
    def Test_num_observations_stored_correctly(
        self,
        n_assets: int,
        n_obs: int,
        estimator: Covariance_Estimator,
    ) -> None:
        """Stored observation count equals the number of rows in the input."""
        rng = np.random.default_rng(seed=21)
        returns_array = rng.standard_normal((n_obs, n_assets)) * 0.01
        df_returns = _make_returns_df(returns_array, n_assets)
        cov_obj = Covariance_Matrix(data_returns=df_returns, estimator=estimator)
        assert cov_obj.m_num_observations == n_obs
