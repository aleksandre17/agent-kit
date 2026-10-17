"""weigh -- a change's class, computed from the areas it touches, and what that class requires (ADR-025).

    python .agents/kit/interpreters/cli.py weigh --root .                       # the working change
    python .agents/kit/interpreters/cli.py weigh --root . --path a,b            # a change not yet made
    python .agents/kit/interpreters/cli.py weigh --root . --base <rev> --head <rev>
    python .agents/kit/interpreters/cli.py weigh --root . --class standard      # refuse a lighter claim
    python .agents/kit/interpreters/cli.py weigh --root . --base <rev> --head <rev> --each   # CI: every commit

The class is the lightest one whose envelope admits the change, raised by every touched area that
asks more; `--class` names the class the change is declared as, and a declaration lighter than the
computed floor is refused, naming what raised it. `--each` holds every commit of a range to the floor
the commit hook holds -- weighed by the areas its parent held, its card read as the commit holds it --
so a hook skipped with --no-verify, or a commit made where no hook runs, is caught in CI. Reading
only: nothing is written.
"""

from __future__ import annotations

import json

import vcs
import weighing
import workclass
from errors import KitError

SUMMARY = "compute a change's work class from the areas it touches, and what that class requires"
MUTATES = False
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--base", {"default": None, "help": "the revision a weighed range starts from"}),
    ("--head", {"default": None, "help": "the revision a weighed range ends at"}),
    ("--class", {"dest": "declared_class", "default": None,
                 "help": "the class the change is declared as: refused when lighter than the computed one"}),
    ("--each", {"action": "store_true",
                "help": "hold every commit of the range (or of --head's history) to the commit floor"}),
]


class WeighRefused(KitError):
    """A change declared lighter than the class its areas compute, or a range given by half."""

    code = "KIT0086"


def _paths(ctx, args) -> list:
    if getattr(args, "path", None):
        return list(args.path)
    base, head = getattr(args, "base", None), getattr(args, "head", None)
    if bool(base) != bool(head):
        raise WeighRefused("--base and --head name ONE range: give both or neither")
    root = ctx.workspace.root
    if base:
        return workclass.paths(vcs.range_paths(root, base, head), f"what changed between {base} and {head}")
    return workclass.paths(vcs.working_paths(root), "what the working change touches")


def _json_at(root, sha: str, rel):
    if rel is None:
        return None
    text, _why = vcs.file_at(root, sha, rel)
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _each(ctx, args, classes_doc: dict, areas_doc: dict) -> int:
    """Every commit of the range against the floor its own hook would have held."""
    root, head = ctx.workspace.root, getattr(args, "head", None)
    if not head:
        raise WeighRefused("--each needs --head <rev>, and --base <rev> unless every commit is meant")
    shas = workclass.paths(vcs.commits_between(root, getattr(args, "base", None), head), "which commits the range holds")
    areas_rel, space = workclass.areas_target(ctx), workclass.card_space(ctx)
    keys = classes_doc["trailers"]
    doors, closed = workclass.lifecycle_flags(ctx)
    decided = workclass.decided(ctx)
    refused = skipped = 0
    for sha in shas:
        stood, left = _json_at(root, f"{sha}^", areas_rel), _json_at(root, sha, areas_rel)
        if stood is None and left is None:
            skipped += 1  # made before this host weighed its work: no scale stood to weigh it by
            continue
        paths = workclass.paths(vcs.commit_paths(root, sha), f"what {sha[:12]} changed")
        message, _why = vcs.commit_message(root, sha)
        _sig, verdict = weighing.weigh(paths, classes_doc, stood or left, weighing.loosened(classes_doc, stood, left))
        cards = {}
        listing = (vcs.run(root, ["ls-tree", "-r", "--name-only", sha, "--", space.rstrip("/")])[0] or "") if space else ""
        for rel in listing.splitlines():
            card = _json_at(root, sha, rel) if rel.endswith(".json") else None
            if isinstance(card, dict) and card.get("id"):
                cards[card["id"]] = card
        card_paths = [rel for rel in paths if space and rel.startswith(space) and rel.endswith(".json")]
        before = {rel: c for rel in card_paths if isinstance(c := _json_at(root, f"{sha}^", rel), dict) and c.get("id")}
        after = {rel: (c if isinstance(c := _json_at(root, sha, rel), dict) else None) for rel in before}
        try:
            why = (weighing.commit_refusals(classes_doc, verdict, message or "", cards, doors, decided)
                   + weighing.demotions(classes_doc, before, after, closed))
        except weighing.WeighError as error:
            why = [str(error)]
        for line in why:
            print(f"weigh: REFUSED [{WeighRefused.code}] {sha[:12]} -- {line}")
        refused += bool(why)
    print(f"weigh: {len(shas) - skipped} commit(s) held to the floor, {refused} refused"
          + (f"; {skipped} made before this host weighed its work, not weighed" if skipped else ""))
    return 1 if refused else 0


def run(ctx, args) -> int:
    found = workclass.declarations(ctx)
    if found is None:
        print("weigh: no work-class catalogue is declared on this host -- nothing is weighed")
        return 0
    classes_doc, areas_doc = found
    if getattr(args, "each", False):
        return _each(ctx, args, classes_doc, areas_doc)
    sig, verdict = weighing.weigh(_paths(ctx, args), classes_doc, areas_doc)
    row = verdict["class"]
    print(f"weigh: {row['id']} -- {verdict['why']}")
    for identity, hit in sorted(sig["touched"].items()):
        area = hit["area"]
        owner = f", owner {area['owner']}" if area.get("owner") else ""
        print(f"  area {identity} ({area['undo']}{owner}): {len(hit['paths'])} path(s) -- {area['because']}")
    declared_areas = {a["id"]: a for a in areas_doc.get("areas", [])}
    for identity in sig["downstream"]:
        owner = declared_areas[identity].get("owner")
        print(f"  feeds {identity}" + (f" (owner {owner})" if owner else "") + " -- downstream of this change: "
              f"it moves with it, or the change says why it need not")
    # A lesson whose subject is a touched area reaches the work at the moment it applies, and costs no
    # context anywhere else (ADR-025 decision 12).
    field = workclass.governed_field(ctx, "lesson")
    for card in sorted(workclass.cards(ctx).values(), key=lambda c: c["id"]) if field else []:
        lesson = card.get(field) or {}
        if lesson.get("subject") in sig["touched"]:
            print(f"  lesson ({card['id']}, {lesson['subject']}): {lesson['statement']}")
    if sig["unclaimed"]:
        print(f"  unclaimed: {len(sig['unclaimed'])} path(s), undo cost {areas_doc['default_undo']} "
              f"(no area declares them)")
    print(f"  requires: {', '.join(verdict['requires'])}")
    for door in row.get("doors", []):
        print(f"  door: {door}")
    claimed = getattr(args, "declared_class", None)
    if claimed and not weighing.heavier_or_equal(classes_doc, claimed, row["id"]):
        raise WeighRefused(f"declared {claimed!r}, but the change computes {row['id']!r} ({verdict['why']}); "
                           f"a declared class may be heavier than the computed one, never lighter. "
                           f"Instead: leave the records {row['id']} requires ({', '.join(verdict['requires'])}), "
                           f"or narrow the change")
    return 0
