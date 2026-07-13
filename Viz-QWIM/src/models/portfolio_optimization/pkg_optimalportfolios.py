"""Portfolio optimization methods from optimalportfolios Python package.

Facade module — re-exports all public functions from the private sub-modules:

- :mod:._optport_validators — pure validation and conversion helpers
- :mod:._optport_builders — Constraints builder and Portfolio_QWIM extractor
- :mod:._optport_convex — minimum variance, maximum quadratic utility,
  budgeted risk contribution
- :mod:._optport_hierarchical — maximum diversification, maximum Sharpe ratio,
  maximum CARA GMM, tracking error minimization

All public names are importable directly from this module, preserving
backward compatibility.

References
----------
- optimalportfolios: https://pypi.org/project/optimalportfolios/
- Markowitz, H. (1952). Portfolio Selection. Journal of Finance.
"""

from __future__ import annotations

from ._optport_validators import (
    _compute_covar_and_means,
    _convert_polars_to_numpy_returns,
    _validate_returns_data,
)
from ._optport_builders import (
    _build_constraints,
    _extract_weights_to_portfolio_qwim,
)
from ._optport_convex import (
    calc_optimalportfolios_budgeted_risk_contribution,
    calc_optimalportfolios_maximum_quadratic_utility,
    calc_optimalportfolios_minimum_variance,
)
from ._optport_hierarchical import (
    calc_optimalportfolios_maximum_cara_gaussian_mixture,
    calc_optimalportfolios_maximum_diversification,
    calc_optimalportfolios_maximum_sharpe_ratio,
    calc_optimalportfolios_tracking_error_minimization,
)


__all__ = [
    "_compute_covar_and_means",
    "_convert_polars_to_numpy_returns",
    "_validate_returns_data",
    "_build_constraints",
    "_extract_weights_to_portfolio_qwim",
    "calc_optimalportfolios_minimum_variance",
    "calc_optimalportfolios_maximum_quadratic_utility",
    "calc_optimalportfolios_budgeted_risk_contribution",
    "calc_optimalportfolios_maximum_diversification",
    "calc_optimalportfolios_maximum_sharpe_ratio",
    "calc_optimalportfolios_maximum_cara_gaussian_mixture",
    "calc_optimalportfolios_tracking_error_minimization",
]
