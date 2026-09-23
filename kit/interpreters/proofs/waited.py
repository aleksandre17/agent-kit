"""A reference to how long a record has stood where it stands: has it waited past a stated number?

ADR-020 decision 9, second half. A record that waits beyond what a host will tolerate leaves by a
declared PASSAGE, said out loud and dated, and from there by another into what is dead by
location. Not a cron, not a cleanup task, and not a discretionary tidy-up -- three mechanisms that
each remove a record from view without the removal being a move anybody made. This resolver is the
reading such a passage is decided by; the passage itself, and where it goes, are the host's
lifecycle declaration and are named nowhere here.

The reading is of the WAIT, not of the life. The moment counted from is the moment the record
entered the state it is in now -- derived from its own record of its passages, never stored beside
it -- and it is deliberately NOT the moment it began. That other number exists, it is read by the
unit of spend that counts a record's whole life against a limit, and it answers a different
question. One number answering two questions is how two readings of one reality begin to disagree
while each goes on reading as correct (Cardinal III). Waiting and spending keep different clocks.

The number to have been exceeded is the DECLARATION's, carried in the reference's own parameters.
This kit ships no such number and no default for one: a threshold a framework chose is a threshold
nobody undertook. A reference that states none takes no reading at all, which is the honest answer
and never a pass -- an absent threshold that resolved to *not yet* would retire nothing while
reading exactly like a host whose records are all fresh.

Nothing here archives, deletes, moves or cancels anything. It answers one question about one
record and the answer travels back to the passage that asked.
"""

from __future__ import annotations

import collection
import criteria
import lifecycle as lifecycle_module

#: The parameter this reference is configured by, in the unit the reading is taken in. The word is
#: this resolver's own and is published with the kind it answers, exactly as a unit of spend is.
DAYS = "days"


def _waited(request) -> criteria.Verdict:
    record = request.subject
    limit = request.params.get(DAYS)
    if not isinstance(limit, (int, float)) or isinstance(limit, bool):
        return criteria.Verdict.unreadable(
            f"this reference states no {DAYS!r} to have been exceeded, so there is no threshold "
            f"to read against; it states {limit!r}. Nothing was observed, and an unstated "
            f"threshold is not a threshold that has not been reached"
        )
    try:
        since = lifecycle_module.entered_at(record)
    except KeyError:
        return criteria.Verdict.unreadable(
            f"record {record.get(collection.IDENTITY)!r} states neither a passage nor a moment it "
            f"began, so there is no moment to count a wait from"
        )
    now = request.ctx.clock.now()
    try:
        waited = lifecycle_module.days_between(since, now)
    except lifecycle_module.LifecycleError as exc:
        return criteria.Verdict.unreadable(
            f"the moment this record last moved cannot be read -- {exc}"
        )
    return criteria.Verdict(
        waited > limit,
        f"it has stood where it stands for {waited:.1f} {DAYS} since {since}, against the "
        f"{limit} this reference names; reading taken at {now}"
    )


RESOLVERS = {"waited-longer-than": _waited}
