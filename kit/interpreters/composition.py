"""Base + overlay -- one declaration composed from two, and never two bodies for one thing.

The failure this module exists to make unreachable is not a duplicated file. It is TWO FILES THAT
ARE BOTH RIGHT: one truth with two homes, each locally correct, drifting apart while every reader
standing at either one sees no contradiction at all. The cure is structural rather than
disciplinary -- what binds is declared ONCE and RENDERED into every composition, so a binding line
is not a line anybody is trusted to keep in step. It is a line nobody can restate.

Three rules, and the second is the whole design:

  * A composition is BASE plus INSTANCE. The base states what is true of the kind; the instance
    states what is true of this host's one of them.

  * **An instance never overrides.** A key carried by both is REFUSED, not resolved. Overriding is
    precedence, and precedence is how the loser's declaration goes on reading as true while the
    value came from somewhere else. Where a host must vary something the base states, the base was
    wrong to state it: that thing was never true of the kind, and the cure is to move it -- not to
    let one side win an argument at render time. The schemas make the collision nearly unreachable
    by declaring disjoint key sets; this refuses the residue, because `additionalProperties` is a
    statement about one document and composition is a statement about two.

  * An instance naming a base nobody declares is UNBOUND -- a declared state on the composed row,
    carried to the surface in those words. Not a traceback, and not a row that renders as though
    it were complete. The verb that renders is not the verb that judges: a gate says the same
    thing with an exit code, and the surface says it in prose, and neither is allowed to be the
    only one that knows.

It knows the name of no capability, no role and no field. WHICH readable holds the instances,
which sources hold the bases and which field points from one to the other all arrive as data,
from the declaration that owns them.
"""

from __future__ import annotations

import collection
import declared
from errors import KitError

#: The word a composed row carries when its base could not be found. Vocabulary of the contract
#: between this module and the templates that read its output -- one home, spelled here, never
#: invented by an instance.
UNBOUND = "unbound"

#: The word a composed row carries for the lines that bind every composition whatever its base.
#: Rendered INTO each row rather than referenced from it, because a reference can be left
#: unfollowed and a rendered line cannot.
PROTOCOL = "protocol"

#: How the census is put: the bases this host has TAKEN UP, each with the instances that took it,
#: and a COUNT of the ones it has not. The asymmetry is deliberate and it is not squeamishness.
#:
#: A base a host instanced may be named on the host's surface, because the host named it. A base
#: nobody instanced may NOT: a framework that printed its cast into a host that has chosen none of
#: it would have decided how that host is organised before meeting it, which is the one thing this
#: kit is not allowed to do. So the untaken are COUNTED and located rather than listed -- a number
#: is a declared zero, and it points at the declaration where the names honestly live.
#:
#: A count and never a silence: omitting them would make a base shipped and never used
#: indistinguishable from one that was never shipped, and those are two different questions asked
#: of two different people.
TAKEN = "taken"
UNTAKEN = "untaken"
INSTANCES = "instances"
ORIGIN = "origin"


class CompositionConflict(KitError):
    """An instance and its base both carry one key. Refused rather than ordered: whichever side
    lost would go on declaring a value the composition does not have."""


class Composed:
    """What one `composes` declaration resolved to: the composed rows, and the census of bases."""

    __slots__ = ("spec", "rows", "census")

    def __init__(self, spec: dict, rows: list, census: dict) -> None:
        self.spec = spec
        self.rows = rows
        self.census = census


def _bases(ctx, spec: dict) -> tuple[dict, dict]:
    """Every declared base, by id, and where each one came from.

    The merge across sources is `declared.rules`, unchanged and for the same reason it was written:
    a base id declared twice is two homes for one judgement, and it is refused before anything is
    composed on it. The ORIGIN is read separately, from the same named sources, because a census
    that cannot say whether a base was shipped or authored can report a zero and not explain it.
    """
    where = spec["base"]
    rows = {row[collection.IDENTITY]: row
            for row in declared.rules(ctx, where["sources"], where["list"])}
    origin = {}
    for name, document in declared.sources(ctx, where["sources"]).items():
        for row in document[where["list"]]:
            origin[row[collection.IDENTITY]] = name
    return rows, origin


def _shape(ctx, bases: dict, instances) -> set:
    """The vocabulary a composed row ALWAYS has, whatever any one row happens to say.

    Every field is present, holding nothing where it was not declared. Otherwise an absence
    reaches a surface as a name that does not exist rather than as a field that is empty -- and
    nothing downstream can tell a typo from an honest blank, which is the difference between a
    defect and a state.

    Two sources, and neither is a list kept here. From the BASES: whatever they carry, so a row
    whose base was not found still has the shape of one that was. From the SCHEMA that judged the
    instances: what an instance MAY hold, which is the only place that question has an answer --
    the union of what the instances happen to hold is a reading of today's content, and an
    optional field nobody has used yet would be missing from it exactly when a host first needs
    the surface to say so.
    """
    shape = {key for base in bases.values() for key in base}
    if instances.schema:
        shape |= set(ctx.manifest.schema(instances.schema).get("properties", {}))
    return shape - {collection.IDENTITY}


def _merge(instance: dict, base, shape: set, protocol: list) -> dict:
    row = {key: None for key in shape}
    if base is not None:
        overlap = (set(base) & set(instance)) - {collection.IDENTITY}
        if overlap:
            raise CompositionConflict(
                f"{instance.get(collection.IDENTITY)!r} and the base it composes both declare "
                f"{sorted(overlap)}. An instance adds and never overrides: one of these two "
                f"declarations would go on reading as true while the composition carried the "
                f"other. Whatever a host must vary was never true of the kind -- move it, rather "
                f"than letting one side win here."
            )
        row.update({key: value for key, value in base.items() if key != collection.IDENTITY})
    row.update(instance)
    row[UNBOUND] = base is None
    row[PROTOCOL] = protocol
    return row


def composed_of(ctx, capability, readings) -> "Composed | None":
    """The composition a capability declares, or None. Every name points INSIDE the capability's
    own declaration; no path, no capability id and no field name reaches this module as a
    constant. A capability that composes nothing says so by declaring nothing."""
    spec = capability.raw.get("composes")
    if not spec:
        return None
    bases, origin = _bases(ctx, spec)
    shared = spec["shared"]
    protocol = declared.rules(ctx, shared["sources"], shared["list"])
    instances = readings[spec["instances"]]
    shape = _shape(ctx, bases, instances)
    named_by = spec["base"]["named_by"]

    rows = [
        _merge(instance, bases.get(instance.get(named_by)), shape, protocol)
        for instance in instances.value
    ]

    # The census is the other half of the same reading, and it is the half that is easy to skip:
    # the composed rows answer "what does this host run", and only the census answers "what was
    # declared and never taken up". A zero that occupies no space on a surface is a zero nobody
    # will ever be asked about.
    taken, untaken = [], 0
    for identity in sorted(bases):
        instanced = sorted(row[collection.IDENTITY] for row in rows
                           if row.get(named_by) == identity)
        if not instanced:
            untaken += 1
            continue
        entry = dict(bases[identity])
        entry[ORIGIN] = origin.get(identity)
        entry[INSTANCES] = [{collection.IDENTITY: name} for name in instanced]
        taken.append(entry)
    return Composed(spec, rows, {TAKEN: taken, UNTAKEN: untaken})
