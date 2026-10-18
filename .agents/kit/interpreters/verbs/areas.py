"""areas -- draft a host's areas and their proof from the modules its build tool declares (ADR-025 am. 4).

    python .agents/kit/interpreters/cli.py areas --root .                    # the draft, and what it adds
    python .agents/kit/interpreters/cli.py areas --root . --approve <who>    # write what it adds

A host whose areas are empty weighs every change alike and proves it by everything or nothing. A build
tool already knows the host's modules: its adapter publishes a MODULE MAP (where the modules are
declared, the field that is a module's path, the vouched command that proves one). This verb reads
every module map an enabled capability publishes and drafts one area per module -- its path, proved by
its own tests where that command is vouched -- one for the tool's own declarations (one rung dearer: how the
host is built and delivered), and its prose (proved by `check` alone). A module at the repository root
claims what no other area claims. An area the host wrote is never touched: the draft ADDS, and it
recomputes only the `paths` of an area it drafted itself and nobody edited since -- one whose
`drafted_as` still equals its `paths` (a root module's, once the kit planes are known). Writing it is a
door (`--approve`).

A module map takes one of two forms. The MANIFEST form names the file and the pointer where a build tool
declares its modules. The MARKER form is for a host with no such manifest: a module is every directory
the repository carries that holds one of its `markers` (a build script, a package manifest -- with a value
at `marker_pointer` when one is named), and its proof is the map's `command` template; drafting such an
area also drafts the policy command it is proved by (`commands.test-<id>`), at the same door.

The KIT PLANES -- every directory an enabled capability installs, projects or floors into, and the
directory the kit itself is vendored in -- are drafted as one area a rung dearer, proved by `check` alone: how the
host is governed is not the root module's reversible code. It is drafted only once the areas declaration
is committed: the install commit right after `start` carries every plane, and a scale that made it owe a
card would be the ceremony a fresh host cannot walk yet. A module at the repository root WAITS for them:
drafted before the planes, it would claim every plane as the root module's code.
"""

from __future__ import annotations

import re

import collection
import declared
import hostlock
import lifecycle as lifecycle_module
import workclass
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




def _excluding(patterns) -> str:
    """A pattern claiming every path NONE of `patterns` claims, as `re.search` reads each: inside a
    start-anchored lookahead an unanchored pattern must be free to start anywhere (`.*?`), and a pattern
    is kept whole -- never stripped of its own anchors or groups."""
    return "^(?!" + "|".join(f"(?:.*?(?:{p}))" for p in patterns) + ").+"


def planes(capabilities, kit_dir=None) -> list:
    """The top-level directories the enabled capabilities write into (installs, projections, floors) and
    the directory the kit is vendored in -- pure over what the declarations say. Only a hidden directory
    is a plane: a capability that seeds into a visible one (`docs/`) writes into the host's own tree."""
    found = set()
    for capability in capabilities:
        rows = [i.get("target") for i in capability.installs] + [f.get("path") for f in capability.raw.get("floor") or []]
        for rel in rows:
            rel = str(rel or "")
            rel = rel[2:] if rel.startswith("./") else rel
            top = rel.split("/", 1)[0] + "/" if "/" in rel else ""
            if top.startswith(".") and top != "./":  # a tool's own plane; a visible directory is the host's
                found.add(top)
    if kit_dir:
        found.add(kit_dir.strip("/").split("/", 1)[0] + "/")
    return sorted(found)


