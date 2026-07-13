"""Unit tests for shared RNG factory helpers.

Mirrors source: ``src/num_methods/rng/rng_factory.py``.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.num_methods.rng import create_rng_QWIM, spawn_rng_streams_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)


class Class_Test_Create_Rng_QWIM:
    """Unit tests for ``create_rng_QWIM``."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        ("rng_type", "seed"),
        [
            ("pcg64", 42),
            ("mt19937", 7),
            ("philox", 101),
            ("sfc64", 5),
        ],
    )
    def Test_Known_Rng_Types_Return_Generator(
        self,
        rng_type: str,
        seed: int,
    ) -> None:
        """Known RNG types build NumPy generators."""
        rng = create_rng_QWIM(rng_type = rng_type, seed = seed)

        assert isinstance(rng, np.random.Generator)

    @pytest.mark.unit()
    def Test_Same_Seed_Same_Output(
        self,
    ) -> None:
        """Same RNG type and seed produce identical samples."""
        rng_left = create_rng_QWIM(rng_type = "pcg64", seed = 42)
        rng_right = create_rng_QWIM(rng_type = "pcg64", seed = 42)

        assert np.array_equal(
            rng_left.standard_normal(8),
            rng_right.standard_normal(8),
        )

    @pytest.mark.unit()
    def Test_Unknown_Type_Raises_When_No_Fallback(
        self,
    ) -> None:
        """Unknown types raise validation errors when fallback is disabled."""
        with pytest.raises(Exception_Validation_Input, match="rng_type"):
            create_rng_QWIM(rng_type = "unknown", seed = 0)

    @pytest.mark.unit()
    def Test_Unknown_Type_Uses_Fallback_When_Configured(
        self,
    ) -> None:
        """Unknown types resolve to the configured fallback type."""
        rng_default = create_rng_QWIM(
            rng_type = "unknown",
            seed = 42,
            fallback_rng_type="pcg64",
        )
        rng_expected = create_rng_QWIM(rng_type = "pcg64", seed = 42)

        assert np.array_equal(
            rng_default.standard_normal(10),
            rng_expected.standard_normal(10),
        )

    @pytest.mark.unit()
    def Test_Boolean_Seed_Raises(
        self,
    ) -> None:
        """Boolean seeds are rejected before integer coercion."""
        with pytest.raises(Exception_Validation_Input, match="seed"):
            create_rng_QWIM(rng_type = "pcg64", seed = True)


class Class_Test_Spawn_Rng_Streams_QWIM:
    """Unit tests for ``spawn_rng_streams_QWIM``."""

    @pytest.mark.unit()
    def Test_Spawned_Streams_Are_Reproducible_For_Same_Parent(
        self,
    ) -> None:
        """Spawning from the same parent seed yields reproducible child streams."""
        parent_left = create_rng_QWIM(rng_type = "pcg64", seed = 17)
        parent_right = create_rng_QWIM(rng_type = "pcg64", seed = 17)

        streams_left = spawn_rng_streams_QWIM(rng_parent = parent_left, num_streams = 3)
        streams_right = spawn_rng_streams_QWIM(rng_parent = parent_right, num_streams = 3)

        for item_left, item_right in zip(streams_left, streams_right, strict=True):
            assert np.array_equal(
                item_left.standard_normal(6),
                item_right.standard_normal(6),
            )

    @pytest.mark.unit()
    def Test_Spawned_Streams_Differ_Across_Children(
        self,
    ) -> None:
        """Different child streams should not reuse the same sample path."""
        parent_rng = create_rng_QWIM(rng_type = "pcg64", seed = 23)

        stream_first, stream_second = spawn_rng_streams_QWIM(rng_parent = parent_rng, num_streams = 2)

        assert not np.array_equal(
            stream_first.standard_normal(8),
            stream_second.standard_normal(8),
        )

    @pytest.mark.unit()
    def Test_Invalid_Stream_Count_Raises(
        self,
    ) -> None:
        """Child stream count must be a positive integer."""
        with pytest.raises(Exception_Validation_Input, match="num_streams"):
            spawn_rng_streams_QWIM(rng_parent = create_rng_QWIM(rng_type = "pcg64", seed = 1), num_streams = 0)