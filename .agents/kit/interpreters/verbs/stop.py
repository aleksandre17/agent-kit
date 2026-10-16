"""stop -- the hook before a session ends: the continuity capsule it leaves must keep its contract.

The capsule is the one handoff the next session reads (the shared-tree bundle). A session that ends
over a capsule that breaks its contract -- a field missing, two things in progress, the seed deleted --
leaves the next one a handoff it cannot read, and nobody finds out until then. So where the host
takes a capsule, the stop is refused with the reason, and the session goes on to repair it. A host
that takes no capsule is never held here (and is served no stop hook at all). Blocking: a stop this
hook cannot judge is refused; the product bounds how often a stop may be refused in a row.
"""

from __future__ import annotations

import sys

import capsule  # the verb that owns the capsule: its seat, its contract, its refusal
import hooks

SUMMARY = "before a session ends: the continuity capsule it leaves must keep its contract (blocking)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.BLOCKING
STDOUT_IS_THE_PRODUCTS = True


def run(ctx, args) -> int:
    hand = hooks.hand_of(ctx, getattr(args, "surface", None))
    sys.stdin.read()
    seat = next((i["target"] for c in ctx.enabled_capabilities() for i in c.installs
                 if i.get("validates") == capsule.CONTRACT), None)
    if seat is None:
        return 0
    try:
        if not ctx.workspace.exists(seat):
            raise capsule.CapsuleRefused(f"the continuity capsule {seat} is missing; `render` seeds it again")
        capsule._validated(ctx, ctx.workspace.read_json(seat), seat)
    except (capsule.CapsuleRefused, ValueError) as refused:
        print(f"stop: REFUSED [{capsule.CapsuleRefused.code}] -- {refused}. Repair the handoff before ending: "
              f"write the next revision with `capsule --write <file> --rev <the revision on disk>`.", file=sys.stderr)
        return hand["refusal"]["exit"]
    return 0