def drafted(maps: list, vouched: set, plane_dirs=(), plane_files=(), roots=True, scale=(), drafts=None) -> list:
    """The areas the module maps imply -- pure: `maps` is [(map document, {module id: module})]. The kit
    planes are `plane_dirs` and `plane_files`, the repository's own metadata files (the vcs port names them).
    `roots` False holds back a module at the repository root. Every drafted area carries `drafted_as`, the
    paths it was drafted with: the mark that it is the draft's and not the host's. `scale` is the host's
    undo scale, cheapest first, as its work-class catalogue declares it: code is drafted at its cheapest rung,
    the planes and a tool's declarations one rung above -- the words are the catalogue's, never spelled here."""
    if not scale:
        raise AreasError("no undo scale to draft against: the host's work-class catalogue declares none")
    cheap, guarded = scale[0], scale[min(1, len(scale) - 1)]
    drafts = drafts or {}

    def rung(n) -> str:
        return scale[min(int(n), len(scale) - 1)]
    out, want_roots, roots = [], roots, []
    planes = drafts.get("planes")
    if plane_dirs and planes:
        held = [re.escape(d) for d in plane_dirs] + [re.escape(f) + "$" for f in plane_files]
        out.append({"id": planes["id"], "paths": "^(" + "|".join(held) + ")", "undo": rung(planes["rung"]),
                    "because": planes["because"], "proved_by": list(planes.get("proved_by", []))})
    for doc, modules in maps:
        for mid, module in sorted(modules.items()):
            path = str((module or {}).get(doc.get("path_field", "path")) or "").strip("/")
            proof = doc["proof"].replace("{id}", str(mid))
            area = {"id": f"module-{_slug(mid)}", "undo": cheap,
                    "because": f"the {mid} module, as {doc.get('path') or 'its marker'} declares it"}
            if proof in vouched:
                area["proved_by"] = [proof]
            if any(a["id"] == area["id"] for a in out + roots):
                continue  # two maps that find one module draft it once: the first map's reading stands
            if path in ("", "."):
                roots.append(area)
            else:
                area["paths"] = f"^{re.escape(path)}/"
                out.append(area)
        if doc.get("declarations"):
            area = {"id": f"{_slug(doc['id'])}-declarations", "paths": "(" + "|".join(doc["declarations"]) + ")",
                    "undo": guarded, "because": f"how {doc['path']} builds and delivers this host"}
            if doc.get("declarations_proof") in vouched:
                area["proved_by"] = [doc["declarations_proof"]]
            out.append(area)
    for shared in drafts.get("shared", []):  # the areas every host has, as the catalogue declares them
        out.append({"id": shared["id"], "paths": shared["paths"], "undo": rung(shared["rung"]),
                    "because": shared["because"], "proved_by": list(shared.get("proved_by", []))})
    claimed = [a["paths"] for a in out]
    for area in roots if want_roots else []:  # the repository root claims what no other area claims
        area["paths"] = _excluding(claimed)
        out.append(area)
    return [dict(area, drafted_as=area["paths"]) for area in out]


