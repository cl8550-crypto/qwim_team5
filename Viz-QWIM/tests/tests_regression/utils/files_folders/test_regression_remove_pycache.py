"""Regression tests for remove_pycache validation messages.

These baselines lock in the explicit validation messages and CLI return-code
behavior so later refactors do not drift back to silent no-op scans or raw
executor errors.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.utils.files_folders.remove_pycache import clean_pycache, main


class Class_Test_Regression_Remove_Pycache:
    """Regression baselines for remove_pycache validation."""

    @pytest.mark.regression()
    def Test_Missing_Target_Message_Baseline(self, tmp_path) -> None:
        """Missing-target validation message must remain stable."""
        missing_root = (tmp_path / "missing_root").resolve()

        with pytest.raises(FileNotFoundError) as exc_info:
            clean_pycache(target_dir = missing_root)

        assert str(exc_info.value) == f"Target directory not found: {missing_root}"

    @pytest.mark.regression()
    def Test_Empty_Target_Dirs_Message_Baseline(self) -> None:
        """Empty target_dirs validation message must remain stable."""
        with pytest.raises(ValueError) as exc_info:
            clean_pycache(target_dirs=[])

        assert str(exc_info.value) == "'target_dirs' must contain at least one path."

    @pytest.mark.regression()
    def Test_Invalid_Worker_Message_And_Cli_Code_Baseline(self, tmp_path) -> None:
        """Invalid worker validation and CLI exit code must remain stable."""
        with pytest.raises(ValueError) as exc_info:
            clean_pycache(target_dir = tmp_path, max_workers=0)

        assert str(exc_info.value) == "'max_workers' must be a positive integer."

        with patch("sys.argv", ["remove_pycache.py", str(tmp_path), "--workers", "0"]):
            assert main() == 1