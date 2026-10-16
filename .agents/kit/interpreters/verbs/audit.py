"""audit -- every edit gate in force, over the whole tree: the violations already standing in it.

`judge` holds what a change INTRODUCES; a line that was there before the gate is never seen by it.
This verb runs the same calibrated gates -- the host's own and every taken policy's -- over the full
text of every tracked file each gate's `paths` reach, and prints path:line, the gate and its
`because`. It never prints the matched text: a secret it finds is located, never repeated.

A known violation is acknowledged by declaration (`known-violations`: gate, path, tracking, until?),
never by silencing the gate; it prints KNOWN with its tracking. An acknowledgement whose `until` has
passed is a finding again (EXPIRED); one that matches nothing is STALE, to be removed. Exit 1 when a
finding stands unacknowledged (ADR-024 decision 20).
"""

from __future__ import annotations

import standing

SUMMARY = "every edit gate in force over every tracked file: violations already in the tree, known ones by declaration"
MUTATES = False
REQUIRES_APPROVED_HOST = True


def _until(row) -> str:
    return f" until {row['until']}" if row.get("until") else ""


def run(ctx, args) -> int:
    found = standing.audit(ctx)
    for f in found.open:
        print(f"  FINDING  {f.where}  {f.gate} -- {f.because}")
    for f in found.expired:
        print(f"  EXPIRED  {f.where}  {f.gate} -- {f.because} (acknowledged as {f.acknowledged['tracking']}"
              f"{_until(f.acknowledged)}, which has passed)")
    for f in found.known:
        print(f"  KNOWN    {f.where}  {f.gate} -- tracked as {f.acknowledged['tracking']}{_until(f.acknowledged)}")
    for row in found.stale:
        print(f"  STALE    {row['path']}  {row['gate']} -- acknowledged as {row['tracking']}, and the tree "
              f"holds no such violation: remove the acknowledgement")
    for gate in found.unjudged:
        print(f"  NOT APPLIED  {gate} -- uncalibrated, and failing `check`")
    print(f"audit: {found.counts()}")
    return 1 if (found.open or found.expired) else 0
