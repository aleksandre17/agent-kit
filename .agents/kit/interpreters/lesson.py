"""What a host has learned that it says is not about itself -- read, counted, and never carried.

A record whose work is over may state what that work TAUGHT: the subject the teaching is about,
the teaching itself in the host's own sentence, and a WORD saying how far the host claims it
holds. The word is the only one of the three a machine reads, and it is read by looking it up in
a published vocabulary that says, of each word, whether a record carrying it claims to hold
beyond the repository that learned it. Nothing here is matched against prose: a mark is a field
of a record, its meaning is a row somebody published, and a mark in a word nobody published is
NAMED rather than guessed at -- because a reader that guessed would be inventing the claim it
then forwarded as somebody else's.

Three properties are the whole of this module, and each one answers something that goes wrong in
exactly one way:

  * It is a READING and never a carriage. Nothing here, and nothing above here, opens a network,
    writes a byte outside the repository it was pointed at, or creates the faintest dependency
    from a host on whoever published its framework. What leaves is TEXT; a person carries it, or
    it does not travel. A framework that could reach its hosts' lessons by itself would have
    turned every host into a supplier of a service nobody bought.

  * The work must be OVER. A record still in motion states an intention, and an intention
    forwarded as a finding is exactly how a body of doctrine acquires clauses that turned out
    not to be true. What OVER means is not a word held here -- it is the SHAPE of the lifecycle
    the collection declares: a state that no declared passage leads out of is a state the work
    does not leave. Read from the declaration, so the day a lifecycle grows an exit from that
    state, this stops counting it and nothing is edited.

  * One occasion is not a pattern. A claim is counted across the SEPARATE records that carry it,
    and the number at which it may be carried is declared beside the word it is carried under --
    never here. A framework that held that number would have decided how much evidence somebody
    else's proposal needs, and a number nobody can find in a declaration is not a bar anyone
    agreed to.

An unread world answers with None. A host whose enabled capabilities declare nowhere for such a
statement to be written has not learned nothing: there is no question to ask it, and a zero here
would read on every surface above exactly like a host that had nothing to say.
"""

from __future__ import annotations

import collection
import declared
import lifecycle as lifecycle_module

#: The contract a vocabulary of these words keeps, and the field its rows sit under. Both are the
#: SCHEMA's words -- the one vocabulary a declaration and its reader are equally entitled to
#: spell -- and the set is open: every enabled capability publishing under that contract is read,
#: none of them by name.
VOCABULARY = {"validates": "lesson"}
ROWS = "extents"

#: What a row of that vocabulary carries: what the word means to a reader who has never seen this
#: host, whether it claims to hold beyond the host, and how many occasions it must have before it
#: may be carried. The third is read as ABSENT-or-declared and never defaulted.
MEANS, BEYOND, SEEN_AT_LEAST = "means", "beyond", "seen_at_least"

#: The key under which a governed collection names the field one of its records writes this in.
#: The key belongs to the capability contract; the field NAME belongs to the declaration and is
#: read from it. A capability that declares no such key holds no lessons, which is a complete
#: state and not a missing feature.
LESSON = "lesson"

#: The three words inside that field, as the schema that governs such a record declares them.
SUBJECT, EXTENT, STATEMENT = "subject", "extent", "statement"

#: What a record calls itself for a reader. Declared by the same schema, spelled for the same
#: reason: a text that named a record by its identity alone would send its reader hunting.
TITLE = "title"


class Sighting:
    """One record carrying one claim, and everything a reader somewhere else needs to check it.

    The path travels with the claim for the same reason a stance carries its author: a finding
    whose origin the reader cannot open is testimony, and testimony is what this whole mechanism
    exists to replace. The state travels with its own declared intent, so a word out of this
    host's lifecycle arrives explained rather than merely quoted.
    """

    __slots__ = ("subject", "statement", "mark", "identity", "title", "where", "state",
                 "state_title", "state_intent", "over")

    def __init__(self, subject, statement, mark, identity, title, where, state, state_title,
                 state_intent, over) -> None:
        self.subject, self.statement, self.mark = subject, statement, mark
        self.identity, self.title, self.where = identity, title, where
        self.state, self.state_title, self.state_intent = state, state_title, state_intent
        self.over = over


