"""Investor goal definitions for the MSGP goal-based investing model.

This module implements the investor-facing parameters of Kim et al. (2019),
"Personalized goal-based investing via multi-stage stochastic goal
programming" (Quantitative Finance, 20:3, 515-526): current wealth, future
contributions, and prioritized consumption goals :math:`G^p_t`. See Section
2.1 of the paper for the corresponding notation (``G^p_t``, ``I_t``, ``x_{1,0}``).

Design notes
------------
The paper indexes goals by an integer priority level ``p`` and assumes one
scalar priority ordering. In practice, users describe goals by name
("Emergency Fund", "Retirement", ...), each attached to a stage (time) and a
priority rank. This module keeps the human-facing ``Goal`` objects separate
from the priority-indexed arrays (``G^p_t``) the optimizer consumes, and
``GoalSet`` performs the translation, including tie-break rules when two
goals share a priority rank.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Goal:
    """A single personalized consumption/spending goal.

    Parameters
    ----------
    name : str
        Human-readable goal label, e.g. ``"Retirement"``.
    target_wealth : float
        Target consumption amount in today's (stage-0) monetary units. This
        is the paper's :math:`G^p_t` before inflation adjustment; inflation
        compounding is applied inside the optimizer using scenario-specific
        inflation paths (equation 2 of the paper).
    horizon_stage : int
        Stage index ``t`` (0-indexed, matching the scenario tree) at which
        the goal's consumption occurs. A goal may span multiple stages by
        creating multiple ``Goal`` objects that share a priority.
    priority : int
        Priority rank, 1 = highest priority solved first (paper Section 2.2,
        Figure 1). Ties are broken by ``horizon_stage`` ascending, then by
        insertion order, so that within a shared priority the model attempts
        earlier obligations first -- an explicit, documented convention the
        paper leaves unspecified.
    probability_of_success : float, optional
        Investor-stated target probability of achieving this goal, used only
        for reporting / CVaR calibration (Section 2.3). Not a hard
        optimization constraint unless ``cvar_alpha`` /
        ``cvar_shortfall_ratio`` are also supplied.
    current_wealth : float, default 0.0
        Wealth already earmarked for this goal at stage 0. Only meaningful
        for the first goal in a household's overall plan; the optimizer sums
        all ``current_wealth`` across goals into the single stage-0 cash
        balance :math:`x_{1,0}` (paper assumes all initial wealth starts in
        cash, generalized here to accept a nonzero amount from any goal).
    contribution_schedule : dict[int, float], optional
        Mapping of stage -> additional investment :math:`I_t` earmarked for
        this goal. Schedules from all goals are summed per-stage by
        ``GoalSet.investment_schedule``.
    cvar_alpha : float, optional
        If set (e.g. 0.90), enables a downside-protection CVaR constraint on
        this goal's shortfall per equation (25)-(26) of the paper.
    cvar_shortfall_ratio : float, optional
        The ``rho`` in equation (25): average shortfall in the worst
        ``1-alpha`` scenarios must be <= ``rho * inflation-adjusted goal``.
        Required if ``cvar_alpha`` is set.
    """

    name: str
    target_wealth: float
    horizon_stage: int
    priority: int
    probability_of_success: float | None = None
    current_wealth: float = 0.0
    contribution_schedule: dict[int, float] = field(default_factory=dict)
    cvar_alpha: float | None = None
    cvar_shortfall_ratio: float | None = None

    def __post_init__(self) -> None:
        if self.target_wealth < 0:
            raise ValueError(f"Goal '{self.name}': target_wealth must be >= 0.")
        if self.horizon_stage < 0:
            raise ValueError(f"Goal '{self.name}': horizon_stage must be >= 0.")
        if self.priority < 1:
            raise ValueError(f"Goal '{self.name}': priority must be >= 1 (1 = highest).")
        if (self.cvar_alpha is None) != (self.cvar_shortfall_ratio is None):
            raise ValueError(
                f"Goal '{self.name}': cvar_alpha and cvar_shortfall_ratio must be set together."
            )
        if self.cvar_alpha is not None and not (0.0 < self.cvar_alpha < 1.0):
            raise ValueError(f"Goal '{self.name}': cvar_alpha must be in (0, 1).")


@dataclass
class GoalSet:
    """A prioritized collection of an investor's goals.

    Provides the translation from human-readable ``Goal`` objects into the
    priority-indexed structures (``G^p_t``, priority levels ``1..P``) that
    :mod:`stochastic_optimizer` consumes directly.
    """

    goals: list[Goal]

    def __post_init__(self) -> None:
        if not self.goals:
            raise ValueError("GoalSet requires at least one goal.")
        # Stable ordering used everywhere downstream: priority asc, then
        # horizon_stage asc, then original insertion order.
        self._order = sorted(
            range(len(self.goals)),
            key=lambda i: (self.goals[i].priority, self.goals[i].horizon_stage, i),
        )

    @property
    def priority_levels(self) -> list[int]:
        """Distinct priority levels in solve order (ascending = highest first)."""
        seen: list[int] = []
        for i in self._order:
            p = self.goals[i].priority
            if p not in seen:
                seen.append(p)
        return seen

    def goals_at_level(self, priority: int) -> list[Goal]:
        """All goals sharing a given priority rank, in tie-break order."""
        return [self.goals[i] for i in self._order if self.goals[i].priority == priority]

    def goals_up_to_level(self, priority: int) -> list[Goal]:
        """All goals with priority <= the given rank (cumulative, paper's 1..p)."""
        return [self.goals[i] for i in self._order if self.goals[i].priority <= priority]

    def initial_wealth(self) -> float:
        """Total stage-0 cash wealth :math:`x_{1,0}^{\\rightarrow}`, summed over goals."""
        return float(sum(g.current_wealth for g in self.goals))

    def investment_schedule(self, n_stages: int) -> np.ndarray:
        """Aggregate additional investment :math:`I_t` for stages ``1..n_stages``.

        Returns
        -------
        np.ndarray
            Array of length ``n_stages + 1``; index 0 is unused (stage 0 has
            no contribution, only initial wealth), matching the paper's
            ``t = 1, ..., T`` indexing for ``I_t``.
        """
        sched = np.zeros(n_stages + 1)
        for g in self.goals:
            for stage, amount in g.contribution_schedule.items():
                if stage < 1 or stage > n_stages:
                    raise ValueError(
                        f"Goal '{g.name}': contribution at stage {stage} outside 1..{n_stages}."
                    )
                sched[stage] += amount
        return sched

    def goal_targets_by_level(self, n_stages: int) -> dict[int, np.ndarray]:
        """Per-priority-level goal arrays :math:`G^p_t`, ``t = 0..n_stages``.

        Returns
        -------
        dict[int, np.ndarray]
            Maps priority level -> array of length ``n_stages + 1`` giving the
            (pre-inflation) consumption target at each stage for goals *at
            that exact priority level* (not cumulative -- cumulative handling
            of equation (2)/(14) happens in the optimizer via ``c^{p-1}``).
        """
        out: dict[int, np.ndarray] = {}
        for p in self.priority_levels:
            arr = np.zeros(n_stages + 1)
            for g in self.goals_at_level(p):
                if g.horizon_stage > n_stages:
                    raise ValueError(
                        f"Goal '{g.name}': horizon_stage {g.horizon_stage} > n_stages {n_stages}."
                    )
                arr[g.horizon_stage] += g.target_wealth
            out[p] = arr
        return out

    def cvar_specs_by_level(self) -> dict[int, list[tuple[int, float, float]]]:
        """Per-priority-level CVaR downside-protection specs.

        Returns
        -------
        dict[int, list[tuple[int, float, float]]]
            Maps priority level -> list of ``(horizon_stage, alpha,
            shortfall_ratio)`` tuples for goals at that level requesting
            protection (equation 25-26).
        """
        out: dict[int, list[tuple[int, float, float]]] = {}
        for p in self.priority_levels:
            specs = [
                (g.horizon_stage, g.cvar_alpha, g.cvar_shortfall_ratio)
                for g in self.goals_at_level(p)
                if g.cvar_alpha is not None
            ]
            if specs:
                out[p] = specs
        return out

    def summary(self) -> str:
        """Human-readable summary table, one line per goal, priority order."""
        lines = [
            f"{'Priority':>8} | {'Goal':<20} | {'Stage':>5} | {'Target':>14} | {'Success target':>14}"
        ]
        for i in self._order:
            g = self.goals[i]
            success = f"{g.probability_of_success:.0%}" if g.probability_of_success else "n/a"
            lines.append(
                f"{g.priority:>8} | {g.name:<20} | {g.horizon_stage:>5} | "
                f"{g.target_wealth:>14,.0f} | {success:>14}"
            )
        return "\n".join(lines)
