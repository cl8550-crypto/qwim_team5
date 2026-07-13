"""Unit tests for simulation_dispatch module.

Tests cover:
- compute_chunk_indices: edge cases, perfect divisibility, remainder distribution.
- generate_random_returns_tensor: shape, dtype, determinism, all three distributions.
- compute_portfolio_paths_from_returns_tensor: shape, initial value, compounding.
- dispatch_simulation_run: all 6 backends produce bit-identical results; invalid backend.
- compute_simulation_stats: column set.
- build_compare_summary_table: shape, columns, 3-row-per-metric layout, Δ-rel small-denominator rule.
- compute_compare_results: all 6 backends succeed; progress callback invoked with monotone current_index.
- _resolve_num_chunks: standard returns 1; non-standard bounded by num_scenarios.
- _compute_delta_pair: N/A guards, small-denominator rule, normal ratio rule.
"""
# ruff: noqa: PLC0415, N803

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture()
def dist_normal():
    """Dist normal."""
    from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

    return Distribution_Type.NORMAL


@pytest.fixture()
def dist_lognormal():
    """Dist lognormal."""
    from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

    return Distribution_Type.LOGNORMAL


@pytest.fixture()
def dist_student_t():
    """Dist student t."""
    from src.num_methods.scenarios.scenarios_distrib import Distribution_Type

    return Distribution_Type.STUDENT_T


@pytest.fixture()
def base_config(dist_normal):
    """Minimal Simulation_Run_Config for fast tests."""
    from src.models.simulation.simulation_dispatch import Simulation_Run_Config

    return Simulation_Run_Config(
        names_components=["A", "B"],
        weights=np.array([0.5, 0.5]),
        distribution_type=dist_normal,
        mean_returns=np.array([0.0003, 0.0002]),
        covariance_matrix=np.array([[0.0004, 0.0001], [0.0001, 0.0003]]),
        initial_value=100.0,
        num_scenarios=200,
        num_days=10,
        start_date=dt.date(2026, 1, 2),
        random_seed=42,
        degrees_of_freedom=5.0,
        rng_type="pcg64",
    )


# ======================================================================
# compute_chunk_indices
# ======================================================================


class Test_Compute_Chunk_Indices:
    """Edge cases and correctness for compute_chunk_indices."""

    @pytest.mark.unit()
    def test_single_chunk(self):
        """Test that single chunk."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        result = compute_chunk_indices(num_scenarios = 10, num_chunks = 1)
        assert result == [(0, 10)]

    @pytest.mark.unit()
    def test_equal_chunks(self):
        """Test that equal chunks."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        result = compute_chunk_indices(num_scenarios = 12, num_chunks = 3)
        assert result == [(0, 4), (4, 8), (8, 12)]

    @pytest.mark.unit()
    def test_remainder_distributed(self):
        """Remainder scenarios go to the first chunks."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        result = compute_chunk_indices(num_scenarios = 10, num_chunks = 3)
        # 10 = 3+3+4 → [(0,4),(4,7),(7,10)] with remainder=1 going first
        sizes = [e - s for s, e in result]
        assert sum(sizes) == 10
        assert len(result) == 3
        # First chunk(s) should be larger than last
        assert sizes[0] >= sizes[-1]

    @pytest.mark.unit()
    def test_non_overlapping_full_coverage(self):
        """All indices cover [0, N) without gaps or overlaps."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        N = 17
        K = 5
        chunks = compute_chunk_indices(num_scenarios = N, num_chunks = K)
        all_indices = []
        for s, e in chunks:
            all_indices.extend(range(s, e))
        assert sorted(all_indices) == list(range(N))

    @pytest.mark.unit()
    def test_num_chunks_exceeds_scenarios(self):
        """num_chunks > num_scenarios → clamped to num_scenarios chunks of 1."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        result = compute_chunk_indices(num_scenarios = 3, num_chunks = 10)
        assert len(result) == 3
        assert all(e - s == 1 for s, e in result)

    @pytest.mark.unit()
    def test_single_scenario_single_chunk(self):
        """Test that single scenario single chunk."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        result = compute_chunk_indices(num_scenarios = 1, num_chunks = 1)
        assert result == [(0, 1)]

    @pytest.mark.unit()
    def test_invalid_num_chunks_raises(self):
        """Test that invalid num chunks raises."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            compute_chunk_indices(num_scenarios = 10, num_chunks = 0)

    @pytest.mark.unit()
    def test_invalid_num_scenarios_raises(self):
        """Zero or boolean num_scenarios should raise before chunk math."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_num_scenarios in (0, True):
            with pytest.raises(Exception_Validation_Input, match="num_scenarios"):
                compute_chunk_indices(num_scenarios = item_num_scenarios, num_chunks = 1)

    @pytest.mark.unit()
    def test_ordering_monotone(self):
        """Chunks are sorted in ascending order."""
        from src.models.simulation.simulation_dispatch import compute_chunk_indices

        chunks = compute_chunk_indices(num_scenarios = 20, num_chunks = 4)
        for (s1, e1), (s2, _) in zip(chunks, chunks[1:]):
            assert e1 == s2  # contiguous


# ======================================================================
# generate_random_returns_tensor
# ======================================================================


