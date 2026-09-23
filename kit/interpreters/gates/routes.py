"""Two gate kinds over the corpus ROUTE GRAPH -- what reaches an obligation, and whether an index
and the place it indexes agree in both directions (ADR-019 decisions 5 and 6).

Neither builds a graph. *What reaches what* is answered once, in `corpus`, beside the reading it is
computed from, for the same reason the reading is not inside a gate: two walks of one corpus are
two answers to one question, and they agree exactly until one of them is fixed (Cardinal III).

**The two are opposite in what they may refuse, and that is the design.**

*Reachability is a MEASUREMENT.* An obligation that no entry reaches is a promise the system has
quietly stopped keeping -- and on the day the mechanism ships there are hundreds of them, every one
of them legal, every one of them somebody's, none of them a defect this gate may decide. So this
gate PRINTS what it read: how many documents carry an obligation, how many of those no route
reaches, each of them by name with the marks it carries, and how deep the reachable ones are. What
it RETURNS is the one thing that is genuinely wrong here -- a MARKER that fails its own
calibration. A detector that does not match the line its own row swears it matches reports that
nothing is owed, silently, in the direction nobody checks; every count above it is then a fiction
with a number. Whether the unreached count is too high is a different proposition, it belongs to a
budget, and the budget belongs to the host (ADR-006, ADR-001 point 4).

*Index completeness is DECIDABLE.* It starts at zero on every host, because a place that declares
no index is not checked at all -- so there is no legal state this gate fails on, and it may bite
from the first day. It is decided in BOTH directions or it is not decided: a one-directional check
(every link resolves) passes an index that is missing half its subject, which is how a corpus loses
a decision while its index stays green.

**Depth is reported and never gated** (ADR-019 decision 5). The number that would turn a distance
into a verdict does not exist, and a hop limit would fail a well-routed document for being deep
while passing a badly-routed one for being shallow.
"""

from __future__ import annotations

import re

import collection
import corpus
import declared

#: The obligation-markers schema's own field names. The MARKS are rows of a declared vocabulary --
#: the kit ships four and a host may declare its own set against the same schema -- so no pattern,
#: and no word a pattern looks for, is written here (Cardinal IV).
PATTERN, PROVES, ADMITS = "pattern", "proves", "admits"

#: What a gate's params call the marker vocabulary it reads: the same `sources`/`list`/`where`
#: shape every other declared rule set arrives in.
MARKERS = "markers"

#: The front-matter field with which a document claims to be the index of a place. The corpus map's
#: `indexed_by` is the one home of that fact; this field is read ONLY to catch the two disagreeing,
#: because a document and a map that name different indexes are both locally correct.
INDEXES = "indexes"


# -- the marks, held to their own calibration --------------------------------------------------
def _markers(ctx, among: dict) -> tuple:
    """The declared marks, resolved wherever they were declared -- the kit's default set, a host's
    own, or both -- and each one held to its own calibration before it reads anything."""
    return calibrated(
        declared.rules(ctx, among[corpus.SOURCES], among[corpus.LIST], among.get(corpus.WHERE)))


def calibrated(rows: list) -> tuple:
    """(the usable marks, what is wrong with the rest).

    Every row is run against its own two calibration lines before it is allowed to read a single
    document: the line it swears it matches, and the lookalike it swears it tolerates. This is the
    discipline the residence vocabulary already ships per genre, and it is not decoration -- a
    marker vocabulary with no calibration is a regex somebody believed, and its failure mode is
    silence.
    """
    usable, findings = [], []
    for row in rows:
        identity = row[collection.IDENTITY]
        try:
            pattern = re.compile(row[PATTERN])
        except re.error as exc:
            findings.append(
                f"{identity}: its pattern is not an expression this machine can read -- {exc}. A "
                f"mark that cannot compile catches nothing, and a corpus read with it reports that "
                f"nothing is owed."
            )
            continue
        if not pattern.search(row[PROVES]):
            findings.append(
                f"{identity}: its pattern does not match the line its own {PROVES!r} states it "
                f"must. The row is a detector that fails its own calibration: every document it "
                f"reads from here reports no obligation, and the reading is wrong in the one "
                f"direction nobody goes looking in."
            )
            continue
        if pattern.search(row[ADMITS]):
            findings.append(
                f"{identity}: its pattern also matches the lookalike its own {ADMITS!r} states it "
                f"must tolerate. A mark that fires on prose routes work that does not exist, and a "
                f"gate that cries wolf is switched off within a week -- taking the marks that were "
                f"right with it."
            )
            continue
        usable.append((identity, pattern))
    return usable, findings


