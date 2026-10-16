"""No two interpreter modules share a name: the interpreters are imported flat.

Every interpreter directory is put on `sys.path`, and the kinds registries import a discovered
module by its file name. Two files with one name in two families (`gates/check.py` beside
`verbs/check.py`) would not be refused anywhere: whichever directory comes first wins, and the other
module is silently shadowed -- a verb that runs a gate's code, read as correct by both.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

INTERPRETERS = Path(__file__).resolve().parents[2] / "kit" / "interpreters"


def test_every_interpreter_module_name_has_one_home():
    homes = defaultdict(list)
    for path in INTERPRETERS.rglob("*.py"):
        if "__pycache__" not in path.parts:
            homes[path.stem].append(path.relative_to(INTERPRETERS).as_posix())
    shared = {name: sorted(where) for name, where in homes.items() if len(where) > 1}
    assert shared == {}, f"one name, two modules -- the first on sys.path shadows the other: {shared}"
