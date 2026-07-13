"""Root conftest for ``tests/tests_hypothesis``.

Registers the ``tests/tests_hypothesis/_strategies`` module so that all
hypothesis test sub-packages can request shared Polars strategies by fixture
name rather than importing directly.

All fixture names are identical to those defined in
``tests/tests_hypothesis/_strategies/conftest.py`` — pytest discovers the
``_strategies`` conftest automatically via normal conftest resolution, so
this file only provides the top-level registration hook and shared settings.

Version: 1.0.0
"""

from __future__ import annotations

from hypothesis import settings, HealthCheck

# ---------------------------------------------------------------------------
# Project-wide hypothesis settings profile
# ---------------------------------------------------------------------------

settings.register_profile(
    "qwim_ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)

settings.register_profile(
    "qwim_dev",
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)

# Default to qwim_dev; CI pipelines should set HYPOTHESIS_PROFILE=qwim_ci.
settings.load_profile("qwim_dev")
