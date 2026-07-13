"""Selective copy workflows for exporting curated QWIM project bundles."""

from __future__ import annotations

import os
import shutil
import sys

import attrs
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
	Exception_Configuration,
	Exception_File_Operation,
	Exception_Not_Found,
	Exception_Security_Violation,
	Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._copy_folders_cli import (
	launch_copy_gui_impl_QWIM,
	launch_copy_workflow_impl_QWIM,
	main_impl_QWIM,
	run_gui_workflow_impl_QWIM,
)


if TYPE_CHECKING:
	from collections.abc import Callable, Iterable, Sequence


_logger = get_logger(name = __name__)

IGNORED_DIRECTORY_NAMES_QWIM = frozenset({"__pycache__", "pycache"})
ALLOWED_SUFFIXES_PYTHON_QWIM = frozenset({".py"})
ALLOWED_SUFFIXES_TESTS_QWIM = frozenset({".py", ".parquet"})
ALLOWED_SUFFIXES_TYPST_QWIM = frozenset({".typ"})
MAX_CONFLICT_PREVIEW_COUNT_QWIM = 10

_type_dialog_result_QWIM = TypeVar("_type_dialog_result_QWIM")


@attrs.frozen(kw_only=True)
class Copy_Path_Spec_QWIM:
	"""One project-relative file or directory included in a copy bundle."""

	relative_path: Path = attrs.field()
	item_kind: Literal["file", "directory"] = attrs.field()
	allowed_suffixes: frozenset[str] | None = attrs.field(default=None)


