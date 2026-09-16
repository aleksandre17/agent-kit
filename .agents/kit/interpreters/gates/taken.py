"""Gate kind for what a host TOOK from outside the kit -- held, on every check, to its pin.

The door that pins a capability is walked once; this is the reading taken every time after it. It
re-measures every capability the kit's lock does not account for and fails on anything that is not
held to a pin: bytes that drifted, a version older than the one pinned, a capability this host has
never pinned. It does NOT re-run a verifier: authenticity is a reading taken at the door and dated
there, and integrity is what carries it forward -- a check that re-verified would make every check
depend on a tool and a trust root that the pin exists to make unnecessary.

It reports and never repairs, and it never re-pins: a gate that could take a fresh digest would
certify whatever it found. The measuring and the vocabulary are `provenance`'s; this only asks.
"""

from __future__ import annotations

import estate as estate_module
import provenance


def _pinned(ctx, params) -> list:
    recorded = estate_module.read(ctx)
    rows = provenance.survey(ctx, ctx.enabled_capabilities(), (recorded or {}).get("taken", []))
    provenance.report(ctx, rows)
    return [f"{row['state']}  {row['capability']}@{row['version']}  {row['digest']} -- "
            f"{provenance._says(ctx, 'states', row['state'], 'state')}"
            for row in rows if row["disposition"] not in (provenance.HOLD, provenance.CARRY)]


KINDS = {"provenance-pinned": _pinned}
