"""areas -- draft a host's areas and their proof from the modules its build tool declares (ADR-025 am. 4).

    python .agents/kit/interpreters/cli.py areas --root .                    # the draft, and what it adds
    python .agents/kit/interpreters/cli.py areas --root . --approve <who>    # write what it adds

A host whose areas are empty weighs every change alike and proves it by everything or nothing. A build
tool already knows the host's modules: its adapter publishes a MODULE MAP (where the modules are
declared, the field that is a module's path, the vouched command that proves one). This verb reads
every module map an enabled capability publishes and drafts one area per module -- its path, proved by
its own tests where that command is vouched -- one for the tool's own declarations (costly: how the
host is built and delivered), and its prose (proved by `check` alone). A module at the repository root
claims what no other area claims. An area the host already declares is
never touched: the draft only ADDS. Writing it is a door (`--approve`).
"""

from __future__ import annotations

import re

import collection
import declared
import hostlock
import lifecycle as lifecycle_module
from errors import KitError

SUMMARY = "draft the host's areas and their proof from the modules its build tool declares, at a door"
MUTATES = True
REQUIRES_APPROVED_HOST = True
MAPS = {declared.CONTRACT: "module-map"}


class AreasError(KitError):
    """A draft that cannot be taken honestly."""

    code = "KIT0092"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "root"


def drafted(maps: list, vouched: set) -> list:
    """The areas the module maps imply -- pure: `maps` is [(map document, {module id: module})]."""
    out, roots = [], []
    for doc, modules in maps:
        for mid, module in sorted(modules.items()):
            path = str((module or {}).get(doc["path_field"]) or "").strip("/")
            proof = doc["proof"].replace("{id}", str(mid))
            area = {"id": f"module-{_slug(mid)}", "undo": "reversible",
                    "because": f"the {mid} module, as {doc['path']} declares it"}
            if proof in vouched:
                area["proved_by"] = [proof]
            if path in ("", "."):
                roots.append(area)
            else:
                area["paths"] = f"^{re.escape(path)}/"
                out.append(area)
        if doc.get("declarations"):
            area = {"id": f"{_slug(doc['id'])}-declarations", "paths": "(" + "|".join(doc["declarations"]) + ")",
                    "undo": "costly", "because": f"how {doc['path']} builds and delivers this host"}
            if doc.get("declarations_proof") in vouched:
                area["proved_by"] = [doc["declarations_proof"]]
            out.append(area)
    # Prose every host has. Its own declarations under `.agents/` are not drafted heavier: the first commit
    # after `start` carries them all, and a draft that made it owe a card would be the ceremony it removes.
    out.append({"id": "prose", "paths": r"(^docs/|\.md$)", "undo": "reversible",
             "because": "prose changes nothing that runs; check reads its structure", "proved_by": []})
    claimed = [a["paths"] for a in out]
    for area in roots:  # the repository root claims what no other area claims
        area["paths"] = "^(?!(?:" + "|".join(p.lstrip("^").strip("()") for p in claimed) + r")).+"
        out.append(area)
    return out


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    import prove  # the vouched commands are prove's reading, held once
    vouched, _unread = prove._commands(ctx)
    maps = []
    for document in declared.sources(ctx, MAPS).values():
        if not ctx.workspace.exists(document["path"]):
            continue
        value = ctx.workspace.read_json(document["path"])
        for step in document["pointer"].split("."):
            value = value.get(step) if isinstance(value, dict) else None
        if isinstance(value, dict):
            maps.append((document, value))
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    install = next((i for i in governed.capability.installs if i.get("reads_as") == "areas"), None)
    if install is None:
        raise AreasError("the delivery capability declares no areas to draft into")
    areas_doc = ctx.workspace.read_json(install["target"])
    have = {a["id"] for a in areas_doc.get("areas") or []}
    adding = [a for a in drafted(maps, set(vouched)) if a["id"] not in have]
    if not maps:
        print("areas: no enabled capability publishes a module map, or its manifest is not here -- only the "
              "areas every host has are drafted")
    for area in adding:
        proof = ", ".join(area["proved_by"]) if "proved_by" in area else "everything (no vouched command proves it)"
        print(f"  + {area['id']}  {area['paths']}  [{area['undo']}]  proved by {proof}")
    if not adding:
        print("areas: nothing to add -- every drafted area is declared")
        return 0
    who = getattr(args, "approve", None)
    if not who:
        print(f"areas: {len(adding)} area(s) drafted and not written -- writing them is the owner's door: "
              f"areas --approve <who>")
        return 0

    def write() -> int:
        ctx.workspace.scoped(governed.capability.targets()).write_json(
            install["target"], dict(areas_doc, areas=list(areas_doc.get("areas") or []) + adding))
        print(f"areas: {len(adding)} area(s) written by {who}")
        return 0

    return hostlock.held(ctx, args, write)