class Standing:
    """One claim -- a subject under one word -- and everything seen of it.

    A subject marked with two different words is two claims and stands as two: each word carries
    its own meaning and its own bar, and merging them would need a rule about which claim wins
    that nobody has declared. What did NOT count toward this claim is carried beside it, because
    a refusal that cannot say what is missing sends its reader looking for something that is
    already there.
    """

    __slots__ = ("subject", "mark", "row", "seen", "aside")

    def __init__(self, subject: str, mark: str, row: dict, seen: list, aside: list) -> None:
        self.subject, self.mark, self.row = subject, mark, row
        self.seen, self.aside = seen, aside

    @property
    def bar(self):
        """The number of occasions this word declares, or None where it declares none. Never a
        default: a bar nobody published is not a bar, and a claim measured against one the
        framework invented would be carrying evidence to a standard its reader never set."""
        return self.row.get(SEEN_AT_LEAST)

    @property
    def carried(self) -> bool:
        return self.bar is not None and len(self.seen) >= self.bar

    def missing(self) -> str:
        """What this claim lacks, in the words of what was found. One sentence per cause, because
        the cure for each is different and a single sentence would send the reader to the wrong
        file."""
        if self.bar is None:
            said = (f"the word {self.mark!r} says this holds beyond the host that learned it and "
                    f"declares no number of occasions at which it may be carried; until that "
                    f"number is declared where the word is, nothing is carried under it")
        else:
            said = (f"seen on {len(self.seen)} record(s) and the word {self.mark!r} may be "
                    f"carried at {self.bar}. What is missing is another record, of work that is "
                    f"over, marking the same subject with the same word -- and it has to be "
                    f"another record: one occasion restated twice is the same occasion, and a "
                    f"pattern nobody has paid for twice is an observation")
        for note in self.aside:
            said += f"; {note}"
        return said


def _over(governed) -> set:
    """The states of this lifecycle that no declared passage leads out of.

    DERIVED, never named. Which state means the work is over is the lifecycle's own statement
    about itself, and a word for it held in this module would be a second home for that statement
    -- correct on the day it was written and silently wrong the first time a passage was added.
    """
    leaves = {edge["from"] for edge in governed.doc["transitions"]}
    return {state["id"] for state in governed.states if state["id"] not in leaves}


def vocabulary(ctx) -> dict:
    """Every word a claim may be marked with, by name, as the enabled capabilities publish them.

    An open set that finds nothing is a DECLARED ZERO and not a missing source: a host whose
    capabilities publish no such vocabulary can mark nothing, and the reader above says so in its
    own words rather than reading every mark as unknown.
    """
    return {row[collection.IDENTITY]: row for row in declared.rules(ctx, VOCABULARY, ROWS)}


def _sighting(governed, over, rel, record) -> Sighting:
    said = record[governed.spec[LESSON]]
    state = record[governed.state_field]
    declared_state = governed.state(state) or {}
    return Sighting(
        subject=said[SUBJECT], statement=said[STATEMENT], mark=said[EXTENT],
        identity=record[collection.IDENTITY], title=record.get(TITLE, ""), where=rel,
        state=state, state_title=declared_state.get(TITLE, state),
        state_intent=declared_state.get("intent", ""), over=state in over)


