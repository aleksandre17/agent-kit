"""A section of a bounded artifact whose content is COMPUTED, filled from the records that own it.

ADR-020 decision 4. The shape declaration already states, per section, where its content comes
from; S2 landed the word and this is what makes the word MEAN something. A section whose source
carries the machine fact *this is derived* holds no truth of its own: delete its content, run this
passage, and it comes back character for character. A hand that writes there is writing a second
home for a fact somebody else owns, and the next run replaces what it wrote without reading it.

That sentence is the whole cure. Synchronisation by discipline is not a mechanism: two copies of
one truth both stay internally correct while the system speaks with confidence and lies, and the
copy is removed rather than kept in step (Cardinal III). What this module removes is the copy.

It knows no section, no artifact, no path, no record and no field. Four things arrive as data and
there is no fifth:

  * the SHAPE, which says what sections there are and which of them is computed from what;
  * the VOCABULARY rows, which carry the machine fact that tells a computed provenance from a
    hand-written one -- read as a FACT and never by recognising a word, because an interpreter
    that recognised one would have privileged a row of somebody else's declaration, and the third
    provenance to be declared would need this file's permission to exist;
  * the VIEW this host's declarations already compute, which carries the rows;
  * the ARTIFACT's current text.

Three things it refuses to decide:

  * WHERE IN THE ARTIFACT A SECTION STANDS. The artifact names the place, twice, with a pair of
    markers this passage rewrites in canonical form but never invents. A passage that appended a
    section it could not find would be choosing the shape of somebody's steering surface under
    exactly the pressure that makes a bad place look like a fine one -- and the mistake would be
    invisible, because the content would be correct and only its position wrong. Absent markers
    are a refusal that names the two lines to write; two pairs are a refusal too, because a name
    that resolves to two spans is not a name.
  * WHAT A LINE LOOKS LIKE. The declaration carries the line, in the logic-less template grammar
    every other projection is written in, so the fields a surface repeats are chosen where
    surfaces are chosen. No field name is spelled here and none ever will be.
  * WHETHER THERE BEING NOTHING IS WORTH SAYING. It always is, and the words are the host's: an
    empty computation that fell silent is indistinguishable from one that never ran, and a reader
    cannot tell a declared nothing from a broken something by looking at a blank (Cardinal V).

It also refuses to touch a section a hand owns. Not by care, and not by a rule anybody keeps: the
only text this passage can address is the span between two markers of a section whose provenance
carries the computed fact, so a section owned by a principal is not *protected* here, it is
unreachable. Every write leaves through S1's one writer, so a replacement is journalled before the
artifact is replaced and this passage adds no second way to write a bounded artifact.
"""

from __future__ import annotations

import re

import collection
import eviction
import template
from errors import KitError

#: The kit schema that is the ONE home of a shape declaration's form, and the fields this passage
#: resolves from it. Spelled here because an interpreter of a declaration must name the parts it
#: reads -- and nowhere else.
SCHEMA = "position-shape"
SECTIONS, ARTIFACT, SOURCE = "sections", "artifact", "source"
PROJECTS, OVER, LINE, EMPTY = "projects", "over", "line", "empty"

#: The machine fact a provenance row carries, whose home is the record-keeping schema. Read as a
#: fact, never as a word: this module can be handed a vocabulary written in a language it has
#: never seen and still tell the two kinds of section apart.
DERIVED = "derived"

#: The two lines that say WHERE a computed section stands. Their sentence has one home -- here --
#: so a marker cannot drift into two spellings that each go on matching from where they stand. The
#: opening line carries its own warning, because the one reader who needs it is the one about to
#: type into a span that will be replaced unread, and a warning in a manual reaches nobody.
OPENS = ("<!-- kit:begin {id} -- computed from this host's declaration; anything written between "
         "these two lines is replaced unread -->")
CLOSES = "<!-- kit:end {id} -->"

#: How a marker is RECOGNISED, as opposed to how it is written. Deliberately looser than what is
#: emitted: a host writes the pair by hand the first time, the identifier is what carries meaning,
#: and a passage that demanded its own punctuation back would refuse a correct declaration over a
#: space. What is written is always canonical, so the tolerance never compounds (Cardinal VII: the
#: boundary is measured, and a value that crosses it is carried in a form both sides read alike).
_MARKER = re.compile(r"^\s*<!--\s*kit:(?P<edge>begin|end)\s+(?P<id>\S+)(?P<rest>.*?)-->\s*$")


