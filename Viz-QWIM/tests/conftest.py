"""
Pytest configuration and fixtures for the entire test suite.

This module provides shared fixtures and configuration used across
all test modules in the project.
"""

import sys  # MUST be first import to enable UTF-8 encoding fix


# CRITICAL: Force UTF-8 encoding for all I/O on Windows BEFORE any other imports
# This prevents UnicodeEncodeError when logging special characters during tests
if sys.platform == "win32":
    import os as _os_for_encoding

    # Set environment variable for subprocess and future operations
    _os_for_encoding.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # Force UTF-8 for default encoding
    if hasattr(sys, "_enablelegacywindowsfsencoding"):
        sys._enablelegacywindowsfsencoding = lambda: None

    # Reconfigure all existing standard streams to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Custom exception hook for UTF-8 safe error handling
    import io

    _original_excepthook = sys.excepthook

    def _utf8_safe_excepthook(exc_type, exc_value, exc_traceback):
        """Exception hook that safely handles Unicode characters on Windows."""
        import traceback

        try:
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            message = "".join(lines)
            stderr_utf8 = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            stderr_utf8.write(message)
            stderr_utf8.flush()
        except Exception:
            try:
                _original_excepthook(exc_type, exc_value, exc_traceback)
            except Exception:
                print(f"Error: {exc_type.__name__}: {exc_value}", file=sys.stderr)

    sys.excepthook = _utf8_safe_excepthook

# Now safe to import other modules
from pathlib import Path

import pytest


# ============================================================================
# Path Configuration
# ============================================================================


# Ensure the project root is in the Python path for imports.
# NOTE: Only the project root is added to sys.path — NOT src/.
# This ensures all test imports use the `src.` package prefix
# (e.g., `from src.portfolios.portfolio_QWIM import Portfolio_QWIM`)
# which is the canonical import path and the one coverage.py tracks.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# WMI-safe platform guard  +  faulthandler watchdog
# ============================================================================
# CRITICAL (Windows / Python 3.13): ``import polars`` calls platform.machine()
# at module top, which resolves through a WMI query.  If the host's WMI service
# is hung, every polars import (and thus pytest collection) blocks forever with
# no output.  Seed platform._uname_cache *before* any test module imports
# polars to make that call return instantly.  No-op on Linux/Posit.
from src.utils.custom_exceptions_errors_loggers.platform_utils import (  # noqa: E402
    seed_uname_cache_for_windows,
)

seed_uname_cache_for_windows()

# Enable a faulthandler watchdog so any *future* hang dumps a stack trace to
# stderr instead of silently blocking.  Timeout is configurable via the
# PYTEST_FAULTHANDLER_TIMEOUT env var (seconds); 0/unset disables the dump.
import faulthandler as _faulthandler  # noqa: E402
import os as _os_for_watchdog  # noqa: E402

_faulthandler_timeout = float(
    _os_for_watchdog.environ.get("PYTEST_FAULTHANDLER_TIMEOUT", "0")
)
if _faulthandler_timeout > 0:  # pragma: no cover - opt-in diagnostic path
    _faulthandler.dump_traceback_later(_faulthandler_timeout, repeat=True)


# ============================================================================
# Logging isolation for the test run
# ============================================================================
# CRITICAL: Multiple test modules (e.g. ``src.dashboard.shiny_utils.utils_data``)
# call ``get_logger(name=__name__)`` at module-import time.  The first such
# call auto-configures logging with the default ``./logs/`` directory and starts
# opening ``debug.log``.  When a later test fixture then calls
# ``setup_logging(log_dir=temp_log_dir, ...)``, the previous handlers are
# removed but the underlying file may still be in mid-rotation by loguru,
# producing ``PermissionError: [WinError 32]`` noise on every test run.
#
# Fix: redirect the auto-configured log directory to a session-scoped temp dir
# at conftest import time (which happens *before* test collection), so any
# subsequent ``get_logger()`` call inside an imported test module picks up
# the redirected directory.  This keeps the project's persistent ``./logs/``
# untouched and avoids concurrent rotation races on a shared ``debug.log``.
import os as _os_for_log_redirect  # noqa: E402
import tempfile as _tempfile_for_log  # noqa: E402

