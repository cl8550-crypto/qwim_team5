"""QWIM client domain model and related enumerations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Self

import attrs
import polars as pl

from aenum import Enum

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


# ---------------------------------------------------------------------------
# attrs factory helpers for default Polars DataFrames
# ---------------------------------------------------------------------------

def _factory_personal_info_empty() -> pl.DataFrame:
    """Return an empty Polars DataFrame with the personal-info schema."""
    return pl.DataFrame(
        schema={
            "First Name": pl.Utf8,
            "Last Name": pl.Utf8,
            "Marital Status": pl.Utf8,
            "Gender": pl.Utf8,
            "Risk Tolerance": pl.Int64,
            "Current Age": pl.Int64,
            "Retirement Age": pl.Int64,
            "Income Start Age for Strategy Annuity": pl.Int64,
        },
    )


def _factory_assets_empty() -> pl.DataFrame:
    """Return an empty Polars DataFrame with the assets schema."""
    return pl.DataFrame(
        schema={
            "Investable Assets": pl.Float64,
            "Taxable Assets": pl.Float64,
            "Tax Deferred Assets": pl.Float64,
            "Tax Free Assets": pl.Float64,
            "Asset Name": pl.Utf8,
            "Asset Class": pl.Utf8,
        },
    )


def _factory_goals_empty() -> pl.DataFrame:
    """Return an empty Polars DataFrame with the goals schema."""
    return pl.DataFrame(
        schema={
            "Essential Annual Expense": pl.Float64,
            "Important Annual Expense": pl.Float64,
            "Aspirational Annual Expense": pl.Float64,
            "Essential Annual Expense is Inflation Indexed": pl.Boolean,
            "Important Annual Expense is Inflation Indexed": pl.Boolean,
            "Aspirational Annual Expense is Inflation Indexed": pl.Boolean,
        },
    )


def _factory_income_empty() -> pl.DataFrame:
    """Return an empty Polars DataFrame with the income schema."""
    return pl.DataFrame(
        schema={
            "Annual Social Security": pl.Float64,
            "Annual Pension in Retirement": pl.Float64,
            "Annual Annuity Income": pl.Float64,
            "Annual Other Income": pl.Float64,
            "Annual Income from Pension is Inflation Indexed": pl.Boolean,
            "Annual Income from Existing Annuity is Inflation Indexed": pl.Boolean,
            "Annual Income from Other Sources is Inflation Indexed": pl.Boolean,
            "Income Start Age for Pension": pl.Int64,
            "Income Start Age for Existing Annuity": pl.Int64,
            "Income Start Age for Other Sources": pl.Int64,
            "Income Duration for Pension": pl.Int64,
            "Income Duration for Existing Annuity": pl.Int64,
            "Income Duration for Other Sources": pl.Int64,
        },
    )


def _normalize_aggregate_scalar_to_float(
    *, value_aggregate: Any) -> float:
    """Return a safe aggregate float while keeping booleans on the 0.0 path."""
    if value_aggregate is None or isinstance(value_aggregate, bool):
        return 0.0

    try:
        return float(value_aggregate)
    except (TypeError, ValueError):
        return 0.0


def _normalize_aggregate_column_total_to_float(
    *, data_frame: pl.DataFrame, column_name: str, value_aggregate: Any = None) -> float:
    """Return a safe aggregate total while rejecting boolean-typed columns."""
    if data_frame.schema.get(column_name) == pl.Boolean:
        return 0.0

    if value_aggregate is None:
        value_aggregate = data_frame.select(pl.sum(column_name)).item()

    return _normalize_aggregate_scalar_to_float(value_aggregate = value_aggregate)


class Marital_Status(Enum):  # type: ignore[misc]
    """Marital status options for a QWIM client."""

    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"
    DOMESTIC_PARTNERSHIP = "Domestic Partnership"


class Employment_Status(Enum):  # type: ignore[misc]
    """Employment status options for a QWIM client."""

    EMPLOYED = "Employed"
    UNEMPLOYED = "Unemployed"
    SELF_EMPLOYED = "Self-employed"
    RETIRED = "Retired"
    STUDENT = "Student"


class Asset_Type(Enum):  # type: ignore[misc]
    """Asset type options for a QWIM client."""

    CASH = "Cash"
    STOCKS = "Stocks"
    BONDS = "Bonds"
    REAL_ESTATE = "Real Estate"
    RETIREMENT_ACCOUNT = "Retirement Account"
    OTHER = "Other"


class Goal_Type(Enum):  # type: ignore[misc]
    """Financial goal types for a QWIM client."""

    RETIREMENT = "Retirement"
    EDUCATION = "Education"
    HOME_PURCHASE = "Home Purchase"
    TRAVEL = "Travel"
    EMERGENCY_FUND = "Emergency Fund"
    OTHER = "Other"


class Income_Type(Enum):  # type: ignore[misc]
    """Income source types for a QWIM client."""

    SALARY = "Salary"
    BUSINESS = "Business Income"
    INVESTMENT = "Investment Income"
    PENSION = "Pension"
    SOCIAL_SECURITY = "Social Security"
    OTHER = "Other"


class Client_Type(Enum):  # type: ignore[misc]
    """QWIM client role — primary client or partner."""

    CLIENT_PRIMARY = "Client Primary"
    CLIENT_PARTNER = "Client Partner"


@attrs.define(kw_only=True)
class Client_QWIM:
    """QWIM client record containing personal, asset, goal, and income data.

    Attributes
    ----------
    client_ID : str
        Unique client identifier.
    first_name : str
        Client's first name.
    last_name : str
        Client's last name.
    client_type : Client_Type
        Client role — primary or partner.
    """

    # --- Required constructor fields ---
    client_ID: str = attrs.field()
    first_name: str = attrs.field()
    last_name: str = attrs.field()
    client_type: Client_Type = attrs.field()

    # --- Internal state with factory defaults ---
    m_creation_date: datetime = attrs.field(factory=lambda: datetime.now(UTC))
    m_last_updated: datetime = attrs.field(factory=lambda: datetime.now(UTC))
    m_logger: Any = attrs.field(factory=lambda: get_logger(name=__name__))
    m_personal_info: pl.DataFrame = attrs.field(factory=_factory_personal_info_empty)
    m_assets: pl.DataFrame = attrs.field(factory=_factory_assets_empty)
    m_goals: pl.DataFrame = attrs.field(factory=_factory_goals_empty)
    m_income: pl.DataFrame = attrs.field(factory=_factory_income_empty)

    def update_personal_info(
        self, *, data_personal_info: dict[str, Any]) -> bool:
        """Update client personal information from dashboard inputs."""
        try:
            valid_fields = [
                "First Name",
                "Last Name",
                "Marital Status",
                "Gender",
                "Risk Tolerance",
                "Current Age",
                "Retirement Age",
                "Income Start Age",
            ]

            filtered_data = {
                item_k: item_v
                for item_k, item_v in data_personal_info.items()
                if item_k in valid_fields
            }

            numeric_fields = ["Risk Tolerance", "Current Age", "Retirement Age", "Income Start Age"]
            for item_field in numeric_fields:
                if item_field in filtered_data:
                    if isinstance(filtered_data[item_field], bool):
                        self.m_logger.warning(
                            "Could not convert {} to integer: {}",
                            item_field,
                            filtered_data[item_field],
                        )
                        filtered_data[item_field] = None
                        continue
                    try:
                        filtered_data[item_field] = int(filtered_data[item_field])
                    except (ValueError, TypeError):
                        self.m_logger.warning(
                            "Could not convert {} to integer: {}",
                            item_field,
                            filtered_data[item_field],
                        )
                        filtered_data[item_field] = None

            self.m_personal_info = pl.DataFrame([filtered_data])

            if "First Name" in data_personal_info:
                self.first_name = data_personal_info["First Name"]
            if "Last Name" in data_personal_info:
                self.last_name = data_personal_info["Last Name"]

            self.m_last_updated = datetime.now(UTC)
            self.m_logger.info("Updated personal information for client {}", self.client_ID)
            return True

        except Exception:  # defensive handler for arbitrary Polars errors
            self.m_logger.exception(
                "Error updating personal information for client {}",
                self.client_ID,
            )
            return False

    def update_assets(
        self, *, data_assets: list[dict[str, Any]]) -> bool:
        """Update client assets from dashboard inputs."""
        try:
            if data_assets:
                clean_data = []

                for item_asset in data_assets:
                    clean_asset: dict[str, Any] = {
                        "Taxable Assets": 0.0,
                        "Tax Deferred Assets": 0.0,
                        "Tax Free Assets": 0.0,
                        "Asset Name": "",
                        "Asset Class": "",
                    }

                    for item_field in ("Taxable Assets", "Tax Deferred Assets", "Tax Free Assets"):
                        if item_field in item_asset:
                            if isinstance(item_asset[item_field], bool):
                                continue
                            try:
                                clean_asset[item_field] = float(item_asset[item_field])
                            except (ValueError, TypeError):
                                pass

                    if "Asset Name" in item_asset:
                        clean_asset["Asset Name"] = str(item_asset["Asset Name"])

                    if "Asset Class" in item_asset:
                        clean_asset["Asset Class"] = str(item_asset["Asset Class"])
                    elif "Type" in item_asset:  # backward compatibility
                        clean_asset["Asset Class"] = str(item_asset["Type"])

                    clean_data.append(clean_asset)

                self.m_assets = pl.DataFrame(clean_data)
            else:
                self.m_assets = pl.DataFrame(
                    schema={
                        "Taxable Assets": pl.Float64,
                        "Tax Deferred Assets": pl.Float64,
                        "Tax Free Assets": pl.Float64,
                        "Asset Name": pl.Utf8,
                        "Asset Class": pl.Utf8,
                    },
                )

            self.m_last_updated = datetime.now(UTC)
            self.m_logger.info("Updated assets for client {}", self.client_ID)
            return True

        except Exception:  # defensive handler for arbitrary Polars errors
            self.m_logger.exception("Error updating assets for client {}", self.client_ID)
            return False

    def update_goals(
        self, *, data_goals: list[dict[str, Any]] | dict[str, Any]) -> bool:
        """Update client financial goals from dashboard inputs."""
        try:
            if isinstance(data_goals, dict):
                data_goals = [data_goals]

            if data_goals:
                clean_data = []

                for item_goal in data_goals:
                    clean_goal: dict[str, Any] = {
                        "Essential Annual Expense": 0.0,
                        "Important Annual Expense": 0.0,
                        "Aspirational Annual Expense": 0.0,
                        "Essential Annual Expense is Inflation Indexed": False,
                        "Important Annual Expense is Inflation Indexed": False,
                        "Aspirational Annual Expense is Inflation Indexed": False,
                    }

                    for expense_type in (
                        "Essential Annual Expense",
                        "Important Annual Expense",
                        "Aspirational Annual Expense",
                    ):
                        if expense_type in item_goal:
                            if isinstance(item_goal[expense_type], bool):
                                continue
                            try:
                                clean_goal[expense_type] = float(item_goal[expense_type])
                            except (ValueError, TypeError):
                                pass

                    for idx_field in (
                        "Essential Annual Expense is Inflation Indexed",
                        "Important Annual Expense is Inflation Indexed",
                        "Aspirational Annual Expense is Inflation Indexed",
                    ):
                        if idx_field in item_goal:
                            item_val = item_goal[idx_field]
                            if isinstance(item_val, bool):
                                clean_goal[idx_field] = item_val
                            elif isinstance(item_val, str):
                                clean_goal[idx_field] = item_val.lower() in (
                                    "true",
                                    "yes",
                                    "y",
                                    "1",
                                )
                            elif isinstance(item_val, (int, float)):
                                clean_goal[idx_field] = bool(item_val)

                    clean_data.append(clean_goal)

                self.m_goals = pl.DataFrame(clean_data)
            else:
                self.m_goals = pl.DataFrame(
                    schema={
                        "Essential Annual Expense": pl.Float64,
                        "Important Annual Expense": pl.Float64,
                        "Aspirational Annual Expense": pl.Float64,
                        "Essential Annual Expense is Inflation Indexed": pl.Boolean,
                        "Important Annual Expense is Inflation Indexed": pl.Boolean,
                        "Aspirational Annual Expense is Inflation Indexed": pl.Boolean,
                    },
                )

            self.m_last_updated = datetime.now(UTC)
            self.m_logger.info("Updated goals for client {}", self.client_ID)
            return True

        except Exception:  # defensive handler for arbitrary Polars errors
            self.m_logger.exception("Error updating goals for client {}", self.client_ID)
            return False

    def update_income(
        self, *, data_income: list[dict[str, Any]] | dict[str, Any]) -> bool:
        """Update client income sources from dashboard inputs."""
        # Mapping from dashboard input keys to schema column names
        _AMOUNT_MAP = {
            "Annual Social Security": "Annual Social Security",
            "Annual Pension in Retirement": "Annual Pension in Retirement",
            "Annual Annuity Income": "Annual Annuity Income",
            "Annual Other Income": "Annual Other Income",
        }
        # Flag keys (input) mapped to schema column names
        _FLAG_MAP = {
            "Annual Pension in Retirement is Inflation Indexed": "Annual Income from Pension is Inflation Indexed",
            "Annual Annuity Income is Inflation Indexed": "Annual Income from Existing Annuity is Inflation Indexed",
            "Annual Other Income is Inflation Indexed": "Annual Income from Other Sources is Inflation Indexed",
            # Direct schema keys are also accepted
            "Annual Income from Pension is Inflation Indexed": "Annual Income from Pension is Inflation Indexed",
            "Annual Income from Existing Annuity is Inflation Indexed": "Annual Income from Existing Annuity is Inflation Indexed",
            "Annual Income from Other Sources is Inflation Indexed": "Annual Income from Other Sources is Inflation Indexed",
        }

        try:
            if isinstance(data_income, dict):
                data_income = [data_income]

            if data_income:
                clean_data = []

                for income_entry in data_income:
                    clean_income: dict[str, Any] = {
                        "Annual Social Security": 0.0,
                        "Annual Pension in Retirement": 0.0,
                        "Annual Annuity Income": 0.0,
                        "Annual Other Income": 0.0,
                        "Annual Income from Pension is Inflation Indexed": False,
                        "Annual Income from Existing Annuity is Inflation Indexed": False,
                        "Annual Income from Other Sources is Inflation Indexed": False,
                        "Income Start Age for Pension": 65,
                        "Income Start Age for Existing Annuity": 65,
                        "Income Start Age for Other Sources": 65,
                        "Income Duration for Pension": 25,
                        "Income Duration for Existing Annuity": 25,
                        "Income Duration for Other Sources": 25,
                    }

                    for input_key, schema_key in _AMOUNT_MAP.items():
                        if input_key in income_entry:
                            if isinstance(income_entry[input_key], bool):
                                continue
                            try:
                                clean_income[schema_key] = float(income_entry[input_key])
                            except (ValueError, TypeError):
                                pass

                    for input_key, schema_key in _FLAG_MAP.items():
                        if input_key in income_entry:
                            item_val = income_entry[input_key]
                            if isinstance(item_val, bool):
                                clean_income[schema_key] = item_val
                            elif isinstance(item_val, str):
                                clean_income[schema_key] = item_val.lower() in (
                                    "true",
                                    "yes",
                                    "y",
                                    "1",
                                )
                            elif isinstance(item_val, (int, float)):
                                clean_income[schema_key] = bool(item_val)

                    clean_data.append(clean_income)

                self.m_income = pl.DataFrame(clean_data)
            else:
                self.m_income = pl.DataFrame(
                    schema={
                        "Annual Social Security": pl.Float64,
                        "Annual Pension in Retirement": pl.Float64,
                        "Annual Annuity Income": pl.Float64,
                        "Annual Other Income": pl.Float64,
                        "Annual Income from Pension is Inflation Indexed": pl.Boolean,
                        "Annual Income from Existing Annuity is Inflation Indexed": pl.Boolean,
                        "Annual Income from Other Sources is Inflation Indexed": pl.Boolean,
                        "Income Start Age for Pension": pl.Int64,
                        "Income Start Age for Existing Annuity": pl.Int64,
                        "Income Start Age for Other Sources": pl.Int64,
                        "Income Duration for Pension": pl.Int64,
                        "Income Duration for Existing Annuity": pl.Int64,
                        "Income Duration for Other Sources": pl.Int64,
                    },
                )

            self.m_last_updated = datetime.now(UTC)
            self.m_logger.info("Updated income for client {}", self.client_ID)
            return True

        except Exception:  # defensive handler for arbitrary Polars errors
            self.m_logger.exception("Error updating income for client {}", self.client_ID)
            return False

    def get_personal_info(self) -> pl.DataFrame:
        """Return the client's personal information DataFrame."""
        return self.m_personal_info

    def get_marital_status(self) -> str | None:
        """Return the client's marital status, or ``None`` if not set."""
        if self.m_personal_info.is_empty():
            return None
        try:
            return self.m_personal_info.select("Marital Status").item()  # type: ignore[return-value]
        except Exception:  # pragma: no cover  # Polars error if column absent
            return None

    def get_risk_tolerance(self) -> int | None:
        """Return the client's risk tolerance, or ``None`` if not set."""
        if self.m_personal_info.is_empty():
            return None
        try:
            return self.m_personal_info.select("Risk Tolerance").item()  # type: ignore[return-value]
        except Exception:  # pragma: no cover
            return None

    def get_current_age(self) -> int | None:
        """Return the client's current age, or ``None`` if not set."""
        if self.m_personal_info.is_empty():
            return None
        try:
            return self.m_personal_info.select("Current Age").item()  # type: ignore[return-value]
        except Exception:  # pragma: no cover
            return None

    def get_retirement_age(self) -> int | None:
        """Return the client's retirement age, or ``None`` if not set."""
        if self.m_personal_info.is_empty():
            return None
        try:
            return self.m_personal_info.select("Retirement Age").item()  # type: ignore[return-value]
        except Exception:  # pragma: no cover
            return None

    def get_income_start_age(self) -> int | None:
        """Return the client's income start age, or ``None`` if not set."""
        if self.m_personal_info.is_empty():
            return None
        try:
            return self.m_personal_info.select("Income Start Age").item()  # type: ignore[return-value]
        except Exception:  # pragma: no cover
            return None

    def get_assets(self) -> pl.DataFrame:
        """Return the client's assets DataFrame."""
        return self.m_assets

    def get_goals(self) -> pl.DataFrame:
        """Return the client's financial goals DataFrame."""
        return self.m_goals

    def get_income(self) -> pl.DataFrame:
        """Return the client's income sources DataFrame."""
        return self.m_income

    def get_total_assets(self) -> float:
        """Calculate and return the total value of client's investable assets."""
        if self.m_assets.is_empty():
            return 0.0

        try:
            asset_columns = ["Taxable Assets", "Tax Deferred Assets", "Tax Free Assets"]
            asset_sums = self.m_assets.select(
                [
                    pl.sum(idx_col).alias(f"total_{idx_col.lower().replace(' ', '_')}")
                    for idx_col in asset_columns
                ],
            )
            totals = [
                _normalize_aggregate_column_total_to_float(
                    data_frame = self.m_assets,
                    column_name = idx_col,
                    value_aggregate = asset_sums[0, f"total_{idx_col.lower().replace(' ', '_')}"],
                )
                for idx_col in asset_columns
            ]
            total_assets = sum(totals)
            return float(total_assets)

        except Exception:  # pragma: no cover  # defensive — Polars error on bad schema
            self.m_logger.exception(
                "Error calculating total assets for client {}",
                self.client_ID,
            )
            return 0.0

    def get_taxable_assets(self) -> float:
        """Return the total taxable assets."""
        if self.m_assets.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_assets,
                column_name = "Taxable Assets",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception("Error getting taxable assets for client {}", self.client_ID)
            return 0.0

    def get_tax_deferred_assets(self) -> float:
        """Return the total tax-deferred assets."""
        if self.m_assets.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_assets,
                column_name = "Tax Deferred Assets",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error getting tax-deferred assets for client {}",
                self.client_ID,
            )
            return 0.0

    def get_tax_free_assets(self) -> float:
        """Return the total tax-free assets."""
        if self.m_assets.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_assets,
                column_name = "Tax Free Assets",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception("Error getting tax-free assets for client {}", self.client_ID)
            return 0.0

    def get_total_annual_income(self) -> float:
        """Calculate and return total annual income across all income sources."""
        if self.m_income.is_empty():
            return 0.0

        try:
            income_columns = [
                "Annual Social Security",
                "Annual Pension in Retirement",
                "Annual Annuity Income",
                "Annual Other Income",
            ]
            income_sum = self.m_income.select(
                [
                    pl.sum(idx_col).alias(f"total_{idx_col.lower().replace(' ', '_')}")
                    for idx_col in income_columns
                ],
            )
            totals = [
                _normalize_aggregate_column_total_to_float(
                    data_frame = self.m_income,
                    column_name = idx_col,
                    value_aggregate = income_sum[0, f"total_{idx_col.lower().replace(' ', '_')}"],
                )
                for idx_col in income_columns
            ]
            total_income = sum(totals)
            return float(total_income)

        except Exception:  # pragma: no cover  # reason: defensive handler; arbitrary Polars errors cannot be reliably triggered in unit tests
            self.m_logger.exception(
                "Error calculating total annual income for client {}",
                self.client_ID,
            )
            return 0.0

    def get_social_security_income(self) -> float:
        """Return the total social security income."""
        if self.m_income.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_income,
                column_name = "Annual Social Security",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error getting social security income for client {}",
                self.client_ID,
            )
            return 0.0

    def get_pension_income(self) -> float:
        """Return the total pension income."""
        if self.m_income.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_income,
                column_name = "Annual Pension in Retirement",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception("Error getting pension income for client {}", self.client_ID)
            return 0.0

    def get_annuity_income(self) -> float:
        """Return the total annuity income."""
        if self.m_income.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_income,
                column_name = "Annual Annuity Income",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception("Error getting annuity income for client {}", self.client_ID)
            return 0.0

    def get_other_income(self) -> float:
        """Return the total other income."""
        if self.m_income.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_income,
                column_name = "Annual Other Income",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception("Error getting other income for client {}", self.client_ID)
            return 0.0

    def is_pension_income_inflation_indexed(self) -> bool:
        """Return whether pension income is inflation-indexed."""
        if self.m_income.is_empty():
            return False
        try:
            return bool(
                self.m_income.select(
                    pl.any("Annual Income from Pension is Inflation Indexed"),
                ).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking pension inflation index for client {}",
                self.client_ID,
            )
            return False

    def is_income_from_existing_annuity_inflation_indexed(self) -> bool:
        """Return whether income from existing annuity is inflation-indexed."""
        if self.m_income.is_empty():
            return False
        try:
            return bool(
                self.m_income.select(
                    pl.any("Annual Income from Existing Annuity is Inflation Indexed"),
                ).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking annuity inflation index for client {}",
                self.client_ID,
            )
            return False

    def is_income_from_other_sources_inflation_indexed(self) -> bool:
        """Return whether other income is inflation-indexed."""
        if self.m_income.is_empty():
            return False
        try:
            return bool(
                self.m_income.select(
                    pl.any("Annual Income from Other Sources is Inflation Indexed"),
                ).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking other income inflation index for client {}",
                self.client_ID,
            )
            return False

    def get_total_annual_expenses(self) -> float:
        """Calculate and return total annual expenses across all categories."""
        if self.m_goals.is_empty():
            return 0.0

        try:
            expense_columns = [
                "Essential Annual Expense",
                "Important Annual Expense",
                "Aspirational Annual Expense",
            ]
            expenses_sum = self.m_goals.select(
                [
                    pl.sum(idx_col).alias(f"total_{idx_col.lower().replace(' ', '_')}")
                    for idx_col in expense_columns
                ],
            )
            totals = [
                _normalize_aggregate_column_total_to_float(
                    data_frame = self.m_goals,
                    column_name = idx_col,
                    value_aggregate = expenses_sum[0, f"total_{idx_col.lower().replace(' ', '_')}"],
                )
                for idx_col in expense_columns
            ]
            total_expenses = sum(totals)
            return float(total_expenses)

        except Exception:  # pragma: no cover  # defensive — Polars error on bad schema
            self.m_logger.exception(
                "Error calculating total annual expenses for client {}",
                self.client_ID,
            )
            return 0.0

    def get_annual_essential_expenses(self) -> float:
        """Return total essential annual expenses."""
        if self.m_goals.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_goals,
                column_name = "Essential Annual Expense",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error getting essential expenses for client {}",
                self.client_ID,
            )
            return 0.0

    def get_annual_important_expenses(self) -> float:
        """Return total important annual expenses."""
        if self.m_goals.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_goals,
                column_name = "Important Annual Expense",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error getting important expenses for client {}",
                self.client_ID,
            )
            return 0.0

    def get_annual_aspirational_expenses(self) -> float:
        """Return total aspirational annual expenses."""
        if self.m_goals.is_empty():
            return 0.0
        try:
            return _normalize_aggregate_column_total_to_float(
                data_frame = self.m_goals,
                column_name = "Aspirational Annual Expense",
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error getting aspirational expenses for client {}",
                self.client_ID,
            )
            return 0.0

    def is_annual_essential_expense_inflation_indexed(self) -> bool:
        """Return whether essential expenses are inflation-indexed."""
        if self.m_goals.is_empty():
            return False
        try:
            return bool(
                self.m_goals.select(pl.any("Essential Annual Expense is Inflation Indexed")).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking essential expense inflation index for client {}",
                self.client_ID,
            )
            return False

    def is_annual_important_expense_inflation_indexed(self) -> bool:
        """Return whether important expenses are inflation-indexed."""
        if self.m_goals.is_empty():
            return False
        try:
            return bool(
                self.m_goals.select(pl.any("Important Annual Expense is Inflation Indexed")).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking important expense inflation index for client {}",
                self.client_ID,
            )
            return False

    def is_annual_aspirational_expense_inflation_indexed(self) -> bool:
        """Return whether aspirational expenses are inflation-indexed."""
        if self.m_goals.is_empty():
            return False
        try:
            return bool(
                self.m_goals.select(
                    pl.any("Aspirational Annual Expense is Inflation Indexed"),
                ).item(),
            )
        except Exception:  # pragma: no cover
            self.m_logger.exception(
                "Error checking aspirational expense inflation index for client {}",
                self.client_ID,
            )
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the client to a dictionary."""
        return {
            "client_ID": self.client_ID,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "client_type": self.client_type.value,
            "creation_date": self.m_creation_date.isoformat(),
            "last_updated": self.m_last_updated.isoformat(),
            "personal_info": self.m_personal_info.to_dicts(),
            "assets": self.m_assets.to_dicts(),
            "goals": self.m_goals.to_dicts(),
            "income": self.m_income.to_dicts(),
        }

    @classmethod
    def from_dict(cls, *, input_data: dict[str, Any]) -> Self:
        """Create a ``Client_QWIM`` instance from a serialized dictionary."""
        client = cls(
            client_ID=input_data.get("client_ID", ""),
            first_name=input_data.get("first_name", ""),
            last_name=input_data.get("last_name", ""),
            client_type=(
                Client_Type(input_data["client_type"])
                if "client_type" in input_data
                else Client_Type.CLIENT_PRIMARY
            ),
        )

        if "creation_date" in input_data:
            client.m_creation_date = datetime.fromisoformat(input_data["creation_date"])
        if "last_updated" in input_data:
            client.m_last_updated = datetime.fromisoformat(input_data["last_updated"])

        if input_data.get("personal_info"):
            client.m_personal_info = pl.DataFrame(input_data["personal_info"])
        if input_data.get("assets"):
            client.m_assets = pl.DataFrame(input_data["assets"])
        if input_data.get("goals"):
            client.m_goals = pl.DataFrame(input_data["goals"])
        if input_data.get("income"):
            client.m_income = pl.DataFrame(input_data["income"])

        return client

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.first_name and self.last_name:
            name = f"{self.first_name} {self.last_name}"
        else:
            name = self.client_ID
        return f"QWIM Client: {name} (Total Assets: ${self.get_total_assets():,.2f})"
