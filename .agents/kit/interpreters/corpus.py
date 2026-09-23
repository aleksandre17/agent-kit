"""The corpus READING -- what every resident of a declared place IS, resolved once, for every gate.

Four gates ask one question and none of them may own the answer. *What is this document, and how
much does it bind?* is resolved HERE, in one order, from two declaration sites and no third: the
artifact's own front matter first, the host's corpus-map row second. Two gates computing that
resolution their own way would be two homes for one reading, and they would stay in agreement
exactly until one of them was fixed (Cardinal III) -- which is the failure ADR-019 exists to
prevent, committed in the act of implementing it.

It knows no class, no plane and no authority state. Which words exist arrives as ROWS: the state
default ceiling is the row whose `place_default` is true, and *more binding* is `binding_rank`.
A place may LOWER a claim and may never RAISE one (ADR-019 amendment 1). Nothing here may be read by
grepping for a word, because there is no word here to grep for (Cardinal IV).

Three properties of the reading are deliberate and each is a cardinal:

  * **A place CONFERS a class and never supplies authority.** Authority reaches a document from
    exactly one place -- the document. A place's ceiling CAPS what a resident may declare --
    the states a place is allowed to name at all; the state no place may name is outside the
    ceiling's jurisdiction and stays reachable only by the artifact's own word, which is the whole
    of ADR-019 decision 1.
  * **Undeclared is a STATE, not an absence.** A document declaring nothing is reported and
    counted, never inferred into something better and never quietly passed (Cardinal V).
  * **The subject is what the HOST declared.** The reading is over the residents of declared
    places and says so in its own words. A corpus-wide walk would need an exclusion list held in
    an interpreter -- policy in the machinery -- and would read a tree the host never mapped.

**The ROUTE GRAPH lives here too, and for the same reason.** *Can this document be reached from
where the work is steered* is one question with two askers -- the obligation reading and the index
reading -- and a graph built twice is two answers that agree until one of them is fixed. It is the
same reading seen as edges rather than as rows, computed from the text already in hand:

  * an EDGE is a link one resident writes that RESOLVES to another resident, and an `indexed_by`
    row -- the index reaches every resident of the place it answers for. Nothing else is an edge.
    A mention in prose is not a link, a link into a fenced block is an example of a link, and a
    link this reading cannot resolve is COUNTED as unresolved rather than dropped, because a graph
    that quietly forgets what it could not read reports a corpus better connected than it is.
  * a ROOT is a place the host's map marks as an entry, and which flag marks one arrives as a
    DECLARED filter. A graph whose roots are everything has no unreachable node and measures
    nothing; a graph whose roots are chosen in here would be this interpreter deciding where the
    work is steered from.
  * DEPTH is recorded and never judged. The number that would turn a distance into a verdict does
    not exist (ADR-019 decision 5), so what is produced is the distance and the honest statement
    of what it was measured from.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import unquote

import collection
import declared
import placement
from errors import KitError

#: The medium a DECLARATION can live in. Front matter in a source file is a comment a machine
#: believes (ADR-019, declared absence 5), so the reading looks at documents and at nothing else.
DOCUMENT = ".md"

#: The fence a front-matter block is written between, and the one place it may start.
FENCE = "---"

#: The contract an artifact's own declaration keeps. Named here rather than handed in as a param:
#: what a document may say about itself is the KIT's contract and has one home, and a gate free to
#: name another schema would be a second one.
CONTRACT = "front-matter"

#: The front-matter contract's own field names -- the schema `front-matter` is their home; these
#: are the ones this reading resolves with. The others the contract carries are declared there and
#: consumed by the slices that own them.
KIND, AUTHORITY, OWNS = "kind", "authority", "owns"
SUPERSEDES, SUPERSEDED_BY = "supersedes", "superseded_by"

#: The corpus map's own field names (schema `corpus-map`). `INDEX` is the document answerable for
#: a place: one declaration, two consequences -- an edge into every resident, and an index that can
#: be held to what it leaves out. Which field marks an ENTRY is NOT here: it arrives as a declared
#: filter, because a root is the host's statement about where work is steered from.
PATH, HOLDS, CEILING, INDEX = "path", "holds", "authority_ceiling", "indexed_by"
WRITER, LIFECYCLE, READ_WHEN = "writer", "lifecycle", "read_when"

#: The field every vocabulary row states itself in, and the `kinds` row field naming the plane its
#: class belongs to. A plane is a word of the vocabulary like any other: which planes exist, and
#: which class sits in which, is declared there and read here -- never a section list in a page.
SUMMARY, PLANE = "summary", "plane"

#: The authority vocabulary's own field names (schema `record-keeping`). Not the states -- the
#: FIELDS by which the states declare their own order and their own reach.
RANK, IS_DEFAULT = "binding_rank", "place_default"

#: What a gate's params call the parts of the reading it wants. The contract between the
#: declaration that configures a gate and this module.
MAP, AUTHORITIES, CLASSES = "map", "authorities", "classes"
SOURCES, LIST, WHERE = "sources", "list", "where"

#: What a PROJECTION's declaration additionally calls the vocabulary it groups the catalog by --
#: the same `sources`/`list` shape as the other two, because a plane list is a declared vocabulary
#: and not a structure of this module.
PLANES = "planes"

#: What a gate's params call the ROOT set: a filter over the map's own rows, one field and one
#: value (`declared.matching`). It is a param and not a constant here because *which declaration
#: makes a place an entry* is the corpus map's word; an interpreter that knew it would be deciding
#: policy, and a graph rooted by a guess measures the guess (Cardinal IV).
ROOTS = "roots"

#: Where a resolved value CAME FROM. The reading's own words about provenance -- a value without
#: its source is a reading nobody can check, which is the difference between conferred and claimed.
SELF, PLACE = "its own front matter", "its place"


class CorpusError(KitError):
    """The corpus reading cannot be taken as declared: a vocabulary with no comparable order, or
    no single default ceiling. Refused rather than resolved, because every resolution downstream
    would inherit the guess."""

    code = "KIT0053"


class Unreadable(Exception):
    """This document has front matter and it cannot be read. Named, never skipped."""


def _front_matter(text: str) -> "dict | None":
    """The block a document declares itself in, or None when it declares nothing.

    The grammar is deliberately tiny, and that is the point: a declaration carries no behaviour,
    no expression and no nesting (Cardinal IV), so anything richer than `key: value` and a block
    list is REFUSED by name rather than half-understood. A parser that guesses at a line it does
    not know produces a declaration nobody wrote.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != FENCE:
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == FENCE)
    except StopIteration:
        raise Unreadable(f"it opens a {FENCE} block and never closes it")

    found: dict = {}
    key = None
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):
            item = line.strip()
            if not item.startswith("- ") or key is None:
                raise Unreadable(f"line {number} ({line.strip()!r}) continues nothing")
            found.setdefault(key, [])
            if not isinstance(found[key], list):
                raise Unreadable(f"line {number} lists under {key!r}, which already has a value")
            found[key].append(_scalar(item[2:].strip()))
            continue
        if ":" not in line:
            raise Unreadable(f"line {number} ({line.strip()!r}) is neither a field nor a list item")
        key, _, value = line.partition(":")
        key = key.strip()
        if key in found:
            raise Unreadable(f"{key!r} is declared twice; one field, one value")
        value = value.strip()
        found[key] = _scalar(value) if value else []
    return found