# Honour an explicit caller override via env var (used by some CI pipelines).
_qwim_test_log_dir = _os_for_log_redirect.environ.get(
    "QWIM_TEST_LOG_DIR",
    _tempfile_for_log.mkdtemp(prefix="qwim_test_logs_"),
)
try:
    # Configure loguru to write to the per-session temp dir BEFORE any
    # application module is imported.  Console + JSON are disabled to
    # keep pytest output clean and fast.
    from src.utils.custom_exceptions_errors_loggers.logger_custom import (  # noqa: E402
        setup_logging,
    )

    setup_logging(
        log_level="DEBUG",
        environment="development",
        log_dir=_qwim_test_log_dir,
        enable_console=False,
        enable_JSON=False,
    )
except Exception:  # pragma: no cover - defensive, never fail test setup
    # Logging is auxiliary to testing; a misconfiguration here must not
    # abort the entire test run.
    pass


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fast, isolated, no external dependencies)",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (may use external resources)",
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (excluded from regular test runs unless specified)",
    )
    config.addinivalue_line(
        "markers",
        "regression: marks tests as regression tests (compare against known benchmark values)",
    )
    config.addinivalue_line(
        "markers",
        "windows_only: marks tests that only run on Windows (skipped automatically on Linux)",
    )
    config.addinivalue_line(
        "markers",
        "linux_only: marks tests that only run on Linux/Posit (skipped automatically on Windows)",
    )


def pytest_runtest_setup(item):
    """Auto-skip tests marked windows_only or linux_only on the wrong platform."""
    for _ in item.iter_markers(name="windows_only"):
        if sys.platform != "win32":
            pytest.skip("Skipped: windows_only test (not on Windows)")
    for _ in item.iter_markers(name="linux_only"):
        if sys.platform == "win32":
            pytest.skip("Skipped: linux_only test (not on Linux/Posit)")


