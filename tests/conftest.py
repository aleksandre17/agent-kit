"""One home for the suite's one environmental rule: running a test never writes into the kit.

The kit's lock refuses any path it cannot account for, so a bytecode cache written into `kit/` by an
import makes the kit refuse itself. Pytest loads this file before any test module is imported, so
the rule holds for every directory under `tests/`, and a new test cannot forget it.
"""

import sys

sys.dont_write_bytecode = True
