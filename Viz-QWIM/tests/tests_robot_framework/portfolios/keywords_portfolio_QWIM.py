"""Robot Framework keyword library for portfolio_QWIM and utils_portfolio tests.

Tests cover
-----------
Keyword wrappers for portfolio_QWIM construction from component names and
weights DataFrames, property access (name, count, components, raw weights),
weight-sum validation, and end-to-end portfolio value calculation via
calculate_portfolio_values and create_benchmark_portfolio_values.

Also covers utils_portfolio functions: create_sample_portfolio_weights,
CSV round-trip, create_custom_portfolio, suggest_component_matches,
ensure_path_exists, and portfolio_QWIM mutation methods (add_weights,
modify_weights).

Author:
    QWIM Development Team

Version:
    0.2.0

Last Modified:
    2026-05-25
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime as dt
from pathlib import Path
from typing import Any

import polars as pl

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so that "src." imports resolve correctly
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Module-level import guard following project coding standards
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    from src.portfolios.portfolio_QWIM import Portfolio_QWIM
    from src.portfolios.utils_portfolio import (
        calculate_portfolio_values,
        create_benchmark_portfolio_values,
        create_custom_portfolio as _util_create_custom_portfolio,
        create_sample_portfolio_weights,
        ensure_path_exists,
        load_portfolio_weights,
        load_sample_etf_data,
        suggest_component_matches as _util_suggest_component_matches,
    )
    from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger
    _logger = get_logger(name = __name__)
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    _logger.warning("Import failed — keywords will raise on use: {}", _exc)

# ---------------------------------------------------------------------------
# Default data file paths
# ---------------------------------------------------------------------------
_ETF_DATA_PATH: Path = _PROJECT_ROOT / "inputs" / "raw" / "data_ETFs.csv"
_WEIGHTS_PATH: Path = _PROJECT_ROOT / "inputs" / "raw" / "sample_portfolio_weights_ETFs.csv"


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _require_imports() -> None:
    """Raise RuntimeError when source modules could not be imported."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"portfolio_QWIM source modules could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Portfolio construction keywords
# ===========================================================================


def create_portfolio_from_component_names(name_portfolio: str, *components: str) -> Any:
    """Create a portfolio_QWIM from one or more component name strings (equal weights).

    Arguments:
        name_portfolio  Name to assign to the portfolio.
        *components     One or more ETF/asset component name strings.

    Returns:
        portfolio_QWIM instance with equal weights for all components.
    """
    _require_imports()

    if not components:
        raise ValueError("At least one component name must be supplied to the keyword.")

    _logger.debug(
        "Creating portfolio {!r} from {} components: {}",
        name_portfolio, len(components), list(components),
    )

    return Portfolio_QWIM(
        name_portfolio=name_portfolio,
        names_components=list(components),
    )


def create_portfolio_from_weights_csv(name_portfolio: str = "CSV Portfolio") -> Any:
    """Create a portfolio_QWIM by loading weights from the default sample CSV file.

    Arguments:
        name_portfolio  Name to assign to the portfolio (default: 'CSV Portfolio').

    Returns:
        portfolio_QWIM instance initialised with the CSV weights.
    """
    _require_imports()

    weights_df = load_portfolio_weights(filepath=_WEIGHTS_PATH)
    _logger.debug("Loaded weights CSV with {} rows and columns: {}", weights_df.height, weights_df.columns)

    return Portfolio_QWIM(
        name_portfolio=name_portfolio,
        portfolio_weights=weights_df,
    )


# ===========================================================================
# Portfolio property / accessor keywords
# ===========================================================================


def get_portfolio_name(portfolio: Any) -> str:
    """Return the name stored in a portfolio object.

    Arguments:
        portfolio   portfolio_QWIM instance.

    Returns:
        Portfolio name string.
    """
    _require_imports()
    return portfolio.get_portfolio_name


def get_portfolio_num_components(portfolio: Any) -> int:
    """Return the integer count of components in a portfolio.

    Arguments:
        portfolio   portfolio_QWIM instance.

    Returns:
        Integer number of components.
    """
    _require_imports()
    return portfolio.get_num_components


