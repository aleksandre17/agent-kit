"""A DECLARED SPACE -- a place the host authors into, and the one form in which its EMPTINESS
survives the repository.

A capability that declares a `space` install, and a collection projection over a set the host has
not filled, each own a directory whose honest state is EMPTY. Creating the directory states that
truthfully to the filesystem -- and to nobody else. Git carries FILES; an empty directory is not a
thing a repository can hold. So the kit creates it, the host commits, and the path is simply gone
from the next clone -- at which point the floor reads a DRAWN path as MISSING and tells the host it
is broken when nothing is.

The kit and git agreed on the path's NAME and disagreed on whether it EXISTED (Cardinal VII), and
the disagreement was invisible from both sides because each was locally right: the kit had made
the directory, git had nothing to lose, and the floor was reading the world correctly. A failure
of this shape never announces itself as a contradiction -- it announces itself as a thing that is
simply not there.

Therefore the directory is carried in a form both sides provably read the same way: ONE marker
file, written UNCONDITIONALLY -- into a space holding records exactly as into one holding none.
Two things were learned making it conditional, and both are kept here because each cost a test:

  * a file that appears in one host and not another is a VARIATION, and the two-host boundary rule
    names it as a difference whose cause is readable only by knowing what each host happened to
    have authored. An unconditional declaration has no branch for anyone to trace;
  * so the marker's sentence must be true of a full space and an empty one alike. It states the
    SPACE, never its contents.

It is a DECLARED STATE and not content: it says nothing about any domain, which is the test the
blueprint's blank rule (T2) actually applies. And its NAME is not here -- a filename written into
a host is policy, and an interpreter holds none. It is declared by the capability that can never
be disabled, so every host has been told it and no path the kit writes ends in a word no
declaration carries.

One home, because a second would drift: where the name is declared, the sentence the marker
carries, and the act of opening a space are here, and are reached by every verb that opens one.
"""

from __future__ import annotations

from errors import KitError

#: The block a capability declares the marker in, and the field inside it. The NAME itself is not
#: here: a filename written into a host is policy, and an interpreter holds none (Cardinal IV). It
#: was here for one draft, and the two-host boundary test refused it -- a path whose last segment
#: no declaration carries is a path no host was ever told about, whatever the kit's reasons were.
#: It is declared by the capability that can never be disabled, so every host has been told it.
BLOCK = "space"
FIELD = "marker"

#: What the marker says. It states the SPACE, never its contents: the marker is written whether
#: the space holds records or none, so its sentence must be true in both cases. An earlier draft
#: said "intentionally EMPTY", which made the marker's PRESENCE a variation between hosts -- and
#: the two-host boundary test named it at once as a difference with no declared ancestor, which is
#: exactly what it was. A declaration that is unconditional has no branch to trace.
TEXT = (
    "# This directory is DECLARED by the kit and is yours to author into.\n"
    "# The file exists only because a repository cannot carry a directory of its own; without it\n"
    "# the path would vanish from the next clone whenever the directory happened to be empty,\n"
    "# and be reported as missing. Delete it on purpose or not at all.\n"
)


#: The install modes that OPEN a space -- `init` carries each out with `declare`. Named here, with
#: the rule below, so that the installer's foresight and the upgrade's reconciliation read one
#: definition of when a space is there.
MODES = frozenset({"space", "taken"})


class SpaceError(KitError):
    """No capability in this kit declares how a directory is carried, so a space cannot be opened
    without the interpreter inventing a filename -- which is the one thing it may not do."""

    code = "KIT0042"


def marker(manifest) -> str:
    """The marker's name, read from the one capability that declares it. Refused rather than
    defaulted: a default here would be the policy this module exists to keep out, and it would be
    invisible -- a host would carry a file no declaration mentions and nothing would say why."""
    found = {c.id: c.raw[BLOCK][FIELD] for c in manifest.capabilities if BLOCK in c.raw}
    if len(found) != 1:
        raise SpaceError(
            f"a declared directory is carried by a marker named in a capability's {BLOCK!r} "
            f"block, and {sorted(found) or 'no capability'} declares one. Exactly one must: "
            f"two would drift, and none leaves the interpreter to invent the name."
        )
    return next(iter(found.values()))


def marker_in(manifest, target: str) -> str:
    """Where the marker of `target` sits. One composition, so no caller ever spells the name."""
    return target.rstrip("/") + "/" + marker(manifest)


def carried(manifest, ws, target: str) -> bool:
    """Whether the space reaches a clone: its directory AND its marker are there. A bare directory
    is held by this working tree only -- the next clone has no such path -- so a space opened before
    its marker existed is NOT there, and is completed rather than kept."""
    return ws.exists(target) and ws.exists(marker_in(manifest, target))


def declare(manifest, ws, target: str) -> None:
    """Open `target` as a declared space: the directory, and the one file that carries it through
    a clone. `ws` is any workspace scope entitled to write there -- the entitlement is the caller's
    to hold, because a space is owned by the capability that declared it."""
    ws.make_dir(target)
    path = marker_in(manifest, target)
    if not ws.exists(path):
        ws.write_text(path, TEXT)
