"""doctor -- prove the enforcement layer FIRES: a throwaway violation through every served hook.

`check` proves each gate bites its own specimen (calibration). That does not prove the CHAIN a product
runs -- the pinned kit's entry point, the surface's hands, the judge -- refuses a real edit. So this
verb hands each served surface's judge the event its product would write, carrying a declared gate's
own specimen, exactly as the product's hook command runs it (the pinned kit, `--surface`), and expects
the surface's refusal. It writes nothing to the tree: the judge is asked as a CANARY, so no observation
or claim is recorded. What a product actually fired is a different fact, read from the hook receipts. A
control outside the tree that only a person sets (a surface's `controls`) is named NOT ASSERTED, with the
exact command the person runs; the kit never runs it.
"""

from __future__ import annotations

import json
import subprocess
import sys

import declared
import hooks
import reference
import serving

SUMMARY = "prove every served hook refuses a throwaway violation, and read what each product fired"
MUTATES = False
REQUIRES_APPROVED_HOST = True
GATES = ({declared.CONTRACT: "edit-gate"}, "gates")


def _stdin(hand: dict, path: str, text: str) -> str:
    if hand.get("carries") == "patch":
        return f"diff --git a/{path} b/{path}\n+++ b/{path}\n+{text}\n"
    event: dict = {}
    for key, value in ((hand["paths"][0], path), (hand["texts"][0], text)):
        here = event
        parts = key.split(".")
        for part in parts[:-1]:
            here = here.setdefault(part, {})
        here[parts[-1]] = value
    return json.dumps(event)


def _controls(ctx, served: set) -> None:
    """What no hook can prove: a control outside the tree only a person sets. Named, with the person's
    exact command, and never reported as either state -- the kit neither sets nor reads it."""
    for surface in declared.rules(ctx, *hooks.SURFACES):
        if surface["id"] in served:
            for control in surface.get("controls", []):
                print(f"  NOT ASSERTED  {surface['id']}: {control['id']} -- {control['says']} A person with the "
                      f"rights runs:\n    {control['command']}")


def run(ctx, args) -> int:
    gates = declared.rules(ctx, *GATES)
    canary = next((g for g in gates if g["paths"] == ".*"), gates[0] if gates else None)
    served = serving.served_surfaces(ctx, ctx.enabled_capabilities())
    if canary is None:
        print("doctor: this host declares no edit gate, so there is nothing a hook could refuse")
        _controls(ctx, served)
        return 0
    cli = ctx.workspace.path(reference.runs_from(ctx)) / "interpreters" / "cli.py"
    dead = 0
    for surface in declared.rules(ctx, *hooks.SURFACES):
        hand = surface.get("hands")
        if surface["id"] not in served:
            continue
        if not hand:  # served with no hook hand: no canary can be fired through it, and that is said
            print(f"  UNTESTED  {surface['id']}: served, and declares no hook hand a canary could be fired through")
            continue
        if not cli.is_file():  # the path the hook runs is the one judged -- never the kit's own in its place
            dead += 1
            print(f"  DEAD  {surface['id']}: the hook runs {cli}, which is not there")
            continue
        ran = subprocess.run([sys.executable, "-I", "-B", str(cli),
                              "judge", "--root", str(ctx.workspace.root), "--surface", surface["id"], "--canary"],
                             input=_stdin(hand, canary["proves"]["path"], canary["proves"]["text"]),
                             capture_output=True, text=True, encoding="utf-8")
        live = ran.returncode == hand["refusal"]["exit"]
        dead += 0 if live else 1
        fired = hooks.receipts(ctx, surface["id"], fired_only=True)
        last = fired[-1]["at"] if fired else "never"
        print(f"  {'LIVE' if live else 'DEAD'}  {surface['id']}: {canary['id']} refused with exit {ran.returncode} "
              f"(expects {hand['refusal']['exit']}); {len(fired)} receipt(s), last {last}")
        if not live and ran.stderr.strip():  # why it did not refuse, in its own words
            print("        " + ran.stderr.strip().replace("\n", "\n        "))
    _controls(ctx, served)
    return 1 if dead else 0