class Test_Generate_Random_Returns_Tensor:
    """Shape, dtype, determinism and distribution paths."""

    @pytest.mark.unit()
    def test_shape_normal(self, dist_normal):
        """Test that shape normal."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )

        rng = _make_rng(rng_type = "pcg64", seed = 42)
        T, N, K = 5, 10, 2
        tensor = generate_random_returns_tensor(
            num_days = T, num_scenarios = N, num_components = K, distribution_type = dist_normal,
            mean_returns = np.array([0.001, 0.002]),
            cov_matrix = np.eye(2) * 0.0004,
            dof = 5.0,
            rng = rng,
        )
        assert tensor.shape == (T, N, K)
        assert tensor.dtype == np.float64

    @pytest.mark.unit()
    def test_shape_lognormal(self, dist_lognormal):
        """Test that shape lognormal."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )

        rng = _make_rng(rng_type = "pcg64", seed = 0)
        T, N, K = 5, 8, 2
        # lognormal needs positive means
        tensor = generate_random_returns_tensor(
            num_days = T, num_scenarios = N, num_components = K, distribution_type = dist_lognormal,
            mean_returns = np.array([1.001, 1.002]),
            cov_matrix = np.eye(2) * 0.0004,
            dof = 5.0,
            rng = rng,
        )
        assert tensor.shape == (T, N, K)

    @pytest.mark.unit()
    def test_shape_student_t(self, dist_student_t):
        """Test that shape student t."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )

        rng = _make_rng(rng_type = "pcg64", seed = 7)
        T, N, K = 5, 8, 2
        tensor = generate_random_returns_tensor(
            num_days = T, num_scenarios = N, num_components = K, distribution_type = dist_student_t,
            mean_returns = np.array([0.001, 0.002]),
            cov_matrix = np.eye(2) * 0.0004,
            dof = 5.0,
            rng = rng,
        )
        assert tensor.shape == (T, N, K)

    @pytest.mark.unit()
    def test_deterministic_with_seed(self, dist_normal):
        """Test that deterministic with seed."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )

        kwargs = dict(
            num_days=5, num_scenarios=10, num_components=2,
            distribution_type=dist_normal,
            mean_returns=np.array([0.001, 0.002]),
            cov_matrix=np.eye(2) * 0.0004,
            dof=5.0,
        )
        t1 = generate_random_returns_tensor(**kwargs, rng=_make_rng(rng_type = "pcg64", seed = 99))
        t2 = generate_random_returns_tensor(**kwargs, rng=_make_rng(rng_type = "pcg64", seed = 99))
        np.testing.assert_array_equal(t1, t2)

    @pytest.mark.unit()
    def test_invalid_distribution_raises(self):
        """Test that invalid distribution raises."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        rng = _make_rng(rng_type = "pcg64", seed = 0)
        with pytest.raises(Exception_Validation_Input):
            generate_random_returns_tensor(
                num_days = 5, num_scenarios = 4, num_components = 2, distribution_type = "not_a_distribution_type",  # type: ignore[arg-type]
                mean_returns = np.zeros(2), cov_matrix = np.eye(2), dof = 5.0, rng = rng,
            )


# ======================================================================
# compute_portfolio_paths_from_returns_tensor
# ======================================================================


class Test_Compute_Portfolio_Paths_From_Returns_Tensor:
    """Shape, initial value, and compounding correctness."""

    @pytest.mark.unit()
    def test_output_shape(self):
        """Test that output shape."""
        from src.models.simulation.simulation_dispatch import (
            compute_portfolio_paths_from_returns_tensor,
        )

        T, N, K = 10, 8, 3
        tensor = np.zeros((T, N, K))
        weights = np.ones(K) / K
        paths = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 100.0)
        assert paths.shape == (T, N)

    @pytest.mark.unit()
    def test_zero_returns_constant_value(self):
        """Zero returns → all paths stay at initial_value."""
        from src.models.simulation.simulation_dispatch import (
            compute_portfolio_paths_from_returns_tensor,
        )

        T, N, K = 5, 4, 2
        tensor = np.zeros((T, N, K))
        weights = np.array([0.5, 0.5])
        paths = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 200.0)
        np.testing.assert_allclose(paths, 200.0)

    @pytest.mark.unit()
    def test_compounding(self):
        """Constant positive returns should compound geometrically."""
        from src.models.simulation.simulation_dispatch import (
            compute_portfolio_paths_from_returns_tensor,
        )

        T, N, K = 3, 1, 1
        r = 0.01
        tensor = np.full((T, N, K), r)
        weights = np.array([1.0])
        paths = compute_portfolio_paths_from_returns_tensor(returns_tensor = tensor, weights = weights, initial_value = 100.0)
        expected = np.array([[100 * (1 + r) ** t for t in range(1, T + 1)]]).T
        np.testing.assert_allclose(paths, expected, rtol=1e-10)


# ======================================================================
# dispatch_simulation_run — bit-identical results across backends
# ======================================================================


class Test_Dispatch_Simulation_Run_Backend_Equivalence:
    """All 6 backends must produce bit-identical scenario columns."""

    @pytest.mark.unit()
    def test_standard_and_asyncio_identical(self, base_config):
        """Test that standard and asyncio identical."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        df_std, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
        df_async, _ = dispatch_simulation_run(computation_type = "asyncio", config = base_config)

        scenario_cols = [c for c in df_std.columns if c.startswith("Scenario_")]
        for col in scenario_cols:
            np.testing.assert_array_equal(
                df_std[col].to_numpy(), df_async[col].to_numpy(),
                err_msg=f"Column {col} differs between standard and asyncio",
            )

    @pytest.mark.unit()
    def test_joblib_identical_to_standard(self, base_config):
        """Test that joblib identical to standard."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        df_std, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
        df_jb, _ = dispatch_simulation_run(computation_type = "joblib", config = base_config)

        scenario_cols = [c for c in df_std.columns if c.startswith("Scenario_")]
        for col in scenario_cols:
            np.testing.assert_array_equal(
                df_std[col].to_numpy(), df_jb[col].to_numpy(),
                err_msg=f"Column {col} differs between standard and joblib",
            )

    @pytest.mark.unit()
    def test_results_have_correct_columns(self, base_config):
        """Test that results have correct columns."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        df, elapsed = dispatch_simulation_run(computation_type = "standard", config = base_config)
        assert "Date" in df.columns
        assert elapsed >= 0.0
        scenario_cols = [c for c in df.columns if c.startswith("Scenario_")]
        assert len(scenario_cols) == base_config.num_scenarios
        assert df.height == base_config.num_days

    @pytest.mark.unit()
    def test_results_df_date_column_cast(self, base_config):
        """Test that results df date column cast."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        df, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
        assert df["Date"].dtype == pl.Date


class Test_Dispatch_Simulation_Run_Invalid_Backend:
    """Invalid computation_type should raise Exception_Validation_Input."""

    @pytest.mark.unit()
    def test_unknown_backend_raises(self, base_config):
        """Test that unknown backend raises."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        with pytest.raises(Exception_Validation_Input):
            dispatch_simulation_run(computation_type = "unknown_backend_xyz", config = base_config)


# ======================================================================
# compute_simulation_stats
# ======================================================================


class Test_Compute_Simulation_Stats:
    """compute_simulation_stats mirrors Simulation_Base.get_summary_statistics."""

    @pytest.mark.unit()
    def test_columns_present(self, base_config):
        """Test that columns present."""
        from src.models.simulation.simulation_dispatch import (
            compute_simulation_stats,
            dispatch_simulation_run,
        )

        df, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
        stats = compute_simulation_stats(results_df = df)
        expected_cols = {"Date", "Mean", "Median", "Std", "P5", "P25", "P75", "P95", "Min", "Max"}
        assert expected_cols.issubset(set(stats.columns))

    @pytest.mark.unit()
    def test_row_count_matches_num_days(self, base_config):
        """Test that row count matches num days."""
        from src.models.simulation.simulation_dispatch import (
            compute_simulation_stats,
            dispatch_simulation_run,
        )

        df, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
        stats = compute_simulation_stats(results_df = df)
        assert stats.height == base_config.num_days


# ======================================================================
# build_compare_summary_table
# ======================================================================


