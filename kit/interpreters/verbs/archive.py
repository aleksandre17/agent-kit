"""archive -- finished cards past the host's declared age leave the working set for the archive (ADR-025 d. 13).

    python .agents/kit/interpreters/cli.py archive --root . --by <who> [--plan]

A card in a state the lifecycle marks closed, which entered it more than the host's
`archive_after_days` ago, is moved -- byte for byte -- into the archive space beside the card space,
where no board, gate or reading looks again: dead by location (ADR-019), never deleted -- in the folder
of the year it closed in (`<archive>/2026/`), the one thing about a finished card that never changes,
so the archive stays a set of bounded folders however many years the project runs. A card some
working card still names (`after`, `parent`) stays where it is, because an order that pointed into
the archive would point at nothing. With no declared age nothing moves: when work leaves the surface
is the host's decision, and a kit that picked a number would be deciding it.
"""

from __future__ import annotations

import collection
import hostlock
import lifecycle as lifecycle_module
import plan as plan_module
import render as render_verb
from errors import KitError

SUMMARY = "move finished cards past the host's declared age into the archive, where nothing reads them"
MUTATES = True
REQUIRES_APPROVED_HOST = True

#: The card fields that name another card -- the edges a working card may hold into a finished one.
EDGES = ("after", "parent")


class ArchiveError(KitError):
    """An archive asked for with no mover, or on a delivery that declares no archive space."""

    code = "KIT0089"


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    by = getattr(args, "by", None)
    if not by:
        raise ArchiveError("archive needs --by <who>: a move nobody made is a state change nobody owns")
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    days = governed.policy.get("archive_after_days")
    if days is None:
        print("archive: this host declares no archive_after_days -- nothing leaves the working set")
        return 0
    # The archive is found by DECLARATION: the space that keeps the cards' own contract and that no
    # reading is declared over -- cards, by shape; read, by nothing. Never by a name or a path.
    card_install = next(i for i in governed.capability.installs if i.get("reads_as") == governed.spec["collection"])
    archive_space = next((i["target"] for i in governed.capability.installs
                          if i.get("mode") == "space" and i.get("validates") == card_install.get("validates")
                          and not i.get("reads_as")), None)
    if archive_space is None:
        raise ArchiveError("the delivery capability declares no archive space: a space keeping the cards' "
                           "contract that no reading is declared over")
    closed = {s["id"] for s in governed.states if s.get("closed")}
    now = ctx.clock.now()
    def names(card):
        return {t for edge in EDGES for t in ([card[edge]] if isinstance(card.get(edge), str) else card.get(edge) or [])}

    old = {c["id"] for c in governed.members.value if c.get(governed.state_field) in closed
           and lifecycle_module.days_between(lifecycle_module.entered_at(c), now) > days}
    # A card any STAYING card names stays too -- closed or not -- and so on, to a fixed point: an order
    # or a parent that pointed into the archive would point at nothing. And a part of a staying card
    # stays with it: a program's card tree is read from the parts that name it, so a finished part
    # that left would leave a working program with no tree.
    while True:
        staying = [c for c in governed.members.value if c["id"] not in old]
        named = {t for c in staying for t in names(c)}
        ids = {c["id"] for c in staying}
        under = {c["id"] for c in governed.members.value if c["id"] in old
                 and any(t in ids for t in ([c["parent"]] if isinstance(c.get("parent"), str) else []))}
        kept = old & (named | under)
        if not kept:
            break
        old -= kept
    archived = {rel.split("/")[-1]: rel for rel in ctx.workspace.files_under(archive_space.rstrip("/"))}

    def home(rel, card) -> str:
        return f"{archive_space.rstrip('/')}/{lifecycle_module.entered_at(card)[:4]}/{rel.split('/')[-1]}"

    leaving = []
    for rel, card in sorted(governed.members.records):
        if card["id"] in old:
            held = archived.get(rel.split("/")[-1])
            if held:
                print(f"archive: {card['id']} stays -- {held} already holds an archived card; one id, one home")
                continue
            leaving.append((rel, card))
    writes = []
    for rel, card in leaving:
        moved_to = home(rel, card)
        writes += [plan_module.Write("create", "binding", "space", governed.capability.id, moved_to),
                   plan_module.Write("remove", "binding", "space", governed.capability.id, rel)]
    if getattr(args, "plan", False) or not writes:
        print(plan_module.report("archive", writes) if writes else
              f"archive: no finished card is older than {days} day(s) -- nothing leaves")
        return 0

    def write() -> int:
        scoped = ctx.workspace.scoped(governed.capability.targets())
        for rel, card in leaving:
            moved_to = home(rel, card)
            scoped.write_json(moved_to, card)
            scoped.remove_file(rel)
            print(f"  archived  {card['id']}  {rel} -> {moved_to}  by {by}")
        return render_verb.run(ctx, args, capabilities)

    return hostlock.held(ctx, args, write)
