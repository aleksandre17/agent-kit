"""upgrade -- the first verb that meets a tree the kit did not create.

Everything else this kit does was proved on a repository it made itself, where nothing had moved
because nothing was ever supposed to have. An upgrade meets a host a human has been living in,
and the whole difficulty is one distinction that is invisible in the bytes on disk: *the host
edited this* against *upstream changed this*. Neither can be recovered by looking at the file.
The estate is what makes them separable, and a host without one is refused rather than guessed at.

    python kit/interpreters/cli.py upgrade --root <host> --plan   # read, report, write nothing
    python kit/interpreters/cli.py upgrade --root <host>          # reconcile, refuse or install
    python kit/interpreters/cli.py upgrade --root <host> --approve <who>   # walk the door

This verb WRITES NOTHING ITSELF, and that is a design decision rather than an economy. `init`
already carries out every install mode correctly -- vendor replaces, seeds are created once,
projections are rebuilt -- so a second installer here would be a second home for the one thing
that must never have two. What was missing was never the writing. It was the judgement of whether
the writing is SAFE, and that is all this verb is: a gate in front of the installer.

It also cannot delete. A capability's `installs` IS its write permission, so a path the new kit
no longer declares is a path nothing gives it permission to touch -- which settles what happens
to a withdrawn file without anyone having to choose: it stays, and the record goes on accounting
for it as ORPHANED, so it never becomes an unexplained path in a governed plane.

The door: a refusal that a NAMED HUMAN may accept is declared adoptable by the steward, and
nothing else can be waved through. Adoption is recorded on the row -- who, when, and the digest
it superseded -- because a decision whose only record is a terminal session answers differently
on Tuesday. The bytes are not archived: the refusal happens BEFORE the write, so the host still
holds its own file at the moment it decides.
"""

from __future__ import annotations

import doors
import estate as estate_module
import hostlock
import init as init_verb
import reconcile
import relocation
from errors import KitError

SUMMARY = "reconcile what was shipped, what the host has, and what this kit ships -- then install"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class UpgradeRefused(KitError):
    """The three readings could not be reconciled. The paths are named and so are both moments."""

    code = "KIT0029"


def _report(ctx, recorded, rows, stewards) -> None:
    print(f"upgrade: kit {ctx.manifest.version} against a host recorded at "
          f"{recorded['taken_at']} as kit {recorded['kit_version']}, signed by "
          f"{recorded['signed_by']}")
    reconcile.report(stewards, rows, reconcile.UNCHANGED)


def _refuse(rows) -> None:
    """Every refusal at once, and the upgrade stops. Not the path skipped and the rest applied: a
    partial upgrade leaves a host in a state no version describes, and nothing can then say what
    it is. Adoptable refusals are told apart from structural ones, because they are answered by
    different things -- one by a person, the other by a repair."""
    refusals = reconcile.refused(rows)
    if not refusals:
        return
    adoptable = [row for row in refusals if row["adoptable"]]
    structural = [row for row in refusals if not row["adoptable"]]
    lines = "\n  ".join(f"{row['state']}  {row['path']}  --  {row['why']}" for row in refusals)
    if structural:
        raise UpgradeRefused(
            f"{len(structural)} path(s) this upgrade cannot reconcile, and no name resolves "
            f"them:\n  {lines}"
        )
    doors.refuse(
        f"{len(adoptable)} path(s) this host has changed and this kit also changes:\n  {lines}",
        "person who owns these files",
        "upgrade --root <host> --approve <who>",
        "Keeping them silently and overwriting them silently are both decisions nobody would be "
        "able to read afterwards, so neither is taken. Revert the file to be rid of the change, "
        "or accept the replacement by name -- the digest it supersedes is recorded either way.",
    )


def run(ctx, args) -> int:
    # Guarded on arrival, so a held host is named as the cause before a reconciliation is printed
    # against a tree somebody else is writing. The hold itself is taken by the installer this verb
    # hands its verdict to, at the moment that installer writes, and under THIS verb's name.
    hostlock.arrive(ctx, args)
    recorded = estate_module.read(ctx)
    if recorded is None:
        raise UpgradeRefused(
            f"{estate_module.target(ctx)}: this host has no record of what it was given, so "
            f"nothing here can tell a file the host edited from one this kit changed. A tree "
            f"states what it IS and never what it RECEIVED. Take a first record with `init "
            f"--root <host>` on the kit this host is already running, then upgrade"
        )

    stewards = estate_module.stewardship(ctx)
    enabled = ctx.enabled_capabilities()
    # The relocations this host owes are reconciled AS IF carried out (ADR-021): `init` carries
    # them out first, so the verdict printed here is the verdict over the tree it will write.
    moved = relocation.view(relocation.planned(ctx, enabled))
    rows = reconcile.survey(ctx, enabled, recorded, stewards, ctx.adopted, moved)
    _report(ctx, recorded, rows, stewards)

    if args.approve:
        # The door is walked ONCE, against the plan just printed -- not once per file. Every row
        # it accepts carries the name, the moment and the digest it supersedes onto the record.
        ctx.adopted = {
            row["path"]: doors.record(args.approve, ctx.clock.now()) | {"superseded": row["here"]}
            for row in reconcile.refused(rows) if row["adoptable"] and row["here"]
        }
        rows = reconcile.survey(ctx, enabled, recorded, stewards, ctx.adopted, moved)

    _refuse(rows)

    # The reconciliation's verdict is handed to the installer as DATA. `init` carries it out and
    # decides nothing again -- which is the only construction under which what was just printed
    # and what is about to be written cannot be two different things.
    ctx.decided = {row["path"]: row for row in rows}

    if getattr(args, "plan", False):
        print(f"upgrade: reconciled; the writes below are {init_verb.SUMMARY}")
    return init_verb.run(ctx, args)
