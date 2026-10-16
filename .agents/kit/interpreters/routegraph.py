"""The ROUTE GRAPH of the corpus -- *can this document be reached from where the work is steered*.

One question with two askers -- the obligation reading and the index reading -- and a graph built
twice is two answers that agree until one of them is fixed. It is the corpus reading (`corpus`)
seen as edges rather than as rows, computed from the text already in hand:

  * an EDGE is a link one resident writes that RESOLVES to another resident, and an `indexed_by`
    row -- the index reaches every resident of the place it answers for. Nothing else is an edge.
  * a ROOT is a place the host's map marks as an entry, and which flag marks one arrives as a
    DECLARED filter.
  * DEPTH is recorded and never judged (ADR-019 decision 5).
"""

from __future__ import annotations

import corpus
import declared

class Indexed:
    """A place, the document answerable for it, and the residents it answers for. One declaration
    (`indexed_by`) with two consequences, held together so that the graph and the completeness
    reading cannot disagree about which document indexes what."""

    __slots__ = ("place", "index", "residents", "present")

    def __init__(self, place: dict, index, residents: list, present: bool) -> None:
        self.place, self.index, self.residents, self.present = place, index, residents, present


def indexed(ctx, reading: corpus.Reading) -> list:
    """Every place that declares an index, with the residents that index answers for.

    A resident belongs to the MOST SPECIFIC place that names it (`_places`), so a nested place's
    residents answer to the nested place's index and never to the coarser one. That follows from
    the reading and is not a second rule: the alternative -- an index answerable for every document
    beneath it -- would make a host that maps a subtree more precisely liable for it twice.
    """
    found = []
    for place in reading.places:
        named = place.get(corpus.INDEX)
        if not named:
            continue
        index = corpus.resolved(ctx, named)
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


def routes(ctx, reading: corpus.Reading, where) -> Routes:
    """The route graph, walked from the roots the host declared.

    The root filter is REQUIRED and never defaulted. `matching` with no filter selects every row,
    so a missing declaration would silently make every place an entry and the walk would reach
    everything -- a green reading of a corpus nobody can navigate, which is the exact lie this
    invariant exists to catch (Cardinal V).
    """
    if where is None:
        raise declared.DeclarationError(
            f"this gate was declared with no {corpus.ROOTS!r} filter, so no row of the corpus map marks "
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
            target = corpus.reference(ctx, resident.path, raw)
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


