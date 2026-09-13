"""adopt -- take a reading of a repository this kit has never touched, and CLASS NOTHING.

    python kit/interpreters/cli.py adopt --root <host>

Every other verb here has met a tree the kit had a relationship with: `init` creates one,
`upgrade` carries one forward against the record of what it received. This one meets a repository
written by people and tools that never heard of this kit, and the only honest thing it can do is
READ. It writes nothing -- not a plane, not a record, not a marker. A verb whose entire subject is
*paths this kit has no permission to touch* may not begin by writing into the host it surveys.

What it produces is the ROSTER: every path that has no class. `foreign` is not a fifth class and
never will be -- a class in this kit is a WRITE PERMISSION conferred by a declaration, and a class
conferred by the ABSENCE of one would be a permission over bytes nobody declared (ADR-003). So a
foreign path is the declared absence of a class, read at a stated moment, and it HALTS.

The roster is produced by the machine and never by judgement. A row is there because a
capability's `installs` states this kit writes that exact path, or because a PLANE ROOT states the
path sits in a plane this kit governs entirely and nothing explains it. Both are declarations.
Nothing is matched against a filename and nothing is guessed at -- that guess is the precise lie
this whole system exists to prevent.

This verb is a GATE, and it is not the only place the gate stands: `init` at first contact takes
the SAME reading and refuses on it, so adoption cannot be bypassed by simply running the
installer. One decision, computed in one module, printed the same way.
"""

from __future__ import annotations

import adoption

SUMMARY = "read a host this kit has never touched and name every path that has no class"
MUTATES = False
REQUIRES_APPROVED_HOST = False


def run(ctx, args) -> int:
    if not adoption.at_first_contact(ctx):
        raise adoption.AdoptionRefused(
            f"{ctx.install_of_mode('declaration')['target']}: this host has already ANSWERED this "
            f"kit, so it is not a host to be adopted -- it is one to be carried forward. What it "
            f"received is recorded, and `upgrade` reads that record. Adopting it again would take "
            f"a reading that says this host was given nothing, over a host that was given "
            f"something, and every reading built on that would be a fiction dressed as a "
            f"measurement"
        )

    # Measured at the boundary, upward, BEFORE the survey -- because a host inside a host makes
    # every row below ambiguous about which law governs it, and an ambiguous roster read as a
    # plain one is worse than no roster.
    adoption.require_unenclosed(ctx)

    reading = ctx.take_reading()
    candidates, unavailable, blocked = ctx.classify(reading["facts"])
    print(f"reading taken at {reading['taken_at']} on {reading['boundary']['os']}")
    for fact, value in reading["facts"].items():
        print(f"  fact  {fact} = {value}")
    for entry in unavailable:
        print(f"  unavailable  {entry['id']}: {entry['reason']}")

    # WHAT THIS KIT WOULD SHIP is the third reading, and it depends on which capabilities this
    # host would run. Nothing is answered here on the host's behalf: the same selection `init`
    # would make is made, from the same flags, so the roster is the roster of the install that
    # would actually be attempted and not of some other one.
    enabled = ctx.compose(ctx.select(candidates, args.enable, args.disable), blocked)

    _recorded, rows = adoption.survey(ctx, enabled, reading["taken_at"])
    adoption.roster(ctx, rows, reading["taken_at"])
    adoption.require_adoptable(ctx, rows)

    print("adoption: no path in this host stands foreign; every one either resolves to a declared "
          "class or is out of account. This host can be installed into with `init`.")
    return 0
