"""capture -- a finding met on the way, written down as a card in one act, so it is never done on the side.

    python .agents/kit/interpreters/cli.py capture --root . --card <id> --title "<what was found>" --by <who> [--from <card>]

The card is written in the lifecycle's INITIAL state, with its moment and its author, and -- when it was
found while working on another card -- the card it came from as its `origin`. Nothing else: shaping it,
classing it and deciding whether it is worth doing are later acts by their owners (ADR-025 decision 10).
Doing the finding inside the unrelated work is what the work-class floor catches instead: the change
touches an area its card does not, and its class rises.
"""

from __future__ import annotations

import collection
import hostlock
import lifecycle as lifecycle_module
import plan as plan_module
import render as render_verb
from errors import KitError

SUMMARY = "write a finding met on the way as a card in the initial state, in one act"
MUTATES = True
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--title", {"default": None, "help": "what was found, in a line"}),
    ("--from", {"dest": "found_in", "default": None, "help": "the card this was found while working on"}),
]


class CaptureError(KitError):
    """A capture that names no card, no title or no author, or a card id that is already taken."""

    code = "KIT0088"


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    identity, title, by = getattr(args, "card", None), getattr(args, "title", None), getattr(args, "by", None)
    if not identity or not title or not by:
        raise CaptureError("capture needs --card <id>, --title <what was found> and --by <who>")
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    if governed.members.record_of(identity)[0] is not None:
        raise CaptureError(f"a card {identity!r} already exists; a finding is a new card, never an edit to one")
    space = next(item["target"] for item in governed.capability.installs
                 if item.get("reads_as") == governed.spec["collection"])
    rel = f"{space.rstrip('/')}/{identity}.json"
    card = {"schema_version": ctx.manifest.version_of("card"), "id": identity, "title": title,
            "state": governed.doc["initial"], "owner": by, "created_at": ctx.clock.now()}
    found_in = getattr(args, "found_in", None)
    if found_in:
        origin_rel, _origin = governed.members.record_of(found_in)
        if origin_rel is None:
            raise CaptureError(f"--from {found_in!r} names no card this host holds")
        card["origin"] = {"kind": "artifact-present", "ref": origin_rel}
    errors = ctx.manifest.validate(card, "card")
    if errors:
        raise CaptureError(f"the card would not honour its schema: {'; '.join(errors)}")
    writes = [plan_module.Write("create", "binding", "space", governed.capability.id, rel)]
    if getattr(args, "plan", False):
        print(plan_module.report("capture", writes + render_verb.plan_entries(ctx, capabilities)))
        return 0

    def write() -> int:
        ctx.workspace.scoped(governed.capability.targets()).write_json(rel, card)
        print(f"  captured  card {identity}  in {card['state']}  by {by}" + (f"  from {found_in}" if found_in else ""))
        print(f"  {writes[0].accomplished:<9}  {rel}")
        return render_verb.run(ctx, args, capabilities)

    return hostlock.held(ctx, args, write)
