"""Hypothesis property-based tests for Inflation_Model_Constant.

Property tests verify:

- Constructor accepts any rate in [-0.5, 1.0] and stores it correctly.
- Constructor rejects rates outside that range.
- fit(empty) preserves the constructor rate.
- fit(data) sets m_annual_rate to arithmetic mean of inflation_rate column.
- predict() returns exactly n_periods rows with constant inflation_rate.
- get_annual_rate() returns the fitted rate.

Author: QWIM Team
Version: 1.0.0
"""

from __future__ import annotations

import math

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.inflation.model_inflation_constant import Inflation_Model_Constant
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid annual rate range: [-0.5, 1.0]
_strategy_rate_valid = st.floats(
    min_value=-0.5, max_value=1.0, allow_nan=False, allow_infinity=False
)

_strategy_n_periods = st.integers(min_value=1, max_value=120)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Constant_Construction:
    """Property tests for ``Inflation_Model_Constant.__init__``."""

    @pytest.mark.unit()
    def Test_Bool_Rate_Raises(self) -> None:
        """Boolean annual rates are rejected as invalid numeric inputs."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=True)  # type: ignore[arg-type]

    @pytest.mark.unit()
    @given(rate_val=_strategy_rate_valid)
    @settings(max_examples=200)
    def Test_valid_rate_stored_correctly(self, rate_val: float) -> None:
        """Constructor stores any valid rate without error."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        assert math.isclose(model.m_annual_rate, rate_val, rel_tol=1e-12, abs_tol=1e-15)

    @pytest.mark.unit()
    @given(
        rate_val=st.floats(
            min_value=1.0 + 1e-9,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_rate_above_max_raises(self, rate_val: float) -> None:
        """annual_rate > 1.0 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=rate_val)

    @pytest.mark.unit()
    @given(
        rate_val=st.floats(
            max_value=-0.5 - 1e-9,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def Test_rate_below_min_raises(self, rate_val: float) -> None:
        """annual_rate < -0.5 raises Exception_Validation_Input."""
        with pytest.raises(Exception_Validation_Input):
            Inflation_Model_Constant(annual_rate=rate_val)


# ---------------------------------------------------------------------------
# fit
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Constant_Fit:
    """Property tests for ``Inflation_Model_Constant.fit``."""

    @pytest.mark.unit()
    @given(rate_val=_strategy_rate_valid)
    @settings(max_examples=200, deadline=None)
    def Test_fit_empty_preserves_rate(self, rate_val: float) -> None:
        """fit(empty DataFrame) leaves m_annual_rate unchanged."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        model.fit(data = pl.DataFrame())
        assert math.isclose(model.m_annual_rate, rate_val, rel_tol=1e-12)

    @pytest.mark.unit()
    @given(
        rates_val=st.lists(
            st.floats(
                min_value=-0.5,
                max_value=1.0,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=200, deadline=None)
    def Test_fit_data_sets_mean_rate(self, rates_val: list[float]) -> None:
        """fit() with data sets m_annual_rate to the arithmetic mean."""
        dates_str = [f"202{(idx % 10):01d}-01-01" for idx in range(len(rates_val))]
        hist = pl.DataFrame({"Date": dates_str, "inflation_rate": rates_val})
        model = Inflation_Model_Constant()
        model.fit(data = hist)
        expected_mean = sum(rates_val) / len(rates_val)
        assert math.isclose(model.m_annual_rate, expected_mean, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# predict
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Constant_Predict:
    """Property tests for ``Inflation_Model_Constant.predict``."""

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_valid,
        n_periods_val=_strategy_n_periods,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_row_count(self, rate_val: float, n_periods_val: int) -> None:
        """predict() returns exactly n_periods rows."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_periods=n_periods_val)
        assert len(df) == n_periods_val

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_valid,
        n_periods_val=_strategy_n_periods,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_inflation_rate_column_constant(
        self, rate_val: float, n_periods_val: int
    ) -> None:
        """All inflation_rate values in predict() equal m_annual_rate."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_periods=n_periods_val)
        for row_rate in df["inflation_rate"].to_list():
            assert math.isclose(row_rate, rate_val, rel_tol=1e-9)

    @pytest.mark.unit()
    @given(
        rate_val=_strategy_rate_valid,
        n_periods_val=_strategy_n_periods,
    )
    @settings(max_examples=200, deadline=None)
    def Test_predict_has_date_and_rate_columns(
        self, rate_val: float, n_periods_val: int
    ) -> None:
        """predict() output has 'Date' and 'inflation_rate' columns."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        model.fit(data = pl.DataFrame())
        df = model.predict(n_periods=n_periods_val)
        assert "Date" in df.columns
        assert "inflation_rate" in df.columns


# ---------------------------------------------------------------------------
# get_annual_rate
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Inflation_Constant_Get_Rate:
    """Property tests for ``Inflation_Model_Constant.get_annual_rate``."""

    @pytest.mark.unit()
    @given(rate_val=_strategy_rate_valid)
    @settings(max_examples=200, deadline=None)
    def Test_get_annual_rate_returns_fitted_rate(self, rate_val: float) -> None:
        """get_annual_rate() returns the rate set by constructor after fit."""
        model = Inflation_Model_Constant(annual_rate=rate_val)
        model.fit(data = pl.DataFrame())
        assert math.isclose(model.get_annual_rate(), rate_val, rel_tol=1e-12)