def get_portfolio_components_list(portfolio: Any) -> list[str]:
    """Return the list of component names contained in a portfolio.

    Arguments:
        portfolio   portfolio_QWIM instance.

    Returns:
        List of component name strings.
    """
    _require_imports()
    return portfolio.get_portfolio_components


def get_portfolio_weights_dataframe(portfolio: Any) -> Any:
    """Return the Polars DataFrame of portfolio weights.

    Arguments:
        portfolio   portfolio_QWIM instance.

    Returns:
        pl.DataFrame with Date column and one column per component.
    """
    _require_imports()
    return portfolio.get_portfolio_weights()


# ===========================================================================
# Assertion / validation keywords
# ===========================================================================


def portfolio_name_should_equal(portfolio: Any, expected_name: str) -> None:
    """Fail if the portfolio name does not equal the expected string.

    Arguments:
        portfolio       portfolio_QWIM instance.
        expected_name   Expected portfolio name string.
    """
    actual = portfolio.get_portfolio_name
    if actual != expected_name:
        raise AssertionError(
            f"Portfolio name mismatch: expected '{expected_name}', got '{actual}'"
        )


def portfolio_num_components_should_equal(portfolio: Any, expected_count: int) -> None:
    """Fail if the component count does not equal the expected integer.

    Arguments:
        portfolio       portfolio_QWIM instance.
        expected_count  Expected component count (int or int-castable string).
    """
    actual = portfolio.get_num_components
    if actual != int(expected_count):
        raise AssertionError(
            f"Component count mismatch: expected {expected_count}, got {actual}"
        )


def portfolio_should_contain_component(portfolio: Any, component_name: str) -> None:
    """Fail if a specific component name is not present in the portfolio.

    Arguments:
        portfolio        portfolio_QWIM instance.
        component_name   Component name string to check for.
    """
    components = portfolio.get_portfolio_components
    if component_name not in components:
        raise AssertionError(
            f"Component '{component_name}' not found. Available: {components}"
        )


def portfolio_weights_dataframe_should_be_valid(portfolio: Any) -> None:
    """Fail if the portfolio weights DataFrame is not a non-empty pl.DataFrame.

    Arguments:
        portfolio   portfolio_QWIM instance.
    """
    weights = portfolio.get_portfolio_weights()

    if not isinstance(weights, pl.DataFrame):
        raise AssertionError(
            f"Expected pl.DataFrame for portfolio weights, got {type(weights).__name__}"
        )
    if weights.is_empty():
        raise AssertionError("Portfolio weights DataFrame must not be empty.")


def portfolio_weights_should_sum_to_one(portfolio: Any) -> None:
    """Fail if any row of the portfolio weights does not sum to approximately 1.0.

    Arguments:
        portfolio   portfolio_QWIM instance.
    """
    weights = portfolio.get_portfolio_weights()
    numeric_cols = [c for c in weights.columns if c != "Date"]

    for row_idx in range(weights.height):
        row_sum = sum(float(weights[col][row_idx]) for col in numeric_cols)
        if abs(row_sum - 1.0) > 1e-4:
            raise AssertionError(
                f"Row {row_idx} weights sum to {row_sum:.6f}; expected ≈ 1.0"
            )


def validate_and_normalise_portfolio_weights(portfolio: Any) -> None:
    """Call validate_all_weights(normalize=True) and fail if it raises an exception.

    Arguments:
        portfolio   portfolio_QWIM instance.
    """
    _require_imports()
    portfolio.validate_all_weights(normalize=True)


# ===========================================================================
# Portfolio value calculation keywords
# ===========================================================================


def calculate_portfolio_values_from_csv(
    portfolio: Any,
    initial_value: float = 100.0,
) -> Any:
    """Calculate the portfolio value time series using the default ETF price CSV.

    Arguments:
        portfolio       portfolio_QWIM instance.
        initial_value   Starting portfolio value (default: 100.0).

    Returns:
        pl.DataFrame with Date and Portfolio_Value columns.
    """
    _require_imports()

    price_data = load_sample_etf_data(filepath=_ETF_DATA_PATH)
    return calculate_portfolio_values(
        portfolio_obj=portfolio,
        price_data=price_data,
        initial_value=float(initial_value),
    )


