"""Behave step definitions for portfolio_QWIM and utils_portfolio.

Tests cover:
    - portfolio_QWIM construction from component names and CSV weights
    - Property access: name, num_components, component list, weights DataFrame
    - Weight-sum validation (each row sums to ~1.0)
    - End-to-end portfolio value calculation with initial value
    - Benchmark creation and divergence check
    - utils_portfolio: create_sample_portfolio_weights, CSV round-trip,
      create_custom_portfolio, suggest_component_matches, ensure_path_exists
    - portfolio_QWIM: add_weights, modify_weights

Author:         QWIM Development Team
Version:        0.2.0
Last Modified:  2026-05-25
"""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

# ---------------------------------------------------------------------------
# Project root on sys.path — step files live 4 levels below the root:
#   tests/tests_behave/features/steps/<this file>
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_ETF_DATA_PATH: Path = _PROJECT_ROOT / "inputs" / "raw" / "data_ETFs.csv"
_WEIGHTS_PATH: Path = _PROJECT_ROOT / "inputs" / "raw" / "sample_portfolio_weights_ETFs.csv"

# ---------------------------------------------------------------------------
# Module-level import guard
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    import polars as pl
    from src.portfolios.portfolio_QWIM import Portfolio_QWIM
    from src.portfolios.utils_portfolio import (
        calculate_portfolio_values,
        create_benchmark_portfolio_values,
        create_custom_portfolio,
        create_sample_portfolio_weights,
        ensure_path_exists,
        load_portfolio_weights,
        load_sample_etf_data,
        suggest_component_matches,
    )
except ImportError as _exc:
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


def _require_imports() -> None:
    """Require imports."""
    if not MODULE_IMPORT_AVAILABLE:
        raise RuntimeError(
            f"portfolio_QWIM source modules could not be imported: {_import_error_message}"
        )


# ===========================================================================
# Given / When — construction
# ===========================================================================


@when(u'I create a portfolio named "{name}" with components "{components}"')
def step_create_portfolio(context, name: str, components: str) -> None:
    """Create portfolio_QWIM from comma-separated component names."""
    _require_imports()
    names_list = [c.strip() for c in components.split(",")]
    context.portfolio = Portfolio_QWIM(
        name_portfolio=name,
        names_components=names_list,
    )


@when(u'I create a second portfolio named "{name}" with components "{components}"')
def step_create_second_portfolio(context, name: str, components: str) -> None:
    """Create a second portfolio_QWIM and store in context.portfolio2."""
    _require_imports()
    names_list = [c.strip() for c in components.split(",")]
    context.portfolio2 = Portfolio_QWIM(
        name_portfolio=name,
        names_components=names_list,
    )


@when(u'I load a portfolio from the sample weights CSV file')
def step_load_portfolio_csv(context) -> None:
    """Load portfolio_QWIM from the default sample weights CSV file."""
    _require_imports()
    weights_df = load_portfolio_weights(filepath=_WEIGHTS_PATH)
    context.portfolio = Portfolio_QWIM(
        name_portfolio="CSV Portfolio",
        portfolio_weights=weights_df,
    )


@when(u'I load ETF price data from the sample ETF file')
def step_load_etf_data(context) -> None:
    """Load ETF price data from the default sample ETF CSV file."""
    _require_imports()
    context.etf_data = load_sample_etf_data(filepath=_ETF_DATA_PATH)


@when(u'I calculate portfolio values with initial value {initial_value:g}')
def step_calculate_portfolio_values(context, initial_value: float) -> None:
    """Calculate time-series portfolio values."""
    _require_imports()
    context.portfolio_values = calculate_portfolio_values(
        portfolio_obj=context.portfolio,
        price_data=context.etf_data,
        initial_value=float(initial_value),
    )


@when(u'I create a benchmark from the portfolio values')
def step_create_benchmark(context) -> None:
    """Create benchmark portfolio values from calculated portfolio values."""
    _require_imports()
    context.benchmark_values = create_benchmark_portfolio_values(
        portfolio_values = context.portfolio_values
    )


