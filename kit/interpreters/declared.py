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

    code = "KIT0005"


#: The word that turns a source list from a CLOSED enumeration into an OPEN set (ADR-014). It is
#: the word a document and a readable install already use to state the contract they keep, so the
#: selector adds no vocabulary: `{"validates": "<schema>"}` means every source, from every enabled
#: capability, that keeps that contract -- found by the contract, exactly as the stance vocabulary
#: is found, never by a publisher's name.
CONTRACT = "validates"
#: The documents in which a taken adapter VOUCHES for the enforcers it finds in the host -- found by
#: their contract, never by a product's name: read by the normative tree, by `prove` and by the floor.
ENFORCERS = {CONTRACT: "enforcers"}


def named(capabilities, spec) -> list:
    """The source names a declaration reads. A LIST is a closed set its author enumerated; an
    OBJECT carrying the contract word is the open set of every source any of these capabilities
    ships (a document) or declares readable (an install read back) under that contract -- sorted,
    so the order is the declaration's and never a manifest's. An open set that finds nothing is
    a DECLARED ZERO, not a missing source: nobody having published is a state, and the reader
    that asked says so in its own words."""
    if isinstance(spec, list):
        return spec
    if not isinstance(spec, dict) or set(spec) != {CONTRACT}:
        raise DeclarationError(
            f"a source set is either a list of names or {{{CONTRACT!r}: <schema>}}; {spec!r} is "
            f"neither, and a selector nobody can read would select whatever a guess decided")
    contract = spec[CONTRACT]
    found = set()
    for capability in capabilities:
        found |= {d["id"] for d in capability.raw.get("documents", []) if d.get(CONTRACT) == contract}
        found |= {item["reads_as"] for item in capability.installs
                  if item.get(CONTRACT) == contract and item.get("reads_as")}
    return sorted(found)


def sources(ctx, names) -> dict:
    """The named documents, wherever they were declared: SHIPPED by a capability, or AUTHORED by
    the host in a path a capability declared readable. Both arrive by name -- or by the contract
    they keep, when the set is open (`named`)."""
    names = named(ctx.enabled_capabilities(), names)
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


def homes(ctx, names) -> set:
    """The host paths the named sources are AUTHORED at -- the installs a capability declared
    readable under those names. A shipped document has no host path and is not among them."""
    names = named(ctx.enabled_capabilities(), names)
    return {item["target"] for capability in ctx.enabled_capabilities() for item in capability.installs
            if item.get("reads_as") in names}


#: The two words a `where` is written in. A filter is ONE field and ONE value, and that narrowness
#: is the design: a referent set is often a SUBSET of a declared list -- the states a place may
#: name, the kinds of one plane -- and the alternative to expressing it as data was a gate module
#: per subset, each holding in Python a rule the vocabulary already states in a row. What it cannot
#: express is deliberate: no absence, no negation, no range, no second field, no expression. A
#: declaration that could compute would stop being data, and nothing could generate it (Cardinal IV).
FIELD, EQUALS = "field", "equals"


def matching(rows: list, where) -> list:
    """The rows a filter selects, or all of them when no filter was declared. A row that does not
    CARRY the field is not selected: absent is not equal to anything, and a filter that admitted
    it would widen a referent set by silence."""
    if where is None:
        return rows
    if not isinstance(where, dict) or set(where) != {FIELD, EQUALS}:
        raise DeclarationError(
            f"a filter is {{{FIELD!r}: <field>, {EQUALS!r}: <value>}}; {where!r} is neither, and a "
            f"selector nobody can read would select whatever a guess decided")
    return [row for row in rows if row.get(where[FIELD], _ABSENT) == where[EQUALS]]


#: Distinct from every value a declaration can carry, so *absent* and *declared null* stay two
#: states rather than one.
_ABSENT = object()


def rules(ctx, names: list, field: str, where=None) -> list:
    """Every row of every named source, in the order the sources were declared, with each id
    claimed exactly once. `field` is the word the source's own SCHEMA gives its rows; `where`, when
    a declaration carries one, narrows those rows to the ones it names -- and the narrowing is read
    from the row, never from a word held here."""
    names = named(ctx.enabled_capabilities(), names)
    found = sources(ctx, names)
    rows, owners = [], {}
    for name in names:
        for rule in matching(found[name][field], where):
            if rule["id"] in owners:
                raise DeclarationError(
                    f"rule {rule['id']!r} is declared by both {owners[rule['id']]!r} and "
                    f"{name!r}; two rules under one name is two homes for one judgement"
                )
            owners[rule["id"]] = name
            rows.append(rule)
    return rows