def _owed(ctx, resident, marks: list) -> list:
    """The obligations one document carries: `(the mark, the line number, the line)`.

    Read line by line over the WHOLE document, fenced blocks included -- the opposite choice from
    the link reading, and deliberately so: a link inside an example routes nothing, while a task
    box written inside an example is still a task box somebody wrote and nobody ticked.
    """
    try:
        text = ctx.workspace.read_text(resident.path)
    except (OSError, ValueError, UnicodeDecodeError):
        return []
    found = []
    for number, line in enumerate(text.split("\n"), start=1):
        for identity, pattern in marks:
            if pattern.search(line):
                found.append((identity, number, line.strip()))
    return found


def _unreached(ctx, params) -> tuple:
    """`(the absence in words or None, the reading, the graph, the marks, what is owed, the
    unrouted paths, findings)` -- the ONE computation of *which documents carry an obligation that
    no declared entry reaches*.

    Two callers ask it: the gate below, which names them, and the MEASURE, which only counts them
    for whoever holds a budget over the number. Walked twice it would be two answers to one
    question, agreeing until the day one of them was fixed (Cardinal III). When nothing could be
    walked the absence is returned IN WORDS -- never as an empty set, which reads like a corpus
    whose obligations are all routed.
    """
    reading = corpus.read(ctx, params)
    absent = reading.nothing_read()
    if absent:
        return absent, reading, None, [], {}, [], []

    marks, findings = _markers(ctx, params[MARKERS])
    if not marks:
        return (
            f"NOTHING WAS COUNTED: not one of the {len(findings)} declared mark(s) can be used, so "
            f"no document was read for what it owes. The reading below is absent, not empty.",
            reading, None, marks, {}, [], findings,
        )

    graph = corpus.routes(ctx, reading, params.get(corpus.ROOTS))
    owed = {}
    for resident in reading.residents:
        carried = _owed(ctx, resident, marks)
        if carried:
            owed[resident.path] = carried

    unreachable = {resident.path for resident in graph.unreachable}
    unrouted = sorted(path for path in owed if path in unreachable)
    return None, reading, graph, marks, owed, unrouted, findings


def _routed(ctx, params) -> list:
    """Which documents owe something, and which of those no declared entry can reach."""
    absent, reading, graph, marks, owed, unrouted, findings = _unreached(ctx, params)
    if absent:
        print(f"        {absent}")
        return findings

    unreachable = {resident.path for resident in graph.unreachable}
    quiet = len(unreachable) - len(unrouted)
    depths = graph.by_depth()
    spread = ", ".join(f"{distance}:{depths[distance]}" for distance in sorted(depths)) or "none"

    print(
        f"        READ {graph.subject()}, using {len(marks)} declared mark(s). "
        f"{len(owed)} document(s) carry {sum(len(v) for v in owed.values())} live obligation "
        f"mark(s); {len(graph.depth)} document(s) are reachable from an entry, at distances "
        f"(hops:documents) {spread} -- a distance, never a verdict, and no hop "
        f"limit is applied to it. {len(unrouted)} document(s) carry an obligation that NO route "
        f"from a declared entry reaches; they are named below. The other {quiet} unreachable "
        f"document(s) owe nothing and are not a finding: an unlinked reference is inert, while an "
        f"obligation nobody can reach is a promise the system has stopped keeping. Whether "
        f"{len(unrouted)} is too many is a budget's verdict, and the budget is the host's."
    )
    for path in unrouted:
        carried = ", ".join(f"{identity} (line {number})" for identity, number, _ in owed[path])
        print(f"          UNROUTED: {path} -- {carried}")
    if not graph.roots:
        print(
            f"          NO ENTRY WAS DECLARED: {len(reading.places)} place(s) are mapped and not "
            f"one of them is marked as a root, so the walk started nowhere and every document "
            f"above is unreachable by construction. That is a statement about the map, not about "
            f"the corpus."
        )
    for entry in graph.indexes:
        if not entry.present:
            print(
                f"          AN INDEX IS NOT THERE: {entry.place[corpus.PATH]} is declared indexed "
                f"by {entry.place[corpus.INDEX]!r}, which no document occupies, so nothing is "
                f"reached through it. Named here as a hole in the graph; refused by the gate that "
                f"owns indexes."
            )
    return findings


# -- an index, and the place it answers for ----------------------------------------------------
def _authority_stated(reading, line: str) -> "str | None":
    """The authority an index row STATES, read from the rows of the vocabulary and from nowhere
    else -- or None when the line names none of them, or names more than one and is therefore a
    sentence rather than a statement. Ambiguity resolves to NOTHING, never to a guess."""
    named = {identity for identity in reading.authorities
             if re.search(rf"(?<![0-9A-Za-z_]){re.escape(identity)}(?![0-9A-Za-z_])", line,
                          re.IGNORECASE)}
    return named.pop() if len(named) == 1 else None


