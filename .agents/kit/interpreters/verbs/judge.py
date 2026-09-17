"""judge -- the hook: one edit a runtime hands over, judged against this host's declared gates.

A runtime's hook runs this verb from the host's PINNED kit, passing the product's event on stdin
and naming the surface it was served through. Everything product-shaped arrives from that
surface's `hands` declaration -- where the edited paths and introduced text sit in the event,
and which exit code tells the product no. Everything policy-shaped arrives from the host's edit
gates. The verb holds neither: it is the interpreter half of Cardinal IV, and a new product or a
new gate costs it no edit.

An edit whose target cannot be read is REFUSED, never waved through: an unjudged write is not an
allowed one.
"""

from __future__ import annotations

import json
import sys

import check as check_verb
import declared
import edits as edits_module
from errors import KitError

SUMMARY = "judge one edit a runtime hook hands over, against this host's declared edit gates"
MUTATES = False
REQUIRES_APPROVED_HOST = True

#: The contract a surface document keeps -- the schema's own name, as every reader of it uses.
SURFACES = {"validates": "runtime-surface"}


class JudgeError(KitError):
    """The hook named a surface no taken adapter declares, or one that declares no hand."""

    code = "KIT0043"


def _hand(ctx, surface_id: "str | None") -> dict:
    surfaces = {row["id"]: row for row in declared.rules(ctx, SURFACES, "surfaces")}
    surface = surfaces.get(surface_id or "")
    if surface is None or "hands" not in surface:
        raise JudgeError(
            f"the hook asks to be judged through the surface {surface_id!r}, and no taken adapter "
            f"declares that surface with a `hands` block (declared: {sorted(surfaces)}). Nothing "
            f"states where this product puts the edit, so nothing can be judged.")
    return surface["hands"]


def run(ctx, args) -> int:
    hand = _hand(ctx, getattr(args, "surface", None))
    no = hand["refusal"]["exit"]
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else None
    except ValueError:
        event = None
    handed = edits_module.edits_in(event, hand) if event is not None else []
    if not handed:
        print("judge: REFUSED -- the event names no edited path this surface declares, so nothing "
              "could be judged; an unjudged write is not an allowed one.", file=sys.stderr)
        return no
    within, outside = [], []
    for path, text in handed:
        try:
            rel = edits_module.host_relative(ctx.workspace.path("."), path)
        except edits_module.Unplaceable as exc:
            print(f"judge: REFUSED -- {exc}; an edit that cannot be placed is not one that lies "
                  f"outside this host.", file=sys.stderr)
            return no
        (within.append((rel, text)) if rel is not None else outside.append(path))
    refused, unjudged = [], []
    judges = check_verb.registry("EDITS")
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            if gate["kind"] in judges:
                found, blind = judges[gate["kind"]](ctx, gate.get("params", {}), within)
                refused += found
                unjudged += blind
    for path in outside:
        print(f"judge: {path} lies outside this host; its gates do not reach it")
    if unjudged:
        print(f"judge: NOT APPLIED (uncalibrated, and failing `check`): {', '.join(unjudged)}",
              file=sys.stderr)
    if refused:
        for path, rule_id, because, instead in refused:
            print(f"judge: REFUSED  {path}  {rule_id} -- {because} Instead: {instead}", file=sys.stderr)
        return no
    print(f"judge: {len(within)} edited path(s) pass every edit judgement this host declares")
    return 0
