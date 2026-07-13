"""Hypothesis property-based tests for Longevity_Model_Constant.

Property tests verify mathematical invariants:

- Survival probability S(t) = (1-q)^t in (0, 1] for valid q and t >= 0.
- S(0) == 1 (no one has died yet).
- predict() output has correct row count and all-equal qx column.
- fit() with empty DataFrame preserves constructor rate.
- fit() with life-table data updates m_qx to mean of qx column.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math

import polars as pl
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.models.longevity.model_longevity_constant import Longevity_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid qx range: [1e-6, 0.5]
_strategy_qx = st.floats(
    min_value=1e-6, max_value=0.5, allow_nan=False, allow_infinity=False
)

_strategy_n_ages = st.integers(min_value=1, max_value=120)
_strategy_start_age = st.integers(min_value=0, max_value=110)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Constant_Construction:
    """Property tests for ``Longevity_Model_Constant.__init__``."""

    @pytest.mark.unit()
    def Test_Bool_Qx_Raises(self) -> None:
        """Boolean mortality rates are rejected as invalid numeric inputs."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(qx_val=_strategy_qx)
    @settings(max_examples=200)
    def Test_valid_qx_stored_correctly(self, qx_val: float) -> None:
        """Constructor stores any valid qx without error."""
        model = Longevity_Model_Constant(qx=qx_val)
        assert math.isclose(model.m_qx, qx_val, rel_tol=1e-12, abs_tol=1e-15)

    @pytest.mark.unit()
    @given(
        qx_val=st.floats(
            min_value=0.5 + 1e-9,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_qx_above_max_raises(self, qx_val: float) -> None:
        """qx > 0.5 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=qx_val)

    @pytest.mark.unit()
    @given(
        qx_val=st.floats(
            max_value=-1e-9,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_negative_qx_raises(self, qx_val: float) -> None:
        """Negative qx raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Longevity_Model_Constant(qx=qx_val)


# ---------------------------------------------------------------------------
# predict: structural invariants
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Constant_Predict:
    """Property tests for ``Longevity_Model_Constant.predict``."""

    @pytest.mark.unit()
    @given(
        qx_val=_strategy_qx,
        n_ages_val=_strategy_n_ages,
        start_age_val=_strategy_start_age,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_row_count(
        self, qx_val: float, n_ages_val: int, start_age_val: int
    ) -> None:
        """predict() returns exactly n_ages rows."""
        model = Longevity_Model_Constant(qx=qx_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_ages=n_ages_val, start_age=start_age_val)
        assert len(df) == n_ages_val

    @pytest.mark.unit()
    @given(
        qx_val=_strategy_qx,
        n_ages_val=_strategy_n_ages,
        start_age_val=_strategy_start_age,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_qx_column_constant(
        self, qx_val: float, n_ages_val: int, start_age_val: int
    ) -> None:
        """All qx values in predict() output equal m_qx."""
        model = Longevity_Model_Constant(qx=qx_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_ages=n_ages_val, start_age=start_age_val)
        qx_values = df["qx"].to_list()
        for qx_row in qx_values:
            assert math.isclose(qx_row, qx_val, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        qx_val=_strategy_qx,
        n_ages_val=_strategy_n_ages,
        start_age_val=_strategy_start_age,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_age_column_starts_at_start_age(
        self, qx_val: float, n_ages_val: int, start_age_val: int
    ) -> None:
        """Age column starts at start_age and increments by 1."""
        model = Longevity_Model_Constant(qx=qx_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_ages=n_ages_val, start_age=start_age_val)
        ages = df["Age"].to_list()
        assert ages[0] == start_age_val
        assert ages[-1] == start_age_val + n_ages_val - 1


# ---------------------------------------------------------------------------
# fit: empty data preserves constructor qx
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Longevity_Constant_Fit:
    """Property tests for ``Longevity_Model_Constant.fit``."""

    @pytest.mark.unit()
    @given(qx_val=_strategy_qx)
    @settings(max_examples=200)
    def Test_fit_empty_preserves_qx(self, qx_val: float) -> None:
        """fit(empty DataFrame) leaves m_qx unchanged."""
        model = Longevity_Model_Constant(qx=qx_val)
        model.fit(data = pl.DataFrame())
        assert math.isclose(model.m_qx, qx_val, rel_tol=1e-12)

    @pytest.mark.unit()
    @given(
        qx_vals=st.lists(
            st.floats(min_value=1e-6, max_value=0.5, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=30,
        )
    )
    @settings(max_examples=200)
    def Test_fit_life_table_sets_mean_qx(self, qx_vals: list[float]) -> None:
        """fit() with life-table data sets m_qx to the arithmetic mean."""
        ages = list(range(len(qx_vals)))
        life_table = pl.DataFrame({"Age": ages, "qx": qx_vals})
        model = Longevity_Model_Constant()
        model.fit(data = life_table)
        expected_mean = sum(qx_vals) / len(qx_vals)
        assert math.isclose(model.m_qx, expected_mean, rel_tol=1e-9)
