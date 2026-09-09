"""render -- recompute every projection from scratch.

A projection has no history. It is deleted and rebuilt, never merged and never diffed against its
old self, so there is nothing for it to drift FROM. Its inputs are VENDOR + BINDING only; the wall
clock is deliberately not one of them, which is what makes the output byte-reproducible.

It MUTATES, so it can be asked for a plan; and it runs only on an APPROVED host, because a
projection of an answer nobody accepted would be a surface stating a decision as settled.
"""

from __future__ import annotations

import plan as plan_module
import template

SUMMARY = "recompute every projection from VENDOR + BINDING"
MUTATES = True
REQUIRES_APPROVED_HOST = True


def view_model(ctx, capabilities=None) -> dict:
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    project = ctx.host_answers()
    profile = ctx.binding(ctx.install_of_mode("reading")["target"], "profile")
    described = []
    for capability in capabilities:
        described.append({
            "id": capability.id,
            "version": capability.version,
            "summary": capability.summary,
            "installs": [dict(item) for item in capability.installs],
            "gates": [dict(gate) for gate in capability.gates],
        })
    return {
        "kit_version": ctx.manifest.version,
        "project": project,
        "capabilities": described,
        "facts": [{"key": k, "value": v} for k, v in sorted(profile["facts"].items())],
    }


def _plane(ctx) -> str:
    return next(p["root"] for p in ctx.manifest.planes if p["class"] == "projection")


def projections(ctx, capabilities=None) -> dict:
    """Every projected path and its bytes, computed in memory. `check` uses this to prove the
    plane on disk is exactly what the declaration implies."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    view = view_model(ctx, capabilities)
    produced: dict[str, str] = {}
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            body = ctx.manifest.payload_text(item["source"])
            produced[item["target"]] = template.render(body, view)
    return produced


def plan_entries(ctx, capabilities=None) -> list:
    """The write set, as DATA and without rendering a single byte of content. A plan must be
    computable before the bindings it would project from exist -- otherwise the one moment an
    operator most needs to see what would happen is the one moment nothing can be shown."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    targets, writes = [], []
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            targets.append(item["target"])
            writes.append(plan_module.Write(
                "replace" if ctx.workspace.exists(item["target"]) else "create",
                item["class"], item["mode"], capability.id, item["target"], item))
    # The plane is rebuilt wholesale, so anything in it that nothing renders is REMOVED. A plan
    # that lists only what it writes is not a plan: deletion is the effect an operator most
    # needs to have seen coming.
    orphans = [
        plan_module.Write("remove", "projection", "projection", "-", rel)
        for rel in ctx.workspace.files_under(_plane(ctx)) if rel not in targets
    ]
    return orphans + writes


def run(ctx, args, capabilities=None) -> int:
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    writes = plan_entries(ctx, capabilities)
    if getattr(args, "plan", False):
        print(plan_module.report("render", writes))
        return 0

    ctx.workspace.unscoped().remove_tree(_plane(ctx))
    produced = projections(ctx, capabilities)
    scopes = {c.id: ctx.workspace.scoped(c.targets()) for c in capabilities}
    for write in writes:
        if write.disposition != "remove":
            scopes[write.capability].write_text(write.target, produced[write.target])
        print(f"  {write.accomplished:<9}  {write.target}")
    return 0