def _scalar(raw: str):
    """A value as written. Quotes are stripped because a declaration may need to carry a colon;
    nothing else is interpreted -- no numbers, no booleans, no references, no dates."""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def listed(value) -> list:
    """A field that may name one thing or several, read as several. One document superseding two
    is an ordinary succession; making the caller branch on the shape would put the grammar of a
    declaration into every reader of it."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


#: The two forms in which a document NAMES another one: the target of a link, and the target of a
#: reference definition. Nothing else is read as an edge. A bare path written in prose is a
#: mention, and a graph built from mentions measures the prose instead of the routing.
_LINK = re.compile(r"\[[^\]\n]*\]\(\s*<?([^)>\s]+)>?[^)\n]*\)")
_DEFINITION = re.compile(r"^\[[^\]\n]+\]:\s*<?([^>\s]+)>?")

#: The line that opens or closes a fenced block. What is inside one is an EXAMPLE, and an example
#: link that routed a document would make the graph read better connected than the corpus is.
_FENCED = re.compile(r"^\s*(?:```|~~~)")


def links_in(text: str) -> list:
    """Every document this text NAMES: `(the target as written, the line number, the whole line)`.

    The line travels with the target because a reader downstream has to judge what the document
    SAID about what it linked, and a target torn out of its sentence cannot be held to anything.
    Fenced blocks are skipped -- see `_FENCED`.
    """
    found: list = []
    fenced = False
    for number, line in enumerate(text.split("\n"), start=1):
        if _FENCED.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for match in (*_LINK.findall(line), *_DEFINITION.findall(line)):
            found.append((match, number, line.strip()))
    return found


class Resident:
    """One document of the corpus, as this reading found it: where it lives, which place declared
    that spot, what it says about itself, and what it names. What it IS is not stored here -- it is
    RESOLVED by the reading, so there is no second copy of the answer to keep in step."""

    __slots__ = ("path", "place", "front", "unreadable", "links")

    def __init__(self, path: str, place: dict, front, unreadable=None, links=()) -> None:
        self.path, self.place, self.front, self.unreadable = path, place, front or {}, unreadable
        self.links = list(links)

    def declares(self, field: str):
        return self.front.get(field)

    @property
    def declares_nothing(self) -> bool:
        """It said neither what it IS nor how much it BINDS. Other fields are not a
        classification: an artifact that declares only that it indexes something has still never
        said what it is."""
        return self.declares(KIND) is None and self.declares(AUTHORITY) is None


class Reading:
    """The corpus as one resolution. Every gate reads this and none of them re-derives it."""

    __slots__ = ("maps", "places", "residents", "missing_places", "authorities", "classes")

    def __init__(self, maps, places, residents, missing_places, authorities, classes) -> None:
        self.maps = maps
        self.places = places
        self.residents = residents
        self.missing_places = missing_places
        self.authorities = authorities
        self.classes = classes

    # -- the vocabulary, read as rows --------------------------------------------------------
    def _row(self, identity):
        return self.authorities.get(identity)

    @property
    def default_ceiling(self) -> dict:
        rows = [row for row in self.authorities.values() if row[IS_DEFAULT]]
        if len(rows) != 1:
            raise CorpusError(
                f"the authority vocabulary declares {len(rows)} default ceiling(s); exactly one is "
                f"required, because a place that names none must still cap its residents by "
                f"something, and a cap chosen here would be this interpreter deciding policy"
            )
        return rows[0]

    def is_the_most_binding(self, row: dict) -> bool:
        """Whether this state is the most binding one the vocabulary declares. It is asked for one
        reason only: the most binding claim is the one a second claimant can contradict, so it is
        the one that must say what it OWNS. Read from the ranks, so the vocabulary can grow a
        stronger state without this line being touched (ADR-019 amendment 1)."""
        return row[RANK] == max(r[RANK] for r in self.authorities.values())

    def ceiling_of(self, resident: Resident) -> dict:
        named = resident.place.get(CEILING)
        return self._row(named) if named in self.authorities else self.default_ceiling

    # -- the resolution, in its order --------------------------------------------------------
    def class_of(self, resident: Resident) -> tuple:
        """(the class, where it came from). The artifact's own word first; the place's row second;
        and when neither speaks, NOTHING -- never a guess, and never the place's word dressed as
        the artifact's."""
        own = resident.declares(KIND)
        if own is not None:
            return own, SELF
        conferred = resident.place.get(HOLDS)
        if conferred is not None:
            return conferred, PLACE
        return None, None

    def authority_of(self, resident: Resident) -> tuple:
        """(the authority, where it came from). ONE site only: a place confers a class and never
        an authority, so there is no second rung here and the absence of one is the mechanism."""
        own = resident.declares(AUTHORITY)
        return (own, SELF) if own is not None else (None, None)

    # -- the census, as four readings of one set ------------------------------------------------
    # How much of this corpus has ever said what it is, resolved HERE because two readers now ask
    # it: the census gate, which prints it, and the catalog projection, which prints it beside the
    # places it falls in. Counted twice it would be two answers to one question that agree until
    # one of them is fixed (Cardinal III) -- and a catalog whose totals disagreed with the gate's
    # would leave a reader unable to tell which of two correct-looking numbers described the tree.
    @property
    def spoke(self) -> list:
        """The residents that declared their own class or authority."""
        return [r for r in self.residents if not r.declares_nothing and not r.unreadable]

    @property
    def undeclared(self) -> list:
        """The residents that declared neither -- UNCLASSIFIED, which is a state and not a gap."""
        return [r for r in self.residents if r.declares_nothing and not r.unreadable]

    @property
    def conferred(self) -> list:
        """Of those, the ones a place classes anyway. The rest are classed by nothing at all."""
        return [r for r in self.undeclared if r.place.get(HOLDS)]

    @property
    def unreadable_documents(self) -> list:
        """The residents whose declaration could not be read. Named, never counted as silent."""
        return [r for r in self.residents if r.unreadable]

    # -- what it read, in its own words ------------------------------------------------------
    def subject(self) -> str:
        return (
            f"{len(self.residents)} document(s) ending {DOCUMENT!r}, under {len(self.places)} "
            f"declared place(s), from {self.maps} corpus-map file(s)"
        )

    @property
    def unmapped(self) -> bool:
        return not self.places

    def nothing_read(self) -> "str | None":
        """The honest absence, in the reading's own words, or None when there is a corpus to
        report on. A host may legitimately have mapped nothing; what it may not do is have that
        read as a clean corpus (Cardinal V). Every gate over this reading opens with the same
        sentence because there is one state being described, and a gate that worded it for itself
        would be a second account of what was not read."""
        if self.unmapped:
            return (
                "NOTHING WAS READ: this host declares no corpus map, so no place confers a class, "
                "no document was opened, and no count below is a count of this repository. That "
                "is a legal state and it is green. What was NOT read: every document in the tree. "
                "A place is a row a human writes; until one exists there is nothing to read it "
                "against."
            )
        if not self.residents:
            return (
                f"NOTHING WAS READ: {len(self.places)} place(s) are declared and not one document "
                f"ending {DOCUMENT!r} resides in them. The map is a statement about places that "
                f"hold nothing yet -- green, and not a corpus that was found clean."
            )
        return None


