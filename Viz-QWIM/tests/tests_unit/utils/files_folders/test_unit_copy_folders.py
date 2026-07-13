"""Unit tests for selective project-copy utilities."""

from __future__ import annotations

import sys
import types

from pathlib import Path

import pytest

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Not_Found,
    Exception_Security_Violation,
    Exception_Validation_Input,
)


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
    _write_text_file_QWIM(project_root / "src" / "package" / "UPPER.PY", "value_upper = 2\n")
    _write_text_file_QWIM(project_root / "src" / "package" / "notes.md", "ignore me\n")
    _write_text_file_QWIM(project_root / "src" / "package" / "pycache" / "ignored.py", "skip\n")
    _write_binary_file_QWIM(project_root / "src" / "package" / "__pycache__" / "ignored.pyc")

    _write_text_file_QWIM(
        project_root / "src" / "dashboard" / "reporting" / "report_QWIM.typ",
        "#let report_QWIM = (config) => {}\n",
    )
    _write_text_file_QWIM(
        project_root / "src" / "dashboard" / "reporting" / "utils_table.typ",
        "#let utils_table = (rows) => {}\n",
    )
    _write_text_file_QWIM(
        project_root / "src" / "dashboard" / "reporting" / "README.md",
        "skip me\n",
    )

    _write_text_file_QWIM(project_root / "tests" / "unit" / "test_example.py", "def test_example():\n    assert True\n")
    _write_binary_file_QWIM(project_root / "tests" / "data" / "sample.parquet")
    _write_text_file_QWIM(project_root / "tests" / "data" / "sample.txt", "skip\n")
    _write_binary_file_QWIM(project_root / "tests" / "pycache" / "skip.parquet")

    _write_text_file_QWIM(project_root / "inputs" / "config.json", '{"mode": "demo"}\n')
    _write_text_file_QWIM(project_root / "inputs" / "notes.txt", "keep me\n")
    _write_text_file_QWIM(project_root / "inputs" / "pycache" / "skip.json", "skip\n")

    _write_text_file_QWIM(project_root / "docs" / "index.md", "# docs\n")
    _write_binary_file_QWIM(project_root / "docs" / "assets" / "logo.png")
    _write_text_file_QWIM(project_root / "docs" / "pycache" / "skip.md", "skip\n")

    return project_root


def _patch_show_message_QWIM(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, str, str]]:
    import src.utils.files_folders.copy_folders as copy_folders

    captured_messages: list[tuple[str, str, str]] = []

    def _show_message(
        message_text: str,
        *,
        title: str,
        message_kind: str = "info",
    ) -> None:
        captured_messages.append((title, message_kind, message_text))

    monkeypatch.setattr(copy_folders, "_show_message_QWIM", _show_message)
    return captured_messages


