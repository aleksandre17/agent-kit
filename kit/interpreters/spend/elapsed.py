"""Elapsed time, read from the dated record itself -- the receipt every record already carries.

A record states the moment it came into being and, from then on, every passage it has made with
the moment of each. That is written anyway, by the writer, for reasons that have nothing to do
with any limit -- so counting elapsed time against a declared limit runs nothing a second time and
creates no second home for a number (ADR-015 amendment 6).

The window is the whole life of the record: from the moment it states it began, to the moment this
reading is taken. Deliberately NOT the time since its last passage -- that number already exists,
under the staleness limit this host declares, and one number answering two different questions is
how two readings of one reality begin to disagree while each goes on reading as correct
(Cardinal III). Waiting and spending are different truths and keep different numbers.

ADR-020 does not say WHEN an appetite's clock starts. This reading takes the only beginning that
can be named without naming a state, states it in its own words every time it is taken, and leaves
the contradiction visible rather than resolving it quietly in favour of whatever was convenient.
"""

from __future__ import annotations

import appetite
import lifecycle as lifecycle_module

#: The word this module answers for. The join is by name, exactly as a kind of rule or a kind of
#: proof joins a declaration to the module that answers it.
UNIT = "day"


def _elapsed(ctx, record) -> appetite.Spend:
    began = record.get(lifecycle_module.CREATED_AT)
    now = ctx.clock.now()
    if began is None:
        return appetite.Spend.unreadable(
            "this record states no moment it began, so no stretch of time can be counted from it"
        )
    try:
        elapsed = lifecycle_module.days_between(began, now)
    except lifecycle_module.LifecycleError as exc:
        return appetite.Spend.unreadable(
            f"the moment this record states it began cannot be read -- {exc}"
        )
    return appetite.Spend(
        elapsed,
        f"{elapsed:.1f} {UNIT}(s) have elapsed since {began}, reading taken at {now}",
    )


READINGS = {UNIT: _elapsed}
