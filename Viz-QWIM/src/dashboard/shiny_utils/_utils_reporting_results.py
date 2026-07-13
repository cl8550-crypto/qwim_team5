from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Configuration,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger


_logger = get_logger(name = __name__)


VALID_RESULTS_SUBTAB_KEYS: frozenset[str] = frozenset(
    [
        "Portfolio_Analysis_Inputs",
        "Portfolio_Analysis_Outputs",
        "Portfolio_Comparison_Inputs",
        "Portfolio_Comparison_Outputs",
        "Weights_Analysis_Inputs",
        "Weights_Analysis_Outputs",
        "Portfolio_Optimization_Skfolio_Inputs",
        "Portfolio_Optimization_Skfolio_Outputs",
        "Portfolio_Optimization_OptimalPortfolios_Inputs",
        "Portfolio_Optimization_OptimalPortfolios_Outputs",
        "Portfolio_Simulation_Inputs",
        "Portfolio_Simulation_Outputs",
    ],
)


def validate_data_results_in_reactives(*, reactives_shiny: Any) -> tuple[bool, str]:
    """Validate that the Data_Results category exists and has the required structure."""
    if reactives_shiny is None:
        return False, "reactives_shiny dictionary cannot be None"
    if not isinstance(reactives_shiny, dict):
        return (
            False,
            f"reactives_shiny must be a dictionary, got {type(reactives_shiny).__name__}",
        )
    if "Data_Results" not in reactives_shiny:
        available_categories = list(reactives_shiny.keys())
        return (
            False,
            f"'Data_Results' category not found in reactives_shiny. Available categories: {available_categories}",
        )

    data_results = reactives_shiny["Data_Results"]
    if not isinstance(data_results, dict):
        return (
            False,
            f"'Data_Results' must be a dictionary, got {type(data_results).__name__}",
        )

    for subtab_key_name in sorted(VALID_RESULTS_SUBTAB_KEYS):
        if subtab_key_name not in data_results:
            available_keys = list(data_results.keys())
            return (
                False,
                f"Subtab key '{subtab_key_name}' not found in Data_Results. Available keys: {available_keys}",
            )
    return True, ""


def validate_results_subtab_key(*, subtab_key: Any) -> tuple[bool, str]:
    """Validate that the provided subtab key is one of the allowed Data_Results keys."""
    if subtab_key is None:
        return False, "subtab_key cannot be None"
    if not isinstance(subtab_key, str):
        return False, f"subtab_key must be a string, got {type(subtab_key).__name__}"
    if len(subtab_key.strip()) == 0:
        return False, "subtab_key cannot be an empty string"
    if subtab_key not in VALID_RESULTS_SUBTAB_KEYS:
        return (
            False,
            f"Invalid subtab_key '{subtab_key}'. Valid keys: {sorted(VALID_RESULTS_SUBTAB_KEYS)}",
        )
    return True, ""


