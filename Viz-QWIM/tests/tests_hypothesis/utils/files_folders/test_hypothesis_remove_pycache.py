"""Hypothesis (property-based) tests for remove_pycache module.

Tests cover pure-function invariants for ``clean_pycache``:
- dry_run=True always returns a list (never deletes)
- Output is always a list of Path objects
- Multiple target_dirs consolidates results
- Mutually-exclusive argument validation raises ValueError
- Both-absent raises ValueError

Key invariants tested:
- Return type is always ``list[Path]``
- ``dry_run=True`` returns candidates without deleting them
- ``max_workers`` accepted as positive int (no crash)
- Providing both ``target_dir`` and ``target_dirs`` raises ``ValueError``
- Providing neither raises ``ValueError``
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from hypothesis import assume, given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Clean_Pycache_Dry_Run
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Clean_Pycache_Dry_Run:
    """Property-based tests for clean_pycache with dry_run=True."""

    @pytest.mark.unit()
    @given(num_pycache=st.integers(min_value=0, max_value=3))
    @settings(max_examples=30)
    def Test_dry_run_returns_list(self, tmp_path: Path, num_pycache: int) -> None:
        """dry_run=True always returns a list regardless of how many __pycache__ dirs exist."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        for idx in range(num_pycache):
            pkg = tmp_path / f"pkg_{idx}" / "__pycache__"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / f"mod_{idx}.cpython-313.pyc").write_bytes(b"")

        result = clean_pycache(target_dir = tmp_path, dry_run=True)

        assert isinstance(result, list)

    @pytest.mark.unit()
    @given(num_pycache=st.integers(min_value=1, max_value=3))
    @settings(max_examples=30)
    def Test_dry_run_does_not_delete(self, tmp_path: Path, num_pycache: int) -> None:
        """dry_run=True leaves all __pycache__ dirs intact."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        dirs: list[Path] = []
        for idx in range(num_pycache):
            pkg = tmp_path / f"pkg_{idx}" / "__pycache__"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / f"mod_{idx}.cpython-313.pyc").write_bytes(b"")
            dirs.append(pkg)

        clean_pycache(target_dir = tmp_path, dry_run=True)

        for d in dirs:
            assert d.exists(), f"__pycache__ dir was deleted in dry-run: {d}"

    @pytest.mark.unit()
    @given(num_pycache=st.integers(min_value=1, max_value=3))
    @settings(max_examples=30)
    def Test_dry_run_returns_candidate_paths(self, num_pycache: int) -> None:
        """dry_run=True returns the paths it would have removed."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        tmp = Path(tempfile.mkdtemp())
        for idx in range(num_pycache):
            pkg = tmp / f"pkg_{idx}" / "__pycache__"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "mod.pyc").write_bytes(b"")

        result = clean_pycache(target_dir = tmp, dry_run=True)

        assert len(result) == num_pycache
        for item in result:
            assert isinstance(item, Path)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Clean_Pycache_Real_Run
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Clean_Pycache_Real_Run:
    """Property-based tests for clean_pycache with actual deletion."""

    @pytest.mark.unit()
    @given(num_pycache=st.integers(min_value=0, max_value=3))
    @settings(max_examples=30)
    def Test_real_run_returns_list_of_paths(self, num_pycache: int) -> None:
        """Real run always returns a list of Path objects."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        tmp = Path(tempfile.mkdtemp())
        for idx in range(num_pycache):
            pkg = tmp / f"pkg_{idx}" / "__pycache__"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "mod.pyc").write_bytes(b"")

        result = clean_pycache(target_dir = tmp)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, Path)

    @pytest.mark.unit()
    @given(num_pycache=st.integers(min_value=1, max_value=3))
    @settings(max_examples=30)
    def Test_real_run_removes_pycache(self, num_pycache: int) -> None:
        """Real run removes __pycache__ directories."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        tmp = Path(tempfile.mkdtemp())
        for idx in range(num_pycache):
            pkg = tmp / f"pkg_{idx}" / "__pycache__"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "mod.pyc").write_bytes(b"")

        clean_pycache(target_dir = tmp)

        remaining = list(tmp.rglob("__pycache__"))
        assert remaining == [], f"Expected all __pycache__ removed, found: {remaining}"

    @pytest.mark.unit()
    @given(max_workers=st.integers(min_value=1, max_value=8))
    @settings(max_examples=20)
    def Test_accepts_max_workers_param(self, tmp_path: Path, max_workers: int) -> None:
        """clean_pycache accepts any positive max_workers without error."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        result = clean_pycache(target_dir = tmp_path, max_workers=max_workers)

        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Class_Test_Hypothesis_Clean_Pycache_Multiple_Dirs
# ---------------------------------------------------------------------------


class Class_Test_Hypothesis_Clean_Pycache_Multiple_Dirs:
    """Property-based tests for clean_pycache with target_dirs."""

    @pytest.mark.unit()
    @given(num_roots=st.integers(min_value=1, max_value=3))
    @settings(max_examples=20)
    def Test_target_dirs_accepts_multiple_roots(self, num_roots: int) -> None:
        """target_dirs keyword arg accepts a list of paths without error."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        roots: list[Path] = []
        for idx in range(num_roots):
            tmp = Path(tempfile.mkdtemp())
            (tmp / "__pycache__").mkdir()
            (tmp / "__pycache__" / "x.pyc").write_bytes(b"")
            roots.append(tmp)

        result = clean_pycache(target_dirs=roots, dry_run=True)

        assert isinstance(result, list)
        assert len(result) == num_roots

    @pytest.mark.unit()
    def Test_both_target_dir_and_target_dirs_raises(self) -> None:
        """Providing both target_dir and target_dirs raises ValueError."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        tmp = Path(tempfile.mkdtemp())

        with pytest.raises(ValueError, match="not both"):
            clean_pycache(target_dir=tmp, target_dirs=[tmp])

    @pytest.mark.unit()
    def Test_neither_target_raises(self) -> None:
        """Providing neither target_dir nor target_dirs raises ValueError."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="must be supplied"):
            clean_pycache()


class Class_Test_Hypothesis_Clean_Pycache_Validation:
    """Property-based validation tests for clean_pycache."""

    @pytest.mark.unit()
    @given(max_workers=st.integers(max_value=0))
    @settings(max_examples=20)
    def Test_invalid_max_workers_raise_value_error(
        self,
        tmp_path: Path,
        max_workers: int,
    ) -> None:
        """Non-positive worker counts must always raise ValueError."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="positive integer"):
            clean_pycache(target_dir = tmp_path, max_workers=max_workers)

    @pytest.mark.unit()
    @given(name=st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True))
    @settings(max_examples=20)
    def Test_missing_target_root_raises_file_not_found(
        self,
        tmp_path: Path,
        name: str,
    ) -> None:
        """Missing root directories must always raise FileNotFoundError."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        missing_root = tmp_path / f"{name}_missing"

        with pytest.raises(FileNotFoundError, match="Target directory not found"):
            clean_pycache(target_dir = missing_root)
