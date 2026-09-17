"""activate -- point a setting OUTSIDE the tree at what a served surface serves, or withdraw it,
through a door.

Some products run what the kit serves only once their own configuration names it (a hooks
directory is the case that made this verb). That configuration is not a file in any plane the kit
writes, so a render cannot project it and the record cannot account for it: changing it is a SIDE
EFFECT on the host's machine, and a side effect is a door, walked by name, never a by-product of a
render. The surface declares everything product-shaped -- the setting's name, the directory it
must name, the argv that reads, sets and unsets it, and where the product looks while it is unset.
This verb holds none of it.

Work protection is the whole of its policy, and it is the same policy everywhere:
  * a setting that already names somewhere else is REFUSED -- the kit never overwrites what it did
    not make; the setting's owner changes it;
  * live entries where the product looks while the setting is unset are REFUSED -- setting it
    would silently switch that prior work off;
  * a setting that cannot be read is REFUSED -- unmeasured is not unset;
  * withdrawal unsets only a setting that names the served directory -- never somebody else's.

    python .agents/kit/interpreters/cli.py activate --root . --surface <id> --plan
    python .agents/kit/interpreters/cli.py activate --root . --surface <id> --approve <who>
    python .agents/kit/interpreters/cli.py activate --root . --surface <id> --to inactive --approve <who>
"""

from __future__ import annotations

import subprocess

import activation
import doors
import hostlock

SUMMARY = "point a setting outside the tree at what a served surface serves -- or withdraw it -- through a door"
MUTATES = True
REQUIRES_APPROVED_HOST = True

#: The two states this door moves a setting between, as `--to` names them.
TO_ACTIVE, TO_INACTIVE = "active", "inactive"

Refused = activation.ActivationRefused


def _declared(ctx, surface_id) -> dict:
    offered = activation.served(ctx)
    if surface_id not in offered:
        raise Refused(f"activate needs --surface naming a surface this host is SERVED that declares a "
                      f"setting (served here with one: {sorted(offered) or 'none'}); render serves a "
                      f"surface, and only a served one has anything to point a setting at")
    return offered[surface_id]


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    to = args.to or TO_ACTIVE
    if to not in (TO_ACTIVE, TO_INACTIVE):
        raise Refused(f"--to {to!r}: a setting is moved to {TO_ACTIVE!r} or {TO_INACTIVE!r}, nothing else")
    declared = _declared(ctx, args.surface)
    setting, where = declared["setting"], declared["points_at"]
    state, value, detail = activation.reading(ctx, declared)
    print(f"  read  {setting}: {state}" + (f" ({value})" if value else "") + (f" -- {detail}" if detail else ""))

    if state == activation.UNREADABLE:
        raise Refused(f"{setting} could not be read ({detail}); an unmeasured setting is not an unset one")
    if to == TO_ACTIVE:
        if state == activation.ACTIVE:
            print(f"  {args.surface}: already ACTIVE -- nothing to change")
            return 0
        if state == activation.ELSEWHERE:
            raise Refused(f"{setting} already names {value!r}, not {where}: the kit never overwrites a "
                          f"setting it did not make. Its owner unsets it (or moves that work under "
                          f"{where} as a declaration) and walks this door again.")
        occupied = activation.occupants(ctx, declared)
        if occupied:
            raise Refused(f"the product runs live entries where it looks while {setting} is unset "
                          f"({', '.join(occupied)}); setting it would silently switch them off. "
                          f"Move that work into a declaration this host serves, or remove it, first.")
        if not ctx.workspace.path(where).is_dir():
            raise Refused(f"nothing is served at {where}; `render` serves it before a setting may name it")
        command = activation.argv(declared, "set")
    else:
        if state == activation.INACTIVE:
            print(f"  {args.surface}: already INACTIVE -- nothing to withdraw")
            return 0
        if state == activation.ELSEWHERE:
            raise Refused(f"{setting} names {value!r}, not {where}: it is not the kit's setting, so the "
                          f"kit does not withdraw it")
        command = activation.argv(declared, "unset")

    print(f"  {to}  {args.surface}  {setting} -> {where if to == TO_ACTIVE else '(unset)'}  via {command}")
    if args.plan:
        return 0
    if not args.approve:
        doors.refuse(f"{setting} would be moved to {to.upper()} for the surface {args.surface}",
                     "person who owns this host",
                     f"activate --root <host> --surface {args.surface}"
                     + (f" --to {to}" if to != TO_ACTIVE else "") + " --approve <who>",
                     "The setting lives outside every tree the kit writes, so changing it is a side "
                     "effect on this machine, and the record of it names who chose.")

    def act() -> int:
        ran = subprocess.run(command, cwd=ctx.workspace.path("."), capture_output=True, text=True)
        after, value_after, _ = activation.reading(ctx, declared)
        wanted = activation.ACTIVE if to == TO_ACTIVE else activation.INACTIVE
        if ran.returncode != 0 or after != wanted:
            raise Refused(f"the command exited {ran.returncode} ({ran.stderr.strip()}) and the setting "
                          f"now reads {after}, not {wanted}: observed, not assumed")
        if to == TO_ACTIVE:
            activation.make_executable(ctx, declared)
        print(f"  {after}  {args.surface}  {setting}"
              + (f" = {value_after}" if value_after else "")
              + f"  by {args.approve} at {ctx.clock.now()} (read back after the change)")
        return 0

    return hostlock.held(ctx, args, act)
