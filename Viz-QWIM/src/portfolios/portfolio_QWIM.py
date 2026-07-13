"""Portfolio Module.

This module provides functionality for managing financial portfolios with time-varying weights.

Classes
-------
portfolio_QWIM
    A class representing a financial portfolio with weights of components over time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Self

import attrs
import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Portfolio,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from ._portfolio_QWIM_dates import _parse_portfolio_date_QWIM


#: Module-level logger instance
_logger = get_logger(name = __name__)


@attrs.define(kw_only=True)
class Portfolio_QWIM:
    """A class representing a financial portfolio with weights of components over time.

    The portfolio is represented as a DataFrame with dates and component weights.

    Attributes
    ----------
    m_portfolio_name : str
        Name of the portfolio.
    m_portfolio_weights : pl.DataFrame
        DataFrame containing dates and portfolio weights.
    m_portfolio_components : list[str]
        List of strings containing names of the portfolio components.
    m_num_components : int
        Number of portfolio components.

    Examples
    --------
    Creating a portfolio with equal weights:

    >>> import polars as pl
    >>> from src.portfolios.portfolio_QWIM import Portfolio_QWIM
    >>> # Create portfolio with equal weights for three components
    >>> p1 = Portfolio_QWIM(
    ...     name_portfolio="Tech Portfolio", names_components=["AAPL", "MSFT", "GOOG"]
    ... )
    >>> p1.get_portfolio_components
    ['AAPL', 'MSFT', 'GOOG']
    >>> p1.get_num_components
    3
    >>> p1.get_portfolio_name
    'Tech Portfolio'

    Creating a portfolio from existing data:

    >>> # Create portfolio from existing data
    >>> df = pl.DataFrame(
    ...     {"Date": ["2023-01-01", "2023-02-01"], "AAPL": [0.5, 0.6], "MSFT": [0.5, 0.4]}
    ... )
    >>> p2 = Portfolio_QWIM(name_portfolio="Apple-Microsoft Mix", portfolio_weights=df)
    >>> p2.get_num_components
    2
    >>> p2.get_portfolio_name
    'Apple-Microsoft Mix'
    """

    # ------------------------------------------------------------------
    # attrs fields — keyword-only, mutable (frozen=False)
    # ------------------------------------------------------------------

    m_portfolio_name: str = attrs.field(init=False, default="")
    m_portfolio_weights: pl.DataFrame = attrs.field(init=False, default=attrs.Factory(pl.DataFrame))
    m_portfolio_components: list[str] = attrs.field(init=False, default=attrs.Factory(list))
    m_num_components: int = attrs.field(init=False, default=0)

    # User-facing init parameters (not stored directly)
    name_portfolio: str = attrs.field()
    portfolio_weights: pl.DataFrame | None = attrs.field(default=None)
    names_components: list[str] | None = attrs.field(default=None)
    date_portfolio: str | datetime | None = attrs.field(default=None)

    @name_portfolio.validator
    def _validate_name_portfolio(self, attribute: attrs.Attribute, value: str) -> None:
        """Validate that name_portfolio is a non-empty string."""
        if not isinstance(value, str) or not value.strip():
            raise Exception_Validation_Input(
                "Portfolio name must be a non-empty string",
            )

    def __attrs_post_init__(self) -> None:
        """Validate and initialize portfolio state after attrs construction."""
        try:
            # Set the canonical portfolio name
            self.m_portfolio_name = self.name_portfolio.strip()

            # Determine initialization mode
            has_weights = self.portfolio_weights is not None
            has_components = self.names_components is not None

            if not has_weights and not has_components:
                raise Exception_Validation_Input(
                    "Either portfolio_weights or names_components must be provided",
                )

            # Initialize from weights DataFrame
            if has_weights:
                try:
                    # Validate DataFrame
                    self.m_validate_dataframe(
                        df=self.portfolio_weights, df_name="portfolio_weights",
                    )

                    # Coerce types to canonical form (pl.Date for dates, Float64 for weights)
                    coerced = self.m_coerce_dataframe(df=self.portfolio_weights)

                    # Extract component names
                    self.m_portfolio_components = [
                        item_col for item_col in coerced.columns if item_col != "Date"
                    ]
                    self.m_num_components = len(self.m_portfolio_components)

                    # Validate and potentially correct weights
                    corrected_weights = self.m_validate_weights(
                        df=coerced,
                        component_cols=self.m_portfolio_components,
                    )

                    # Ensure Date is first column
                    cols = ["Date"] + self.m_portfolio_components
                    self.m_portfolio_weights = corrected_weights.select(cols)

                except Exception as weights_init_error:
                    if isinstance(
                        weights_init_error,
                        (ValueError, TypeError, Exception_Validation_Input),
                    ):
                        raise
                    raise Exception_Validation_Input(
                        f"Error initializing from weights DataFrame: {weights_init_error!s}",
                    ) from weights_init_error  # pragma: no cover
            else:
                try:
                    # Validate component names
                    self.m_validate_type_and_value(
                        var=self.names_components,
                        var_name="names_components",
                        expected_type=list,
                        additional_check=lambda x: len(x) > 0,
                        error_msg="names_components cannot be empty",
                    )

                    # Validate each component name
                    for idx, idx_name in enumerate(self.names_components):
                        self.m_validate_type_and_value(
                            var=idx_name,
                            var_name=f"Component name at index {idx}",
                            expected_type=str,
                            additional_check=lambda x: len(x.strip()) > 0,
                            error_msg=f"Component name at index {idx} must be a non-empty string",
                        )

                    # Validate uniqueness
                    if len(set(self.names_components)) != len(self.names_components):
                        raise Exception_Validation_Input("Component names must be unique")

                    # Store clean component names
                    self.m_portfolio_components = [
                        item_name.strip() for item_name in self.names_components
                    ]
                    self.m_num_components = len(self.m_portfolio_components)

                    # Parse date
                    parsed_date = self.m_parse_date(date_input=self.date_portfolio)

                    # Create equal weights
                    equal_weight = 1.0 / self.m_num_components

                    # Create DataFrame
                    data_temp: dict[str, Any] = {"Date": [date.fromisoformat(parsed_date)]}
                    for idx_component in self.m_portfolio_components:
                        data_temp[idx_component] = [equal_weight]

                    self.m_portfolio_weights = pl.DataFrame(data_temp)

                except Exception as components_init_error:
                    if isinstance(
                        components_init_error,
                        (ValueError, TypeError, Exception_Validation_Input),
                    ):
                        raise
                    raise Exception_Validation_Input(
                        f"Error initializing from component names: {components_init_error!s}",
                    ) from components_init_error  # pragma: no cover

        except Exception as portfolio_init_error:
            # Add more context to the error
            if isinstance(
                portfolio_init_error,
                (ValueError, TypeError, Exception_Validation_Input),
            ):
                raise
            raise Exception_Portfolio(
                f"Unexpected error initializing portfolio: {portfolio_init_error!s}",
            ) from portfolio_init_error  # pragma: no cover

    def m_initialize_from_dataframe(self, *, portfolio_weights: pl.DataFrame) -> None:
        """Initialize portfolio from a DataFrame containing weights.

        Parameters
        ----------
        portfolio_weights : pl.DataFrame
            DataFrame with dates and portfolio weights.

        Raises
        ------
        ValueError
            If portfolio_weights does not have a 'Date' column.

        Warning
        -------
        This method assumes that all non-Date columns are portfolio components.
        Ensure your DataFrame doesn't contain any non-component columns besides 'Date'.
        """
        # Further validation (already checked for 'Date' and >1 column in __init__)
        if portfolio_weights.is_empty():
            raise Exception_Validation_Input("portfolio_weights DataFrame cannot be empty")

        # Extract component names (all columns except 'Date')
        components = [item_col for item_col in portfolio_weights.columns if item_col != "Date"]
        if not components:  # pragma: no cover
            raise Exception_Validation_Input(
                "portfolio_weights DataFrame must have component columns besides 'Date'",
            )

        # Validate component columns are numeric (or can be cast)
        df_clone = portfolio_weights.clone()  # Work on a clone for validation/casting
        for item_col in components:  # pragma: no branch
            try:
                # Attempt to cast to Float64, allow nulls on failure initially
                df_clone = df_clone.with_columns(pl.col(item_col).cast(pl.Float64, strict=False))
                # Check if the column became all nulls after casting
                if df_clone.select(pl.col(item_col).is_null()).sum().item() == df_clone.height:
                    raise Exception_Validation_Input(
                        f"Component column '{item_col}' contains no valid numeric data.",
                    )
            except Exception as e:
                raise Exception_Validation_Input(
                    f"Error validating or casting component column '{item_col}': {e}",
                ) from e
        # Validate weights
        df_clone = self.m_validate_weights(df=df_clone, component_cols=components)

        # Store the validated/potentially cast dataframe
        self.m_portfolio_weights = df_clone
        self.m_portfolio_components = components
        self.m_num_components = len(self.m_portfolio_components)

        # Validate that Date is the first column
        if portfolio_weights.columns[0] != "Date":
            # Reorder columns to ensure Date is first
            cols = ["Date"] + self.m_portfolio_components
            self.m_portfolio_weights = self.m_portfolio_weights.select(cols)

    def m_initialize_from_components(
        self,
        *,
        names_components: list[str],
        date_portfolio: str | datetime | None = None,
    ) -> None:
        r"""Initialize portfolio with equal weights for given components.

        Parameters
        ----------
        names_components : List[str]
            Names of portfolio components.
        date_portfolio : str or datetime, optional
            Date for the portfolio weights, defaults to current date if not provided.

        Notes
        -----
        Equal weights are calculated as:

        .. math::
           w_i = \\frac{1}{n}

        Where:

        - :math:`w_i` is the weight of component :math:`i`
        - :math:`n` is the number of components
        """
        # Set the date with validation
        formatted_date = self.m_parse_date(date_input=date_portfolio)

        # Calculate equal weights
        num_components = len(names_components)
        if num_components == 0:  # pragma: no cover
            raise Exception_Validation_Input("Cannot initialize with zero components")
        equal_weight = 1.0 / num_components

        # Create the dataframe with one row
        data_date: dict[str, Any] = {
            "Date": [date.fromisoformat(formatted_date)],
        }  # Use validated date
        for idx_component in names_components:  # pragma: no branch
            data_date[idx_component] = [equal_weight]

        # Store the portfolio data
        self.m_portfolio_weights = pl.DataFrame(data_date)
        self.m_portfolio_components = names_components
        self.m_num_components = num_components

    def m_validate_type_and_value(
        self,
        *,
        var: Any,
        var_name: str,
        expected_type: type | tuple[type, ...],
        allow_none: bool = False,
        additional_check: Callable[[Any], bool] | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Validate variable type and optionally its value.

        Parameters
        ----------
        var : Any
            Variable to validate
        var_name : str
            Name of the variable for error messages
        expected_type : type or tuple of types
            Expected type(s) for the variable
        allow_none : bool, optional
            Whether None is allowed, by default False
        additional_check : callable, optional
            Additional validation function taking var as input, by default None
        error_msg : str, optional
            Custom error message, by default None

        Returns
        -------
        bool
            True if validation passes

        Raises
        ------
        TypeError
            If type validation fails
        ValueError
            If additional validation fails
        """
        # Check for None if not allowed
        if var is None:
            if allow_none:
                return
            raise Exception_Validation_Input(f"{var_name} cannot be None")

        # Type check
        if not isinstance(var, expected_type):
            type_names = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else " or ".join(t.__name__ for t in expected_type)
            )
            raise TypeError(f"{var_name} must be of type {type_names}, got {type(var).__name__}")

        # Additional validation
        if additional_check is not None and not additional_check(var):
            raise Exception_Validation_Input(error_msg or f"Invalid value for {var_name}")

    def m_validate_dataframe(
        self,
        *,
        df: Any,
        df_name: str = "input_DataFrame",
    ) -> bool:
        """Thoroughly validate a DataFrame.

        Parameters
        ----------
        df : pl.DataFrame
            DataFrame to validate
        df_name : str, optional
            Name of DataFrame for error messages, by default "DataFrame"

        Returns
        -------
        bool
            True if validation passes

        Raises
        ------
        TypeError
            If df is not a pl.DataFrame
        ValueError
            If validation fails
        """
        # Type check
        if not isinstance(df, pl.DataFrame):
            raise TypeError(f"{df_name} must be a polars DataFrame, got {type(df).__name__}")

        # Check if empty
        if df.is_empty():
            raise Exception_Validation_Input(f"{df_name} cannot be empty")

        # Check for required Date column
        if "Date" not in df.columns:
            raise Exception_Validation_Input(f"{df_name} must have a 'Date' column")

        # Check number of columns
        if len(df.columns) < 2:
            raise Exception_Validation_Input(
                f"{df_name} must have at least one component column besides 'Date'",
            )

        # Validate Date column
        try:
            # Check Date column type and try to cast if needed
            date_col_type = df.schema["Date"]

            if date_col_type not in (pl.Date, pl.Datetime, pl.Utf8):
                # Try to convert the column
                df = df.with_columns(pl.col("Date").cast(pl.Date, strict=False))

                # Check if conversion worked
                if (
                    df.select(pl.col("Date").is_null()).sum().item() == df.height
                ):  # pragma: no cover
                    raise Exception_Validation_Input(
                        f"Date column in {df_name} could not be converted to a valid date format",
                    )
        except Exception as e:  # pragma: no cover
            raise Exception_Validation_Input(
                f"Error validating Date column in {df_name}: {e!s}",
            ) from e

        # Identify component columns
        component_cols = [item_col for item_col in df.columns if item_col != "Date"]

        # Validate component columns are numeric
        for item_col in component_cols:
            try:
                # Count nulls before casting
                nulls_before = df.select(pl.col(item_col).is_null()).sum().item()

                # Try to cast to numeric
                test_df = df.with_columns(pl.col(item_col).cast(pl.Float64, strict=False))

                # Count nulls after casting
                nulls_after = test_df.select(pl.col(item_col).is_null()).sum().item()

                # Check if casting introduced new nulls
                if nulls_after > nulls_before:
                    raise Exception_Validation_Input(
                        f"Column '{item_col}' contains non-numeric values that cannot be converted",
                    )

                # Check for all nulls
                if nulls_after == df.height:
                    raise Exception_Validation_Input(
                        f"Column '{item_col}' contains no valid numeric data",
                    )

            except Exception as e:
                raise Exception_Validation_Input(
                    f"Error validating component column '{item_col}': {e!s}",
                ) from e
        return True

    def m_coerce_dataframe(self, *, df: pl.DataFrame) -> pl.DataFrame:
        """Coerce DataFrame column types to canonical types.

        Casts the ``Date`` column to :class:`polars.Date` and all component
        columns to :class:`polars.Float64`.  A clone is always returned so
        the caller's DataFrame is never mutated.

        Call this method after :meth:`m_validate_dataframe` has confirmed the
        DataFrame is structurally valid.

        Parameters
        ----------
        df : pl.DataFrame
            DataFrame to coerce.  Must have a ``Date`` column and at least one
            component column.

        Returns
        -------
        pl.DataFrame
            Type-coerced clone of the input DataFrame.
        """
        coerced = df.clone()
        date_dtype = coerced.schema["Date"]
        if date_dtype == pl.Utf8:
            coerced = coerced.with_columns(
                pl.col("Date").str.to_date("%Y-%m-%d", strict=False).alias("Date"),
            )
        elif date_dtype != pl.Date:
            coerced = coerced.with_columns(
                pl.col("Date").cast(pl.Date, strict=False).alias("Date"),
            )
        component_cols = [c for c in coerced.columns if c != "Date"]
        if component_cols:
            coerced = coerced.with_columns(
                [pl.col(c).cast(pl.Float64, strict=False).alias(c) for c in component_cols],
            )
        return coerced

    def m_validate_weights(
        self,
        *,
        df: pl.DataFrame,
        component_cols: list[str],
    ) -> pl.DataFrame:
        """Validate portfolio weights.

        Parameters
        ----------
        df : pl.DataFrame
            DataFrame with weights
        component_cols : list
            List of component column names

        Returns
        -------
        pl.DataFrame
            Validated and potentially corrected DataFrame

        Raises
        ------
        ValueError
            If weights are invalid and cannot be corrected
        """
        try:
            # Create a clone to work with
            validated_df = df.clone()

            # Check for negative weights
            for item_col in component_cols:
                has_negative = validated_df.select(pl.col(item_col) < 0).to_series().any()
                if has_negative:
                    # Log warning and set negative weights to 0
                    _logger.warning("Negative weights found in {!r} and set to 0", item_col)  # noqa: PLE1205  # false positive: loguru-style logger
                    validated_df = validated_df.with_columns(
                        pl.when(pl.col(item_col) < 0)
                        .then(0)
                        .otherwise(pl.col(item_col))
                        .alias(item_col),
                    )

            # Check row sums
            row_sums = validated_df.select(
                [
                    pl.sum_horizontal(component_cols).alias("sum"),
                ],
            )

            # Add row index for better error reporting
            row_sums = row_sums.with_row_index()

            # Check for rows with sum == 0
            zero_sum_rows = row_sums.filter(pl.col("sum") == 0)
            if not zero_sum_rows.is_empty():
                row_indices = zero_sum_rows.select("index").to_series().to_list()
                dates = validated_df.select(pl.col("Date")).filter(
                    pl.int_range(0, validated_df.height).is_in(row_indices),
                )
                date_str = ", ".join(str(d) for d in dates.to_series().to_list())
                raise Exception_Validation_Input(
                    f"Row(s) with all zero weights found for date(s): {date_str}",
                )

            # Check for rows with sum far from 1.0
            tolerance = 0.001  # 0.1% tolerance
            invalid_sum_rows = row_sums.filter(
                (pl.col("sum") < 1 - tolerance) | (pl.col("sum") > 1 + tolerance),
            )

            if not invalid_sum_rows.is_empty():
                # Normalise all out-of-tolerance rows in one vectorised pass (C2 fix)
                sum_col = pl.sum_horizontal(component_cols)
                need_norm = (sum_col < 1 - tolerance) | (sum_col > 1 + tolerance)
                validated_df = validated_df.with_columns(
                    [
                        pl.when(need_norm & (sum_col > 0))
                        .then(pl.col(c) / sum_col)
                        .otherwise(pl.col(c))
                        .alias(c)
                        for c in component_cols
                    ],
                )
                _logger.warning(
                    "Normalized %d row(s) with weight sums not equal to 1.0",
                    invalid_sum_rows.height,
                )

            return validated_df

        except Exception as e:
            if isinstance(e, (ValueError, Exception_Validation_Input)):
                raise
            raise Exception_Validation_Input(
                f"Error validating weights: {e!s}",
            ) from e  # pragma: no cover

    def m_parse_date(
        self,
        *,
        date_input: str | datetime | None,
    ) -> str:
        """Parse supported portfolio date inputs into YYYY-MM-DD strings."""
        return _parse_portfolio_date_QWIM(date_input=date_input)

    def get_portfolio_weights(self) -> pl.DataFrame:
        """Get the portfolio weights DataFrame.

        Returns
        -------
        pl.DataFrame
            A copy of the portfolio weights DataFrame.

        Notes
        -----
        Returns a clone of the internal DataFrame to prevent unintended modifications.
        """
        return self.m_portfolio_weights.clone()

    @property
    def get_portfolio_components(self) -> list[str]:
        """Get the list of portfolio components.

        Returns
        -------
        List[str]
            A copy of the list of portfolio component names.
        """
        return self.m_portfolio_components.copy()

    @property
    def get_num_components(self) -> int:
        """Get the number of portfolio components.

        Returns
        -------
        int
            The number of components in the portfolio.
        """
        return self.m_num_components

    @property
    def get_portfolio_name(self) -> str:
        """Get the name of the portfolio.

        Returns
        -------
        str
            The name of the portfolio.

        See Also
        --------
        set_portfolio_name : Method to set a new portfolio name
        """
        return self.m_portfolio_name

    def set_portfolio_name(self, *, name: str) -> None:
        """Set a new name for the portfolio.

        Parameters
        ----------
        name : str
            The new portfolio name.
        """
        if not isinstance(name, str) or not name:
            raise Exception_Validation_Input("Portfolio name must be a non-empty string")
        self.m_portfolio_name = name

    def __str__(self) -> str:
        """Return string representation of the portfolio.

        Returns
        -------
        str
            A string representation showing the portfolio name, number of components,
            and the portfolio weights.
        """
        return (
            f"Portfolio '{self.m_portfolio_name}' with {self.m_num_components} components:"
            f"\n{self.m_portfolio_weights}"
        )

    def __repr__(self) -> str:
        """Return string representation for developers.

        Returns
        -------
        str
            A detailed string representation showing the portfolio name, components,
            and number of dates.
        """
        return (
            f"portfolio_QWIM(name='{self.m_portfolio_name}', "
            f"components={self.m_portfolio_components}, "
            f"dates={len(self.m_portfolio_weights)} rows)"
        )

    def add_weights(
        self,
        *,
        input_date: str | datetime,
        weights: dict[str, float] | None = None,
        validate: bool = True,
    ) -> Self:
        """Add a new row of weights for a specific date.

        Parameters
        ----------
        input_date : Union[str, datetime, pl.Date, pl.Datetime]
            Date for the new weights
        weights : dict, optional
            Dictionary mapping component names to weights
            If None, uses equal weights for all components
        validate : bool, optional
            Whether to validate and normalize weights, by default True

        Returns
        -------
        portfolio_QWIM
            Self for method chaining

        Raises
        ------
        ValueError
            If date or weights are invalid
        """
        try:
            # Parse date
            parsed_date = self.m_parse_date(date_input=input_date)
            parsed_date_obj = date.fromisoformat(parsed_date)

            # Check if date already exists
            date_exists = (
                self.m_portfolio_weights.filter(pl.col("Date") == parsed_date_obj).height > 0
            )
            if date_exists:
                raise Exception_Validation_Input(f"Weights for date {parsed_date} already exist")

            # Create weights dictionary if not provided
            if weights is None:
                # Use equal weights
                equal_weight = 1.0 / self.m_num_components
                weights = dict.fromkeys(self.m_portfolio_components, equal_weight)
            else:
                # Validate weights dictionary
                self.m_validate_type_and_value(
                    var=weights,
                    var_name="weights",
                    expected_type=dict,
                    error_msg="weights must be a dictionary mapping component names to weight values",
                )

                # Check for missing components
                missing_components = [
                    item_comp
                    for item_comp in self.m_portfolio_components
                    if item_comp not in weights
                ]
                if missing_components:
                    raise Exception_Validation_Input(
                        f"Missing weights for components: {', '.join(missing_components)}",
                    )

                # Check for extra components
                extra_components = [
                    item_comp
                    for item_comp in weights
                    if item_comp not in self.m_portfolio_components
                ]
                if extra_components:
                    raise Exception_Validation_Input(
                        f"Unexpected components in weights: {', '.join(extra_components)}",
                    )

                # Check for negative weights
                neg_components = [item_comp for item_comp, idx_w in weights.items() if idx_w < 0]
                if neg_components:
                    if validate:
                        # Zero out negative weights
                        for idx_comp in neg_components:
                            _logger.warning("Negative weight for {!r} set to 0", idx_comp)  # noqa: PLE1205  # false positive: loguru-style logger
                            weights[idx_comp] = 0
                    else:
                        raise Exception_Validation_Input(
                            f"Negative weights not allowed for: {', '.join(neg_components)}",
                        )

                # Check sum of weights
                weight_sum = sum(weights.values())
                if abs(weight_sum - 1.0) > 0.001:  # More than 0.1% off
                    if validate and weight_sum > 0:
                        # Normalize weights
                        weights = {
                            item_comp: idx_w / weight_sum for item_comp, idx_w in weights.items()
                        }
                        _logger.warning("Weights summed to {}, normalized to 1.0", weight_sum)  # noqa: PLE1205  # false positive: loguru-style logger
                    else:
                        raise Exception_Validation_Input(
                            f"Sum of weights ({weight_sum}) is not close to 1.0",
                        )

            # Create new row
            new_row: dict[str, Any] = {"Date": parsed_date_obj}
            new_row.update(weights)

            # Append to DataFrame
            new_df = pl.DataFrame([new_row])
            self.m_portfolio_weights = pl.concat([self.m_portfolio_weights, new_df], how="vertical")

            # Sort by date
            self.m_portfolio_weights = self.m_portfolio_weights.sort("Date")

            return self

        except Exception as e:
            if isinstance(e, (ValueError, TypeError, Exception_Validation_Input)):
                raise
            raise Exception_Validation_Input(
                f"Error adding weights: {e!s}",
            ) from e  # pragma: no cover

    def modify_weights(
        self,
        *,
        input_date: str | datetime,
        new_weights: dict[str, float],
        validate: bool = True,
    ) -> Self:
        """Modify weights for a specific date.

        Parameters
        ----------
        input_date : Union[str, datetime, pl.Date, pl.Datetime]
            Date of weights to modify
        new_weights : dict
            Dictionary mapping component names to new weights
        validate : bool, optional
            Whether to validate and normalize weights, by default True

        Returns
        -------
        portfolio_QWIM
            Self for method chaining

        Raises
        ------
        ValueError
            If date or weights are invalid
        """
        try:
            # Parse date
            parsed_date = self.m_parse_date(date_input=input_date)
            parsed_date_obj = date.fromisoformat(parsed_date)

            # Check if date exists
            date_filter = self.m_portfolio_weights.filter(pl.col("Date") == parsed_date_obj)
            if date_filter.is_empty():
                raise Exception_Validation_Input(f"No weights exist for date {parsed_date}")

            # Validate weights dictionary
            self.m_validate_type_and_value(
                var=new_weights,
                var_name="new_weights",
                expected_type=dict,
                error_msg="new_weights must be a dictionary mapping component names to weight values",
            )

            # Check for invalid components
            invalid_components = [
                item_comp
                for item_comp in new_weights
                if item_comp not in self.m_portfolio_components
            ]
            if invalid_components:
                raise Exception_Validation_Input(
                    f"Invalid components in new_weights: {', '.join(invalid_components)}",
                )

            # Get current weights
            current_weights = {}
            for item_comp in self.m_portfolio_components:
                current_weights[item_comp] = date_filter.select(pl.col(item_comp))[0, 0]

            # Update with new weights
            current_weights.update(new_weights)

            # Check for negative weights
            neg_components = [
                item_comp for item_comp, idx_w in current_weights.items() if idx_w < 0
            ]
            if neg_components:
                if validate:
                    # Zero out negative weights
                    for item_comp in neg_components:
                        _logger.warning("Negative weight for {!r} set to 0", item_comp)  # noqa: PLE1205  # false positive: loguru-style logger
                        current_weights[item_comp] = 0
                else:
                    raise Exception_Validation_Input(
                        f"Negative weights not allowed for: {', '.join(neg_components)}",
                    )

            # Check sum of weights
            weight_sum = sum(current_weights.values())
            if abs(weight_sum - 1.0) > 0.001:  # More than 0.1% off
                if validate and weight_sum > 0:
                    # Normalize weights
                    current_weights = {
                        item_comp: idx_w / weight_sum
                        for item_comp, idx_w in current_weights.items()
                    }
                    _logger.warning("Modified weights summed to {}, normalized to 1.0", weight_sum)  # noqa: PLE1205  # false positive: loguru-style logger
                else:
                    raise Exception_Validation_Input(
                        f"Sum of modified weights ({weight_sum}) is not close to 1.0",
                    )

            # Update DataFrame
            for item_comp, item_weight in current_weights.items():
                self.m_portfolio_weights = self.m_portfolio_weights.with_columns(
                    [
                        pl.when(pl.col("Date") == parsed_date_obj)
                        .then(pl.lit(item_weight))
                        .otherwise(pl.col(item_comp))
                        .alias(item_comp),
                    ],
                )

            return self

        except Exception as e:
            if isinstance(e, (ValueError, TypeError, Exception_Validation_Input)):
                raise
            raise Exception_Validation_Input(
                f"Error modifying weights: {e!s}",
            ) from e  # pragma: no cover

    def validate_all_weights(
        self,
        *,
        normalize: bool = True,
    ) -> Self:
        """Validate all weights in the portfolio.

        Parameters
        ----------
        normalize : bool, optional
            Whether to normalize rows where sum != 1.0, by default True

        Returns
        -------
        portfolio_QWIM
            Self for method chaining

        Notes
        -----
        This method checks for and optionally corrects:
        - Negative weights (set to 0)
        - Rows where weights do not sum to 1.0 (normalize if normalize=True)
        """
        try:
            component_cols = self.m_portfolio_components

            # Validate and potentially correct weights
            corrected_weights = self.m_validate_weights(
                df=self.m_portfolio_weights,
                component_cols=component_cols,
            )

            # Ensure Date is first column
            cols = ["Date"] + component_cols
            self.m_portfolio_weights = corrected_weights.select(cols)

            return self

        except Exception as e:
            if isinstance(e, (ValueError, Exception_Validation_Input)):
                raise
            raise Exception_Validation_Input(
                f"Error validating weights: {e!s}",
            ) from e  # pragma: no cover
