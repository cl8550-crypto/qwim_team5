"""Concurrency backend runner functions for Monte Carlo simulation.

Extracted from ``simulation_dispatch`` to keep each file under 1000 LOC.
All public names are re-exported via ``simulation_dispatch``.

Notes
-----
Each ``_run_chunks_*`` function accepts the same three arguments
(``chunk_tensors``, ``weights``, ``initial_value``) and returns
``list[np.ndarray]`` where each element has shape ``(T, chunk_N)``.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import os
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import numpy as np

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Calculation,
    Exception_Configuration,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._sim_math import compute_portfolio_paths_from_returns_tensor


_logger = get_logger(name = __name__)


# ---------------------------------------------------------------------------
# Thread-isolation helper
# ---------------------------------------------------------------------------


def _run_callable_in_new_thread[Result_Type](
    *, callable_target: Callable[[], Result_Type]) -> Result_Type:
    """Run *callable_target* in a dedicated thread and return its result.

    This isolates event-loop-based backends from the active Shiny event loop,
    allowing helpers like ``asyncio.run`` and ``anyio.run`` to execute in a
    clean thread even when the caller is already inside an event loop.
    """
    result_holder: dict[str, Result_Type] = {}
    error_holder: dict[str, BaseException] = {}

    def _thread_target() -> None:
        """Run callable_target in this thread; capture result or exception."""
        try:
            result_holder["result"] = callable_target()
        except BaseException as exc_error:  # noqa: BLE001 — re-raised in calling thread
            error_holder["error"] = exc_error

    worker_thread = threading.Thread(target=_thread_target, daemon=False)
    worker_thread.start()
    worker_thread.join()

    if "error" in error_holder:
        raise error_holder["error"]

    if "result" not in result_holder:
        raise Exception_Calculation(
            "Isolated backend thread completed without returning a result",
        )

    return result_holder["result"]


# ---------------------------------------------------------------------------
# Backend runners
# ---------------------------------------------------------------------------


def _run_chunks_standard(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Sequential for-loop runner (no parallelism)."""
    return [
        compute_portfolio_paths_from_returns_tensor(returns_tensor = ct, weights = weights, initial_value = initial_value)
        for ct in chunk_tensors
    ]


