"""Reading back what a capability declared readable -- the plural of a binding.

A binding is one host file read through its schema. Some host truths are MANY files a host
authors freely (cards, entries, records), and a projection over them needs the same guarantees a
single binding gets: validated at the boundary, absent-is-a-declared-state, and no second home
for an identity.

Where a readable path comes from: the INSTALL that owns it, via `reads_as`. Never a path constant
in this module and never a second copy in a gate's params -- the capability already stated where
its files live when it declared that it installs them, and a truth stated twice in one file
drifts exactly as fast as one stated twice across two.
"""

from __future__ import annotations

import functools
from pathlib import Path

import kinds
from errors import KitError

#: The field by which a member of a collection identifies itself. One home for the identity rule.
IDENTITY = "id"


class CollectionError(KitError):
    """A readable declaration is absent, unreadable, invalid, or claims one identity twice."""

    code = "KIT0002"


class Reading:
    """What one `reads_as` name resolved to: the value a projection sees, and the records behind
    it, each still carrying the path it came from so a writer can put it back where it was."""

    __slots__ = ("name", "kind", "value", "records", "schema")

    def __init__(self, name: str, kind: str, value, records: list, schema=None) -> None:
        self.name = name
        self.kind = kind
        self.value = value
        self.records = records
        #: The schema this reading was judged by, carried WITH it. A reader that needs to know
        #: what a record MAY hold -- as opposed to what one happens to hold -- has exactly one
        #: legitimate place to ask, and it is the declaration that judged the read. Carried here
        #: rather than re-derived downstream, so the answer stays single.
        self.schema = schema

    def record_of(self, identity: str):
        for rel, value in self.records:
            if value.get(IDENTITY) == identity:
                return rel, value
        return None, None

    def identities(self) -> list:
        return sorted(value.get(IDENTITY, "?") for _rel, value in self.records)


def validated(ctx, rel: str, schema: str):
    try:
        value = ctx.workspace.read_json(rel)
    except ValueError as exc:
        raise CollectionError(f"{rel}: not readable as JSON -- {exc}") from exc
    errors = ctx.manifest.validate(value, schema) if schema else []
    if errors:
        raise CollectionError(f"{rel} does not honour schema {schema!r}:\n  " + "\n  ".join(errors))
    return value


#: Where a reader kind may be declared -- keyed by the SHAPE OF THE DECLARED PATH (`kind_of`). A new
#: reader kind is a module in `readers/`, never an edit here.
READERS = Path(__file__).resolve().parent / "readers"


@functools.lru_cache(maxsize=None)
def readers() -> dict:
    """Every reader kind, by the name each `readers/` module declares it under."""
    return kinds.registry(READERS, "READERS", "reader kind", CollectionError)


def kind_of(item: dict) -> str:
    return "collection" if item["target"].endswith("/") else "document"


def read(ctx, item, name=None) -> Reading:
    """One declared readable, read the way its OWN declaration says it is shaped.

    This is the single door through which any caller turns an install into a value, and the only
    place that decides whether a declared target is one document or many records. A caller that
    reached past it and read the target as a file would be deciding the shape of somebody else's
    declaration -- and would meet a DIRECTORY the first time a capability declared a space, which
    is precisely the failure this function exists to make impossible.
    """
    kind = kind_of(item)
    reader = readers().get(kind)
    if reader is None:
        raise CollectionError(f"{item['target']}: no reader answers for the kind {kind!r}; the kinds "
                              f"declared are {sorted(readers())}")
    return reader(ctx, item, name or item.get("reads_as") or item["target"])


def named_reading(ctx, name: str, absent: type) -> Reading:
    """The readable one declaration names, or that declaration's own refusal.

    A declaration that says *read this over X* is answered in exactly one place. The loop was
    written twice before this existed -- once per judge that needed it -- and two loops answering
    *which value is X* is the drift that stays invisible, because each one goes on resolving
    correctly from where it stands (Cardinal III). The refusal to RAISE is handed in, the way a
    registry is handed the clash it should report: what a dangling name means belongs to the caller
    that declared it, and a shared helper that chose the error would have decided how somebody
    else's failure is spelled.
    """
    readings = read_all(ctx, ctx.enabled_capabilities())
    if name not in readings:
        raise absent(
            f"this gate was declared over a readable named {name!r}, which no enabled capability "
            f"declares; the names declared are {sorted(readings)}"
        )
    return readings[name]


def read_all(ctx, capabilities) -> dict:
    """Every readable of every enabled capability, by name: what a HOST authored at a path a
    capability declared readable (`reads_as`), and what a capability SHIPS as a document (its id),
    read where the kit that speaks carries it -- on a host running its pinned copy, the in-tree
    file, never a vendored second copy (link L3a). Two claims on one name are refused for the same
    reason two capabilities claiming one path is: the loser's declaration would go on reading as
    true while the value came from somewhere else."""
    readings: dict = {}
    owners: dict = {}

    def claim(name, owner, reading):
        if name in readings:
            raise CollectionError(
                f"capabilities {owners[name]!r} and {owner!r} both declare a readable "
                f"named {name!r}; a name that resolves to two things is not a name"
            )
        owners[name] = owner
        readings[name] = reading

    for capability in capabilities:
        for item in capability.installs:
            name = item.get("reads_as")
            if name:
                claim(name, capability.id, read(ctx, item, name))
        for declared in capability.raw.get("documents", []):
            value = capability.documents[declared["id"]]
            claim(declared["id"], capability.id,
                  Reading(declared["id"], "document", value, [(declared["source"], value)],
                          declared["validates"]))
    return readings
