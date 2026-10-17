"""A reference to the cards a record comes AFTER: has every one of them finished?

ADR-025 decision 9. A program is a card tree with an order, and its phase entry gate is this reading:
a card enters the work only when the cards it is declared to come after stand in a state the
lifecycle marks closed. The referent is the FIELD the order is drawn in, so the field's name is the
declaration's and never this module's; which states are closed is the lifecycle's.

  * every named card closed -- held (a card that names none comes after nothing, which holds);
  * a named card not yet closed -- refuted, naming it and where it stands;
  * a named card this host does not hold -- unreadable: an order pointing nowhere proves nothing.
"""

from __future__ import annotations

import collection
import criteria
import lifecycle as lifecycle_module


def _predecessors_closed(request) -> criteria.Verdict:
    ctx, subject = request.ctx, request.subject
    named = (subject.get(request.ref) or []) if isinstance(subject, dict) else []
    if not named:
        return criteria.Verdict(True, f"nothing is named in {request.ref!r}, so this comes after nothing")
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    closed = {s["id"] for s in governed.states if s.get("closed")}
    held = {c["id"]: c for c in governed.members.value}
    missing = [n for n in named if n not in held]
    if missing:
        return criteria.Verdict.unreadable(f"{request.ref!r} names {missing}, which this host does not hold")
    open_ = [f"{n} ({held[n].get(governed.state_field)})" for n in named
             if held[n].get(governed.state_field) not in closed]
    if open_:
        return criteria.Verdict(False, f"it comes after {', '.join(open_)}, not yet finished")
    return criteria.Verdict(True, f"every card it comes after has finished: {', '.join(named)}")


RESOLVERS = {"predecessors-closed": _predecessors_closed}