class NoSpanToFill(KitError):
    """A computation was asked for a section that has no span: either the shape does not declare
    that section computed from anything, or the artifact does not mark out where it stands. One
    refusal, because it is one state -- there is no text this passage may address -- and one cure:
    say which section is computed, and mark out where it belongs."""

    code = "KIT0063"


class SectionPlacedTwice(KitError):
    """One section is marked out in two places, so the computation has two homes in one file."""

    code = "KIT0064"


class NothingToProjectFrom(KitError):
    """A computed section names rows this host's declarations do not compute."""

    code = "KIT0065"


def _fact(sources: list) -> dict:
    """The machine fact each provenance carries, by the word it is written in."""
    return {row[collection.IDENTITY]: row.get(DERIVED) for row in sources or []}


def computed(row: dict, sources: list) -> bool:
    """Whether this section's content is computed from a declaration elsewhere.

    A provenance this vocabulary does not carry answers NO, and that is the safe direction rather
    than a default: the question being asked is *may this text be replaced unread*, an unreadable
    answer is not a yes, and a section whose provenance nobody can resolve is text somebody may
    have written by hand. The declaration naming a provenance that does not exist is a defect --
    it is REPORTED where defects in declarations are reported, statically, over the whole host, by
    the judge that reads shapes against the vocabulary. It is not re-decided here at a different
    moment, because two readings of one reality taken at two moments is how a contradiction
    becomes survivable instead of detectable (Cardinal III).
    """
    return _fact(sources).get(row.get(SOURCE)) is True


def computable(shape: dict, sources: list) -> list:
    """Every section of this shape that this passage can fill, in declared order.

    A computed section that says nothing about what it is computed FROM is passed over in silence
    and is not an error here. It is an incomplete declaration, and an incomplete declaration is
    judged where declarations are judged; a passage that refused it would be a second judge, firing
    at a different moment, on the same fact. Nothing is at risk either way -- unlike a span with
    nowhere to cool, skipping this one loses nothing at all.
    """
    return [row for row in shape.get(SECTIONS, [])
            if computed(row, sources) and row.get(PROJECTS)]


def body(row: dict, view: dict) -> str:
    """What one computed section says, rendered from the rows its declaration names.

    The iteration happens INSIDE the renderer, deliberately. The rule that a field only some
    records carry is OPTIONAL rather than missing is a property of the renderer's own scope --
    while a list is iterated, the union of its records' keys is the vocabulary in scope -- so a
    loop written here in Python would be a second iteration semantics, and a line that rendered
    under one and was refused by the other would be correct in whichever place you happened to be
    standing. The wrapper is built from the name the DECLARATION gives; nothing here names
    anything.
    """
    spec = row[PROJECTS]
    name = spec[OVER]
    rows = view.get(name)
    if not isinstance(rows, list):
        raise NothingToProjectFrom(
            f"section {row.get(collection.IDENTITY)!r} is one line per {name!r}, and this host "
            f"computes no rows under that name"
            + (f"; it carries {name!r} as {type(rows).__name__}, which is not a set of anything"
               if rows is not None else
               f". The names this host computes are {sorted(view)}")
            + ". Nothing was rendered and the artifact is untouched: a surface built on a name "
              "that resolves to nothing would be showing an emptiness nobody declared"
        )
    if not rows:
        return spec[EMPTY]
    return template.render("{{#" + name + "}}" + spec[LINE] + "{{/" + name + "}}", {name: rows})


