#!/usr/bin/env python3
"""
Portfolio utilities module for portfolio data management and calculations.

This module provides utility functions for working with portfolios,
including loading data files, creating portfolios, and calculating
portfolio values over time.

Functions
---------
load_sample_etf_data
    Load ETF price data from a CSV file in the data/raw directory.
load_portfolio_weights
    Load portfolio weights data from a CSV file in the data/raw directory.
create_sample_portfolio_weights
    Create deterministic sample ETF weights aligned to the available ETF dates.
create_sample_portfolio
    Create a portfolio object from portfolio weights data.
calculate_portfolio_values
    Calculate portfolio value time series given weights and price data.
save_portfolio_weights_to_csv
    Save sample portfolio weights to a CSV file in the data/raw directory.
save_portfolio_values_to_csv
    Save portfolio values to a CSV file in the data/processed directory.
create_benchmark_portfolio_values
    Create a benchmark portfolio with specified random variations.
save_benchmark_portfolio_values_to_csv
    Save benchmark portfolio values to a CSV file in the data/processed directory.
get_sample_portfolio
    Get a pre-configured sample portfolio for testing and demonstrations.
visualize_portfolio_weights
    Visualize portfolio weights over time with matplotlib.
debug_dataframe
    Print debug information about a DataFrame for troubleshooting.

Examples
--------
>>> from utils_portfolio import get_sample_portfolio
>>> portfolio_obj, etf_data, values = get_sample_portfolio()  # doctest: +SKIP
>>> print(f"Portfolio has {portfolio_obj.get_num_components} components")  # doctest: +SKIP
Portfolio has 5 components
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from src.portfolios._portfolio_benchmark import (
    create_benchmark_portfolio_values,  # noqa: F401 - documented re-export
    save_benchmark_portfolio_values_to_csv,  # noqa: F401 - documented re-export
)
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


if TYPE_CHECKING:
    from src.portfolios.portfolio_QWIM import Portfolio_QWIM


# Configure module logger
_logger = get_logger(name = __name__)

# Import local module - with fallback
# Pre-declare the type so type checkers see a consistent annotation.
Portfolio_QWIM_class: type[Portfolio_QWIM] | None = None
try:
    from src.portfolios.portfolio_QWIM import Portfolio_QWIM as Portfolio_QWIM_class
except ImportError:  # pragma: no cover
    _logger.warning("Could not import portfolio_QWIM. Make sure it's in your path.")
    Portfolio_QWIM_class = None  # fallback when module unavailable


def debug_dataframe(
    *,
    df: pl.DataFrame,
    name: str,
) -> None:
    """Print debug information about a DataFrame.

    Parameters
    ----------
    df : pl.DataFrame
        The DataFrame to debug.
    name : str
        Name of the DataFrame for identification.

    Returns
    -------
    None
    """
    _logger.debug("\n=== DEBUG INFO: {} ===", name)
    _logger.debug("Shape: {}", df.shape)
    _logger.debug("Columns: {}", df.columns)
    _logger.debug("First few rows:")
    _logger.debug("{}", df.head(3))
    _logger.debug("Column types:")
    for col in df.columns:
        _logger.debug("  {}: {}", col, df[col].dtype)
    _logger.debug("=" * 40)


def ensure_path_exists(
    *,
    path: str | Path,
) -> Path:
    """Ensure a directory path exists, creating it if necessary.

    Parameters
    ----------
    path : str or Path
        Path to ensure exists.

    Returns
    -------
    Path
        The resolved Path object.
    """
    path_obj = Path(path).resolve()
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def load_sample_etf_data(
    *,
    filepath: str | Path | None = None,
) -> pl.DataFrame:
    """Load ETF price data from a CSV file.

    Parameters
    ----------
    filepath : str or Path, optional
        Path to the CSV file containing ETF data.
        If None, uses the default "data_ETFs.csv" file in the data/raw directory.

    Returns
    -------
    pl.DataFrame
        DataFrame containing ETF price data.

    Raises
    ------
    FileNotFoundError
        If the ETF data file cannot be found at the specified location.

    Notes
    -----
    The expected CSV format has a "Date" column and columns for each ETF's price.
    """
    # Define the root project directory for absolute paths - one level up
    project_root = Path(__file__).resolve().parents[2]

    if filepath is None:
        # Use default file in the inputs/raw directory with absolute path
        filepath = project_root / "inputs" / "raw" / "data_ETFs.csv"

    # Ensure the filepath is a Path object with resolved absolute path
    filepath = Path(filepath).resolve()

    # Load data with better error message
    if not filepath.exists():
        raise FileNotFoundError(
            f"ETF data file not found: {filepath}\n"
            f"Make sure the file exists in the inputs/raw directory.",
        )

    # Read CSV with date formats explicitly specified
    try:
        # Try reading with automatically detected date format
        data = pl.read_csv(filepath)
    except Exception as csv_read_error:
        _logger.warning(
            "Could not read CSV with automatic parsing: {}",
            csv_read_error,
        )
        # Try reading with explicit date formats
        data = pl.read_csv(filepath, try_parse_dates=False)

    # Check if there's a date column but it's not named exactly 'Date'
    date_column_variants = ["date", "Date", "DATE", "datetime", "Datetime", "time", "Time"]
    date_columns = [
        col for col in data.columns if col.lower() in [v.lower() for v in date_column_variants]
    ]

    if not date_columns:
        raise Exception_Validation_Input(
            f"No date column found in {filepath}. Please ensure your CSV file has a 'Date' column.",
        )
    if "Date" not in data.columns and date_columns:
        # Rename the first found date column to 'Date'
        old_name = date_columns[0]
        data = data.rename({old_name: "Date"})
        _logger.info("Renamed column {!r} to 'Date' for consistency.", old_name)

    # Ensure Date column is properly parsed - try multiple date formats.
    date_sample = data["Date"].head(5).to_list()
    _logger.debug("Date sample values: {}", date_sample)

    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y%m%d",
        "%d.%m.%Y",
    ]

    parsed = False
    for date_format in date_formats:
        try:
            # Try to parse with this format.
            from datetime import datetime

            if isinstance(date_sample[0], str):
                datetime.strptime(date_sample[0], date_format)
                _logger.debug("Using date format: {}", date_format)
                data = data.with_columns(
                    pl.col("Date").str.strptime(pl.Date, date_format, strict=False),
                )
                parsed = True
                break
        except (ValueError, TypeError):
            continue

    if not parsed and isinstance(date_sample[0], str):
        try:
            # Handle timestamp strings like 2026-05-09 00:00:00-05:00.
            parsed_dates = data.select(
                pl.col("Date")
                .str.slice(0, 10)
                .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                .alias("Date"),
            )["Date"]
            if parsed_dates.null_count() < data.height:
                data = data.with_columns(parsed_dates)
                parsed = True
        except Exception:  # pragma: no cover - defensive against unexpected Polars string failures
            parsed = False

    if not parsed and isinstance(date_sample[0], str):
        _logger.warning(
            "Could not parse 'Date' column as date with any standard format. "
            "Common date formats are: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY. "
            "Continuing with string dates.",
        )

    return data


def load_portfolio_weights(
    *,
    filepath: str | Path | None = None,
) -> pl.DataFrame:
    """Load portfolio weights data from a CSV file.

    Parameters
    ----------
    filepath : str or Path, optional
        Path to the CSV file containing portfolio weights.
        If None, uses the default "sample_portfolio_weights_ETFs.csv" file
        in the data/raw directory.

    Returns
    -------
    pl.DataFrame
        DataFrame containing portfolio weights data.

    Raises
    ------
    FileNotFoundError
        If the portfolio weights file cannot be found at the specified location.

    Notes
    -----
    The expected CSV format has a "Date" column and columns for each asset's weight.
    The weights in each row should sum to approximately 1.0.
    """
    # Define the root project directory for absolute paths
    project_root = Path(__file__).resolve().parents[2]

    if filepath is None:
        # Use default file in the inputs/raw directory with absolute path
        filepath = project_root / "inputs" / "raw" / "sample_portfolio_weights_ETFs.csv"

    # Ensure the filepath is a Path object with resolved absolute path
    filepath = Path(filepath).resolve()

    # Load data with better error message
    if not filepath.exists():
        # Try to list files in the directory to help debugging
        parent_dir = filepath.parent
        if parent_dir.exists():
            files = list(parent_dir.glob("*.csv"))
            file_list = "\n  ".join([f.name for f in files])
            raise FileNotFoundError(
                f"Portfolio weights file not found: {filepath}\n"
                f"Available CSV files in {parent_dir}:\n  {file_list}",
            )

        raise FileNotFoundError(
            f"Portfolio weights file not found: {filepath}\n"
            f"Make sure the file exists in the inputs/raw directory.",
        )

    # Read CSV and ensure proper column naming
    data = pl.read_csv(filepath)

    # Check if there's a date column but it's not named exactly 'Date'
    date_column_variants = ["date", "Date", "DATE", "datetime", "Datetime", "time", "Time"]
    date_columns = [
        col for col in data.columns if col.lower() in [v.lower() for v in date_column_variants]
    ]

    if not date_columns:
        raise Exception_Validation_Input(
            f"No date column found in {filepath}. Please ensure your CSV file has a 'Date' column.",
        )
    if "Date" not in data.columns and date_columns:
        # Rename the first found date column to 'Date'
        data = data.rename({date_columns[0]: "Date"})
        _logger.info("Renamed column {!r} to 'Date' for consistency.", date_columns[0])

    # Ensure Date column is properly parsed
    try:
        # For polars >= 0.19.0
        if hasattr(pl.col("Date").str, "to_date"):
            data = data.with_columns(pl.col("Date").str.to_date())
        # For older polars versions
        else:  # pragma: no cover
            data = data.with_columns(pl.col("Date").cast(pl.Date))
    except Exception as date_parse_error:  # pragma: no cover
        _logger.warning(
            f"Could not parse 'Date' column as date: {date_parse_error}. Continuing with string dates.",
        )

    weight_columns = [column_name for column_name in data.columns if column_name != "Date"]
    if weight_columns:
        weight_sum = pl.sum_horizontal(
            [pl.col(column_name).cast(pl.Float64) for column_name in weight_columns],
        )
        data = data.with_columns(
            [
                pl.when(weight_sum > 0)
                .then(pl.col(column_name).cast(pl.Float64) / weight_sum)
                .otherwise(pl.col(column_name).cast(pl.Float64))
                .alias(column_name)
                for column_name in weight_columns
            ],
        )

    return data


def create_sample_portfolio_weights(
    *,
    etf_data: pl.DataFrame,
    rebalance_frequency_months: int = 6,
    random_seed: int = 42,
) -> pl.DataFrame:
    """Create deterministic sample ETF weights aligned to available ETF dates.

    Parameters
    ----------
    etf_data : pl.DataFrame
        ETF price history containing a ``Date`` column and one column per ETF.
    rebalance_frequency_months : int, optional
        Minimum number of months between rebalance dates, by default 6.
    random_seed : int, optional
        Seed for deterministic sample weight generation, by default 42.

    Returns
    -------
    pl.DataFrame
        Rebalance-date sample weights with one row per rebalance event.
    """
    if "Date" not in etf_data.columns:
        raise Exception_Validation_Input("ETF data must contain a 'Date' column.")

    asset_columns = [column_name for column_name in etf_data.columns if column_name != "Date"]
    if not asset_columns:
        raise Exception_Validation_Input("ETF data must contain at least one asset column.")

    def _coerce_date(*, date_value: object) -> date:
        """Coerce *date_value* to a :class:`datetime.date` instance."""
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, date):
            return date_value
        if hasattr(date_value, "date"):
            return date_value.date()
        return date.fromisoformat(str(date_value)[:10])

    def _months_between(*, start_date: date, end_date: date) -> int:
        """Return the number of whole months from *start_date* to *end_date*."""
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    sorted_dates = sorted(
        _coerce_date(date_value=item_date) for item_date in etf_data["Date"].to_list()
    )
    rebalance_dates: list[date] = []
    for current_date in sorted_dates:
        if not rebalance_dates:
            rebalance_dates.append(current_date)
            continue

        if (
            _months_between(start_date=rebalance_dates[-1], end_date=current_date)
            >= rebalance_frequency_months
        ):
            rebalance_dates.append(current_date)

    if sorted_dates and rebalance_dates[-1] != sorted_dates[-1]:
        rebalance_dates.append(sorted_dates[-1])

    random_generator = np.random.default_rng(seed=random_seed)
    rows_weights: list[dict[str, object]] = []

    for rebalance_date in rebalance_dates:
        raw_weights = random_generator.random(size=len(asset_columns)).tolist()
        filtered_weights = [
            0.0 if weight_value < 0.12 else weight_value for weight_value in raw_weights
        ]
        if sum(filtered_weights) == 0.0:
            filtered_weights = [1.0] + [0.0] * (len(asset_columns) - 1)

        total_weight = sum(filtered_weights)
        normalized_weights = [weight_value / total_weight for weight_value in filtered_weights]
        if len(normalized_weights) > 1:
            normalized_weights[-1] = 1.0 - sum(normalized_weights[:-1])
        else:
            normalized_weights[0] = 1.0

        row_weights: dict[str, object] = {
            "Date": rebalance_date.isoformat(),
            **dict(zip(asset_columns, normalized_weights, strict=False)),
        }

        rows_weights.append(row_weights)

    return pl.DataFrame(rows_weights)


def save_portfolio_weights_to_csv(
    *,
    portfolio_weights: pl.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    """Save sample portfolio weights to a CSV file.

    Parameters
    ----------
    portfolio_weights : pl.DataFrame
        DataFrame with sample ETF weights by rebalance date.
    output_path : str or Path, optional
        Path where to save the CSV file. If None, saves to
        ``inputs/raw/sample_portfolio_weights_ETFs.csv``.

    Returns
    -------
    Path
        Absolute path where the CSV file was saved.
    """
    project_root = Path(__file__).resolve().parents[2]

    if output_path is None:
        output_path = project_root / "inputs" / "raw" / "sample_portfolio_weights_ETFs.csv"

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    portfolio_weights.write_csv(output_path)
    return output_path


def create_sample_portfolio(
    *,
    weights_data: pl.DataFrame,
) -> Portfolio_QWIM:
    """Create a portfolio object from portfolio weights data.

    Parameters
    ----------
    weights_data : pl.DataFrame
        DataFrame containing portfolio weights data.

    Returns
    -------
    portfolio
        Portfolio object initialized with the provided weights data.

    Raises
    ------
    ValueError
        If the weights data is missing required columns.
    ImportError
        If the portfolio class could not be imported.

    Examples
    --------
    >>> from utils_portfolio import load_portfolio_weights, create_sample_portfolio
    >>> weights = load_portfolio_weights()
    >>> p = create_sample_portfolio(weights)
    >>> print(p.get_num_components)
    5
    """
    # Validate the weights data before creating the portfolio
    if "Date" not in weights_data.columns:
        raise Exception_Validation_Input("The weights data must contain a 'Date' column.")

    # Check if there are any non-Date columns that could be component weights
    component_columns = [col for col in weights_data.columns if col != "Date"]
    if not component_columns:
        raise Exception_Validation_Input(
            "The weights data must contain columns for component weights in addition to 'Date'.",
        )

    # Report potentially problematic columns
    for col in component_columns:
        if col.isdigit() or (col.startswith("-") and col[1:].isdigit()):
            _logger.warning(
                f"Column '{col}' is numeric and might be an index rather than a component name.",
            )

    # Clean up weights_data to ensure proper format
    cleaned_weights = weights_data.clone()

    # Make sure we have the portfolio class available
    if Portfolio_QWIM_class is None:
        raise ImportError("The portfolio class could not be imported. Check your installation.")

    # Proceed with creating the portfolio - using the updated constructor order
    portfolio_obj = Portfolio_QWIM_class(
        name_portfolio="Sample Portfolio",
        portfolio_weights=cleaned_weights,
    )

    # Verify the portfolio was created correctly
    if not portfolio_obj.get_portfolio_components:
        raise Exception_Validation_Input(
            "Created portfolio has no components. Check your weights data format.",
        )

    return portfolio_obj  # pyrefly: ignore[bad-return]


def calculate_portfolio_values(
    *,
    portfolio_obj: Portfolio_QWIM,
    price_data: pl.DataFrame,
    initial_value: float = 100.0,
) -> pl.DataFrame:
    """Calculate time series of portfolio values based on weights and price data.

    Parameters
    ----------
    portfolio_obj : portfolio
        Portfolio object containing weight information.
    price_data : pl.DataFrame
        DataFrame containing price data for the assets in the portfolio.
    initial_value : float, optional
        Initial portfolio value (default: 100.0).

    Returns
    -------
    pl.DataFrame
        DataFrame with columns for Date and Portfolio_Value.

    Raises
    ------
    ValueError
        If components in the portfolio are missing from price data.
        If no weight dates are found in the portfolio.

    Notes
    -----
    This function:
    1. Aligns portfolio weights with price data dates using date ranges
    2. For dates between DateOne and DateTwo in the weights DataFrame,
       applies the weights from DateTwo to all price dates in that range
    3. Calculates portfolio values by multiplying weights with prices
    4. Returns a time series of portfolio values
    """
    # Get portfolio weights and components
    weights_df = portfolio_obj.get_portfolio_weights()
    components = portfolio_obj.get_portfolio_components

    # Debug info
    _logger.debug("Portfolio components: {}", components)
    _logger.debug("Price data columns: {}", price_data.columns)

    # Filter out numeric column names (likely index columns) from components
    valid_components = []
    for comp in components:
        if comp != "Date" and comp in price_data.columns:
            valid_components.append(comp)
        elif comp.isdigit() or (comp.startswith("-") and comp[1:].isdigit()):
            _logger.warning("Ignoring numeric component {!r} which is likely an index column", comp)
        else:
            _logger.warning("Component {!r} not found in price data columns", comp)

    if not valid_components:
        raise Exception_Validation_Input(
            "No valid components found that match between portfolio and price data.\n"
            "Check that your portfolio weights columns match ETF names in price data.",
        )

    # Replace components with valid_components
    components = valid_components
    _logger.debug("Using these components: {}", components)

    # Sort weights by date
    weights_df = weights_df.sort("Date")

    # Sort price data by date
    price_data = price_data.sort("Date")

    # Filter price data to include only the components in the portfolio and the date
    price_cols = ["Date"] + components
    filtered_prices = price_data.select(price_cols)

    # Normalise price Date dtype to pl.Date so join_asof type is consistent with
    # the weights DataFrame (m_coerce_dataframe always stores Date as pl.Date).
    price_date_dtype = filtered_prices.schema["Date"]
    if price_date_dtype == pl.Utf8:
        filtered_prices = filtered_prices.with_columns(
            pl.col("Date").str.to_date("%Y-%m-%d", strict=False).alias("Date"),
        )
    elif price_date_dtype != pl.Date:  # pragma: no cover
        filtered_prices = filtered_prices.with_columns(
            pl.col("Date").cast(pl.Date, strict=False).alias("Date"),
        )

    # Rename weight columns to avoid collision with identically named price columns
    weight_col_map = {c: f"w_{c}" for c in components}
    weights_renamed = weights_df.rename(weight_col_map)

    # For each price date, look up the most recent prior weight row (O(n log n))
    joined = filtered_prices.join_asof(weights_renamed, on="Date", strategy="backward")

    # Drop rows before the first weight date (null weights from the asof join)
    first_weight_col = f"w_{components[0]}"
    joined = joined.filter(pl.col(first_weight_col).is_not_null())

    if joined.is_empty():
        _logger.warning("No portfolio values could be calculated. Returning empty DataFrame.")
        return pl.DataFrame({"Date": [], "Portfolio_Value": []})

    # Per-component daily arithmetic return: price[t] / price[t-1] - 1
    joined = joined.with_columns(
        [((pl.col(c) / pl.col(c).shift(1)) - 1).alias(f"ret_{c}") for c in components],
    )

    # Portfolio daily return = weighted sum of component daily returns
    portfolio_return_expr = pl.sum_horizontal(
        [pl.col(f"ret_{c}") * pl.col(f"w_{c}") for c in components],
    )
    joined = joined.with_columns(portfolio_return_expr.alias("portfolio_daily_return"))

    # First row has no prior price -> null return; fill with 0 so value = initial_value
    joined = joined.with_columns(
        pl.col("portfolio_daily_return").fill_null(0.0),
    )

    # Compound: Portfolio_Value[t] = initial_value x prod(1 + r[i], i = 0 to t)
    joined = joined.with_columns(
        ((pl.col("portfolio_daily_return") + 1).cum_prod() * initial_value).alias(
            "Portfolio_Value",
        ),
    )

    return joined.select(["Date", "Portfolio_Value"])


def save_portfolio_values_to_csv(
    *,
    portfolio_values: pl.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    """Save portfolio values to a CSV file.

    Parameters
    ----------
    portfolio_values : pl.DataFrame
        DataFrame with portfolio values data.
    output_path : str or Path, optional
        Path where to save the CSV file. If None, saves to
        'data/processed/sample_portfolio_values.csv' by default.

    Returns
    -------
    Path
        Absolute Path where the CSV file was saved.

    Notes
    -----
    The output CSV file will have two columns:
    - Date: containing dates
    - Value: containing portfolio values
    """
    # Define the root project directory for absolute paths
    project_root = Path(__file__).resolve().parents[2]

    if output_path is None:
        # Use default path in the inputs/processed directory with absolute path
        output_path = project_root / "inputs" / "processed" / "sample_portfolio_values.csv"

    # Ensure the filepath is a Path object with resolved absolute path
    output_path = Path(output_path).resolve()

    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a new DataFrame with the desired format
    output_portfolio_values = portfolio_values.select(
        pl.col("Date"),
        pl.col("Portfolio_Value").alias("Value"),
    )

    # Write to CSV
    output_portfolio_values.write_csv(output_path)

    return output_path


def get_sample_portfolio() -> tuple[Portfolio_QWIM, pl.DataFrame, pl.DataFrame]:
    """Get a sample portfolio, raw data, and calculated portfolio values.

    This is a convenience function for testing and demonstrations.

    Returns
    -------
    tuple
        A tuple containing:
        - portfolio: The sample portfolio object
        - pl.DataFrame: The ETF price data
        - pl.DataFrame: The calculated portfolio values time series

    Examples
    --------
    >>> p, data, values = get_sample_portfolio()
    >>> print(f"Portfolio has {len(p.get_portfolio_components)} components")
    Portfolio has 5 components
    >>> print(f"Values span {len(values)} days")
    Values span 252 days
    """
    # Load data
    sample_data_etfs = load_sample_etf_data()
    sample_portfolio_data = load_portfolio_weights()

    # Create portfolio - using the create_sample_portfolio function
    sample_portfolio_obj = create_sample_portfolio(weights_data=sample_portfolio_data)

    # Calculate portfolio values
    portfolio_values = calculate_portfolio_values(
        portfolio_obj=sample_portfolio_obj,
        price_data=sample_data_etfs,
    )

    return sample_portfolio_obj, sample_data_etfs, portfolio_values


def suggest_component_matches(
    *,
    components: list,
    etf_columns: list,
) -> dict:
    """Suggest possible matches between portfolio components and ETF columns.

    Parameters
    ----------
    components : list
        List of component names from portfolio.
    etf_columns : list
        List of column names from ETF data.

    Returns
    -------
    dict
        Dictionary mapping component names to potential ETF column matches.
    """
    suggestions = {}

    # Convert all to lowercase for case-insensitive matching
    etf_lower = [col.lower() for col in etf_columns]

    for comp in components:
        if comp == "Date":
            continue

        comp_lower = comp.lower()

        # Check for exact match but case-insensitive
        matches = []
        for i, etf in enumerate(etf_lower):
            # Exact match
            if etf == comp_lower:
                matches.append(etf_columns[i])
                continue

            # Partial match: one is contained in the other
            if etf in comp_lower or comp_lower in etf:
                matches.append(etf_columns[i])
                continue

            # Numeric component might match numeric ETF
            if (comp.isdigit() and etf.isdigit()) or (
                comp.startswith("-")
                and comp[1:].isdigit()
                and etf.startswith("-")
                and etf[1:].isdigit()
            ):
                matches.append(etf_columns[i])

        if matches:
            suggestions[comp] = matches

    return suggestions


def create_custom_portfolio(
    *,
    components: list[str],
    date: str | None = None,
) -> Portfolio_QWIM:
    """Create a custom portfolio with equal weights for the given components.

    Parameters
    ----------
    components : list
        List of component names (e.g., ["AAPL", "MSFT"]).
    date : str, optional
        Date for the portfolio weights.

    Returns
    -------
    portfolio
        Portfolio object with equal weights for the given components.

    Examples
    --------
    >>> create_custom_portfolio(["AAPL", "MSFT"])
    portfolio(name='Custom Portfolio', components=['AAPL', 'MSFT'], dates=1 rows)
    """
    # Validate inputs
    if Portfolio_QWIM_class is None:
        raise ImportError("Portfolio class not available.")

    if not components:
        raise Exception_Validation_Input("Components list cannot be empty.")

    return Portfolio_QWIM_class(  # pyrefly: ignore[bad-return]
        name_portfolio="Custom Portfolio",
        names_components=components,
        date_portfolio=date,
    )
