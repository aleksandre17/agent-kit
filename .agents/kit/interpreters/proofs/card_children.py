"""A reference to everything that hangs UNDER a record: does each of them satisfy what is asked?

This is how a record that was decomposed is read from what it was decomposed into, and it is the
reason no rung needs a name (ADR-020 decision 5). The referent is the FIELD the edge is drawn in,
so the depth of the walk is a fact about the records and never about this module: one record
below or four, the reading is the same reading and nothing here counts levels.

What each of them must satisfy is DECLARED beside the reference, as a reference of its own, and
resolved back through the one registry -- so this module holds no condition, knows no other kind
of proof by name, and is not the file that changes when a new way of proving something arrives
(Cardinal IV). The reading it returns is the same three-valued arithmetic a record's own criteria
already use, for the same reason:

  * a record nothing hangs under holds. Nothing is below it, so nothing below it is unmet -- and
    a leaf is the ordinary case, not a wall;
  * one descendant measurably refuted refutes the whole reading, and it still says how many of
    the others could not be read, so the weaker fact is not swallowed by the stronger;
  * otherwise one descendant that could not be read makes the whole reading unreadable. Never a
    refutation: nothing was observed about the work, only about the reading.

A host whose records cannot be reached from here gets no reading at all, which is the honest
answer and never an empty set of descendants. An empty set would report a record whose parts were
never looked for as a record that has none -- the fabricated zero Cardinal V exists to refuse.
"""

from __future__ import annotations

import collection
import criteria
import lineage

#: What the reference calls the condition each descendant is held to. Named here because it is
#: this kind's own parameter; the GRAMMAR of what goes in it belongs to the criterion that
#: declares one and is not restated.
EACH = "each"


def _descendants_all_hold(request) -> criteria.Verdict:
    records = lineage.among(request.ctx)
    if records is None:
        return criteria.Verdict.unreadable(
            "the records this edge would be read among cannot be reached from here, so nothing "
            "below this one was looked for. Nothing was observed, so nothing is claimed"
        )
    asked = request.params.get(EACH)
    if asked is None:
        return criteria.Verdict.unreadable(
            f"this reference names no {EACH!r}, so there is nothing to hold a descendant to; "
            f"a reading of everything below a record that asks nothing of any of them is not a "
            f"reading"
        )
    below = lineage.descendants_of(records, request.subject.get(collection.IDENTITY), request.ref)
    if not below:
        return criteria.Verdict(
            True, f"nothing hangs under this record by {request.ref!r}, so nothing below it is "
                  f"unmet"
        )
    readings = [(record, request.about(asked, record)) for record in below]
    refuted = [(r, v) for r, v in readings if v.holds is False]
    unread = [(r, v) for r, v in readings if v.holds is None]
    counted = (f"{len(readings) - len(refuted) - len(unread)} of {len(readings)} record(s) below "
               f"this one were proved by what this reference asks of each; {len(refuted)} were "
               f"refuted and {len(unread)} could not be read")
    told = "; ".join(f"{record.get(collection.IDENTITY)!r} -- {verdict.reading}"
                     for record, verdict in (refuted or unread))
    if refuted:
        return criteria.Verdict(False, counted + ": " + told)
    if unread:
        return criteria.Verdict.unreadable(counted + ": " + told)
    return criteria.Verdict(True, counted)


RESOLVERS = {"descendants-all-hold": _descendants_all_hold}
