"""claim -- take, list, release or break a claim on paths, so two principals on one tree cannot erase
each other's unmerged work (ADR-022 decision 7).

    python .agents/kit/interpreters/cli.py claim --root . --by <principal> --path a,b --reason "..."
    python .agents/kit/interpreters/cli.py claim --root . --by <principal> --relinquish
    python .agents/kit/interpreters/cli.py claim --root . --by <principal> --relinquish --break-lock <who>
    python .agents/kit/interpreters/cli.py claim --root .

A principal is the runtime a served surface names, by its descriptor id, or a person. A claim stands
until its owner releases it or a person breaks it BY NAME -- never by elapsed time (ADR-007) -- and
the one judge refuses another principal's write under it.
"""

from __future__ import annotations

import claims

SUMMARY = "take, list, release or break by name a claim on paths, which the judge holds other writers to"
MUTATES = False
REQUIRES_APPROVED_HOST = True

ARGUMENTS = [
    ("--relinquish", {"action": "store_true", "help": "release this principal's standing claim"}),
    ("--reason", {"default": None, "help": "why the paths are claimed -- read by whoever the claim blocks"}),
]


def run(ctx, args) -> int:
    now = ctx.clock.now()
    if getattr(args, "relinquish", False):
        held = claims.release(ctx, args.by, now, broken_by=getattr(args, "break_lock", None))
        word = f"BROKEN by {held['broken_by']}" if held.get("broken_by") else "RELEASED"
        print(f"claim: {word}  {held['principal']}  {held['paths']}")
        return 0
    if args.path:
        held = claims.take(ctx, args.by, args.path, getattr(args, "reason", None), now)
        print(f"claim: TAKEN  {held['principal']}  {held['paths']}  -- {held['reason']}")
        return 0
    standing = claims.standing(ctx)
    if not standing:
        print("claim: no claim stands on this host")
    for held in standing:
        print(f"claim: STANDING  {held['principal']}  {held['paths']}  since {held['taken_at']}  -- {held['reason']}")
    return 0
