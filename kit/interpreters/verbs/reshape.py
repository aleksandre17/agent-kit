"""reshape -- change the work class a card is shaped as, recorded on the card (ADR-025 decision 4).

    python .agents/kit/interpreters/cli.py reshape --root . --card <id> --class <class> --by <who>
    python .agents/kit/interpreters/cli.py reshape --root . --card <id> --class <lighter> --approve <owner>

Raising a class is anyone's act -- more care is never a risk. LOWERING one is the owner's door: the
weight a card was bet at is the owner's bet, and an author who could lighten it could lighten every
record the class owes. The change is appended to the card's `reshaped` record, and the commit floor
admits a lighter card only when that record says who approved it.
"""

from __future__ import annotations

import collection
import hostlock
import lifecycle as lifecycle_module
import plan as plan_module
import render as render_verb
import weighing
import workclass
from errors import KitError

SUMMARY = "change the work class a card is shaped as -- raising is anyone's, lowering the owner's door"
MUTATES = True
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--class", {"dest": "to_class", "default": None, "help": "the work class the card is shaped as from now on"}),
]

#: The exit code that means waiting for a human, as every door in this kit uses it.
DOOR_EXIT = 3


class ReshapeError(KitError):
    """A reshape that names no card or class, a class nobody declared, or one asked of a host that does not weigh."""

    code = "KIT0090"


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    identity, target = getattr(args, "card", None), getattr(args, "to_class", None)
    by, approver = getattr(args, "by", None), getattr(args, "approve", None)
    if not identity or not target or not (by or approver):
        raise ReshapeError("reshape needs --card <id>, --class <class> and --by <who> (or --approve <owner>)")
    found = workclass.declarations(ctx)
    if found is None:
        raise ReshapeError("this host declares no work classes, so no card has a class to reshape")
    classes_doc, _areas = found
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    rel, card = governed.members.record_of(identity)
    if card is None:
        raise ReshapeError(f"no card {identity!r}; this host holds {governed.members.identities()}")
    was = card.get("class")
    weighing.heavier_or_equal(classes_doc, target, target)  # refuses a class nobody declared (KIT0085)
    rows = {row["id"]: row for row in classes_doc["classes"]}
    if rows[target].get("expedite"):
        raise ReshapeError(f"{target!r} is an expedite class: an emergency is declared in a commit's trailer, and "
                           f"the card that repays it is shaped as the work it was")
    lowering = was is not None and (rows.get(was, {}).get("expedite")
                                    or not weighing.heavier_or_equal(classes_doc, target, was))
    if lowering and not approver:
        print(f"reshape: lowering {identity} from {was} to {target} is the owner's door -- run it with "
              f"--approve <owner>", flush=True)
        return DOOR_EXIT
    entry = {"to": target, "at": ctx.clock.now(), "by": by or approver}
    if was is not None:
        entry["from"] = was
    if lowering:
        entry["approved_by"] = approver
    updated = dict(card, **{"class": target, "reshaped": list(card.get("reshaped") or []) + [entry]})
    writes = [plan_module.Write("replace", "binding", "space", governed.capability.id, rel)]
    if getattr(args, "plan", False):
        print(plan_module.report("reshape", writes + render_verb.plan_entries(ctx, capabilities)))
        return 0

    def write() -> int:
        ctx.workspace.scoped(governed.capability.targets()).write_json(rel, updated)
        print(f"  reshaped  {identity}  {was or '(no class)'} -> {target}  by {entry['by']}"
              + (f"  APPROVED by {approver}" if lowering else ""))
        return render_verb.run(ctx, args, capabilities)

    return hostlock.held(ctx, args, write)
