"""render -- recompute every projection from scratch.

A projection has no history. It is deleted and rebuilt, never merged and never diffed against its
old self, so there is nothing for it to drift FROM. Its inputs are VENDOR + BINDING only; the wall
clock is deliberately not one of them, which is what makes the output byte-reproducible.
"""

from __future__ import annotations

import template

SUMMARY = "recompute every projection from VENDOR + BINDING"


def view_model(ctx) -> dict:
    project = ctx.binding(".agents/project/project.json", "project")
    profile = ctx.binding(".agents/project/profile.json", "profile")
    capabilities = []
    for capability in ctx.enabled_capabilities():
        capabilities.append({
            "id": capability.id,
            "version": capability.version,
            "summary": capability.summary,
            "installs": [dict(item) for item in capability.installs],
            "gates": [dict(gate) for gate in capability.gates],
        })
    return {
        "kit_version": ctx.manifest.version,
        "project": project,
        "capabilities": capabilities,
        "facts": [{"key": k, "value": v} for k, v in sorted(profile["facts"].items())],
    }


def projections(ctx) -> dict:
    """Every projected path and its bytes, computed in memory. `check` uses this to prove the
    plane on disk is exactly what the declaration implies."""
    view = view_model(ctx)
    produced: dict[str, str] = {}
    for capability in ctx.enabled_capabilities():
        for item in capability.installs_of_class("projection"):
            body = ctx.manifest.payload_text(item["source"])
            produced[item["target"]] = template.render(body, view)
    return produced


def run(ctx, args) -> int:
    plane = next(p["root"] for p in ctx.manifest.planes if p["class"] == "projection")
    ctx.workspace.unscoped().remove_tree(plane)
    produced = projections(ctx)
    for capability in ctx.enabled_capabilities():
        scoped = ctx.workspace.scoped(capability.targets())
        for item in capability.installs_of_class("projection"):
            scoped.write_text(item["target"], produced[item["target"]])
            print(f"  projected  {item['target']}")
    return 0
