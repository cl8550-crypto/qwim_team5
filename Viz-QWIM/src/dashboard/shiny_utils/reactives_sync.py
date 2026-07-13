"""Reactive observer registration for client and portfolio inputs.

This module registers ``@reactive.effect`` observers that keep
``reactives_shiny`` in sync with Shiny UI inputs for client data
and portfolio/simulation controls.
"""

from __future__ import annotations

from typing import Any

from shiny import reactive

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

from .reactives_access import safe_get_shiny_input_value
from .reactives_validation import validate_reactives_shiny_structure


#: Module-level logger instance
_logger = get_logger(name = __name__)

#: Maps each ``User_Inputs_Shiny`` key prefix to the corresponding base key in
#: ``Data_Results`` (i.e. ``"{base}_Inputs"`` and ``"{base}_Outputs"``).  Order
#: matters: more-specific prefixes must come before less-specific ones so that
#: the longest-match wins when grouping keys by subtab.
_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP: dict[str, str] = {
    "Input_Tab_Portfolios_Subtab_Portfolios_Analysis_": "Portfolio_Analysis",
    "Input_Tab_Portfolios_Subtab_Comparison_": "Portfolio_Comparison",
    "Input_Tab_Portfolios_Subtab_Weights_Analysis_": "Weights_Analysis",
    "Input_Tab_Portfolios_Subtab_Skfolio_": "Portfolio_Optimization_Skfolio",
    "Input_Tab_Results_Subtab_Simulation_": "Portfolio_Simulation",
}


def _reactive_key_to_input_id(*, reactive_key: str) -> str:
    """Derive the Shiny input element ID from a ``User_Inputs_Shiny`` reactive key.

    Applies the project naming convention::

        Input_Tab_<rest>  →  input_ID_tab_<rest_lowercased>

    Args:
        reactive_key: Key from the ``User_Inputs_Shiny`` sub-dict, e.g.
            ``Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name``

    Returns
    -------
        str: Corresponding Shiny input element ID, e.g.
            ``input_ID_tab_clients_subtab_clients_personal_info_client_primary_name``

    Raises
    ------
        ValueError: If ``reactive_key`` does not start with ``"Input_Tab_"``.
    """
    # Configuration validation
    if not reactive_key.startswith("Input_Tab_"):
        raise Exception_Validation_Input(
            f"reactive_key must start with 'Input_Tab_', got: '{reactive_key}'",
        )

    # Business logic: strip known prefix, lowercase the rest, re-attach new prefix
    suffix = reactive_key[len("Input_Tab_") :]
    return f"input_ID_tab_{suffix.lower()}"


def _register_single_input_observer(
    *, input: Any, reactives_shiny: dict[str, Any], input_id: str, reactive_key: str) -> None:
    """Mirror one Shiny UI input into ``User_Inputs_Shiny[reactive_key]``.

    Registers a ``reactive.effect`` that keeps
    ``reactives_shiny["User_Inputs_Shiny"][reactive_key]`` in sync with the
    ``input_id`` Shiny UI element.

    Uses a dedicated function scope to avoid the Python closure-over-loop-variable
    pitfall: each call binds ``input_id`` and ``reactive_key`` in its own local
    scope, so the inner ``_observer`` captures the correct pair of values.

    Args:
        input: The Shiny ``input`` proxy object available inside a module server.
        reactives_shiny: The central reactive state dictionary.
        input_id: Shiny input element ID, e.g.
            ``input_ID_tab_clients_subtab_clients_personal_info_client_primary_name``
        reactive_key: Corresponding key in ``User_Inputs_Shiny``, e.g.
            ``Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name``
    """
    # Resolve the target reactive.Value once at registration time so the observer
    # body performs no dict look-ups on every reactive invalidation cycle.
    target_reactive = reactives_shiny["User_Inputs_Shiny"].get(reactive_key)

    if target_reactive is None:
        _logger.warning(
            "Skipping observer registration: reactive key not found in User_Inputs_Shiny",
            extra={"reactive_key": reactive_key, "input_id": input_id},
        )
        return

    @reactive.effect
    def _observer() -> None:  # pragma: no cover
        """Forward the current UI input value to the corresponding User_Inputs_Shiny entry."""
        value = safe_get_shiny_input_value(input_events = input, input_identifier = input_id)

        # Input validation with early return - do not overwrite with None
        if value is None:
            return

        # Only use try-except for reactive.Value.set() which can fail unpredictably
        try:
            target_reactive.set(value)
            _logger.debug(
                "Synced client input to User_Inputs_Shiny",
                extra={"input_id": input_id, "reactive_key": reactive_key},
            )
        except Exception as exc:
            _logger.error(
                "Failed to sync client input to User_Inputs_Shiny",
                extra={
                    "input_id": input_id,
                    "reactive_key": reactive_key,
                    "error": str(exc),
                },
            )


