"""Integration tests for remove_pycache utilities."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.utils.files_folders.remove_pycache import clean_pycache, main


class Class_Test_Integration_Remove_Pycache:
    """Integration tests for real remove_pycache filesystem behavior."""

    @pytest.mark.integration()
    def Test_Cleans_Multiple_Real_Roots(self, tmp_path) -> None:
        """clean_pycache removes both __pycache__ dirs and orphan .pyc files across roots."""
        root_a = tmp_path / "root_a"
        root_b = tmp_path / "root_b"
        pycache_dir = root_a / "pkg" / "__pycache__"
        orphan_pyc = root_b / "legacy.pyc"
        pycache_dir.mkdir(parents=True)
        (pycache_dir / "module.pyc").write_bytes(b"")
        orphan_pyc.parent.mkdir(parents=True)
        orphan_pyc.write_bytes(b"")

        removed = clean_pycache(target_dirs=[root_a, root_b], max_workers=2)

        assert pycache_dir in removed
        assert orphan_pyc in removed
        assert not pycache_dir.exists()
        assert not orphan_pyc.exists()

    @pytest.mark.integration()
    def Test_Missing_Target_Raises_File_Not_Found(self, tmp_path) -> None:
        """Missing root directories must raise FileNotFoundError."""
        missing_root = tmp_path / "missing_root"

        with pytest.raises(FileNotFoundError, match="Target directory not found"):
            clean_pycache(target_dir = missing_root)

    @pytest.mark.integration()
    def Test_Main_Returns_One_For_Invalid_Target(self, tmp_path) -> None:
        """CLI main() returns 1 instead of raising on invalid targets."""
        missing_root = tmp_path / "missing_root"

        with patch("sys.argv", ["remove_pycache.py", str(missing_root)]):
            result = main()

        assert result == 1