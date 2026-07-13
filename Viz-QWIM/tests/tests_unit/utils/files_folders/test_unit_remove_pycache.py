"""Unit tests for remove_pycache module."""

from __future__ import annotations

import shutil
from unittest.mock import patch

import pytest


class Class_Test_Clean_Pycache:
    """Tests for clean_pycache() utility function."""

    @pytest.mark.unit()
    def Test_Removes_Pycache_Directories(self, tmp_path):
        """clean_pycache should delete all __pycache__ dirs under target_dir."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        (tmp_path / "pkg" / "__pycache__").mkdir(parents=True)
        (tmp_path / "pkg" / "__pycache__" / "mod.cpython-313.pyc").write_bytes(b"")
        (tmp_path / "sub" / "nested" / "__pycache__").mkdir(parents=True)
        (tmp_path / "sub" / "nested" / "__pycache__" / "x.pyc").write_bytes(b"")

        clean_pycache(target_dir = tmp_path)

        remaining = list(tmp_path.rglob("__pycache__"))
        assert remaining == [], f"Expected no __pycache__ dirs, found: {remaining}"

    @pytest.mark.unit()
    def Test_Accepts_String_Path(self, tmp_path):
        """clean_pycache should accept a plain string as target_dir."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "a.pyc").write_bytes(b"")

        clean_pycache(target_dir = str(tmp_path))

        assert not (tmp_path / "__pycache__").exists()

    @pytest.mark.unit()
    def Test_No_Error_When_No_Pycache_Present(self, tmp_path):
        """clean_pycache should succeed when no __pycache__ or orphan .pyc exists."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        (tmp_path / "somemodule.py").write_text("x = 1\n")
        result = clean_pycache(target_dir = tmp_path)
        assert result == []

    @pytest.mark.unit()
    def Test_Ignores_File_Named_Pycache(self, tmp_path):
        """clean_pycache should ignore a file whose name matches __pycache__."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        pycache_file = tmp_path / "pkg" / "__pycache__"
        pycache_file.parent.mkdir(parents=True)
        pycache_file.write_text("not a directory\n")

        clean_pycache(target_dir = tmp_path)

        assert pycache_file.exists()
        assert pycache_file.is_file()

    @pytest.mark.unit()
    def Test_Module_Is_Importable(self):
        """The module itself should be importable without side effects."""
        import src.utils.files_folders.remove_pycache  # noqa: F401

    @pytest.mark.unit()
    def Test_Dry_Run_Does_Not_Delete_Dirs(self, tmp_path):
        """dry_run=True logs directories but does not remove them."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        pycache = tmp_path / "pkg" / "__pycache__"
        pycache.mkdir(parents=True)
        (pycache / "mod.cpython-313.pyc").write_bytes(b"")

        removed = clean_pycache(target_dir = tmp_path, dry_run=True)

        assert pycache.exists(), "__pycache__ must not be deleted in dry-run mode"
        assert pycache in removed

    @pytest.mark.unit()
    def Test_Dry_Run_Does_Not_Delete_Orphan_Pyc(self, tmp_path):
        """dry_run=True reports orphan .pyc files but does not unlink them."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        orphan = tmp_path / "pkg" / "stale.pyc"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"")

        removed = clean_pycache(target_dir = tmp_path, dry_run=True)

        assert orphan.exists(), "orphan .pyc must not be deleted in dry-run mode"
        assert orphan in removed

    @pytest.mark.unit()
    def Test_Dry_Run_Returns_All_Candidates(self, tmp_path):
        """dry_run returns every __pycache__ directory it found."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        for sub_ in ("a", "b", "c"):
            pc = tmp_path / sub_ / "__pycache__"
            pc.mkdir(parents=True)

        removed = clean_pycache(target_dir = tmp_path, dry_run=True)

        assert len(removed) == 3

    @pytest.mark.unit()
    def Test_Parallel_Removal_With_Max_Workers(self, tmp_path):
        """Multiple __pycache__ directories are removed using max_workers > 1."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        for sub_ in ("x", "y", "z"):
            pc = tmp_path / sub_ / "__pycache__"
            pc.mkdir(parents=True)
            (pc / "dummy.pyc").write_bytes(b"")

        removed = clean_pycache(target_dir = tmp_path, dry_run=False, max_workers=3)

        assert len(removed) == 3
        for sub_ in ("x", "y", "z"):
            assert not (tmp_path / sub_ / "__pycache__").exists()

    @pytest.mark.unit()
    def Test_Returns_List_Of_Paths(self, tmp_path):
        """clean_pycache always returns a list of Path objects."""
        from pathlib import Path
        from src.utils.files_folders.remove_pycache import clean_pycache

        pc = tmp_path / "__pycache__"
        pc.mkdir()
        result = clean_pycache(target_dir = tmp_path)

        assert isinstance(result, list)
        for item_ in result:
            assert isinstance(item_, Path)

    @pytest.mark.unit()
    def Test_No_Pycache_Returns_Empty_List(self, tmp_path):
        """Returns empty list when no __pycache__ directories or orphan .pyc exist."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        result = clean_pycache(target_dir = tmp_path)
        assert result == []

    @pytest.mark.unit()
    def Test_Accepts_Target_Dirs_Sequence(self, tmp_path):
        """target_dirs keyword accepts a sequence of path-like objects."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        root_a = tmp_path / "root_a"
        root_b = tmp_path / "root_b"
        (root_a / "__pycache__").mkdir(parents=True)
        (root_b / "__pycache__").mkdir(parents=True)

        removed = clean_pycache(target_dirs=[root_a, root_b])

        assert len(removed) == 2
        assert not (root_a / "__pycache__").exists()
        assert not (root_b / "__pycache__").exists()

    @pytest.mark.unit()
    def Test_Cleans_Multiple_Roots(self, tmp_path):
        """Removes items found in all supplied root directories."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        root1 = tmp_path / "proj1"
        root2 = tmp_path / "proj2"
        (root1 / "pkg" / "__pycache__").mkdir(parents=True)
        orphan = root2 / "stale.pyc"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"")

        removed = clean_pycache(target_dirs=[str(root1), str(root2)])

        assert not (root1 / "pkg" / "__pycache__").exists()
        assert not orphan.exists()
        assert len(removed) == 2

    @pytest.mark.unit()
    def Test_Raises_When_Both_Given(self, tmp_path):
        """ValueError is raised when both target_dir and target_dirs are supplied."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="not both"):
            clean_pycache(target_dir=tmp_path, target_dirs=[tmp_path])

    @pytest.mark.unit()
    def Test_Raises_When_Neither_Given(self):
        """ValueError is raised when neither target_dir nor target_dirs is supplied."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="must be supplied"):
            clean_pycache()

    @pytest.mark.unit()
    def Test_Raises_For_Empty_Target_Dirs(self):
        """Empty target_dirs sequences must be rejected explicitly."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="must contain at least one path"):
            clean_pycache(target_dirs=[])

    @pytest.mark.unit()
    def Test_Raises_For_Missing_Target_Directory(self, tmp_path):
        """Missing root directories must raise FileNotFoundError."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        missing_root = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError, match="Target directory not found"):
            clean_pycache(target_dir = missing_root)

    @pytest.mark.unit()
    def Test_Raises_For_File_Target(self, tmp_path):
        """File targets must raise NotADirectoryError instead of scanning silently."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        file_target = tmp_path / "module.py"
        file_target.write_text("x = 1\n", encoding="utf-8")

        with pytest.raises(NotADirectoryError, match="not a directory"):
            clean_pycache(target_dir = file_target)

    @pytest.mark.unit()
    def Test_Raises_For_Invalid_Max_Workers(self, tmp_path):
        """Non-positive worker counts must be rejected before executor creation."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="positive integer"):
            clean_pycache(target_dir = tmp_path, max_workers=0)

    @pytest.mark.unit()
    def Test_Raises_For_Boolean_Max_Workers(self, tmp_path):
        """Boolean max_workers values must not pass integer validation."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        with pytest.raises(ValueError, match="positive integer"):
            clean_pycache(target_dir = tmp_path, max_workers=False)

    @pytest.mark.unit()
    def Test_Orphan_Pyc_Files_Deleted(self, tmp_path):
        """.pyc files outside a __pycache__ dir are treated as orphans and removed."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        orphan = tmp_path / "pkg" / "legacy_module.pyc"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"\x00")

        removed = clean_pycache(target_dir = tmp_path)

        assert not orphan.exists()
        assert orphan in removed

    @pytest.mark.unit()
    def Test_Pyc_Inside_Pycache_Not_Listed_Separately(self, tmp_path):
        """.pyc files inside __pycache__ are deleted with the dir, not listed alone."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        pycache_dir = tmp_path / "pkg" / "__pycache__"
        pycache_dir.mkdir(parents=True)
        inner_pyc = pycache_dir / "mod.cpython-313.pyc"
        inner_pyc.write_bytes(b"")

        removed = clean_pycache(target_dir = tmp_path)

        # The __pycache__ dir itself must be in the list
        assert pycache_dir in removed
        # The .pyc file inside it must NOT be listed separately
        assert inner_pyc not in removed

    @pytest.mark.unit()
    def Test_Combined_Dirs_And_Orphan_Pyc(self, tmp_path):
        """Both __pycache__ dirs and orphan .pyc files appear in the return list."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        pycache_dir = tmp_path / "pkg" / "__pycache__"
        pycache_dir.mkdir(parents=True)
        orphan = tmp_path / "stale.pyc"
        orphan.write_bytes(b"")

        removed = clean_pycache(target_dir = tmp_path)

        assert pycache_dir in removed
        assert orphan in removed
        assert len(removed) == 2

    @pytest.mark.unit()
    def Test_Error_During_Removal_Is_Handled(self, tmp_path):
        """If rmtree raises, the error is logged and function completes without raising."""
        from src.utils.files_folders.remove_pycache import clean_pycache

        pycache_dir = tmp_path / "pkg" / "__pycache__"
        pycache_dir.mkdir(parents=True)

        with patch("src.utils.files_folders.remove_pycache.shutil.rmtree", side_effect=OSError("Permission denied")):
            removed = clean_pycache(target_dir = tmp_path)

        # No item in removed since rmtree failed
        assert removed == []


class Class_Test_Main_CLI:
    """Tests for main() CLI entry-point."""

    @pytest.mark.unit()
    def Test_Returns_Zero_On_Success(self, tmp_path):
        """main() always returns 0."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path)]):
            with patch("src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]):
                result = main()

        assert result == 0

    @pytest.mark.unit()
    def Test_Default_Targets_Are_Src_And_Tests(self):
        """When no positional args given, main uses ['src', 'tests'] as targets."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py"]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]
            ) as mock_clean:
                main()

        call_kwargs = mock_clean.call_args.kwargs
        assert call_kwargs["target_dirs"] == ["src", "tests"]

    @pytest.mark.unit()
    def Test_Custom_Single_Target(self, tmp_path):
        """Explicit single target is forwarded as a one-element target_dirs list."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path)]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]
            ) as mock_clean:
                main()

        call_kwargs = mock_clean.call_args.kwargs
        assert call_kwargs["target_dirs"] == [str(tmp_path)]

    @pytest.mark.unit()
    def Test_Custom_Multiple_Targets(self, tmp_path):
        """Multiple explicit targets are forwarded together."""
        from src.utils.files_folders.remove_pycache import main

        root_a = str(tmp_path / "a")
        root_b = str(tmp_path / "b")
        with patch("sys.argv", ["remove_pycache.py", root_a, root_b]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]
            ) as mock_clean:
                main()

        call_kwargs = mock_clean.call_args.kwargs
        assert call_kwargs["target_dirs"] == [root_a, root_b]

    @pytest.mark.unit()
    def Test_Dry_Run_Flag(self, tmp_path):
        """--dry-run flag sets dry_run=True in the clean_pycache call."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path), "--dry-run"]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]
            ) as mock_clean:
                main()

        call_kwargs = mock_clean.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.unit()
    def Test_Workers_Arg(self, tmp_path):
        """--workers N sets max_workers=N in the clean_pycache call."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path), "--workers", "2"]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache", return_value=[]
            ) as mock_clean:
                main()

        call_kwargs = mock_clean.call_args.kwargs
        assert call_kwargs["max_workers"] == 2

    @pytest.mark.unit()
    def Test_Returns_One_On_Invalid_Input(self, tmp_path):
        """main() returns 1 when clean_pycache raises a validation error."""
        from src.utils.files_folders.remove_pycache import main

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path)]):
            with patch(
                "src.utils.files_folders.remove_pycache.clean_pycache",
                side_effect=FileNotFoundError("Target directory not found"),
            ):
                result = main()

        assert result == 1


class Class_Test_Files_Folders_Init:
    """Smoke tests for files_folders __init__."""

    @pytest.mark.unit()
    def Test_Package_Is_Importable(self):
        """src.utils.files_folders package should be importable."""
        import src.utils.files_folders  # noqa: F401
