"""The `corpus-reading` view: the corpus reading and its route graph as PLAIN DATA a surface walks.

A resolver of the `resolves` block (`resolution`): a capability declares it wants this view by its
kind, and the params travel here untouched.
"""

from __future__ import annotations

import collection
import corpus
import routegraph

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


def _place_row(reading: corpus.Reading, place: dict, residents: list, entry, rooted: set) -> dict:
    """One declared PLACE, as the catalog prints it: what the map says about it, and what the
    reading found there. Every key is present on every row -- an absent field is the empty
    string, never a missing key -- so a page can say *nothing was declared here* in words rather
    than rendering a hole a reader would read as a zero (Cardinal V)."""
    held = reading.classes.get(place.get(corpus.HOLDS))
    declared_ceiling = place.get(corpus.CEILING)
    unreadable = [r for r in residents if r.unreadable]
    undeclared = [r for r in residents if r.declares_nothing and not r.unreadable]
    return {
        "path": place[corpus.PATH],
        "holds": place.get(corpus.HOLDS) or "",
        "class_summary": (held or {}).get(corpus.SUMMARY, ""),
        # The EFFECTIVE cap, and whether the place stated it. A place that states none is capped
        # by the vocabulary's own default row, which a reader can recompute from the two
        # declarations and nothing else (ADR-019 amendment 1).
        "ceiling": declared_ceiling or reading.default_ceiling[collection.IDENTITY],
        "ceiling_declared": declared_ceiling or "",
        "writer": place.get(corpus.WRITER) or "",
        "lifecycle": place.get(corpus.LIFECYCLE) or "",
        "index": place.get(corpus.INDEX) or "",
        "index_missing": bool(entry is not None and not entry.present),
        # Read off the declared ROOT filter the graph was walked with -- never off a field name
        # spelled here, because which declaration makes a place an entry is the host's word.
        "entry": id(place) in rooted,
        "read_when": list(place.get(corpus.READ_WHEN) or []),
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
    reading = corpus.read(ctx, params)
    graph = routegraph.routes(ctx, reading, params.get(corpus.ROOTS))
    planes = corpus.vocabulary(ctx, params[corpus.PLANES])

    residents_of: dict = {}
    for resident in reading.residents:
        residents_of.setdefault(id(resident.place), []).append(resident)
    indexes = {id(entry.place): entry for entry in graph.indexes}
    rooted = {id(row) for row in graph.rooted_places}

    held: dict = {}
    outside: list = []
    placed: list = []
    for place in sorted(reading.places, key=lambda row: row[corpus.PATH]):
        row = _place_row(reading, place, residents_of.get(id(place), []),
                         indexes.get(id(place)), rooted)
        placed.append(row)
        where = (reading.classes.get(place.get(corpus.HOLDS)) or {}).get(corpus.PLANE)
        (held.setdefault(where, []) if where in planes else outside).append(row)

    sections = [{
        "id": identity,
        "summary": plane.get(corpus.SUMMARY, ""),
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
                        "owns": corpus.listed(resident.declares(corpus.OWNS))})

    successions = [
        {"path": resident.path, "states": stated, "names": named}
        for resident in reading.residents
        for stated in (corpus.SUPERSEDES, corpus.SUPERSEDED_BY)
        for named in corpus.listed(resident.declares(stated))
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
                             key=lambda row: row[corpus.RANK])[collection.IDENTITY],
        "indexes": [{"place": entry.place[corpus.PATH], "index": entry.index or "",
                     "declared": entry.place.get(corpus.INDEX) or "", "present": entry.present,
                     "documents": len(entry.residents)}
                    for entry in sorted(graph.indexes, key=lambda e: e.place[corpus.PATH])],
        "successions": successions,
        "unreadable_documents": [{"path": resident.path, "why": resident.unreadable}
                                 for resident in reading.unreadable_documents],
        "missing_places": [{"path": place[corpus.PATH]}
                           for place in sorted(reading.missing_places, key=lambda p: p[corpus.PATH])],
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
RESOLVES = {VIEW: projected}
