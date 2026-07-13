"""Focused integration tests for selective project-copy utilities."""

from __future__ import annotations

from pathlib import Path

import pytest


def _write_text_file_QWIM(
    file_path: Path,
    content: str,
) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def _write_binary_file_QWIM(
    file_path: Path,
    content: bytes = b"placeholder",
) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)


def _create_sample_project_root_QWIM(
    project_root: Path,
) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)

    _write_text_file_QWIM(project_root / "app.py", "# app.py\n")
    _write_text_file_QWIM(project_root / "main.py", "# main.py\n")
    _write_text_file_QWIM(project_root / "requirements.txt", "# requirements\n")
    _write_text_file_QWIM(project_root / "pyproject.toml", "[project]\nname = 'sample'\n")
    _write_text_file_QWIM(project_root / "properdocs.yml", "site_name: Sample\n")
    _write_text_file_QWIM(project_root / "pytest.ini", "[pytest]\n")
    _write_text_file_QWIM(project_root / "behave.ini", "[behave]\n")

    _write_text_file_QWIM(project_root / ".github" / "workflows" / "ci.yml", "name: ci\n")
    _write_text_file_QWIM(project_root / "GHCP-Plans" / "plan.md", "# plan\n")
    _write_text_file_QWIM(project_root / "src" / "package" / "module.py", "value_module = 1\n")
    _write_text_file_QWIM(project_root / "src" / "package" / "notes.md", "skip\n")
    _write_text_file_QWIM(
        project_root / "src" / "dashboard" / "reporting" / "report_QWIM.typ",
        "#let report_QWIM = (config) => {}\n",
    )
    _write_text_file_QWIM(
        project_root / "src" / "dashboard" / "reporting" / "utils_table.typ",
        "#let utils_table = (rows) => {}\n",
    )
    _write_binary_file_QWIM(project_root / "tests" / "data" / "sample.parquet")
    _write_text_file_QWIM(project_root / "tests" / "data" / "sample.txt", "skip\n")
    _write_text_file_QWIM(project_root / "tests" / "unit" / "test_example.py", "def test_example():\n    assert True\n")
    _write_text_file_QWIM(project_root / "inputs" / "config.json", '{"mode": "demo"}\n')
    _write_text_file_QWIM(project_root / "docs" / "index.md", "# docs\n")
    _write_binary_file_QWIM(project_root / "docs" / "assets" / "logo.png")
    _write_text_file_QWIM(project_root / "inputs" / "pycache" / "skip.json", "skip\n")
    _write_text_file_QWIM(project_root / "docs" / "pycache" / "skip.md", "skip\n")

    return project_root


class Class_Test_Copy_Folders_Integration_QWIM:
    """End-to-end filesystem tests for project-copy bundles."""

    @pytest.mark.integration()
    def Test_Copy_Content_My_Projects_Creates_Expected_Project_Slice(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        from src.utils.files_folders.copy_folders import copy_content_my_projects_QWIM

        source_project = _create_sample_project_root_QWIM(tmp_path / "source_project")
        target_project = tmp_path / "target_project"
        target_project.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            "src.utils.files_folders.copy_folders._show_message_QWIM",
            lambda message_text, *, title, message_kind="info": None,
        )

        copied_paths = copy_content_my_projects_QWIM(
            target_dir=target_project,
            source_root=source_project,
        )

        copied_relative_paths = {
            item_path.relative_to(target_project).as_posix()
            for item_path in copied_paths
        }

        assert copied_relative_paths == {
            ".github/workflows/ci.yml",
            "GHCP-Plans/plan.md",
            "app.py",
            "behave.ini",
            "docs/assets/logo.png",
            "docs/index.md",
            "inputs/config.json",
            "properdocs.yml",
            "pyproject.toml",
            "requirements.txt",
            "src/dashboard/reporting/report_QWIM.typ",
            "src/dashboard/reporting/utils_table.typ",
            "src/package/module.py",
            "tests/data/sample.parquet",
            "tests/unit/test_example.py",
        }
        assert not (target_project / "src" / "package" / "notes.md").exists()
        assert not (target_project / "tests" / "data" / "sample.txt").exists()
        assert not (target_project / "docs" / "pycache").exists()
        assert not (target_project / "inputs" / "pycache").exists()