class Test_Build_Compare_Summary_Table:
    """Shape, columns, 3-row layout, and Δ-rel small-denominator rule."""

    @pytest.fixture()
    def small_compare_results(self, base_config):
        """Run all backends and return compare_results dict."""
        from src.models.simulation.simulation_dispatch import compute_compare_results

        return compute_compare_results(config = base_config)

    @pytest.mark.unit()
    def test_columns(self, small_compare_results):
        """Test that columns."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        table = build_compare_summary_table(compare_results = small_compare_results)
        expected_cols = {
            "Metric", "standard", "asyncio", "asyncio + anyio",
            "trio", "trio + anyio",
        }
        assert expected_cols.issubset(set(table.columns))

    @pytest.mark.unit()
    def test_three_rows_per_metric(self, small_compare_results):
        """Test that three rows per metric."""
        from src.models.simulation.simulation_dispatch import (
            DEFAULT_COMPARE_METRICS,
            build_compare_summary_table,
        )

        table = build_compare_summary_table(compare_results = small_compare_results)
        # 1 Status row + 1 Elapsed row + N metrics × 3 rows (value / Δabs / Δrel)
        assert table.height == (len(DEFAULT_COMPARE_METRICS) * 3) + 2

    @pytest.mark.unit()
    def test_first_metric_is_elapsed_time(self, small_compare_results):
        """Test that first metric is elapsed time."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        table = build_compare_summary_table(compare_results = small_compare_results)
        assert table["Metric"][0] == "Status"
        assert table["Metric"][1] == "Elapsed time (s)"

    @pytest.mark.unit()
    def test_delta_rows_zero_for_bit_identical_results(self, small_compare_results):
        """All financial-metric Δ abs rows must be 0 (bit-identical results).

        Elapsed time (s) is intentionally excluded because backends have
        legitimately different wall-clock times.
        """
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        table = build_compare_summary_table(compare_results = small_compare_results)
        # Filter to Δ abs rows but exclude elapsed-time (which differs by design)
        delta_abs_rows = table.filter(
            pl.col("Metric").str.contains("Δ abs")
            & ~pl.col("Metric").str.contains("Elapsed time")
        )
        assert delta_abs_rows.height > 0, "No financial-metric Δ abs rows found"
        # Every backend column's Δ abs value (vs standard) should be 0.0
        for backend in ["asyncio", "asyncio + anyio", "trio", "trio + anyio", "joblib"]:
            if backend in table.columns:
                vals = [float(v) for v in delta_abs_rows[backend].to_list()]
                for v in vals:
                    assert abs(v) < 1e-10, f"Non-zero Δ abs for {backend}: {v}"

    @pytest.mark.unit()
    def test_delta_rel_small_denominator_rule(self):
        """When |standard| < 0.01, Δ rel = abs_diff (not abs_diff / |standard| * 100).

        Craft compare_results so:
        - standard: day-1 threshold = 50.0, terminal = 200.0 → Prob(Loss) = 0.0
        - asyncio:  day-1 threshold = 50.0, terminal = 10.0  → Prob(Loss) = 100.0

        abs_diff = 100; |standard_val| = 0 < 0.01 → rel = abs_diff = 100 (not inf).
        """
        from src.models.simulation.simulation_dispatch import (
            build_compare_summary_table,
            compute_simulation_stats,
        )

        num_days = 5
        dates = [dt.date(2026, 1, i + 2) for i in range(num_days)]
        n = 10

        data_std: dict = {"Date": dates}
        data_other: dict = {"Date": dates}
        for i in range(n):
            # Day-1 value = 50.0 → used as Prob(Loss) threshold inside _get_terminal_metric
            # Terminal (day-5) = 200.0 → all above 50.0 → Prob(Loss) = 0.0
            data_std[f"Scenario_{i+1}"] = [50.0] + [200.0] * (num_days - 1)
            # Day-1 value = 50.0 (same threshold);
            # Terminal (day-5) = 10.0 → all below 50.0 → Prob(Loss) = 100.0
            data_other[f"Scenario_{i+1}"] = [50.0] + [10.0] * (num_days - 1)

        df_std = pl.DataFrame(data_std).with_columns(pl.col("Date").cast(pl.Date))
        df_other = pl.DataFrame(data_other).with_columns(pl.col("Date").cast(pl.Date))

        def fake_entry(df: pl.DataFrame) -> dict:
            """Fake entry."""
            return {
                "status": "success",
                "results_df": df,
                "stats_df": compute_simulation_stats(results_df = df),
                "elapsed": 0.1,
                "error_type": None,
                "error_message": None,
            }

        compare_results = {
            "standard": fake_entry(df_std),
            "asyncio": fake_entry(df_other),
            "asyncio + anyio": fake_entry(df_std),
            "trio": fake_entry(df_std),
            "trio + anyio": fake_entry(df_std),
            "joblib": fake_entry(df_std),
        }

        table = build_compare_summary_table(
            compare_results = compare_results, metrics_to_include=["Prob(Loss)"]
        )
        # standard Prob(Loss) = 0.0, asyncio = 100.0
        # |standard| = 0.0 < 0.01 → rel_diff = abs_diff = 100.0 (not inf)
        rel_row = table.filter(pl.col("Metric") == "Prob(Loss) (Δ rel)")
        assert rel_row.height == 1
        rel_val = float(rel_row["asyncio"][0])
        assert abs(rel_val - 100.0) < 1e-6, f"Expected rel=100.0, got {rel_val}"

    @pytest.mark.unit()
    def test_custom_metrics_subset(self, small_compare_results):
        """Custom metrics_to_include is respected."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        # "Elapsed time (s)" is filtered out of the numeric loop and rendered
        # as the dedicated single-value Elapsed row — so passing it together
        # with "Mean" yields: Status(1) + Elapsed(1) + Mean×3(3) = 5 rows.
        table = build_compare_summary_table(
            compare_results = small_compare_results, metrics_to_include=["Elapsed time (s)", "Mean"]
        )
        assert table.height == 5  # Status + Elapsed + Mean × 3

    @pytest.mark.unit()
    def test_failed_backend_adds_error_row(self, small_compare_results):
        """A failed backend should add a trailing Error row after all metric rows."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        failed_compare_results = dict(small_compare_results)
        failed_compare_results["trio"] = {
            "status": "error",
            "results_df": None,
            "stats_df": None,
            "elapsed": 0.25,
            "error_type": "Exception_Calculation",
            "error_message": "synthetic trio failure",
        }

        table = build_compare_summary_table(
            compare_results = failed_compare_results, metrics_to_include=["Mean"]
        )

        # Row layout: Status, Elapsed, Mean, Mean (Δ abs), Mean (Δ rel), Error
        assert table["Metric"][0] == "Status"
        assert table["Metric"][1] == "Elapsed time (s)"  # Elapsed is always row 1
        assert table["Metric"][-1] == "Error"            # Error row is trailing

        error_row = table.filter(pl.col("Metric") == "Error")
        assert error_row.height == 1
        assert "Exception_Calculation" in str(error_row["trio"][0])

        # Failed backend's metric cells are N/A (not ERROR)
        mean_value_row = table.filter(pl.col("Metric") == "Mean")
        assert mean_value_row.height == 1
        assert mean_value_row["trio"][0] == "N/A"


# ======================================================================
# compute_compare_results — progress callback
# ======================================================================


class Test_Compute_Compare_Results_Progress_Callback:
    """Progress callback is invoked exactly 5 times with monotone index."""

    @pytest.mark.unit()
    def test_callback_called_five_times(self, base_config):
        """Test that callback called five times."""
        from src.models.simulation.simulation_dispatch import compute_compare_results

        calls: list[tuple[int, str]] = []

        def cb(idx: int, ctype: str) -> None:
            """Cb."""
            calls.append((idx, ctype))

        compute_compare_results(config = base_config, progress_callback=cb)
        assert len(calls) == 5

    @pytest.mark.unit()
    def test_callback_monotone_index(self, base_config):
        """Test that callback monotone index."""
        from src.models.simulation.simulation_dispatch import compute_compare_results

        indices: list[int] = []

        def cb(idx: int, ctype: str) -> None:
            """Cb."""
            indices.append(idx)

        compute_compare_results(config = base_config, progress_callback=cb)
        assert indices == list(range(5))

    @pytest.mark.unit()
    def test_callback_receives_all_types(self, base_config):
        """Test that callback receives all types."""
        from src.models.simulation.simulation_dispatch import (
            COMPUTATION_TYPES_SIMULATION_COMPARE,
            compute_compare_results,
        )

        types_seen: list[str] = []

        def cb(idx: int, ctype: str) -> None:
            """Cb."""
            types_seen.append(ctype)

        compute_compare_results(config = base_config, progress_callback=cb)
        assert types_seen == list(COMPUTATION_TYPES_SIMULATION_COMPARE)