# ===========================================================================
# Then — name and component assertions
# ===========================================================================


@then(u'the portfolio name should be "{expected_name}"')
def step_portfolio_name(context, expected_name: str) -> None:
    """Step portfolio name."""
    actual = context.portfolio.get_portfolio_name
    assert actual == expected_name, (
        f"Portfolio name mismatch: expected '{expected_name}', got '{actual}'"
    )


@then(u'the portfolio should have {count:d} components')
def step_portfolio_component_count(context, count: int) -> None:
    """Step portfolio component count."""
    actual = context.portfolio.get_num_components
    assert actual == count, (
        f"Component count mismatch: expected {count}, got {actual}"
    )


@then(u'the component list should contain "{component}"')
def step_component_in_list(context, component: str) -> None:
    """Step component in list."""
    components = context.portfolio.get_portfolio_components
    assert component in components, (
        f"Component '{component}' not found. Available: {components}"
    )


@then(u'the two portfolios should be distinct objects')
def step_portfolios_distinct(context) -> None:
    """Step portfolios distinct."""
    assert context.portfolio is not context.portfolio2, (
        "Expected two distinct portfolio objects but got the same instance"
    )


# ===========================================================================
# Then — weights DataFrame assertions
# ===========================================================================


@then(u'the weights DataFrame should have a "{col}" column')
def step_weights_df_has_column(context, col: str) -> None:
    """Step weights df has column."""
    weights = context.portfolio.get_portfolio_weights()
    assert col in weights.columns, (
        f"Column '{col}' not found in weights DataFrame. Available: {weights.columns}"
    )


@then(u'the weights for each row should sum to approximately 1.0')
def step_weights_sum_to_one(context) -> None:
    """Step weights sum to one."""
    weights = context.portfolio.get_portfolio_weights()
    numeric_cols = [c for c in weights.columns if c != "Date"]
    for row_idx in range(weights.height):
        row_sum = sum(float(weights[col][row_idx]) for col in numeric_cols)
        assert abs(row_sum - 1.0) <= 1e-4, (
            f"Row {row_idx} weights sum to {row_sum:.6f}; expected ≈ 1.0"
        )


# ===========================================================================
# Then — CSV / general creation assertions
# ===========================================================================


@then(u'the portfolio should be created without error')
def step_portfolio_created(context) -> None:
    """Step portfolio created."""
    assert context.portfolio is not None, "Portfolio was not created (is None)"


@then(u'the portfolio should have at least 1 component')
def step_portfolio_at_least_one_component(context) -> None:
    """Step portfolio at least one component."""
    count = context.portfolio.get_num_components
    assert count >= 1, f"Expected at least 1 component but got {count}"


# ===========================================================================
# Then — portfolio values assertions
# ===========================================================================


@then(u'the portfolio values DataFrame should not be empty')
def step_portfolio_values_not_empty(context) -> None:
    """Step portfolio values not empty."""
    _require_imports()
    df = context.portfolio_values
    assert isinstance(df, pl.DataFrame), (
        f"Expected pl.DataFrame for portfolio values, got {type(df).__name__}"
    )
    assert not df.is_empty(), "Portfolio values DataFrame is empty"


@then(u'the first portfolio value should equal {expected_value:g}')
def step_first_portfolio_value(context, expected_value: float) -> None:
    """Step first portfolio value."""
    first = context.portfolio_values["Portfolio_Value"][0]
    assert first is not None, "First Portfolio_Value is None"
    assert abs(float(first) - float(expected_value)) <= 1e-3, (
        f"Expected first Portfolio_Value ≈ {expected_value}, got {first}"
    )


@then(u'all portfolio values should be positive')
def step_all_portfolio_values_positive(context) -> None:
    """Step all portfolio values positive."""
    min_val = context.portfolio_values["Portfolio_Value"].min()
    assert min_val is not None and float(min_val) > 0.0, (
        f"All Portfolio_Value entries must be > 0. Minimum found: {min_val}"
    )


