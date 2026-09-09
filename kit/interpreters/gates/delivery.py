"""Gate kinds for a governed collection -- capacity, and staleness.

Both read the SAME functions the `move` verb reads, so a host can never be refused a move it
would afterwards pass a gate with, nor pass a gate on a state a move would have refused. Two
mechanisms keeping one promise separately is not a promise; it is a coincidence with a good
record.

Neither gate carries a number. The limits are the host's, in the file the capability declared and
seeded, and the gate merely reports what the declaration says about what is on disk. The clock
arrives through the port, so the reading states its moment and a test can hold it still.
"""

from __future__ import annotations

import collection
import lifecycle as lifecycle_module


def _governed(ctx):
    capabilities = ctx.enabled_capabilities()
    return lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))


def _capacity_within_limit(ctx, params):
    return lifecycle_module.capacity_failures(_governed(ctx))


def _state_age_within_limit(ctx, params):
    """The Clock's first time-dependent rule. A card that has sat too long is REPORTED with the
    moment the reading was taken -- never silently moved, because a passage records who made it
    and no machine may be that who."""
    return lifecycle_module.age_failures(_governed(ctx), ctx.clock.now())


KINDS = {
    "capacity-within-limit": _capacity_within_limit,
    "state-age-within-limit": _state_age_within_limit,
}