# ======================================================================
# _resolve_num_chunks
# ======================================================================


class Test_Resolve_Num_Chunks:
    """_resolve_num_chunks returns 1 for standard and a bounded value for others."""

    @pytest.mark.unit()
    def test_standard_returns_one(self):
        """Test that standard returns one."""
        from src.models.simulation.simulation_dispatch import _resolve_num_chunks

        assert _resolve_num_chunks(computation_type = "standard", num_scenarios = 1000) == 1

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "backend",
        ["asyncio", "asyncio + anyio", "trio", "trio + anyio", "joblib"],
    )
    def test_non_standard_at_least_one(self, backend: str):
        """Test that non standard at least one."""
        from src.models.simulation.simulation_dispatch import _resolve_num_chunks

        result = _resolve_num_chunks(computation_type = backend, num_scenarios = 10)
        assert result >= 1

    @pytest.mark.unit()
    def test_bounded_by_num_scenarios_single(self):
        """Test that bounded by num scenarios single."""
        from src.models.simulation.simulation_dispatch import _resolve_num_chunks

        # When num_scenarios=1, result must be 1 regardless of cpu_count
        result = _resolve_num_chunks(computation_type = "asyncio", num_scenarios = 1)
        assert result == 1

    @pytest.mark.unit()
    def test_does_not_exceed_num_scenarios(self):
        """Test that does not exceed num scenarios."""
        from src.models.simulation.simulation_dispatch import _resolve_num_chunks

        for n in [2, 5, 10]:
            result = _resolve_num_chunks(computation_type = "joblib", num_scenarios = n)
            assert result <= n

    @pytest.mark.unit()
    def test_invalid_num_scenarios_raises(self):
        """Zero or boolean num_scenarios should raise before chunk resolution."""
        from src.models.simulation.simulation_dispatch import _resolve_num_chunks
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_num_scenarios in (0, True):
            with pytest.raises(Exception_Validation_Input, match="num_scenarios"):
                _resolve_num_chunks(computation_type = "joblib", num_scenarios = item_num_scenarios)


# ======================================================================
# _compute_delta_pair
# ======================================================================


class Test_Compute_Delta_Pair:
    """Unit tests for the \u0394 helper used in build_compare_summary_table."""

    @pytest.mark.unit()
    def test_both_na_when_candidate_is_none(self):
        """Test that both na when candidate is none."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        abs_str, rel_str = _compute_delta_pair(value_candidate = None, value_standard = 100.0)
        assert abs_str == "N/A"
        assert rel_str == "N/A"

    @pytest.mark.unit()
    def test_both_na_when_standard_is_none(self):
        """Test that both na when standard is none."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        abs_str, rel_str = _compute_delta_pair(value_candidate = 100.0, value_standard = None)
        assert abs_str == "N/A"
        assert rel_str == "N/A"

    @pytest.mark.unit()
    def test_both_na_when_non_finite(self):
        """Test that both na when non finite."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        abs_str, rel_str = _compute_delta_pair(value_candidate = float("nan"), value_standard = 100.0)
        assert abs_str == "N/A"
        assert rel_str == "N/A"

        abs_str2, rel_str2 = _compute_delta_pair(value_candidate = 100.0, value_standard = float("inf"))
        assert abs_str2 == "N/A"
        assert rel_str2 == "N/A"

    @pytest.mark.unit()
    def test_zero_diff_identical_values(self):
        """Test that zero diff identical values."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        abs_str, rel_str = _compute_delta_pair(value_candidate = 100.0, value_standard = 100.0)
        assert float(abs_str) == pytest.approx(0.0, abs=1e-12)
        assert float(rel_str) == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit()
    def test_small_denominator_rule_rel_equals_abs(self):
        """When |standard| < 0.01, \u0394_rel = \u0394_abs (not \u0394_abs / |standard|)."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        # standard = 0.005 (< 0.01), candidate = 0.035, abs_diff = 0.03
        abs_str, rel_str = _compute_delta_pair(value_candidate = 0.035, value_standard = 0.005)
        assert float(abs_str) == pytest.approx(0.03, rel=1e-6)
        # \u0394_rel should equal \u0394_abs, NOT 0.03 / 0.005 = 6.0
        assert float(rel_str) == pytest.approx(0.03, rel=1e-6)

    @pytest.mark.unit()
    def test_normal_denominator_rule_rel_is_ratio(self):
        """When |standard| >= 0.01, \u0394_rel = \u0394_abs / |standard|."""
        from src.models.simulation.simulation_dispatch import _compute_delta_pair

        # standard = 200.0, candidate = 202.0, abs_diff = 2.0
        # rel = 2.0 / 200.0 = 0.01
        abs_str, rel_str = _compute_delta_pair(value_candidate = 202.0, value_standard = 200.0)
        assert float(abs_str) == pytest.approx(2.0, rel=1e-6)
        assert float(rel_str) == pytest.approx(0.01, rel=1e-6)


# ======================================================================
# All backends bit-identical for same seed
# ======================================================================


class Test_All_Backends_Bit_Identical_Same_Seed:
    """All 6 backends produce identical terminal statistics for the same seed."""

    @pytest.mark.unit()
    @pytest.mark.parametrize(
        "backend",
        ["asyncio", "asyncio + anyio", "trio", "trio + anyio", "joblib"],
    )
    def test_terminal_stats_match_standard(self, base_config, backend: str):
        """Each non-standard backend must produce terminal statistics within 1 e-9 of standard."""
        from src.models.simulation.simulation_dispatch import (
            compute_simulation_stats,
            dispatch_simulation_run,
        )

        try:
            std_df, _ = dispatch_simulation_run(computation_type = "standard", config = base_config)
            other_df, _ = dispatch_simulation_run(computation_type = backend, config = base_config)
        except Exception as exc:  # pragma: no cover \u2014 skip if optional dep missing
            pytest.skip(f"{backend} unavailable: {exc}")

        std_stats = compute_simulation_stats(results_df = std_df)
        other_stats = compute_simulation_stats(results_df = other_df)

        for col in ["Mean", "Median", "Std", "P5", "P95", "Min", "Max"]:
            std_vals = std_stats[col].to_list()
            other_vals = other_stats[col].to_list()
            for sv, ov in zip(std_vals, other_vals):
                assert abs(float(sv) - float(ov)) < 1e-9, (
                    f"Mismatch in {col} between standard and {backend}: {sv} vs {ov}"
                )


# ======================================================================
# compute_compare_results — all 6 backends succeed
# ======================================================================


class Test_Compute_Compare_Results_All_Backends_Succeed:
    """compute_compare_results must complete successfully for all 5 backends.

    The ``standard`` entry is used as the canonical reference. Every
    other backend entry must be byte-identical.
    """

    @pytest.mark.unit()
    def test_all_five_entries_have_success_status(self, base_config) -> None:
        """Every backend entry must have status=='success'."""
        from src.models.simulation.simulation_dispatch import (
            COMPUTATION_TYPES_SIMULATION_COMPARE,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE:
            entry = compare_results.get(computation_type)
            assert entry is not None, f"Missing entry for {computation_type}"
            assert entry["status"] == "success", (
                f"{computation_type} failed: "
                f"{entry.get('error_type')}: {entry.get('error_message')}"
            )

    @pytest.mark.unit()
    def test_all_entries_have_results_df_and_stats_df(self, base_config) -> None:
        """Every successful entry must contain a non-empty results_df and stats_df."""
        from src.models.simulation.simulation_dispatch import (
            COMPUTATION_TYPES_SIMULATION_COMPARE,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE:
            entry = compare_results[computation_type]
            results_df = entry.get("results_df")
            stats_df = entry.get("stats_df")
            assert isinstance(results_df, pl.DataFrame), (
                f"results_df missing for {computation_type}"
            )
            assert isinstance(stats_df, pl.DataFrame), (
                f"stats_df missing for {computation_type}"
            )
            assert results_df.height == base_config.num_days
            assert stats_df.height == base_config.num_days

    @pytest.mark.unit()
    def test_all_non_standard_entries_bit_identical_to_standard(self, base_config) -> None:
        """Every non-standard backend's Scenario columns must be byte-identical to standard."""
        from src.models.simulation.simulation_dispatch import (
            COMPUTATION_TYPES_SIMULATION_COMPARE,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        std_df: pl.DataFrame = compare_results["standard"]["results_df"]
        scenario_cols = [c for c in std_df.columns if c.startswith("Scenario_")]

        for computation_type in COMPUTATION_TYPES_SIMULATION_COMPARE:
            if computation_type == "standard":
                continue
            entry = compare_results[computation_type]
            if entry["status"] != "success":  # pragma: no cover
                pytest.skip(f"{computation_type} did not succeed")
            other_df: pl.DataFrame = entry["results_df"]
            for col in scenario_cols:
                np.testing.assert_array_equal(
                    std_df[col].to_numpy(),
                    other_df[col].to_numpy(),
                    err_msg=(
                        f"Column {col} differs between standard and {computation_type}"
                    ),
                )


# ======================================================================
# Nested event-loop safety
# ======================================================================


class Test_Dispatch_Nested_Event_Loop_Safety:
    """dispatch_simulation_run for async backends does not raise RuntimeError inside asyncio."""

    @pytest.mark.unit()
    def test_asyncio_backend_inside_running_loop(self, base_config):
        """Calling the asyncio backend from within a running event loop must not crash."""
        import asyncio

        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        async def inner():
            """Inner."""
            results_df, elapsed = dispatch_simulation_run(computation_type = "asyncio", config = base_config)
            return results_df, elapsed

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop — safe to use asyncio.run()
            results_df, elapsed = asyncio.run(inner())
        else:
            # Already inside an event loop — run in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                results_df, elapsed = pool.submit(
                    lambda: asyncio.run(inner())
                ).result()
        assert results_df is not None
        assert elapsed >= 0.0


