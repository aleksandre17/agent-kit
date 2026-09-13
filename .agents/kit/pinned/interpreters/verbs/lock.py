"""lock -- the kit states what it is, and refuses to state it over a tree it cannot account for.

Two halves, and the second one is the point. FORESEE surveys the kit against its own enumeration
and prints a state for every path that is not `matched`. APPLY writes the reading down -- and it
is allowed to write only when the survey is clean, so a lockfile can never be produced ACROSS an
unaccounted path. That is what makes bytecode in the payload impossible rather than fenced: the
fence let it sit there unseen; this refuses to ship, and says its name.

    python kit/interpreters/cli.py lock --root <any repo> --plan   # read, report, write nothing
    python kit/interpreters/cli.py lock --root <any repo>          # read, refuse or record

Read `--plan` as the ordinary use. Regenerating is an authoring act, and the suite is what stands
between a lockfile and the thing a lockfile most easily becomes: a certificate, generated once,
trusted forever, and never failed against by anything.

The subject is the KIT, not the host, and the workspace this verb writes through is rooted at the
kit and scoped to the single lock path. `installs` remains the only write permission a capability
has; this verb is not a way around it, because it installs nothing and can reach exactly one file.
"""

from __future__ import annotations

import lockfile
from errors import KitError
from workspace import Workspace

SUMMARY = "enumerate what the kit is, measure it, and record the reading"
MUTATES = True
#: What this verb mutates is the KIT, never the host `--root` names -- so the host's hold is not
#: this verb's to take (ADR-007). Declared, so the set of verbs that hold is read, never listed.
SUBJECT = "kit"
REQUIRES_APPROVED_HOST = False


class LockRefused(KitError):
    """The kit could not honestly state what it is, or what it is no longer matches the record."""

    code = "KIT0026"


def run(ctx, args) -> int:
    kit = Workspace(ctx.manifest.root)
    lock_path = ctx.manifest.raw_ships()["lock"]
    rows = lockfile.survey(ctx.manifest, kit)
    moment = ctx.clock.now()

    unresolved = [row for row in rows if row["state"] != lockfile.MATCHED]
    print(f"lock: {ctx.manifest.root.as_posix()}")
    print(f"  {len(rows)} path(s) surveyed at {moment}, {len(unresolved)} not resolved")
    for row in unresolved:
        print(f"  {row['state']:>13}  {row['path']}")

    if unresolved:
        raise LockRefused(
            f"{len(unresolved)} path(s) the kit cannot ship: "
            + ", ".join(f"{row['path']} ({row['state']})" for row in unresolved)
        )

    fresh = lockfile.document(ctx.manifest, rows, moment)
    errors = ctx.manifest.validate(fresh, "lock")
    if errors:
        raise LockRefused(f"the reading does not honour the lock schema:\n  " + "\n  ".join(errors))

    if kit.exists(lock_path):
        recorded = kit.read_json(lock_path)
        drift = lockfile.compare(recorded, rows)
        for state, path, why in drift:
            print(f"  {state:>13}  {path}  --  {why}")
        if args.plan:
            print(f"lock: {len(drift)} path(s) differ from the recorded reading")
            return 1 if drift else 0
    elif args.plan:
        print(f"lock: no reading has been recorded yet; {len(rows)} path(s) would be")
        return 1

    Workspace(ctx.manifest.root).scoped([lock_path]).write_json(lock_path, fresh)
    print(f"  recorded  {lock_path}  ({fresh['count']} path(s), read at {moment})")
    return 0
