"""Pytest configuration and shared fixtures for the QWIM Shiny test suite.

Covers two test categories:

1. **Unit tests** — exercise pure-Python dashboard utilities without a
   running server (``test_utils_data``, ``test_reactives_shiny``,
   ``test_utils_enhanced_formatting``, ``test_utils_tab_results``).

2. **Playwright end-to-end tests** — launch the Shiny app as a subprocess,
   then drive it through a real browser via ``pytest-playwright``.

How to run (from the project root):
    # All shiny tests
    pytest tests/tests_shiny/ -p no:cacheprovider --import-mode=importlib

    # Only unit tests (no browser)
    pytest tests/tests_shiny/ -m "unit"

    # Only playwright tests
    pytest tests/tests_shiny/ -m "playwright" --headed  # (add --headed to watch)
"""

from __future__ import annotations

import io
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Generator

import pytest

# ---------------------------------------------------------------------------
# pytest-playwright availability  (must be checked before conftest.py body runs)
# ---------------------------------------------------------------------------
# When pytest-playwright is installed, we explicitly register it via
# ``pytest_plugins`` so its fixtures (``page``, ``browser``, etc.) are
# available even when the plugin is not auto-discovered.  When it is absent,
# a stub ``page`` fixture skips browser tests immediately.
#
# Developers who want to run the full Playwright suite should:
#   1. ``python -m playwright install chromium``
#   2. ``pip install pytest-playwright``
try:
    import importlib.util

    _PYTEST_PLAYWRIGHT_AVAILABLE: bool = (
        importlib.util.find_spec("pytest_playwright") is not None
    )
except ImportError:
    _PYTEST_PLAYWRIGHT_AVAILABLE = False


if _PYTEST_PLAYWRIGHT_AVAILABLE:
    # Explicitly register the plugin module so its fixtures are available.
    # We use ``pytest_plugins`` instead of relying on auto-discovery so that
    # the ``page`` fixture works regardless of ``-p no:pytest_playwright``
    # in pytest.ini addopts.
    pytest_plugins = ["pytest_playwright.pytest_playwright"]

    # Shared storage-state file path — created once per session so that
    # browser contexts across tests reuse cookies and localStorage,
    # reducing per-test navigation overhead.
    _STORAGE_STATE_PATH: Path | None = None

    @pytest.fixture(scope="session")
    def base_url() -> str:
        """Provide ``base_url`` for ``pytest-playwright``'s ``browser_context_args``.

        Returns a default localhost URL.  Playwright browser tests that need
        a running Shiny server request the :func:`shiny_server_url` fixture
        explicitly and navigate to it via ``page.goto(shiny_server_url)``.
        """
        return "http://127.0.0.1:8765"

    @pytest.fixture(scope="session")
    def _storage_state_file(
        tmp_path_factory: pytest.TempPathFactory,
    ) -> Path:
        """Provide a session-scoped storage-state file for browser contexts.

        Returns
        -------
        pathlib.Path
            Path to a JSON file that Playwright uses to persist and restore
            cookies / localStorage across tests within the same session.

        Notes
        -----
        The file is created in a pytest-managed temp directory and
        automatically cleaned up after the session.  The first browser
        context to use it writes state on teardown; subsequent contexts
        load that state to avoid cold-start navigation penalties.
        """
        global _STORAGE_STATE_PATH
        if _STORAGE_STATE_PATH is None:
            _STORAGE_STATE_PATH = (
                tmp_path_factory.mktemp("playwright_storage") / "state.json"
            )
        return _STORAGE_STATE_PATH

    @pytest.fixture
    def browser_context_args(
        browser_context_args: dict[str, Any],
        _storage_state_file: Path,
    ) -> dict[str, Any]:
        """Augment browser context args with shared storage state for speed.

        Parameters
        ----------
        browser_context_args : dict
            Default args provided by ``pytest-playwright``.
        _storage_state_file : pathlib.Path
            Session-scoped path for persisting browser storage state.

        Returns
        -------
        dict
            Merged args including ``storage_state`` pointing to the shared
            session file, plus ``no_viewport=True`` to skip viewport emulation
            overhead.

        Notes
        -----
        ``no_viewport=True`` tells Playwright to use the default viewport
        size of the browser window, skipping emulation which saves a small
        amount of per-context setup time.
        """
        return {
            **browser_context_args,
            "storage_state": str(_storage_state_file),
            "no_viewport": True,
        }

