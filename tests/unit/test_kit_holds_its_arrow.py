"""Unit: the kit's own interpreters hold the arrow its own repository declares (ADR-017, ADR-022).

Found the expensive way: three gate modules imported ports, every unit and acceptance test stayed
green, and only `check` on the kit's own repository -- host #0, which declares the layering of the
interpreters it ships -- named the breach. A defect that only the dogfood host can see is caught a
release late. So the same gate kind that judges a host's tree judges the kit's source here, on every
unit run, through the declaration host #0 already holds.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import arrow  # noqa: E402 -- the gate module, discovered beside the others
from context import Context  # noqa: E402


def test_the_kit_source_holds_the_arrow_its_repository_declares():
    ctx = Context(kit_root=KIT, host_root=REPO)
    breaches = arrow.KINDS[arrow.KIND](ctx, {"sources": {"validates": "arrow"}})
    assert not breaches, "the kit's interpreters break their own declared layering:\n  " + "\n  ".join(breaches)
