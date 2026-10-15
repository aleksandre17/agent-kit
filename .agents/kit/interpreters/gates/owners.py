"""A place somebody OWNS: the row says whose it is, and this reading holds the row to it.

ADR-020 decision 6 puts a record's proofs in a PLACE and declares that place where every other
place of this corpus is declared -- as a row of the host's map, with what it holds, how much a
resident of it may bind, and when it is read. Nothing here scans a tree, and nothing here learns
a second way to find a document: the places, their residents and their classes all arrive from
the ONE reading of the corpus that already exists, and this module adds a question to it rather
than an answer beside it (Cardinal III, and Cardinal VIII on direction).

**Why the binding is on the ROW and not on the record.** The other direction was available: the
record could carry the path of the place that belongs to it. That is a LINK -- a claim about a
file, written where nothing can check it, rotting silently and reading afterwards exactly like a
claim that is still true. The row is not a claim about a place; the row IS how a place comes to
exist here at all. So the plane that owns places owns the sentence, the work record stays the one
home of work and says nothing about the tree, and the only thing left to hold is that the owner a
row names is real -- which is what this reading does.

**And it names no class of record and no collection.** A row states which collection its owner
lives in, because that is the host's own statement about its own tree; this module resolves that
name against what the host has declared readable and says so plainly when nothing answers to it.
An interpreter that knew which collection owns evidence would have privileged one plane, and the
second host to arrive with a different one would need the framework's permission to be read.
"""

from __future__ import annotations

import collection
import corpus

#: What a place row calls its owner, and the two things that reference carries. The row's own
#: spelling, declared once here and read from the schema that judges it -- never a path, never a
#: collection name and never the name of any class a place may hold.
OWNED_BY, COLLECTION = "owned_by", "collection"


class Owned:
    """One place a record claims: the row, the owner it names, and what lives there NOW.

    The residents are not counted into a verdict anywhere. A place that is empty is an honest
    state of young work, and this reading exists so that what is there can be READ through the
    plane whose job that is -- never so that a number about it can be invented here.
    """

    __slots__ = ("place", "owner", "residents")

    def __init__(self, place: dict, owner: dict, residents: list) -> None:
        self.place, self.owner, self.residents = place, owner, residents

    @property
    def path(self) -> str:
        return self.place[corpus.PATH]

    @property
    def holds(self):
        return self.place.get(corpus.HOLDS)


def owned(reading) -> list:
    """Every place of this corpus that declares an owner, with the residents the same reading
    already found in it. One pass over one reading; no second walk of the tree."""
    found = []
    for place in reading.places:
        if place.get(OWNED_BY) is None:
            continue
        found.append(Owned(place, place[OWNED_BY],
                           [r for r in reading.residents
                            if r.place is not None
                            and r.place.get(corpus.PATH) == place[corpus.PATH]]))
    return sorted(found, key=lambda item: item.path)


def _owner_named(owner: dict) -> str:
    return f"{owner.get(COLLECTION)!r}/{owner.get(collection.IDENTITY)!r}"


def _owners_are_real(ctx, params) -> list:
    """Every owned place whose owner cannot be resolved, and every owner or path claimed twice."""
    reading = corpus.read(ctx, params)
    if reading.nothing_read():
        return []
    readings = collection.read_all(ctx, ctx.enabled_capabilities())
    failures, by_owner, by_path = [], {}, {}
    for item in owned(reading):
        name, where = item.owner.get(collection.IDENTITY), item.owner.get(COLLECTION)
        if where not in readings:
            failures.append(
                f"the place {item.path!r} is owned by {_owner_named(item.owner)}, and nothing "
                f"enabled on this host declares a collection named {where!r} readable; the "
                f"readable names are {sorted(readings)}. The owner cannot be resolved, so the "
                f"place belongs to nobody that can be checked"
            )
        elif name not in readings[where].identities():
            failures.append(
                f"the place {item.path!r} is owned by {_owner_named(item.owner)}, and no record "
                f"of that collection answers to that name. A place whose owner does not exist "
                f"outlives the work it was opened for and is read afterwards as if it still had "
                f"one"
            )
        claim = (where, name)
        if claim in by_owner:
            failures.append(
                f"{_owner_named(item.owner)} owns both {by_owner[claim]!r} and {item.path!r}. "
                f"One record's proofs would then live in two places, and a reader standing at "
                f"either one would be correct about it and wrong about the record"
            )
        by_owner.setdefault(claim, item.path)
        if item.path in by_path:
            failures.append(
                f"the place {item.path!r} is claimed by {_owner_named(by_path[item.path])} and "
                f"by {_owner_named(item.owner)}. A place with two owners has none: whichever "
                f"reader gets there first decides whose proofs these are"
            )
        by_path.setdefault(item.path, item.owner)
    return failures


KINDS = {"owned-places-resolve": _owners_are_real}
