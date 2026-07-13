#!/usr/bin/env python3
"""Benchmark portfolio creation and demo utilities.

This module provides functions for generating benchmark portfolio values
derived from an existing portfolio time series, plus a demonstration
script for the full end-to-end portfolio pipeline.

Functions
---------
create_benchmark_portfolio_values
    Create a benchmark portfolio with time-based variations from an original
    portfolio values time series.
save_benchmark_portfolio_values_to_csv
    Save benchmark portfolio values to a CSV file.
"""

from __future__ import annotations

import random

from datetime import datetime
from pathlib import Path

import polars as pl

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


def create_benchmark_portfolio_values(*, portfolio_values: pl.DataFrame) -> pl.DataFrame:
    """Create a benchmark portfolio with time-based variations from the original.

    Parameters
    ----------
    portfolio_values : pl.DataFrame
        DataFrame with original portfolio values data.

    Returns
    -------
    pl.DataFrame
        DataFrame with benchmark portfolio values.

    Notes
    -----
    This function creates a benchmark with time-based pattern:
    - First 2 years: Subtract 0.11 * portfolio_value * random(0,1)
    - Next 3 years: Add 0.04 * portfolio_value * random(0,1)
    - Next 4 years: Subtract 0.08 * portfolio_value * random(0,1)
    - Next 2 years: Add 0.03 * portfolio_value * random(0,1)
    - Remaining years: Subtract 0.05 * portfolio_value * random(0,1)

    This creates a benchmark that has different performance characteristics
    over different time periods, simulating varying market conditions.

    Examples
    --------
    >>> import polars as pl
    >>> df = pl.DataFrame({"Date": ["2023-01-01", "2023-01-02"], "Portfolio_Value": [100.0, 105.0]})
    >>> benchmark = create_benchmark_portfolio_values(df)
    >>> print(benchmark.columns)
    ['Date', 'Value']
    >>> print(len(benchmark))
    2
    """
    # Extract dates and values
    dates = portfolio_values["Date"].to_list()
    values = portfolio_values["Portfolio_Value"].to_list()

    # Create benchmark values with time-based adjustments
    benchmark_values = []

    # Use fixed seed for reproducibility
    random.seed(42)

    # Convert dates to datetime objects if they are strings
    date_objects = []
    if dates and isinstance(dates[0], str):
        # Try common date formats
        date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]

        # Find the correct format by trying each one
        format_found = False

        for date_format in date_formats:
            try:
                date_objects = [datetime.strptime(date, date_format).date() for date in dates]
                format_found = True
                break
            except ValueError:
                continue

        if not format_found:
            # If no format works, use numeric indices for time periods
            _logger.warning("Could not parse dates. Using sequential indices for time periods.")
            date_objects = []
    else:
        # Dates are already datetime objects
        date_objects = dates

    # If we have valid date objects, use them to determine time periods
    if date_objects:
        # Find the start date
        start_date = min(date_objects)

        # Define the time periods in years
        period_years = [2, 3, 4, 2]  # 2, 3, 4, 2, and remaining years

        # Calculate the end dates for each period
        from datetime import timedelta

        period_end_dates = []
        current_date = start_date

        for years in period_years:
            # Approximate years by adding 365.25 days per year
            days = int(years * 365.25)
            current_date = current_date + timedelta(days=days)
            period_end_dates.append(current_date)

        # Apply the adjustments based on which period each date falls into
        for i, (date, value) in enumerate(zip(date_objects, values, strict=False)):
            if i == 0:
                # For the first date, keep the original value
                benchmark_values.append(value)
                continue

            # Determine which period this date falls into
            period = 4  # Default to the last period (index 4)
            for p, end_date in enumerate(period_end_dates):
                if date <= end_date:
                    period = p
                    break

            # Apply the appropriate adjustment based on the period
            rand_factor = random.random()  # Random number between 0 and 1

            if period == 0:
                # First 2 years: Subtract 0.11 * value * random
                adjustment = value * 0.11 * rand_factor
                benchmark_value = value - adjustment
            elif period == 1:
                # Next 3 years: Add 0.04 * value * random
                adjustment = value * 0.04 * rand_factor
                benchmark_value = value + adjustment
            elif period == 2:
                # Next 4 years: Subtract 0.08 * value * random
                adjustment = value * 0.08 * rand_factor
                benchmark_value = value - adjustment
            elif period == 3:
                # Next 2 years: Add 0.03 * value * random
                adjustment = value * 0.03 * rand_factor
                benchmark_value = value + adjustment
            else:
                # Remaining years: Subtract 0.05 * value * random
                adjustment = value * 0.05 * rand_factor
                benchmark_value = value - adjustment

            benchmark_values.append(benchmark_value)
    else:
        # If date parsing failed, use a simpler approach based on index position
        total_periods = len(values)

        # Calculate period lengths
        period_lengths = []
        remaining_length = total_periods

        # Define period fractions (approximate years out of the total)
        period_fractions = [2 / 11, 3 / 11, 4 / 11, 2 / 11]

        for fraction in period_fractions:
            length = max(1, int(total_periods * fraction))
            if length < remaining_length:
                period_lengths.append(length)
                remaining_length -= length
            else:
                period_lengths.append(remaining_length)
                remaining_length = 0
                break

        if remaining_length > 0:
            period_lengths.append(remaining_length)

        # Calculate the ending indices for each period
        period_end_indices = []
        current_index = 0

        for length in period_lengths:
            current_index += length
            period_end_indices.append(current_index)

        # Apply the adjustments based on which period each index falls into
        for i, value in enumerate(values):
            if i == 0:
                # For the first value, keep the original
                benchmark_values.append(value)
                continue

            # Determine which period this index falls into
            period = len(period_lengths)  # Default to beyond all defined periods
            for p, end_index in enumerate(period_end_indices):  # pragma: no branch
                if i < end_index:
                    period = p
                    break

            # Apply the appropriate adjustment based on the period
            rand_factor = random.random()  # Random number between 0 and 1

            if period == 0:
                # First period: Subtract 0.11 * value * random
                adjustment = value * 0.11 * rand_factor
                benchmark_value = value - adjustment
            elif period == 1:
                # Second period: Add 0.04 * value * random
                adjustment = value * 0.04 * rand_factor
                benchmark_value = value + adjustment
            elif period == 2:
                # Third period: Subtract 0.08 * value * random
                adjustment = value * 0.08 * rand_factor
                benchmark_value = value - adjustment
            elif period == 3:
                # Fourth period: Add 0.03 * value * random
                adjustment = value * 0.03 * rand_factor
                benchmark_value = value + adjustment
            else:
                # Remaining period: Subtract 0.05 * value * random
                adjustment = value * 0.05 * rand_factor
                benchmark_value = value - adjustment

            benchmark_values.append(benchmark_value)

    # Create the benchmark dataframe
    return pl.DataFrame(
        {
            "Date": dates,
            "Value": benchmark_values,
        },
    )


