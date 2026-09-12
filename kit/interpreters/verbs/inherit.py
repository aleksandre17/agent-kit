"""inherit -- read a host's PRIOR agent system and state what becomes of every path of it.

    python kit/interpreters/cli.py inherit --root <host> [--map <migration-map.json>]

With no `--map`, the map at the RESIDENCE the succession vocabulary declares is read where one is
there -- the same reading `takeover` carries out (ADR-012).

A host that already runs an agent system of its own keeps it outside this kit's planes, where
`adopt` never looks. This verb takes the census of that system -- every path inside a DECLARED
boundary, never one found by resemblance -- measures what can be proven about each path, and
prints the disposition the host's migration map assigns it: every state counted, zeros included,
and every path no row answers named `undecided`, never defaulted (ADR-011).

It is a READING. It writes nothing, moves nothing and deletes nothing; carrying a roster out is a
separate act at a signed door, and it is not this verb.
"""

from __future__ import annotations

import succession

SUMMARY = "read a host's prior agent system and state what becomes of every path of it"
MUTATES = False
REQUIRES_APPROVED_HOST = False


def run(ctx, args) -> int:
    reading = succession.read(ctx, getattr(args, "map", None))
    succession.report(ctx, reading, ctx.clock.now())
    return 0