def register_client_input_observers(
    *, input: Any, reactives_shiny: dict[str, Any]) -> None:
    """Keep ``reactives_shiny`` in sync with all client-related UI inputs.

    Registers reactive observers that fire whenever the user edits a value in
    the dashboard, covering all four client input domains in ``User_Inputs_Shiny``.

    Must be called once from within a Shiny module server (or app server) so that
    the ``@reactive.effect`` decorators are registered inside the active session
    context.  Covers all four client input domains in ``User_Inputs_Shiny``:

    - **Personal Info** — name, age, marital status, gender, risk tolerance, etc.
    - **Assets** — taxable, tax-deferred, and tax-free amounts (primary & partner)
    - **Goals** — essential, important, and aspirational goals (primary & partner)
    - **Income** — Social Security, pension, annuity, and other income (primary & partner)

    For every key in ``User_Inputs_Shiny`` that matches the pattern
    ``Input_Tab_clients_*``, this function registers an observer that:

    1. Reads the current UI input value via the corresponding
       ``input_ID_tab_clients_*`` Shiny element.
    2. Writes the value into ``reactives_shiny["User_Inputs_Shiny"][reactive_key]``
       so it is available to all other dashboard modules through the shared
       reactive state dictionary.

    The input-ID derivation follows the project naming convention::

        Input_Tab_clients_Subtab_clients_Personal_Info_client_Primary_Name
            →  input_ID_tab_clients_subtab_clients_personal_info_client_primary_name

    Args:
        input: The Shiny ``input`` proxy object available inside a module server or
            app server function.
        reactives_shiny: The central reactive state dictionary as returned by
            :func:`initialize_reactives_shiny`.

    Raises
    ------
        ValueError: If ``input`` is ``None`` or ``reactives_shiny`` has an invalid
            structure.

    Examples
    --------
    Call once at the top of each client subtab module server:

    .. code-block:: python

        @module.server
        def subtab_personal_info_server(
            input, output, session, reactives_shiny, data_utils, data_inputs
        ):
            register_client_input_observers(input, reactives_shiny)
            # ... rest of server logic
    """
    # Input validation with early returns
    if input is None:
        raise Exception_Validation_Input("register_client_input_observers: input cannot be None")

    is_valid, error_msg = validate_reactives_shiny_structure(reactives_shiny = reactives_shiny)
    if not is_valid:
        raise Exception_Validation_Input(
            f"register_client_input_observers: invalid reactives_shiny — {error_msg}",
        )

    # Configuration validation - gather all client-domain reactive keys
    user_inputs_dict = reactives_shiny["User_Inputs_Shiny"]
    client_reactive_keys = [key for key in user_inputs_dict if key.startswith("Input_Tab_clients_")]

    if not client_reactive_keys:
        _logger.warning(
            "register_client_input_observers: no 'Input_Tab_clients_*' keys found in "
            "User_Inputs_Shiny — no observers registered",
        )
        return

    # Business logic - register one scoped observer per (input_id, reactive_key) pair.
    # _register_single_input_observer creates a new function scope for each pair,
    # preventing the Python closure-over-loop-variable pitfall.
    registered_count = 0
    for reactive_key in client_reactive_keys:
        try:
            input_id = _reactive_key_to_input_id(reactive_key = reactive_key)
        except ValueError as exc:  # pragma: no cover
            _logger.warning(
                "Skipping observer: cannot derive input_id from reactive_key",
                extra={"reactive_key": reactive_key, "error": str(exc)},
            )
            continue

        _register_single_input_observer(
            input=input,
            reactives_shiny=reactives_shiny,
            input_id=input_id,
            reactive_key=reactive_key,
        )
        registered_count += 1

    _logger.info(
        "register_client_input_observers: registered %d client input observers",
        registered_count,
        extra={"registered_count": registered_count},
    )


