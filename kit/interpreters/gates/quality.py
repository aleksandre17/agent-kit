"""A gate kind for records that POINT at something a host declared.

A record may be perfectly well-formed and still be about nothing. A judgement can name a case that
was renamed last week, a rubric that was never written, a judge nobody put on the roster -- and
from the record's own side all three read exactly like a case that passed. That is the failure this
kind exists for: not an invalid document, but a valid one whose referent is gone.

It knows no field and no list. Which fields point where arrives as data: each reference names the
field on the record, the readable the referents live in and the list inside it, and carries its own
reason and its own calibration. A reference nobody declared is not measured, and a reference
declared here is measured whatever it happens to be about.

Two refusals shape it:

  * **An ABSENT field is not a dangling reference.** A judgement that has not been judged names no
    judge, and it must not: absence is a declared state, and a sensor that read it as a violation
    would report every honest blank as a defect and teach a host to stop looking.
  * **A referent set that is EMPTY is not a licence.** A host that has declared no case has a zero
    measure, and a judgement about a case on a host with no cases is exactly as dangling as one on
    a host with a hundred. The empty set is the strictest set, not the most permissive.

It reports and never repairs. A judgement is evidence; nothing here writes, and no port that could
write is reachable from it.
"""

from __future__ import annotations

from functools import partial

import collection
import declared

#: What a reference declaration calls the parts of itself. Schema vocabulary of this kind's own
#: params -- the contract between the declaration that configures this gate and this gate.
FIELD, AMONG, SOURCE, LIST = "field", "among", "source", "list"


def _readable(ctx, name: str):
    """The readable a name resolves to, through the one door that turns an install into a value.
    A gate that opened the path itself would be deciding the shape of somebody else's
    declaration."""
    readings = collection.read_all(ctx, ctx.enabled_capabilities())
    if name not in readings:
        raise declared.DeclarationError(
            f"this gate was declared over a readable named {name!r}, which no enabled capability "
            f"declares; the names declared are {sorted(readings)}"
        )
    return readings[name]


def _referents(ctx, among: dict) -> set:
    """Every identity the host declared in one named list of one named readable."""
    document = _readable(ctx, among[SOURCE]).value
    if among[LIST] not in document:
        raise declared.DeclarationError(
            f"this gate was declared over a list named {among[LIST]!r} in {among[SOURCE]!r}, "
            f"which that document does not carry; it carries {sorted(document)}"
        )
    return {row[collection.IDENTITY] for row in document[among[LIST]]}


#: The other word a reference may use to say where its referents live. Schema vocabulary of this
#: kind's own params, exactly as `source` is -- one home each, and never both on one reference.
SOURCES = "sources"

#: And the word by which a reference says its referents are a SUBSET of that list -- the rows the
#: vocabulary itself marks. Optional, one field and one value, and read where the rows are resolved
#: (`declared.matching`): a subset stated as data is a declaration, and the alternative was a gate
#: module per subset, each holding in Python a rule a row already states.
WHERE = "where"


def _referents_across(ctx, among: dict) -> set:
    """Every identity declared in one named list ACROSS several named sources.

    The same question as `_referents` and a different reach, which is why it is a second function
    and not a branch inside the first. A referent set that spans sources is the ordinary case the
    moment a thing can be declared by the KIT or by the HOST -- an archetype, a policy, a kind --
    and a gate able to look in only one of the two places would report a perfectly well-founded
    reference as dangling, which is the most expensive kind of false finding: it teaches a host
    that the sensor is wrong, and after that it teaches nothing at all.

    The merge is `declared.rules`, unchanged: it already refuses an id declared twice, which is
    the failure a multi-source referent set brings with it.
    """
    return {row[collection.IDENTITY]
            for row in declared.rules(ctx, among[SOURCES], among[LIST], among.get(WHERE))}


#: The word a reference uses to say that the field it reads holds MANY pointers rather than one,
#: and which sub-field of each row carries the name. Schema vocabulary of this kind's own params,
#: exactly as `field` is -- and a declared DEPTH rather than a second gate kind, because how deep
#: a name sits is a property of the record's shape and not a different question: the scan, the
#: calibration and every word of the report are identical either way. A branch in the machinery
#: would have made the depth an interpreter's opinion about somebody else's record.
EACH = "each"


def _named(record: dict, reference: dict) -> list:
    """Every referent this record NAMES through one reference -- none, one, or one per row of a
    list-valued field. A field the record does not carry names nothing, and a row that does not
    carry the sub-field names nothing: an absence is a state, and only a claim can be false."""
    held = record.get(reference[FIELD])
    if held is None:
        return []
    if EACH in reference:
        return [row[reference[EACH]] for row in held
                if isinstance(row, dict) and reference[EACH] in row]
    return [held]


def _dangling(record: dict, reference: dict, referents: set) -> list:
    """The referents this record names that the host declares nowhere. Empty is the ordinary
    answer and is not a judgement: a record that names nothing has nothing to be wrong about."""
    return [name for name in _named(record, reference) if name not in referents]


def _calibration(ctx, references: list, referents_of) -> list:
    """What the sensor can prove about itself, before it is pointed at anything. Each reference
    declares one record it MUST flag and one it MUST admit, and both are read through exactly the
    machinery that will read the host's."""
    failures = []
    for reference in references:
        referents = referents_of(ctx, reference[AMONG])
        if not _dangling(reference["proves"], reference, referents):
            failures.append(
                f"{reference['id']}: UNCALIBRATED -- it does not flag the record it declares it "
                f"catches. A sensor that cannot prove what it sees is not evidence, and nothing "
                f"was scanned on its word."
            )
        if _dangling(reference["admits"], reference, referents):
            failures.append(
                f"{reference['id']}: UNCALIBRATED -- it also flags the record it declares "
                f"legitimate. A rule with no measured edge eventually names everything, and "
                f"nothing was scanned on its word."
            )
    return failures


def _reference_declared(ctx, params, referents_of) -> list:
    references = params["references"]
    uncalibrated = _calibration(ctx, references, referents_of)
    if uncalibrated:
        return uncalibrated
    referents = {reference["id"]: referents_of(ctx, reference[AMONG]) for reference in references}
    failures = []
    for rel, record in _readable(ctx, params["over"]).records:
        for reference in references:
            for name in _dangling(record, reference, referents[reference["id"]]):
                failures.append(
                    f"{rel}: {reference['id']} -- it names {name!r}, which "
                    f"this host does not declare. {reference['because']} {reference['instead']} "
                    f"Nothing was removed: this names a record, and clearing it is yours."
                )
    return failures


#: What this module PROVIDES: two ways of asking one question -- does this record point at
#: something a host declares -- differing only in WHERE the referents are looked for. The scan,
#: the calibration and every word of the report are the same code; the reach is a strategy handed
#: in, never a branch, because the day a third place to declare a referent arrives the machinery
#: must not change. A new way of reading a record is a row here and a function beside these,
#: never an edit to the verb that runs the gates.
KINDS = {
    "reference-declared": partial(_reference_declared, referents_of=_referents),
    "reference-declared-across": partial(_reference_declared, referents_of=_referents_across),
}
