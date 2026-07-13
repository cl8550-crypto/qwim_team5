"""Shared RNG helpers for scenario generation."""

from __future__ import annotations

import numpy as np

from src.num_methods.rng import create_rng_QWIM, spawn_rng_streams_QWIM


def create_scenario_rng_QWIM(*, seed: int | None) -> np.random.Generator:
    """Create a scenario generator, preserving ``None`` as non-deterministic."""
    if seed is None:
        return np.random.default_rng()
    return create_rng_QWIM(rng_type = "pcg64", seed = seed)


def spawn_scenario_rng_streams_QWIM(
    *, seed: int | None, num_streams: int) -> list[np.random.Generator]:
    """Spawn child generators for independent scenario random streams."""
    return spawn_rng_streams_QWIM(rng_parent = create_scenario_rng_QWIM(seed = seed), num_streams = num_streams)