# ======================================================================
# compute_compare_results \u2014 partial failure continues
# ======================================================================


class Test_Compare_Partial_Failure_Continues:
    """When one backend raises, compare_results still includes the remaining 5."""

    @pytest.mark.unit()
    def test_remaining_backends_succeed_when_one_raises(self, base_config):
        """Mock trio to always raise; all other backends should succeed."""
        import unittest.mock

        import src.models.simulation.simulation_dispatch as dispatch_mod
        from src.models.simulation.simulation_dispatch import compute_compare_results

        def fake_trio_runner(chunk_tensors, weights, initial_value):
            """Fake trio runner."""
            raise RuntimeError("Synthetic trio failure")

        # Patch the _BACKEND_RUNNERS dict entry so compute_compare_results
        # picks up the mock (dict is already bound at import time).
        patched_runners = dict(dispatch_mod._BACKEND_RUNNERS)
        patched_runners["trio"] = fake_trio_runner

        with unittest.mock.patch.object(dispatch_mod, "_BACKEND_RUNNERS", patched_runners):
            compare_results = compute_compare_results(config = base_config)

        assert compare_results["trio"]["status"] == "error"
        assert "Synthetic trio failure" in str(compare_results["trio"]["error_message"])

        for backend in ["standard", "asyncio", "asyncio + anyio", "trio + anyio"]:
            assert compare_results[backend]["status"] == "success", (
                f"Expected {backend} to succeed, got: {compare_results[backend]}"
            )


# ======================================================================
# build_compare_summary_table \u2014 Elapsed is single row, no \u0394 sub-rows
# ======================================================================