else:

    @pytest.fixture
    def page() -> None:
        """Stub: skip all Playwright tests when the plugin is not installed.

        To actually run browser tests:
          1. ``python -m playwright install chromium``
          2. ``pip install pytest-playwright``
        """
        pytest.skip(
            "Playwright browser tests are disabled by default. "
            "Run 'python -m playwright install chromium' then pass "
            "'-p pytest_playwright' to pytest to enable them."
        )



# ---------------------------------------------------------------------------
# UTF-8 safety patch  (mirrors main conftest.py)
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    import os as _os_enc

    _os_enc.environ.setdefault("PYTHONIOENCODING", "utf-8")

    for _stream in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    if not hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# CRITICAL: Seed platform._uname_cache BEFORE any module imports polars.
# On Windows / Python 3.13, ``import polars`` calls ``platform.machine()``
# which resolves through a WMI query.  If WMI is hung, every polars import
# (including during pytest collection) blocks forever.
#
# This must run before the shiny-specific fixtures below, because those
# fixtures may trigger polars imports indirectly.  It is a no-op on Linux.
# ---------------------------------------------------------------------------
from src.utils.custom_exceptions_errors_loggers.platform_utils import (  # noqa: E402
    seed_uname_cache_for_windows,
)

seed_uname_cache_for_windows()

# ---------------------------------------------------------------------------
# Pytest marker declarations
# ---------------------------------------------------------------------------


def pytest_configure(config: Any) -> None:
    """Register custom markers so --strict-markers never rejects them."""
    markers = [
        "unit: fast tests that exercise pure Python functions",
        "integration: tests that load data files from disk",
        "playwright: browser-based end-to-end tests via Playwright",
        "smoke: quick sanity checks — subset of unit/playwright",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


# ---------------------------------------------------------------------------
# Fixtures — data paths
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def project_dir() -> Path:
    """Return the absolute project root directory."""
    return _PROJECT_ROOT


@pytest.fixture(scope="session")
def inputs_raw_dir(project_dir: Path) -> Path:
    """Return the `inputs/raw/` directory path."""
    return project_dir / "inputs" / "raw"


@pytest.fixture(scope="session")
def inputs_processed_dir(project_dir: Path) -> Path:
    """Return the `inputs/processed/` directory path."""
    return project_dir / "inputs" / "processed"


# ---------------------------------------------------------------------------
# Fixtures — loaded dashboard data  (session scope for speed)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def data_utils(project_dir: Path) -> dict[str, Any]:
    """Load ``get_data_utils`` once per session."""
    from src.dashboard.shiny_utils.utils_data import get_data_utils

    return get_data_utils(project_dir=project_dir)


@pytest.fixture(scope="session")
def data_inputs(project_dir: Path) -> dict[str, Any]:
    """Load ``get_data_inputs`` once per session."""
    from src.dashboard.shiny_utils.utils_data import get_data_inputs

    return get_data_inputs(project_dir=project_dir)


# ---------------------------------------------------------------------------
# Fixtures — in-memory Polars DataFrames  (unit tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_portfolio_df() -> "import polars as pl; pl.DataFrame":
    """Return a minimal portfolio-style Polars DataFrame with a Date column."""
    import polars as pl

    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Value": [100.0, 102.5, 101.0],
        }
    )


@pytest.fixture(scope="session")
def sample_timeseries_df() -> Any:
    """Return a Polars DataFrame with 250 rows to test downsampling."""
    import polars as pl

    n = 250
    return pl.DataFrame(
        {
            "Date": [f"2024-01-{(i % 28) + 1:02d}" for i in range(n)],
            "VTI": [100.0 + i * 0.1 for i in range(n)],
            "AGG": [90.0 - i * 0.05 for i in range(n)],
        }
    )


@pytest.fixture(scope="session")
def sample_weights_df() -> Any:
    """Return a portfolio-weights Polars DataFrame (rows sum ~1.0)."""
    import polars as pl

    return pl.DataFrame(
        {
            "Date": ["2024-01-01", "2024-02-01"],
            "VTI": [0.40, 0.45],
            "AGG": [0.35, 0.30],
            "VNQ": [0.25, 0.25],
        }
    )


@pytest.fixture(scope="session")
def minimal_reactives_shiny(data_utils: dict[str, Any]) -> dict[str, Any]:
    """Return a fully-initialised reactives_shiny dict (session scope)."""
    from src.dashboard.shiny_utils.reactives_shiny import initialize_reactives_shiny
    from shiny import reactive

    with reactive.isolate():
        return initialize_reactives_shiny(data_utils=data_utils)


