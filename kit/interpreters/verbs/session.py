"""session -- the hook at a session's start: ONE context line the product adds before the first prompt.

A session starts knowing nothing but its always-loaded briefing. What it needs beyond that, cheaply, is
where it stands: which kit governs the tree, how a change is proven here, and -- where the host keeps a
continuity capsule -- the handoff the last session left (its revision, its state, the one thing in
progress, the exact next action). One line, computed at zero model tokens; a pointer to the capsule,
never a copy of it. How the product takes the line is its surface's `hands.context`; a surface that
declares none is handed nothing, and the verb says so on stderr. Advisory: a start is never refused.
"""

from __future__ import annotations

import json
import sys

import capsule  # the verb that owns the capsule: its seat, its contract, its refusal
import hooks

SUMMARY = "at a session's start: one context line -- the kit, how a change is proven, the capsule's handoff (advisory)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.ADVISORY
STDOUT_IS_THE_PRODUCTS = True


def line(ctx) -> str:
    vendor = ctx.manifest.plane("vendor")
    said = [f"kit {ctx.manifest.version} governs this tree: the briefing carries its laws and commands; "
            f"`python {vendor}/interpreters/cli.py check --root .` proves a change"]
    seat = next((i["target"] for c in ctx.enabled_capabilities() for i in c.installs
                 if i.get("validates") == capsule.CONTRACT), None)
    if seat is not None:
        if not ctx.workspace.exists(seat):
            said.append(f"the continuity capsule {seat} is missing -- `render` seeds it again")
        else:
            held = ctx.workspace.read_json(seat)
            wip = "; in progress: " + held["wip"][0] if held.get("wip") else ""
            said.append(f"continuity capsule {seat} rev {held.get(capsule.REV)} ({held.get('handoff')}): "
                        f"next -- {held.get('next_action')}{wip}")
    return ". ".join(said) + "."


def run(ctx, args) -> int:
    hand = hooks.hand_of(ctx, getattr(args, "surface", None))
    sys.stdin.read()
    shape = hand.get("context")
    if shape is None:
        print(f"session: the surface {args.surface!r} declares no `hands.context`, so no context line is handed "
              f"to it", file=sys.stderr)
        return 0
    print(shape["stdout"].replace("{context}", json.dumps(line(ctx))[1:-1]))
    return 0
