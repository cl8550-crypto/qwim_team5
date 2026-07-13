"""Robot Framework keyword library for get_data_ETFs tests."""

from __future__ import annotations

import io
import sys
import tempfile

from datetime import date as _date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import polars as pl


_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")  # type: ignore[assignment]


MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    import src.utils.data_utils.get_data_ETFs as get_data_etfs_module
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(f"get_data_ETFs could not be imported: {_import_error_message}")


def _build_fake_module_path(depth: int) -> Path:
    """Create a fake module path whose fallback root resolves to a temp directory."""
    tmp_dir = Path(tempfile.mkdtemp())
    fake_path = tmp_dir
    for index in range(depth):
        fake_path = fake_path / chr(ord("a") + index)
    fake_path.mkdir(parents=True, exist_ok=True)
    fake_file = fake_path / "get_data_ETFs.py"
    fake_file.touch()
    return fake_file


def _make_bulk_download_frame(tickers: list[str]) -> pd.DataFrame:
    """Build a MultiIndex pandas DataFrame matching the yfinance bulk shape."""
    index = pd.date_range("2024-01-02", periods=3, freq="B")
    data: dict[tuple[str, str], list[float]] = {}
    for ticker_index, ticker in enumerate(tickers):
        data[(ticker, "Close")] = [
            100.0 + ticker_index * 10 + row_index for row_index in range(3)
        ]
    frame = pd.DataFrame(data, index=index)
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)
    return frame


def _make_main_frame() -> pl.DataFrame:
    """Build a small deterministic polars DataFrame for main()."""
    return pl.DataFrame(
        {
            "Date": [_date(2024, 1, 2), _date(2024, 1, 3)],
            "IVV": [450.0, 451.0],
            "AGG": [100.0, 100.1],
        },
    )


def module_is_importable() -> bool:
    """Return True if get_data_ETFs can be imported."""
    return MODULE_IMPORT_AVAILABLE


def mocked_etf_retrieval_has_expected_columns() -> None:
    """Assert a mocked ETF retrieval preserves the requested public columns."""
    _require_imports()
    get_data_etfs_module._ETF_CACHE.clear()
    with patch(
        "yfinance.download",
        return_value=_make_bulk_download_frame(["SPY", "QQQ"]),
    ):
        result = get_data_etfs_module.get_etf_data(
            tickers=["SPY", "QQQ"],
            start_date="2024-01-02",
            end_date="2024-01-05",
        )

    assert result.columns == ["Date", "SPY", "QQQ"]


def main_writes_etf_csv_in_temp_root() -> None:
    """Assert main() writes the expected ETF CSV under a temporary project root."""
    _require_imports()
    fake_file = _build_fake_module_path(depth=2)
    original_file = get_data_etfs_module.__file__
    try:
        get_data_etfs_module.__file__ = str(fake_file)
        with patch.object(get_data_etfs_module, "get_etf_data", return_value=_make_main_frame()):
            get_data_etfs_module.main()
    finally:
        get_data_etfs_module.__file__ = original_file

    output_file = fake_file.parents[2] / "inputs" / "raw" / "data_ETFs.csv"
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def reversed_requests_preserve_requested_ticker_order() -> None:
    """Assert reversed ETF requests keep their own column order."""
    _require_imports()
    get_data_etfs_module._ETF_CACHE.clear()
    with patch(
        "yfinance.download",
        side_effect=[
            _make_bulk_download_frame(["SPY", "QQQ"]),
            _make_bulk_download_frame(["QQQ", "SPY"]),
        ],
    ):
        forward_result = get_data_etfs_module.get_etf_data(
            tickers=["SPY", "QQQ"],
            start_date="2024-01-02",
            end_date="2024-01-05",
        )
        reverse_result = get_data_etfs_module.get_etf_data(
            tickers=["QQQ", "SPY"],
            start_date="2024-01-02",
            end_date="2024-01-05",
        )

    assert forward_result.columns == ["Date", "SPY", "QQQ"]
    assert reverse_result.columns == ["Date", "QQQ", "SPY"]