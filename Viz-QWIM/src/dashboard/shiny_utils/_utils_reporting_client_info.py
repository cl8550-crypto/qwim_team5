from __future__ import annotations

from typing import Any


def build_client_info_json_from_reactives(*, reactives_shiny: Any) -> dict[str, Any]:
    """Build the ``client_info.json`` dictionary from ``reactives_shiny``.

    Reads all client data from ``User_Inputs_Shiny`` (where the client subtabs
    store every individual field as a ``reactive.Value``) and assembles the
    nested dictionary expected by the Typst report template ``report_QWIM.typ``.
    """
    from src.dashboard.shiny_utils import utils_reporting as public_module

    def _get_ui(*, key: str) -> Any:
        """Return the unwrapped value for *key* from User_Inputs_Shiny, or None."""
        if not isinstance(reactives_shiny, dict):
            return None
        user_inputs = reactives_shiny.get("User_Inputs_Shiny")
        if not isinstance(user_inputs, dict):
            return None
        reactive_var = user_inputs.get(key)
        if reactive_var is None:
            return None
        if hasattr(reactive_var, "get"):
            try:
                return reactive_var.get()
            except Exception:  # pragma: no cover
                return None
        return reactive_var

    def _str_ui(*, key: str, default: str = "") -> str:
        """Return string value for *key*, or *default* when absent."""
        value = _get_ui(key = key)
        return str(value) if value is not None else default

    def _flt_ui(*, key: str, default: float = 0.0) -> float:
        """Return float value for *key*, or *default* when absent."""
        value = _get_ui(key = key)
        if value is None or isinstance(value, bool):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    single_or_couple: str = "Single"
    try:
        single_or_couple = public_module.get_single_or_couple_from_reactives(reactives_shiny = reactives_shiny)
    except Exception as exc:
        public_module._logger.debug("Could not retrieve Single_Or_Couple from reactives: %s", exc)

    def _int_ui(*, key: str, default: int = 0) -> int:
        """Return integer value for *key*, or *default* when absent."""
        value = _get_ui(key = key)
        if value is None or isinstance(value, bool):
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def _build_personal_info(*, prefix: str, default_name: str) -> dict[str, Any]:
        """Build personal-info dict for one investor."""
        base = f"Input_Tab_clients_Subtab_clients_Personal_Info_{prefix}"
        name = _str_ui(key = f"{base}_Name") or default_name
        return {
            "name": name,
            "age_current": _int_ui(key = f"{base}_Age_Current"),
            "age_retirement": _int_ui(key = f"{base}_Age_Retirement"),
            "age_income_starting": _int_ui(key = f"{base}_Age_Income_Starting"),
            "status_marital": _str_ui(key = f"{base}_Status_Marital"),
            "gender": _str_ui(key = f"{base}_Gender"),
            "tolerance_risk": _str_ui(key = f"{base}_Tolerance_Risk"),
            "state": _str_ui(key = f"{base}_State"),
            "code_zip": _str_ui(key = f"{base}_Code_Zip"),
        }

    def _build_assets(*, prefix: str) -> dict[str, float]:
        """Build assets dict for one investor prefix."""
        base = f"Input_Tab_clients_Subtab_clients_Assets_{prefix}_Assets"
        taxable = _flt_ui(key = f"{base}_Taxable")
        tax_deferred = _flt_ui(key = f"{base}_Tax_Deferred")
        tax_free = _flt_ui(key = f"{base}_Tax_Free")
        return {
            "taxable": taxable,
            "tax_deferred": tax_deferred,
            "tax_free": tax_free,
            "total": taxable + tax_deferred + tax_free,
        }

    def _build_assets_combined() -> dict[str, float]:
        """Combine primary and partner asset totals into a single dict."""
        primary_assets = _build_assets(prefix = "client_Primary")
        partner_assets = _build_assets(prefix = "client_Partner")
        return {
            "taxable": primary_assets["taxable"] + partner_assets["taxable"],
            "tax_deferred": primary_assets["tax_deferred"] + partner_assets["tax_deferred"],
            "tax_free": primary_assets["tax_free"] + partner_assets["tax_free"],
            "total": primary_assets["total"] + partner_assets["total"],
        }

    def _build_goals(*, prefix: str) -> dict[str, float]:
        """Build goals dict for one investor prefix."""
        base = f"Input_Tab_clients_Subtab_clients_Goals_{prefix}_Goal"
        essential = _flt_ui(key = f"{base}_Essential")
        important = _flt_ui(key = f"{base}_Important")
        aspirational = _flt_ui(key = f"{base}_Aspirational")
        return {
            "essential": essential,
            "important": important,
            "aspirational": aspirational,
            "total": essential + important + aspirational,
        }

    def _build_goals_combined() -> dict[str, float]:
        """Combine primary and partner goal totals into a single dict."""
        primary_goals = _build_goals(prefix = "client_Primary")
        partner_goals = _build_goals(prefix = "client_Partner")
        return {
            "essential": primary_goals["essential"] + partner_goals["essential"],
            "important": primary_goals["important"] + partner_goals["important"],
            "aspirational": primary_goals["aspirational"] + partner_goals["aspirational"],
            "total": primary_goals["total"] + partner_goals["total"],
        }

    def _build_income(*, prefix: str) -> dict[str, float]:
        """Build income dict for one investor prefix."""
        base = f"Input_Tab_clients_Subtab_clients_Income_{prefix}_Income"
        social_security = _flt_ui(key = f"{base}_Social_Security")
        pension = _flt_ui(key = f"{base}_Pension")
        annuity_existing = _flt_ui(key = f"{base}_Annuity_Existing")
        other = _flt_ui(key = f"{base}_Other")
        return {
            "social_security": social_security,
            "pension": pension,
            "annuity_existing": annuity_existing,
            "other": other,
            "total": social_security + pension + annuity_existing + other,
        }

    def _build_income_combined() -> dict[str, float]:
        """Combine primary and partner income totals into a single dict."""
        primary_income = _build_income(prefix = "client_Primary")
        partner_income = _build_income(prefix = "client_Partner")
        return {
            "social_security": primary_income["social_security"] + partner_income["social_security"],
            "pension": primary_income["pension"] + partner_income["pension"],
            "annuity_existing": primary_income["annuity_existing"] + partner_income["annuity_existing"],
            "other": primary_income["other"] + partner_income["other"],
            "total": primary_income["total"] + partner_income["total"],
        }

    public_module._logger.info(
        "Building client_info JSON from User_Inputs_Shiny reactives",
        extra={"single_or_couple": single_or_couple},
    )

    return {
        "single_or_couple": single_or_couple,
        "personal_info": {
            "primary": _build_personal_info(prefix = "client_Primary", default_name = "Primary Investor"),
            "partner": _build_personal_info(prefix = "client_Partner", default_name = "Partner Investor"),
        },
        "assets": {
            "primary": _build_assets(prefix = "client_Primary"),
            "partner": _build_assets(prefix = "client_Partner"),
            "combined": _build_assets_combined(),
        },
        "goals": {
            "primary": _build_goals(prefix = "client_Primary"),
            "partner": _build_goals(prefix = "client_Partner"),
            "combined": _build_goals_combined(),
        },
        "income": {
            "primary": _build_income(prefix = "client_Primary"),
            "partner": _build_income(prefix = "client_Partner"),
            "combined": _build_income_combined(),
        },
    }