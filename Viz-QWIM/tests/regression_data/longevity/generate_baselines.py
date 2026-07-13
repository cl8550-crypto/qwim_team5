"""Generate Parquet baseline files for longevity model regression tests.

Run this script whenever an **intentional** change is made to the
longevity model modules.  Commit the updated Parquet files together
with the corresponding code change so that regression tests continue to
pass.

Usage
-----
    python tests/regression_data/longevity/generate_baselines.py

Baselines written
-----------------
Constant model
~~~~~~~~~~~~~~
* ``constant_historical_qx.parquet``
* ``constant_predict_default.parquet``
* ``constant_predict_fitted.parquet``
* ``constant_summary_default.parquet``
* ``constant_summary_fitted.parquet``
* ``constant_parameters_default.parquet``
* ``constant_parameters_fitted.parquet``
* ``constant_life_expectancy_default.parquet``
* ``constant_survival_default.parquet``

Standard (Gompertz) model
~~~~~~~~~~~~~~~~~~~~~~~~~
* ``gompertz_historical_qx.parquet``
* ``gompertz_parameters_fitted.parquet``
* ``gompertz_predict_20ages.parquet``
* ``gompertz_predict_50ages.parquet``
* ``gompertz_summary_20ages.parquet``
* ``gompertz_life_expectancy.parquet``
* ``gompertz_survival_probability.parquet``
* ``gompertz_force_of_mortality.parquet``

Author
------
QWIM Team
"""

from __future__ import annotations

import sys

from pathlib import Path

import numpy as np
import polars as pl


# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.longevity.model_longevity_constant import (  # noqa: E402
    Longevity_Model_Constant,
)
from src.models.longevity.model_longevity_standard import (  # noqa: E402
    Longevity_Model_Standard,
)


# ---------------------------------------------------------------------------
# Fixed seeds and canonical constants — MUST match conftest.py
# ---------------------------------------------------------------------------

# Constant-model defaults
CONSTANT_DEFAULT_QX: float = 0.02  # 2 % annual death probability
CONSTANT_N_AGES: int = 20
CONSTANT_START_AGE: int = 65

# Gompertz constructor priors (approximate US adult mortality)
GOMPERTZ_B: float = 5e-5
GOMPERTZ_b: float = 0.09

# Prediction parameters
GOMPERTZ_N_AGES_SHORT: int = 20
GOMPERTZ_N_AGES_LONG: int = 50
GOMPERTZ_START_AGE: int = 40

# Life-expectancy / survival ages
LIFE_EXPECTANCY_AGES: list[int] = [0, 30, 50, 65, 80]
SURVIVAL_AGES: list[int] = [40, 50, 65, 75]
SURVIVAL_HORIZONS: list[float] = [1.0, 5.0, 10.0, 20.0, 30.0]

# Force of mortality ages
FORCE_OF_MORTALITY_AGES: list[int] = [0, 20, 40, 60, 65, 70, 80, 90, 100]

BASELINES_DIR: Path = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Canonical historical data builders
# ---------------------------------------------------------------------------


def _build_constant_historical_qx() -> pl.DataFrame:
    """Build a small deterministic historical qx dataset for the constant model.

    Returns
    -------
    pl.DataFrame
        5-row DataFrame with ``Age`` and ``qx`` columns.
    """
    return pl.DataFrame(
        {
            "Age": [60, 65, 70, 75, 80],
            "qx": [0.010, 0.014, 0.021, 0.032, 0.045],
        },
    )


