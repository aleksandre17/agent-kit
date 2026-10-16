"""Hooks -- a verb a product's hook runs: the surface's hands, its declared POSTURE, and its receipt.

A hook stands between a runtime and an act (an edit, a command, a spawn, a push). Three facts about it
are the kit's, the same for every hook and every product (ADR-024):

  * WHERE the product puts what is being done -- the surface's `hands`, read by dotted keys;
  * its POSTURE: a `blocking` hook that cannot decide -- a crash, an undeclared surface -- FAILS CLOSED
    with the surface's own refusal exit; an `advisory` one lets the act through and says why. A crash
    that a product reads as "non-blocking error" is the most expensive silence there is, so the entry
    point applies the posture, never the verb;
  * a RECEIPT on every exit path: a configured hook and a hook that RAN are different facts, and only a
    receipt proves the second. One line per invocation, runtime-local, in the observed plane.
"""

from __future__ import annotations

import json
import time

import declared
import ephemeral
from errors import KitError

BLOCKING, ADVISORY = "blocking", "advisory"
SURFACES = ({declared.CONTRACT: "runtime-surface"}, "surfaces")
#: Where receipts are kept, inside the observed plane.
RECEIPTS = "hooks"
#: The exit a blocking hook fails closed with where no surface states its own.
CLOSED = 2


class HookError(KitError):
    """A hook asked to act through a surface that declares no `hands` for it."""

    code = "KIT0078"


def hand_of(ctx, surface_id: "str | None") -> dict:
    surfaces = {row["id"]: row for row in declared.rules(ctx, *SURFACES)}
    surface = surfaces.get(surface_id or "")
    if surface is None or "hands" not in surface:
        raise HookError(
            f"the hook asks to act through the surface {surface_id!r}, and no taken adapter declares "
            f"that surface with a `hands` block (declared: {sorted(surfaces)}). Nothing states where "
            f"this product puts what it is doing, so nothing can be decided.")
    return surface["hands"]


def values_at(event, key: str) -> list:
    """Every value a dotted key reaches in an event; `*` fans over a list."""
    found = [event]
    for part in key.split("."):
        nxt = []
        for value in found:
            if part == "*" and isinstance(value, list):
                nxt += value
            elif isinstance(value, dict) and part in value:
                nxt.append(value[part])
        found = nxt
    return [v for v in found if isinstance(v, str)]


def first_of(event, keys: list) -> "str | None":
    for key in keys:
        found = values_at(event, key)
        if found:
            return found[0]
    return None


def failed_exit(ctx, surface_id, posture: str) -> int:
    """What a hook that could not decide exits with: its surface's refusal when blocking, 0 when not."""
    if posture != BLOCKING:
        return 0
    try:
        return hand_of(ctx, surface_id)["refusal"]["exit"]
    except Exception:  # noqa: BLE001 -- an unreadable surface still fails closed
        return CLOSED


def receipt(ctx, verb: str, surface_id, code, started: float, canary: bool = False) -> None:
    """One line, on every exit path. A fault writing it is swallowed: a receipt never changes a verdict."""
    try:
        rel = ephemeral.place(ctx, f"{RECEIPTS}/{surface_id or 'none'}.jsonl")
        path = ctx.workspace.path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps({"at": ctx.clock.now(), "verb": verb, "surface": surface_id, "exit": code,
                                  "ms": round((time.monotonic() - started) * 1000),
                                  **({"canary": True} if canary else {})}) + "\n")
    except Exception:  # noqa: BLE001
        pass


def receipts(ctx, surface_id, fired_only: bool = False) -> list:
    """Every receipt a surface's hooks left; `fired_only` drops the doctor's own canaries."""
    rel = ephemeral.place(ctx, f"{RECEIPTS}/{surface_id}.jsonl")
    if not ctx.workspace.exists(rel):
        return []
    rows = [json.loads(line) for line in ctx.workspace.read_text(rel).splitlines() if line.strip()]
    return [r for r in rows if not (fired_only and r.get("canary"))]
