"""Shared random-number-generator utilities for numerical methods.

This package centralizes generator creation and substream management so the
simulation and scenario modules use one validated implementation.
"""

from __future__ import annotations

from src.num_methods.rng.rng_factory import (
    RNG_TYPE_BIT_GENERATOR_QWIM,
    create_rng_QWIM,
    spawn_rng_streams_QWIM,
)


__all__ = [
    "RNG_TYPE_BIT_GENERATOR_QWIM",
    "create_rng_QWIM",
    "spawn_rng_streams_QWIM",
]