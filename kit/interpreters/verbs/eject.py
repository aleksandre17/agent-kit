"""eject -- hand a path the kit shipped to the host, by name, through a door, and record it.

This is the kit's whole answer to a host that wants to LEAVE the seam. ADR-010 named this verb
`cede` and rejected an all-or-nothing `eject` (the CRA / `ng eject` shape: one-way, everything at
once, widely regretted). ADR-015 amendment 1 draws the verb list as init/render/check/upgrade/
`eject`, and there are never two verbs for one act -- so this module now answers to the drawn
name, and keeps ADR-010's per-path grain: leaving is granular by design, not the discredited
all-or-nothing copy. Leaving is done one path at a time, because what a host loses by leaving is
different at every grain, and an all-or-nothing verb would make it lose everything in order to
own one file. The larger grains already exist and are not rebuilt here: a capability is left by
disabling it, and the whole kit is left by no longer running it -- every byte it wrote is already
in the host's tree and the host's history.

What this verb does is the one act ADR-002 refuses as `re-stewarded` when it happens SILENTLY:
bytes changing hands. Here it happens in the open. A named person opens the door; the estate row
records who, when, and what the host held at that moment; the row's class becomes the class the
steward declares its paths transfer to; and from then on the steward that answers for the path is
that one, so every later reading NAMES it as taken over and no writer of this kit touches it again.

This verb decides nothing about ownership. Which stewards offer a transfer, what the path becomes
and what the host sees afterwards are all rows in `stewardship.json`. The interpreter privileges
no path, no capability and no steward: it asks the declaration, and refuses where it is silent.

    python kit/interpreters/cli.py eject --root <host> --path <path> --plan
    python kit/interpreters/cli.py eject --root <host> --path <path> --approve <who>
"""

from __future__ import annotations

import hashlib

import doors
import estate as estate_module
import hostlock
import plan as plan_module
import serving
from errors import KitError

SUMMARY = "hand a path the kit shipped to the host, through a signed door"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class EjectRefused(KitError):
    """A path was asked to change hands that the record or the declaration cannot hand over."""

    code = "KIT0035"


def _asked(args) -> list:
    paths = getattr(args, "path", None)
    if not paths:
        raise EjectRefused(
            "eject needs --path <path>[,<path>...]: the grain of leaving the seam is a PATH, and "
            "a transfer that names nothing would hand over whatever a default decided"
        )
    return paths


def _held(ws, path: str):
    """What the host holds at this path now, or None where nothing stands there to measure."""
    if not ws.exists(path) or ws.path(path).is_dir():
        return None
    return hashlib.sha256(ws.read_bytes(path)).hexdigest()


def _transfers(ctx, recorded, stewards, paths) -> list:
    """(row, steward, transfer) for every asked path -- or a refusal naming EVERY path that cannot
    change hands, at once. Not the first one and then the next: a door walked for half a request
    leaves a host in a state nobody asked for."""
    rows = {row["path"]: row for row in recorded["files"]}
    # A file served to a runtime is a path this host WAS given, recorded in the projection plane
    # rather than the estate (ADR-013). Reading only the estate would answer "never given it" --
    # a confident lie about a file carrying the kit's bytes. Asked of the port that owns the record.
    served = serving.served_rows(ctx, ctx.enabled_capabilities())
    classes = {plane["class"] for plane in ctx.manifest.planes}
    found, problems = [], []
    for path in paths:
        if path not in rows and path in served:
            row = served[path]
            steward = stewards.of_mode(row["mode"])
            if stewards.transfer(steward) is None:
                problems.append(
                    f"{path}: SERVED to a runtime by {row['capability']} (the kit's record in "
                    f"the projection plane), held by the steward {steward!r}, which declares no "
                    f"transfer -- a served file is rebuilt from what this host declares, so it has "
                    f"no bytes anyone could own. It is left by no longer serving it: drop the "
                    f"surface from the runtime descriptor that names it, or stop taking the adapter "
                    f"that declares it, and render -- the kit then removes it while it still holds "
                    f"the kit's recorded bytes, and refuses if it does not")
            else:
                problems.append(
                    f"{path}: SERVED to a runtime by {row['capability']}, and its steward "
                    f"{steward!r} declares a transfer this verb cannot carry for a path outside "
                    f"the estate -- NOT BUILT (ADR-014), refused rather than recorded nowhere")
            continue
        row = rows.get(path)
        if row is None:
            problems.append(
                f"{path}: the record taken at {recorded['taken_at']} carries no such path. Only "
                f"what this kit SHIPPED can be handed over, and this host was never given it")
            continue
        signed = row.get(estate_module.CEDED)
        if signed:
            problems.append(
                f"{path}: already taken over by {signed['signed_by']} at {signed['signed_at']}. "
                f"A door is walked once, and a second signature would date the transfer twice")
            continue
        steward = stewards.of_mode(row["mode"])
        transfer = stewards.transfer(steward)
        if transfer is None:
            problems.append(
                f"{path}: held by the steward {steward!r}, which declares no transfer -- there is "
                f"nothing here for a host to take over. What is already the host's needs no door, "
                f"and what is rebuilt from its inputs has no bytes anyone could own")
            continue
        if transfer["class"] not in classes:
            problems.append(
                f"{path}: the steward {steward!r} transfers its paths to the class "
                f"{transfer['class']!r}, which is not one of this kit's classes {sorted(classes)}. "
                f"Every path holds exactly one declared class, before a transfer and after it")
            continue
        found.append((row, steward, transfer))
    if problems:
        raise EjectRefused(
            f"{len(problems)} of {len(paths)} path(s) cannot change hands, so none does:\n  "
            + "\n  ".join(problems))
    return found