def portfolio_values_dataframe_should_be_valid(values_df: Any) -> None:
    """Fail if the portfolio values DataFrame is missing or structurally invalid.

    Arguments:
        values_df   pl.DataFrame returned by calculate_portfolio_values.
    """
    if not isinstance(values_df, pl.DataFrame):
        raise AssertionError(
            f"Expected pl.DataFrame for values, got {type(values_df).__name__}"
        )
    if values_df.is_empty():
        raise AssertionError("Portfolio values DataFrame must not be empty.")
    if "Portfolio_Value" not in values_df.columns:
        raise AssertionError(
            f"'Portfolio_Value' column missing. Available: {values_df.columns}"
        )


def portfolio_values_first_row_should_equal(
    values_df: Any,
    expected_value: float = 100.0,
    tolerance: float = 1e-3,
) -> None:
    """Fail if the first Portfolio_Value row does not match the expected starting value.

    Arguments:
        values_df        pl.DataFrame with Portfolio_Value column.
        expected_value   Expected initial value (default: 100.0).
        tolerance        Absolute tolerance for floating-point comparison (default: 1e-3).
    """
    first = values_df["Portfolio_Value"][0]
    if first is None:
        raise AssertionError("First Portfolio_Value is None — calculation likely failed.")
    if abs(float(first) - float(expected_value)) > float(tolerance):
        raise AssertionError(
            f"Expected first Portfolio_Value ≈ {expected_value}, got {first}"
        )


def portfolio_values_should_all_be_positive(values_df: Any) -> None:
    """Fail if any Portfolio_Value entry is zero or negative.

    Arguments:
        values_df   pl.DataFrame with Portfolio_Value column.
    """
    min_val = values_df["Portfolio_Value"].min()
    if min_val is None or float(min_val) <= 0.0:
        raise AssertionError(
            f"All Portfolio_Value entries must be > 0. Minimum found: {min_val}"
        )


def create_benchmark_from_portfolio_values(values_df: Any) -> Any:
    """Create a benchmark portfolio values DataFrame from an existing portfolio DataFrame.

    Arguments:
        values_df   pl.DataFrame with Portfolio_Value column.

    Returns:
        pl.DataFrame with benchmark Portfolio_Value column.
    """
    _require_imports()
    return create_benchmark_portfolio_values(portfolio_values = values_df)


def benchmark_values_should_differ_from_portfolio(
    portfolio_values: Any,
    benchmark_values: Any,
) -> None:
    """Fail if benchmark values are identical to portfolio values.

    Arguments:
        portfolio_values   Original portfolio pl.DataFrame.
        benchmark_values   Benchmark pl.DataFrame.
    """
    port_list = portfolio_values["Portfolio_Value"].to_list()
    bench_list = benchmark_values["Value"].to_list()
    if port_list == bench_list:
        raise AssertionError(
            "Benchmark values are identical to portfolio values — expected divergence."
        )


# ===========================================================================
# utils_portfolio — create_sample_portfolio_weights keywords
# ===========================================================================


def load_etf_data_from_csv() -> Any:
    """Load ETF price data from the default sample CSV file.

    Returns:
        pl.DataFrame with Date column and one column per ETF.
    """
    _require_imports()
    return load_sample_etf_data(filepath=_ETF_DATA_PATH)


def create_sample_portfolio_weights_from_etf_data(etf_data: Any) -> Any:
    """Create deterministic sample portfolio weights from ETF price data.

    Arguments:
        etf_data   pl.DataFrame with Date column and ETF price columns.

    Returns:
        pl.DataFrame with rebalance-date sample weights.
    """
    _require_imports()
    return create_sample_portfolio_weights(etf_data = etf_data)


def sample_weights_should_sum_to_one_per_row(weights_df: Any) -> None:
    """Fail if any row of sample weights does not sum to ~1.0.

    Arguments:
        weights_df   pl.DataFrame with Date and weight columns.
    """
    numeric_cols = [c for c in weights_df.columns if c != "Date"]
    for row_idx in range(weights_df.height):
        row_sum = sum(float(weights_df[col][row_idx]) for col in numeric_cols)
        if abs(row_sum - 1.0) > 1e-4:
            raise AssertionError(
                f"Row {row_idx} weights sum to {row_sum:.6f}; expected ≈ 1.0"
            )


