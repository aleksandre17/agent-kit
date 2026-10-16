"""doctor -- prove the enforcement layer FIRES: a throwaway violation through every served hook.

`check` proves each gate bites its own specimen (calibration). That does not prove the CHAIN a product
runs -- the pinned kit's entry point, the surface's hands, the judge -- refuses a real edit. So this
verb hands each served surface's judge the event its product would write, carrying a declared gate's
own specimen, exactly as the product's hook command runs it (the pinned kit, `--surface`), and expects
the surface's refusal. It writes nothing to the tree: the judge is asked as a CANARY, so no observation
or claim is recorded. What a product actually fired is a different fact, read from the hook receipts.
"""

from __future__ import annotations

import json
import subprocess
import sys

import declared
import hooks
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


def run(ctx, args) -> int:
    gates = declared.rules(ctx, *GATES)
    canary = next((g for g in gates if g["paths"] == ".*"), gates[0] if gates else None)
    if canary is None:
        print("doctor: this host declares no edit gate, so there is nothing a hook could refuse")
        return 0
    cli = ctx.workspace.path(ctx.manifest.plane("vendor")) / "interpreters" / "cli.py"
    served = serving.served_surfaces(ctx, ctx.enabled_capabilities())
    dead = 0
    for surface in declared.rules(ctx, *hooks.SURFACES):
        hand = surface.get("hands")
        if not hand or surface["id"] not in served:
            continue
        ran = subprocess.run([sys.executable, "-I", "-B", str(cli if cli.is_file() else ctx.manifest.root / "interpreters" / "cli.py"),
                              "judge", "--root", str(ctx.workspace.root), "--surface", surface["id"], "--canary"],
                             input=_stdin(hand, canary["proves"]["path"], canary["proves"]["text"]),
                             capture_output=True, text=True, encoding="utf-8")
        live = ran.returncode == hand["refusal"]["exit"]
        dead += 0 if live else 1
        fired = hooks.receipts(ctx, surface["id"], fired_only=True)
        last = fired[-1]["at"] if fired else "never"
        print(f"  {'LIVE' if live else 'DEAD'}  {surface['id']}: {canary['id']} refused with exit {ran.returncode} "
              f"(expects {hand['refusal']['exit']}); {len(fired)} receipt(s), last {last}")
    return 1 if dead else 0