def marked(doc: dict, carried: list, read_json, excluded=()) -> tuple:
    """({module id: {"path": dir}}, {command key: command}) for a MARKER map -- every carried directory
    holding one of its markers (with a value at `marker_pointer`, when named), outside the kit planes."""
    modules, commands = {}, {}
    names = set(doc["markers"])
    for rel in sorted(carried):
        head, _, name = rel.rpartition("/")
        if name not in names or any(rel.startswith(d) for d in excluded):
            continue
        if doc.get("marker_pointer"):
            try:
                value = read_json(rel)
            except (OSError, ValueError):
                continue
            for step in doc["marker_pointer"].split("."):
                value = value.get(step) if isinstance(value, dict) else None
            if not value:
                continue
        mid = _slug(head or "root")
        if mid in modules:
            continue
        modules[mid] = {"path": head or "."}
        commands[doc["proof"].replace("{id}", mid).split(":", 1)[1]] = doc["command"].replace("{path}", head or ".")
    return modules, commands


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    import prove  # the vouched commands are prove's reading, held once
    vouched, unread = prove._commands(ctx)
    if unread:  # an area such a command would prove is drafted as proved by everything: why is said
        print("areas: commands not read -- " + "; ".join(f"{prefix} ({why})" for prefix, why in sorted(unread.items()))
              + " -- an area one of them would prove is drafted as proved by everything")
    capabilities = ctx.enabled_capabilities()
    try:
        kit_dir = ctx.manifest.root.resolve().relative_to(ctx.workspace.root.resolve()).as_posix()
    except ValueError:
        kit_dir = None
    plane_dirs = planes(capabilities, kit_dir)
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    install = next((i for i in governed.capability.installs if i.get("reads_as") == "areas"), None)
    if install is None:
        raise AreasError("the delivery capability declares no areas to draft into")
    committed, _why = ctx.workspace.accepted_text(install["target"])
    if committed is None:
        print(f"areas: the areas declaration is not committed yet -- the kit planes ({', '.join(plane_dirs)}) are "
              f"drafted once it is: the install commit carries every plane, and must not owe a card for it")
        plane_dirs = []
    maps, new_commands = [], {}
    carried = None
    for document in declared.sources(ctx, MAPS).values():
        if document.get("markers"):
            if not document.get("command"):
                raise AreasError(f"the module map {document['id']} names markers and no command to prove a module")
            carried = ctx.workspace.carried() if carried is None else carried
            if carried is None:
                print(f"areas: {document['id']} finds modules by what the repository carries, and that cannot be "
                      f"read here -- not drafted")
                continue
            modules, commands = marked(document, carried, ctx.workspace.read_json, plane_dirs or planes(capabilities, kit_dir))
            fresh = {k: v for k, v in commands.items() if f"{document['proof'].split(':', 1)[0]}:{k}" not in vouched}
            new_commands.update(fresh)
            vouched.update({f"{document['proof'].split(':', 1)[0]}:{k}": v for k, v in commands.items()})
            maps.append((dict(document, path_field="path"), modules))
            continue
        if not ctx.workspace.exists(document["path"]):
            print(f"areas: {document['id']} reads {document['path']}, which is not here -- no module drafted from it")
            continue
        value = ctx.workspace.read_json(document["path"])
        for step in document["pointer"].split("."):
            value = value.get(step) if isinstance(value, dict) else None
        if isinstance(value, dict):
            maps.append((document, value))
    areas_doc = ctx.workspace.read_json(install["target"])
    have = {a["id"] for a in areas_doc.get("areas") or []}
    own = ctx.workspace.vcs_files() if plane_dirs else []
    found = workclass.declarations(ctx)
    if found is None:
        print("areas: this host declares no work classes, so no area would weigh anything -- nothing drafted")
        return 0
    scale = [row["id"] for row in found[0]["undo"]]
    draft = drafted(maps, set(vouched), plane_dirs, own, roots=bool(plane_dirs), scale=scale, drafts=found[0].get("drafted_areas"))
    if not plane_dirs:
        waiting = [a["id"] for a in drafted(maps, set(vouched), scale=scale, drafts=found[0].get("drafted_areas")) if a["id"] not in {d["id"] for d in draft}]
        if waiting:
            print(f"areas: {', '.join(waiting)} (the repository root) waits for the kit planes -- drafted now, it "
                  f"would claim every plane as its own code")
    adding = [a for a in draft if a["id"] not in have]
    # An area the draft wrote and nobody edited since (`drafted_as` still its `paths`) follows the draft;
    # an area the host wrote, or edited, is never touched.
    fresh = {a["id"]: a["paths"] for a in draft}
    kept, moved = [], []
    for area in areas_doc.get("areas") or []:
        if area.get("drafted_as") and area["drafted_as"] == area.get("paths") and fresh.get(area["id"], area["paths"]) != area["paths"]:
            area = dict(area, paths=fresh[area["id"]], drafted_as=fresh[area["id"]])
            moved.append(area)
        kept.append(area)
    wanted = {p.split(":", 1)[1] for a in adding for p in a.get("proved_by", [])}
    new_commands = {k: v for k, v in new_commands.items() if k in wanted}
    if not maps:
        print("areas: no enabled capability publishes a module map, or its manifest is not here -- only the "
              "areas every host has are drafted")
    for area in adding:
        proof = ", ".join(area["proved_by"]) if "proved_by" in area else "everything (no vouched command proves it)"
        print(f"  + {area['id']}  {area['paths']}  [{area['undo']}]  proved by {proof or 'check alone'}")
    for area in moved:
        print(f"  ~ {area['id']}  {area['paths']}  (drafted by this verb and not edited since: redrafted)")
    for key, command in sorted(new_commands.items()):
        print(f"  + command {key}: {command}  (the delivery policy's `commands`)")
    if not adding and not moved:
        print("areas: nothing to add -- every drafted area is declared")
        return 0
    who = getattr(args, "approve", None)
    if not who:
        print(f"areas: {len(adding) + len(moved)} area(s) drafted and not written -- writing them is the owner's "
              f"door: areas --approve <who>")
        return 0

    def write() -> int:
        scoped = ctx.workspace.scoped(governed.capability.targets())
        scoped.write_json(install["target"], dict(areas_doc, areas=kept + adding))
        if new_commands:
            policy = next((i for i in governed.capability.installs if i.get("reads_as") == "policy"), None)
            if policy is None:
                raise AreasError("the delivery capability declares no policy to draft the module commands into")
            body = ctx.workspace.read_json(policy["target"]) if ctx.workspace.exists(policy["target"]) else {}
            scoped.write_json(policy["target"], dict(body, commands={**new_commands, **(body.get("commands") or {})}))
            print(f"areas: {len(new_commands)} command(s) written into {policy['target']}")
        print(f"areas: {len(adding)} area(s) written{f', {len(moved)} redrafted' if moved else ''} by {who}")
        return 0

    return hostlock.held(ctx, args, write)
