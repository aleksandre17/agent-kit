"""move -- carry one card across one DECLARED passage, and record who did it and when.

This verb decides nothing. It reads the lifecycle the governing capability declared, asks it
whether this passage exists for this card, and either writes the card or reports the refusal the
declaration produced. Every rule it appears to enforce -- the door, the guarded bypass, the
capacity, the states themselves -- is a row in a document a host can read.

It MUTATES, so it can be asked for a plan; it runs only on an APPROVED host; and it re-renders
the board afterwards, because a board that lagged its cards would be a second reading of one
reality presented as the reality.
"""

from __future__ import annotations

import collection
import lifecycle as lifecycle_module
import plan as plan_module
import render as render_verb
from errors import KitError

SUMMARY = "move one card across one declared transition"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class MoveError(KitError):
    """The move named something the host does not have, or was asked for incompletely."""

    code = "KIT0027"


def _asked(args) -> tuple:
    card_id, target = getattr(args, "card", None), getattr(args, "to", None)
    if not card_id or not target:
        raise MoveError("move needs --card <id> and --to <state>")
    by, approver = getattr(args, "by", None), getattr(args, "approve", None)
    if not by and not approver:
        raise MoveError(
            "move needs --by <who>, or --approve <who> where the passage is a door. A passage "
            "with no mover is a state change nobody made, which is exactly what this board exists "
            "to make impossible"
        )
    return card_id, target, by or approver, approver


def run(ctx, args) -> int:
    card_id, target, by, approver = _asked(args)
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))

    rel, card = governed.members.record_of(card_id)
    if card is None:
        raise MoveError(
            f"no card {card_id!r} in {governed.spec['collection']}; this host holds "
            f"{governed.members.identities()}"
        )

    edge = lifecycle_module.resolve(governed, card, target, approver)
    when = ctx.clock.now()
    updated = lifecycle_module.moved(governed, card, edge, when, by, approver)

    # The host's own capacity declaration, applied to the board this move WOULD produce -- so a
    # limit is refused before the byte, not reported by a gate after it.
    prospective = [updated if c["id"] == card_id else c for c in governed.members.value]
    over = lifecycle_module.capacity_failures(governed, prospective)
    if over:
        raise MoveError(
            f"card {card_id!r} may not enter {target!r}: " + "; ".join(over)
            + ". Finish or park what is already there -- the limit is this host's declaration, "
              "not the kit's opinion"
        )

    writes = [plan_module.Write("replace", "binding", "space", governed.capability.id, rel)]
    if getattr(args, "plan", False):
        print(plan_module.report("move", writes + render_verb.plan_entries(ctx, capabilities)))
        return 0

    scoped = ctx.workspace.scoped(governed.capability.targets())
    scoped.write_json(rel, updated)
    print(f"  {edge['from']} -> {edge['to']}  card {card_id}  by {by}"
          + (f"  ACCEPTED by {approver}" if approver else "") + f"  at {when}")
    print(f"  {writes[0].accomplished:<9}  {rel}")
    return render_verb.run(ctx, args, capabilities)
