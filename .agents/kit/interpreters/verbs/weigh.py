"""weigh -- a change's class, computed from the areas it touches, and what that class requires (ADR-025).

    python .agents/kit/interpreters/cli.py weigh --root .                       # the working change
    python .agents/kit/interpreters/cli.py weigh --root . --path a,b            # a change not yet made
    python .agents/kit/interpreters/cli.py weigh --root . --base <rev> --head <rev>
    python .agents/kit/interpreters/cli.py weigh --root . --class standard      # refuse a lighter claim

The class is the lightest one whose envelope admits the change, raised by every touched area that
asks more; `--class` names the class the change is declared as, and a declaration lighter than the
computed floor is refused, naming what raised it. Reading only: nothing is written.
"""

from __future__ import annotations

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


def run(ctx, args) -> int:
    found = workclass.declarations(ctx)
    if found is None:
        print("weigh: no work-class catalogue is declared on this host -- nothing is weighed")
        return 0
    classes_doc, areas_doc = found
    sig, verdict = weighing.weigh(_paths(ctx, args), classes_doc, areas_doc)
    row = verdict["class"]
    print(f"weigh: {row['id']} -- {verdict['why']}")
    for identity, hit in sorted(sig["touched"].items()):
        area = hit["area"]
        print(f"  area {identity} ({area['undo']}): {len(hit['paths'])} path(s) -- {area['because']}")
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