def get_results_data_from_reactives(
    *, reactives_shiny: Any, subtab_key: Any) -> Any | None:
    """Retrieve results data stored at a specific subtab key in Data_Results."""
    validation_result, validation_message = validate_data_results_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Results structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_results_subtab_key(subtab_key = subtab_key)
    if not validation_result:
        error_message = f"Subtab key validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if subtab_key not in reactives_shiny["Data_Results"]:  # pragma: no cover
        available_keys = list(reactives_shiny["Data_Results"].keys())
        error_message = (
            f"Subtab key '{subtab_key}' not found in Data_Results. Available keys: {available_keys}"
        )
        _logger.error(error_message)
        raise KeyError(error_message)

    reactive_variable = reactives_shiny["Data_Results"][subtab_key]
    if reactive_variable is None:
        error_message = (
            f"Reactive variable at Data_Results['{subtab_key}'] is None — it was not properly initialized"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)
    if not hasattr(reactive_variable, "get"):
        error_message = (
            f"Reactive variable at Data_Results['{subtab_key}'] does not have a 'get' method. Object type: {type(reactive_variable).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    try:
        retrieved_value = reactive_variable.get()
        _logger.debug(
            "Retrieved results data from reactives",
            extra={"subtab_key": subtab_key, "value_type": type(retrieved_value).__name__},
        )
        return retrieved_value
    except Exception as exc:
        error_message = f"Unexpected error retrieving Data_Results['{subtab_key}']: {exc}"
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def save_results_data_to_reactives(
    *, reactives_shiny: Any, subtab_key: Any, data_value: Any) -> dict:
    """Save results data to a specific subtab key in the Data_Results reactive structure."""
    validation_result, validation_message = validate_data_results_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        error_message = f"Data_Results structure validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    validation_result, validation_message = validate_results_subtab_key(subtab_key = subtab_key)
    if not validation_result:
        error_message = f"Subtab key validation failed: {validation_message}"
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    if subtab_key not in reactives_shiny["Data_Results"]:  # pragma: no cover
        available_keys = list(reactives_shiny["Data_Results"].keys())
        error_message = (
            f"Subtab key '{subtab_key}' not found in Data_Results. Available keys: {available_keys}"
        )
        _logger.error(error_message)
        raise KeyError(error_message)

    reactive_variable = reactives_shiny["Data_Results"][subtab_key]
    if reactive_variable is None:
        error_message = (
            f"Reactive variable at Data_Results['{subtab_key}'] is None — it was not properly initialized"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)
    if not hasattr(reactive_variable, "set"):
        error_message = (
            f"Reactive variable at Data_Results['{subtab_key}'] does not have a 'set' method. Object type: {type(reactive_variable).__name__}"
        )
        _logger.error(error_message)
        raise Exception_Validation_Input(error_message)

    try:
        reactive_variable.set(data_value)
        _logger.debug(
            "Saved results data to reactives",
            extra={"subtab_key": subtab_key, "value_type": type(data_value).__name__},
        )
        return reactives_shiny
    except Exception as exc:
        error_message = f"Unexpected error saving Data_Results['{subtab_key}']: {exc}"
        _logger.error(error_message)
        raise Exception_Configuration(error_message) from exc


def save_portfolio_analysis_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Analysis subtab input values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Analysis_Inputs", data_value = data_value)


def save_portfolio_analysis_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Analysis subtab output values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Analysis_Outputs", data_value = data_value)


def save_portfolio_comparison_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Comparison subtab input values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Comparison_Inputs", data_value = data_value)


def save_portfolio_comparison_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Comparison subtab output values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Comparison_Outputs", data_value = data_value)


def save_weights_analysis_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Weights Analysis subtab input values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Weights_Analysis_Inputs", data_value = data_value)


def save_weights_analysis_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Weights Analysis subtab output values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Weights_Analysis_Outputs", data_value = data_value)


def save_portfolio_optimization_skfolio_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save skfolio optimization subtab input values to Data_Results."""
    return save_results_data_to_reactives(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_Skfolio_Inputs",
        data_value = data_value,
    )


def save_portfolio_optimization_skfolio_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save skfolio optimization subtab output values to Data_Results."""
    return save_results_data_to_reactives(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_Skfolio_Outputs",
        data_value = data_value,
    )


def save_portfolio_optimization_optimalportfolios_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save OptimalPortfolios optimization subtab input values to Data_Results."""
    return save_results_data_to_reactives(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_OptimalPortfolios_Inputs",
        data_value = data_value,
    )


def save_portfolio_optimization_optimalportfolios_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save OptimalPortfolios optimization subtab output values to Data_Results."""
    return save_results_data_to_reactives(
        reactives_shiny = reactives_shiny,
        subtab_key = "Portfolio_Optimization_OptimalPortfolios_Outputs",
        data_value = data_value,
    )


def save_portfolio_simulation_inputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Simulation subtab input values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Simulation_Inputs", data_value = data_value)


def save_portfolio_simulation_outputs_to_reactives(
    *, reactives_shiny: Any, data_value: Any) -> dict:
    """Save Portfolio Simulation subtab output values to Data_Results."""
    return save_results_data_to_reactives(reactives_shiny = reactives_shiny, subtab_key = "Portfolio_Simulation_Outputs", data_value = data_value)


def _coerce_results_value_to_json(*, data: Any) -> dict[str, Any]:
    """Convert a raw ``Data_Results`` value to a JSON-serialisable dict."""
    if data is None:
        return {}
    if isinstance(data, pl.DataFrame):
        return {"records": data.to_dicts()}
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"records": data}
    return {"value": str(data)}


def build_results_data_json_from_reactives(
    *, reactives_shiny: Any, subtab_key: Any) -> dict[str, Any]:
    """Build a JSON-serialisable dict from ``Data_Results`` for one subtab key."""
    validation_result, validation_message = validate_data_results_in_reactives(reactives_shiny = reactives_shiny)
    if not validation_result:
        _logger.error(
            "build_results_data_json_from_reactives: invalid reactives structure: %s",
            validation_message,
        )
        raise Exception_Validation_Input(
            "build_results_data_json_from_reactives: invalid reactives structure: "
            f"{validation_message}",
        )

    validation_result, validation_message = validate_results_subtab_key(subtab_key = subtab_key)
    if not validation_result:
        _logger.error(
            "build_results_data_json_from_reactives: invalid subtab_key: %s",
            validation_message,
        )
        raise Exception_Validation_Input(
            f"build_results_data_json_from_reactives: invalid subtab_key: {validation_message}",
        )

    try:
        raw_data = get_results_data_from_reactives(reactives_shiny = reactives_shiny, subtab_key = subtab_key)
    except (RuntimeError, Exception_Configuration) as exc:
        _logger.warning(
            "build_results_data_json_from_reactives: could not retrieve '%s' from reactives, returning empty dict: %s",
            subtab_key,
            exc,
        )
        return {}

    json_dict = _coerce_results_value_to_json(data = raw_data)
    _logger.info(
        "build_results_data_json_from_reactives: built JSON dict for '%s' (%d top-level keys)",
        subtab_key,
        len(json_dict),
    )
    return json_dict