def _places(rows: list) -> list:
    """The places, most specific first. Two rows may legitimately nest -- a host says one thing
    about `docs/` and another about `docs/decisions/` -- and the resident belongs to the row that
    names the smallest place containing it. Refusing the overlap would forbid a map every host
    needs; choosing the shorter row would let a coarse statement silently overrule a precise one."""
    return sorted(rows, key=lambda row: len(row[PATH]), reverse=True)


def _resident_paths(ctx, place: dict) -> list:
    path = place[PATH]
    if path.endswith("/"):
        return [rel for rel in ctx.workspace.files_under(path.rstrip("/"))
                if rel.endswith(DOCUMENT)]
    return [path] if path.endswith(DOCUMENT) and ctx.workspace.exists(path) else []


def _vocabulary(ctx, among: dict) -> dict:
    """One named list of the vocabulary, by id. Resolved through `declared`, which already refuses
    an id declared twice -- the one failure a set spanning kit and host brings with it."""
    rows = declared.rules(ctx, among[SOURCES], among[LIST], among.get(WHERE))
    return {row[collection.IDENTITY]: row for row in rows}


def declaration(ctx, params: dict) -> tuple:
    """WHERE this host writes its corpus map, and the files of it as the tree holds them now:
    `(the space, [(path, document)])`.

    One home for *which space is the map*, because two readers ask it. The reading below merges the
    places out of the files; the ratchet must find the same space in the PREVIOUS accepted state,
    where the files are whatever HEAD holds and not what is on disk. A caller that located the space
    for itself would be a second answer to a question the install declaration already owns, and the
    two would agree until the day the capability moved it (Cardinal III).
    """
    readings = collection.read_all(ctx, ctx.enabled_capabilities())
    if params[MAP] not in readings:
        raise declared.DeclarationError(
            f"this gate was declared over a corpus map named {params[MAP]!r}, which no enabled "
            f"capability declares readable; the names declared are {sorted(readings)}"
        )
    space = next(item["target"] for capability in ctx.enabled_capabilities()
                 for item in capability.installs if item.get("reads_as") == params[MAP])
    return space.rstrip("/"), readings[params[MAP]].records