def _build_gompertz_historical_qx() -> pl.DataFrame:
    """Build a realistic life-table excerpt for Gompertz fitting.

    Uses the known Gompertz formula with B=5e-5, b=0.09 to generate
    exact qx values for ages 30-89 (60 data points), ensuring OLS
    recovery of the true parameters.

    Returns
    -------
    pl.DataFrame
        60-row DataFrame with ``Age`` and ``qx`` columns.
    """
    ages = np.arange(30, 90, dtype=np.float64)
    B_true = 5e-5
    b_true = 0.09

    # qx = 1 - exp(-(B/b) * exp(b*x) * (exp(b) - 1))
    integral_mu = (B_true / b_true) * np.exp(b_true * ages) * (np.exp(b_true) - 1.0)
    qx_values = 1.0 - np.exp(-integral_mu)

    return pl.DataFrame(
        {
            "Age": ages.astype(int).tolist(),
            "qx": qx_values.tolist(),
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_parquet(df: pl.DataFrame, name: str) -> None:
    """Write *df* to ``BASELINES_DIR / {name}.parquet``."""
    path = BASELINES_DIR / f"{name}.parquet"
    df.write_parquet(path)
    print(f"  [OK] {path.name}  ({len(df)} rows, {df.shape[1]} cols)")


def _dict_to_dataframe(params: dict[str, float]) -> pl.DataFrame:
    """Convert a flat parameter dict to a single-row DataFrame."""
    return pl.DataFrame({key: [val] for key, val in params.items()})


# ---------------------------------------------------------------------------
# Constant-model baselines
# ---------------------------------------------------------------------------


def _generate_constant_baselines() -> None:
    """Generate all Parquet baselines for the constant mortality model."""
    print("\n=== Constant mortality model baselines ===")

    # ---- Historical data ------------------------------------------------
    hist = _build_constant_historical_qx()
    _save_parquet(hist, "constant_historical_qx")

    # ---- Default model (constructor qx, empty fit) ----------------------
    model_default = Longevity_Model_Constant(qx=CONSTANT_DEFAULT_QX)
    model_default.fit(data = pl.DataFrame())

    pred_default = model_default.predict(n_ages=CONSTANT_N_AGES, start_age=CONSTANT_START_AGE)
    _save_parquet(pred_default, "constant_predict_default")

    summary_default = model_default.get_summary_statistics(df_predict = pred_default)
    _save_parquet(summary_default, "constant_summary_default")

    params_default = _dict_to_dataframe(model_default.parameters)
    _save_parquet(params_default, "constant_parameters_default")

    # ---- Life expectancy for default model ------------------------------
    le_rows = []
    for age in LIFE_EXPECTANCY_AGES:
        le_val = model_default.get_life_expectancy(current_age = age)
        le_rows.append({"Age": age, "Life_Expectancy": le_val})
    le_df = pl.DataFrame(le_rows)
    _save_parquet(le_df, "constant_life_expectancy_default")

    # ---- Survival probability for default model -------------------------
    surv_rows = []
    for age in SURVIVAL_AGES:
        for t_yr in SURVIVAL_HORIZONS:
            prob = model_default.survival_probability(current_age = age, t_years = t_yr)
            surv_rows.append(
                {"Age": age, "t_years": t_yr, "Survival_Probability": prob},
            )
    surv_df = pl.DataFrame(surv_rows)
    _save_parquet(surv_df, "constant_survival_default")

    # ---- Fitted model (from historical data) ----------------------------
    model_fitted = Longevity_Model_Constant()
    model_fitted.fit(data = hist)

    pred_fitted = model_fitted.predict(n_ages=CONSTANT_N_AGES, start_age=CONSTANT_START_AGE)
    _save_parquet(pred_fitted, "constant_predict_fitted")

    summary_fitted = model_fitted.get_summary_statistics(df_predict = pred_fitted)
    _save_parquet(summary_fitted, "constant_summary_fitted")

    params_fitted = _dict_to_dataframe(model_fitted.parameters)
    _save_parquet(params_fitted, "constant_parameters_fitted")


# ---------------------------------------------------------------------------
# Gompertz-model baselines
# ---------------------------------------------------------------------------


def _generate_gompertz_baselines() -> None:
    """Generate all Parquet baselines for the Gompertz mortality model."""
    print("\n=== Gompertz mortality model baselines ===")

    # ---- Historical data ------------------------------------------------
    hist = _build_gompertz_historical_qx()
    _save_parquet(hist, "gompertz_historical_qx")

    # ---- Fit the model --------------------------------------------------
    model = Longevity_Model_Standard(B=GOMPERTZ_B, b=GOMPERTZ_b)
    model.fit(data = hist)

    # ---- Parameters -----------------------------------------------------
    params = _dict_to_dataframe(model.parameters)
    _save_parquet(params, "gompertz_parameters_fitted")

    # ---- Predictions (short: 20 ages, long: 50 ages) --------------------
    pred_short = model.predict(n_ages=GOMPERTZ_N_AGES_SHORT, start_age=GOMPERTZ_START_AGE)
    _save_parquet(pred_short, "gompertz_predict_20ages")

    pred_long = model.predict(n_ages=GOMPERTZ_N_AGES_LONG, start_age=GOMPERTZ_START_AGE)
    _save_parquet(pred_long, "gompertz_predict_50ages")

    # ---- Summary stats (short prediction) -------------------------------
    summary = model.get_summary_statistics(df_predict = pred_short)
    _save_parquet(summary, "gompertz_summary_20ages")

    # ---- Life expectancy at various ages --------------------------------
    le_rows = []
    for age in LIFE_EXPECTANCY_AGES:
        le_val = model.get_life_expectancy(current_age = age)
        le_rows.append({"Age": age, "Life_Expectancy": le_val})
    le_df = pl.DataFrame(le_rows)
    _save_parquet(le_df, "gompertz_life_expectancy")

    # ---- Survival probability grid (age x horizon) ----------------------
    surv_rows = []
    for age in SURVIVAL_AGES:
        for t_yr in SURVIVAL_HORIZONS:
            prob = model.survival_probability(current_age = age, t_years = t_yr)
            surv_rows.append(
                {"Age": age, "t_years": t_yr, "Survival_Probability": prob},
            )
    surv_df = pl.DataFrame(surv_rows)
    _save_parquet(surv_df, "gompertz_survival_probability")

    # ---- Force of mortality at various ages -----------------------------
    mu_rows = []
    for age in FORCE_OF_MORTALITY_AGES:
        mu_val = model.get_force_of_mortality(age = age)
        mu_rows.append({"Age": age, "Force_Of_Mortality": mu_val})
    mu_df = pl.DataFrame(mu_rows)
    _save_parquet(mu_df, "gompertz_force_of_mortality")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate all longevity model regression baselines."""
    print("Generating longevity model regression baselines …")
    print(f"  Output directory: {BASELINES_DIR}")

    _generate_constant_baselines()
    _generate_gompertz_baselines()

    print("\n✓ All baseline Parquet files generated successfully.")


if __name__ == "__main__":
    main()
