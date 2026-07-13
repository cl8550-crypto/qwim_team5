"""Hypothesis property-based tests for Nelson-Siegel yield-curve helpers.

Property tests focus on the pure module-level functions:

- ``_ns_loadings``:  L1 always 1.0; L2 in (0, 1] for tau > 0.
- ``_ns_yield``:     finite output for finite inputs; continuity at tau→0.
- ``_ns_forward``:   finite output for finite inputs; limit at tau=0.
- ``_design_matrix``:column-0 all-ones; shape (n, 3).

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.models.yield_curve.model_yield_curve_standard import (
    _design_matrix,
    _ns_forward,
    _ns_loadings,
    _ns_yield,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_strategy_tau_positive = st.floats(
    min_value=1e-6, max_value=100.0, allow_nan=False, allow_infinity=False
)

_strategy_lam_positive = st.floats(
    min_value=0.01, max_value=50.0, allow_nan=False, allow_infinity=False
)

_strategy_beta = st.floats(
    min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False
)


# ---------------------------------------------------------------------------
# _ns_loadings
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_NS_Loadings:
    """Property tests for :func:`_ns_loadings`."""

    @pytest.mark.unit()
    @given(
        tau_val=_strategy_tau_positive,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_l1_always_one(self, tau_val: float, lam_val: float) -> None:
        """First loading L1 is always exactly 1.0 (level factor)."""
        l1_val, _l2, _l3 = _ns_loadings(tau = tau_val, lam = lam_val)
        assert l1_val == 1.0

    @pytest.mark.unit()
    @given(
        tau_val=_strategy_tau_positive,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_l2_in_zero_one(self, tau_val: float, lam_val: float) -> None:
        """Second loading L2 lies in (0, 1] for all positive tau and lam."""
        _l1, l2_val, _l3 = _ns_loadings(tau = tau_val, lam = lam_val)
        assert l2_val > 0.0
        assert l2_val <= 1.0 + 1e-12

    @pytest.mark.unit()
    @given(
        tau_val=_strategy_tau_positive,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_all_loadings_finite(self, tau_val: float, lam_val: float) -> None:
        """All three loadings are finite floats."""
        l1_val, l2_val, l3_val = _ns_loadings(tau = tau_val, lam = lam_val)
        assert math.isfinite(l1_val)
        assert math.isfinite(l2_val)
        assert math.isfinite(l3_val)

    @pytest.mark.unit()
    @given(lam_val=_strategy_lam_positive)
    @settings(max_examples=200)
    def Test_l2_near_one_at_small_tau(self, lam_val: float) -> None:
        """L2 approaches 1.0 as tau → 0 (L'Hôpital limit)."""
        tau_tiny = 1e-12
        _l1, l2_val, _l3 = _ns_loadings(tau = tau_tiny, lam = lam_val)
        assert math.isclose(l2_val, 1.0, abs_tol=1e-6)


# ---------------------------------------------------------------------------
# _ns_yield
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_NS_Yield:
    """Property tests for :func:`_ns_yield`."""

    @pytest.mark.unit()
    @given(
        tau_val=_strategy_tau_positive,
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_output_is_finite(
        self,
        tau_val: float,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """Spot yield is always finite for finite inputs."""
        result = _ns_yield(tau = tau_val, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        assert math.isfinite(result)

    @pytest.mark.unit()
    @given(
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_yield_at_large_tau_approaches_beta0(
        self,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """As tau → ∞, L2 → 0 and L3 → 0, so y → beta0."""
        tau_large = 1e6
        result = _ns_yield(tau = tau_large, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        # Large-tau limit: exp(-tau/lam) → 0, so y → beta0; use generous tolerance
        # because at tau=1e6 the exponential is essentially machine-zero
        assert math.isclose(result, beta0_val, abs_tol=1e-3, rel_tol=1e-6)

    @pytest.mark.unit()
    @given(
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_yield_at_tiny_tau_approaches_beta0_plus_beta1(
        self,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """As tau → 0, y → beta0 + beta1 (L2 → 1, L3 → 0)."""
        tau_tiny = 1e-9
        result = _ns_yield(tau = tau_tiny, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        expected = beta0_val + beta1_val
        assert math.isclose(result, expected, abs_tol=1e-4)


# ---------------------------------------------------------------------------
# _ns_forward
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_NS_Forward:
    """Property tests for :func:`_ns_forward`."""

    @pytest.mark.unit()
    @given(
        tau_val=_strategy_tau_positive,
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_output_is_finite(
        self,
        tau_val: float,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """Instantaneous forward rate is always finite for finite inputs."""
        result = _ns_forward(tau = tau_val, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        assert math.isfinite(result)

    @pytest.mark.unit()
    @given(
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_forward_at_zero_equals_beta0_plus_beta1(
        self,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """f(tau=0) = beta0 + beta1 (exp(-0)=1, 0*exp(-0)=0)."""
        result = _ns_forward(tau = 0.0, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        expected = beta0_val + beta1_val
        assert math.isclose(result, expected, abs_tol=1e-12)

    @pytest.mark.unit()
    @given(
        beta0_val=_strategy_beta,
        beta1_val=_strategy_beta,
        beta2_val=_strategy_beta,
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_forward_at_large_tau_approaches_beta0(
        self,
        beta0_val: float,
        beta1_val: float,
        beta2_val: float,
        lam_val: float,
    ) -> None:
        """f(tau → ∞) → beta0 (exponential decay kills beta1 and beta2 terms)."""
        tau_large = 1e6
        result = _ns_forward(tau = tau_large, beta0 = beta0_val, beta1 = beta1_val, beta2 = beta2_val, lam = lam_val)
        assert math.isclose(result, beta0_val, abs_tol=1e-4)


# ---------------------------------------------------------------------------
# _design_matrix
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Design_Matrix:
    """Property tests for :func:`_design_matrix`."""

    @pytest.mark.unit()
    @given(
        taus=st.lists(
            _strategy_tau_positive,
            min_size=1,
            max_size=20,
        ),
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_shape_n_by_3(self, taus: list[float], lam_val: float) -> None:
        """Design matrix has shape (n, 3) where n == len(taus)."""
        arr = np.array(taus, dtype=np.float64)
        mat = _design_matrix(taus = arr, lam = lam_val)
        assert mat.shape == (len(taus), 3)

    @pytest.mark.unit()
    @given(
        taus=st.lists(
            _strategy_tau_positive,
            min_size=1,
            max_size=20,
        ),
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_first_column_all_ones(self, taus: list[float], lam_val: float) -> None:
        """First column of design matrix is all-ones (level loading)."""
        arr = np.array(taus, dtype=np.float64)
        mat = _design_matrix(taus = arr, lam = lam_val)
        assert np.all(mat[:, 0] == 1.0)

    @pytest.mark.unit()
    @given(
        taus=st.lists(
            _strategy_tau_positive,
            min_size=1,
            max_size=20,
        ),
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_all_entries_finite(self, taus: list[float], lam_val: float) -> None:
        """All entries in the design matrix are finite."""
        arr = np.array(taus, dtype=np.float64)
        mat = _design_matrix(taus = arr, lam = lam_val)
        assert np.all(np.isfinite(mat))

    @pytest.mark.unit()
    @given(
        taus=st.lists(
            _strategy_tau_positive,
            min_size=1,
            max_size=20,
        ),
        lam_val=_strategy_lam_positive,
    )
    @settings(max_examples=200)
    def Test_second_column_in_zero_one(
        self, taus: list[float], lam_val: float
    ) -> None:
        """Second column (slope loading L2) lies in (0, 1] for all positive tau."""
        arr = np.array(taus, dtype=np.float64)
        mat = _design_matrix(taus = arr, lam = lam_val)
        col2 = mat[:, 1]
        assert np.all(col2 > 0.0)
        assert np.all(col2 <= 1.0 + 1e-12)
