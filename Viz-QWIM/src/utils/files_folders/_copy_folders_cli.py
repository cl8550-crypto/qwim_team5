"""Private CLI and GUI helpers for copy_folders."""

from __future__ import annotations

import argparse

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
	Exception_Configuration,
	Exception_File_Operation,
	Exception_Not_Found,
	Exception_Security_Violation,
	Exception_Validation_Input,
)


if TYPE_CHECKING:
	from collections.abc import Callable, Mapping


def launch_copy_workflow_impl_QWIM(
	*, workflow_name: str, target_dir: str | Path | None, source_root: str | Path | None, workflow_map: Mapping[str, Callable[..., list[Path]]]) -> list[Path]:
	"""Launch one copy workflow by name."""
	workflow_name_normalized = workflow_name.strip().casefold()
	workflow_function = workflow_map.get(workflow_name_normalized)
	if workflow_function is None:
		raise Exception_Validation_Input(
			"Unknown copy workflow name.",
			field_name="workflow_name",
			actual_value=workflow_name,
		)

	return workflow_function(target_dir=target_dir, source_root=source_root)


def run_gui_workflow_impl_QWIM(
	*, workflow_name: str, source_root: str | Path | None, launch_copy_workflow_QWIM: Callable[..., list[Path]], show_message_QWIM: Callable[..., None], logger: Any) -> None:
	"""Execute one workflow from the tkinter launcher."""
	try:
		launch_copy_workflow_QWIM(workflow_name = workflow_name, source_root=source_root)
	except (
		Exception_Configuration,
		Exception_File_Operation,
		Exception_Not_Found,
		Exception_Security_Violation,
		Exception_Validation_Input,
	) as copy_error:
		error_message_text = str(copy_error.args[0]) if copy_error.args else str(copy_error)
		logger.error("%s", copy_error)
		show_message_QWIM(
			error_message_text,
			title="Copy workflow error",
			message_kind="warning",
		)


def launch_copy_gui_impl_QWIM(
	*,
	source_root: str | Path | None,
	run_gui_workflow_QWIM: Callable[..., None],
) -> None:
	"""Open a small tkinter launcher for the three copy workflows."""
	try:
		import tkinter as tk
	except ImportError as exc:
		raise Exception_Configuration(
			"tkinter is required to launch the copy workflow GUI.",
			config_key="tkinter",
		) from exc

	root_window: Any | None = None
	try:
		root_window = tk.Tk()
		root_window.title("QWIM Copy Workflows")
		root_window.resizable(False, False)

		tk.Label(
			root_window,
			text="Select one copy workflow to launch:",
		).pack(padx=16, pady=(16, 8))

		tk.Label(
			root_window,
			text="A folder picker will open after you choose a workflow.",
		).pack(padx=16, pady=(0, 12))

		def _build_workflow_command(
			*, selected_workflow_name: str) -> Callable[[], None]:
			def _handle_workflow_selection() -> None:
				if root_window is not None:
					root_window.destroy()
				run_gui_workflow_QWIM(
					workflow_name=selected_workflow_name,
					source_root=source_root,
				)

			return _handle_workflow_selection

		workflow_buttons = (
			("Student Projects", "student-projects"),
			("Posit Connect Deployment", "posit-connect"),
			("My Projects", "my-projects"),
		)
		for button_text, workflow_name in workflow_buttons:
			tk.Button(
				root_window,
				text=button_text,
				width=28,
				command=_build_workflow_command(selected_workflow_name = workflow_name),
			).pack(padx=16, pady=4)

		tk.Button(
			root_window,
			text="Close",
			width=28,
			command=root_window.destroy,
		).pack(padx=16, pady=(8, 16))

		root_window.mainloop()
	except tk.TclError as exc:
		raise Exception_Configuration(
			"Unable to launch the copy workflow GUI with tkinter in this environment.",
			config_key="tkinter",
		) from exc


def main_impl_QWIM(
	*, argv: list[str] | None, launch_copy_gui_QWIM: Callable[..., None], launch_copy_workflow_QWIM: Callable[..., list[Path]], logger: Any) -> int:
	"""CLI entry-point for the selective copy workflows."""
	parser = argparse.ArgumentParser(
		description="Copy one curated QWIM project bundle into another folder or launch the GUI.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	parser.add_argument(
		"workflow",
		nargs="?",
		choices=("student-projects", "posit-connect", "my-projects"),
		help="Copy workflow to execute. Omit to launch the GUI.",
	)
	parser.add_argument(
		"--gui",
		action="store_true",
		help="Launch the tkinter workflow selector instead of running one CLI workflow.",
	)
	parser.add_argument(
		"--target-dir",
		dest="target_dir",
		default=None,
		help="Existing destination project folder. When omitted, a folder picker is shown.",
	)
	parser.add_argument(
		"--source-root",
		dest="source_root",
		default=None,
		help="Optional explicit source project root. Defaults to the current repository root.",
	)
	args = parser.parse_args(argv)

	try:
		if args.gui and args.workflow is not None:
			raise Exception_Validation_Input(
				"Cannot combine --gui with a workflow name.",
				field_name="workflow",
				actual_value=args.workflow,
			)

		if args.gui and args.target_dir is not None:
			raise Exception_Validation_Input(
				"Cannot combine --gui with --target-dir.",
				field_name="target_dir",
				actual_value=args.target_dir,
			)

		if args.gui or args.workflow is None:
			launch_copy_gui_QWIM(source_root=args.source_root)
		else:
			launch_copy_workflow_QWIM(
				workflow_name = args.workflow,
				target_dir=args.target_dir,
				source_root=args.source_root,
			)
	except (
		Exception_Configuration,
		Exception_File_Operation,
		Exception_Not_Found,
		Exception_Security_Violation,
		Exception_Validation_Input,
	) as copy_error:
		logger.error("%s", copy_error)
		return 1

	return 0