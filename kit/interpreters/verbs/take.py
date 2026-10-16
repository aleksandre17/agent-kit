"""take -- place a capability the release did not issue BESIDE the pinned kit, never inside it.

ADR-018. The pinned kit is only ever the release: `.agents/kit/` equals its lock, always. What a
host chooses to add has its own two homes, both DECLARED by governance and found here by asking the
declarations, never spelled:

  * the PLANE (install mode `taken`) -- a verbatim copy of the capability as its source published
    it, one directory per id;
  * the DECLARATION (install mode `taken-declaration`) -- one row per take: `id`, `source`,
    `taken_by`, `at`. The h1 printed at the take is a reading, not a declaration: its one home is
    the ADR-008 provenance pin (ADR-018 amendment 1).

The take is a DOOR: without `--approve <who>` it prints what it would take and refuses by name, and
nothing is written. A take whose id the release issued is refused -- a take never shadows the
release. Enabling the taken capability, and pinning its provenance in the estate, stay the acts
they always were (`project.json` is the owner's; `init --approve` pins at first contact).

    python .agents/kit/interpreters/cli.py take --root . --path <capability-dir>[,<dir>] --approve <who>
"""

from __future__ import annotations

import json
from pathlib import Path

import doors
import estate as estate_module
import hostlock
import manifest as manifest_port
import provenance
from errors import KitError

SUMMARY = "take a published capability into this host's take plane, beside the pinned kit"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class TakeError(KitError):
    """A take named no capability directory, a directory whose declaration is not a capability,
    or a capability whose id the release already issued."""

    code = "KIT0045"


def homes(ctx) -> tuple:
    """(plane install, declaration install, the capability that owns both) -- as governance
    declares them. A release that declares no take plane cannot be taken into, and says so."""
    found = {}
    for capability in ctx.manifest.capabilities:
        for item in capability.installs:
            if item["mode"] in (manifest_port.TAKEN_MODE, manifest_port.TAKEN_DECLARATION_MODE):
                found.setdefault(item["mode"], []).append((item, capability))
    if any(len(found.get(m, [])) != 1
           for m in (manifest_port.TAKEN_MODE, manifest_port.TAKEN_DECLARATION_MODE)):
        raise TakeError("this kit declares no single take plane and take declaration, so nothing "
                        "can be taken beside it (ADR-018)")
    (plane, owner), (statement, _same) = (found[manifest_port.TAKEN_MODE][0],
                                          found[manifest_port.TAKEN_DECLARATION_MODE][0])
    return plane, statement, owner