def _register_subtab_snapshot_observer(
    *, input: Any, reactives_shiny: dict[str, Any], group_keys: list[str], results_base_key: str) -> None:
    """Snapshot all inputs for one dashboard subtab into ``Data_Results``.

    Registers one ``reactive.effect`` that writes a fresh snapshot dict to
    ``reactives_shiny["Data_Results"]["{results_base_key}_Inputs"]``.

    The snapshot is a plain ``dict`` mapping each ``User_Inputs_Shiny`` reactive
    key to its current UI input value.  Subtab servers read this snapshot via
    ``reactives_shiny["Data_Results"]["{results_base_key}_Inputs"].get()`` and
    write their computed results back into the matching ``"*_Outputs"`` entry.

    Uses a dedicated function scope so each registered observer closure captures
    its own ``group_keys`` and ``results_base_key``, avoiding the Python
    closure-over-loop-variable pitfall.

    Parameters
    ----------
    input : Any
        The Shiny ``input`` proxy available inside a module or app server.
    reactives_shiny : dict[str, Any]
        The central reactive state dictionary.
    group_keys : list[str]
        All ``User_Inputs_Shiny`` keys that belong to this subtab, e.g.
        ``["Input_Tab_Portfolios_Subtab_Comparison_Time_Period", ...]``.
    results_base_key : str
        Base key into ``Data_Results``, e.g. ``"Portfolio_Comparison"``.
        The observer writes to ``Data_Results["{results_base_key}_Inputs"]``.
    """
    inputs_results_key = f"{results_base_key}_Inputs"
    target_reactive = reactives_shiny["Data_Results"].get(inputs_results_key)

    if target_reactive is None:
        _logger.warning(
            "Skipping snapshot observer: Data_Results key not found",
            extra={"inputs_results_key": inputs_results_key, "results_base_key": results_base_key},
        )
        return

    # Pre-resolve (reactive_key → input_id) pairs once at registration time so
    # the inner observer body performs no dict look-ups on every invalidation.
    input_id_pairs: list[tuple[str, str]] = []
    for reactive_key in group_keys:
        try:
            input_id = _reactive_key_to_input_id(reactive_key = reactive_key)
            input_id_pairs.append((reactive_key, input_id))
        except ValueError as exc:  # pragma: no cover
            _logger.warning(
                "Skipping input in snapshot group: cannot derive input_id",
                extra={"reactive_key": reactive_key, "error": str(exc)},
            )

    @reactive.effect
    def _snapshot_observer() -> None:  # pragma: no cover
        """Collect all subtab input values and store as a snapshot dict."""
        snapshot: dict[str, Any] = {}
        for reactive_key, input_id in input_id_pairs:
            value = safe_get_shiny_input_value(input_events = input, input_identifier = input_id)
            snapshot[reactive_key] = value

        # Only use try-except for reactive.Value.set() which can fail unpredictably
        try:
            target_reactive.set(snapshot)
            _logger.debug(
                "Snapshot stored in Data_Results",
                extra={
                    "inputs_results_key": inputs_results_key,
                    "num_inputs": len(snapshot),
                },
            )
        except Exception as exc:
            _logger.error(
                "Failed to store snapshot in Data_Results",
                extra={"inputs_results_key": inputs_results_key, "error": str(exc)},
            )


