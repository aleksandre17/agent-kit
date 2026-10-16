"""Install modes that OPEN a space: a place the host authors into, carried by its marker.

The take plane is opened as a space too -- every host has one, empty until it takes something
(ADR-018).
"""

from __future__ import annotations

import space
from installmodes import Mode


def _foresee(ws, item, state):
    """A space is its directory AND the marker that carries it through a clone. One opened before
    the marker existed is completed -- the marker is the only write, and nothing the host put in
    the space is touched -- because a directory held only by the working tree is missing from the
    next clone, and the floor then reads a drawn place as broken when nothing is."""
    return "keep" if space.carried(state["manifest"], ws, item["target"]) else "create"


def _open(ctx, ws, item, state):
    """A place the HOST authors into, owned by the capability that declared it. The kit opens it
    and puts no content in it: seeding an example would be the kit authoring the host's content,
    and an empty space is an honest declared state, not a missing one -- carried, by `space`, in
    the one form that survives a clone."""
    space.declare(ctx.manifest, ws, item["target"])


MODES = {
    "space": Mode("install", _foresee, _open, space=True),
    "taken": Mode("install", _foresee, _open, space=True),
}