def read(ctx, params: dict) -> Reading:
    """The corpus, as this host declared it and as its documents declare themselves.

    A host that has declared no map is not an error and not an empty corpus: it is a host whose
    corpus was never mapped, and the reading says exactly that instead of reporting a green zero.
    """
    _space, records = declaration(ctx, params)

    rows: list = []
    for _rel, document in records:
        rows.extend(document["places"])

    residents: dict = {}
    missing: list = []
    for place in _places(rows):
        if not ctx.workspace.exists(place[PATH].rstrip("/")):
            missing.append(place)
            continue
        for rel in _resident_paths(ctx, place):
            residents.setdefault(rel, place)

    read_back = []
    for rel in sorted(residents):
        try:
            text = ctx.workspace.read_text(rel)
            front = _front_matter(text)
            errors = ctx.manifest.validate(front, CONTRACT) if front is not None else []
            if errors:
                raise Unreadable(f"its declaration does not honour {CONTRACT!r} -- " + "; ".join(errors))
            read_back.append(Resident(rel, residents[rel], front, None, links_in(text)))
        except Unreadable as exc:
            read_back.append(Resident(rel, residents[rel], None, str(exc), links_in(text)))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            read_back.append(Resident(rel, residents[rel], None, f"it cannot be read -- {exc}"))

    return Reading(
        maps=len(records),
        places=rows,
        residents=read_back,
        missing_places=missing,
        authorities=_vocabulary(ctx, params[AUTHORITIES]),
        classes=_vocabulary(ctx, params[CLASSES]),
    )


