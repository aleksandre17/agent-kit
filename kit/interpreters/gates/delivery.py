"""Gate kinds for a governed collection -- capacity, staleness, and a limit declared on one record.

Both read the SAME functions the `move` verb reads, so a host can never be refused a move it
would afterwards pass a gate with, nor pass a gate on a state a move would have refused. Two
mechanisms keeping one promise separately is not a promise; it is a coincidence with a good
record.

Neither gate carries a number. The limits are the host's, in the file the capability declared and
seeded, and the gate merely reports what the declaration says about what is on disk. The clock
arrives through the port, so the reading states its moment and a test can hold it still.
"""

from __future__ import annotations

import appetite as appetite_module
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


def _appetite_within_limit(ctx, params):
    """The third limit, and the first one declared on a single record rather than on a whole
    state. What has been spent against it is READ from receipts the host already writes, so this
    reading runs nothing and measures nothing twice.

    It is REPORTED and never acted on. The exit from a limit that has been spent is a decision by
    the record's owner, taken on the record, and this gate names that door instead of opening it:
    a machine that extended the limit would have granted the extension the owner never gave, and a
    machine that ended the work would have decided it was not worth finishing. A record that
    declares no limit is passed over, which is every record in existence on the day this ships.
    """
    return appetite_module.unkept(ctx, _governed(ctx).members.value)


KINDS = {
    "capacity-within-limit": _capacity_within_limit,
    "state-age-within-limit": _state_age_within_limit,
    "appetite-within-limit": _appetite_within_limit,
}

#: Every kind here judges by reading the governed records: none of them may prove one (ADR-025 decision 16).
READS_THE_RECORDS = {kind: True for kind in KINDS}
