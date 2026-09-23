"""Two gate kinds over the corpus READING -- the census, and the authority claims (ADR-019 7).

Neither of these resolves anything. *What is this document and how much does it bind* is answered
once, in `corpus`, and both kinds here are reports over that one answer: the first counts what the
corpus has never said about itself, the second names the claims that cannot stand. The two slices
that follow read the same resolution, which is the whole reason it does not live in either of
them (Cardinal III).

**Who states the subject.** The census states what was read -- how many documents, over how many
declared places, from how many map files -- every time it runs, because a count whose subject is
unstated is a number. The authority reading therefore does not repeat that sentence; it speaks
when it has something to say, and when its subject is ABSENT it says that instead, because a gate
that is silent over nothing reads exactly like a gate that looked (Cardinal V).

**Neither refuses the undeclared.** A corpus reaches two thousand documents before anything asks
one of them what it is; a gate that failed on the first run would be switched off within a day and
the mechanism would die at birth. So the undeclared is REPORTED, counted and named, and neither
gate returns it as a finding -- and neither ships a stance to make that safe, because a stance is
the host's declaration and a gate that needed one would be a gate that fails on a legal state
(ADR-019 amendment 1, ADR-006, ADR-001 point 4). The number that turns a count into a verdict is
the host's budget, and it arrives with the ratchet -- not here.
"""

from __future__ import annotations

import collection
import corpus

#: The front-matter field a top-authority claim must carry, and the two that state a succession.
#: The `front-matter` schema is their home; these are the ones this module reasons about.
OWNS, SUPERSEDES, SUPERSEDED_BY = corpus.OWNS, corpus.SUPERSEDES, corpus.SUPERSEDED_BY

#: The two ends of a succession, and the field each end must answer with. A succession stated at
#: one end is a document that believes it was replaced and a document that does not know it
#: replaced anything -- both locally correct, which is the condition that makes a contradiction
#: undetectable from where either stands.
COUNTERPART = {SUPERSEDES: SUPERSEDED_BY, SUPERSEDED_BY: SUPERSEDES}


def _census(ctx, params) -> list:
    """How much of this corpus has ever said what it is.

    A READING, not a judgement. What it counts it PRINTS -- the same voice `activated` and `floor`
    already speak in -- and what it RETURNS is only what is actually wrong: a word no vocabulary
    declares, a declaration that cannot be read, a place that holds nothing. An unclassified
    document is not among them. It is a declared state (ADR-019 decision 2), and a gate that failed
    on a legal state would teach every reader to ignore it inside a day -- which is the same defect
    as a gate that passes on an illegal one, arriving by the opposite road.

    Whether the unclassified COUNT is too high is a different proposition, it belongs to a budget,
    and the budget belongs to the host (ADR-006, ADR-001 point 4). The ratchet over this corpus's
    budgets is where that verdict lives; this gate produces the number it compares. That gate is
    not named here on purpose: an interpreter that spells one gate's id has privileged it, and the
    registry -- never this docstring -- is what says which gate consumes this measure.
    """
    reading = corpus.read(ctx, params)
    absent = reading.nothing_read()
    if absent:
        print(f"        {absent}")
        return []

    # The counts are the READING's, not this gate's. They were computed here once and are now
    # computed in one place, because the catalog projection states the same four numbers and two
    # comprehensions that must agree forever is the drift this whole ADR exists to prevent.
    print(
        f"        READ {reading.subject()}. {len(reading.spoke)} declared their own class or "
        f"authority; {len(reading.undeclared)} declared nothing and are UNCLASSIFIED -- of those, "
        f"{len(reading.conferred)} are classed by the place they reside in and the rest by nothing "
        f"at all. UNCLASSIFIED is a state, not a failure: nothing here is moved, deleted or "
        f"guessed at. The unclassified are counted and not named one by one -- naming them is the "
        f"catalog projection's work, and it states them by place on every render."
    )
    findings = []
    for resident in reading.residents:
        if resident.unreadable:
            findings.append(
                f"{resident.path}: UNREADABLE -- {resident.unreadable}. It is named rather than "
                f"skipped: a document whose declaration cannot be read has not declared nothing, "
                f"and counting it as either would be a reading nobody took."
            )
    for resident in reading.residents:
        declared_class, source = reading.class_of(resident)
        if declared_class is not None and declared_class not in reading.classes:
            findings.append(
                f"{resident.path}: it is classed {declared_class!r} by {source}, and no row of the "
                f"class vocabulary declares that word. A class nobody declares appears in no "
                f"section of any catalog, which is how a corpus acquires a part nobody reads."
            )
    for place in reading.missing_places:
        findings.append(
            f"{place[corpus.PATH]}: a place is declared here and nothing resides at that path. A "
            f"map that names a place the tree does not have is a statement about a corpus that "
            f"does not exist; nothing was read for it."
        )
    return findings


