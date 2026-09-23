"""Cooling -- a span leaves the POSITION and lands in the RECORD its own section declares.

ADR-020 decision 3. S1 made the destructive act impossible to perform silently: what a write
removes is journalled before the artifact is replaced, and a removal that was curated nowhere is
preserved and counted. This module is the other half -- it gives a removed span somewhere to GO --
and it is ONE passage:

    evict this span  ->  land it at the destination its SECTION declares  ->  journal both halves

It knows no section name, no artifact, no path and no destination. All four arrive as data: the
shape declaration (`position-shape`) states, per section, the record KIND its cold spans belong to,
and this passage reads that row and carries the span there. A new section is a ROW; a new
destination is a ROW; neither is an edit here, and there is no place in this module where a
particular section could be special-cased even by accident -- the only thing it ever asks of a
declaration is *what does your section say*, never *which section is it*.

THE ORDER IS THE PRODUCT, and it is one stage longer than S1's:

    the span is LANDED  ->  the landing is JOURNALLED  ->  and only then is the artifact replaced

Each stage is ahead of the one that destroys, so every possible interruption leaves the text
preserved MORE times and never fewer: a landing that fails leaves the artifact whole and the
journal untouched; a journal append that fails leaves the artifact whole and the text already at
its destination (S1 refuses the write); a write that fails leaves the text in all three places.
The inverse order -- journal a landing, then perform it -- would let the record claim a home the
text never reached, which is a surface stating something that was not observed (Cardinal V). The
duplicate a failure can leave is the cost of that guarantee and is paid deliberately: a reader who
finds a span twice has a question, and a reader who finds it nowhere has nothing.

Three things it refuses to decide, because each belongs to somebody else:

  * WHERE A KIND LIVES. `cools_to` is a WORD from the record-keeping vocabulary, and which paths
    hold records of that kind is the corpus map's answer, not an interpreter's. The carrying is a
    port -- `land` -- handed in by the caller, exactly as the journal and the artifact are.
  * WHETHER THE DESTINATION IS A DECLARED KIND. That is a property of the declaration and is
    judged statically, over the whole host, by the gate that reads the shape against the
    vocabulary -- which is deliberately not named here: an interpreter that spells one gate's id
    has privileged it, and the registry is what says which gate reads this declaration. A passage
    that re-checked the vocabulary would be a second reading of it at a different moment, and the
    two would disagree the day one of them was fixed.
  * WHETHER A SPAN SHOULD HAVE COOLED AT ALL. Cooling is a curated act the caller chooses; the
    ordinary editorial cut still goes through `eviction.accept` with no landing, is counted, and
    is never refused. A mechanism that made every removal a curation would be switched off within
    a week, and then nothing would be preserved at all.

What it DOES refuse is a guess. A span whose section declares no destination -- or whose section
the shape does not declare -- is not carried anywhere: the refusal names the artifact, the section
and the words the declaration actually offers, and the caller may still remove the text through
`eviction.accept`, where it is preserved and counted as unlanded. That is the whole difference
between this and the measured failure it answers: under pressure, a destination invented in the
moment is how true history ends up somewhere nobody will ever read it.
"""

from __future__ import annotations

import collection
import eviction
from errors import KitError

#: The kit schema that is the ONE home of a shape declaration's form; these are the fields this
#: passage resolves from it, and nothing else in this module reads that document.
SCHEMA = "position-shape"

#: The shape declaration's own field names. The schema is their home -- spelled here because an
#: interpreter of a declaration must name the parts it reads, and nowhere else.
SECTIONS, ARTIFACT, COOLS_TO = "sections", "artifact", "cools_to"


class NowhereToCool(KitError):
    """A span was told to cool and its section declares no destination, so nothing was moved.

    The refusal IS the mechanism. The alternative -- pick a plausible home -- is an interpreter
    deciding policy under exactly the pressure that produced every deletion this link exists
    against, and a span filed where nobody expects it is lost in the one way that also looks
    tidy."""

    code = "KIT0058"


class LandingUnaddressed(KitError):
    """The span was carried somewhere the caller cannot state an address for, so nothing is
    journalled.

    A landing is a reference a later reader FOLLOWS. A record kind with no address is a claim that
    the text is somewhere, which is exactly as useful as a digest: it proves a move happened and
    returns nothing."""

    code = "KIT0059"