def _install_fake_tkinter_QWIM(
    monkeypatch: pytest.MonkeyPatch,
    *,
    selected_directory: str = "",
    ask_yes_no_response: bool = True,
    raise_tcl_error: bool = False,
    auto_invoke_button_text: str | None = None,
) -> dict[str, object]:
    captured: dict[str, object] = {
        "askdirectory_kwargs": None,
        "button_texts": [],
        "button_commands": {},
        "mainloop_called": False,
        "showinfo": [],
        "showwarning": [],
        "askyesno": [],
        "destroy_called": False,
        "window_title": None,
    }

    fake_tkinter_module = types.ModuleType("tkinter")

    class Fake_Tcl_Error(Exception):
        pass

    class Fake_Root_Window:
        def withdraw(self) -> None:
            return None

        def attributes(self, *_args: object) -> None:
            return None

        def title(self, title_text: str) -> None:
            captured["window_title"] = title_text

        def resizable(self, *_args: object) -> None:
            return None

        def mainloop(self) -> None:
            captured["mainloop_called"] = True
            if auto_invoke_button_text is None:
                return None
            button_command = captured["button_commands"].get(auto_invoke_button_text)
            if button_command is not None:
                button_command()
            return None

        def destroy(self) -> None:
            captured["destroy_called"] = True

    class Fake_Label:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        def pack(self, *_args: object, **_kwargs: object) -> None:
            return None

    class Fake_Button:
        def __init__(self, *_args: object, **kwargs: object) -> None:
            button_text = str(kwargs.get("text", ""))
            button_command = kwargs.get("command")
            captured["button_texts"].append(button_text)
            if callable(button_command):
                captured["button_commands"][button_text] = button_command

        def pack(self, *_args: object, **_kwargs: object) -> None:
            return None

    def _build_root_window() -> Fake_Root_Window:
        if raise_tcl_error:
            raise Fake_Tcl_Error("tk unavailable")
        return Fake_Root_Window()

    fake_filedialog_module = types.ModuleType("tkinter.filedialog")
    fake_messagebox_module = types.ModuleType("tkinter.messagebox")

    def _askdirectory(**kwargs: object) -> str:
        captured["askdirectory_kwargs"] = kwargs
        return selected_directory

    def _showinfo(title: str, message: str) -> None:
        captured["showinfo"].append((title, message))

    def _showwarning(title: str, message: str) -> None:
        captured["showwarning"].append((title, message))

    def _askyesno(title: str, message: str) -> bool:
        captured["askyesno"].append((title, message))
        return ask_yes_no_response

    fake_tkinter_module.Tk = _build_root_window
    fake_tkinter_module.TclError = Fake_Tcl_Error
    fake_tkinter_module.filedialog = fake_filedialog_module
    fake_tkinter_module.messagebox = fake_messagebox_module

    fake_filedialog_module.askdirectory = _askdirectory
    fake_messagebox_module.showinfo = _showinfo
    fake_messagebox_module.showwarning = _showwarning
    fake_messagebox_module.askyesno = _askyesno
    fake_tkinter_module.Button = Fake_Button
    fake_tkinter_module.Label = Fake_Label

    monkeypatch.setitem(sys.modules, "tkinter", fake_tkinter_module)
    monkeypatch.setitem(sys.modules, "tkinter.filedialog", fake_filedialog_module)
    monkeypatch.setitem(sys.modules, "tkinter.messagebox", fake_messagebox_module)

    return captured


@pytest.fixture()
def fixture_source_project_QWIM(
    tmp_path: Path,
) -> Path:
    return _create_sample_project_root_QWIM(tmp_path / "source_project")


@pytest.fixture()
def fixture_target_project_QWIM(
    tmp_path: Path,
) -> Path:
    target_project = tmp_path / "target_project"
    target_project.mkdir(parents=True, exist_ok=True)
    return target_project


