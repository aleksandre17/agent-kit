"""What a work record says about where it came from -- the two contradictions, and one count.

The edge itself is read next door; this module decides only what is REPORTED about it and what is
merely COUNTED, and the difference between those two is the whole adoption strategy of ADR-020
decision 5.

**Reported, because it is a contradiction in the declaration.** A record that hangs under a name
nothing answers to, and a record that is its own ancestor. Neither is a fact about the work: the
first is a typed name or a renamed record, the second is a walk with no root, and a host can fix
either by editing the record in front of it. Neither can be true of a record that hangs under
nothing, which is every record in existence on the day this ships -- so this reading is empty on
the first run by construction, and not by anybody's forbearance.

**Reported, because a declaration that points nowhere reads exactly like one that points home.**
A reference this record draws that resolved to no reading at all. What it says is what was
attempted and what came back, in the resolver's own words: a rotted reference is the one failure
that is invisible from where the reader stands, and the whole reason the referent is a typed
reference rather than a line of prose.

**Counted, and only counted.** A record that names nothing which justifies it. Every record that
exists today is one, so a gate that refused one would be switched off within a day and the state
would go back to being invisible. The number is published as a MEASURE, the host writes the
ceiling it undertakes to hold in its own map, and the ratchet this kit already carries is what
turns that number into a verdict. No second ratchet is built here, and no ceiling is named here.
"""

from __future__ import annotations

import collection
import criteria
import lineage


def _records(ctx) -> "tuple[list, list]":
    records = lineage.among(ctx)
    if records is None:
        return [], [
            "this reading was asked for where no single collection of work records can be "
            "reached: either nothing enabled here governs one, or two do. Nothing was read, so "
            "nothing is said about any record"
        ]
    return records, []


def _references_that_read_as_nothing(ctx, records: list) -> list:
    failures = []
    for record in sorted(records, key=lambda r: r[collection.IDENTITY]):
        for field, reference in lineage.references(record):
            verdict = criteria.resolve(ctx, reference, record)
            if verdict.holds is None:
                failures.append(
                    f"record {record[collection.IDENTITY]!r} draws a {field!r} reference that "
                    f"resolved to no reading at all: {verdict.reading}. A reference nobody can "
                    f"follow is indistinguishable from one that leads home, which is why it is "
                    f"said out loud here rather than left to the reader to discover"
                )
    return failures


def _lineage_resolves(ctx, params) -> list:
    """Every edge that ends in a contradiction, and every reference that reads as nothing."""
    records, unreachable = _records(ctx)
    if unreachable:
        return unreachable
    return lineage.unresolved(records) + _references_that_read_as_nothing(ctx, records)


def _without_origin(ctx, params) -> "int | None":
    """How many records name nothing that justifies them -- the number, and nothing about it.

    `None`, not 0, where the records cannot be reached: a host whose work plane was never read
    has not got zero of these, it has an unasked question, and a measure that answered 0 there
    would report a collection nobody looked at as a collection with nothing wrong in it.
    """
    records, unreachable = _records(ctx)
    return None if unreachable else len(lineage.unjustified(records))


KINDS = {"lineage-resolves": _lineage_resolves}

#: What this module can be held to a BUDGET on, published where the reading lives and discovered
#: by the same registry that finds a gate kind. The host writes this word in its own map.
MEASURES = {lineage.UNJUSTIFIED: _without_origin}

#: Which of THIS module's judgements that count is the reading of -- both words its own, one home
#: for the pairing. An undertaking at the terminal value reaches the judgement through this row,
#: and what the maturation then costs is settled where every stance is.
JUDGED_BY = {lineage.UNJUSTIFIED: "lineage-resolves"}

#: Every kind here judges by reading the governed records: none of them may prove one (ADR-025 decision 16).
READS_THE_RECORDS = {kind: True for kind in KINDS}
