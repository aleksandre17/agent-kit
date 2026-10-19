"""Elapsed time, read from the dated record itself -- the receipt every record already carries.

A record states the moment it came into being and, from then on, every passage it has made with
the moment of each. That is written anyway, by the writer, for reasons that have nothing to do
with any limit -- so counting elapsed time against a declared limit runs nothing a second time and
creates no second home for a number (ADR-015 amendment 6).

WHICH stretch of that life is spent is the lifecycle's to say, not this module's (ADR-020
amendment 2). A lifecycle marks the states in which work SPENDS its appetite (`spends: true`); the
spend is the sum of the record's stays in those states, read from its own passages, and the stay
it is in now runs to the moment of the reading. So a card captured weeks before it was bet starts
at nothing, a card that landed stops spending the moment it landed, and a card parked on purpose
does not spend while it waits. The older reading answered neither half: from capture to now, it
charged the time a card waited to be chosen AND kept charging after the work was finished, so
every landed card with a limit turned red in the end.

A lifecycle that marks no such state keeps the reading this module has always taken -- the whole
life of the record, from the moment it states it began -- and the reading SAYS which of the two it
took, every time, so a number can be contradicted rather than believed.

Deliberately NOT the time since its last passage -- that number already exists, under the
staleness limit a host declares, and one number answering two different questions is how two
readings of one reality begin to disagree while each goes on reading as correct (Cardinal III).
"""

from __future__ import annotations

import appetite
import lifecycle as lifecycle_module

#: The word this module answers for. The join is by name, exactly as a kind of rule or a kind of
#: proof joins a declaration to the module that answers it.
UNIT = "day"


def _spending_states(ctx) -> set:
    """The states the governing lifecycle marks as spending -- read from its declaration, never
    named here. A world with no lifecycle to read answers with none, and the older reading stands."""
    try:
        states = lifecycle_module.declared_states(ctx.enabled_capabilities())
    except (AttributeError, lifecycle_module.LifecycleError):
        return set()
    return {state["id"] for state in states if state.get(lifecycle_module.SPENDS)}


def _stays(record: dict, now: str) -> list:
    """Each stay the record has made, as (state, from, until), from its own passages. The state it
    was created in is the one its first passage left, or the one it is in if it never moved."""
    history = record.get(lifecycle_module.HISTORY) or []
    state = history[0]["from"] if history else record.get("state")
    since = record[lifecycle_module.CREATED_AT]
    stays = []
    for passage in history:
        stays.append((state, since, passage["at"]))
        state, since = passage["to"], passage["at"]
    stays.append((state, since, now))
    return stays


def _elapsed(ctx, record) -> appetite.Spend:
    began = record.get(lifecycle_module.CREATED_AT)
    now = ctx.clock.now()
    if began is None:
        return appetite.Spend.unreadable(
            "this record states no moment it began, so no stretch of time can be counted from it"
        )
    spending = _spending_states(ctx)
    try:
        if not spending:
            elapsed = lifecycle_module.days_between(began, now)
            return appetite.Spend(
                elapsed,
                f"{elapsed:.1f} {UNIT}(s) have elapsed since {began}, reading taken at {now} -- "
                f"the whole life of the record, because its lifecycle marks no state that spends",
            )
        stays = [s for s in _stays(record, now) if s[0] in spending]
        spent = sum(lifecycle_module.days_between(start, until) for _, start, until in stays)
    except (KeyError, lifecycle_module.LifecycleError) as exc:
        return appetite.Spend.unreadable(
            f"the moments this record states cannot be read -- {exc}"
        )
    if not stays:
        # A measured zero, not an unreadable one: the passages were read, and none of them entered
        # a state that spends. Nothing has been undertaken yet, so nothing has been consumed.
        return appetite.Spend(
            0.0,
            f"0.0 {UNIT}(s) spent: the record has not entered a state that spends "
            f"({', '.join(sorted(spending))}), reading taken at {now}",
        )
    return appetite.Spend(
        spent,
        f"{spent:.1f} {UNIT}(s) spent in {', '.join(sorted({s[0] for s in stays}))} since "
        f"{stays[0][1]}, reading taken at {now}",
    )


READINGS = {UNIT: _elapsed}
