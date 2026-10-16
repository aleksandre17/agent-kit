"""The `collection` reader: a declared target ending in `/` -- a directory of records, each read
through its schema, each holding one identity."""

from __future__ import annotations

import collection

def _collection(ctx, item, name: str) -> collection.Reading:
    root = item["target"].rstrip("/")
    records = []
    for rel in ctx.workspace.files_under(root):
        if not rel.endswith(".json"):
            continue
        records.append((rel, collection.validated(ctx, rel, item.get("validates"))))

    # A record names itself by its `id`; a kind whose schema declares none (an observation) is named
    # by its file, which its directory already makes unique -- never by an absent value shared by all.
    def named(rel, value):
        return value.get(collection.IDENTITY) if isinstance(value, dict) and collection.IDENTITY in value else rel

    seen: dict = {}
    for rel, value in records:
        identity = named(rel, value)
        if identity in seen:
            raise collection.CollectionError(
                f"{root}: {collection.IDENTITY} {identity!r} is declared by two files -- {seen[identity]} and "
                f"{rel}. One thing with two declarations has two homes for every truth it carries, "
                f"and both will go on reading as correct while they disagree. Delete one."
            )
        seen[identity] = rel
    records.sort(key=lambda pair: str(named(*pair)))
    return collection.Reading(name, "collection", [value for _rel, value in records], records,
                   item.get("validates"))



READERS = {"collection": _collection}