def _placed(lines: list, identity: str) -> tuple:
    """Where this section's markers stand, as the two line numbers between which its content is
    this passage's to replace. Neither number is guessed and neither is defaulted."""
    opens = [i for i, line in enumerate(lines) if marker_on(line) == ("begin", identity)]
    closes = [i for i, line in enumerate(lines) if marker_on(line) == ("end", identity)]
    if len(opens) > 1 or len(closes) > 1:
        raise SectionPlacedTwice(
            f"section {identity!r} is marked out {max(len(opens), len(closes))} times in this "
            f"artifact, so there is no single span its content belongs in. Nothing was written. A "
            f"name that resolves to two spans is not a name, and filling both would put one fact "
            f"in two places inside the one file this whole mechanism exists to keep single"
        )
    if not opens or not closes or closes[0] < opens[0]:
        raise NoSpanToFill(
            f"NOTHING WAS WRITTEN AND THIS ARTIFACT IS UNCHANGED: it is declared to carry a "
            f"computed section {identity!r}, and it does not say where that section stands"
            + (" -- its two markers are present in the wrong order, so they mark out no span"
               if opens and closes else "")
            + ". The place is not guessed: a computation appended wherever there was room would be "
              "correct in its content and wrong in its position, which is the one kind of wrong a "
              "reader does not notice. Put these two lines where the section belongs and run "
              f"again:\n  {OPENS.format(id=identity)}\n  {CLOSES.format(id=identity)}"
        )
    return opens[0], closes[0]


def marker_on(line: str) -> "tuple | None":
    """Which edge of which section's span this line is, or `None` where it is ordinary text.

    Public, and it is the only way anything learns that a line is a marker. A second reader of
    this punctuation -- a judge matching the same two lines for itself -- would be a second answer
    to *where does a computed span begin*, and the day the marker changed, one of the two would go
    on finding nothing and calling the artifact clean (Cardinal III).
    """
    found = _MARKER.match(line)
    return None if found is None else (found.group("edge"), found.group("id"))


def filled(text: str, *, shape: dict, sources: list, section: str, view: dict) -> str:
    """The artifact, with one computed section's span replaced by what the records say.

    Everything outside the two markers is returned exactly as it arrived, byte for byte. That is
    not restraint: it is the only text this function can address.
    """
    row = next((r for r in shape.get(SECTIONS, [])
                if r.get(collection.IDENTITY) == section), None)
    if row is None or not computed(row, sources) or not row.get(PROJECTS):
        raise NoSpanToFill(
            f"NOTHING WAS WRITTEN: this shape declares no section {section!r} whose content is "
            f"computed from anything. The sections it can fill are "
            f"{[r.get(collection.IDENTITY) for r in computable(shape, sources)] or 'none'}. A "
            f"section whose provenance says a principal owns it is not filled by refusal here -- "
            f"it is simply not something this passage can address, and nothing it holds is touched"
        )
    lines = text.split("\n")
    first, last = _placed(lines, section)
    written = body(row, view)
    # One trailing newline is absorbed rather than rendered as a blank line: a declaration whose
    # line ends in a break and one whose line does not must both produce a span that reads back
    # identically, or the second run of this passage would differ from the first over a character
    # nobody wrote.
    written = written[:-1] if written.endswith("\n") else written
    block = [OPENS.format(id=section)] + written.split("\n") + [CLOSES.format(id=section)]
    return "\n".join(lines[:first] + block + lines[last + 1:])


def refresh(ctx, *, shape: dict, sources: list, section: str, view: dict, prior: str,
            append, write, at: str, rev: int = None, runtime: str = None) -> "dict | None":
    """One computed section, brought back into agreement with the records -- through the one writer.

    Returns the journalled before-image, or `None` where the span already said exactly this and
    nothing was removed. The write happens either way, and it happens through S1's `accept`, so
    the record of what left the artifact is extended BEFORE the artifact is replaced and this
    passage adds no second way to write a bounded surface.

    What it deliberately does not do is touch the artifact's count of its own losses. That count
    is of removals curated nowhere, it is restated by the writer that owns the artifact's front
    matter, and whether replacing a span whose source was never at risk belongs in it is a
    question ADR-020 does not answer. It is left visible rather than settled quietly: a passage
    that decided it would have moved a number the host undertook to bring down, for a reason the
    host never agreed to.
    """
    return eviction.accept(
        ctx, prior=prior,
        candidate=filled(prior, shape=shape, sources=sources, section=section, view=view),
        append=append, write=write, at=at, artifact=shape[ARTIFACT], section=section,
        rev=rev, runtime=runtime)
