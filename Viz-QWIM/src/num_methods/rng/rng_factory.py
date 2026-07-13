"""Validated NumPy generator helpers shared across QWIM numerical modules.

Notes
-----
These helpers centralize generator construction so simulation, scenario,
and dashboard modules do not duplicate BitGenerator selection logic.
"""

from __future__ import annotations

from collections.abc import Collection

import numpy as np

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


RNG_TYPE_BIT_GENERATOR_QWIM: dict[str, type[np.random.BitGenerator]] = {
    "pcg64": np.random.PCG64,
    "mt19937": np.random.MT19937,
    "philox": np.random.Philox,
    "sfc64": np.random.SFC64,
}


def _validate_seed_QWIM(*, seed: int) -> int:
    """Validate and return a non-negative integer seed."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise Exception_Validation_Input(
            "seed must be a non-negative integer",
            field_name="seed",
            expected_type=int,
            actual_value=seed,
        )
    return seed


def _normalize_rng_type_QWIM(
    *, rng_type: str, supported_rng_types: Collection[str] | None, fallback_rng_type: str | None) -> str:
    """Normalize an RNG type string and apply optional fallback behavior."""
    if isinstance(rng_type, bool) or not isinstance(rng_type, str):
        raise Exception_Validation_Input(
            "rng_type must be a supported string value",
            field_name="rng_type",
            expected_type=str,
            actual_value=rng_type,
        )

    value_rng_type = rng_type.strip().lower()
    allowed_rng_types = (
        set(RNG_TYPE_BIT_GENERATOR_QWIM)
        if supported_rng_types is None
        else {item_rng_type.strip().lower() for item_rng_type in supported_rng_types}
    )

    if value_rng_type in allowed_rng_types:
        return value_rng_type

    if fallback_rng_type is not None:
        value_fallback_rng_type = fallback_rng_type.strip().lower()
        if value_fallback_rng_type not in allowed_rng_types:
            raise Exception_Validation_Input(
                "fallback_rng_type must be one of the supported RNG types",
                field_name="fallback_rng_type",
                expected_type=str,
                actual_value=fallback_rng_type,
            )
        return value_fallback_rng_type

    raise Exception_Validation_Input(
        f"rng_type must be one of {sorted(allowed_rng_types)}",
        field_name="rng_type",
        expected_type=str,
        actual_value=rng_type,
    )


def create_rng_QWIM(
    *, rng_type: str, seed: int, supported_rng_types: Collection[str] | None = None, fallback_rng_type: str | None = None) -> np.random.Generator:
    """Create a NumPy Generator for a validated BitGenerator key."""
    value_seed = _validate_seed_QWIM(seed = seed)
    value_rng_type = _normalize_rng_type_QWIM(
        rng_type = rng_type,
        supported_rng_types=supported_rng_types,
        fallback_rng_type=fallback_rng_type,
    )
    bit_generator_class = RNG_TYPE_BIT_GENERATOR_QWIM[value_rng_type]
    return np.random.Generator(bit_generator_class(value_seed))


def spawn_rng_streams_QWIM(
    *, rng_parent: np.random.Generator, num_streams: int) -> list[np.random.Generator]:
    """Spawn independent child generators from a parent NumPy Generator."""
    if not isinstance(rng_parent, np.random.Generator):
        raise Exception_Validation_Input(
            "rng_parent must be a NumPy Generator",
            field_name="rng_parent",
            expected_type=np.random.Generator,
            actual_value=type(rng_parent).__name__,
        )

    if isinstance(num_streams, bool) or not isinstance(num_streams, int) or num_streams < 1:
        raise Exception_Validation_Input(
            "num_streams must be a positive integer",
            field_name="num_streams",
            expected_type=int,
            actual_value=num_streams,
        )

    bit_generator_parent = rng_parent.bit_generator
    if not hasattr(bit_generator_parent, "spawn"):
        raise Exception_Validation_Input(
            "rng_parent.bit_generator does not support spawned child streams",
            field_name="rng_parent",
            expected_type=np.random.Generator,
            actual_value=type(bit_generator_parent).__name__,
        )

    child_bit_generators = bit_generator_parent.spawn(num_streams)
    return [np.random.Generator(item_child) for item_child in child_bit_generators]