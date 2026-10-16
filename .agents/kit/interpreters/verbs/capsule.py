"""capsule -- the CONTINUITY CAPSULE: one typed handoff between sessions and runtimes, written by
compare-and-swap so two writers on one tree never lose an update.

    ... cli.py capsule --root <host>                                   # show it, and validate it
    ... cli.py capsule --root <host> --write <new.json> --rev <n>      # replace revision n, atomically

Where two runtimes share one working tree (two products' sessions side by side), the handoff a
session leaves is read by the next one -- whichever product it runs on -- and a capsule overwritten by
a writer that read an older revision loses the other's decisions silently. So a write states the
revision it replaces: it lands only if that is still the revision on disk (CAS), under an exclusive
lock, and every landed write appends one line to the journal. A stale write is refused by name.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import ephemeral
from errors import KitError

SUMMARY = "show the continuity capsule, or replace one revision of it by compare-and-swap"
MUTATES = True
REQUIRES_APPROVED_HOST = True
SUBJECT = "continuity"
CONTRACT = "continuity-capsule"
REV = "capsule_rev"
ARGUMENTS = [
    ("--write", {"default": None, "help": "the new capsule (a JSON file) to write"}),
    ("--rev", {"default": None, "type": int, "help": "the revision on disk this write replaces (compare-and-swap)"}),
]


class CapsuleRefused(KitError):
    """A capsule that does not keep its contract, or a write against a revision that is no longer on disk."""

    code = "KIT0081"


def _seat(ctx):
    item = next((i for c in ctx.enabled_capabilities() for i in c.installs if i.get("validates") == CONTRACT), None)
    if item is None:
        raise CapsuleRefused("no enabled capability declares a continuity capsule (take the shared-tree bundle)")
    return item["target"]


def _validated(ctx, value, where):
    errors = ctx.manifest.validate(value, CONTRACT)
    if errors:
        raise CapsuleRefused(f"{where} does not keep the continuity-capsule contract:\n  " + "\n  ".join(errors))
    if len(value["wip"]) > 1:
        raise CapsuleRefused(f"{where} holds {len(value['wip'])} items in progress; a handoff names ONE (WIP=1)")
    return value


def run(ctx, args) -> int:
    seat = _seat(ctx)
    current = _validated(ctx, ctx.workspace.read_json(seat), seat) if ctx.workspace.exists(seat) else None
    if not getattr(args, "write", None):
        print(json.dumps(current, indent=2) if current else f"capsule: none at {seat}")
        return 0
    new = _validated(ctx, json.loads(Path(args.write).read_text(encoding="utf-8")), args.write)
    on_disk = current[REV] if current else 0
    if args.rev is None or args.rev != on_disk or new[REV] != on_disk + 1:
        raise CapsuleRefused(f"the capsule on disk is revision {on_disk}; this write replaces {args.rev} as "
                             f"revision {new[REV]} -- a write is accepted only as revision {on_disk + 1} over "
                             f"{on_disk}: read the capsule again, merge, and write over what is there")
    lock = ctx.workspace.path(ephemeral.place(ctx, f"{SUBJECT}.lock"))
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise CapsuleRefused(f"another writer holds {lock.name}; nothing was written") from exc
    try:
        again = ctx.workspace.read_json(seat) if ctx.workspace.exists(seat) else None
        if (again[REV] if again else 0) != on_disk:
            raise CapsuleRefused("the capsule moved while this write waited for its lock; nothing was written")
        ctx.workspace.scoped((seat,)).write_json(seat, new)
        journal = ctx.workspace.path(ephemeral.place(ctx, f"{SUBJECT}.journal.jsonl"))
        with journal.open("a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps({"at": ctx.clock.now(), REV: new[REV], "by": new.get("updated_by")}) + "\n")
    finally:
        os.close(handle)
        os.remove(lock)
    print(f"capsule: revision {new[REV]} written over {on_disk}")
    return 0
