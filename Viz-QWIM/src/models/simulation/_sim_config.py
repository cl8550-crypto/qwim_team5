"""Simulation configuration model and public constants.

Extracted from ``simulation_dispatch`` to keep each file under 1000 LOC.
All public names are re-exported via ``simulation_dispatch``.
"""

from __future__ import annotations

import datetime as dt
import numpy as np

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from src.num_methods.scenarios.scenarios_distrib import Distribution_Type
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Ordered tuple of all supported computation-type labels (matches Setup UI).
COMPUTATION_TYPES_SIMULATION: tuple[str, ...] = (
    "standard",
    "asyncio",
    "asyncio + anyio",
    "trio",
    "trio + anyio",
    "joblib",
)

#: Ordered tuple of computation types used by the Compute-and-Compare
#: feature.  ``"joblib"`` is excluded because its thread-based parallelism
#: can saturate the OS scheduler at high scenario counts on Windows.
COMPUTATION_TYPES_SIMULATION_COMPARE: tuple[str, ...] = (
    "standard",
    "asyncio",
    "asyncio + anyio",
    "trio",
    "trio + anyio",
)

#: Numeric metrics included in the compare-summary table.
#: "Elapsed time (s)" is intentionally excluded — it is always rendered
#: as a dedicated single-value row (no Δ abs / Δ rel sub-rows).
DEFAULT_COMPARE_METRICS: list[str] = [
    "Mean",
    "Median",
    "Std",
    "P5",
    "P95",
    "Prob(Loss)",
    "Min",
    "Max",
    "P25",
    "P75",
]

SUPPORTED_RNG_TYPES_SIMULATION: tuple[str, ...] = (
    "pcg64",
    "mt19937",
    "philox",
    "sfc64",
)


# ---------------------------------------------------------------------------
# Pydantic config model
# ---------------------------------------------------------------------------


class Simulation_Run_Config(BaseModel):  # noqa: N801
    """Typed container for Monte Carlo simulation parameters.

    All fields consumed by :func:`dispatch_simulation_run` and
    :func:`compute_compare_results` are grouped here to keep call-sites
    clean and to enable Pydantic v2 validation.

    Attributes
    ----------
    names_components : list[str]
        Ticker symbols of portfolio components.
    weights : np.ndarray
        Static portfolio weights of shape ``(K,)`` summing to 1.
    distribution_type : Distribution_Type
        Return-distribution family.
    mean_returns : np.ndarray
        Daily mean returns per component, shape ``(K,)``.
    covariance_matrix : np.ndarray
        ``(K, K)`` covariance matrix.
    initial_value : float
        Starting portfolio value.
    num_scenarios : int
        Number of Monte Carlo paths.
    num_days : int
        Simulation horizon in trading days.
    start_date : dt.date
        First date of the simulation.
    random_seed : int
        Master RNG seed; guarantees bit-identical results across backends.
    degrees_of_freedom : float
        DoF for Student-*t* (ignored for Normal / Lognormal).
    rng_type : str
        BitGenerator type: ``"pcg64"``, ``"mt19937"``, ``"philox"``,
        or ``"sfc64"``.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    names_components: list[str]
    weights: np.ndarray
    distribution_type: Distribution_Type
    mean_returns: np.ndarray
    covariance_matrix: np.ndarray
    initial_value: float = 100.0
    num_scenarios: int = 1_000
    num_days: int = 252
    start_date: dt.date = Field(
        default_factory=lambda: dt.datetime.now(tz=dt.UTC).date(),
    )
    random_seed: int = 42
    degrees_of_freedom: float = 5.0
    rng_type: str = "pcg64"

    @field_validator(
        "initial_value",
        "num_scenarios",
        "num_days",
        "random_seed",
        "degrees_of_freedom",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric_inputs(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> object:
        """Reject boolean values before Pydantic coerces them to numeric types."""
        if isinstance(value, bool):
            raise ValueError(f"{info.field_name} must not be a boolean value")
        return value

    @field_validator("initial_value")
    @classmethod
    def _validate_initial_value(cls, value: float) -> float:
        """Require a positive finite starting value."""
        if not np.isfinite(value) or value <= 0:
            raise ValueError("initial_value must be a positive finite number (> 0)")
        return value

    @field_validator("num_scenarios", "num_days")
    @classmethod
    def _validate_positive_int_fields(
        cls,
        value: int,
        info: ValidationInfo,
    ) -> int:
        """Require positive integer sizing parameters."""
        if value < 1:
            raise ValueError(f"{info.field_name} must be a positive integer (> 0)")
        return value

    @field_validator("random_seed")
    @classmethod
    def _validate_random_seed(cls, value: int) -> int:
        """Require a non-negative integer RNG seed."""
        if value < 0:
            raise ValueError("random_seed must be a non-negative integer")
        return value

    @field_validator("degrees_of_freedom")
    @classmethod
    def _validate_degrees_of_freedom(cls, value: float) -> float:
        """Require a finite degrees-of-freedom value."""
        if not np.isfinite(value):
            raise ValueError("degrees_of_freedom must be a finite real number")
        return value

    @field_validator("rng_type", mode="before")
    @classmethod
    def _validate_rng_type(cls, value: object) -> str:
        """Require a supported BitGenerator label."""
        if isinstance(value, bool) or not isinstance(value, str):
            raise ValueError("rng_type must be a supported string value")

        value_rng_type = value.strip().lower()
        if value_rng_type not in SUPPORTED_RNG_TYPES_SIMULATION:
            raise ValueError(
                f"rng_type must be one of {SUPPORTED_RNG_TYPES_SIMULATION}",
            )
        return value_rng_type

    @model_validator(mode="after")
    def _validate_student_t_degrees_of_freedom(self) -> "Simulation_Run_Config":
        """Require Student-t degrees_of_freedom to match the tensor generator contract."""
        if (
            self.distribution_type == Distribution_Type.STUDENT_T
            and self.degrees_of_freedom <= 2.0
        ):
            raise ValueError(
                "degrees_of_freedom must be > 2 for Student-t simulations",
            )
        return self
