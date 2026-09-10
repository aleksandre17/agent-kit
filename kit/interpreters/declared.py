"""Where a gate's rules come from -- resolved once, for every gate that reads rules.

A sensor is a pair: a MACHINE that knows how to look, and a DECLARATION that says what to look
for. The second half is the same shape wherever it appears -- a set of named documents, some
SHIPPED by a capability and some AUTHORED by the host in a path a capability declared readable,
each carrying a list of rows under a field name its own schema declares. That resolution was
written once for residence and would have been written again, identically, for the first sensor
of another subject. Two copies of a rule-resolver are two homes for the answer to *whose rule
wins*, and they stay in agreement exactly until one of them is fixed.

So it lives here, and it knows nothing about what any rule SAYS. The field a document carries its
rows under arrives as an argument, because that word belongs to the schema that declares the
document -- not to this module and not to the gate that called it.

Two refusals are the whole content, and both are the same refusal:

  * a NAME that resolves to two documents is not a name -- the loser would go on reading as true
    while the value came from somewhere else, and both readers would be locally correct;
  * a RULE id declared twice is two homes for one judgement, and the same follows.

A missing source is refused rather than treated as empty, which is the ledger's rule in its
sharpest form: a scan of nothing passes gloriously and reads exactly like a scan that looked.
"""

from __future__ import annotations

from errors import KitError

import collection


class DeclarationError(KitError):
    """A declared source of rules is missing, or a name resolves to two things."""


def sources(ctx, names: list) -> dict:
    """The named documents, wherever they were declared: SHIPPED by a capability, or AUTHORED by
    the host in a path a capability declared readable. Both arrive by name."""
    found: dict = {}
    owners: dict = {}

    def claim(name, value, owner):
        if name in found:
            raise DeclarationError(
                f"capabilities {owners[name]!r} and {owner!r} both declare rules named {name!r}; "
                f"a name that resolves to two things is not a name"
            )
        owners[name] = owner
        found[name] = value

    for capability in ctx.enabled_capabilities():
        for identity, document in capability.documents.items():
            if identity in names:
                claim(identity, document, capability.id)
        for item in capability.installs:
            if item.get("reads_as") in names:
                claim(item["reads_as"], collection.read(ctx, item).value, capability.id)

    missing = [name for name in names if name not in found]
    if missing:
        raise DeclarationError(
            f"this gate was declared over rules named {missing}, which no enabled capability "
            f"ships or declares readable; a source that cannot be found is not an empty source"
        )
    return found


def rules(ctx, names: list, field: str) -> list:
    """Every row of every named source, in the order the sources were declared, with each id
    claimed exactly once. `field` is the word the source's own SCHEMA gives its rows."""
    found = sources(ctx, names)
    rows, owners = [], {}
    for name in names:
        for rule in found[name][field]:
            if rule["id"] in owners:
                raise DeclarationError(
                    f"rule {rule['id']!r} is declared by both {owners[rule['id']]!r} and "
                    f"{name!r}; two rules under one name is two homes for one judgement"
                )
            owners[rule["id"]] = name
            rows.append(rule)
    return rows