def save_benchmark_portfolio_values_to_csv(
    *,
    benchmark_portfolio_values: pl.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    """Save benchmark portfolio values to a CSV file.

    Parameters
    ----------
    benchmark_portfolio_values : pl.DataFrame
        DataFrame with benchmark portfolio values data.
    output_path : str or Path, optional
        Path where to save the CSV file. If None, saves to
        'data/processed/benchmark_portfolio_values.csv' by default.

    Returns
    -------
    Path
        Absolute Path where the CSV file was saved.

    Notes
    -----
    The output CSV file will have two columns:
    - Date: containing dates
    - Value: containing benchmark portfolio values
    """
    # Define the root project directory for absolute paths
    project_root = Path(__file__).resolve().parents[2]

    if output_path is None:
        # Use default path in the inputs/processed directory with absolute path
        output_path = project_root / "inputs" / "processed" / "benchmark_portfolio_values.csv"

    # Ensure the filepath is a Path object with resolved absolute path
    output_path = Path(output_path).resolve()

    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    benchmark_portfolio_values.write_csv(output_path)

    return output_path


# Example usage when run as a script
if __name__ == "__main__":
    # Deferred imports — avoids circular dependency with utils_portfolio at module level.
    from src.portfolios.utils_portfolio import (  # noqa: PLC0415
        calculate_portfolio_values,
        create_sample_portfolio,
        create_sample_portfolio_weights,
        debug_dataframe,
        load_sample_etf_data,
        save_portfolio_values_to_csv,
        save_portfolio_weights_to_csv,
        suggest_component_matches,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (  # noqa: PLC0415
        Exception_Validation_Input,
    )

    try:
        # Define and create required directories
        project_root = Path(__file__).resolve().parents[2]
        raw_dir = project_root / "inputs" / "raw"
        processed_dir = project_root / "inputs" / "processed"

        # Create directories if they don't exist
        for directory in [raw_dir, processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Print directory information
        _logger.info("Project root: {}", project_root)
        _logger.info("Raw data directory: {}", raw_dir)
        _logger.info("Processed data directory: {}", processed_dir)

        try:
            # Check if sample files exist
            etf_file = raw_dir / "data_ETFs.csv"
            weights_file = raw_dir / "sample_portfolio_weights_ETFs.csv"

            if not etf_file.exists():
                _logger.warning("ETF data file not found at {}", etf_file)
                _logger.warning("Please ensure this file exists before continuing.")

            if not weights_file.exists():
                _logger.warning("Portfolio weights file not found at {}", weights_file)
                _logger.warning("Please ensure this file exists before continuing.")

            # Get sample portfolio and data
            sample_data_etfs = load_sample_etf_data()
            debug_dataframe(df=sample_data_etfs, name="ETF Data")

            sample_portfolio_data = create_sample_portfolio_weights(etf_data=sample_data_etfs)
            weights_file = save_portfolio_weights_to_csv(
                portfolio_weights=sample_portfolio_data,
                output_path=weights_file,
            )
            _logger.info("Sample portfolio weights saved to: {}", weights_file)
            debug_dataframe(df=sample_portfolio_data, name="Portfolio Weights")

            # Create portfolio
            sample_portfolio_obj = create_sample_portfolio(weights_data=sample_portfolio_data)

            # Calculate portfolio values
            _logger.info("Calculating portfolio values...")
            portfolio_values = calculate_portfolio_values(
                portfolio_obj=sample_portfolio_obj,
                price_data=sample_data_etfs,
            )

            # Check if we have portfolio values
            if portfolio_values.shape[0] == 0:
                raise Exception_Validation_Input(
                    "No portfolio values were calculated. Please check your data.",
                )

            debug_dataframe(df=portfolio_values, name="Portfolio Values")

            # Display information
            _logger.info(
                f"Sample Portfolio Components: {sample_portfolio_obj.get_portfolio_components}",
            )
            _logger.info("Number of ETFs: {}", sample_portfolio_obj.get_num_components)
            _logger.info("\nSample Portfolio Weights (first 3 rows):")
            _logger.info(sample_portfolio_obj.get_portfolio_weights().head(3))

            _logger.info("\nETF Data (first 3 rows):")
            _logger.info(sample_data_etfs.head(3))

            _logger.info("\nPortfolio Values (first 3 rows):")
            _logger.info(portfolio_values.head(3))

            # Save portfolio values to CSV
            output_portfolio_values = portfolio_values.select(
                pl.col("Date"),
                pl.col("Portfolio_Value").alias("Value"),
            )

            # Save sample portfolio values to CSV
            output_path = save_portfolio_values_to_csv(
                portfolio_values=portfolio_values,
                output_path=processed_dir / "sample_portfolio_values.csv",
            )
            _logger.info("\nPortfolio values saved to: {}", output_path)

            # Create benchmark portfolio values
            benchmark_portfolio_values = create_benchmark_portfolio_values(
                portfolio_values=portfolio_values,
            )

            # Save benchmark portfolio values to CSV
            benchmark_path = save_benchmark_portfolio_values_to_csv(
                benchmark_portfolio_values=benchmark_portfolio_values,
                output_path=processed_dir / "benchmark_portfolio_values.csv",
            )
            _logger.info("Benchmark portfolio values saved to: {}", benchmark_path)

            # Try to visualize weights
            try:
                vis_path = processed_dir / "portfolio_weights.png"
                visualize_portfolio_weights(sample_portfolio_obj, vis_path)  # noqa: F821  # function planned but not yet implemented
            except Exception as e:
                _logger.warning("Could not visualize weights: {}", e)

            # Show sample comparison
            _logger.info("\nComparison of Original vs Benchmark (first 3 rows):")
            comparison = pl.DataFrame(
                {
                    "Date": output_portfolio_values["Date"].head(3),
                    "Original": output_portfolio_values["Value"].head(3),
                    "Benchmark": benchmark_portfolio_values["Value"].head(3),
                    "Difference": (
                        output_portfolio_values["Value"] - benchmark_portfolio_values["Value"]
                    ).head(3),
                },
            )
            _logger.info(comparison)

            _logger.info("\nPortfolio Performance Summary:")
            initial_value = portfolio_values["Portfolio_Value"].to_list()[0]
            final_value = portfolio_values["Portfolio_Value"].to_list()[-1]
            total_return = (final_value / initial_value - 1) * 100
            _logger.info("Starting Value: %.2f", initial_value)
            _logger.info("Final Value: %.2f", final_value)
            _logger.info("Total Return: %.2f%%", total_return)

            # Calculate annualized return if possible
            try:
                start_date = portfolio_values["Date"][0]
                end_date = portfolio_values["Date"][-1]

                # Check if dates are strings and try to convert them
                if isinstance(start_date, str) or isinstance(end_date, str):
                    from datetime import datetime as _dt

                    # Try different date formats
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

                    for date_format in date_formats:
                        try:
                            if isinstance(start_date, str):
                                start_date = _dt.strptime(start_date, date_format).date()
                            if isinstance(end_date, str):
                                end_date = _dt.strptime(end_date, date_format).date()
                            break
                        except ValueError:
                            continue

                    if isinstance(start_date, str) or isinstance(end_date, str):
                        raise Exception_Validation_Input(
                            f"Could not parse date strings: {start_date}, {end_date}",
                        )

                # Calculate days between dates
                days = (end_date - start_date).days

                if days <= 0:
                    raise Exception_Validation_Input(
                        f"Invalid date range: {start_date} to {end_date}",
                    )

                years = days / 365.0
                annualized_return = (
                    (final_value / initial_value) ** (1 / max(years, 0.01)) - 1
                ) * 100
                _logger.info(
                    f"Annualized Return: {annualized_return:.2f}% (over {years:.2f} years)",
                )
            except Exception as e:
                _logger.warning("Could not calculate annualized return: {}", e)
                # Add additional debugging info
                _logger.debug(
                    f"Date types - Start: {type(portfolio_values['Date'][0])}, "
                    f"End: {type(portfolio_values['Date'][-1])}",
                )
                _logger.debug(
                    f"Date values - Start: {portfolio_values['Date'][0]}, "
                    f"End: {portfolio_values['Date'][-1]}",
                )

            # In the main block after loading the data
            _logger.info("\nChecking portfolio components vs. ETF data columns...")
            components = sample_portfolio_obj.get_portfolio_components
            etf_columns = [col for col in sample_data_etfs.columns if col != "Date"]
            missing_components = [c for c in components if c not in etf_columns]
            if missing_components:
                _logger.warning(
                    "These components are missing in the ETF data: %s",
                    missing_components,
                )
                _logger.info("Available ETF columns: {}", etf_columns)

                # Suggest possible matches
                suggestions = suggest_component_matches(
                    components=missing_components,
                    etf_columns=etf_columns,
                )
                if suggestions:
                    _logger.info("\nPossible column matches:")
                    for comp, matches in suggestions.items():
                        _logger.info("  {!r} might match: {}", comp, matches)

                # Offer to create a mapping file
                _logger.info(
                    "\nConsider creating a mapping file to rename components "
                    "or ETFs to match each other.",
                )
            else:
                _logger.info("All components are present in ETF data.")

        except ImportError as e:
            _logger.error("ImportError: {}", e)
            _logger.error("This may be because the 'portfolio' class could not be imported.")
            _logger.error(
                "Make sure your Python path includes the directory "
                "containing the portfolios module.",
            )

    except Exception as e:
        _logger.exception("Error: {}", e)