class Test_Build_Compare_Summary_Table_Elapsed_Single_Row:
    """Elapsed time (s) produces exactly one row with no \u0394 sub-rows."""

    @pytest.fixture()
    def all_success_results(self, base_config):
        """All success results."""
        from src.models.simulation.simulation_dispatch import compute_compare_results

        return compute_compare_results(config = base_config)

    @pytest.mark.unit()
    def test_elapsed_has_no_delta_rows(self, all_success_results):
        """Test that elapsed has no delta rows."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        table = build_compare_summary_table(compare_results = all_success_results)

        elapsed_rows = table.filter(pl.col("Metric").str.starts_with("Elapsed"))
        # Only the value row \u2014 no \u0394 abs or \u0394 rel
        assert elapsed_rows.height == 1
        assert elapsed_rows["Metric"][0] == "Elapsed time (s)"

    @pytest.mark.unit()
    def test_elapsed_row_is_always_row_1(self, all_success_results):
        """Test that elapsed row is always row 1."""
        from src.models.simulation.simulation_dispatch import build_compare_summary_table

        table = build_compare_summary_table(compare_results = all_success_results)
        assert table["Metric"][0] == "Status"
        assert table["Metric"][1] == "Elapsed time (s)"


# ======================================================================
# Internal helpers — branch coverage
# ======================================================================


class Test_Internal_Helpers_Branch_Coverage:
    """Targeted tests that exercise defensive branches missed by higher-level tests.

    These tests call private helpers directly with crafted inputs to ensure
    both sides of every conditional are covered.
    """

    # ------------------------------------------------------------------
    # Simulation_Run_Config — default start_date
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_simulation_run_config_default_start_date(self, dist_normal) -> None:
        """Omitting start_date uses the typed default factory to fill today's date."""
        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        cfg = Simulation_Run_Config(
            names_components=["A"],
            weights=np.array([1.0]),
            distribution_type=dist_normal,
            mean_returns=np.array([0.0001]),
            covariance_matrix=np.array([[0.0001]]),
        )
        import datetime as dt

        assert cfg.start_date is not None
        assert isinstance(cfg.start_date, dt.date)

    @pytest.mark.unit()
    def test_simulation_run_config_bool_numeric_fields_raise(self, dist_normal) -> None:
        """Boolean numeric fields should be rejected before Pydantic coercion."""
        from pydantic import ValidationError

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        common = {
            "names_components": ["A"],
            "weights": np.array([1.0]),
            "distribution_type": dist_normal,
            "mean_returns": np.array([0.0001]),
            "covariance_matrix": np.array([[0.0001]]),
        }

        for item_field_name in (
            "initial_value",
            "num_scenarios",
            "num_days",
            "random_seed",
            "degrees_of_freedom",
        ):
            with pytest.raises(ValidationError, match=item_field_name):
                Simulation_Run_Config(
                    **common,
                    **{item_field_name: True},
                )

    @pytest.mark.unit()
    def test_simulation_run_config_invalid_numeric_ranges_raise(self, dist_normal) -> None:
        """Invalid numeric ranges should be rejected at the config boundary."""
        from pydantic import ValidationError

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        common = {
            "names_components": ["A"],
            "weights": np.array([1.0]),
            "distribution_type": dist_normal,
            "mean_returns": np.array([0.0001]),
            "covariance_matrix": np.array([[0.0001]]),
        }

        for item_field_name, item_value in (
            ("initial_value", 0.0),
            ("initial_value", float("nan")),
            ("num_scenarios", 0),
            ("num_days", 0),
            ("random_seed", -1),
            ("degrees_of_freedom", float("inf")),
        ):
            with pytest.raises(ValidationError, match=item_field_name):
                Simulation_Run_Config(
                    **common,
                    **{item_field_name: item_value},
                )

    @pytest.mark.unit()
    def test_simulation_run_config_student_t_invalid_degrees_of_freedom_raises(
        self,
        dist_student_t,
    ) -> None:
        """Student-t configs should reject degrees_of_freedom <= 2."""
        from pydantic import ValidationError

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        with pytest.raises(ValidationError, match="degrees_of_freedom"):
            Simulation_Run_Config(
                names_components=["A"],
                weights=np.array([1.0]),
                distribution_type=dist_student_t,
                mean_returns=np.array([0.0001]),
                covariance_matrix=np.array([[0.0001]]),
                degrees_of_freedom=2.0,
            )

    @pytest.mark.unit()
    def test_simulation_run_config_invalid_rng_type_raises(self, dist_normal) -> None:
        """Unsupported rng_type values should be rejected at config construction."""
        from pydantic import ValidationError

        from src.models.simulation.simulation_dispatch import Simulation_Run_Config

        common = {
            "names_components": ["A"],
            "weights": np.array([1.0]),
            "distribution_type": dist_normal,
            "mean_returns": np.array([0.0001]),
            "covariance_matrix": np.array([[0.0001]]),
        }

        for item_rng_type in ("invalid_rng", True):
            with pytest.raises(ValidationError, match="rng_type"):
                Simulation_Run_Config(
                    **common,
                    rng_type=item_rng_type,
                )

    # ------------------------------------------------------------------
    # _run_callable_in_new_thread — exception propagation
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_run_callable_reraises_exception_from_thread(self) -> None:
        """An exception raised inside the callable must propagate to the caller."""
        from src.models.simulation.simulation_dispatch import _run_callable_in_new_thread

        def _boom() -> None:
            raise ValueError("synthetic thread failure")

        with pytest.raises(ValueError, match="synthetic thread failure"):
            _run_callable_in_new_thread(callable_target = _boom)

    @pytest.mark.unit()
    def test_run_callable_raises_when_thread_returns_no_result(self) -> None:
        """A thread that sets neither result nor error must raise Exception_Calculation."""
        import unittest.mock

        import src.models.simulation._sim_runners as sim_runners_mod
        from src.models.simulation.simulation_dispatch import _run_callable_in_new_thread
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        class _ThreadWithoutOutcome:
            def __init__(self, target, daemon):
                self._target = target
                self._daemon = daemon

            def start(self) -> None:
                return None

            def join(self) -> None:
                return None

        with unittest.mock.patch.object(
            sim_runners_mod.threading,
            "Thread",
            _ThreadWithoutOutcome,
        ):
            with pytest.raises(
                Exception_Calculation,
                match="completed without returning a result",
            ):
                _run_callable_in_new_thread(callable_target = lambda: 123)

    @pytest.mark.unit()
    def test_run_chunks_asyncio_anyio_missing_anyio_raises(self) -> None:
        """Missing anyio should be translated to Exception_Configuration."""
        import builtins
        import unittest.mock

        from src.models.simulation._sim_runners import _run_chunks_asyncio_anyio
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        real_import = builtins.__import__

        def _missing_anyio(name, *args, **kwargs):
            if name == "anyio":
                raise ImportError("forced anyio missing")
            return real_import(name, *args, **kwargs)

        with unittest.mock.patch("builtins.__import__", side_effect=_missing_anyio):
            with pytest.raises(Exception_Configuration, match="anyio is not installed"):
                _run_chunks_asyncio_anyio(chunk_tensors = [np.zeros((2, 1, 1))], weights = np.array([1.0]), initial_value = 100.0)

    @pytest.mark.unit()
    def test_run_chunks_trio_missing_trio_raises(self) -> None:
        """Missing trio should be translated to Exception_Configuration."""
        import builtins
        import unittest.mock

        from src.models.simulation._sim_runners import _run_chunks_trio
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        real_import = builtins.__import__

        def _missing_trio(name, *args, **kwargs):
            if name == "trio":
                raise ImportError("forced trio missing")
            return real_import(name, *args, **kwargs)

        with unittest.mock.patch("builtins.__import__", side_effect=_missing_trio):
            with pytest.raises(Exception_Configuration, match="trio is not installed"):
                _run_chunks_trio(chunk_tensors = [np.zeros((2, 1, 1))], weights = np.array([1.0]), initial_value = 100.0)

    @pytest.mark.unit()
    def test_run_chunks_trio_anyio_missing_dependency_raises(self) -> None:
        """Missing trio in the anyio/trio backend should raise Exception_Configuration."""
        import builtins
        import unittest.mock

        from src.models.simulation._sim_runners import _run_chunks_trio_anyio
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        real_import = builtins.__import__

        def _missing_trio(name, *args, **kwargs):
            if name == "trio":
                raise ImportError("forced trio missing")
            return real_import(name, *args, **kwargs)

        with unittest.mock.patch("builtins.__import__", side_effect=_missing_trio):
            with pytest.raises(
                Exception_Configuration,
                match="Both trio and anyio must be installed",
            ):
                _run_chunks_trio_anyio(chunk_tensors = [np.zeros((2, 1, 1))], weights = np.array([1.0]), initial_value = 100.0)

    @pytest.mark.unit()
    def test_run_chunks_joblib_missing_joblib_raises(self) -> None:
        """Missing joblib should be translated to Exception_Configuration."""
        import builtins
        import unittest.mock

        from src.models.simulation._sim_runners import _run_chunks_joblib
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        real_import = builtins.__import__

        def _missing_joblib(name, *args, **kwargs):
            if name == "joblib":
                raise ImportError("forced joblib missing")
            return real_import(name, *args, **kwargs)

        with unittest.mock.patch("builtins.__import__", side_effect=_missing_joblib):
            with pytest.raises(Exception_Configuration, match="joblib is not installed"):
                _run_chunks_joblib(chunk_tensors = [np.zeros((2, 1, 1))], weights = np.array([1.0]), initial_value = 100.0)

    @pytest.mark.unit()
    def test_run_chunks_joblib_uses_threadpool_limits_when_available(self) -> None:
        """threadpoolctl limits BLAS threads to 1 inside the Parallel call."""
        import unittest.mock

        import numpy as np

        from src.models.simulation._sim_runners import _run_chunks_joblib

        fake_parallel = unittest.mock.MagicMock()
        fake_parallel.return_value = [np.zeros((2, 1))]
        fake_limits = unittest.mock.MagicMock()
        fake_limits.__enter__ = unittest.mock.Mock(return_value=None)
        fake_limits.__exit__ = unittest.mock.Mock(return_value=False)

        with (
            unittest.mock.patch("joblib.Parallel", return_value=fake_parallel),
            unittest.mock.patch("joblib.parallel_backend", unittest.mock.MagicMock()),
            unittest.mock.patch("joblib.delayed", lambda fn: fn),
            unittest.mock.patch(
                "threadpoolctl.threadpool_limits",
                return_value=fake_limits,
            ) as mock_limits,
        ):
            _run_chunks_joblib(
                chunk_tensors=[np.zeros((2, 1, 1))],
                weights=np.array([1.0]),
                initial_value=100.0,
            )

        mock_limits.assert_called_once_with(limits=1, user_api="blas")
        fake_limits.__enter__.assert_called_once()
        fake_limits.__exit__.assert_called_once()

    @pytest.mark.unit()
    def test_run_chunks_joblib_skips_threadpool_limits_when_unavailable(self) -> None:
        """If threadpoolctl is absent the runner still works (nullcontext fallback)."""
        import builtins
        import unittest.mock

        import numpy as np

        from src.models.simulation._sim_runners import _run_chunks_joblib

        real_import = builtins.__import__

        def _missing_threadpoolctl(name, *args, **kwargs):
            if name == "threadpoolctl":
                raise ImportError("forced threadpoolctl missing")
            return real_import(name, *args, **kwargs)

        fake_parallel = unittest.mock.MagicMock()
        fake_parallel.return_value = [np.zeros((2, 1))]

        with unittest.mock.patch("builtins.__import__", side_effect=_missing_threadpoolctl):
            with (
                unittest.mock.patch("joblib.Parallel", return_value=fake_parallel),
                unittest.mock.patch("joblib.parallel_backend", unittest.mock.MagicMock()),
                unittest.mock.patch("joblib.delayed", lambda fn: fn),
            ):
                result = _run_chunks_joblib(
                    chunk_tensors=[np.zeros((2, 1, 1))],
                    weights=np.array([1.0]),
                    initial_value=100.0,
                )

        assert len(result) == 1
        assert np.array_equal(result[0], np.zeros((2, 1)))

    @pytest.mark.unit()
    def test_run_chunks_joblib_falls_back_to_standard_on_timeout(self) -> None:
        """If joblib exceeds 15 s the runner falls back to standard sequentially."""
        import time
        import unittest.mock

        import numpy as np

        from src.models.simulation._sim_runners import _run_chunks_joblib

        def _slow_joblib_callable(*args, **kwargs):
            """Simulate a joblib call that hangs longer than the timeout."""
            time.sleep(20)
            return [np.zeros((2, 1))]

        with (
            unittest.mock.patch("joblib.Parallel", side_effect=_slow_joblib_callable),
            unittest.mock.patch("joblib.parallel_backend", unittest.mock.MagicMock()),
            unittest.mock.patch("joblib.delayed", lambda fn: fn),
            unittest.mock.patch(
                "threadpoolctl.threadpool_limits",
                return_value=unittest.mock.MagicMock(),
            ),
        ):
            result = _run_chunks_joblib(
                chunk_tensors=[np.zeros((2, 1, 1))],
                weights=np.array([1.0]),
                initial_value=100.0,
            )

        # Fallback to standard produces the real computed result (not mocked zeros)
        assert len(result) == 1
        assert np.array_equal(result[0], np.array([[100.0], [100.0]]))

    @pytest.mark.unit()
    def test_run_chunks_joblib_returns_fast_result_without_timeout(self) -> None:
        """A fast joblib call returns normally without triggering the fallback."""
        import unittest.mock

        import numpy as np

        from src.models.simulation._sim_runners import _run_chunks_joblib

        fake_parallel = unittest.mock.MagicMock()
        fake_parallel.return_value = [np.zeros((2, 1))]

        with (
            unittest.mock.patch("joblib.Parallel", return_value=fake_parallel),
            unittest.mock.patch("joblib.parallel_backend", unittest.mock.MagicMock()),
            unittest.mock.patch("joblib.delayed", lambda fn: fn),
            unittest.mock.patch(
                "threadpoolctl.threadpool_limits",
                return_value=unittest.mock.MagicMock(),
            ),
        ):
            result = _run_chunks_joblib(
                chunk_tensors=[np.zeros((2, 1, 1))],
                weights=np.array([1.0]),
                initial_value=100.0,
            )

        assert len(result) == 1
        assert np.array_equal(result[0], np.zeros((2, 1)))

    # ------------------------------------------------------------------
    # dispatch_simulation_run — progress_callback path
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_dispatch_progress_callback_invoked(self, base_config) -> None:
        """progress_callback is called with the computation_type string."""
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run

        calls: list[str] = []
        dispatch_simulation_run(computation_type = "standard", config = base_config, progress_callback=calls.append)
        assert calls == ["standard"]

    # ------------------------------------------------------------------
    # dispatch_simulation_run — re-raise of Exception_Configuration
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_dispatch_reraises_exception_configuration(self, base_config) -> None:
        """Exception_Configuration from a runner must not be wrapped."""
        import unittest.mock

        import src.models.simulation.simulation_dispatch as dispatch_mod
        from src.models.simulation.simulation_dispatch import dispatch_simulation_run
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Configuration,
        )

        def _raise_cfg(chunk_tensors, weights, initial_value):
            raise Exception_Configuration("synthetic config error")

        patched_runners = dict(dispatch_mod._BACKEND_RUNNERS)
        patched_runners["standard"] = _raise_cfg
        with unittest.mock.patch.object(dispatch_mod, "_BACKEND_RUNNERS", patched_runners):
            with pytest.raises(Exception_Configuration, match="synthetic config error"):
                dispatch_simulation_run(computation_type = "standard", config = base_config)

    # ------------------------------------------------------------------
    # _safe_cholesky — PSD fallback
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_safe_cholesky_psd_fallback_for_near_singular_matrix(self) -> None:
        """_safe_cholesky must succeed (via PSD fallback) for a near-singular matrix."""
        from src.models.simulation.simulation_dispatch import _safe_cholesky

        # A matrix with a tiny negative eigenvalue due to floating-point noise
        mat = np.array([[1.0, 1.0], [1.0, 1.0 - 1e-15]])
        result = _safe_cholesky(matrix = mat)
        # Result must be lower triangular and L @ L.T must approximate the PSD form
        assert result.shape == (2, 2)
        assert result[0, 1] == pytest.approx(0.0, abs=1e-10)  # lower triangular

    # ------------------------------------------------------------------
    # generate_random_returns_tensor — lognormal negative-arg guard
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_generate_random_returns_tensor_lognormal_negative_arg_raises(
        self, dist_lognormal
    ) -> None:
        """A covariance matrix that makes the lognormal arg non-positive must raise."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Calculation,
        )

        # mean_returns = [0.001, 0.001], off-diagonal cov = -1 forces arg <= 0
        rng = _make_rng(rng_type = "pcg64", seed = 0)
        with pytest.raises(Exception_Calculation, match="Lognormal parameter mapping failed"):
            generate_random_returns_tensor(
                num_days = 2, num_scenarios = 4, num_components = 2, distribution_type = dist_lognormal,
                mean_returns = np.array([0.001, 0.001]),
                cov_matrix = np.array([[0.0004, -1.0], [-1.0, 0.0004]]),
                dof = 5.0,
                rng = rng,
            )

    # ------------------------------------------------------------------
    # generate_random_returns_tensor — unsupported distribution type
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_generate_random_returns_tensor_invalid_distribution_raises(self) -> None:
        """Passing an unrecognised distribution type must raise Exception_Validation_Input."""
        from src.models.simulation.simulation_dispatch import (
            _make_rng,
            generate_random_returns_tensor,
        )
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        rng = _make_rng(rng_type = "pcg64", seed = 0)
        with pytest.raises(Exception_Validation_Input):
            generate_random_returns_tensor(
                num_days = 2, num_scenarios = 4, num_components = 2,
                distribution_type = "INVALID_DIST_TYPE",  # type: ignore[arg-type]
                mean_returns = np.array([0.001, 0.001]),
                cov_matrix = np.eye(2) * 0.0004,
                dof = 5.0,
                rng = rng,
            )

    @pytest.mark.unit()
    def test_make_rng_invalid_rng_type_raises(self) -> None:
        """Unsupported rng_type values should raise instead of silently defaulting."""
        from src.models.simulation.simulation_dispatch import _make_rng
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_rng_type in ("invalid_rng", True):
            with pytest.raises(Exception_Validation_Input, match="rng_type"):
                _make_rng(rng_type = item_rng_type, seed = 0)

    @pytest.mark.unit()
    def test_make_rng_invalid_seed_raises(self) -> None:
        """Invalid seed values should raise before NumPy coercion or failure."""
        from src.models.simulation.simulation_dispatch import _make_rng
        from src.utils.custom_exceptions_errors_loggers.exception_custom import (
            Exception_Validation_Input,
        )

        for item_seed in (True, -1):
            with pytest.raises(Exception_Validation_Input, match="seed"):
                _make_rng(rng_type = "pcg64", seed = item_seed)

    # ------------------------------------------------------------------
    # _compare_entry_is_successful — None / bad-type guard
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_compare_entry_is_successful_none(self) -> None:
        """None input returns False (not-a-dict branch)."""
        from src.models.simulation.simulation_dispatch import _compare_entry_is_successful

        assert _compare_entry_is_successful(entry = None) is False

    @pytest.mark.unit()
    def test_compare_entry_is_successful_missing_dfs(self) -> None:
        """Dict with status='success' but None DataFrames returns False."""
        from src.models.simulation.simulation_dispatch import _compare_entry_is_successful

        entry = {"status": "success", "results_df": None, "stats_df": None,
                 "elapsed": 0.1, "error_type": None, "error_message": None}
        assert _compare_entry_is_successful(entry = entry) is False

    # ------------------------------------------------------------------
    # _format_compare_value — None / non-finite guard
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_format_compare_value_none_returns_na(self) -> None:
        """None input returns 'N/A'."""
        from src.models.simulation.simulation_dispatch import _format_compare_value

        assert _format_compare_value(value = None) == "N/A"

    @pytest.mark.unit()
    def test_format_compare_value_nan_returns_na(self) -> None:
        """NaN input returns 'N/A'."""
        from src.models.simulation.simulation_dispatch import _format_compare_value

        assert _format_compare_value(value = float("nan")) == "N/A"

    # ------------------------------------------------------------------
    # _format_compare_error — non-dict guard
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_format_compare_error_none_returns_missing(self) -> None:
        """None input returns the 'Missing compare result' sentinel string."""
        from src.models.simulation.simulation_dispatch import _format_compare_error

        result = _format_compare_error(entry = None)
        assert result == "Missing compare result"

    # ------------------------------------------------------------------
    # _get_terminal_metric — Elapsed time (s) path
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_get_terminal_metric_elapsed_time(self, base_config) -> None:
        """_get_terminal_metric with 'Elapsed time (s)' returns the elapsed float."""
        from src.models.simulation.simulation_dispatch import (
            _get_terminal_metric,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        entry = compare_results["standard"]
        result = _get_terminal_metric(entry = entry, metric = "Elapsed time (s)")
        assert isinstance(result, float)
        assert result >= 0.0

    # ------------------------------------------------------------------
    # _get_terminal_metric — unsupported metric name
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_get_terminal_metric_unknown_metric_returns_nan(self, base_config) -> None:
        """An unrecognised metric name must return NaN (not raise)."""
        from src.models.simulation.simulation_dispatch import (
            _get_terminal_metric,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        entry = compare_results["standard"]
        result = _get_terminal_metric(entry = entry, metric = "NoSuchMetric_XYZ")
        assert not np.isfinite(result)

    # ------------------------------------------------------------------
    # _get_terminal_metric — failed entry guard
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_get_terminal_metric_failed_entry_returns_nan(self) -> None:
        """A failed (non-successful) entry must return NaN."""
        from src.models.simulation.simulation_dispatch import _get_terminal_metric

        failed_entry = {
            "status": "error", "results_df": None, "stats_df": None,
            "elapsed": 0.1, "error_type": "RuntimeError", "error_message": "boom",
        }
        result = _get_terminal_metric(entry = failed_entry, metric = "Mean")
        assert not np.isfinite(result)

    # ------------------------------------------------------------------
    # build_compare_summary_table — standard backend absent (non-dict entry)
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_build_compare_summary_table_missing_standard_entry(self, base_config) -> None:
        """When 'standard' entry is None, metric Δ values are 'N/A' and elapsed is 'N/A'."""
        from src.models.simulation.simulation_dispatch import (
            build_compare_summary_table,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        # Replace standard with None to trigger the non-dict / absent-standard paths
        compare_results_no_std = dict(compare_results)
        compare_results_no_std["standard"] = None  # type: ignore[assignment]
        table = build_compare_summary_table(
            compare_results = compare_results_no_std,
            metrics_to_include=["Mean"],
        )
        # Elapsed row: standard column should be "N/A" (non-dict entry)
        elapsed_row = table.filter(pl.col("Metric") == "Elapsed time (s)")
        assert elapsed_row["standard"][0] == "N/A"
        # Δ values for other backends: standard_value is None → "N/A"
        delta_abs_row = table.filter(pl.col("Metric") == "Mean (Δ abs)")
        assert delta_abs_row["asyncio"][0] == "N/A"

    # ------------------------------------------------------------------
    # build_compare_summary_table — standard backend failed (dict entry)
    # ------------------------------------------------------------------

    @pytest.mark.unit()
    def test_build_compare_summary_table_standard_failed_entry(self, base_config) -> None:
        """When 'standard' entry has status='error', metric standard_values are None."""
        from src.models.simulation.simulation_dispatch import (
            build_compare_summary_table,
            compute_compare_results,
        )

        compare_results = compute_compare_results(config = base_config)
        compare_results_std_failed = dict(compare_results)
        compare_results_std_failed["standard"] = {
            "status": "error", "results_df": None, "stats_df": None,
            "elapsed": 0.05, "error_type": "RuntimeError", "error_message": "std failed",
        }
        table = build_compare_summary_table(
            compare_results = compare_results_std_failed,
            metrics_to_include=["Mean"],
        )
        # With standard failed, Δ abs for asyncio should be "N/A"
        delta_abs_row = table.filter(pl.col("Metric") == "Mean (Δ abs)")
        assert delta_abs_row["asyncio"][0] == "N/A"

