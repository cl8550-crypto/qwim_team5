"""Orchestrator: regenerate all regression baseline artefacts.

Discovers every ``generate_baselines.py`` script under
``tests/regression_data/`` and runs each one in sequence using the same
Python interpreter that invoked this script.

Usage
-----
Regenerate all baselines from the project root::

    python tests/regression_data/generate_regression_baselines.py

Regenerate a specific subsystem only::

    python tests/regression_data/generate_regression_baselines.py --subsystem simulation

List subsystems without running anything::

    python tests/regression_data/generate_regression_baselines.py --list

Exit codes
----------
0 : all generators succeeded
1 : one or more generators failed (failures are listed at the end)
2 : invalid subsystem name supplied via --subsystem

Author
------
QWIM Team

Version
-------
0.1.0 (2026-05-17)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Path setup — must precede any imports from src/
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REGRESSION_DATA = Path(__file__).resolve().parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(name=__name__)


def _discover_generators(subsystem: str | None = None) -> list[Path]:
    """Return sorted list of generate_baselines.py paths to run.

    Parameters
    ----------
    subsystem : str | None
        When provided, only return the generator for that specific subsystem.

    Returns
    -------
    list[Path]
        Paths to generator scripts, sorted alphabetically by subsystem name.
    """
    generators = sorted(_REGRESSION_DATA.glob("*/generate_baselines.py"))

    if subsystem is not None:
        matched = [g for g in generators if g.parent.name == subsystem]
        return matched

    return generators


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _run_generator(script: Path) -> tuple[str, bool, str]:
    """Run a single generator script.

    Parameters
    ----------
    script : pathlib.Path
        Absolute path to the generator script to execute.

    Returns
    -------
    tuple[str, bool, str]
        (subsystem_name, success_flag, captured_stderr_on_failure)
    """
    subsystem = script.parent.name
    print(f"  [{subsystem}] Generating baselines ...", flush=True)

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode == 0:
        print(f"  [{subsystem}] OK", flush=True)
        return subsystem, True, ""
    else:
        print(f"  [{subsystem}] FAILED (exit {result.returncode})", flush=True)
        return subsystem, False, result.stderr or result.stdout


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(
    *,
    subsystem: str | None,
    list_only: bool,
) -> int:
    """Run all (or one) baseline generator(s).

    Parameters
    ----------
    subsystem : str | None
        When provided, only run the generator for that specific subsystem.
    list_only : bool
        If True, list discovered generator scripts without running them.

    Returns
    -------
    int
        0 on full success, 1 on partial failure, 2 on bad --subsystem.
    """
    generators = _discover_generators(subsystem)

    if subsystem is not None and not generators:
        known = sorted(p.parent.name for p in _discover_generators())
        print(
            f"ERROR: No generate_baselines.py found for subsystem '{subsystem}'.\n"
            f"Known subsystems: {', '.join(known)}",
            file=sys.stderr,
        )
        return 2

    if list_only:
        print("Discovered regression baseline generators:")
        for g in generators:
            print(f"  {g.relative_to(_PROJECT_ROOT)}")
        return 0

    print(
        f"\nRegenerating baselines for {len(generators)} subsystem(s)...\n",
        flush=True,
    )

    failures: list[tuple[str, str]] = []
    for script in generators:
        name, ok, err = _run_generator(script)
        if not ok:
            failures.append((name, err))

    print()
    if not failures:
        print(f"All {len(generators)} generator(s) completed successfully.")
        print(
            "\nNOTE: If you changed source behaviour, commit the updated baseline "
            "artefacts so regression tests reflect the new expected values."
        )
        return 0

    print(f"FAILED: {len(failures)} of {len(generators)} generator(s) failed:\n")
    for name, err in failures:
        print(f"  {name}:")
        for line in (err or "(no output)").splitlines()[-10:]:
            print(f"    {line}")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Regenerate all regression baseline artefacts."
    )
    parser.add_argument(
        "--subsystem",
        default=None,
        help="Only regenerate baselines for this subsystem (e.g. simulation).",
    )
    parser.add_argument(
        "--list",
        dest="list_only",
        action="store_true",
        help="List discovered generator scripts without running them.",
    )
    args = parser.parse_args()
    sys.exit(main(subsystem=args.subsystem, list_only=args.list_only))
