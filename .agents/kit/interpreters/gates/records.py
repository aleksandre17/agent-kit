"""Gate kinds for the records this kit keeps -- a record that says something is wrong about itself.

Two kinds are provided and they are one scan: a run's own receipt, and a judgement of a case
against a rubric, are both collections of records read against declared dispositions. What differs
is only what a READING may carry, which is handed in as a strategy.


This module knows no disposition. It knows the SHAPE of a dispositions document -- a list of rows,
each carrying one match and its own calibration -- and nothing about what any of them say. Which
documents it reads and which readable it reads them OVER arrive as params.

It reports and never removes, and here that posture is sharper than it was for residence: a run's
record is EVIDENCE, and evidence is not swept up by the thing being questioned. Enforced by
omission -- no write, no port that could write, no branch that could reach one.

It refuses to scan on the word of an uncalibrated sensor. Every disposition states one record it
MUST match and one lookalike it MUST tolerate; both are checked before a single record is read,
and a disposition that fails either is itself the failure. The calibration is run through exactly
the same reading path as the real scan, so a specimen is judged by the machinery that will judge
the host -- a calibration that took a shortcut would prove a sensor nobody is going to use.

The one thing this gate knows that no declaration could tell it: whether the run holding a record
is the run now reading it. A run cannot judge its own liveness. Its record is legitimately open
because it has not finished, and a sensor unable to tell that from a corpse would report every
healthy run as one. That fact is added to the READING, as a field a disposition may name, so the
exclusion is declared and visible rather than an exemption hidden in the machine -- and so a host
that wants to be stricter can be, without an interpreter edit.
"""

from __future__ import annotations

from functools import partial

import collection
import declared
import predicate

#: The field by which a dispositions document carries its rows. Schema vocabulary, one home.
RULES = "dispositions"

#: The one thing the reader knows and the record does not. Declared by the schema that governs a
#: disposition's `when`, which is what entitles this module to spell it: it is the contract
#: between a declaration and its reader, and not a word some instance invented.
IN_FLIGHT = "in_flight"


def _as_found(ctx, record: dict) -> dict:
    """A record as it was found, and nothing else. The ordinary case: what a document SAYS is the
    whole of what a reader may say about it, and a reading that quietly added a field would be the
    machine putting a word into a declaration's mouth."""
    return dict(record)


def _with_liveness(ctx, record: dict) -> dict:
    """A record as the sensor reads it, at the moment of reading: what the record SAYS, plus the
    one thing only the running process can know. A reading, never a rewrite -- nothing here
    reaches the record on disk."""
    reading = dict(record)
    #: A record found on disk can never carry this field -- the schema that governs a receipt
    #: closes itself to properties it did not declare, so a planted file cannot claim to be alive
    #: and walk past the sensor. A declared SPECIMEN can, and must: a calibration states the whole
    #: reading it is measured on, including the half no document could ever hold.
    reading.setdefault(IN_FLIGHT, record.get(collection.IDENTITY) in ctx.in_flight)
    return reading


def _calibration(ctx, rules: list, reading_of) -> list:
    """What the sensor can prove about itself, before it is pointed at anything. The specimens are
    read through the SAME reading the real scan uses -- a calibration that took a shortcut would
    prove a sensor nobody is going to use."""
    failures = []
    for rule in rules:
        if not predicate.matches(rule["when"], reading_of(ctx, rule["proves"])):
            failures.append(
                f"{rule['id']}: UNCALIBRATED -- it does not match the record it declares it "
                f"catches. A sensor that cannot prove what it sees is not evidence, and nothing "
                f"was scanned on its word."
            )
        if predicate.matches(rule["when"], reading_of(ctx, rule["admits"])):
            failures.append(
                f"{rule['id']}: UNCALIBRATED -- it also matches the record it declares "
                f"legitimate. A rule with no measured edge eventually names everything, and "
                f"nothing was scanned on its word."
            )
    return failures


def _over(ctx, name: str):
    """The readable these dispositions are read over, resolved through the one door that turns an
    install into a value. A gate that opened the path itself would be deciding the shape of
    somebody else's declaration. The resolution has one home and this is not it -- it stood here
    and, character for character, beside another judge as well."""
    return collection.named_reading(ctx, name, declared.DeclarationError)


def _scan(ctx, params, reading_of) -> list:
    """Every declared reading, applied to every record of one declared readable. The only thing
    that varies between the kinds below is HOW a record is read -- which is a strategy handed in,
    never a branch, because the day a second kind of record arrives the machinery must not
    change."""
    rules = declared.rules(ctx, params["sources"], RULES)
    uncalibrated = _calibration(ctx, rules, reading_of)
    if uncalibrated:
        return uncalibrated
    failures = []
    for rel, record in _over(ctx, params["over"]).records:
        reading = reading_of(ctx, record)
        for rule in rules:
            if predicate.matches(rule["when"], reading):
                failures.append(
                    f"{rel}: {rule['id']} -- {rule['because']} {rule['instead']} "
                    f"Nothing was removed: this names a record, and clearing it is yours."
                )
    return failures


#: What this module PROVIDES: two ways of reading a collection of records against declared
#: dispositions, differing in one thing only -- whether the reading may carry the half no document
#: can hold. `record-disposition` is the general one and is what a new kind of record gets;
#: `run-disposition` is the same scan over a reading that also knows whether the run holding the
#: record is the run doing the reading. A third would be another row, and nothing that dispatches
#: to it is ever edited.
KINDS = {
    "record-disposition": partial(_scan, reading_of=_as_found),
    "run-disposition": partial(_scan, reading_of=_with_liveness),
}