# ============================================================================
# Common Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory path.

    Returns
    -------
    Path
        Absolute path to the project root directory.
    """
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_directory(project_root):
    """Return the src directory path.

    Returns
    -------
    Path
        Absolute path to the src directory.
    """
    return project_root / "src"


@pytest.fixture(scope="session")
def inputs_directory(project_root):
    """Return the inputs directory path.

    Returns
    -------
    Path
        Absolute path to the inputs directory.
    """
    return project_root / "inputs"


@pytest.fixture(scope="session")
def outputs_directory(project_root):
    """Return the outputs directory path.

    Returns
    -------
    Path
        Absolute path to the outputs directory.
    """
    return project_root / "outputs"


@pytest.fixture()
def temp_workspace(tmp_path):
    """Create a temporary workspace with standard directory structure.

    Returns
    -------
    dict
        Dictionary containing paths to temporary directories.
    """
    # Create standard project structure
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "inputs" / "raw").mkdir(parents=True)
    (tmp_path / "inputs" / "processed").mkdir(parents=True)
    (tmp_path / "outputs").mkdir(parents=True)

    return {
        "root": tmp_path,
        "data_raw": tmp_path / "data" / "raw",
        "data_processed": tmp_path / "data" / "processed",
        "inputs_raw": tmp_path / "inputs" / "raw",
        "inputs_processed": tmp_path / "inputs" / "processed",
        "outputs": tmp_path / "outputs",
    }


# ============================================================================
# Test Skip Conditions
# ============================================================================


@pytest.fixture()
def skip_if_no_network():
    """Skip test if no network connection available."""
    import socket

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        pytest.skip("No network connection available")


@pytest.fixture()
def skip_if_no_matplotlib():
    """Skip test if matplotlib is not installed."""
    try:
        import matplotlib
    except ImportError:
        pytest.skip("matplotlib not installed")


# ============================================================================
# Polars / financial data fixtures  (shared across all test layers)
# ============================================================================


@pytest.fixture(scope="session")
def sample_tickers() -> list[str]:
    """Return the canonical list of QWIM ETF tickers.

    Returns
    -------
    list[str]
        Ticker symbols used across regression and unit fixtures.
    """
    return ["IVV", "IJH", "IWM", "EFA", "EEM", "AGG", "SPTL", "HYG", "SPBO", "IYR", "DBC", "GLD"]


@pytest.fixture(scope="session")
def sample_returns_polars(sample_tickers):
    """Deterministic daily-return ``pl.DataFrame`` (seed=42, 252 rows).

    Shape: (252, len(sample_tickers)).
    Column names match *sample_tickers*.
    Values are drawn from N(0.0005, 0.015) — representative equity daily returns.

    Returns
    -------
    pl.DataFrame
        252 × 12 Polars DataFrame of simulated daily log-returns.
    """
    import numpy as np
    import polars as pl

    rng = np.random.default_rng(42)
    n_periods = 252
    data = rng.normal(0.0005, 0.015, size=(n_periods, len(sample_tickers)))
    return pl.DataFrame(
        {ticker: data[:, i].tolist() for i, ticker in enumerate(sample_tickers)},
    )


@pytest.fixture(scope="session")
def sample_weights_polars(sample_tickers):
    """Equal-weight portfolio as a single-row ``pl.DataFrame``.

    Returns
    -------
    pl.DataFrame
        1 × 12 Polars DataFrame with equal weights summing to 1.0.
    """
    import polars as pl

    n = len(sample_tickers)
    w = 1.0 / n
    return pl.DataFrame({ticker: [w] for ticker in sample_tickers})


@pytest.fixture()
def temp_parquet_dir(tmp_path):
    """Temporary directory pre-created for parquet I/O tests.

    Returns
    -------
    pathlib.Path
        Absolute path to an empty temporary directory.
    """
    parquet_dir = tmp_path / "parquet"
    parquet_dir.mkdir()
    return parquet_dir


@pytest.fixture()
def frozen_clock():
    """Freeze time at 2026-01-15T12:00:00 UTC for deterministic time tests.

    Requires ``freezegun``.  Tests that use this fixture will see a stable
    ``datetime.now()`` / ``date.today()`` regardless of when they run.

    Yields
    ------
    freezegun.api.FakeDatetime
        The frozen datetime class (rarely needed directly).
    """
    try:
        from freezegun import freeze_time
    except ImportError:
        pytest.skip("freezegun not installed")

    with freeze_time("2026-01-15T12:00:00+00:00") as frozen:
        yield frozen


@pytest.fixture()
def mock_yfinance(monkeypatch):
    """Monkeypatch ``yfinance.download`` to return deterministic data.

    Prevents any real network calls in unit tests.  The fake download returns
    a small ``pandas.DataFrame`` whose ``Adj Close`` sub-columns match the
    canonical ETF tickers so that ``get_etf_data`` can convert it to polars.

    Yields
    ------
    unittest.mock.MagicMock
        The patched ``yfinance.download`` callable.

    Returns
    -------
    pl.DataFrame
        Deterministic 5-row price table (via the real ``get_etf_data`` path).
    """
    import numpy as np

    try:
        import pandas as pd
        import yfinance  # noqa: F401
    except ImportError:
        pytest.skip("yfinance or pandas not installed")

    tickers = ["IVV", "IJH", "IWM", "EFA", "EEM", "AGG", "SPTL", "HYG", "SPBO", "IYR", "DBC", "GLD"]
    rng = np.random.default_rng(0)
    prices = rng.uniform(50, 500, size=(5, len(tickers)))
    dates = pd.date_range("2025-01-01", periods=5, freq="B")

    # Build multi-level DataFrame that mirrors yfinance bulk-download output
    adj_close_df = pd.DataFrame(
        prices,
        index=dates,
        columns=pd.MultiIndex.from_product([["Adj Close"], tickers]),
    )
    adj_close_df.index.name = "Date"

    def _fake_download(*args, **kwargs):  # noqa: ANN002, ANN003
        return adj_close_df

    monkeypatch.setattr("yfinance.download", _fake_download)
    yield _fake_download
