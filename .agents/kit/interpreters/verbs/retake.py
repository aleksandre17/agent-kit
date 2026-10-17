"""retake -- take this host's reading again, through a door, when its reality has legitimately moved.

    python .agents/kit/interpreters/cli.py retake --root . --plan
    python .agents/kit/interpreters/cli.py retake --root . --approve <who>

The reading is taken once, by `init`, and `check` compares a fresh one against it
(`reading-current`). A host whose tree changed on purpose -- a project added, a stack adopted, a
detector that learned to see it -- would otherwise fail that gate for ever, with nothing to do but
delete the file and let `upgrade` take it again unsigned. This verb is that act, made a door
(ADR-021 amendment 2): it prints every fact that moved, refuses without `--approve <who>`, and
records who replaced which reading and when. The replaced reading is not kept beside the new one:
its bytes are in the host's history, and two readings in the tree would be two answers to one
question.

What the new facts make AVAILABLE is not decided here: the host's set is its answer's, and
`upgrade --plan` names any capability the new reading admits or withdraws.
"""

from __future__ import annotations

import doors
import hostlock
from errors import KitError

SUMMARY = "take this host's reading again, through a door, when its reality has legitimately moved"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class RetakeError(KitError):
    """A retake on a host holding no reading, or a reading that would not honour its schema."""

    code = "KIT0072"


def moved(recorded: dict, fresh: dict) -> list:
    """Every fact that differs between two readings, as the line that names it."""
    lines = []
    for key in sorted(set(recorded) | set(fresh)):
        if key not in fresh:
            lines.append(f"- {key} = {recorded[key]}")
        elif key not in recorded:
            lines.append(f"+ {key} = {fresh[key]}")
        elif recorded[key] != fresh[key]:
            lines.append(f"~ {key}: {recorded[key]} -> {fresh[key]}")
    return lines


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    item = ctx.install_of_mode("reading")
    if not ctx.workspace.exists(item["target"]):
        raise RetakeError(f"{item['target']}: this host holds no reading to replace; `init` takes "
                          f"the first one")
    recorded = ctx.binding(item["target"], item["validates"])
    fresh = ctx.take_reading()
    lines = moved(recorded["facts"], fresh["facts"])
    if not lines:
        print(f"retake: the reading taken at {recorded['taken_at']} holds -- nothing moved, "
              f"nothing to retake")
        return 0
    print(f"retake: the reading taken at {recorded['taken_at']} and one taken at "
          f"{fresh['taken_at']} differ in {len(lines)} fact(s):")
    for line in lines:
        print(f"  {line}")
    if args.plan:
        return 0
    if not args.approve:
        doors.refuse(
            f"{item['target']} would be replaced by the reading taken at {fresh['taken_at']}",
            "person who owns this host",
            "retake --root <host> --approve <who>",
            "A reading is what every composition on this host is decided from; replacing it is a "
            "statement that the host moved, and the record of it names who stated it.")

    document = {**fresh, "retaken": {**doors.record(args.approve, fresh["taken_at"]),
                                     "replaces": recorded["taken_at"]}}
    errors = ctx.manifest.validate(document, item["validates"])
    if errors:
        raise RetakeError(f"{item['target']} would not honour its schema:\n  " + "\n  ".join(errors))
    owner = next(c for c in ctx.manifest.capabilities for i in c.installs if i is item
                 or i.get("target") == item["target"])

    def write() -> int:
        ctx.workspace.scoped(owner.targets()).write_json(item["target"], document)
        print(f"  RETAKEN  {item['target']}  by {args.approve} at {fresh['taken_at']}, replacing the "
              f"reading of {recorded['taken_at']}; `upgrade --plan` names what the new facts admit")
        # What is served is rendered from the reading, as `init` renders it: a retake that left the served
        # files stale would leave `check` red until somebody remembered `render`.
        ctx.reread()
        import render as render_verb
        return render_verb.run(ctx, args)

    return hostlock.held(ctx, args, write)