def _indexed(ctx, params) -> list:
    """An index and its place, agreed in both directions or refused."""
    reading = corpus.read(ctx, params)
    absent = reading.nothing_read()
    if absent:
        print(f"        {absent}")
        return []

    entries = corpus.indexed(ctx, reading)
    residents = {resident.path: resident for resident in reading.residents}
    unindexed = len(reading.places) - len(entries)

    findings: list = []
    elsewhere = 0
    for entry in entries:
        found, skipped = _completeness(ctx, reading, residents, entry)
        findings.extend(found)
        elsewhere += skipped
    print(
        f"        READ {len(entries)} declared index(es) over {sum(len(e.residents) for e in entries)} "
        f"resident(s), out of {len(reading.places)} declared place(s). {unindexed} place(s) "
        f"declare no index and are NOT CHECKED: an index nobody promised is not an index anybody "
        f"is missing. A resident answers to the most specific place that names it, so a nested "
        f"place's documents are its own index's subject and never this one's. {elsewhere} link(s) "
        f"written by an index point outside the place it answers for and were NOT JUDGED here: a "
        f"broken link is a defect of the document that wrote it, and this gate decides one thing "
        f"-- whether an index and its place agree about what is in it."
    )
    for resident in reading.residents:
        claimed = resident.declares(INDEXES)
        if claimed is None:
            continue
        rows = [e for e in entries if e.index == resident.path]
        if not any(e.place[corpus.PATH] == claimed for e in rows):
            findings.append(
                f"{resident.path}: it declares that it {INDEXES} {claimed!r}, and that place's row "
                f"names {[e.place[corpus.PATH] for e in rows] or 'no index at all'}. One place has "
                f"one answerable document: while the map and the document disagree, both are "
                f"locally correct and no reader can tell which index is the one that is missing "
                f"something."
            )
    return findings


def _completeness(ctx, reading, residents: dict, entry) -> tuple:
    """(what is wrong with this index, how many of its links it was not asked about).

    One index, held to the place it answers for, in both directions -- and counting what it
    declined to judge, because a reading that states only what it looked at reads exactly like a
    reading that looked at everything.
    """
    place = entry.place[corpus.PATH]
    if not entry.present:
        return ([
            f"{entry.place[corpus.INDEX]}: the map declares this the index of {place} and no "
            f"document is there. A place that promises an index and has none is worse than a place "
            f"that promised nothing: the promise is what stops anybody writing one."
        ], 0)
    if entry.index in residents:
        links = residents[entry.index].links
    else:
        try:
            links = corpus.links_in(ctx.workspace.read_text(entry.index))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            return ([f"{entry.index}: it indexes {place} and it cannot be read -- {exc}."], 0)

    findings, reached, elsewhere = [], {}, 0
    for raw, number, line in links:
        target = corpus.reference(ctx, entry.index, raw)
        if target is None or not (target == place.rstrip("/") or target.startswith(place)):
            elsewhere += 1
            continue
        if not ctx.workspace.exists(target):
            findings.append(
                f"{entry.index}: line {number} links {raw!r} inside {place}, and nothing is there. "
                f"A row for a document that does not exist is the failure an index is consulted "
                f"for: the reader believes the thing was written and stops looking."
            )
            continue
        reached.setdefault(target, (number, line))

    for path in entry.residents:
        if path not in reached:
            findings.append(
                f"{entry.index}: it indexes {place} and it does not link {path}. An index that is "
                f"missing its subject is consulted and believed, which is worse than no index -- "
                f"the reader concludes the document does not exist and writes it again."
            )
            continue
        _number, line = reached[path]
        stated = _authority_stated(reading, line)
        if stated is None:
            continue
        held, _source = reading.authority_of(residents[path]) if path in residents else (None, None)
        if held != stated:
            findings.append(
                f"{entry.index}: its row for {path} states {stated!r}, and that document declares "
                f"{held!r}. An index that restates an authority has made a second home for it, and "
                f"a reader who trusts the index binds themselves by a claim the document never "
                f"made."
            )
    return findings, elsewhere


def _unrouted_obligations(ctx, params) -> "int | None":
    """How many documents carry an obligation no declared entry reaches. The number alone: whether
    it is too many is a ceiling's verdict, and the ceiling is the host's (ADR-019 decision 9).
    `None` where nothing could be walked -- an unwalked corpus has not got zero unrouted
    obligations, and a measure that said 0 there would report a promise being kept by nobody."""
    absent, _reading, _graph, _marks, _owed, unrouted, _findings = _unreached(ctx, params)
    return None if absent else len(unrouted)


#: What this module PROVIDES. Two kinds, one graph: a further question about what reaches what is a
#: row here and a function beside these -- never a second walk of the same corpus.
KINDS = {
    "obligation-reachable": _routed,
    "index-complete": _indexed,
}

#: What this module can be held to a BUDGET on -- published where the walk that produces it lives,
#: and read by the same discovery that finds a gate kind, so the ratchet names no measure itself.
MEASURES = {"unrouted_obligation_docs": _unrouted_obligations}
