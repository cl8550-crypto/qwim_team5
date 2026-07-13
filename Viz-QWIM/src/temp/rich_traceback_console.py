"""Demonstration script for the ``rich`` traceback and console integration.

This script exercises ``rich.traceback.install()`` and ``rich.console.Console``
to verify that formatted tracebacks and structured console logging work
correctly in the project's virtual environment.

Notes
-----
This file lives in ``src/temp/`` and is not part of the production package.
"""

import time
import rich
# from rich.console import Console
# from rich.traceback import install
rich.traceback.install()

def add_two(n1, n2):
    """Add two numbers and log the operation to the rich console.

    Parameters
    ----------
    n1 : numeric
        First operand.
    n2 : numeric
        Second operand.

    Returns
    -------
    numeric
        The sum of *n1* and *n2*.
    """
    console.log("About to add two numbers.", log_locals=True)
    return n1 + n2

console = rich.console.Console()
for i in range(10):
    time.sleep(0.2)
    add_two(1, i)
add_two(1, 'a')