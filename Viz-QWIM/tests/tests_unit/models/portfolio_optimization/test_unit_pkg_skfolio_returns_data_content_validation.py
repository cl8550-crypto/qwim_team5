from __future__ import annotations

import polars as pl
import pytest

from src.models.portfolio_optimization.pkg_skfolio import (
    _validate_returns_data,
)


@pytest.mark.unit()
class Class_Test_Pkg_Skfolio_Returns_Data_Content_Validation:
    """Focused tests for skfolio returns-data content validation boundaries."""

    @pytest.mark.unit()
    def Test_Null_Date_Value_Is_Rejected(self) -> None:
        """A null Date value should fail shared skfolio returns-data validation."""

        returns_data = pl.DataFrame(
            {
                "Date": ["2024-01-01", None],
                "AAPL": [0.01, 0.02],
            }
        )

        is_valid, error_message = _validate_returns_data(returns_data = returns_data)

        assert is_valid is False
        assert "Date" in error_message
        assert "null" in error_message

    @pytest.mark.unit()
    def Test_Null_Asset_Value_Is_Rejected(self) -> None:
        """A null asset-return value should fail shared skfolio returns-data validation."""

        returns_data = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "AAPL": [0.01, None],
            }
        )

        is_valid, error_message = _validate_returns_data(returns_data = returns_data)

        assert is_valid is False
        assert "AAPL" in error_message
        assert "null" in error_message

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("invalid_value", "case_id"),
        [
            pytest.param(float("nan"), "nan", id="nan"),
            pytest.param(float("inf"), "inf", id="inf"),
        ],
    )
    def Test_Non_Finite_Asset_Value_Is_Rejected(
        self,
        invalid_value: float,
        case_id: str,
    ) -> None:
        """A non-finite asset-return value should fail skfolio returns-data validation."""

        returns_data = pl.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "AAPL": [0.01, invalid_value],
            }
        )

        is_valid, error_message = _validate_returns_data(returns_data = returns_data)

        assert case_id in {"nan", "inf"}
        assert is_valid is False
        assert "AAPL" in error_message
        assert "finite" in error_message