def resolved(ctx, rel: str) -> "str | None":
    """A path one document names in another's front matter, as the host-relative path a reading
    reads -- or None when it names something outside this host, whose documents this reading does
    not reach. Measured by the one home of that measurement, never re-implemented here."""
    try:
        return placement.host_relative(ctx.workspace.root, rel)
    except placement.Unplaceable:
        return None


def reference(ctx, source: str, raw: str) -> "str | None":
    """One link, as the host-relative path it points at -- or None when it points somewhere this
    reading does not reach: another machine (a scheme), a position inside a document (a fragment
    alone), or outside this host.

    A link is written relative to the DOCUMENT that writes it, and that is the one thing a graph
    over documents has to get right (Cardinal VII): resolved against the root instead, every
    relative link in a nested place would name a file that is not there and the corpus would read
    as unlinked while every link in it worked perfectly in a browser.
    """
    raw = unquote(raw.split("#", 1)[0].split("?", 1)[0].strip())
    if not raw:
        return None
    if ":" in raw.split("/", 1)[0]:
        return None
    if raw.startswith("/"):
        return resolved(ctx, raw.lstrip("/"))
    return resolved(ctx, str(PurePosixPath(source).parent / raw))


class Indexed:
    """A place, the document answerable for it, and the residents it answers for. One declaration
    (`indexed_by`) with two consequences, held together so that the graph and the completeness
    reading cannot disagree about which document indexes what."""

    __slots__ = ("place", "index", "residents", "present")

    def __init__(self, place: dict, index, residents: list, present: bool) -> None:
        self.place, self.index, self.residents, self.present = place, index, residents, present


