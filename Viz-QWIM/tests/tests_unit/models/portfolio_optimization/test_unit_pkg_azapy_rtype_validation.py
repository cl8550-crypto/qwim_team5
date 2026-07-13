from __future__ import annotations

from collections.abc import Callable
from typing import Any

import polars as pl
import pytest

from src.models.portfolio_optimization.pkg_azapy import (
    calc_azapy_cvar,
    calc_azapy_evar,
    calc_azapy_kelly,
    calc_azapy_mad,
    calc_azapy_mean_variance,
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


Calc_Function_Azapy = Callable[..., Any]


@pytest.fixture()
def returns_data_sample() -> pl.DataFrame:
    """Return a minimal Polars returns frame for azapy validation tests.

    Returns
    -------
    pl.DataFrame
        Small deterministic returns dataset with a ``Date`` column and
        three numeric asset columns.
    """
    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "AAPL": [0.01, -0.005, 0.02],
            "MSFT": [0.015, 0.01, -0.01],
            "GOOG": [0.005, 0.02, 0.015],
        }
    )


@pytest.mark.unit()
class Class_Test_Pkg_Azapy_Rtype_Validation:
    """Focused validation tests for azapy ``rtype`` boundaries."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("calc_function", "function_kwargs"),
        [
            pytest.param(calc_azapy_mean_variance, {}, id="mean_variance"),
            pytest.param(calc_azapy_cvar, {}, id="cvar"),
            pytest.param(calc_azapy_mad, {}, id="mad"),
            pytest.param(calc_azapy_kelly, {}, id="kelly"),
            pytest.param(calc_azapy_evar, {}, id="evar"),
        ],
    )
    @pytest.mark.parametrize(
        "invalid_rtype",
        [
            pytest.param("INVALID", id="invalid_string"),
            pytest.param(["INVALID"], id="invalid_list"),
        ],
    )
    def Test_Public_Functions_Invalid_Rtype_Raises(
        self,
        returns_data_sample: pl.DataFrame,
        calc_function: Calc_Function_Azapy,
        function_kwargs: dict[str, Any],
        invalid_rtype: object,
    ) -> None:
        """Public azapy functions should normalize invalid rtype failures."""

        with pytest.raises(Exception_Validation_Input, match="rtype"):
            calc_function(
                returns_data=returns_data_sample,
                rtype=invalid_rtype,
                **function_kwargs,
            )