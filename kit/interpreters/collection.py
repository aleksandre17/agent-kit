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


def _validated(ctx, rel: str, schema: str):
    try:
        value = ctx.workspace.read_json(rel)
    except ValueError as exc:
        raise CollectionError(f"{rel}: not readable as JSON -- {exc}") from exc
    errors = ctx.manifest.validate(value, schema) if schema else []
    if errors:
        raise CollectionError(f"{rel} does not honour schema {schema!r}:\n  " + "\n  ".join(errors))
    return value


def _document(ctx, item, name: str) -> Reading:
    rel = item["target"]
    if not ctx.workspace.exists(rel):
        raise CollectionError(
            f"{rel}: declared readable as {name!r} and absent; run `init` first"
        )
    value = _validated(ctx, rel, item.get("validates"))
    return Reading(name, "document", value, [(rel, value)], item.get("validates"))


def _collection(ctx, item, name: str) -> Reading:
    root = item["target"].rstrip("/")
    records = []
    for rel in ctx.workspace.files_under(root):
        if not rel.endswith(".json"):
            continue
        records.append((rel, _validated(ctx, rel, item.get("validates"))))

    seen: dict = {}
    for rel, value in records:
        identity = value.get(IDENTITY)
        if identity in seen:
            raise CollectionError(
                f"{root}: {IDENTITY} {identity!r} is declared by two files -- {seen[identity]} and "
                f"{rel}. One thing with two declarations has two homes for every truth it carries, "
                f"and both will go on reading as correct while they disagree. Delete one."
            )
        seen[identity] = rel
    records.sort(key=lambda pair: pair[1].get(IDENTITY, ""))
    return Reading(name, "collection", [value for _rel, value in records], records,
                   item.get("validates"))


#: An open registry, keyed by the SHAPE OF THE DECLARED PATH: a target ending in `/` is a
#: directory of records, anything else is one document. A new reader kind is a registration.
READER_KINDS = {"document": _document, "collection": _collection}


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
    return READER_KINDS[kind_of(item)](ctx, item, name or item.get("reads_as") or item["target"])


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