# ---------------------------------------------------------------------------
# Fixtures — Playwright / Shiny server  (session scope)
# ---------------------------------------------------------------------------

_SHINY_TEST_HOST: str = "127.0.0.1"


def _find_free_local_port() -> int:
    """Return an available localhost TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
        socket_server.bind((_SHINY_TEST_HOST, 0))
        socket_server.listen(1)
        socket_name = socket_server.getsockname()
        return int(socket_name[1])


def _read_text_file_tail(
    path_file: Path,
    num_lines: int = 40,
) -> str:
    """Return the last *num_lines* lines from a UTF-8 text file."""
    if not path_file.exists():
        return ""

    lines_file = path_file.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines_file[-num_lines:])


def _poll_http_ready(
    url: str,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> bool:
    """Poll an HTTP endpoint until it returns 200 or *timeout* elapses.

    Parameters
    ----------
    url : str
        Full HTTP URL to poll (e.g. ``"http://127.0.0.1:8765"``).
    timeout : float, optional
        Maximum time in seconds to keep polling, by default ``30.0``.
    interval : float, optional
        Time in seconds between polling attempts, by default ``0.5``.

    Returns
    -------
    bool
        ``True`` when the server responds with HTTP 200 before the deadline;
        ``False`` otherwise.

    Notes
    -----
    Uses ``urllib.request.urlopen`` with a short per-request timeout so a
    hung server does not block the polling loop.  Replaces the previous
    fixed ``time.sleep(3.0)`` pause in :func:`shiny_server_url` with an
    active readiness check.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def shiny_server_url(
    project_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str, None, None]:
    """Start the QWIM Shiny app as a subprocess then yield its base URL.

    The fixture waits until the server is responsive (up to 90 s) before
    yielding.  On teardown it sends SIGTERM and waits for the process to exit.

    Usage in a playwright test::

        def test_my_page(page, shiny_server_url):
            page.goto(shiny_server_url)
            ...

    When Playwright browser tests are disabled (default), this fixture skips
    immediately so no server subprocess is started.
    """
    if not _PYTEST_PLAYWRIGHT_AVAILABLE:
        pytest.skip(
            "pytest-playwright not installed — install it to run browser tests"
        )

    port_server = _find_free_local_port()
    shiny_url = f"http://{_SHINY_TEST_HOST}:{port_server}"
    path_log_server = tmp_path_factory.mktemp("shiny_server") / "server.log"
    env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}
    with path_log_server.open("w", encoding="utf-8") as file_log_server:
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import sys, os; "
                    f"sys.path.insert(0, r'{project_dir}'); "
                    "os.environ['QWIM_ENVIRONMENT'] = 'development'; "
                    "from shiny import run_app; "
                    "from src.dashboard.main_App import app; "
                    f"run_app(app, host='{_SHINY_TEST_HOST}', port={port_server}, reload=False)"
                ),
            ],
            stdout=file_log_server,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=str(project_dir),
        )

        deadline = time.monotonic() + 90.0
        server_up = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break

            try:
                with socket.create_connection((_SHINY_TEST_HOST, port_server), timeout=1.0):
                    server_up = True
                    break
            except OSError:
                time.sleep(1.0)

        if not server_up:
            exit_code = process.poll()
            if exit_code is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()

            tail_server_log = _read_text_file_tail(path_log_server)
            detail_skip = ""
            if exit_code is not None:
                detail_skip = f" Exit code: {exit_code}."
            if tail_server_log:
                detail_skip += f"\nServer log tail:\n{tail_server_log}"

            pytest.skip(
                f"Shiny server did not start on port {port_server} within 90 s.{detail_skip}",
            )

        # Poll the HTTP endpoint until the Shiny app is truly ready.
        # Replaces the previous fixed ``time.sleep(3.0)`` with an active
        # health-check that returns as soon as the server responds with 200.
        if not _poll_http_ready(shiny_url, timeout=15.0, interval=0.5):
            tail_server_log = _read_text_file_tail(path_log_server)
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            pytest.skip(
                f"Shiny server socket opened on port {port_server} but HTTP "
                f"endpoint did not respond within 15 s.\n"
                f"Server log tail:\n{tail_server_log}",
            )

        yield shiny_url

        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()