def sighted(ctx):
    """Every claim this host has written down, by subject -- or None where it has nowhere to.

    `(by_subject, unreadable)`, where `by_subject` is None exactly when no enabled capability
    declares a field for such a statement. That is the unread world, and it answers None rather
    than an empty mapping: a host that was never asked the question and a host that answered
    nothing are two different states, and one zero for both would make them one.
    """
    capabilities = ctx.enabled_capabilities()
    carrying = [c for c in capabilities if (c.governs or {}).get(LESSON)]
    if not carrying:
        return None, []
    readings = collection.read_all(ctx, capabilities)
    by_subject: dict = {}
    for capability in carrying:
        governed = lifecycle_module.governed_of(capability, readings)
        over = _over(governed)
        field = governed.spec[LESSON]
        for rel, record in governed.members.records:
            if record.get(field) is None:
                continue
            found = _sighting(governed, over, rel, record)
            by_subject.setdefault(found.subject, []).append(found)
    for found in by_subject.values():
        found.sort(key=lambda s: (s.identity, s.where))
    words = vocabulary(ctx)
    return by_subject, sorted(
        f"{seen.where}: {seen.identity!r} says what it learned is {seen.mark!r}, and no "
        f"vocabulary published here declares that word (published: {sorted(words)}). Nothing is "
        f"claimed about it in either direction -- a mark whose meaning nobody published cannot "
        f"be read as one that holds here, and cannot be read as one that holds anywhere else"
        for found in by_subject.values() for seen in found if seen.mark not in words)


def _aside(sightings, mark: str, words: dict) -> list:
    """What was written about this subject and did not count toward this claim, each with why."""
    notes = []
    for seen in sightings:
        if seen.mark == mark and seen.over:
            continue
        if seen.mark == mark:
            notes.append(
                f"{seen.where} carries the same claim and its work is not over -- it stands at "
                f"{seen.state!r} ({seen.state_intent!r}), and a record still in motion states an "
                f"intention rather than something learned")
        elif seen.mark in words and not words[seen.mark][BEYOND]:
            notes.append(
                f"{seen.where} speaks about the same subject and is marked {seen.mark!r}, which "
                f"its vocabulary declares as holding only where it was learned, so it is not "
                f"evidence for a claim about anywhere else")
        elif seen.mark not in words:
            notes.append(
                f"{seen.where} speaks about the same subject in a word no vocabulary published "
                f"here declares ({seen.mark!r}), so nothing could be read from it")
    return notes


class Reading:
    """One reading of everything this host has written down about what its work taught.

    It states the moment it was taken, because a second reader arriving later is reading a
    different world and the two must be able to contradict each other rather than merely
    disagree. `subjects` is None for a host that declares nowhere such a statement may be
    written -- the unread world, which is not an empty one.
    """

    __slots__ = ("subjects", "standings", "unreadable", "words", "taken_at")

    def __init__(self, subjects, standings, unreadable, words, taken_at) -> None:
        self.subjects, self.standings = subjects, standings
        self.unreadable, self.words, self.taken_at = unreadable, words, taken_at

    @property
    def unread(self) -> bool:
        return self.subjects is None

    def of(self, subject: str) -> list:
        """The claims this host makes about one subject that are addressed past its own walls."""
        return [s for s in self.standings if s.subject == subject]

    def about(self, subject: str) -> list:
        """Everything written about one subject, whatever it claims and whatever state it is in.
        What a refusal needs: a subject is not absent merely because nothing may be carried on it.
        """
        return (self.subjects or {}).get(subject, [])

    def named(self) -> list:
        return sorted(self.subjects or {})


def read(ctx) -> Reading:
    """Everything this host has to say past its own walls, and the state each claim stands in.

    A standing exists for every subject-and-word a record claims to hold beyond this host --
    including the ones nothing may carry yet, because a reading that held only the ready ones
    would look exactly like a host that had learned nothing at all.
    """
    by_subject, unreadable = sighted(ctx)
    words = vocabulary(ctx)
    if by_subject is None:
        return Reading(None, [], unreadable, words, ctx.clock.now())
    found = []
    for subject in sorted(by_subject):
        sightings = by_subject[subject]
        for mark in sorted({s.mark for s in sightings}):
            row = words.get(mark)
            if row is None or not row[BEYOND]:
                continue
            found.append(Standing(subject, mark, row,
                                  [s for s in sightings if s.mark == mark and s.over],
                                  _aside(sightings, mark, words)))
    return Reading(by_subject, found, unreadable, words, ctx.clock.now())
