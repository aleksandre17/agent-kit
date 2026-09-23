"""The edge one work record draws to another, read once (ADR-020 decision 5).

A record may name ONE other record it hangs under. That is the whole grammar: a recursive edge to
the same kind of thing, not a ladder of named rungs. A rung list is a closed enumeration -- work
that needs a fifth level either lies about its depth or waits for a schema change, and three of
the four rungs sit empty on most work anyway (Cardinal II). Depth here is a POSITION, never a
class: the same record is read the same way whether it hangs under nothing or under four others.

So this module holds exactly three readings and no verdict:

  * WHERE a record hangs -- the chain up from it, and how that chain ends. It ends at a record
    that names nothing, at a name no record answers to, or at a record already on the way up.
    Those three endings are different facts and stay different: a typed name and a closed loop
    fail for opposite reasons, and one message for both would send the reader to the wrong file.
  * WHO hangs under a record -- the same edge read backwards, computed from the records in hand
    rather than stored anywhere. A back-pointer would be a second home for one edge, and the day
    the two disagreed each would go on reading as correct (Cardinal III).
  * WHICH records name nothing that justifies them. A count, and nothing about it: whether that
    number is too high is a ceiling, a ceiling is a number, and every number here is the host's.

Nothing in this file refuses anything, and nothing in it writes. A chain that ends badly is
reported by the module that reports; a count is capped by the ratchet this kit already carries.
"""

from __future__ import annotations

import collection
import lifecycle as lifecycle_module

#: The fields a record declares its lineage in. One home for each spelling, read at both ends of
#: every boundary it crosses -- the grammar that judges them, and the readings below.
PARENT, ORIGIN, PRODUCED = "parent", "origin", "produced"

#: What this module can be held to a budget on. The word a host writes in its own map, and it is
#: the field's own spelling: one word, one meaning, at the declaration and at the count that caps
#: it. It says RECORDS and not the name of any collection, because which collection is governed is
#: declared by the capability that governs one and may not be spelled a second time here.
UNJUSTIFIED = "records_without_origin"


def among(ctx):
    """The records this edge is read among, or None where that question has no single answer.

    They are the members of the GOVERNED collection -- found through the capability that declares
    it governs one, so the collection's name is read from its one home rather than repeated here.
    A host with no such collection, or with two, gets None: an unasked question, never an empty
    list. An empty list would report a host that was never looked at as a host with nothing in it.
    """
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(capability, "governs", None) for capability in capabilities):
        return None
    try:
        governed = lifecycle_module.the_governed(
            capabilities, collection.read_all(ctx, capabilities))
    except (lifecycle_module.LifecycleError, collection.CollectionError):
        return None
    return governed.members.value


def by_identity(records) -> dict:
    return {record[collection.IDENTITY]: record for record in records}


def children_of(records, identity: str, field: str = PARENT) -> list:
    """Every record that names this one in `field`. The edge read backwards, computed each time
    from what is in hand: there is no stored list of parts, and there will not be one.

    The field is a PARAMETER and not a constant read from here, because a caller that was handed
    the field by a declaration must pass on the field it was handed -- an interpreter that
    substituted its own spelling would be answering about an edge nobody asked about.
    """
    return [record for record in records if record.get(field) == identity]


def descendants_of(records, identity: str, field: str = PARENT) -> list:
    """Everything below a record, at any depth, each reached once. A record already seen is not
    followed again, so a loop in the host's declaration costs this reading nothing and is left to
    be REPORTED as the contradiction it is rather than met as a recursion limit."""
    found, frontier, seen = [], [identity], {identity}
    while frontier:
        for child in children_of(records, frontier.pop(), field):
            name = child[collection.IDENTITY]
            if name in seen:
                continue
            seen.add(name)
            found.append(child)
            frontier.append(name)
    return found


class Chain:
    """Where a record hangs, and how the walk up from it ENDED. `names` is the walk in order,
    starting at the record itself; `missing` is the name nothing answered to, and `repeated` is
    the name the walk arrived at twice. At most one of those two is set, and a chain with neither
    reached a record that names nothing -- which is a root and a complete, ordinary state."""

    __slots__ = ("names", "missing", "repeated")

    def __init__(self, names: list, missing=None, repeated=None) -> None:
        self.names, self.missing, self.repeated = names, missing, repeated

    @property
    def resolves(self) -> bool:
        return self.missing is None and self.repeated is None

    @property
    def depth(self) -> int:
        """How far above this record the walk reached. Recorded, never judged: the number that
        would turn a distance into a verdict does not exist here either."""
        return len(self.names) - 1


def chain_of(records, record: dict, field: str = PARENT) -> Chain:
    """The walk up from one record, and the ending it found."""
    index = by_identity(records)
    names, seen = [record[collection.IDENTITY]], {record[collection.IDENTITY]}
    standing = record
    while standing.get(field) is not None:
        above = standing[field]
        if above in seen:
            return Chain(names, repeated=above)
        if above not in index:
            return Chain(names, missing=above)
        names.append(above)
        seen.add(above)
        standing = index[above]
    return Chain(names)


def unresolved(records, field: str = PARENT) -> list:
    """Every chain that ends in a contradiction, said in the words of the ending it found.

    These are the two things that are genuinely illegal about this edge, and both are facts about
    the DECLARATION rather than about the work: a name nothing answers to, and a walk that arrives
    where it started. Neither can be true of a record that names no parent, which is why this
    reading is empty on a host that has not started drawing edges yet.
    """
    failures = []
    for record in sorted(records, key=lambda r: r[collection.IDENTITY]):
        chain = chain_of(records, record, field)
        if chain.missing is not None:
            failures.append(
                f"record {chain.names[0]!r} hangs under {chain.missing!r}, and no record of this "
                f"collection answers to that name -- the walk up got as far as "
                f"{' -> '.join(chain.names)} and stopped at a name, not at a record"
            )
        elif chain.repeated is not None:
            failures.append(
                f"record {chain.names[0]!r} hangs under {chain.repeated!r}, which is already on "
                f"the way up from it: {' -> '.join(chain.names)} -> {chain.repeated}. A record "
                f"that is its own ancestor has no root, and nothing about it can be computed from "
                f"what is below it"
            )
    return failures


def unjustified(records) -> list:
    """Every record that names nothing which justifies it, by identity and in order.

    Counted, and only counted. Every record in existence on the day this ships is one of these,
    so a gate that refused one would be switched off within a day -- and the count is what makes
    the state visible in the meantime. What is too many is the host's word, written as a ceiling
    in its own map and judged by the ratchet that already judges every other count here.
    """
    return sorted(record[collection.IDENTITY] for record in records
                  if record.get(ORIGIN) is None)


def references(record: dict) -> list:
    """Every typed reference this record draws, as `(field, reference)`.

    The GRAMMAR of a reference is declared where a criterion declares one and is not restated
    here: this reading knows only which FIELDS carry one, which is the single thing about them
    that belongs to lineage.
    """
    drawn = []
    if record.get(ORIGIN) is not None:
        drawn.append((ORIGIN, record[ORIGIN]))
    drawn += [(PRODUCED, item) for item in (record.get(PRODUCED) or [])]
    return drawn