def indexed(ctx, reading: Reading) -> list:
    """Every place that declares an index, with the residents that index answers for.

    A resident belongs to the MOST SPECIFIC place that names it (`_places`), so a nested place's
    residents answer to the nested place's index and never to the coarser one. That follows from
    the reading and is not a second rule: the alternative -- an index answerable for every document
    beneath it -- would make a host that maps a subtree more precisely liable for it twice.
    """
    found = []
    for place in reading.places:
        named = place.get(INDEX)
        if not named:
            continue
        index = resolved(ctx, named)
        held = sorted(r.path for r in reading.residents if r.place is place)
        present = index is not None and ctx.workspace.exists(index)
        found.append(Indexed(place, index, [p for p in held if p != index], present))
    return found


class Routes:
    """The corpus as a GRAPH, and what a walk from the declared roots actually reached.

    It holds a distance and never a verdict. `depth` is *how far from an entry*, recorded for every
    node the walk reached; a node absent from it was reached by nothing, which is a reading and not
    yet a defect -- what makes an unreachable document a defect is what it OWES, and that belongs
    to the gate that reads obligations (ADR-019 decision 5).
    """

    __slots__ = ("reading", "roots", "rooted_places", "depth", "edges", "unresolved", "indexes",
                 "written")

    def __init__(self, reading, roots, rooted_places, depth, edges, unresolved, indexes,
                 written) -> None:
        self.reading, self.roots, self.rooted_places = reading, roots, rooted_places
        self.depth, self.edges, self.unresolved, self.indexes = depth, edges, unresolved, indexes
        self.written = written

    @property
    def unreachable(self) -> list:
        return [r for r in self.reading.residents if r.path not in self.depth]

    @property
    def spans(self) -> int:
        return sum(len(targets) for targets in self.edges.values())

    def by_depth(self) -> dict:
        found: dict = {}
        for distance in self.depth.values():
            found[distance] = found.get(distance, 0) + 1
        return found

    def subject(self) -> str:
        """What the walk was over, stated with the count (Cardinal V). A reachability number whose
        root set is unstated is not a measurement of anything: the same corpus is fully routed from
        every place and routed from none."""
        return (
            f"{len(self.reading.residents)} node(s) joined by {self.spans} edge(s) -- "
            f"{self.written} written as a link one document resolves to another, the rest "
            f"conferred by an index on the place it answers for -- walked from "
            f"{len(self.roots)} document(s) resident in {len(self.rooted_places)} declared "
            f"entry place(s); {self.unresolved} link(s) named nothing this reading reaches"
        )


def routes(ctx, reading: Reading, where) -> Routes:
    """The route graph, walked from the roots the host declared.

    The root filter is REQUIRED and never defaulted. `matching` with no filter selects every row,
    so a missing declaration would silently make every place an entry and the walk would reach
    everything -- a green reading of a corpus nobody can navigate, which is the exact lie this
    invariant exists to catch (Cardinal V).
    """
    if where is None:
        raise declared.DeclarationError(
            f"this gate was declared with no {ROOTS!r} filter, so no row of the corpus map marks "
            f"an entry; a walk with no roots would either reach nothing or, if the filter were "
            f"defaulted to every row, reach everything -- and both are readings of a corpus that "
            f"was never asked where the work is steered from"
        )
    rooted = declared.matching(reading.places, where)
    marked = {id(row) for row in rooted}
    residents = {resident.path: resident for resident in reading.residents}

    edges: dict = {}
    unresolved = 0
    for resident in reading.residents:
        reached = edges.setdefault(resident.path, set())
        for raw, _number, _line in resident.links:
            target = reference(ctx, resident.path, raw)
            if target is None or target not in residents:
                unresolved += 1
                continue
            if target != resident.path:
                reached.add(target)

    written = sum(len(targets) for targets in edges.values())
    found = indexed(ctx, reading)
    for entry in found:
        if entry.index is not None:
            edges.setdefault(entry.index, set()).update(entry.residents)

    roots = sorted(path for path, resident in residents.items() if id(resident.place) in marked)
    depth = {path: 0 for path in roots}
    frontier, distance = list(roots), 0
    while frontier:
        distance += 1
        onward = []
        for path in frontier:
            for target in sorted(edges.get(path, ())):
                if target not in depth:
                    depth[target] = distance
                    onward.append(target)
        frontier = onward

    return Routes(reading, roots, rooted, depth, edges, unresolved, found, written)


