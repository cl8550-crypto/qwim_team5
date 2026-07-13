"""Local conftest for dashboard Playwright tests.

Overrides the session-wide ``browser_context_args`` fixture to drop the
``storage_state`` entry that causes ``FileNotFoundError`` on first-run
contexts.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """Drop ``storage_state`` so the first context creation never fails.

    The parent ``tests_shiny/conftest.py`` fixture points ``storage_state``
    at a JSON file written by a *prior* context on teardown.  When this
    module is the first to create a context, the file does not exist and
    Playwright raises ``FileNotFoundError``.  Removing the key keeps the
    test self-contained.
    """
    args = dict(browser_context_args)
    args.pop("storage_state", None)
    return args
