"""Utility script for removing Python bytecode cache directories.

This module provides a helper function and a CLI entry-point for
recursively deleting ``__pycache__`` directories and orphan ``.pyc`` files
from one or more project trees, keeping the repository clean between runs.

Uses ``concurrent.futures.ThreadPoolExecutor`` for parallel removal when
multiple items are found, which speeds up large projects with many packages.

Functions
---------
clean_pycache
    Recursively remove all ``__pycache__`` directories and orphan ``.pyc``
    files under one or more root directories.
main
    CLI entry-point with ``--dry-run`` and ``--workers`` options.
"""

from __future__ import annotations

import argparse
import shutil
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def _validate_max_workers_QWIM(*, max_workers: int) -> None:
    """Validate the worker-count configuration.

    Parameters
    ----------
    max_workers : int
        Maximum number of worker threads requested by the caller.

    Raises
    ------
    ValueError
        If *max_workers* is not a positive integer.
    """
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
        raise ValueError("'max_workers' must be a positive integer.")


def _resolve_target_roots_QWIM(
    *, target_dir: str | Path | None, target_dirs: Sequence[str | Path] | None) -> list[Path]:
    """Resolve and validate target directories for pycache cleanup.

    Parameters
    ----------
    target_dir : str | pathlib.Path | None
        Optional single root directory.
    target_dirs : collections.abc.Sequence[str | pathlib.Path] | None
        Optional sequence of root directories.

    Returns
    -------
    list[pathlib.Path]
        Resolved root directories.

    Raises
    ------
    ValueError
        If both target styles are supplied, if neither is supplied, or if the
        target sequence is empty.
    FileNotFoundError
        If any resolved target directory does not exist.
    NotADirectoryError
        If any resolved target path is not a directory.
    """
    if target_dir is not None and target_dirs is not None:
        raise ValueError(
            "Provide either 'target_dir' (single path) or 'target_dirs' "
            "(sequence of paths), not both.",
        )

    if target_dir is None and target_dirs is None:
        raise ValueError("One of 'target_dir' or 'target_dirs' must be supplied.")

    raw_roots = [target_dir] if target_dir is not None else list(target_dirs or [])
    if not raw_roots:
        raise ValueError("'target_dirs' must contain at least one path.")

    roots: list[Path] = []
    for raw_root in raw_roots:
        resolved_root = Path(raw_root).resolve()
        if not resolved_root.exists():
            raise FileNotFoundError(f"Target directory not found: {resolved_root}")
        if not resolved_root.is_dir():
            raise NotADirectoryError(
                f"Target path is not a directory: {resolved_root}",
            )
        roots.append(resolved_root)

    return roots


