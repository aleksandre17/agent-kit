"""Install modes -- the ONE discovery of which module installs which declared mode.

A capability's install row names a MODE; a module in `modes/` answers it. Each mode carries the two
halves an install is made of -- FORESEE, which says what would happen, and APPLY, which does it --
and the PHASE of a run that carries it out. The apply never decides: it is handed the foreseen
disposition, which is what makes a plan incapable of drifting from its own application.

Two callers need the answer and neither may own it: `init` plans and applies, and `reconcile` asks
whether a mode's target is a SPACE (a place carried through a clone by its marker). A table kept in
one of them was the second home ADR-023 amendment 4 measured (`init.INSTALL_MODES` beside
`space.MODES`); a new mode is now a module that declares its entry, and no interpreter that
dispatches over the set is edited (Cardinals II, III).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import kinds
from errors import KitError

#: Where an install mode may be declared. One directory, read by name, never a list kept by hand.
MODES = Path(__file__).resolve().parent / "modes"
ENTRY = "MODES"


class InstallError(KitError):
    """A declaration named an install mode this interpreter does not know, a selection that
    contradicts host truth, or a written file that does not honour its own schema."""

    code = "KIT0025"


@dataclass(frozen=True)
class Mode:
    """One install mode: the phase that carries it, its two halves, and whether its target is a
    SPACE -- a directory the host authors into, carried through a clone by its marker."""

    phase: str
    foresee: object = None
    apply: object = None
    space: bool = False


@functools.lru_cache(maxsize=None)
def registry() -> dict:
    """Every install mode, by the name each `modes/` module declares it under."""
    return kinds.registry(MODES, ENTRY, "install mode", InstallError)


def mode_of(capability, item) -> Mode:
    found = registry().get(item["mode"])
    if found is None:
        raise InstallError(
            f"capability {capability.id!r} declares install mode {item['mode']!r}; "
            f"registered modes are {sorted(registry())}"
        )
    return found


def opens_space(mode: str) -> bool:
    """Whether a mode's target is a space, present when a clone would receive it (its marker)."""
    found = registry().get(mode)
    return bool(found and found.space)