def register_portfolio_results_observers(
    *, input: Any, reactives_shiny: dict[str, Any]) -> None:
    """Keep ``reactives_shiny["Data_Results"]`` in sync with portfolio and simulation UI inputs.

    Registers reactive observers that update ``Data_Results["*_Inputs"]`` entries
    whenever the user changes any portfolio or simulation UI control.

    Must be called once from within the appropriate Shiny module server (or app
    server) so that ``@reactive.effect`` decorators are registered inside the
    active session context.

    **What this function does**

    For each of the five subtabs it:

    1. Finds all ``User_Inputs_Shiny`` keys that belong to that subtab
       (prefix-matched against :data:`_PORTFOLIO_SUBTAB_RESULTS_KEY_MAP`).
    2. Registers one :func:`_register_subtab_snapshot_observer` that reacts
       whenever *any* input in the group changes and stores a fresh snapshot
       dict into ``Data_Results["{subtab}_Inputs"]``.
    3. Registers one :func:`_register_single_input_observer` per input so that
       the corresponding individual ``User_Inputs_Shiny`` entry is also updated.

    **Covered subtabs and Data_Results keys**

    =========================================  ==============================
    Subtab                                     ``Data_Results`` key updated
    =========================================  ==============================
    Portfolio Analysis                         ``Portfolio_Analysis_Inputs``
    Portfolio Comparison                       ``Portfolio_Comparison_Inputs``
    Weights Analysis                           ``Weights_Analysis_Inputs``
    Skfolio Portfolio Optimization             ``Portfolio_Optimization_Skfolio_Inputs``
    Portfolio Simulation                       ``Portfolio_Simulation_Inputs``
    =========================================  ==============================

    Subtab servers read the snapshot from ``Data_Results["*_Inputs"].get()``
    to detect changes and compute results, then write back into
    ``Data_Results["*_Outputs"]``.

    Parameters
    ----------
    input : Any
        The Shiny ``input`` proxy available inside a module or app server.
    reactives_shiny : dict[str, Any]
        The central reactive state dictionary as returned by
        :func:`initialize_reactives_shiny`.

    Raises
    ------
    ValueError
        If ``input`` is ``None`` or ``reactives_shiny`` has an invalid structure.

    Examples
    --------
    Call once at the top of the relevant tab server:

    .. code-block:: python

        @module.server
        def tab_portfolios_server(input, output, session, ...):
            register_portfolio_results_observers(input, reactives_shiny)
            # ... rest of server logic

        @module.server
        def tab_results_server(input, output, session, ...):
            register_portfolio_results_observers(input, reactives_shiny)
    """
    # Input validation with early returns
    if input is None:
        raise Exception_Validation_Input(
            "register_portfolio_results_observers: input cannot be None",
        )

    is_valid, error_msg = validate_reactives_shiny_structure(reactives_shiny = reactives_shiny)
    if not is_valid:
        raise Exception_Validation_Input(
            f"register_portfolio_results_observers: invalid reactives_shiny — {error_msg}",
        )

    user_inputs_dict = reactives_shiny["User_Inputs_Shiny"]
    data_results_dict = reactives_shiny["Data_Results"]

    # Configuration validation - group User_Inputs_Shiny keys by subtab prefix
    # using longest-match so that e.g. "_Portfolios_Analysis_" is not consumed
    # by the shorter "_Portfolios_" if such a prefix were ever added.
    subtab_groups: dict[str, list[str]] = {
        base_key: [] for base_key in _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP.values()
    }

    for reactive_key in user_inputs_dict:
        for prefix, base_key in _PORTFOLIO_SUBTAB_RESULTS_KEY_MAP.items():
            if reactive_key.startswith(prefix):
                subtab_groups[base_key].append(reactive_key)
                break  # longest-match already guaranteed by dict ordering

    # Business logic - for every subtab group with at least one key:
    # a) register a group snapshot observer → Data_Results["*_Inputs"]
    # b) register individual per-input observers → User_Inputs_Shiny
    total_registered = 0
    for base_key, group_keys in subtab_groups.items():
        if not group_keys:
            _logger.debug(
                "No User_Inputs_Shiny keys found for subtab — skipping",
                extra={"base_key": base_key},
            )
            continue

        inputs_results_key = f"{base_key}_Inputs"
        if inputs_results_key not in data_results_dict:
            _logger.warning(
                "Data_Results key missing — snapshot observer not registered",
                extra={"inputs_results_key": inputs_results_key},
            )
        else:
            _register_subtab_snapshot_observer(
                input=input,
                reactives_shiny=reactives_shiny,
                group_keys=group_keys,
                results_base_key=base_key,
            )

        # Per-input mirroring into User_Inputs_Shiny
        for reactive_key in group_keys:
            try:
                input_id = _reactive_key_to_input_id(reactive_key = reactive_key)
            except ValueError as exc:  # pragma: no cover
                _logger.warning(
                    "Skipping individual observer: cannot derive input_id",
                    extra={"reactive_key": reactive_key, "error": str(exc)},
                )
                continue

            _register_single_input_observer(
                input=input,
                reactives_shiny=reactives_shiny,
                input_id=input_id,
                reactive_key=reactive_key,
            )
            total_registered += 1

    _logger.info(
        "register_portfolio_results_observers: registered %d individual + %d snapshot observers",
        total_registered,
        len([g for g in subtab_groups.values() if g]),
        extra={
            "individual_observers": total_registered,
            "snapshot_observers": len([g for g in subtab_groups.values() if g]),
        },
    )