def dataframe_should_have_column(df: Any, column_name: str) -> None:
    """Fail if the DataFrame does not contain the specified column.

    Arguments:
        df            pl.DataFrame to check.
        column_name   Expected column name.
    """
    if column_name not in df.columns:
        raise AssertionError(
            f"Column '{column_name}' not found. Available: {df.columns}"
        )


# ===========================================================================
# utils_portfolio — CSV save/load round-trip keywords
# ===========================================================================


def save_weights_to_temp_csv(weights_df: Any) -> str:
    """Save weights DataFrame to a temporary CSV file.

    Arguments:
        weights_df   pl.DataFrame to save.

    Returns:
        Absolute path string of the saved CSV file.
    """
    _require_imports()
    fd, path_str = tempfile.mkstemp(suffix=".csv")
    weights_df.write_csv(path_str)
    return path_str


def load_csv_file(filepath: str) -> Any:
    """Load a CSV file into a Polars DataFrame.

    Arguments:
        filepath   Path to the CSV file.

    Returns:
        pl.DataFrame with the loaded data.
    """
    _require_imports()
    return pl.read_csv(filepath)


def dataframes_should_have_same_columns(df1: Any, df2: Any) -> None:
    """Fail if two DataFrames have different column sets.

    Arguments:
        df1   First pl.DataFrame.
        df2   Second pl.DataFrame.
    """
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    if cols1 != cols2:
        raise AssertionError(
            f"Column mismatch: first={cols1}, second={cols2}"
        )


def dataframes_should_have_same_row_count(df1: Any, df2: Any) -> None:
    """Fail if two DataFrames have different row counts.

    Arguments:
        df1   First pl.DataFrame.
        df2   Second pl.DataFrame.
    """
    if df1.height != df2.height:
        raise AssertionError(
            f"Row count mismatch: first={df1.height}, second={df2.height}"
        )


# ===========================================================================
# utils_portfolio — create_custom_portfolio keywords
# ===========================================================================


def create_custom_portfolio(*args: str) -> Any:
    """Create a custom portfolio via create_custom_portfolio utility.

    Arguments are passed as alternating key=value pairs:
        VTI    AGG    date=2024-06-30

    Returns:
        portfolio_QWIM instance.
    """
    _require_imports()
    components: list[str] = []
    kwargs: dict[str, str] = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            kwargs[key.strip()] = value.strip()
        else:
            components.append(arg.strip())
    return _util_create_custom_portfolio(components = components, **kwargs)


def portfolio_weights_date_should_be(portfolio: Any, expected_date: str) -> None:
    """Fail if the portfolio weights date does not match expected.

    Arguments:
        portfolio       portfolio_QWIM instance.
        expected_date   Expected date string in YYYY-MM-DD format.
    """
    weights = portfolio.get_portfolio_weights()
    actual_date = str(weights["Date"][0])
    if actual_date != expected_date:
        raise AssertionError(
            f"Date mismatch: expected '{expected_date}', got '{actual_date}'"
        )


# ===========================================================================
# utils_portfolio — suggest_component_matches keywords
# ===========================================================================


def suggest_component_matches(*args: str) -> dict:
    """Suggest matches between portfolio components and ETF columns.

    Arguments are passed as: comp1 comp2 ... ETF1 ETF2 ...
    The first half are components, the second half are ETF columns.

    Returns:
        Dictionary mapping component names to potential ETF column matches.
    """
    _require_imports()
    # Split args at the midpoint — first half components, second half ETFs
    n = len(args)
    mid = n // 2
    components = list(args[:mid])
    etf_columns = list(args[mid:])
    return _util_suggest_component_matches(components = components, etf_columns = etf_columns)


def suggestion_should_include(suggestions: dict, component: str, match: str) -> None:
    """Fail if a component suggestion does not include the expected match.

    Arguments:
        suggestions   Dictionary from suggest_component_matches.
        component     Component name to check.
        match         Expected match string.
    """
    if component not in suggestions:
        raise AssertionError(
            f"No suggestions found for component '{component}'"
        )
    if match not in suggestions[component]:
        raise AssertionError(
            f"Expected '{match}' in suggestions for '{component}', "
            f"got {suggestions[component]}"
        )


