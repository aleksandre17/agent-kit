"""The one guard every unit test needs before it imports an interpreter.

A unit test reaches into `kit/interpreters/` by putting it on `sys.path` and importing the module
under test. Python then writes `kit/interpreters/__pycache__/*.pyc` beside the source -- and the
kit REFUSES a file its lock cannot account for (KIT0041), so the moment a unit test runs, the kit
can no longer state what it is and every acceptance test that installs it fails. Measured, not
imagined: 221 of 379 tests failed this way in one run, with no logic change anywhere, and the
failures name version ranges, selection and serving -- nothing that would send a reader here.

The interpreter itself has always set this flag (`cli.py`), and so does the acceptance harness.
The unit tests were the one door left open, each file deciding for itself; now the decision has
ONE home and a test file cannot forget it (Cardinal III). It is set here rather than asserted,
because a conftest is the only place that runs before the imports it has to protect.

`pytest` imports this file before it imports any test module in this directory, which is exactly
the moment the flag has to be set: after the first import it would already be too late.
"""

import sys

sys.dont_write_bytecode = True
