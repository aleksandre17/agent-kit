"""Where OBSERVED STATE lives -- resolved from the manifest's own plane declarations.

A journal and a lock are not payload and they are not a host's answer: they are the kit's reading
of a run that is happening RIGHT NOW. That reading belongs to the plane the manifest declares for
exactly this, and this module's whole job is to refuse to hold a second copy of that plane's path.
A path written into an interpreter is a second home for a truth the manifest already states, and
it is the home a host cannot change (Cardinal III).

What this module DOES name is the CLASS -- the one word by which the manifest says which plane
holds what a run leaves behind. That word is vocabulary, not a path, and a plane that changes its
root changes nothing here. Where the manifest declares no such plane, this refuses rather than
inventing a folder: a record written somewhere nobody classified is the unaccounted path the whole
design exists to prevent.
"""

from __future__ import annotations

from errors import KitError

#: The class, in the manifest's own vocabulary, of the plane that holds what a run leaves behind.
OBSERVED = "ephemeral"


class PlaneError(KitError):
    """No plane is declared for observed state, or more than one is -- and a name that resolves
    to two places is not a name."""


def root(ctx) -> str:
    found = [p["root"].rstrip("/") for p in ctx.manifest.planes if p["class"] == OBSERVED]
    if len(found) != 1:
        raise PlaneError(
            f"this kit declares {len(found)} plane(s) of class {OBSERVED!r}; exactly one is "
            f"required, because a run's own record has exactly one place to be put"
        )
    return found[0]


def place(ctx, name: str) -> str:
    """A host-relative path inside the observed plane, for a record this interpreter owns."""
    return f"{root(ctx)}/{name}"


def scope(ctx):
    """A workspace whose writes are bounded to the observed plane and nothing else. Every write
    in this kit is scope-checked; a record of a run is not the one exception."""
    return ctx.workspace.scoped([root(ctx) + "/"])