# ===========================================================================
# utils_portfolio — ensure_path_exists keywords
# ===========================================================================


def ensure_temp_path_exists() -> str:
    """Create a temporary directory and ensure a subdirectory path exists.

    Returns:
        Absolute path string of the ensured directory.
    """
    _require_imports()
    temp_dir = Path(tempfile.mkdtemp()) / "new_subdir"
    ensured = ensure_path_exists(path = temp_dir)
    return str(ensured)


def path_should_exist_on_disk(path_str: str) -> None:
    """Fail if the path does not exist on disk.

    Arguments:
        path_str   Absolute path string to check.
    """
    path_obj = Path(path_str)
    if not path_obj.exists():
        raise AssertionError(
            f"Path {path_str} does not exist on disk"
        )


# ===========================================================================
# portfolio_QWIM — add_weights / modify_weights keywords
# ===========================================================================


def add_weights_to_portfolio(portfolio: Any, date_str: str, *weight_pairs: str) -> None:
    """Add a new weights row to the portfolio.

    Arguments:
        portfolio      portfolio_QWIM instance.
        date_str       Date string in YYYY-MM-DD format.
        *weight_pairs  Alternating component=weight pairs (e.g., VTI=0.7 AGG=0.3).
    """
    _require_imports()
    weights: dict[str, float] = {}
    for pair in weight_pairs:
        comp, val = pair.split("=", 1)
        weights[comp.strip()] = float(val.strip())
    portfolio.add_weights(input_date=date_str, weights=weights)


def modify_weights_in_portfolio(portfolio: Any, date_str: str, *weight_pairs: str) -> None:
    """Modify existing weights in the portfolio.

    Arguments:
        portfolio      portfolio_QWIM instance.
        date_str       Date string in YYYY-MM-DD format.
        *weight_pairs  Alternating component=weight pairs (e.g., VTI=0.8 AGG=0.2).
    """
    _require_imports()
    weights: dict[str, float] = {}
    for pair in weight_pairs:
        comp, val = pair.split("=", 1)
        weights[comp.strip()] = float(val.strip())
    portfolio.modify_weights(input_date=date_str, new_weights=weights)


def get_today_date_string() -> str:
    """Return today's date as a YYYY-MM-DD string.

    Returns:
        Today's date in YYYY-MM-DD format.
    """
    return dt.now().strftime("%Y-%m-%d")


def portfolio_weights_row_count_should_be(portfolio: Any, expected_count: int) -> None:
    """Fail if the portfolio weights DataFrame does not have the expected row count.

    Arguments:
        portfolio       portfolio_QWIM instance.
        expected_count  Expected number of rows.
    """
    actual = len(portfolio.get_portfolio_weights())
    if actual != int(expected_count):
        raise AssertionError(
            f"Expected {expected_count} rows in weights DataFrame, got {actual}"
        )


def portfolio_weights_for_date_should_match(
    portfolio: Any,
    date_str: str,
    *weight_pairs: str,
) -> None:
    """Fail if weights for a specific date do not match expected values.

    Arguments:
        portfolio      portfolio_QWIM instance.
        date_str       Date string in YYYY-MM-DD format.
        *weight_pairs  Alternating component=weight pairs (e.g., VTI=0.7 AGG=0.3).
    """
    from datetime import date as _date
    _require_imports()
    df = portfolio.get_portfolio_weights()
    target_date = _date.fromisoformat(date_str)
    row = df.filter(pl.col("Date") == target_date)
    if len(row) != 1:
        raise AssertionError(
            f"Expected 1 row for date {date_str}, got {len(row)}"
        )
    for pair in weight_pairs:
        comp, expected_val = pair.split("=", 1)
        comp = comp.strip()
        expected = float(expected_val.strip())
        actual = float(row[comp][0])
        if abs(actual - expected) > 1e-4:
            raise AssertionError(
                f"Weight mismatch for {comp}: expected {expected}, got {actual}"
            )
