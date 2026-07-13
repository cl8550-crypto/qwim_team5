"""Quantitative models package.

This package contains implementations of domain-specific quantitative models
used across the QWIM dashboard and reporting pipeline.  Each sub-package
provides a self-contained set of classes for a particular modelling domain.

Sub-packages
------------
discounting
    Present-value discounting models (constant rate, etc.).
inflation
    Inflation projection models.
interest_rate
    Interest-rate models.
longevity
    Longevity and mortality models.
portfolio_optimization
    Portfolio construction and optimisation.
portfolio_rebalancing
    Portfolio rebalancing strategies.
simulation
    Monte Carlo simulation dispatch and scenario generation.
taxation
    Tax models for after-tax return calculations.
yield_curve
    Yield-curve construction and interpolation.
"""

from __future__ import annotations