def section_of(shape: dict, section: str) -> "dict | None":
    """The row this shape declares for one section, or `None` where it declares none.

    `None` is not an error here: a shape that has not been declared yet, or that has grown a
    section nobody has described, is a LEGAL state and the whole of what this function reports.
    What to do about it is the caller's question, and `cool` answers it one way while an ordinary
    write answers it another.
    """
    for row in shape.get(SECTIONS, []):
        if row.get(collection.IDENTITY) == section:
            return row
    return None


def destination(shape: dict, section: str) -> "str | None":
    """The record KIND a cold span of one section belongs to, or `None` where the declaration
    names none -- whether because the section is undeclared or because it declares that nothing
    here cools. Both are honest states and neither is defaulted."""
    row = section_of(shape, section)
    return None if row is None else row.get(COOLS_TO)


def cool(ctx, *, shape: dict, section: str, prior: str, candidate: str, land, append, write,
         at: str, rev: int = None, runtime: str = None) -> "dict | None":
    """One curated write: the span this write removes is carried to the destination its section
    declares, and the move is journalled before the artifact is replaced.

    Returns the journalled event, or `None` when the write removes nothing -- and in that case the
    write still HAPPENS. A candidate that only adds has cooled nothing, so no destination is
    consulted and none is demanded: a passage that refused a pure addition would be firing on
    ordinary work, and one that returned early without writing would be reporting a write it never
    performed. There is exactly one exit, and every write leaves through S1's `accept`.

    `land` is a port: any callable `land(destination, spans) -> address` that durably carries the
    text to a record of that KIND and returns the address a reader can follow. It is given the
    word and the prose and nothing else -- no path is computed here, and a `land` that raises
    leaves the artifact untouched and the journal empty.

    `append` and `write` are S1's ports, unchanged and used through `eviction.accept`, so the
    ordering guarantee this passage adds sits ON TOP of that one and never beside it: there is no
    second journal, no second event shape and no second way to replace an artifact.
    """
    artifact = shape[ARTIFACT]
    removed = eviction.spans(prior, candidate)
    cools_to = destination(shape, section) if removed else None
    if removed and cools_to is None:
        declared = [row.get(collection.IDENTITY) for row in shape.get(SECTIONS, [])
                    if row.get(COOLS_TO) is not None]
        known = section_of(shape, section) is not None
        raise NowhereToCool(
            f"NOTHING WAS MOVED AND {artifact!r} IS UNCHANGED: "
            + (f"section {section!r} of it declares no {COOLS_TO!r}, so there is no record kind "
               f"this span belongs to"
               if known else
               f"its shape declares no section named {section!r}, so nothing states where a span "
               f"of it belongs")
            + f". The sections that do declare a destination are {declared or 'none'}. This span "
              f"is not filed by guess: a destination invented at the moment of pressure is how "
              f"true history lands where nobody will look for it. Declare {COOLS_TO!r} on the "
              f"section and cool again -- or remove the text through the ordinary write, where it "
              f"is preserved in the journal and counted as an unlanded removal."
        )

    landing = None
    if removed:
        landing = eviction.landing(cools_to, _addressed(land(cools_to, removed), cools_to,
                                                       artifact, removed))

    return eviction.accept(
        ctx, prior=prior, candidate=candidate, append=append, write=write, at=at,
        artifact=artifact, section=section, rev=rev, runtime=runtime, landing=landing)


def _addressed(address, cools_to: str, artifact: str, removed: list) -> str:
    """The address a landing came back with, or a refusal. Read here rather than trusted, because
    the one thing a landing is FOR is being followed."""
    if not isinstance(address, str) or not address.strip():
        raise LandingUnaddressed(
            f"THE WRITE IS REFUSED AND {artifact!r} IS UNCHANGED: {sum(len(s) for s in removed)} "
            f"character(s) were carried to a record of kind {cools_to!r} and no address came back, "
            f"so the event would say the text is somewhere without saying where. A landing nobody "
            f"can follow is a landing nobody can find, and it would be counted as a MOVE while "
            f"being indistinguishable from a loss. Nothing was journalled; whether the carrying "
            f"itself happened is the port's to report, and it is not assumed here either way."
        )
    return address
