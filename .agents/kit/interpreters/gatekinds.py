"""Gate kinds -- the ONE discovery of which module can judge which kind of gate.

Two callers now need the registry and neither may own it: the `check` verb, running every declared
gate over the tree, and `judgement`, applying the edit gates to a change in somebody's hand. A verb
is built FROM the core, so a core module that imported one would be a cycle wearing a layer's name
(Cardinal VIII, the arrow); and a second discovery loop would be a second answer to *who judges this
kind* (Cardinal III). So the discovery lives here, once, and both reach it.

It knows no gate kind of its own. A new kind of gate is a MODULE in `gates/` that declares its
entry, never an edit here (Cardinal II, IV) -- and a kind two modules claim is refused rather than
ordered, because a name that resolves to two things is not a name.

WHERE those modules are and WHAT they publish is this module's subject; HOW a directory of modules
is turned into a registry is not, and is no longer written here: a second subject arrived that needs
the same loop -- which module reads which kind of reference -- and the loop moved to `kinds`, where
it is written once and knows neither of us.
"""

from __future__ import annotations

from pathlib import Path

import kinds
from errors import KitError

#: Where a gate kind may be declared. One directory, read by name, never a list kept by hand.
GATES = Path(__file__).resolve().parent / "gates"


class GateError(KitError):
    """A declaration named a gate kind no discovered module can evaluate, or two modules claim
    one kind -- which is a name resolving to two meanings, refused rather than ordered."""

    code = "KIT0023"


def registry(entry: str = "KINDS") -> dict:
    """Every gate kind's entry of one registry, discovered from the gate modules: `KINDS` judges
    the tree; another name (an edit judge's) is read by the same discovery, never a second one."""
    return kinds.registry(GATES, entry, "gate kind", GateError)
