"""render -- recompute every projection from scratch.

A projection has no history. It is deleted and rebuilt, never merged and never diffed against its
old self, so there is nothing for it to drift FROM. Its inputs are VENDOR + BINDING only; the wall
clock is deliberately not one of them, which is what makes the output byte-reproducible.

It MUTATES, so it can be asked for a plan; and it runs only on an APPROVED host, because a
projection of an answer nobody accepted would be a surface stating a decision as settled.
"""

from __future__ import annotations

import hostlock
import plan as plan_module
import runtime as runtime_port
from projection import RenderError, _plane, _shape_of, plan_entries, projections  # noqa: F401 -- the verb's surface

SUMMARY = "recompute every projection from VENDOR + BINDING"
MUTATES = True
REQUIRES_APPROVED_HOST = True


def run(ctx, args, capabilities=None) -> int:
    hostlock.arrive(ctx, args)
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    writes = plan_entries(ctx, capabilities)
    if getattr(args, "plan", False):
        print(plan_module.report("render", writes))
        return 0

    def write() -> int:
        # Everything is computed, and every path outside the planes is judged, BEFORE a byte
        # moves: a refusal must leave the host exactly as it was found (ADR-013).
        produced = projections(ctx, capabilities)
        departing = runtime_port.admit(ctx, capabilities, produced)
        ctx.workspace.unscoped().remove_tree(_plane(ctx))
        for rel in departing:
            ctx.workspace.scoped(departing).remove_file(rel)
        # A capability writes only what it declared -- and a served path is declared by the plan
        # computed from that same capability's declaration, never by this function.
        scopes = {c.id: ctx.workspace.scoped(
                      c.targets() + tuple(e.target for e in writes if e.capability == c.id))
                  for c in capabilities}
        for entry in writes:
            if entry.disposition != "remove":
                scopes[entry.capability].write_text(entry.target, produced[entry.target])
            print(f"  {entry.accomplished:<9}  {entry.target}")
        # A COLLECTION projection has a home whether or not the host has declared anything for it
        # to hold: the directory is the declared render target, and an empty one is the honest
        # state of a host that declared nothing -- the same rule a `space` follows. Created, never
        # filled; it is a shape of the tree and no file, so no plan line promises bytes for it.
        for capability in capabilities:
            for item in capability.installs_of_class("projection"):
                if _shape_of(item) == "collection":
                    scopes[capability.id].make_dir(item["target"])
        return 0

    return hostlock.held(ctx, args, write)
