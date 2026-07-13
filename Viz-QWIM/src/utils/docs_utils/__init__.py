"""Documentation utilities package for QWIM projects.

This package provides pure-function helpers for build-time API reference
documentation generation.  All logic intended for use during ``mkdocs build``
lives in :mod:`~src.utils.docs_utils.api_reference_generation` and is tested
independently of the MkDocs plugin runtime.

Modules
-------
api_reference_generation
    Discover Python modules, map paths to module names and documentation
    paths, build navigation trees, generate ``SUMMARY.md``, and inventory
    objects that are missing NumPy-style docstrings.
"""

from __future__ import annotations