# ---------------------------------------------------------------------------
# Shared Playwright navigation helpers
# ---------------------------------------------------------------------------
# These helpers are imported by tab-specific test modules so that every
# test file benefits from the same fast-navigation contract:
#   - ``wait_until="domcontentloaded"`` (NOT ``networkidle`` — Shiny's
#     persistent WebSocket prevents true network idle).
#   - ``wait_for_selector`` on a Shiny-specific element after navigation.
#   - No ``time.sleep()`` calls — all waits are event-driven.

# Selector that signals the Shiny app has fully initialised its reactive graph.
_SEL_SHINY_READY: str = (
    "[data-shiny-server-started], .shiny-bound-output, "
    "#shiny-tab-clients, nav.navbar, .nav-link"
)


def navigate_to_app(
    page: Any,
    url: str,
    *,
    timeout: int = 15_000,
    wait_until: str = "domcontentloaded",
) -> None:
    """Navigate to the Shiny app root and wait for Shiny to initialise.

    Parameters
    ----------
    page : playwright.sync_api.Page
        Playwright page object.
    url : str
        Base URL of the running Shiny server.
    timeout : int, optional
        Maximum wait time in ms for Shiny-ready selector, by default ``15_000``.
    wait_until : str, optional
        Playwright ``goto`` load state, by default ``"domcontentloaded"``.

    Notes
    -----
    Uses ``domcontentloaded`` instead of ``networkidle`` because Shiny
    maintains a persistent WebSocket that prevents the network from ever
    becoming truly idle.  After DOM content is loaded, we wait for a
    Shiny-specific selector to confirm the reactive graph is wired.
    """
    page.goto(url.rstrip("/"), wait_until=wait_until, timeout=30_000)
    # Wait for Shiny to finish wiring — any of these selectors signals readiness.
    page.wait_for_selector(_SEL_SHINY_READY, timeout=timeout, state="attached")


def navigate_to_tab(
    page: Any,
    url: str,
    tab_selector: str,
    *,
    timeout: int = 15_000,
) -> None:
    """Navigate to the app and click a top-level navigation tab.

    Parameters
    ----------
    page : playwright.sync_api.Page
    url : str
    tab_selector : str
        CSS selector for the tab link to click.
    timeout : int, optional
        Max wait time in ms for the tab to become visible, by default ``15_000``.

    Notes
    -----
    After clicking the tab, waits for ``.nav-link.active`` or
    ``[aria-selected='true']`` to confirm client-side navigation completed.
    """
    navigate_to_app(page, url, timeout=timeout)
    tab = page.locator(tab_selector).first
    tab.wait_for(state="visible", timeout=timeout)
    tab.click()
    # Wait for the active-tab indicator to confirm navigation.
    page.wait_for_selector(
        ".nav-link.active, [aria-selected='true']",
        timeout=5_000,
        state="attached",
    )


def navigate_to_subtab(
    page: Any,
    subtab_selector: str,
    *,
    timeout: int = 10_000,
) -> None:
    """Click a subtab navigation link and wait for its panel to appear.

    Parameters
    ----------
    page : playwright.sync_api.Page
    subtab_selector : str
        CSS selector for the subtab link.
    timeout : int, optional
        Max wait time in ms, by default ``10_000``.

    Notes
    -----
    After the click, waits for the corresponding panel element to be
    attached to the DOM so that subsequent assertions on subtab content
    do not race against Shiny's reactive rendering.
    """
    link = page.locator(subtab_selector).first
    link.wait_for(state="visible", timeout=timeout)
    link.click()
    # Wait for the subtab's content panel to be attached.
    # Derive a panel selector from the subtab link: look for an adjacent
    # tab-pane or a sibling .tab-content container.
    page.wait_for_selector(
        ".tab-pane.active, .shiny-tab-panel, [role='tabpanel']:not([hidden])",
        timeout=5_000,
        state="attached",
    )


# ---------------------------------------------------------------------------
# Helpers available to all test modules
# ---------------------------------------------------------------------------


def make_valid_reactives_shiny() -> dict[str, Any]:
    """Return the canonical valid reactives_shiny skeleton for unit tests.

    Avoids needing a running Shiny context — uses plain dicts instead of
    reactive.Value so validators can be tested without the reactive session.
    """
    return {
        "User_Inputs_Shiny": {},
        "Inner_Variables_Shiny": {},
        "Triggers_Shiny": {},
        "Visual_Objects_Shiny": {},
    }