class Class_Test_Tkinter_Dialog_Wrappers_QWIM:
    """Tests for the thin tkinter wrapper helpers."""

    @pytest.mark.unit()
    def Test_Select_Target_Directory_Returns_Selected_Path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured = _install_fake_tkinter_QWIM(
            monkeypatch,
            selected_directory=str(tmp_path),
        )

        selected_directory = copy_folders._select_target_directory_QWIM()

        assert selected_directory == str(tmp_path)
        assert captured["askdirectory_kwargs"] == {
            "mustexist": True,
            "title": "Select the target project folder",
        }
        assert captured["destroy_called"] is True

    @pytest.mark.unit()
    def Test_Show_Message_Uses_Warning_Channel(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured = _install_fake_tkinter_QWIM(monkeypatch)

        copy_folders._show_message_QWIM(
            message_text = "warning message",
            title="Warning title",
            message_kind="warning",
        )

        assert captured["showwarning"] == [("Warning title", "warning message")]
        assert captured["showinfo"] == []

    @pytest.mark.unit()
    def Test_Ask_Yes_No_Returns_Boolean(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured = _install_fake_tkinter_QWIM(
            monkeypatch,
            ask_yes_no_response=False,
        )

        result = copy_folders._ask_yes_no_QWIM(
            message_text = "overwrite?",
            title="Confirm",
        )

        assert result is False
        assert captured["askyesno"] == [("Confirm", "overwrite?")]

    @pytest.mark.unit()
    def Test_Run_Tkinter_Dialog_Raises_Configuration_On_Tcl_Error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        _install_fake_tkinter_QWIM(monkeypatch, raise_tcl_error=True)

        with pytest.raises(Exception_Configuration, match="tkinter"):
            copy_folders._show_message_QWIM(
                message_text = "cannot show",
                title="Failure",
            )


class Class_Test_Copy_Content_Student_Projects_QWIM:
    """Tests for the student-project copy bundle."""

    @pytest.mark.unit()
    def Test_Copies_Allowed_Files_And_Excludes_Pycache(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_messages = _patch_show_message_QWIM(monkeypatch)

        def _unexpected_overwrite_prompt(
            message_text: str,
            *,
            title: str,
        ) -> bool:
            raise AssertionError(f"Unexpected overwrite prompt: {title} {message_text}")

        monkeypatch.setattr(copy_folders, "_ask_yes_no_QWIM", _unexpected_overwrite_prompt)

        copied_paths = copy_folders.copy_content_student_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert "pyproject.toml" in copied_relative_paths
        assert "properdocs.yml" in copied_relative_paths
        assert "src/package/module.py" in copied_relative_paths
        assert "src/package/UPPER.PY" in copied_relative_paths
        assert "src/dashboard/reporting/report_QWIM.typ" in copied_relative_paths
        assert "src/dashboard/reporting/utils_table.typ" in copied_relative_paths
        assert "tests/unit/test_example.py" in copied_relative_paths
        assert "tests/data/sample.parquet" in copied_relative_paths
        assert "inputs/config.json" in copied_relative_paths
        assert "inputs/notes.txt" in copied_relative_paths

        assert not (fixture_target_project_QWIM / "src" / "package" / "notes.md").exists()
        assert not (fixture_target_project_QWIM / "src" / "package" / "pycache").exists()
        assert not (fixture_target_project_QWIM / "src" / "package" / "__pycache__").exists()
        assert not (fixture_target_project_QWIM / "src" / "dashboard" / "reporting" / "README.md").exists()
        assert not (fixture_target_project_QWIM / "tests" / "data" / "sample.txt").exists()
        assert not (fixture_target_project_QWIM / "tests" / "pycache").exists()
        assert not (fixture_target_project_QWIM / "inputs" / "pycache").exists()

        assert captured_messages == [
            (
                "Copy completed",
                "info",
                "Copied 11 file(s) for the student projects bundle.",
            ),
        ]

    @pytest.mark.unit()
    def Test_Cancelled_Folder_Picker_Returns_Empty_List(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        monkeypatch.setattr(copy_folders, "_select_target_directory_QWIM", lambda: None)

        def _unexpected_message(*_args: object, **_kwargs: object) -> None:
            raise AssertionError("No message dialog should be shown when selection is cancelled.")

        monkeypatch.setattr(copy_folders, "_show_message_QWIM", _unexpected_message)

        result = copy_folders.copy_content_student_projects_QWIM(
            source_root=fixture_source_project_QWIM,
        )

        assert result == []

    @pytest.mark.unit()
    def Test_Conflict_Declined_Aborts_Copy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_messages = _patch_show_message_QWIM(monkeypatch)
        captured_prompt: dict[str, str] = {}

        _write_text_file_QWIM(
            fixture_target_project_QWIM / "pyproject.toml",
            "[project]\nname = 'old'\n",
        )

        def _decline_overwrite(
            message_text: str,
            *,
            title: str,
        ) -> bool:
            captured_prompt["title"] = title
            captured_prompt["message"] = message_text
            return False

        monkeypatch.setattr(copy_folders, "_ask_yes_no_QWIM", _decline_overwrite)

        copied_paths = copy_folders.copy_content_student_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        assert copied_paths == []
        assert (fixture_target_project_QWIM / "pyproject.toml").read_text(encoding="utf-8") == (
            "[project]\nname = 'old'\n"
        )
        assert not (fixture_target_project_QWIM / "properdocs.yml").exists()
        assert captured_prompt["title"] == "Confirm overwrite"
        assert "pyproject.toml" in captured_prompt["message"]
        assert captured_messages == [
            (
                "Copy cancelled",
                "warning",
                "The student projects copy was cancelled because overwrite was declined.",
            ),
        ]

    @pytest.mark.unit()
    def Test_Conflict_Approved_Overwrites_And_Preserves_Unrelated_Files(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        _patch_show_message_QWIM(monkeypatch)

        _write_text_file_QWIM(
            fixture_target_project_QWIM / "pyproject.toml",
            "[project]\nname = 'old'\n",
        )
        _write_text_file_QWIM(
            fixture_target_project_QWIM / "src" / "package" / "unrelated.md",
            "keep me\n",
        )

        monkeypatch.setattr(copy_folders, "_ask_yes_no_QWIM", lambda message_text, *, title: True)

        copied_paths = copy_folders.copy_content_student_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        assert copied_paths
        assert (fixture_target_project_QWIM / "pyproject.toml").read_text(encoding="utf-8") == (
            "[project]\nname = 'sample'\n"
        )
        assert (fixture_target_project_QWIM / "src" / "package" / "unrelated.md").exists()

    @pytest.mark.unit()
    def Test_Missing_Source_File_Raises_Not_Found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        from src.utils.files_folders.copy_folders import copy_content_student_projects_QWIM

        _patch_show_message_QWIM(monkeypatch)
        (fixture_source_project_QWIM / "properdocs.yml").unlink()

        with pytest.raises(Exception_Not_Found, match="Required source path"):
            copy_content_student_projects_QWIM(
                target_dir=fixture_target_project_QWIM,
                source_root=fixture_source_project_QWIM,
            )


class Class_Test_Copy_Content_Posit_Connect_QWIM:
    """Tests for the Posit Connect deployment copy bundle."""

    @pytest.mark.unit()
    def Test_Uses_Folder_Picker_When_Target_Not_Supplied(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        _patch_show_message_QWIM(monkeypatch)
        monkeypatch.setattr(
            copy_folders,
            "_select_target_directory_QWIM",
            lambda: str(fixture_target_project_QWIM),
        )

        def _unexpected_overwrite_prompt(
            message_text: str,
            *,
            title: str,
        ) -> bool:
            raise AssertionError(f"Unexpected overwrite prompt: {title} {message_text}")

        monkeypatch.setattr(copy_folders, "_ask_yes_no_QWIM", _unexpected_overwrite_prompt)

        copied_paths = copy_folders.copy_content_posit_connect_QWIM(
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert copied_relative_paths == {
            "app.py",
            "inputs/config.json",
            "inputs/notes.txt",
            "main.py",
            "requirements.txt",
            "src/dashboard/reporting/report_QWIM.typ",
            "src/dashboard/reporting/utils_table.typ",
            "src/package/UPPER.PY",
            "src/package/module.py",
        }
        assert not (fixture_target_project_QWIM / "docs").exists()
        assert not (fixture_target_project_QWIM / "src" / "dashboard" / "reporting" / "README.md").exists()
        assert not (fixture_target_project_QWIM / "tests").exists()


class Class_Test_Copy_Content_My_Projects_QWIM:
    """Tests for the full project-to-project copy bundle."""

    @pytest.mark.unit()
    def Test_Copies_Unfiltered_And_Filtered_Folders(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        from src.utils.files_folders.copy_folders import copy_content_my_projects_QWIM

        _patch_show_message_QWIM(monkeypatch)

        copied_paths = copy_content_my_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert ".github/workflows/ci.yml" in copied_relative_paths
        assert "GHCP-Plans/plan.md" in copied_relative_paths
        assert "docs/index.md" in copied_relative_paths
        assert "docs/assets/logo.png" in copied_relative_paths
        assert "tests/data/sample.parquet" in copied_relative_paths

        assert not (fixture_target_project_QWIM / "docs" / "pycache").exists()

    @pytest.mark.unit()
    def Test_Target_Inside_Source_Raises_Security_Violation(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
    ) -> None:
        from src.utils.files_folders.copy_folders import copy_content_my_projects_QWIM

        _patch_show_message_QWIM(monkeypatch)
        nested_target_dir = fixture_source_project_QWIM / "nested_target"
        nested_target_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(Exception_Security_Violation, match="outside the source project tree"):
            copy_content_my_projects_QWIM(
                target_dir=nested_target_dir,
                source_root=fixture_source_project_QWIM,
            )


class Class_Test_Copy_Content_Typst_Files_QWIM:
    """Tests for Typst (.typ) file inclusion in every copy bundle."""

    @pytest.mark.unit()
    def Test_Typst_Constant_Is_Defined_With_Typ_Only(
        self,
    ) -> None:
        """The Typst allowlist contains only the ``.typ`` extension."""
        from src.utils.files_folders import copy_folders

        assert copy_folders.ALLOWED_SUFFIXES_TYPST_QWIM == frozenset({".typ"})

    @pytest.mark.unit()
    def Test_All_Bundles_Include_Reporting_Spec_With_Typst_Allowlist(
        self,
    ) -> None:
        """Every bundle has a spec for ``src/dashboard/reporting`` with the Typst allowlist."""
        from src.utils.files_folders import copy_folders

        for bundle_specs in (
            copy_folders.COPY_SPECS_STUDENT_PROJECTS_QWIM,
            copy_folders.COPY_SPECS_POSIT_CONNECT_QWIM,
            copy_folders.COPY_SPECS_MY_PROJECTS_QWIM,
        ):
            reporting_specs = [
                spec for spec in bundle_specs
                if spec.relative_path == Path("src/dashboard/reporting")
            ]
            assert len(reporting_specs) == 1, (
                f"Expected exactly one src/dashboard/reporting spec, got {len(reporting_specs)}"
            )
            assert reporting_specs[0].item_kind == "directory"
            assert reporting_specs[0].allowed_suffixes == copy_folders.ALLOWED_SUFFIXES_TYPST_QWIM

    @pytest.mark.unit()
    def Test_Student_Bundle_Copies_Typst_And_Skips_Non_Typst(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        """The student-projects bundle copies ``.typ`` files but not ``.md`` from the reporting tree."""
        import src.utils.files_folders.copy_folders as copy_folders

        _patch_show_message_QWIM(monkeypatch)

        copied_paths = copy_folders.copy_content_student_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert "src/dashboard/reporting/report_QWIM.typ" in copied_relative_paths
        assert "src/dashboard/reporting/utils_table.typ" in copied_relative_paths
        assert "src/dashboard/reporting/README.md" not in copied_relative_paths

    @pytest.mark.unit()
    def Test_Posit_Connect_Bundle_Copies_Typst(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        """The Posit Connect bundle copies ``.typ`` files alongside the source tree."""
        import src.utils.files_folders.copy_folders as copy_folders

        _patch_show_message_QWIM(monkeypatch)

        copied_paths = copy_folders.copy_content_posit_connect_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert "src/dashboard/reporting/report_QWIM.typ" in copied_relative_paths
        assert "src/dashboard/reporting/utils_table.typ" in copied_relative_paths
        assert "src/dashboard/reporting/README.md" not in copied_relative_paths

    @pytest.mark.unit()
    def Test_My_Projects_Bundle_Copies_Typst(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fixture_source_project_QWIM: Path,
        fixture_target_project_QWIM: Path,
    ) -> None:
        """The my-projects bundle copies ``.typ`` files alongside the full source tree."""
        import src.utils.files_folders.copy_folders as copy_folders

        _patch_show_message_QWIM(monkeypatch)

        copied_paths = copy_folders.copy_content_my_projects_QWIM(
            target_dir=fixture_target_project_QWIM,
            source_root=fixture_source_project_QWIM,
        )

        copied_relative_paths = {
            item_path.relative_to(fixture_target_project_QWIM).as_posix()
            for item_path in copied_paths
        }

        assert "src/dashboard/reporting/report_QWIM.typ" in copied_relative_paths
        assert "src/dashboard/reporting/utils_table.typ" in copied_relative_paths
        assert "src/dashboard/reporting/README.md" not in copied_relative_paths


class Class_Test_Copy_Workflow_CLI_QWIM:
    """Tests for the public launcher and CLI entry point."""

    @pytest.mark.unit()
    def Test_Launch_Copy_GUI_Dispatches_Selected_Workflow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_gui_arguments: dict[str, object] = {}
        captured_tkinter = _install_fake_tkinter_QWIM(
            monkeypatch,
            auto_invoke_button_text="Student Projects",
        )

        def _fake_launch(
            workflow_name: str,
            target_dir: str | Path | None = None,
            *,
            source_root: str | Path | None = None,
        ) -> list[Path]:
            captured_gui_arguments["workflow_name"] = workflow_name
            captured_gui_arguments["target_dir"] = target_dir
            captured_gui_arguments["source_root"] = source_root
            return []

        monkeypatch.setattr(copy_folders, "launch_copy_workflow_QWIM", _fake_launch)

        copy_folders.launch_copy_gui_QWIM(source_root="C:/source-project")

        assert captured_tkinter["window_title"] == "QWIM Copy Workflows"
        assert captured_tkinter["mainloop_called"] is True
        assert "Student Projects" in captured_tkinter["button_texts"]
        assert captured_gui_arguments == {
            "workflow_name": "student-projects",
            "target_dir": None,
            "source_root": "C:/source-project",
        }

    @pytest.mark.unit()
    def Test_Launch_Copy_GUI_Shows_Warning_When_Workflow_Fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_messages = _patch_show_message_QWIM(monkeypatch)
        _install_fake_tkinter_QWIM(
            monkeypatch,
            auto_invoke_button_text="My Projects",
        )

        def _raise_not_found(
            workflow_name: str,
            target_dir: str | Path | None = None,
            *,
            source_root: str | Path | None = None,
        ) -> list[Path]:
            del workflow_name, target_dir, source_root
            raise Exception_Not_Found("Target project folder was not found.")

        monkeypatch.setattr(copy_folders, "launch_copy_workflow_QWIM", _raise_not_found)

        copy_folders.launch_copy_gui_QWIM()

        assert captured_messages == [
            (
                "Copy workflow error",
                "warning",
                "Target project folder was not found.",
            ),
        ]

    @pytest.mark.unit()
    def Test_Launch_Copy_Workflow_Dispatches_Student_Workflow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_arguments: dict[str, object] = {}

        def _fake_student_workflow(
            target_dir: str | Path | None = None,
            *,
            source_root: str | Path | None = None,
        ) -> list[Path]:
            captured_arguments["target_dir"] = target_dir
            captured_arguments["source_root"] = source_root
            return [Path("copied.py")]

        monkeypatch.setattr(
            copy_folders,
            "copy_content_student_projects_QWIM",
            _fake_student_workflow,
        )

        copied_paths = copy_folders.launch_copy_workflow_QWIM(
            workflow_name = "student-projects",
            target_dir="C:/target-project",
            source_root="C:/source-project",
        )

        assert copied_paths == [Path("copied.py")]
        assert captured_arguments == {
            "target_dir": "C:/target-project",
            "source_root": "C:/source-project",
        }

    @pytest.mark.unit()
    def Test_Launch_Copy_Workflow_Raises_For_Unknown_Workflow(
        self,
    ) -> None:
        from src.utils.files_folders.copy_folders import launch_copy_workflow_QWIM

        with pytest.raises(Exception_Validation_Input, match="Unknown copy workflow"):
            launch_copy_workflow_QWIM(workflow_name = "unknown-workflow")

    @pytest.mark.unit()
    def Test_Main_Returns_Zero_For_Valid_CLI_Arguments(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_arguments: dict[str, object] = {}

        def _fake_launch(
            workflow_name: str,
            target_dir: str | Path | None = None,
            *,
            source_root: str | Path | None = None,
        ) -> list[Path]:
            captured_arguments["workflow_name"] = workflow_name
            captured_arguments["target_dir"] = target_dir
            captured_arguments["source_root"] = source_root
            return [Path("copied.py")]

        monkeypatch.setattr(copy_folders, "launch_copy_workflow_QWIM", _fake_launch)

        exit_code = copy_folders.main(
            [
                "my-projects",
                "--target-dir",
                "C:/target-project",
                "--source-root",
                "C:/source-project",
            ],
        )

        assert exit_code == 0
        assert captured_arguments == {
            "workflow_name": "my-projects",
            "target_dir": "C:/target-project",
            "source_root": "C:/source-project",
        }

    @pytest.mark.unit()
    def Test_Main_Launches_GUI_When_No_Workflow_Is_Given(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        captured_arguments: dict[str, object] = {}

        def _fake_launch_gui(*, source_root: str | Path | None = None) -> None:
            captured_arguments["source_root"] = source_root

        monkeypatch.setattr(copy_folders, "launch_copy_gui_QWIM", _fake_launch_gui)

        exit_code = copy_folders.main(["--source-root", "C:/source-project"])

        assert exit_code == 0
        assert captured_arguments == {"source_root": "C:/source-project"}

    @pytest.mark.unit()
    def Test_Main_Returns_One_When_Gui_Conflicts_With_Target_Dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        def _unexpected_launch_gui(*, source_root: str | Path | None = None) -> None:
            raise AssertionError(f"Unexpected GUI launch with source_root={source_root!r}")

        monkeypatch.setattr(copy_folders, "launch_copy_gui_QWIM", _unexpected_launch_gui)

        exit_code = copy_folders.main(
            [
                "--gui",
                "--target-dir",
                "C:/target-project",
            ],
        )

        assert exit_code == 1

    @pytest.mark.unit()
    def Test_Main_Returns_One_When_Workflow_Raises_Project_Exception(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import src.utils.files_folders.copy_folders as copy_folders

        def _raise_not_found(
            workflow_name: str,
            target_dir: str | Path | None = None,
            *,
            source_root: str | Path | None = None,
        ) -> list[Path]:
            del workflow_name, target_dir, source_root
            raise Exception_Not_Found("Target project folder was not found.")

        monkeypatch.setattr(copy_folders, "launch_copy_workflow_QWIM", _raise_not_found)

        exit_code = copy_folders.main(
            [
                "posit-connect",
                "--target-dir",
                "C:/missing-target",
            ],
        )

        assert exit_code == 1