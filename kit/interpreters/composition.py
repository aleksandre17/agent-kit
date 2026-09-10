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

#: The STANDING of one member of a declared vocabulary against one composed row, and the three
#: words this module PROVIDES for it. Naming what you provide is a promise; naming what you
#: consume is a policy -- so these are spelled here, in the machinery that produces them, and
#: never read from an instance.
#:
#: The whole reason the accounting exists is that these three are told apart nowhere else. A list
#: of what an instance says it can do reads identically to a list of what it HAS BEEN SEEN to do,
#: and both read identically to a short list belonging to something that genuinely needs nothing.
#: So every member of the vocabulary is placed in exactly one of them, for every row, always:
#:
#:   CLAIMED -- an instance says it, and nothing has been observed. Testimony, and never a fact.
#:   PROVEN  -- a RECORD of something that happened names this row and this member. Never
#:              authored: no instance schema in this kit has a field a proof could be written in.
#:   ABSENT  -- the vocabulary declares it and this instance claims nothing. A named gap, which
#:              is the state an empty list can never express.
CLAIMED = "claimed"
PROVEN = "proven"
ABSENT = "absent"
STANDING = "standing"
COUNTS = "counts"
TOTAL = "total"

#: The readable whose records may turn a claim into an observation, BY NAME -- or nothing, which
#: is a declared gap and not a zero. A count of `0 proven` taken where no source of proof was
#: declared at all is an attribution that cannot fail, and an attribution that cannot fail
#: certifies rather than measures. So the name is carried to the surface with the count, and a
#: surface holding a zero beside no source is required to say which of the two it is looking at.
PROOF_SOURCE = "proof_source"


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


def _observed(spec: dict, readings, identity) -> "set | None":
    """Which vocabulary members a RECORD says were observed of this row, or None where no source
    of proof was declared. Nothing is inferred and nothing is assumed: a proof is a record, in a
    readable the declaration named, that names this row and that member. Where the declaration
    names no readable this returns None rather than an empty set, because those are two different
    answers -- `nothing has been observed` and `nothing here could ever observe` -- and a surface
    shown only the empty set would report the second as the first.
    """
    where = spec.get(PROVEN)
    if not where:
        return None
    reading = readings[where["reading"]]
    return {record[where["names"]] for _rel, record in reading.records
            if record.get(where["of"]) == identity and where["names"] in record}


def _accounted(spec: dict, row: dict, vocabulary: list, observed) -> dict:
    """One row's standing against the whole declared vocabulary -- every member placed, none
    omitted. Grouped by standing rather than flagged, so that a surface iterates a state instead
    of filtering one, and so that a state with no members is a section that can SAY SO.

    This reads a claim and can never read a proof out of one: an instance's own words reach the
    CLAIMED group and no other, whatever they say. That is not a check performed here -- it is
    the shape of the data. A claim arrives from a document a host authored; an observation
    arrives from a record of something that happened; there is no path between them.
    """
    names = spec[CLAIMED]["names"]
    claims = {claim[names]: claim for claim in (row.get(spec[CLAIMED]["field"]) or [])}
    grouped = {CLAIMED: [], PROVEN: [], ABSENT: []}
    for member in vocabulary:
        identity = member[collection.IDENTITY]
        claim = claims.get(identity)
        if claim is None:
            state = ABSENT
        elif observed is not None and identity in observed:
            state = PROVEN
        else:
            state = CLAIMED
        entry = dict(member)
        entry.update({key: value for key, value in (claim or {}).items() if key != names})
        entry[STANDING] = state
        grouped[state].append(entry)
    counts = {state: len(members) for state, members in grouped.items()}
    counts[TOTAL] = len(vocabulary)
    return {**grouped, COUNTS: counts, PROOF_SOURCE: (spec.get(PROVEN) or {}).get("reading")}


def _accounts(ctx, spec: dict, rows: list, readings) -> None:
    """The accounting a composition declares, written onto every row it composed. Knows the name
    of no vocabulary and no member: which list is counted, which field holds the claims and which
    sub-field names a member all arrive from the declaration that owns them."""
    where = spec["vocabulary"]
    vocabulary = declared.rules(ctx, where["sources"], where["list"])
    for row in rows:
        if spec["id"] in row and row[spec["id"]] is not None:
            raise CompositionConflict(
                f"{row.get(collection.IDENTITY)!r} already carries {spec['id']!r}, which this "
                f"composition's accounting also produces. A name that resolves to two things is "
                f"not a name, and the computed value would silently win."
            )
        row[spec["id"]] = _accounted(
            spec, row, vocabulary, _observed(spec, readings, row.get(collection.IDENTITY)))


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

    # An ACCOUNTING, where one is declared: every member of a declared vocabulary placed against
    # every composed row, so that what an instance claims, what has been observed of it, and what
    # it does not claim at all are three groups on the surface rather than one list that reads as
    # whichever of them the reader already believed.
    if spec.get("accounts"):
        _accounts(ctx, spec["accounts"], rows, readings)

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
