"""A reference to a record's own declared limit: has it been spent?

ADR-020 decision 9, joined to decision 8. A limit found spent is a MACHINE-DECIDABLE fact -- the
amount was declared on the record, what has been consumed is read from what the system already
writes, and the comparison is arithmetic. So it is never set by hand: a passage that anybody could
type would mean only that somebody said so, and every reading beside it would become decoration.

What this resolver decides and what it may never do are two different sentences, and the second
one is the longer:

  * it DECIDES one thing -- whether what has been consumed stands past what was undertaken -- and
    reports the reading that produced the answer, so the number can be contradicted rather than
    believed;
  * it may never RAISE the limit. There is nowhere to raise it: the grammar of a limit is two
    inert fields, consumption is read and never written, and an extension is the owner betting
    again, on the record, which is a different act from continuing;
  * it may never END the work. A machine that stopped a piece of work would be deciding it was not
    worth finishing, and that is the one judgement the owner actually keeps;
  * it may never RESUME anything. Nothing here computes a way back out.

What it decides is therefore ONLY a passage INTO somewhere the line has stopped -- and the way out
of there is a door, declared as a door, held by a principal, forever unratchetable. A warning that
let the work carry on was rejected on measurement: it is a silent extension with a paper trail,
which is what every budget that does not bind degenerates into.

A record that declares no limit reads as NO READING, and that is the honest answer rather than a
convenience: nothing was undertaken, so nothing can have been overspent, and a resolver that
answered *not spent* there would be reporting a limit nobody set as a limit being kept. A limit
declared in a unit nothing installed here can read is no reading either, for the sharper version
of the same reason -- an unmeasurable limit looks exactly like one that is being honoured, and
that is the single failure invisible from where the reader stands.
"""

from __future__ import annotations

import appetite
import collection
import criteria


def _spent(request) -> criteria.Verdict:
    record = request.subject
    limit = appetite.declared_by(record)
    if limit is None:
        return criteria.Verdict.unreadable(
            f"record {record.get(collection.IDENTITY)!r} declares no limit, so there is nothing "
            f"here that can have been spent. Nothing was observed and nothing is claimed in "
            f"either direction"
        )
    reading = appetite.spent(request.ctx, record, limit[appetite.UNIT])
    if reading.amount is None:
        return criteria.Verdict.unreadable(
            f"a limit of {limit[appetite.AMOUNT]} {limit[appetite.UNIT]!r} is declared, and "
            f"{reading.reading}"
        )
    return criteria.Verdict(
        reading.amount > limit[appetite.AMOUNT],
        f"{limit[appetite.AMOUNT]} {limit[appetite.UNIT]!r} was undertaken and {reading.reading}"
    )


RESOLVERS = {"appetite-spent": _spent}
