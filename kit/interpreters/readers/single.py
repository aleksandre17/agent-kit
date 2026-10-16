"""The `document` reader: a declared target that is ONE file, read through its schema."""

from __future__ import annotations

import collection

def _document(ctx, item, name: str) -> collection.Reading:
    rel = item["target"]
    if not ctx.workspace.exists(rel):
        raise collection.CollectionError(
            f"{rel}: declared readable as {name!r} and absent; run `init` first"
        )
    value = collection.validated(ctx, rel, item.get("validates"))
    return collection.Reading(name, "document", value, [(rel, value)], item.get("validates"))



READERS = {"document": _document}
