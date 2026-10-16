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

import attestation
import claims
import declared
import edits as edits_module
import judgement
import placement
from errors import KitError

SUMMARY = "judge one edit a runtime hook hands over, against this host's declared edit gates"
MUTATES = False
REQUIRES_APPROVED_HOST = True

#: The contract a surface document keeps -- the schema's own name, as every reader of it uses.
SURFACES = {"validates": "runtime-surface"}
#: The schema's words: a hand whose stdin is a patch, and one whose empty event is admitted.
CARRIES_PATCH = "patch"
NOTHING_ADMITTED = "admitted"


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


#: This verb's stdout can belong to the product whose hook ran it (a decision it reads there), so the
#: entry point writes its own header to stderr (`cli.py`).
STDOUT_IS_THE_PRODUCTS = True


def _speaker(hand: dict):
    """(say, refuse, admit): where the judge's own lines go, and what it hands the product. A surface
    whose product reads the hook's DECISION on stdout declares the text; every other line then goes
    to stderr, so nothing but the decision is ever read as one."""
    refusal, admission = hand["refusal"], hand.get("admission") or {}
    speaks = "stdout" in refusal or "stdout" in admission

    def say(line: str) -> None:
        print(line, file=sys.stderr if speaks else sys.stdout)

    def refuse(*lines: str) -> int:
        for line in lines:
            print(line, file=sys.stderr)
        if "stdout" in refusal:
            print(refusal["stdout"].replace("{reason}", json.dumps(" ".join(lines))[1:-1]))
        return refusal["exit"]

    def admit(line: str) -> int:
        say(line)
        if "stdout" in admission:
            print(admission["stdout"])
        return 0

    return say, refuse, admit


def run(ctx, args) -> int:
    hand = _hand(ctx, getattr(args, "surface", None))
    say, refuse, admit = _speaker(hand)
    raw = sys.stdin.read()
    if hand.get("carries") == CARRIES_PATCH:
        event = raw  # the stdin IS the patch: the hook produced its own reading of the change
    else:
        try:
            event = json.loads(raw) if raw.strip() else None
        except ValueError:
            event = None
    handed = edits_module.edits_in(event, hand) if event is not None else []
    if not handed and hand.get("nothing") == NOTHING_ADMITTED:
        # DECLARED by the surface, never assumed: its grammar is complete, so an event naming no
        # path provably introduces no text (a change of pure deletions, or no change).
        return admit("judge: the change introduces no text in any path; this surface declares that "
                     "nothing introduced is nothing to refuse")
    if not handed:
        return refuse("judge: REFUSED -- the event names no edited path this surface declares, so "
                      "nothing could be judged; an unjudged write is not an allowed one.")
    within, outside = [], []
    for path, text in handed:
        try:
            rel = placement.host_relative(ctx.workspace.path("."), path)
        except placement.Unplaceable as exc:
            return refuse(f"judge: REFUSED -- {exc}; an edit that cannot be placed is not one that "
                          f"lies outside this host.")
        (within.append((rel, text)) if rel is not None else outside.append(path))
    # Who is writing: the runtimes served through this surface. Another principal's standing claim,
    # or a peer's admitted write inside the host's window, refuses before any gate is read (ADR-022).
    principals = attestation.served_through(ctx, getattr(args, "surface", None))
    contested = claims.refusals(ctx, principals, [rel for rel, _t in within], ctx.clock.now())
    if contested:
        return refuse(*(f"judge: REFUSED  {path}  -- {why}" for path, why in contested))
    # The gates are applied where that application has its one home, so this verb and the dispatch
    # port's admission on return cannot come to hold different rule sets (ADR-017 amendment 6).
    # What KIND of writer this is, by the classes of the runtimes served through the surface: a gate
    # may hold one class of writer to a rule another is not held to (`plane-held-by-its-writer`).
    ctx.writers = attestation.classes_through(ctx, getattr(args, "surface", None))
    refused, unjudged = judgement.refusals(ctx, within)
    for path in outside:
        say(f"judge: {path} lies outside this host; its gates do not reach it")
    if unjudged:
        print(f"judge: NOT APPLIED (uncalibrated, and failing `check`): {', '.join(unjudged)}",
              file=sys.stderr)
    if refused:
        # A refusal that happened is a record of what this runtime CAN be held to (ADR-022 decision 6).
        attestation.observe(ctx, getattr(args, "surface", None), attestation.REFUSED_WRITE,
                            [(p, r) for p, r, _b, _i in refused])
        return refuse(*(f"judge: REFUSED  {path}  {rule_id} -- {because} Instead: {instead}"
                        for path, rule_id, because, instead in refused))
    claims.recorded(ctx, principals, [rel for rel, _t in within], ctx.clock.now())
    return admit(f"judge: {len(within)} edited path(s) pass every edit judgement this host declares")