COPY_SPECS_STUDENT_PROJECTS_QWIM: tuple[Copy_Path_Spec_QWIM, ...] = (
	Copy_Path_Spec_QWIM(relative_path=Path("pyproject.toml"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("properdocs.yml"), item_kind="file"),
#	Copy_Path_Spec_QWIM(relative_path=Path("pytest.ini"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("behave.ini"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("src"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_PYTHON_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("src/dashboard/reporting"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_TYPST_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("tests"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_TESTS_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("inputs"), item_kind="directory"),
)

COPY_SPECS_POSIT_CONNECT_QWIM: tuple[Copy_Path_Spec_QWIM, ...] = (
	Copy_Path_Spec_QWIM(relative_path=Path("app.py"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("main.py"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("requirements.txt"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("src"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_PYTHON_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("src/dashboard/reporting"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_TYPST_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("inputs"), item_kind="directory"),
)

COPY_SPECS_MY_PROJECTS_QWIM: tuple[Copy_Path_Spec_QWIM, ...] = (
	Copy_Path_Spec_QWIM(relative_path=Path("app.py"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("requirements.txt"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("pyproject.toml"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("properdocs.yml"), item_kind="file"),
#	Copy_Path_Spec_QWIM(relative_path=Path("pytest.ini"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path("behave.ini"), item_kind="file"),
	Copy_Path_Spec_QWIM(relative_path=Path(".github"), item_kind="directory"),
	Copy_Path_Spec_QWIM(relative_path=Path("GHCP-Plans"), item_kind="directory"),
	Copy_Path_Spec_QWIM(relative_path=Path("src"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_PYTHON_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("src/dashboard/reporting"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_TYPST_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("docs"), item_kind="directory"),
	Copy_Path_Spec_QWIM(relative_path=Path("tests"), item_kind="directory", allowed_suffixes=ALLOWED_SUFFIXES_TESTS_QWIM),
	Copy_Path_Spec_QWIM(relative_path=Path("inputs"), item_kind="directory"),
)

__all__ = [
	"Copy_Path_Spec_QWIM",
	"copy_content_my_projects_QWIM",
	"copy_content_posit_connect_QWIM",
	"copy_content_student_projects_QWIM",
	"launch_copy_gui_QWIM",
	"launch_copy_workflow_QWIM",
	"main",
]


def _is_ignored_directory_name_QWIM(
	*, directory_name: str) -> bool:
	"""Return whether a directory should be excluded from copy traversal.

	Parameters
	----------
	directory_name : str
		Directory name to evaluate.

	Returns
	-------
	bool
		``True`` when the directory is a Python cache folder.
	"""
	return directory_name.casefold() in IGNORED_DIRECTORY_NAMES_QWIM


def _run_tkinter_dialog_QWIM(
	*, dialog_runner: Callable[[], _type_dialog_result_QWIM], operation_name: str) -> _type_dialog_result_QWIM:
	"""Run one ``tkinter`` dialog with a hidden root window.

	Parameters
	----------
	dialog_runner : collections.abc.Callable[[], _type_dialog_result_QWIM]
		Zero-argument callable that opens the desired dialog.
	operation_name : str
		Human-readable description used in error messages.

	Returns
	-------
	_type_dialog_result_QWIM
		The value returned by ``dialog_runner``.

	Raises
	------
	Exception_Configuration
		Raised when ``tkinter`` is unavailable or cannot open the dialog.
	"""
	try:
		import tkinter as tk
	except ImportError as exc:
		raise Exception_Configuration(
			f"tkinter is required to {operation_name}.",
			config_key="tkinter",
		) from exc

	root_window: Any | None = None
	try:
		root_window = tk.Tk()
		root_window.withdraw()
		root_window.attributes("-topmost", True)
		return dialog_runner()
	except tk.TclError as exc:
		raise Exception_Configuration(
			f"Unable to {operation_name} with tkinter in this environment.",
			config_key="tkinter",
		) from exc
	finally:
		if root_window is not None:
			root_window.destroy()


def _select_target_directory_QWIM() -> str | None:
	"""Open a native folder picker and return the selected directory.

	Returns
	-------
	str | None
		Selected directory path, or ``None`` when the user cancels.
	"""

	def _open_dialog() -> str:
		from tkinter import filedialog

		return str(
			filedialog.askdirectory(
				mustexist=True,
				title="Select the target project folder",
			),
		)

	selected_directory = _run_tkinter_dialog_QWIM(
		dialog_runner = _open_dialog,
		operation_name="select a target folder",
	)
	if not selected_directory:
		return None
	return selected_directory


def _show_message_QWIM(
	*, message_text: str, title: str, message_kind: Literal["info", "warning"] = "info") -> None:
	"""Show a simple message dialog.

	Parameters
	----------
	message_text : str
		Message body shown to the user.
	title : str
		Window title.
	message_kind : {"info", "warning"}, optional
		Dialog type, by default ``"info"``.
	"""

	def _open_dialog() -> None:
		from tkinter import messagebox

		if message_kind == "warning":
			messagebox.showwarning(title, message_text)
			return None
		messagebox.showinfo(title, message_text)
		return None

	_run_tkinter_dialog_QWIM(
		dialog_runner = _open_dialog,
		operation_name=f"show a {message_kind} message",
	)


def _ask_yes_no_QWIM(
	*, message_text: str, title: str) -> bool:
	"""Show a yes-or-no confirmation dialog.

	Parameters
	----------
	message_text : str
		Confirmation prompt shown to the user.
	title : str
		Window title.

	Returns
	-------
	bool
		``True`` when the user confirms the action.
	"""

	def _open_dialog() -> bool:
		from tkinter import messagebox

		return bool(messagebox.askyesno(title, message_text))

	return _run_tkinter_dialog_QWIM(
		dialog_runner = _open_dialog,
		operation_name="confirm overwrite",
	)


def _resolve_project_root_QWIM(
	*, source_root: str | Path | None = None) -> Path:
	"""Resolve the source project root for copy operations.

	Parameters
	----------
	source_root : str | pathlib.Path | None, optional
		Optional explicit source project root for tests or custom callers.

	Returns
	-------
	pathlib.Path
		Resolved project-root directory.

	Raises
	------
	Exception_Not_Found
		Raised when the supplied path does not exist or the module cannot
		discover the repository root automatically.
	Exception_Validation_Input
		Raised when the supplied path is not a directory.
	"""
	if source_root is not None:
		resolved_root = Path(source_root).expanduser().resolve()
		if not resolved_root.exists():
			raise Exception_Not_Found(
				"Source project folder was not found.",
				resource_type="Directory",
				resource_id=str(resolved_root),
			)
		if not resolved_root.is_dir():
			raise Exception_Validation_Input(
				"Source project path must be a directory.",
				field_name="source_root",
				actual_value=str(resolved_root),
			)
		return resolved_root

	module_file_path = Path(__file__).resolve()
	for candidate_root in module_file_path.parents:
		if (candidate_root / "pyproject.toml").is_file() and (candidate_root / "src").is_dir():
			return candidate_root

	raise Exception_Not_Found(
		"Could not resolve the current project root from copy_folders.py.",
		resource_type="ProjectRoot",
		resource_id=str(module_file_path),
	)


def _resolve_target_directory_QWIM(
	*, target_dir: str | Path | None) -> Path | None:
	"""Resolve the destination directory for a copy operation.

	Parameters
	----------
	target_dir : str | pathlib.Path | None
		Explicit target directory, or ``None`` to open the folder picker.

	Returns
	-------
	pathlib.Path | None
		Resolved target directory, or ``None`` when the user cancels the
		folder picker.

	Raises
	------
	Exception_Not_Found
		Raised when the requested target directory does not exist.
	Exception_Validation_Input
		Raised when the target path is not a directory.
	"""
	raw_target_dir = target_dir
	if raw_target_dir is None:
		raw_target_dir = _select_target_directory_QWIM()
		if raw_target_dir is None:
			return None

	resolved_target_dir = Path(raw_target_dir).expanduser().resolve()
	if not resolved_target_dir.exists():
		raise Exception_Not_Found(
			"Target project folder was not found.",
			resource_type="Directory",
			resource_id=str(resolved_target_dir),
		)
	if not resolved_target_dir.is_dir():
		raise Exception_Validation_Input(
			"Target project path must be a directory.",
			field_name="target_dir",
			actual_value=str(resolved_target_dir),
		)

	return resolved_target_dir


def _validate_target_outside_source_QWIM(
	*, source_root: Path, target_dir: Path) -> None:
	"""Reject target directories that live inside the source project tree.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	target_dir : pathlib.Path
		Destination project root.

	Raises
	------
	Exception_Security_Violation
		Raised when the target directory is the source root or a child of it.
	"""
	if target_dir.is_relative_to(source_root):
		raise Exception_Security_Violation(
			"Target project folder must be outside the source project tree.",
			violation_type="copy_target_inside_source",
			resource=str(target_dir),
		)


def _resolve_source_path_for_spec_QWIM(
	*, source_root: Path, copy_spec: Copy_Path_Spec_QWIM) -> Path:
	"""Resolve one spec path relative to the source project root.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	copy_spec : Copy_Path_Spec_QWIM
		Copy specification to validate.

	Returns
	-------
	pathlib.Path
		Existing source file or directory.

	Raises
	------
	Exception_Not_Found
		Raised when the source path does not exist.
	Exception_File_Operation
		Raised when the source path kind does not match the copy spec.
	"""
	source_path = source_root / copy_spec.relative_path
	if not source_path.exists():
		raise Exception_Not_Found(
			"Required source path was not found for the copy bundle.",
			resource_type=copy_spec.item_kind.capitalize(),
			resource_id=str(source_path),
		)

	if copy_spec.item_kind == "file" and not source_path.is_file():
		raise Exception_File_Operation(
			"Copy bundle expected a file but found a different path type.",
			file_path=source_path,
			operation="validate source path",
		)

	if copy_spec.item_kind == "directory" and not source_path.is_dir():
		raise Exception_File_Operation(
			"Copy bundle expected a directory but found a different path type.",
			file_path=source_path,
			operation="validate source path",
		)

	return source_path


def _should_copy_file_QWIM(
	*, file_path: Path, allowed_suffixes: frozenset[str] | None) -> bool:
	"""Return whether one file matches the current directory filter.

	Parameters
	----------
	file_path : pathlib.Path
		Candidate file path.
	allowed_suffixes : frozenset[str] | None
		Optional suffix allowlist.

	Returns
	-------
	bool
		``True`` when the file should be copied.
	"""
	if allowed_suffixes is None:
		return True
	return file_path.suffix.casefold() in allowed_suffixes


def _iter_directory_files_QWIM(
	*, source_root: Path, source_dir: Path, allowed_suffixes: frozenset[str] | None) -> Iterable[Path]:
	"""Yield files selected from one directory copy spec.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	source_dir : pathlib.Path
		Directory being traversed.
	allowed_suffixes : frozenset[str] | None
		Optional suffix allowlist.

	Returns
	-------
	collections.abc.Iterable[pathlib.Path]
		Selected file paths below ``source_dir``.
	"""
	del source_root
	for current_root_str, directory_names, file_names in os.walk(source_dir):
		directory_names[:] = [
			item_name for item_name in directory_names if not _is_ignored_directory_name_QWIM(directory_name = item_name)
		]

		current_root = Path(current_root_str)
		for file_name in sorted(file_names):
			current_file = current_root / file_name
			if _should_copy_file_QWIM(file_path = current_file, allowed_suffixes = allowed_suffixes):
				yield current_file


def _collect_conflicting_paths_QWIM(
	*, source_root: Path, target_dir: Path, copy_specs: Sequence[Copy_Path_Spec_QWIM]) -> list[Path]:
	"""Collect destination paths that already exist for a copy bundle.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	target_dir : pathlib.Path
		Destination project root.
	copy_specs : collections.abc.Sequence[Copy_Path_Spec_QWIM]
		Copy specification bundle.

	Returns
	-------
	list[pathlib.Path]
		Sorted destination paths that already exist.
	"""
	conflicts_set: set[Path] = set()
	for copy_spec in copy_specs:
		source_path = _resolve_source_path_for_spec_QWIM(source_root = source_root, copy_spec = copy_spec)
		target_path = target_dir / copy_spec.relative_path
		if target_path.exists():
			conflicts_set.add(target_path)

		if copy_spec.item_kind == "file":
			continue

		for source_file in _iter_directory_files_QWIM(
			source_root = source_root,
			source_dir = source_path,
			allowed_suffixes = copy_spec.allowed_suffixes,
		):
			destination_file = target_dir / source_file.relative_to(source_root)
			if destination_file.exists():
				conflicts_set.add(destination_file)

	return sorted(conflicts_set)


def _format_conflict_message_QWIM(
	*, bundle_label: str, conflicting_paths: Sequence[Path], target_dir: Path) -> str:
	"""Build a readable overwrite prompt for conflicting destination paths.

	Parameters
	----------
	bundle_label : str
		Human-readable name of the copy bundle.
	conflicting_paths : collections.abc.Sequence[pathlib.Path]
		Existing destination paths.
	target_dir : pathlib.Path
		Destination project root.

	Returns
	-------
	str
		Multi-line confirmation message.
	"""
	preview_lines = [
		f"- {item_path.relative_to(target_dir)}"
		for item_path in conflicting_paths[:MAX_CONFLICT_PREVIEW_COUNT_QWIM]
	]
	remaining_count = len(conflicting_paths) - len(preview_lines)
	if remaining_count > 0:
		preview_lines.append(f"- ... plus {remaining_count} more path(s)")

	preview_text = "\n".join(preview_lines)
	return (
		f"The {bundle_label} copy bundle found {len(conflicting_paths)} existing "
		f"matching file(s) or folder(s) in:\n{target_dir}\n\n"
		f"Conflicts:\n{preview_text}\n\n"
		"Overwrite the matching copied items?"
	)


def _confirm_overwrite_QWIM(
	*, bundle_label: str, conflicting_paths: Sequence[Path], target_dir: Path) -> bool:
	"""Ask the user whether a conflicting copy bundle should proceed.

	Parameters
	----------
	bundle_label : str
		Human-readable name of the copy bundle.
	conflicting_paths : collections.abc.Sequence[pathlib.Path]
		Existing destination paths.
	target_dir : pathlib.Path
		Destination project root.

	Returns
	-------
	bool
		``True`` when the user approves overwrite.
	"""
	message_text = _format_conflict_message_QWIM(
		bundle_label = bundle_label,
		conflicting_paths = conflicting_paths,
		target_dir = target_dir,
	)
	return _ask_yes_no_QWIM(message_text = message_text, title="Confirm overwrite")


def _ensure_directory_exists_QWIM(
	*, directory_path: Path) -> None:
	"""Create one destination directory when needed.

	Parameters
	----------
	directory_path : pathlib.Path
		Directory that must exist.

	Raises
	------
	Exception_File_Operation
		Raised when the directory cannot be created.
	"""
	try:
		directory_path.mkdir(parents=True, exist_ok=True)
	except OSError as exc:
		raise Exception_File_Operation(
			"Failed to create a destination directory during copy.",
			file_path=directory_path,
			operation="mkdir",
		) from exc


def _copy_file_QWIM(
	*, source_file: Path, destination_file: Path) -> Path:
	"""Copy one file into the destination tree.

	Parameters
	----------
	source_file : pathlib.Path
		Source file to copy.
	destination_file : pathlib.Path
		Destination file path.

	Returns
	-------
	pathlib.Path
		Destination file path after copying.

	Raises
	------
	Exception_File_Operation
		Raised when the file cannot be copied.
	"""
	_ensure_directory_exists_QWIM(directory_path = destination_file.parent)
	try:
		shutil.copy2(source_file, destination_file)
	except OSError as exc:
		raise Exception_File_Operation(
			"Failed to copy a file into the destination project.",
			file_path=destination_file,
			operation="copy2",
		) from exc
	return destination_file


def _copy_directory_spec_QWIM(
	*, source_root: Path, target_dir: Path, copy_spec: Copy_Path_Spec_QWIM) -> list[Path]:
	"""Copy one directory copy spec into the destination tree.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	target_dir : pathlib.Path
		Destination project root.
	copy_spec : Copy_Path_Spec_QWIM
		Directory specification to copy.

	Returns
	-------
	list[pathlib.Path]
		Destination files copied for this directory spec.
	"""
	source_dir = _resolve_source_path_for_spec_QWIM(source_root = source_root, copy_spec = copy_spec)
	copied_paths: list[Path] = []

	for current_root_str, directory_names, file_names in os.walk(source_dir):
		directory_names[:] = [
			item_name for item_name in directory_names if not _is_ignored_directory_name_QWIM(directory_name = item_name)
		]

		current_source_dir = Path(current_root_str)
		current_target_dir = target_dir / current_source_dir.relative_to(source_root)
		matching_files = [
			current_source_dir / file_name
			for file_name in sorted(file_names)
			if _should_copy_file_QWIM(file_path = current_source_dir / file_name, allowed_suffixes = copy_spec.allowed_suffixes)
		]

		if (
			copy_spec.allowed_suffixes is None
			or current_source_dir == source_dir
			or matching_files
		):
			_ensure_directory_exists_QWIM(directory_path = current_target_dir)

		for source_file in matching_files:
			destination_file = current_target_dir / source_file.name
			copied_paths.append(_copy_file_QWIM(source_file = source_file, destination_file = destination_file))

	return copied_paths


def _copy_bundle_QWIM(
	*, source_root: Path, target_dir: Path, copy_specs: Sequence[Copy_Path_Spec_QWIM]) -> list[Path]:
	"""Copy one validated bundle into the target project folder.

	Parameters
	----------
	source_root : pathlib.Path
		Source project root.
	target_dir : pathlib.Path
		Destination project root.
	copy_specs : collections.abc.Sequence[Copy_Path_Spec_QWIM]
		Copy specification bundle.

	Returns
	-------
	list[pathlib.Path]
		Sorted destination files that were copied.
	"""
	copied_paths: list[Path] = []
	for copy_spec in copy_specs:
		source_path = _resolve_source_path_for_spec_QWIM(source_root = source_root, copy_spec = copy_spec)
		if copy_spec.item_kind == "file":
			destination_path = target_dir / copy_spec.relative_path
			copied_paths.append(_copy_file_QWIM(source_file = source_path, destination_file = destination_path))
			continue

		copied_paths.extend(_copy_directory_spec_QWIM(source_root = source_root, target_dir = target_dir, copy_spec = copy_spec))

	return sorted(copied_paths)


def _copy_project_bundle_QWIM(
	*, bundle_label: str, copy_specs: Sequence[Copy_Path_Spec_QWIM], target_dir: str | Path | None = None, source_root: str | Path | None = None) -> list[Path]:
	"""Execute one copy workflow and return the copied destination paths."""
	resolved_source_root = _resolve_project_root_QWIM(source_root = source_root)
	resolved_target_dir = _resolve_target_directory_QWIM(target_dir = target_dir)
	if resolved_target_dir is None:
		_logger.info("%s copy cancelled because no target folder was selected.", bundle_label)
		return []

	_validate_target_outside_source_QWIM(source_root = resolved_source_root, target_dir = resolved_target_dir)

	conflicting_paths = _collect_conflicting_paths_QWIM(
		source_root = resolved_source_root,
		target_dir = resolved_target_dir,
		copy_specs = copy_specs,
	)
	if conflicting_paths and not _confirm_overwrite_QWIM(
		bundle_label = bundle_label,
		conflicting_paths = conflicting_paths,
		target_dir = resolved_target_dir,
	):
		_logger.info(
			"%s copy cancelled after the user declined overwrite for %s.",
			bundle_label,
			resolved_target_dir,
		)
		_show_message_QWIM(
			message_text = f"The {bundle_label} copy was cancelled because overwrite was declined.",
			title="Copy cancelled",
			message_kind="warning",
		)
		return []

	copied_paths = _copy_bundle_QWIM(source_root = resolved_source_root, target_dir = resolved_target_dir, copy_specs = copy_specs)
	_logger.info(
		"%s copy completed successfully with %s copied file(s) into %s.",
		bundle_label,
		len(copied_paths),
		resolved_target_dir,
	)
	_show_message_QWIM(
		message_text = f"Copied {len(copied_paths)} file(s) for the {bundle_label} bundle.",
		title="Copy completed",
	)
	return copied_paths


def copy_content_student_projects_QWIM(
	*, target_dir: str | Path | None = None, source_root: str | Path | None = None) -> list[Path]:
	"""Copy the student-project bundle into a target project folder."""
	return _copy_project_bundle_QWIM(
		bundle_label = "student projects",
		copy_specs = COPY_SPECS_STUDENT_PROJECTS_QWIM,
		target_dir = target_dir,
		source_root=source_root,
	)


def copy_content_posit_connect_QWIM(
	*, target_dir: str | Path | None = None, source_root: str | Path | None = None) -> list[Path]:
	"""Copy the Posit Connect deployment bundle into a target folder."""
	return _copy_project_bundle_QWIM(
		bundle_label = "Posit Connect deployment",
		copy_specs = COPY_SPECS_POSIT_CONNECT_QWIM,
		target_dir = target_dir,
		source_root=source_root,
	)


def copy_content_my_projects_QWIM(
	*, target_dir: str | Path | None = None, source_root: str | Path | None = None) -> list[Path]:
	"""Copy the full project-to-project export bundle into a target folder."""
	return _copy_project_bundle_QWIM(
		bundle_label = "my projects",
		copy_specs = COPY_SPECS_MY_PROJECTS_QWIM,
		target_dir = target_dir,
		source_root=source_root,
	)


def launch_copy_workflow_QWIM(
	*, workflow_name: str, target_dir: str | Path | None = None, source_root: str | Path | None = None) -> list[Path]:
	"""Launch one named copy workflow and return the copied paths."""
	workflow_map: dict[str, Callable[..., list[Path]]] = {
		"student-projects": copy_content_student_projects_QWIM,
		"posit-connect": copy_content_posit_connect_QWIM,
		"my-projects": copy_content_my_projects_QWIM,
	}
	return launch_copy_workflow_impl_QWIM(
		workflow_name = workflow_name,
		target_dir=target_dir,
		source_root=source_root,
		workflow_map=workflow_map,
	)


def _run_gui_workflow_QWIM(
	*, workflow_name: str, source_root: str | Path | None = None) -> None:
	"""Execute one workflow from the tkinter launcher."""
	run_gui_workflow_impl_QWIM(
		workflow_name = workflow_name,
		source_root=source_root,
		launch_copy_workflow_QWIM=launch_copy_workflow_QWIM,
		show_message_QWIM=_show_message_QWIM,
		logger=_logger,
	)


def launch_copy_gui_QWIM(
	*,
	source_root: str | Path | None = None,
) -> None:
	"""Open the tkinter launcher for the available copy workflows."""
	launch_copy_gui_impl_QWIM(
		source_root=source_root,
		run_gui_workflow_QWIM=_run_gui_workflow_QWIM,
	)


def main(
	argv: list[str] | None = None) -> int:
	"""CLI entry-point for the selective copy workflows."""
	return main_impl_QWIM(
		argv = argv,
		launch_copy_gui_QWIM=launch_copy_gui_QWIM,
		launch_copy_workflow_QWIM=launch_copy_workflow_QWIM,
		logger=_logger,
	)


if __name__ == "__main__":  # pragma: no cover
	sys.exit(main())