def _read(source: Path, plane: dict) -> dict:
    declaration = source / plane["declaration"]
    if not declaration.is_file():
        raise TakeError(f"{source.as_posix()}: no {plane['declaration']} -- a take is a directory "
                        f"that declares one capability")
    try:
        return json.loads(declaration.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TakeError(f"{declaration.as_posix()}: not readable as JSON -- {exc}") from exc


def _named(ctx, source: Path) -> str:
    """Where a take came from, as every clone of this host can read it: relative to the host when
    it lies inside it (a vendored kit, a submodule), absolute only when it lies outside."""
    try:
        return source.relative_to(ctx.workspace.root.resolve()).as_posix()
    except ValueError:
        return source.as_posix()


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    if not args.path:
        raise TakeError("take needs --path <capability-dir>[,<dir>]: the published capability to take")
    plane, statement, owner = homes(ctx)
    issued = {c.id for c in ctx.manifest.capabilities if c.id not in ctx.manifest.taken}
    moment = ctx.clock.now()

    takes = []
    for given in args.path:
        source = Path(given).resolve()
        raw = _read(source, plane)
        errors = ctx.manifest.validate(raw, "capability")
        if errors:
            raise TakeError(f"{source.as_posix()} does not declare a capability:\n  " + "\n  ".join(errors))
        if raw["id"] in issued:
            raise manifest_port.TakeShadows(
                f"{source.as_posix()} declares {raw['id']!r}, which the release issued; a take never "
                f"shadows the release (ADR-018)")
        files = {p.relative_to(source).as_posix(): p.read_bytes()
                 for p in sorted(source.rglob("*")) if p.is_file()}
        signature = (raw.get(provenance.CLAIM) or {}).get("signature")
        prefix = f"{plane['namespace']}{raw['id']}/"
        measured = provenance.h1([(prefix + rel, data) for rel, data in files.items()
                                  if prefix + rel != signature])
        takes.append((raw["id"], source, files, measured))
        print(f"  take  {raw['id']}@{raw['version']}  {measured}  from {source.as_posix()}  -> "
              f"{plane['target']}{raw['id']}/")

    if args.plan:
        return 0
    if not args.approve:
        doors.refuse(
            f"{len(takes)} capability(ies) would be taken beside the pinned kit: "
            + ", ".join(t[0] for t in takes),
            "person who owns this host",
            "take --root <host> --path <dir> --approve <who>",
            "What a host runs that its release did not issue is the host's choice, and the record "
            "of it names who chose.")

    ws = ctx.workspace.scoped(owner.targets())
    current = (ctx.binding(statement["target"], statement["validates"])
               if ctx.workspace.exists(statement["target"])
               else {"schema_version": ctx.manifest.version_of(statement["validates"]), "takes": []})
    # A row carried from before amendment 1 sheds its digest here: the reading has one home, the pin.
    rows = {row["id"]: {k: v for k, v in row.items() if k != "digest"} for row in current["takes"]}
    for identity, source, files, measured in takes:
        rows[identity] = {"id": identity, "source": _named(ctx, source),
                          "taken_by": args.approve, "at": moment}
    document = {"schema_version": current["schema_version"],
                "takes": [rows[k] for k in sorted(rows)]}
    errors = ctx.manifest.validate(document, statement["validates"])
    if errors:
        raise TakeError(f"{statement['target']} would not honour its schema:\n  " + "\n  ".join(errors))

    # The provenance pin is written HERE, at arrival (ADR-018 amendment 2): the digest of the bytes
    # that arrived, marked trust-on-first-use, so a change between this take and the approval that
    # attests it is a drift, never a first contact.
    at = estate_module.target(ctx, required=False)
    recorded = estate_module.read(ctx)
    if at is None or recorded is None:
        raise TakeError("this host holds no estate reading, so there is nowhere to pin what "
                        "arrives; `init --approve <who>` first (ADR-018 amendment 2)")
    estate_owner = next(c for c in ctx.manifest.capabilities for i in c.installs if i["target"] == at)
    pins = {p["capability"]: p for p in recorded.get("taken", [])}
    for identity, _source, files, measured in takes:
        version = json.loads(files[plane["declaration"]].decode("utf-8"))["version"]
        try:
            pins[identity] = provenance.arrival(ctx, identity, version, measured, args.approve, moment,
                                                pins.get(identity))
        except provenance.ProvenanceRefused as exc:
            raise TakeError(str(exc)) from exc
    estate = dict(recorded, taken=[pins[k] for k in sorted(pins)])
    errors = ctx.manifest.validate(estate, ctx.install_of_mode(estate_module.MODE)["validates"])
    if errors:
        raise TakeError(f"{at} would not honour its schema:\n  " + "\n  ".join(errors))

    def write() -> int:
        for identity, _source, files, _measured in takes:
            ws.write_tree(plane["target"] + identity, files)
        ws.write_json(statement["target"], document)
        ctx.workspace.scoped(estate_owner.targets()).write_json(at, estate)
        for identity, _source, _files, measured in takes:
            print(f"  TAKEN  {identity}  {measured}  by {args.approve} at {moment} -- PINNED at "
                  f"arrival, {provenance.basis_at(ctx, provenance.ARRIVAL)}; enable it in the host's declaration, "
                  f"then `init --approve <who>` attests the pin")
        return 0

    return hostlock.held(ctx, args, write)