_VISUAL_OBJECT_SVG_FILENAMES: dict[str, str] = {
    "Chart_Weights_Analysis_Portfolio_Weight_Distribution_Over_Time": "chart_weights_analysis_portfolio_weight_distribution_over_time.svg",
    "Chart_Weights_Analysis_Portfolio_Current_Composition": "chart_weights_analysis_portfolio_current_composition.svg",
    "Chart_Portfolio_Analysis_Returns_Distribution": "chart_portfolio_analysis_returns_distribution.svg",
    "Chart_Portfolio_Comparison_Portfolio_vs_Benchmark": "chart_portfolio_comparison_portfolio_vs_benchmark.svg",
    "Chart_skfolio_Optimization_Portfolio_Weights_Comparison": "chart_skfolio_optimization_portfolio_weights_comparison.svg",
    "Chart_skfolio_Optimization_Comparison_Portfolio_Performance": "chart_skfolio_optimization_comparison_portfolio_performance.svg",
    "Chart_Simulation_Portfolio_Value_Fan_Chart": "chart_simulation_portfolio_value_fan_chart.svg",
    "Chart_Simulation_Terminal_Value_Distribution": "chart_simulation_terminal_value_distribution.svg",
}


_OUTPUTS_IMAGES_DIR: Path = Path(__file__).resolve().parents[1] / "reporting" / "outputs_images"


def export_visual_objects_to_svg(
    *, reactives_shiny: Any, output_dir: Path | None = None) -> dict[str, Path | None]:
    """Save Plotly figures stored in ``Visual_Objects_Shiny`` as SVG image files."""
    if output_dir is None:
        output_dir = _OUTPUTS_IMAGES_DIR
    if reactives_shiny is None or not isinstance(reactives_shiny, dict):
        _logger.warning("export_visual_objects_to_svg: invalid reactives_shiny — skipping export")
        return dict.fromkeys(_VISUAL_OBJECT_SVG_FILENAMES.values())

    visual_objects = reactives_shiny.get("Visual_Objects_Shiny")
    if not isinstance(visual_objects, dict):
        _logger.warning(
            "export_visual_objects_to_svg: 'Visual_Objects_Shiny' missing or not a dict — skipping",
        )
        return dict.fromkeys(_VISUAL_OBJECT_SVG_FILENAMES.values())

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _logger.error(
            "export_visual_objects_to_svg: cannot create output dir '%s': %s",
            output_dir,
            exc,
        )
        return dict.fromkeys(_VISUAL_OBJECT_SVG_FILENAMES.values())

    results: dict[str, Path | None] = {}
    for chart_key, svg_filename in _VISUAL_OBJECT_SVG_FILENAMES.items():
        svg_path = output_dir / svg_filename
        results[svg_filename] = None
        reactive_value = visual_objects.get(chart_key)
        if reactive_value is None:
            _logger.debug(
                "export_visual_objects_to_svg: key '%s' not found in Visual_Objects_Shiny",
                chart_key,
            )
            continue

        try:
            figure = reactive_value.get() if hasattr(reactive_value, "get") else reactive_value
        except Exception as exc:
            _logger.warning(
                "export_visual_objects_to_svg: could not read reactive value for '%s': %s",
                chart_key,
                exc,
            )
            continue

        if figure is None:
            _logger.debug("export_visual_objects_to_svg: no figure stored yet for '%s'", chart_key)
            continue

        try:
            if hasattr(figure, "save"):
                figure.save(str(svg_path), width=12, height=7, dpi=150, verbose=False)
            else:
                figure.write_image(str(svg_path), format="svg", width=1200, height=700)
            results[svg_filename] = svg_path
            _logger.info(
                "export_visual_objects_to_svg: saved '%s' (%d bytes)",
                svg_filename,
                svg_path.stat().st_size,
            )
        except Exception as exc:
            _logger.warning(
                "export_visual_objects_to_svg: could not export '%s' to SVG: %s",
                chart_key,
                exc,
            )

    saved_count = sum(1 for item_path in results.values() if item_path is not None)
    _logger.info(
        "export_visual_objects_to_svg: exported %d / %d charts to '%s'",
        saved_count,
        len(results),
        output_dir,
    )
    return results