"""A reference to the criteria a record carries: do ALL of them hold?

One reference standing for many. It is the same grammar as any other -- a kind and a referent,
where the referent is the FIELD the criteria live in -- so a passage that is decided by a machine
declares its condition in exactly the words a criterion declares its proof, and the interpreter
that reads it holds no condition of its own (ADR-020 decisions 7 and 8).

Three readings, and the arithmetic between them is the whole point:

  * a record that declares no criterion holds. Nothing was stated, so nothing is unmet -- and a
    young record that nobody has shaped yet is a legal state, never a wall;
  * one criterion measurably refuted makes the whole reading a refutation, and it says how many
    of the others could not be read at all, so the weaker fact is not swallowed by the stronger;
  * otherwise, one criterion that could not be read makes the whole reading unreadable. Not a
    failure: nothing was observed, and a machine that treated an absence as a refutation would be
    reporting a broken reference as broken work.

Every nested reference is resolved back through the one registry, carrying the trail, so a record
whose criteria point at the record itself is caught by the trail rather than by a recursion limit.
"""

from __future__ import annotations

import collection
import criteria


def _criteria_all_hold(request) -> criteria.Verdict:
    readings = [
        (item, request.about(item.get(criteria.PROOF)))
        for item in (request.subject.get(request.ref) or [])
    ]
    if not readings:
        return criteria.Verdict(
            True, f"nothing is declared in {request.ref!r}, so nothing stated there is unmet"
        )
    refuted = [item for item, verdict in readings if verdict.holds is False]
    unread = [item for item, verdict in readings if verdict.holds is None]
    held = len(readings) - len(refuted) - len(unread)
    counted = (f"{held} of {len(readings)} in {request.ref!r} were proved by the reference each "
               f"names; {len(refuted)} were refuted and {len(unread)} could not be read")
    if refuted:
        return criteria.Verdict(False, counted + ": " + "; ".join(
            f"{item.get(collection.IDENTITY)!r} -- {verdict.reading}"
            for item, verdict in readings if verdict.holds is False))
    if unread:
        return criteria.Verdict.unreadable(counted + ": " + "; ".join(
            f"{item.get(collection.IDENTITY)!r} -- {verdict.reading}"
            for item, verdict in readings if verdict.holds is None))
    return criteria.Verdict(True, counted)


RESOLVERS = {"criteria-all-hold": _criteria_all_hold}