# -- the reading, as data a surface may walk ---------------------------------------------------
#
# A PROJECTION of the two readings above and never a third one. Everything below is a
# re-shaping: every count comes from a property of `Reading`, every distance from `Routes`, every
# index from `indexed`. Nothing here opens a file, resolves a class or decides what is wrong --
# a projection states what the declarations say and carries no verdict (ADR-019 decision 4).
#
# It lives beside the reading because it is the reading seen as rows. Put in the renderer it
# would be a second traversal of the corpus written by someone who could not see this file, and
# the day a field changed meaning the page and the gate would disagree while both stayed green.

#: The kind of view this module answers for. The word lives here, in the module that owns the
#: reading, exactly as a gate kind lives in the module that judges it: the generic half reads it
#: off this constant and spells no subject of its own.
VIEW = "corpus-reading"


def _place_row(reading: Reading, place: dict, residents: list, entry, rooted: set) -> dict:
    """One declared PLACE, as the catalog prints it: what the map says about it, and what the
    reading found there. Every key is present on every row -- an absent field is the empty
    string, never a missing key -- so a page can say *nothing was declared here* in words rather
    than rendering a hole a reader would read as a zero (Cardinal V)."""
    held = reading.classes.get(place.get(HOLDS))
    declared_ceiling = place.get(CEILING)
    unreadable = [r for r in residents if r.unreadable]
    undeclared = [r for r in residents if r.declares_nothing and not r.unreadable]
    return {
        "path": place[PATH],
        "holds": place.get(HOLDS) or "",
        "class_summary": (held or {}).get(SUMMARY, ""),
        # The EFFECTIVE cap, and whether the place stated it. A place that states none is capped
        # by the vocabulary's own default row, which a reader can recompute from the two
        # declarations and nothing else (ADR-019 amendment 1).
        "ceiling": declared_ceiling or reading.default_ceiling[collection.IDENTITY],
        "ceiling_declared": declared_ceiling or "",
        "writer": place.get(WRITER) or "",
        "lifecycle": place.get(LIFECYCLE) or "",
        "index": place.get(INDEX) or "",
        "index_missing": bool(entry is not None and not entry.present),
        # Read off the declared ROOT filter the graph was walked with -- never off a field name
        # spelled here, because which declaration makes a place an entry is the host's word.
        "entry": id(place) in rooted,
        "read_when": list(place.get(READ_WHEN) or []),
        "documents": len(residents),
        "declared": len(residents) - len(undeclared) - len(unreadable),
        "undeclared": len(undeclared),
        "unreadable": len(unreadable),
    }


