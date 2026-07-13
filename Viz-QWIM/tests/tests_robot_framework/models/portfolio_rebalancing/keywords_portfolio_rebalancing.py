"""
Robot Framework keyword library for Portfolio_Rebalancing_Standard.
====================================================================

Tests cover:
    - Construction with valid/invalid parameters
    - configure() with valid weights and asset names
    - should_rebalance() threshold trigger
    - rebalance() output structure and drift values
    - get_summary_statistics() structure
    - Properties after configure

Author:         QWIM Development Team
Version:        0.1.0
Last Modified:  2026-05-27
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Robot Framework / stderr patch
# ---------------------------------------------------------------------------
if not hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")

# ---------------------------------------------------------------------------
# Conditional imports
# ---------------------------------------------------------------------------
MODULE_IMPORT_AVAILABLE: bool = True
_import_error_message: str = ""

try:
    import numpy as np
    import polars as pl
    from src.models.portfolio_rebalancing.portfolio_rebalancing_standard import (
        Portfolio_Rebalancing_Standard,
    )
    from src.utils.custom_exceptions_errors_loggers.exception_custom import (
        Exception_Validation_Input,
    )
except Exception as _exc:  # noqa: BLE001
    MODULE_IMPORT_AVAILABLE = False
    _import_error_message = str(_exc)


class Keywords_Portfolio_Rebalancing:
    """Robot Framework keyword library for portfolio rebalancing tests."""

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def check_module_available(self) -> None:
        """Fail if the rebalancing module could not be imported."""
        if not MODULE_IMPORT_AVAILABLE:
            raise AssertionError(
                f"Portfolio rebalancing module import failed: {_import_error_message}"
            )

    # ------------------------------------------------------------------
    # Construction keywords
    # ------------------------------------------------------------------

    def construct_standard_strategy(
        self,
        tolerance_abs: float = 0.05,
        rebalancing_frequency_days: int = 0,
        transaction_cost_bps: float = 10.0,
        name_strategy: str = "RF_Test_Strategy",
    ) -> Portfolio_Rebalancing_Standard:
        """Construct and return a ``Portfolio_Rebalancing_Standard``.

        Parameters
        ----------
        tolerance_abs : float
            Drift tolerance; default 0.05.
        rebalancing_frequency_days : int
            Calendar frequency in days; default 0 (disabled).
        transaction_cost_bps : float
            Cost in basis points; default 10.0.
        name_strategy : str
            Human-readable strategy name.

        Returns
        -------
        Portfolio_Rebalancing_Standard
        """
        return Portfolio_Rebalancing_Standard(
            name_strategy=str(name_strategy),
            tolerance_abs=float(tolerance_abs),
            rebalancing_frequency_days=int(rebalancing_frequency_days),
            transaction_cost_bps=float(transaction_cost_bps),
        )

    def construct_strategy_raises_for_invalid_tolerance(
        self, tolerance_abs: float
    ) -> None:
        """Assert that constructing with *tolerance_abs* raises a validation error.

        Parameters
        ----------
        tolerance_abs : float
            Invalid tolerance value.
        """
        try:
            Portfolio_Rebalancing_Standard(tolerance_abs=float(tolerance_abs))
            raise AssertionError(
                f"Expected Exception_Validation_Input for tolerance_abs={tolerance_abs}"
            )
        except Exception_Validation_Input:
            pass

    # ------------------------------------------------------------------
    # Configure keywords
    # ------------------------------------------------------------------

    def configure_strategy_equal_weights(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        n_assets: int,
    ) -> Portfolio_Rebalancing_Standard:
        """Configure *strategy* with equal weights for *n_assets* assets.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Strategy to configure (mutated in-place).
        n_assets : int
            Number of assets.

        Returns
        -------
        Portfolio_Rebalancing_Standard
            The configured strategy (same object).
        """
        n = int(n_assets)
        target = np.ones(n) / n
        names = [f"Asset{i + 1}" for i in range(n)]
        return strategy.configure(target_weights = target, names_assets = names)

    # ------------------------------------------------------------------
    # should_rebalance keywords
    # ------------------------------------------------------------------

    def should_rebalance_returns_true(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        *weights: float,
    ) -> None:
        """Assert that should_rebalance returns True for the given weights.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Configured strategy.
        weights : float
            Current weights as positional arguments.
        """
        current = np.array([float(w) for w in weights])
        result = strategy.should_rebalance(current_weights = current)
        assert result is True, f"Expected should_rebalance=True, got {result}"

    def should_rebalance_returns_false(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        *weights: float,
    ) -> None:
        """Assert that should_rebalance returns False for the given weights.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Configured strategy.
        weights : float
            Current weights as positional arguments.
        """
        current = np.array([float(w) for w in weights])
        result = strategy.should_rebalance(current_weights = current)
        assert result is False, f"Expected should_rebalance=False, got {result}"

    # ------------------------------------------------------------------
    # rebalance keywords
    # ------------------------------------------------------------------

    def rebalance_returns_dataframe(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        portfolio_value: float,
        *weights: float,
    ) -> pl.DataFrame:
        """Perform rebalance and return the result DataFrame.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Configured strategy.
        portfolio_value : float
            Total portfolio value.
        weights : float
            Current weights as positional arguments.

        Returns
        -------
        pl.DataFrame
        """
        current = np.array([float(w) for w in weights])
        return strategy.rebalance(current_weights = current, portfolio_value=float(portfolio_value))

    def rebalance_has_n_columns(self, df: pl.DataFrame, n: int) -> None:
        """Assert *df* has exactly *n* columns.

        Parameters
        ----------
        df : pl.DataFrame
        n : int
        """
        actual = len(df.columns)
        assert actual == int(n), f"Expected {n} columns, got {actual}"

    def rebalance_has_n_rows(self, df: pl.DataFrame, n: int) -> None:
        """Assert *df* has exactly *n* rows.

        Parameters
        ----------
        df : pl.DataFrame
        n : int
        """
        actual = len(df)
        assert actual == int(n), f"Expected {n} rows, got {actual}"

    def rebalance_drift_at_target_is_zero(
        self,
        strategy: Portfolio_Rebalancing_Standard,
    ) -> None:
        """Rebalancing exactly-at-target weights produces zero drift for all assets.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Configured strategy.
        """
        target = strategy.m_target_weights.copy()
        result = strategy.rebalance(current_weights = target)
        for drift_value in result["Drift"].to_list():
            assert abs(drift_value) < 1e-9, f"Drift should be ~0, got {drift_value}"

    # ------------------------------------------------------------------
    # get_summary_statistics keywords
    # ------------------------------------------------------------------

    def summary_statistics_has_expected_columns(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        *weights: float,
    ) -> None:
        """Assert get_summary_statistics output has the 5 expected columns.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
            Configured strategy.
        weights : float
            Current weights as positional arguments.
        """
        current = np.array([float(w) for w in weights])
        result_df = strategy.rebalance(current_weights = current, portfolio_value=1_000_000.0)
        summary = strategy.get_summary_statistics(rebalancing_result = result_df)
        expected = {"Max_Abs_Drift", "Mean_Abs_Drift", "Turnover", "Total_Trade_Value", "Total_Cost"}
        actual = set(summary.columns)
        assert actual == expected, f"Column mismatch: {actual} vs {expected}"

    # ------------------------------------------------------------------
    # Properties keywords
    # ------------------------------------------------------------------

    def strategy_is_configured(
        self, strategy: Portfolio_Rebalancing_Standard
    ) -> None:
        """Assert strategy.is_configured is True.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
        """
        assert strategy.is_configured is True, (
            f"Expected is_configured=True, got {strategy.is_configured}"
        )

    def strategy_tolerance_is(
        self,
        strategy: Portfolio_Rebalancing_Standard,
        expected: float,
    ) -> None:
        """Assert strategy.tolerance_abs equals *expected* within 1e-9.

        Parameters
        ----------
        strategy : Portfolio_Rebalancing_Standard
        expected : float
        """
        actual = strategy.tolerance_abs
        assert abs(actual - float(expected)) < 1e-9, (
            f"Expected tolerance_abs={expected}, got {actual}"
        )
