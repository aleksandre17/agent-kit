"""A bounded artifact saying again, by hand, something a record already holds.

ADR-020 decision 4, as a reading rather than as a rule anybody keeps. A record is the one home of
what it states. A bounded steering artifact legitimately holds what no record can own -- the
governing intent, the handoff, the standing caution -- and the moment it also holds a fact a
record carries, that fact has two homes. Neither copy is wrong on the day it is written; they both
go on being internally correct while they drift, and from then on nobody can detect the
contradiction from where they stand, because each is locally right (Cardinal III).

WHAT IS READ, exactly: every part of the artifact that is NOT inside a computed span -- which is
precisely the text a principal's hand owns -- against the values the records carry in the fields
the declaration names. Nothing is inferred about sections: a computed span says where it is and a
hand-written one does not, so the reading is taken over the remainder, which needs no boundary to
be honest about.

WHY IT REPORTS AND NEVER REFUSES, and this is a design decision rather than a stage on the way to
one. The reading is a CONTAINMENT: a record's value standing inside a line somebody wrote. A
containment can be a coincidence -- a word a record happens to carry is a word a sentence may
legitimately use -- and a judgement that can be coincidentally true must never stop a write. It
must be NAMED, so that a person decides. The number of them is published as a MEASURE beside the
verdict, which is what turns *a person decides* into something with a direction: a host undertakes
a ceiling in its own map, the ratchet this kit already carries refuses any reading above it, and a
budget that has been brought to zero is what earns this judgement the right to bite (ADR-006). The
alternative -- refuse on sight -- is the gate that fires on ordinary work, and a gate that fires
on ordinary work is switched off inside a week, after which nothing is read at all.

It names no artifact, no field, no record and no section. Which fields are worth protecting from a
second home is a decision about surfaces, and it is made in the declaration.
"""

from __future__ import annotations

import collection
import declared
import derivation
import lifecycle as lifecycle_module

#: The words this judge's own declaration is written in. Its schema is their home.
OVER, SOURCES, LIST, FIELDS = "over", "sources", "list", "fields"
BECAUSE, INSTEAD = "because", "instead"


def _found(ctx, params) -> list:
    """Every line a hand wrote that carries, word for word, something a record already holds.

    ONE reading, and both the verdict and the measure stand on it. Two readings of one reality
    taken at two moments would be two numbers that each go on being correct while they disagree,
    and the surface would have no way to tell which one it was showing.
    """
    rows = declared.rules(ctx, params[SOURCES], params[LIST])
    capabilities = ctx.enabled_capabilities()
    records = lifecycle_module.the_governed(
        capabilities, collection.read_all(ctx, capabilities)).members.value
    said = []
    for rel, shape in collection.named_reading(
            ctx, params[OVER], declared.DeclarationError).records:
        artifact = shape[derivation.ARTIFACT]
        if not ctx.workspace.exists(artifact):
            # An artifact a shape describes and the tree does not carry is a fact about the
            # declaration, not about anything written in it. It is somebody else's reading to
            # take; this one would only be reporting an emptiness as a cleanliness.
            continue
        for number, field, identity in restatements(
                ctx.workspace.read_text(artifact), shape, rows, records, params[FIELDS]):
            said.append(
                f"{artifact}:{number}: this line carries {field!r} of record {identity!r} word "
                f"for word, and {rel} says the text here is written by hand. {params[BECAUSE]} "
                f"{params[INSTEAD]} Nothing was removed and nothing was rewritten: what stands "
                f"here may be the one home of something no record owns, and only a reader can "
                f"tell."
            )
    return said


def restatements(text: str, shape: dict, rows: list, records: list, fields: list) -> list:
    """(line number, field, record) for every second home this artifact holds -- the READING,
    with nothing read from the world and nothing said about what it means.

    Separated from the plumbing above on purpose. What a judge concludes and how a judge reaches
    its subject are two reasons to change, and a reading that can only be taken by standing up a
    whole host is a reading nobody can fire deliberately -- so the proof of what this gate does
    would become a proof of what a fixture does (Cardinal VIII).
    """
    found = []
    for number, line in _by_hand(text, shape, rows):
        for record in sorted(records, key=lambda r: r[collection.IDENTITY]):
            for field in fields:
                value = record.get(field)
                if isinstance(value, str) and value and value in line:
                    found.append((number, field, record[collection.IDENTITY]))
    return found


def _by_hand(text: str, shape: dict, rows: list) -> list:
    """(line number, line) for every line of the artifact a principal owns -- which is every line
    outside a computed span. The spans are found by the one passage that knows how a computed
    section is marked out; a judge that recognised the markers itself would be a second reader of
    them, and the day the marker changed one of the two would go on reading nothing and calling it
    clean."""
    inside = {row[collection.IDENTITY] for row in shape.get(derivation.SECTIONS, [])
              if derivation.computed(row, rows)}
    open_at = None
    found = []
    for number, line in enumerate(text.split("\n"), start=1):
        edge = derivation.marker_on(line)
        if edge is not None and edge[1] in inside:
            open_at = edge[1] if edge[0] == "begin" else None
            continue
        if open_at is None:
            found.append((number, line))
    return found


def _restated(ctx, params):
    """How many second homes this artifact holds -- the number, and no verdict about it. Whether
    it is too high is a ceiling, a ceiling is a number, and every number is the host's.

    `None`, never 0, where nothing was read. A host that declares no bounded artifact has not got
    zero second homes: it holds a question nobody asked, and a zero there would report an unread
    world as a clean one -- which is the reading a ceiling would then be congratulated for.
    """
    over = params.get(OVER)
    if over is None:
        return None
    try:
        reading = collection.named_reading(ctx, over, declared.DeclarationError)
    except declared.DeclarationError:
        return None
    return len(_found(ctx, params)) if reading.records else None


KINDS = {"section-restating-a-record": _found}

#: What this module can be held to a BUDGET on, published where the reading lives and discovered
#: by the same registry that finds a gate kind.
MEASURES = {"restated_record_fields": _restated}