def _run_chunks_asyncio(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Asyncio runner using ``asyncio.to_thread`` per chunk."""

    async def _async_main() -> list[np.ndarray]:
        """Gather all asyncio.to_thread tasks and return combined results."""
        tasks = [
            asyncio.to_thread(
                compute_portfolio_paths_from_returns_tensor,
                returns_tensor=ct,
                weights=weights,
                initial_value=initial_value,
            )
            for ct in chunk_tensors
        ]
        return list(await asyncio.gather(*tasks))

    return _run_callable_in_new_thread(callable_target = lambda: asyncio.run(_async_main()))


def _run_chunks_asyncio_anyio(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Anyio (asyncio backend) runner using task groups."""
    try:
        import anyio  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError as exc:
        raise Exception_Configuration(
            "anyio is not installed; cannot use 'asyncio + anyio' backend. Run: pip install anyio",
        ) from exc

    results: list[np.ndarray | None] = [None] * len(chunk_tensors)

    async def _run_all() -> None:
        """Start all chunk tasks in the anyio (asyncio backend) task group."""
        async with anyio.create_task_group() as tg:
            for idx_chunk, ct in enumerate(chunk_tensors):

                async def _run_one(
                    idx: int, ct_inner: np.ndarray) -> None:
                    """Run one chunk in an anyio thread and store the result."""
                    results[idx] = await anyio.to_thread.run_sync(
                        functools.partial(
                            compute_portfolio_paths_from_returns_tensor,
                            returns_tensor=ct_inner,
                            weights=weights,
                            initial_value=initial_value,
                        ),
                    )

                tg.start_soon(_run_one, idx_chunk, ct)

    _run_callable_in_new_thread(callable_target = lambda: anyio.run(_run_all, backend="asyncio"))
    return [r for r in results if r is not None]


def _run_chunks_trio(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Trio runner using a nursery."""
    try:
        import trio  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError as exc:
        raise Exception_Configuration(
            "trio is not installed; cannot use 'trio' backend. Run: pip install trio",
        ) from exc

    results: list[np.ndarray | None] = [None] * len(chunk_tensors)

    async def _run_all() -> None:
        """Start all chunk tasks in the trio nursery."""
        async with trio.open_nursery() as nursery:
            for idx_chunk, ct in enumerate(chunk_tensors):

                async def _run_one(
                    idx: int, ct_inner: np.ndarray) -> None:
                    """Run one chunk in a trio thread and store the result."""
                    results[idx] = await trio.to_thread.run_sync(
                        functools.partial(
                            compute_portfolio_paths_from_returns_tensor,
                            returns_tensor=ct_inner,
                            weights=weights,
                            initial_value=initial_value,
                        ),
                    )

                nursery.start_soon(_run_one, idx_chunk, ct)

    _run_callable_in_new_thread(callable_target = lambda: trio.run(_run_all))
    return [r for r in results if r is not None]


def _run_chunks_trio_anyio(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Anyio (trio backend) runner using task groups."""
    try:
        import anyio  # type: ignore[import-not-found]  # noqa: PLC0415
        import trio as _trio  # noqa: F401,PLC0415  # verify trio is installed
    except ImportError as exc:
        raise Exception_Configuration(
            "Both trio and anyio must be installed for 'trio + anyio' backend. "
            "Run: pip install trio anyio",
        ) from exc

    results: list[np.ndarray | None] = [None] * len(chunk_tensors)

    async def _run_all() -> None:
        """Start all chunk tasks in the anyio (trio backend) task group."""
        async with anyio.create_task_group() as tg:
            for idx_chunk, ct in enumerate(chunk_tensors):

                async def _run_one(
                    idx: int, ct_inner: np.ndarray) -> None:
                    """Run one chunk in an anyio/trio thread and store the result."""
                    results[idx] = await anyio.to_thread.run_sync(
                        functools.partial(
                            compute_portfolio_paths_from_returns_tensor,
                            returns_tensor=ct_inner,
                            weights=weights,
                            initial_value=initial_value,
                        ),
                    )

                tg.start_soon(_run_one, idx_chunk, ct)

    _run_callable_in_new_thread(callable_target = lambda: anyio.run(_run_all, backend="trio"))
    return [r for r in results if r is not None]


def _run_chunks_joblib(
    *, chunk_tensors: list[np.ndarray], weights: np.ndarray, initial_value: float) -> list[np.ndarray]:
    """Joblib thread-based parallel runner with timeout fallback.

    Uses ``prefer="threads"`` instead of loky processes so that:

    * The runner is safe on Windows (no ``if __name__ == '__main__'`` guard
      required for thread-based concurrency).
    * NumPy arrays are shared by reference — no pickling overhead and
      bit-identical results are guaranteed.

    Notes
    -----
    If the joblib call exceeds ``JOBLIB_TIMEOUT_SECONDS`` (15 s) it is
    aborted and the sequential ``_run_chunks_standard`` fallback is used.
    This prevents the UI from hanging when the OS thread scheduler is
    saturated at high scenario counts.
    """
    try:
        from joblib import (  # type: ignore[import-not-found]  # noqa: PLC0415
            Parallel,
            delayed,
            parallel_backend,
        )
    except ImportError as exc:
        raise Exception_Configuration(
            "joblib is not installed; cannot use 'joblib' backend. Run: pip install joblib",
        ) from exc

    n_jobs = min(len(chunk_tensors), max(1, (os.cpu_count() or 1) - 1))
    # Use parallel_backend context to pin the threading backend explicitly and
    # skip joblib's per-call backend-resolution heuristic, which dominates
    # elapsed time for small chunk counts typical of interactive UI workloads.
    #
    # Limit BLAS threads to 1 per joblib worker to prevent thread-explosion
    # (joblib threads x OpenMP/BLAS threads) that causes hangs at high
    # scenario counts on Windows.
    try:
        import threadpoolctl  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError:
        threadpoolctl = None  # type: ignore[misc]

    _limits_ctx = (
        threadpoolctl.threadpool_limits(limits=1, user_api="blas")
        if threadpoolctl is not None
        else contextlib.nullcontext()
    )

    JOBLIB_TIMEOUT_SECONDS: float = 15.0

    def _joblib_callable() -> list[np.ndarray]:
        """Inner callable executed in the timeout-guarded thread."""
        with _limits_ctx, parallel_backend("threading", n_jobs=n_jobs):
            return list(
                Parallel(n_jobs=n_jobs)(
                    delayed(compute_portfolio_paths_from_returns_tensor)(
                        returns_tensor=ct,
                        weights=weights,
                        initial_value=initial_value,
                    )
                    for ct in chunk_tensors
                ),
            )

    # Use a raw daemon thread with join(timeout=…) instead of
    # ThreadPoolExecutor because executor.shutdown(wait=True) would
    # itself block on the hung joblib worker, defeating the timeout.
    result_holder: dict[str, list[np.ndarray]] = {}
    error_holder: dict[str, BaseException] = {}

    def _joblib_thread_target() -> None:
        """Run joblib in this thread; capture result or exception."""
        try:
            result_holder["result"] = _joblib_callable()
        except BaseException as exc_error:  # noqa: BLE001 — re-raised below
            error_holder["error"] = exc_error

    worker_thread = threading.Thread(
        target=_joblib_thread_target,
        daemon=True,
    )
    worker_thread.start()
    worker_thread.join(timeout=JOBLIB_TIMEOUT_SECONDS)

    if worker_thread.is_alive():
        _logger.warning(
            "joblib backend timed out after %.1f s (scenarios=%d, chunks=%d, n_jobs=%d); "
            "falling back to standard sequential runner",
            JOBLIB_TIMEOUT_SECONDS,
            sum(ct.shape[1] for ct in chunk_tensors),
            len(chunk_tensors),
            n_jobs,
        )
        return _run_chunks_standard(
            chunk_tensors=chunk_tensors,
            weights=weights,
            initial_value=initial_value,
        )

    if "error" in error_holder:
        raise error_holder["error"]

    return result_holder["result"]