def _claims(ctx, params) -> list:
    """Every authority this corpus claims, held to what a claim must carry.

    An absence is PRINTED and never returned, for the same reason the census prints its reading: a
    host that has mapped nothing cannot hold two owners of one topic or a claim above a ceiling, so
    there is nothing here to refuse. A gate that failed on that would fail every fresh install on
    the day the capability shipped -- and a gate that fails where nothing is wrong is a gate that
    gets switched off, which costs more than the gate was ever worth (ADR-019 amendment 1).
    """
    reading = corpus.read(ctx, params)
    absent = reading.nothing_read()
    if absent:
        print(f"        {absent}")
        return []

    findings: list = []
    owners: dict = {}
    residents = {resident.path: resident for resident in reading.residents}

    for resident in reading.residents:
        claimed, source = reading.authority_of(resident)
        if claimed is not None:
            findings.extend(_authority(reading, resident, claimed, source, owners))
        findings.extend(_succession(ctx, resident, residents))

    for owned, claimants in sorted(owners.items()):
        if len(claimants) > 1:
            findings.append(
                f"{', '.join(sorted(claimants))}: {len(claimants)} artifacts claim the authority no "
                f"place may confer over the same topic {owned!r}. One fact has one owner: two "
                f"settled answers to one question are not a tie, they are a corpus that will "
                f"answer it differently depending on which document a reader reached first."
            )
    return findings


def _authority(reading, resident, claimed, source, owners) -> list:
    row = reading.authorities.get(claimed)
    if row is None:
        return [
            f"{resident.path}: it declares the authority {claimed!r} in {source}, and no row of "
            f"the authority vocabulary declares that word. An authority nobody declared cannot be "
            f"compared with any other, so what this document binds is not readable at all."
        ]
    if reading.is_the_most_binding(row):
        if not resident.declares(OWNS):
            return [
                f"{resident.path}: it claims {claimed!r} -- the most binding state there is -- "
                f"and names no {OWNS!r}. A settled answer that does not say what question it "
                f"settles cannot be checked against a second one, and the duplicate-owner refusal "
                f"is the only thing standing between this corpus and two of them."
            ]
        for topic in corpus.listed(resident.declares(OWNS)):
            owners.setdefault(topic, []).append(resident.path)

    ceiling = reading.ceiling_of(resident)
    if row[corpus.RANK] > ceiling[corpus.RANK]:
        return [
            f"{resident.path}: it declares {claimed!r}, which binds more than "
            f"{ceiling[collection.IDENTITY]!r} -- "
            f"the ceiling its place {resident.place[corpus.PATH]!r} declares. A place may LOWER a "
            f"claim and may never RAISE one, and the cap has no exception at the top: a document "
            f"claiming more than its place permits is either in the wrong place or making the "
            f"wrong claim, and which one it is a person decides (ADR-019 amendment 1)."
        ]
    return []


def _succession(ctx, resident, residents) -> list:
    findings = []
    for stated, answering in COUNTERPART.items():
        for named in corpus.listed(resident.declares(stated)):
            rel = corpus.resolved(ctx, named)
            if rel is None or not ctx.workspace.exists(rel):
                findings.append(
                    f"{resident.path}: its {stated!r} names {named!r}, which is not a document of "
                    f"this host. A succession that points at nothing leaves a reader who arrived "
                    f"at this text with no way on, and it reads exactly like a succession that was "
                    f"kept."
                )
                continue
            other = residents.get(rel)
            if other is None:
                findings.append(
                    f"{resident.path}: its {stated!r} names {named!r}, which resides in no declared "
                    f"place, so the other end of the succession cannot be read. Stated at one end "
                    f"as far as this reading reaches -- map the place, or the pair stays unverified."
                )
                continue
            if resident.path not in corpus.listed(other.declares(answering)):
                findings.append(
                    f"{resident.path}: its {stated!r} names {named!r}, and that document does not "
                    f"answer with {answering!r}. A succession stated at one end leaves both "
                    f"documents internally correct and the pair contradictory -- which is the "
                    f"state no reader can detect from where they stand."
                )
    return findings


def _unclassified(ctx, params) -> "int | None":
    """How many documents have never said what they are -- the number, and nothing about it.

    A MEASURE, which is a count offered to whoever has a ceiling for it; the census above prints
    the same number and returns no verdict on it, and both read it off the one reading rather than
    counting twice. `None` where nothing was read: a host with no map has not got zero unclassified
    documents, and a measure that answered 0 there would report a clean corpus nobody looked at.
    """
    reading = corpus.read(ctx, params)
    return None if reading.nothing_read() else len(reading.undeclared)


#: What this module PROVIDES. Two kinds, one reading: a new question about the same corpus is a
#: row here and a function beside these -- never a second resolution of what a document is.
KINDS = {
    "artifact-classified": _census,
    "authority-declared": _claims,
}

#: What this module can be held to a BUDGET on (ADR-019 decision 9). Declared here, in the module
#: that owns the reading it comes from, and discovered by the same registry that finds a gate kind
#: -- so the ratchet spells no measure of its own and a new budgetable fact is a row beside this
#: one. The name is the word a host writes in its map, and it is the ADR's own spelling.
MEASURES = {"unclassified_documents": _unclassified}