# ===========================================================================
# Then — benchmark assertions
# ===========================================================================


@then(u'the benchmark values should differ from the source values')
def step_benchmark_differs(context) -> None:
    """Step benchmark differs."""
    port_list = context.portfolio_values["Portfolio_Value"].to_list()
    # create_benchmark_portfolio_values returns a DataFrame with a 'Value' column
    bench_col = "Value" if "Value" in context.benchmark_values.columns else "Portfolio_Value"
    bench_list = context.benchmark_values[bench_col].to_list()
    assert port_list != bench_list, (
        "Benchmark values are identical to portfolio values — expected divergence"
    )


# ===========================================================================
# When — utils_portfolio: create_sample_portfolio_weights
# ===========================================================================


@when(u'I create sample portfolio weights from the ETF data')
def step_create_sample_weights(context) -> None:
    """Create deterministic sample portfolio weights from ETF price data."""
    _require_imports()
    context.sample_weights = create_sample_portfolio_weights(etf_data = context.etf_data)


@when(u'I save the sample weights to a temporary CSV file')
def step_save_weights_to_temp_csv(context) -> None:
    """Save sample weights to a temporary CSV file."""
    import tempfile
    _require_imports()
    context.temp_csv_path = Path(tempfile.mkstemp(suffix=".csv")[1])
    context.sample_weights.write_csv(context.temp_csv_path)


@when(u'I reload the saved weights CSV file')
def step_reload_weights_csv(context) -> None:
    """Reload weights from the temporary CSV file."""
    _require_imports()
    context.reloaded_weights = pl.read_csv(context.temp_csv_path)


@when(u'I create a custom portfolio with components "{components}" and date "{date_str}"')
def step_create_custom_portfolio(context, components: str, date_str: str) -> None:
    """Create a custom portfolio via create_custom_portfolio utility."""
    _require_imports()
    names_list = [c.strip() for c in components.split(",")]
    context.portfolio = create_custom_portfolio(components = names_list, date=date_str)


@when(u'I suggest matches for components "{comps}" against ETF columns "{etfs}"')
def step_suggest_matches(context, comps: str, etfs: str) -> None:
    """Suggest component matches between portfolio and ETF columns."""
    _require_imports()
    comp_list = [c.strip() for c in comps.split(",")]
    etf_list = [e.strip() for e in etfs.split(",")]
    context.suggestions = suggest_component_matches(components = comp_list, etf_columns = etf_list)


@when(u'I ensure a path exists at a temporary location')
def step_ensure_path_exists(context) -> None:
    """Ensure a temporary directory path exists."""
    import tempfile
    _require_imports()
    context.temp_dir = Path(tempfile.mkdtemp()) / "new_subdir"
    context.ensured_path = ensure_path_exists(path = context.temp_dir)


@when(u'I add weights for date "{date_str}" with {comp_a}={weight_a:g} and {comp_b}={weight_b:g}')
def step_add_weights(context, date_str: str, comp_a: str, weight_a: float, comp_b: str, weight_b: float) -> None:
    """Add a new weights row to the portfolio."""
    _require_imports()
    context.portfolio.add_weights(
        input_date=date_str,
        weights={comp_a: weight_a, comp_b: weight_b},
    )


@when(u'I modify weights for date "{date_str}" with {comp_a}={weight_a:g} and {comp_b}={weight_b:g}')
def step_modify_weights(context, date_str: str, comp_a: str, weight_a: float, comp_b: str, weight_b: float) -> None:
    """Modify existing weights in the portfolio."""
    from datetime import datetime as dt
    _require_imports()
    if date_str == "<today>":
        date_str = dt.now().strftime("%Y-%m-%d")
    context.portfolio.modify_weights(
        input_date=date_str,
        new_weights={comp_a: weight_a, comp_b: weight_b},
    )


# ===========================================================================
# Then — sample weights assertions
# ===========================================================================


