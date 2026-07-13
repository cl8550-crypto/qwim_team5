"""Hypothesis tests for shared RNG factory helpers.

Mirrors source: ``src/num_methods/rng/rng_factory.py``.
"""

from __future__ import annotations

import numpy as np
import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from src.num_methods.rng import create_rng_QWIM, spawn_rng_streams_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


@pytest.mark.unit()
@given(
    rng_type=st.sampled_from(["pcg64", "mt19937", "philox", "sfc64"]),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=100, deadline=None)
def Test_Create_Rng_QWIM_Is_Reproducible(
    rng_type: str,
    seed: int,
) -> None:
    """Same RNG type and seed always reproduce the same draws."""
    rng_left = create_rng_QWIM(rng_type = rng_type, seed = seed)
    rng_right = create_rng_QWIM(rng_type = rng_type, seed = seed)

    assert np.array_equal(
        rng_left.standard_normal(12),
        rng_right.standard_normal(12),
    )


@pytest.mark.unit()
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=80, deadline=None)
def Test_Spawn_Rng_Streams_QWIM_Preserves_Child_Count(
    seed: int,
) -> None:
    """Spawning returns the requested number of child generators."""
    streams = spawn_rng_streams_QWIM(rng_parent = create_rng_QWIM(rng_type = "pcg64", seed = seed), num_streams = 4)

    assert len(streams) == 4
    assert all(isinstance(item_stream, np.random.Generator) for item_stream in streams)


@pytest.mark.unit()
def Test_Create_Rng_QWIM_Rejects_Boolean_Rng_Type() -> None:
    """Boolean RNG types are rejected before string coercion."""
    with pytest.raises(Exception_Validation_Input, match="rng_type"):
        create_rng_QWIM(rng_type = True, seed = 42)