def clean_pycache(
    *, target_dir: str | Path | None = None, dry_run: bool = False, max_workers: int = 4, target_dirs: Sequence[str | Path] | None = None) -> list[Path]:
    """Recursively remove all ``__pycache__`` directories and orphan ``.pyc`` files under one or more root directories.

    Either *target_dir* (single root) or *target_dirs* (multiple roots)
    must be supplied — not both, not neither.

    Uses a ``ThreadPoolExecutor`` to delete multiple items in parallel,
    which is beneficial for large projects with hundreds of packages.

    Parameters
    ----------
    target_dir : str or Path, optional
        Single root directory from which to begin the recursive search.
        Relative paths are resolved against the current working directory.
        Mutually exclusive with *target_dirs*.
    dry_run : bool
        If ``True``, log what would be deleted without actually removing
        anything.  Defaults to ``False``.
    max_workers : int
        Maximum number of worker threads for parallel deletion.
        Defaults to ``4``.
    target_dirs : sequence of str or Path, keyword-only, optional
        Multiple root directories to clean in one call.  Each path is
        resolved before scanning.  Mutually exclusive with *target_dir*.

    Returns
    -------
    list[Path]
        Sorted flat list of ``__pycache__`` directories and orphan ``.pyc``
        files that were (or, in dry-run mode, would be) removed.

    Raises
    ------
    ValueError
        If both *target_dir* and *target_dirs* are supplied, if neither is
        supplied, if *target_dirs* is empty, or if *max_workers* is invalid.
    FileNotFoundError
        If any requested root directory does not exist.
    NotADirectoryError
        If any requested target path is not a directory.

    Notes
    -----
    ``.pyc`` files that reside *inside* a ``__pycache__`` directory are
    deleted implicitly when the directory is removed via :func:`shutil.rmtree`.
    Only ``.pyc`` files whose immediate parent is **not** named
    ``__pycache__`` ("orphan" files) are collected and removed separately.

    Examples
    --------
    >>> removed = clean_pycache("src", dry_run=True)
    >>> # logs each item that would be removed; nothing is deleted
    >>> removed = clean_pycache(target_dirs=["src", "tests"], dry_run=True)
    """
    _validate_max_workers_QWIM(max_workers = max_workers)
    roots = _resolve_target_roots_QWIM(target_dir = target_dir, target_dirs = target_dirs)

    pycache_dirs: list[Path] = []
    orphan_pyc: list[Path] = []
    for item_root in roots:
        pycache_dirs.extend(
            sorted(item_path for item_path in item_root.rglob("__pycache__") if item_path.is_dir()),
        )
        orphan_pyc.extend(
            sorted(
                item_path
                for item_path in item_root.rglob("*.pyc")
                if item_path.is_file() and item_path.parent.name != "__pycache__"
            ),
        )

    candidates: list[Path] = sorted(set(pycache_dirs) | set(orphan_pyc))
    root_labels = ", ".join(str(item_root) for item_root in roots)

    if not candidates:
        _logger.info(  # noqa: PLE1205  # false positive: loguru-style logger
            "No __pycache__ directories or orphan .pyc files found under {}",
            root_labels,
        )
        return []

    if dry_run:
        _logger.info(  # noqa: PLE1205  # false positive: loguru-style logger
            "[dry-run] Would remove {} item(s) under {}:",
            len(candidates),
            root_labels,
        )
        for item_path in candidates:
            _logger.info("  {}", item_path)  # noqa: PLE1205  # false positive: loguru-style logger
        return candidates

    removed: list[Path] = []
    errors: list[tuple[Path, Exception]] = []

    def _remove(item_path: Path) -> Path:
        if item_path.is_dir():
            shutil.rmtree(item_path)
        else:
            item_path.unlink()
        return item_path

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_remove, item_path): item_path for item_path in candidates}
        for item_future in as_completed(futures):
            item_path = futures[item_future]
            try:
                item_future.result()
                removed.append(item_path)
                _logger.info("Removed: {}", item_path)  # noqa: PLE1205  # false positive: loguru-style logger
            except OSError as exc:
                errors.append((item_path, exc))
                _logger.warning("Error removing {}: {}", item_path, exc)  # noqa: PLE1205  # false positive: loguru-style logger

    if errors:
        _logger.warning(  # noqa: PLE1205  # false positive: loguru-style logger
            "{} error(s) occurred; {} item(s) removed.",
            len(errors),
            len(removed),
        )
    else:
        _logger.info("Done. {} item(s) removed.", len(removed))  # noqa: PLE1205  # false positive: loguru-style logger

    return sorted(removed)


def main() -> int:
    """CLI entry-point for the pycache cleaner.

    Scans one or more root directories for ``__pycache__`` directories and
    orphan ``.pyc`` files and removes them.  When no positional argument is
    provided the default roots ``src`` and ``tests`` are used.

    Returns
    -------
    int
        Exit code: ``0`` on success, ``1`` when input validation fails.
    """
    parser = argparse.ArgumentParser(
        description="Recursively remove __pycache__ directories and orphan .pyc files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="*",
        metavar="DIR",
        help="Root directories to scan. Defaults to 'src' and 'tests' when omitted.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be deleted without removing anything.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="Number of parallel worker threads.",
    )
    args = parser.parse_args()

    targets: list[str] = args.target or ["src", "tests"]

    try:
        removed = clean_pycache(
            target_dirs=targets,
            dry_run=args.dry_run,
            max_workers=args.workers,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as input_error:
        _logger.error("{}", input_error)  # noqa: PLE1205  # false positive: loguru-style logger
        return 1

    _ = removed  # side-effects handled by logger inside clean_pycache
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