@then(u'the sample weights DataFrame should have a "{col}" column')
def step_sample_weights_has_column(context, col: str) -> None:
    """Assert sample weights DataFrame has the specified column."""
    assert col in context.sample_weights.columns, (
        f"Column '{col}' not found in sample weights. Available: {context.sample_weights.columns}"
    )


@then(u'each row of sample weights should sum to approximately 1.0')
def step_sample_weights_sum_to_one(context) -> None:
    """Assert each row of sample weights sums to ~1.0."""
    numeric_cols = [c for c in context.sample_weights.columns if c != "Date"]
    for row_idx in range(context.sample_weights.height):
        row_sum = sum(float(context.sample_weights[col][row_idx]) for col in numeric_cols)
        assert abs(row_sum - 1.0) <= 1e-4, (
            f"Row {row_idx} weights sum to {row_sum:.6f}; expected ≈ 1.0"
        )


@then(u'the reloaded weights should match the original weights')
def step_reloaded_matches_original(context) -> None:
    """Assert reloaded CSV weights match the original sample weights."""
    _require_imports()
    # Compare column sets
    orig_cols = set(context.sample_weights.columns)
    reloaded_cols = set(context.reloaded_weights.columns)
    assert orig_cols == reloaded_cols, (
        f"Column mismatch: original={orig_cols}, reloaded={reloaded_cols}"
    )
    # Compare row counts
    assert context.sample_weights.height == context.reloaded_weights.height, (
        f"Row count mismatch: original={context.sample_weights.height}, "
        f"reloaded={context.reloaded_weights.height}"
    )


@then(u'the weights date should be "{expected_date}"')
def step_weights_date_is(context, expected_date: str) -> None:
    """Assert the portfolio weights date matches expected."""
    weights = context.portfolio.get_portfolio_weights()
    actual_date = str(weights["Date"][0])
    assert actual_date == expected_date, (
        f"Date mismatch: expected '{expected_date}', got '{actual_date}'"
    )


@then(u'the suggestion for "{comp}" should include "{match}"')
def step_suggestion_includes(context, comp: str, match: str) -> None:
    """Assert a component suggestion includes the expected match."""
    assert comp in context.suggestions, (
        f"No suggestions found for component '{comp}'"
    )
    assert match in context.suggestions[comp], (
        f"Expected '{match}' in suggestions for '{comp}', "
        f"got {context.suggestions[comp]}"
    )


@then(u'the path should exist on disk')
def step_path_exists_on_disk(context) -> None:
    """Assert the ensured path exists on disk."""
    assert context.ensured_path.exists(), (
        f"Path {context.ensured_path} does not exist on disk"
    )


@then(u'the portfolio weights should have {count:d} rows')
def step_portfolio_weights_row_count(context, count: int) -> None:
    """Assert the portfolio weights DataFrame has the expected number of rows."""
    actual = len(context.portfolio.get_portfolio_weights())
    assert actual == count, (
        f"Expected {count} rows in weights DataFrame, got {actual}"
    )


@then(u'the weights for date "{date_str}" should have {comp_a}={weight_a:g} and {comp_b}={weight_b:g}')
def step_weights_for_date(context, date_str: str, comp_a: str, weight_a: float, comp_b: str, weight_b: float) -> None:
    """Assert weights for a specific date match expected values."""
    from datetime import date as _date
    from datetime import datetime as dt
    _require_imports()
    if date_str == "<today>":
        date_str = dt.now().strftime("%Y-%m-%d")
    df = context.portfolio.get_portfolio_weights()
    target_date = _date.fromisoformat(date_str)
    row = df.filter(pl.col("Date") == target_date)
    assert len(row) == 1, f"Expected 1 row for date {date_str}, got {len(row)}"
    actual_a = float(row[comp_a][0])
    actual_b = float(row[comp_b][0])
    assert abs(actual_a - weight_a) <= 1e-4, (
        f"Weight mismatch for {comp_a}: expected {weight_a}, got {actual_a}"
    )
    assert abs(actual_b - weight_b) <= 1e-4, (
        f"Weight mismatch for {comp_b}: expected {weight_b}, got {actual_b}"
    )