def projected(ctx, params: dict) -> dict:
    """The corpus reading and its route graph as PLAIN DATA -- the one thing a projection needs
    and the only thing it gets: rows, counts and the readings' own sentences.

    The sections are the PLANES the vocabulary declares, in the order it declares them, and a
    plane that holds no declared place is a section that says so. A place whose class names a
    plane the vocabulary does not declare is neither dropped nor filed under a guess: it is
    carried out separately, because a row that vanished from a catalog is the one defect a
    catalog may never have.
    """
    reading = read(ctx, params)
    graph = routes(ctx, reading, params.get(ROOTS))
    planes = _vocabulary(ctx, params[PLANES])

    residents_of: dict = {}
    for resident in reading.residents:
        residents_of.setdefault(id(resident.place), []).append(resident)
    indexes = {id(entry.place): entry for entry in graph.indexes}
    rooted = {id(row) for row in graph.rooted_places}

    held: dict = {}
    outside: list = []
    placed: list = []
    for place in sorted(reading.places, key=lambda row: row[PATH]):
        row = _place_row(reading, place, residents_of.get(id(place), []),
                         indexes.get(id(place)), rooted)
        placed.append(row)
        where = (reading.classes.get(place.get(HOLDS)) or {}).get(PLANE)
        (held.setdefault(where, []) if where in planes else outside).append(row)

    sections = [{
        "id": identity,
        "summary": plane.get(SUMMARY, ""),
        "places": held.get(identity, []),
        "place_count": len(held.get(identity, [])),
        "documents": sum(row["documents"] for row in held.get(identity, [])),
    } for identity, plane in planes.items()]

    top = []
    for resident in reading.residents:
        claimed, _source = reading.authority_of(resident)
        row = reading.authorities.get(claimed) if claimed is not None else None
        if row is not None and reading.is_the_most_binding(row):
            top.append({"path": resident.path, "authority": claimed,
                        "owns": listed(resident.declares(OWNS))})

    successions = [
        {"path": resident.path, "states": stated, "names": named}
        for resident in reading.residents
        for stated in (SUPERSEDES, SUPERSEDED_BY)
        for named in listed(resident.declares(stated))
    ]

    return {
        # What was read, in the reading's own words -- and the honest absence in its own words
        # when there was nothing to read. An empty catalog and a catalog of an unmapped corpus
        # are different propositions, and only one of them is about this repository.
        "nothing_read": reading.nothing_read() or "",
        "subject": reading.subject(),
        "graph_subject": graph.subject(),
        "maps": reading.maps,
        "place_count": len(reading.places),
        "documents": len(reading.residents),
        "declared": len(reading.spoke),
        "undeclared": len(reading.undeclared),
        "conferred": len(reading.conferred),
        "unreadable": len(reading.unreadable_documents),
        "default_ceiling": reading.default_ceiling[collection.IDENTITY],
        "planes": sections,
        "outside_a_declared_plane": outside,
        "places": placed,
        # The NAMED exceptions -- the handful of rows a reader of a catalog is actually looking
        # for. Named because there are few of them by construction; the rest are counted, because
        # a row per document is a listing nobody reads (ADR-019 decision 4).
        "top_claims": top,
        "top_authority": max(reading.authorities.values(),
                             key=lambda row: row[RANK])[collection.IDENTITY],
        "indexes": [{"place": entry.place[PATH], "index": entry.index or "",
                     "declared": entry.place.get(INDEX) or "", "present": entry.present,
                     "documents": len(entry.residents)}
                    for entry in sorted(graph.indexes, key=lambda e: e.place[PATH])],
        "successions": successions,
        "unreadable_documents": [{"path": resident.path, "why": resident.unreadable}
                                 for resident in reading.unreadable_documents],
        "missing_places": [{"path": place[PATH]}
                           for place in sorted(reading.missing_places, key=lambda p: p[PATH])],
        # The graph, as the routes page prints it: where a reader may enter, what each entry
        # answers, and how far the walk reached. A distance, never a verdict (decision 5).
        "entries": [row for row in placed if row["entry"]],
        "questions": [row for row in placed if row["read_when"] and not row["entry"]],
        "depths": [{"hops": hops, "documents": count}
                   for hops, count in sorted(graph.by_depth().items())],
        "roots": len(graph.roots),
        "reached": len(graph.depth),
        "unreachable": len(graph.unreachable),
        "unresolved": graph.unresolved,
        "edges": graph.spans,
        "written": graph.written,
    }


#: What this module PROVIDES to a view. One kind, one function, declared where the reading lives:
#: the generic half merges this registry and knows neither the word nor the shape.
VIEWS = {VIEW: projected}
