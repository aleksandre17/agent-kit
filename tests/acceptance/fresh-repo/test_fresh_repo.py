"""The acceptance run. One command, every suite in this directory.

    python tests/acceptance/fresh-repo/test_fresh_repo.py

This module holds no assertion of its own -- deliberately, so that discovery importing it a
second time cannot double-count anybody's tests. The suites are `test_journey` (the walk-in
install and the human door), `test_composition` (what a SET of declarations does) and
`test_selection` (what a HOST CHOSE, and the plan it was shown first).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    suite = unittest.TestLoader().discover(str(HERE), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