def _report(stewards, found) -> None:
    """What changes hands and what the host loses, stated BEFORE the door -- so the person who
    signs it has read what they are signing. The loss is the receiving steward's own declaration,
    printed verbatim, never a paraphrase this verb keeps of it."""
    print(f"eject: {len(found)} path(s) this kit shipped, to be taken over by this host")
    for row, steward, transfer in found:
        print(f"  {row['path']}  class {row['class']} -> {transfer['class']}  steward {steward} "
              f"-> {transfer['steward']}  (shipped by {row['capability']})")
    for receiving in sorted({transfer["steward"] for _, _, transfer in found}):
        summary = next(s["summary"] for s in stewards.stewards if s["id"] == receiving)
        print(f"  afterwards ({receiving}): {summary}")
    print("  unchanged: every gate the owning capability declares still runs at its declared "
          "stance, floors included; its other paths stay the kit's; this door is not reversed "
          "by any verb")


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    paths = _asked(args)
    recorded = estate_module.read(ctx)
    if recorded is None:
        raise EjectRefused(
            f"{estate_module.target(ctx)}: this host has no record of what it was given, so "
            f"nothing here can say which bytes are the kit's to hand over. Take a first record "
            f"with `init --root <host>`, then eject")
    stewards = estate_module.stewardship(ctx)
    found = _transfers(ctx, recorded, stewards, paths)
    _report(stewards, found)

    path = estate_module.target(ctx)
    item = ctx.install_of_mode(estate_module.MODE)
    enabled = ctx.enabled_capabilities()
    owner = next(c for c in enabled for i in c.installs if i["target"] == path)
    writes = [plan_module.Write("replace", item["class"], item["mode"], owner.id, path, item)]
    if getattr(args, "plan", False):
        print(plan_module.report("eject", writes))
        return 0

    if not args.approve:
        doors.refuse(
            f"{len(found)} path(s) would stop being the kit's: {', '.join(r['path'] for r, _, _ in found)}",
            "person who owns this host",
            "eject --root <host> --path <path> --approve <who>",
            "Taking a file over is one-way: the kit will never replace, restore or vouch for it "
            "again, and upgrades will only report what it no longer receives.",
        )

    def write() -> int:
        when = ctx.clock.now()
        chosen = {row["path"]: transfer for row, _, transfer in found}
        entries = []
        for row in recorded["files"]:
            if row["path"] in chosen:
                row = dict(row) | {
                    "class": chosen[row["path"]]["class"],
                    estate_module.CEDED: doors.record(args.approve, when)
                    | {"held": _held(ctx.workspace, row["path"])},
                }
            entries.append(row)
        # The delivery moment and its signature are NOT moved: nothing was delivered. The
        # transfer carries its own name and moment, on the row it is about.
        estate_module.take(ctx, enabled, recorded["taken_at"], recorded["signed_by"],
                           entries=entries, taken=recorded.get("taken", []))
        for row, _, _ in found:
            print(f"  ceded     {row['path']}  by {args.approve}  at {when}")
        print(f"  {writes[0].accomplished:<9}  {path}")
        return 0

    return hostlock.held(ctx, args, write)
